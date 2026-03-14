"""
Project-aware test case generation service
"""
import json
from backend.services.project_rag_service import retrieve_project_context, build_testcase_prompt
from backend.core.llm_client import LLMClient
from backend.core.vectorstore import VectorStore

llm = LLMClient()

def generate_testcases_for_project(query: str, vector_store: VectorStore, project_name: str = "", existing_testcases: list = None):
    """Generate test cases using project-specific knowledge base"""
    try:
        # Logging setup
        with open("backend.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"\n--- New Request for Project '{project_name}': {query} ---\n")
            
        print(f"[Project: {project_name}] Generating test cases for query: {query}")
        chunks = retrieve_project_context(query, vector_store)
        print(f"[Project: {project_name}] Retrieved {len(chunks)} context chunks")
        
        with open("backend.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"Retrieved {len(chunks)} chunks.\n")
        
        # Check if knowledge base is empty
        if not chunks or len(chunks) == 0:
            return {
                "testcases": [],
                "error": "Knowledge Base is empty. Please upload documents first in the Knowledge Base tab.",
                "empty_kb": True
            }
        
        prompt = build_testcase_prompt(query, chunks, existing_testcases)
        print(f"[Project: {project_name}] Sending prompt to LLM...")
        response = llm.generate(prompt)
        print(f"[Project: {project_name}] Received response from LLM (length: {len(response)})")
        
        with open("backend.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"LLM Response:\\n{response}\\n----------\\n")
        
        # Check if LLM couldn't find information
        if "not defined" in response.lower() or "not specified" in response.lower():
            return {
                "testcases": [],
                "error": f"No documentation found for '{query}'. The feature may not be in the uploaded knowledge base.",
                "empty_kb": False
            }

        # Try to parse JSON response with improved robustness
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            import re
            # First, try to clean code blocks
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
            
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            clean_response = clean_response.strip()
            
            # Try to parse cleaned response
            try:
                parsed = json.loads(clean_response)
                print("Successfully parsed JSON after cleaning code blocks")
            except json.JSONDecodeError:
                # If that fails, try to find JSON array or object with regex
                json_match = re.search(r'(\\{.*\\}|\\[.*\\])', clean_response, re.DOTALL)
                if json_match:
                    try:
                        extracted = json_match.group(0)
                        parsed = json.loads(extracted)
                        print("Successfully extracted and parsed JSON from response")
                    except json.JSONDecodeError as e2:
                        print(f"Failed to parse extracted JSON: {e2}")
                        raise
                else:
                    raise ValueError("Could not find valid JSON in response")

        # Ensure parsed is in the correct format
        # LLM should return an array of test cases
        if isinstance(parsed, list):
            testcases = parsed
            print(f"Parsed {len(testcases)} test cases")
        elif isinstance(parsed, dict):
            if "testcases" in parsed:
                testcases = parsed["testcases"]
                print(f"Extracted {len(testcases)} test cases from dict")
            else:
                # Treat single dict as one test case if it looks like one
                testcases = [parsed]
        else:
            print(f"Unexpected response structure: {type(parsed)}")
            testcases = []
        
        # Normalize testcase format for frontend compatibility
        for tc in testcases:
            # Convert preconditions from array to string if needed
            if isinstance(tc.get('preconditions'), list):
                tc['preconditions'] = '; '.join(tc['preconditions'])
            
            # Convert expected_result from dict to string if needed  
            if isinstance(tc.get('expected_result'), dict):
                tc['expected_result'] = str(tc['expected_result'])

        return {
            "testcases": testcases,
            "raw_context": [c.text[:100] for c in chunks]  # Truncate for size
        }
    except Exception as e:
        print(f"ERROR in generate_testcases_for_project: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log to file as well
        try:
            with open("backend_error.log", "a") as f:
                f.write(f"ERROR: {str(e)}\\n")
                f.write(traceback.format_exc())
                f.write("\\n" + "="*50 + "\\n")
        except:
            pass
        
        # Return a structured error response instead of raising 500
        error_msg = str(e)
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            return {
                "testcases": [],
                "error": "Invalid or Expired API Key. Please check your GROQ_API_KEY in .env file.",
                "empty_kb": False
            }
        
        return {
            "testcases": [],
            "error": f"Error generating test cases: {error_msg}",
            "empty_kb": False
        }
