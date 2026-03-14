from fastapi import APIRouter, Depends, HTTPException
from backend.agent.workflow import app as agent_app
from backend.auth.project_helpers import get_current_project
from backend.auth.dependencies import get_current_user
import asyncio

router = APIRouter()

# Track running tasks: project_id -> asyncio.Task
RUNNING_TASKS = {}

async def run_autonomous_mode(project_id: str, access_token: str):
    """Run the LangGraph workflow"""
    from backend.core.websocket_manager import emitter
    
    await emitter.emit_agent_log(project_id, f"🚀 Starting Autonomous Mode for Project {project_id}")
    
    inputs = {
        "project_id": project_id,
        "access_token": access_token,
        "file_structure": "",
        "test_plan": [],
        "generated_scripts": [],
        "execution_results": [],
        "final_report": "",
        "errors": [],
        "html_path": None,
        "chroma_collection_name": None
    }
    
    config = {"recursion_limit": 50}
    
    try:
        # Invoke the graph
        # We use ainvoke for async execution
        result = await agent_app.ainvoke(inputs, config=config)
        
        await emitter.emit_agent_log(project_id, "🏁 Autonomous Run Completed!")
        
        if result.get('errors'):
            for err in result['errors']:
                await emitter.emit_agent_log(project_id, f"Error: {err}", level="error")
        
        if result.get('final_report'):
            await emitter.emit_agent_log(project_id, "📋 Report Generated")
            
    except asyncio.CancelledError:
        print(f"Autonomous run for {project_id} cancelled.")
        await emitter.emit_agent_log(project_id, "🛑 Autonomous Run Stopped by User", level="warning")
    except Exception as e:
        print(f"Autonomous Run Failed: {e}")
        await emitter.emit_agent_log(project_id, f"Autonomous Run Failed: {e}", level="error")
    finally:
        # Cleanup task helper
        if project_id in RUNNING_TASKS:
            del RUNNING_TASKS[project_id]

@router.post("/start")
async def start_autonomous(
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Start the autonomous testing agent"""
    if project['id'] in RUNNING_TASKS and not RUNNING_TASKS[project['id']].done():
        return {"status": "already_running", "message": "Agent is already running for this project"}

    # Launch background task
    task = asyncio.create_task(run_autonomous_mode(project['id'], user['token']))
    RUNNING_TASKS[project['id']] = task
    
    return {"status": "started", "project_id": project['id']}

@router.post("/stop")
async def stop_autonomous(
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Stop the autonomous testing agent"""
    task = RUNNING_TASKS.get(project['id'])
    
    if task and not task.done():
        print(f"Stopping task for project {project['id']}...")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass # Expected
        return {"status": "stopped", "message": "Agent stopped successfully"}
    
    return {"status": "not_running", "message": "No running agent found for this project"}
