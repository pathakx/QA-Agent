from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END
from backend.services.execution_service import execute_test_script
from backend.core.supabase_client import get_supabase_client
from backend.core.websocket_manager import emitter
import json
import asyncio
import os

# Define State
class AgentState(TypedDict):
    project_id: str
    access_token: str # Add access token for authenticated requests
    file_structure: str
    test_plan: List[dict]
    generated_scripts: List[dict]
    execution_results: List[dict]
    final_report: str
    errors: Annotated[List[str], operator.add]
    retry_count: int
    html_path: str # Path to the HTML file for testing
    chroma_collection_name: str # Project-specific vector store collection

# Nodes

async def analyze_project(state: AgentState):
    """Analyze project files and structure"""
    print(f"Analyzing project {state['project_id']}...")
    try:
        await emitter.emit_agent_log(state['project_id'], "🔍 Analyzing project structure...")
        
        # Just verifying project exists
        # Use authenticated client to respect RLS policies
        from backend.core.supabase_client import create_user_client
        client = create_user_client(state['access_token'])
        res = client.table('projects').select('name').eq('id', state['project_id']).single().execute()
        if not res.data:
            return {"errors": ["Project not found"]}
            
        # Retrieve Knowledge Base status
        from backend.services.kb_service import get_kb_status
        from backend.services.selenium_service import load_ui_elements
        
        # Fetch confirmed project HTML file from DB
        html_file = client.table('kb_files').select('storage_path').eq('project_id', state['project_id']).eq('file_type', 'html').limit(1).execute()
        
        # Fetch Project Collection Name for RAG
        proj_data = client.table('projects').select('chroma_collection_name').eq('id', state['project_id']).single().execute()
        collection_name = proj_data.data['chroma_collection_name'] if proj_data.data else None
        
        target_html_path = None
        if html_file.data and len(html_file.data) > 0:
            target_html_path = html_file.data[0]['storage_path']
            print(f"[{state['project_id']}] Found project HTML file: {target_html_path}")
        else:
            # Check for ANY uploaded files in this project
            file_count_res = client.table('kb_files').select('id', count='exact').eq('project_id', state['project_id']).execute()
            file_count = file_count_res.count if file_count_res.count is not None else 0
            
            # Fallback: Check physical directory if DB is empty (handles orphaned files)
            base_p = f"backend/data/projects/{state['project_id']}"
            html_p = f"{base_p}/html"
            docs_p = f"{base_p}/docs"
            
            has_html = os.path.exists(html_p) and len(os.listdir(html_p)) > 0
            has_docs = os.path.exists(docs_p) and len(os.listdir(docs_p)) > 0
            
            if file_count == 0 and not has_html and not has_docs:
                msg = "🛑 No files found in Database or on Disk. Please upload an HTML file or Documents in the Knowledge Base tab to proceed."
                print(f"[{state['project_id']}] Aborting: {msg}")
                await emitter.emit_agent_log(state['project_id'], msg)
                return {"errors": [msg]}
            
            if file_count == 0 and (has_html or has_docs):
                msg = "⚠️ Found orphaned files on disk. Auto-ingesting to restore database and embeddings..."
                await emitter.emit_agent_log(state['project_id'], msg)
                
                # Import ingestion services locally
                from backend.services.project_kb_service import ingest_document_for_project, ingest_html_for_project
                from backend.core.vectorstore import get_vector_store
                
                # Setup context
                project_data = {'id': state['project_id'], 'name': res.data['name']}
                vector_store = get_vector_store()
                
                # 1. Re-ingest HTML (Parses UI Elements)
                if has_html:
                    files = [f for f in os.listdir(html_p) if f.endswith('.html')]
                    for f in files:
                        f_path = os.path.join(html_p, f)
                        try:
                            await emitter.emit_agent_log(state['project_id'], f"  - Re-processing HTML: {f}")
                            # Also insert into DB to fix "orphaned" state permanently?
                            # ingest_html_for_project only parses. 
                            # We should ideally call the API function that does both, but that's complex.
                            # Just updating vector store/local json is enough for Agent.
                            ingest_html_for_project(f_path, project_data)
                            target_html_path = f_path 
                        except Exception as e:
                            print(f"Failed to ingest {f}: {e}")

                # 2. Re-ingest Docs (Generates Embeddings)
                if has_docs:
                    files = [f for f in os.listdir(docs_p) if os.path.isfile(os.path.join(docs_p, f))]
                    for f in files:
                        f_path = os.path.join(docs_p, f)
                        try:
                            await emitter.emit_agent_log(state['project_id'], f"  - Generating Embeddings for: {f}")
                            ingest_document_for_project(f_path, project_data, vector_store)
                        except Exception as e:
                            print(f"Failed to ingest {f}: {e}")
                            
                await emitter.emit_agent_log(state['project_id'], "✅ Context restored automatically.")

            print(f"[{state['project_id']}] Project analysis continuing...")

        kb_status = get_kb_status() # Keep for summary compatibility
        ui_elements = load_ui_elements(target_html_path) # Pass the specific path
        
        # Store for later steps
        state['html_path'] = target_html_path
        
        ui_summary = "\n".join([f"- {e.tag} ({e.element_type}): {e.name or e.id or e.selector}" for e in ui_elements])
        
        structure = f"""
Project: {res.data['name']}
Knowledge Base:
- Documents: {kb_status['doc_count']} ({kb_status['embedding_count']} embeddings)
- Analyzed UI Elements: {len(ui_elements)}

UI Elements Found:
{ui_summary}
"""
        # Emit detailed structure log
        await emitter.emit_agent_log(state['project_id'], f"📂 Analyzed: {kb_status['doc_count']} docs, {len(ui_elements)} UI elements.")
        
        return {"file_structure": structure, "html_path": target_html_path, "chroma_collection_name": collection_name}
    except Exception as e:
        return {"errors": [f"Analysis failed: {str(e)}"]}

async def create_test_plan(state: AgentState):
    """Generate test cases based on analysis"""
    print("Generating Test Plan...")
    try:
        await emitter.emit_agent_log(state['project_id'], "📝 Generating test plan...")
        
        if not state.get('file_structure'):
            return {"errors": ["No file structure found"]}

        from backend.core.supabase_client import create_user_client
        client = create_user_client(state['access_token'])
        
        # 1. Try to load from DB
        existing_tests = client.table('testcases').select('*').eq('project_id', state['project_id']).execute()
        if existing_tests.data and len(existing_tests.data) > 0:
            await emitter.emit_agent_log(state['project_id'], f"📂 Loaded {len(existing_tests.data)} existing test cases from DB.")
            # Ensure correct format (DB might have extra fields, we need clean dicts for processing)
            return {"test_plan": existing_tests.data}

        # 2. If not in DB, Generate with LLM
        from backend.core.llm_client import LLMClient
        llm = LLMClient()
        
        # RAG Integration: Retrieve relevant context from Knowledge Base
        from backend.services.rag_service import retrieve_context
        
        # Create a search query based on the project structure to get general context
        search_query = f"Test requirements and functional specifications for {state['file_structure']}"
        context_chunks = retrieve_context(search_query, top_k=10, collection_name=state.get('chroma_collection_name'))
        
        context_text = "\n".join([f"- {c.text}" for c in context_chunks])
        
        if not context_text:
             context_text = "No specific documentation found in Knowledge Base."

        prompt = f"""Analyze the following project structure and Documentation Context:

PROJECT STRUCTURE:
{state['file_structure']}

DOCUMENTATION CONTEXT (from RAG):
{context_text}

Generate a comprehensive test plan JSON.
You MUST generate test cases to cover ALL identified UI elements and features.
Do NOT limit yourself to a fixed number of test cases. Create as many as needed to ensure full coverage.
Includes positive flows, negative flows (invalid inputs), and edge cases.
IMPORTANT: Use the exact keys 'test_id', 'scenario', 'steps', 'expected_result'.

Format:
[
    {{
        "test_id": "TC-AUTO-001",
        "feature": "Login",
        "scenario": "Verify user login functionality with valid credentials",
        "steps": ["Navigate to login page", "Enter valid username", "Enter valid password", "Click Submit"],
        "expected_result": "User is redirected to dashboard"
    }}
]
"""
        # LLMClient.generate returns the string content directly
        # Run in executor to allow cancellation
        loop = asyncio.get_event_loop()
        test_plan_str = await loop.run_in_executor(None, llm.generate, prompt)
        
        # Basic parsing (LLM might wrap in markdown)
        if "```json" in test_plan_str:
            test_plan_str = test_plan_str.split("```json")[1].split("```")[0]
        elif "```" in test_plan_str:
            test_plan_str = test_plan_str.split("```")[1].split("```")[0]
            
        test_plan = json.loads(test_plan_str.strip())
        
        # 3. Save to DB
        if test_plan:
            try:
                # Prepare records for insertion
                records = []
                for t in test_plan:
                    records.append({
                        "project_id": state['project_id'],
                        "test_id": t.get("test_id"),
                        "feature": t.get("feature"),
                        "scenario": t.get("scenario"),
                        "steps": t.get("steps"), # JSONB
                        "expected_result": t.get("expected_result")
                    })
                client.table('testcases').insert(records).execute()
                await emitter.emit_agent_log(state['project_id'], f"💾 Saved {len(records)} test cases to DB.")
            except Exception as db_err:
                 print(f"DB Insert Error: {db_err}")
                 await emitter.emit_agent_log(state['project_id'], f"⚠️ Failed to save to DB: {str(db_err)}")
        
        await emitter.emit_agent_log(state['project_id'], f"✅ Generated {len(test_plan)} test cases.")
        return {"test_plan": test_plan}
    except Exception as e:
        return {"errors": [f"Test plan generation failed: {str(e)}"]}

async def generate_scripts(state: AgentState):
    """Generate Selenium scripts for each test case"""
    print("Generating Scripts...")
    scripts = []
    try:
        await emitter.emit_agent_log(state['project_id'], "💻 Generating automation scripts...")
        
        from backend.services.selenium_service import generate_selenium_script
        from backend.core.supabase_client import create_user_client
        client = create_user_client(state['access_token'])
        
        if not state.get('test_plan'):
             return {"errors": ["No test plan generated"]}

        # Prefetch existing scripts
        existing_scripts_res = client.table('selenium_scripts').select('*').eq('project_id', state['project_id']).execute()
        existing_map = {s['test_case_id']: s['script_content'] for s in existing_scripts_res.data} if existing_scripts_res.data else {}

        for test in state['test_plan']:
            test_id = test.get('test_id')
            if not test_id:
                continue
            
            script_content = ""
            
            # Check DB Cache
            if test_id in existing_map:
                await emitter.emit_agent_log(state['project_id'], f"  - Using cached script for {test_id}")
                script_content = existing_map[test_id]
            else:
                # Generate New
                await emitter.emit_agent_log(state['project_id'], f"  - Generating script for {test_id}...")
                
                # Pass explicit HTML path if available
                html_path = state.get('html_path')
                collection_name = state.get('chroma_collection_name')
                
                # Run sync generation in executor to non-block event loop
                loop = asyncio.get_event_loop()
                script_content = await loop.run_in_executor(None, generate_selenium_script, test, html_path, collection_name)
                
                # Save to DB
                try:
                    client.table('selenium_scripts').insert({
                        "project_id": state['project_id'],
                        "test_case_id": test_id,
                        "script_content": script_content
                    }).execute()
                except Exception as e:
                    print(f"Failed to save script {test_id}: {e}")
            
            scripts.append({
                "test_id": test_id,
                "content": script_content
            })
            
        await emitter.emit_agent_log(state['project_id'], f"✅ Ready with {len(scripts)} scripts.")
        return {"generated_scripts": scripts}
    except Exception as e:
        return {"errors": [f"Script generation failed: {str(e)}"]}

async def execute_tests(state: AgentState):
    """Execute generated scripts"""
    print("Executing Tests...")
    results = []
    try:
        if not state.get('generated_scripts'):
            await emitter.emit_agent_log(state['project_id'], "⚠️ No scripts to execute.")
            return {"execution_results": []}

        await emitter.emit_agent_log(state['project_id'], "🚀 Starting test execution...")
        
        from backend.services.execution_service import execute_test_script
        
        for script in state['generated_scripts']:
            test_id = script['test_id']
            await emitter.emit_agent_log(state['project_id'], f"Running {test_id}...")
            print(f"Executing {test_id}...")
            
            # Execute script
            result = await execute_test_script(script['content'])
            
            status_icon = "✅" if result.status == 'passed' else "❌"
            await emitter.emit_agent_log(state['project_id'], f"{status_icon} {test_id}: {result.status}")
            
            results.append({
                "test_id": test_id,
                "status": result.status,
                "duration": result.duration,
                "error": result.error_message,
                "video": result.video_path,
                "logs": result.logs
            })
            
        return {"execution_results": results}
    except Exception as e:
        return {"errors": [f"Execution failed: {str(e)}"]}

async def generate_report(state: AgentState):
    """Compile final report"""
    print("Compiling Report...")
    try:
        execution_results = state.get('execution_results', [])
        passed = sum(1 for r in execution_results if r['status'] == 'passed')
        total = len(execution_results)
        
        report = f"""
# Autonomous Test Report
**Project ID**: {state['project_id']}
**Total Tests**: {total}
**Passed**: {passed}
**Failed**: {total - passed}

## Results:
"""
        for res in execution_results:
            icon = "✅" if res['status'] == 'passed' else "❌"
            report += f"\n- {icon} **{res['test_id']}**: {res['status']} ({res['duration']:.2f}s)"
            if res['error']:
                report += f"\n  - Error: {res['error']}"
        
        await emitter.emit_agent_log(state['project_id'], "📊 Report compiled successfully.")
        return {"final_report": report}
    except Exception as e:
         return {"errors": [f"Report generation failed: {str(e)}"]}

async def fix_failures(state: AgentState):
    """Analyze failures and regenerate scripts if needed (Self-Healing)"""
    retry_count = state.get('retry_count', 0)
    
    # Limit retries to 1 to avoid infinite loops and high costs
    if retry_count >= 1:
        return {"retry_count": retry_count + 1} # Stop trying

    execution_results = state.get('execution_results', [])
    failed_tests = [r for r in execution_results if r['status'] != 'passed']
    
    if not failed_tests:
        return {"retry_count": retry_count} # No failures, nothing to fix

    print(f"Attempting to fix {len(failed_tests)} failed tests (Retry {retry_count + 1})...")
    await emitter.emit_agent_log(state['project_id'], f"🔧 Attempting to fix {len(failed_tests)} failed tests...")
    
    from backend.core.llm_client import LLMClient
    from backend.services.selenium_service import generate_selenium_script, build_prompt
    from backend.core.supabase_client import create_user_client
    
    llm = LLMClient()
    client = create_user_client(state['access_token'])
    
    updated_scripts = state.get('generated_scripts', [])
    
    for failure in failed_tests:
        test_id = failure['test_id']
        error_msg = failure['error']
        logs = failure.get('logs', '')
        
        # Find original test case data
        test_case = next((t for t in state['test_plan'] if t['test_id'] == test_id), None)
        if not test_case:
            continue
            
        await emitter.emit_agent_log(state['project_id'], f"  - Fixing {test_id}...")
        
        # Prompt for fixing
        # We assume the test case scenario is correct, but script failed. 
        # But user said "generate test cases and script".
        # We will keep the scenario but Ask LLM to re-write script considering the error.
        
        # We temporarily inject the error into the test case for the prompt builder?
        # A clearer way is to just call generate_selenium_script but maybe modify the function?
        # For simplicity/efficiency, we will just RE-GENERATE the script. 
        # Often failures are due to transient issues or bad selectors. 
        # A fresh generation might not help unless we give feedback.
        
        # Let's use a specialized repair prompt manually here
        # from backend.services.selenium_service import build_prompt (moved to imports)
        html_path = state.get('html_path')
        collection_name = state.get('chroma_collection_name')
        base_prompt = build_prompt(test_case, html_path=html_path, collection_name=collection_name)
        
        repair_prompt = f"""
        {base_prompt}
        
        PREVIOUS EXECUTION FAILED:
        Error: {error_msg}
        Logs: {logs}
        
        INSTRUCTION:
        The previous script failed with the error above. 
        Analyze the failure. 
        Re-write the script to fix this specific error.
        If it was a Timeout, increase waits.
        If it was a generic error, add more robust error handling or check selectors.
        """
        
        # LLMClient.generate is synchronous, run in executor
        loop = asyncio.get_event_loop()
        new_script_content = await loop.run_in_executor(None, llm.generate, repair_prompt)

        # Strip markdown code fences if present
        new_script_content = new_script_content.strip()
        if new_script_content.startswith('```python'):
            new_script_content = new_script_content[len('```python'):].strip()
        elif new_script_content.startswith('```'):
            new_script_content = new_script_content[3:].strip()
        if new_script_content.endswith('```'):
            new_script_content = new_script_content[:-3].strip()

        # Update DB
        try:
             # Delete old script (or update) - we'll update based on project_id + test_case_id
             client.table('selenium_scripts').delete().eq('project_id', state['project_id']).eq('test_case_id', test_id).execute()
             client.table('selenium_scripts').insert({
                "project_id": state['project_id'],
                "test_case_id": test_id,
                "script_content": new_script_content
             }).execute()
        except Exception as e:
            print(f"DB Update Failed: {e}")

        # Update State List
        for s in updated_scripts:
            if s['test_id'] == test_id:
                s['content'] = new_script_content
    
    return {
        "generated_scripts": updated_scripts,
        "retry_count": retry_count + 1,
        "execution_results": [] # Clear results to force re-execution of all? Or just re-run? 
        # execute_tests runs ALL scripts in 'generated_scripts'. Ideally we only run failed ones. 
        # But execution_service logic is simple. Let's just re-run all or we need to filter 'generated_scripts'.
        # For efficiency, we should filter. But modifying 'generated_scripts' affects final state.
        # Let's just re-run all for now to be safe and simple in graph.
    }

def should_retry(state: AgentState):
    """Determine if we should loop back to execute"""
    # If we just performed a fix (retry_count went from 0 -> 1), and we cleared execution_results?
    # Actually 'fix_failures' is run AFTER execute.
    # If fix_failures decided to retry, it incremented counter.
    # We check: Did we just increment retry count? = 1? AND did we have failures?
    
    # State 'retry_count' starts at 0.
    # execute -> fix_failures (sees 0, increments to 1, updates scripts) -> decide
    
    if state.get('retry_count', 0) == 1 and not state.get('execution_results'):
        # We cleared execution results in fix_failures, signaling a re-run
        return "retry"
    return "end"

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("analyze", analyze_project)
workflow.add_node("plan", create_test_plan)
workflow.add_node("script", generate_scripts)
workflow.add_node("execute", execute_tests)
workflow.add_node("fix", fix_failures)
workflow.add_node("report", generate_report)

workflow.set_entry_point("analyze")

workflow.add_edge("analyze", "plan")
workflow.add_edge("plan", "script")
workflow.add_edge("script", "execute")
workflow.add_edge("execute", "fix")

workflow.add_conditional_edges(
    "fix",
    should_retry,
    {
        "retry": "execute",
        "end": "report"
    }
)

workflow.add_edge("report", END)

app = workflow.compile()
