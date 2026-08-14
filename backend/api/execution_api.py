# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
from backend.services.execution_service import execute_test_script as _legacy_execute
from backend.auth.project_helpers import get_current_project
from backend.auth.dependencies import get_current_user
from backend.core.supabase_client import create_user_client
import uuid
import os
from datetime import datetime
from typing import Optional

router = APIRouter()


async def run_test_background(execution_id: str, test_id: str, script_content: str, project_id: str, token: str, retries: int = 0, engine: str = None):
    """
    Run test in background and update DB with results
    Emits real-time WebSocket events for progress tracking
    Supports retries on failure.
    """
    from backend.core.websocket_manager import emitter

    
    try:
        # Emit started event
        await emitter.emit_started(execution_id, test_id, project_id)
        
        # Emit initial progress
        await emitter.emit_progress(execution_id, 1, 5, "Starting test execution...")
        
        # Run the script with retries
        result = None
        for attempt in range(retries + 1):
            msg = "Running test script..." if attempt == 0 else f"Retry {attempt}/{retries}: Running script..."
            await emitter.emit_progress(execution_id, 2, 5, msg)
            
            result = await _legacy_execute(script_content)
            
            if result.status == 'passed':
                break
            
            if attempt < retries:
                await emitter.emit_progress(execution_id, 3, 5, f"Test failed: {result.error_message}. Retrying...")
        
        await emitter.emit_progress(execution_id, 4, 5, "Collecting results...")
        
        # Update DB
        client = create_user_client(token)
        client.table('test_executions').update({
            'status': result.status,
            'completed_at': datetime.utcnow().isoformat(),
            'duration_seconds': result.duration,
            'logs': result.logs,
            'error_message': result.error_message,
            'screenshot_path': result.screenshot_path,
            'video_path': result.video_path,
            'browser': result.browser,
            'browser_version': result.browser_version,
            'os_info': result.os_info
        }).eq('id', execution_id).execute()
        
        await emitter.emit_progress(execution_id, 5, 5, "Execution complete!")
        
        # Emit completed event
        await emitter.emit_completed(
            execution_id, 
            result.status, 
            result.duration, 
            result.error_message
        )
        
    except Exception as e:
        print(f"Background execution failed: {e}")
        try:
            client = create_user_client(token)
            client.table('test_executions').update({
                'status': 'error',
                'completed_at': datetime.utcnow().isoformat(),
                'error_message': str(e)
            }).eq('id', execution_id).execute()
        except:
            pass
        
        # Emit error completion
        await emitter.emit_completed(execution_id, 'error', 0, str(e))

@router.post("/execute/{test_id}")
async def execute_test(
    test_id: str,
    retries: int = 0,
    engine: Optional[str] = Query(None, description="Engine override: 'selenium' or 'playwright'"),
    background_tasks: BackgroundTasks = None,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """
    Execute a test case by ID.
    Fetches the latest script and runs it via the configured engine.
    Optional: retries (default 0), engine override ('selenium' or 'playwright')
    """
    client = create_user_client(current_user['token'])
    
    # 1. Get the script
    script_res = client.table('selenium_scripts').select('script_content').eq(
        'project_id', project['id']
    ).eq('test_case_id', test_id).order('created_at', desc=True).limit(1).execute()
    
    if not script_res.data:
        raise HTTPException(status_code=404, detail="No script found for this test case")
    
    script_content = script_res.data[0]['script_content']
    
    # 2. Create execution record
    execution_data = {
        'project_id': project['id'],
        'test_case_id': test_id,
        'status': 'running',
        'started_at': datetime.utcnow().isoformat()
    }
    
    exec_res = client.table('test_executions').insert(execution_data).execute()
    execution_id = exec_res.data[0]['id']
    
    # 3. Start execution in background (pass engine for dual-runtime routing)
    background_tasks.add_task(
        run_test_background, 
        execution_id,
        test_id,
        script_content,
        project['id'],
        current_user['token'],
        retries,
        engine
    )
    
    return {
        "execution_id": execution_id,
        "status": "running",
        "started_at": execution_data['started_at'],
        "engine": engine or "auto",
    }

@router.get("/executions/{execution_id}")
async def get_execution_status(
    execution_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Get status of a specific execution"""
    client = create_user_client(current_user['token'])
    
    res = client.table('test_executions').select('*').eq(
        'id', execution_id
    ).eq('project_id', project['id']).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    return res.data[0]

@router.get("/testcases/{test_id}/executions")
async def get_test_executions(
    test_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Get execution history for a test case"""
    client = create_user_client(current_user['token'])
    
    res = client.table('test_executions').select('*').eq(
        'project_id', project['id']
    ).eq('test_case_id', test_id).order('created_at', desc=True).execute()
    
    return {
        "executions": res.data or []
    }

@router.get("/executions")
async def get_all_executions(
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Get all executions for the current project"""
    client = create_user_client(current_user['token'])
    
    res = client.table('test_executions').select('*').eq(
        'project_id', project['id']
    ).order('created_at', desc=True).limit(100).execute()
    
    return {
        "executions": res.data or []
    }

@router.get("/executions/{execution_id}/screenshot")
async def get_execution_screenshot(
    execution_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Get screenshot for a specific execution"""
    client = create_user_client(current_user['token'])
    
    res = client.table('test_executions').select('screenshot_path').eq(
        'id', execution_id
    ).eq('project_id', project['id']).execute()
    
    if not res.data or not res.data[0].get('screenshot_path'):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    screenshot_path = res.data[0]['screenshot_path']
    
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot file not found on disk")
    
    return FileResponse(screenshot_path, media_type='image/png')

@router.get("/executions/{execution_id}/video")
async def get_execution_video(
    execution_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Get video for a specific execution"""
    client = create_user_client(current_user['token'])
    
    res = client.table('test_executions').select('video_path').eq(
        'id', execution_id
    ).eq('project_id', project['id']).execute()
    
    if not res.data or not res.data[0].get('video_path'):
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_path = res.data[0]['video_path']
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    
    media_type = 'video/webm' if video_path.endswith('.webm') else 'video/mp4'
    return FileResponse(video_path, media_type=media_type)


# ── Engine Info (Phase 4: Dual Runtime Diagnostics) ──

@router.get("/engine-info")
async def get_engine_info():
    """
    Get the current execution engine configuration.
    """
    return {
        "default_engine": "playwright",
        "playwright_enabled": True,
        "available_engines": ["playwright"],
        "note": "Migration complete",
    }
