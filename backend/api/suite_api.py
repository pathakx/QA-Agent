from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from backend.auth.project_helpers import get_current_project
from backend.auth.dependencies import get_current_user
from backend.core.supabase_client import create_user_client
from backend.services.batch_execution_service import execute_suite_background, execute_all_background
from typing import List, Optional
from pydantic import BaseModel
import uuid

router = APIRouter()

class TestSuiteCreate(BaseModel):
    name: str
    description: Optional[str] = None
    test_case_ids: List[str] = []

class TestSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_case_ids: Optional[List[str]] = None

@router.get("/suites")
async def list_suites(
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """List all test suites for the project"""
    client = create_user_client(current_user['token'])
    res = client.table('test_suites').select('*').eq('project_id', project['id']).order('created_at', desc=True).execute()
    return {"suites": res.data}

@router.post("/suites")
async def create_suite(
    suite: TestSuiteCreate,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Create a new test suite"""
    client = create_user_client(current_user['token'])
    
    # 1. Create Suite
    suite_data = {
        'project_id': project['id'],
        'name': suite.name,
        'description': suite.description
    }
    res = client.table('test_suites').insert(suite_data).execute()
    suite_id = res.data[0]['id']
    
    # 2. Add Tests
    if suite.test_case_ids:
        tests_data = [
            {'suite_id': suite_id, 'test_case_id': tid, 'execution_order': i}
            for i, tid in enumerate(suite.test_case_ids)
        ]
        client.table('suite_tests').insert(tests_data).execute()
        
    return {"suite_id": suite_id, "message": "Suite created successfully"}

@router.get("/suites/{suite_id}")
async def get_suite(
    suite_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Get suite details including tests"""
    client = create_user_client(current_user['token'])
    
    # Get suite metadata
    suite_res = client.table('test_suites').select('*').eq('id', suite_id).single().execute()
    if not suite_res.data:
        raise HTTPException(status_code=404, detail="Suite not found")
        
    # Get tests in suite
    tests_res = client.table('suite_tests').select('*').eq('suite_id', suite_id).order('execution_order').execute()
    
    return {
        **suite_res.data,
        "tests": tests_res.data
    }

@router.put("/suites/{suite_id}")
async def update_suite(
    suite_id: str,
    update_data: TestSuiteUpdate,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Update suite metadata or test list"""
    client = create_user_client(current_user['token'])
    
    # Update Metadata
    if update_data.name or update_data.description:
        data = {}
        if update_data.name: data['name'] = update_data.name
        if update_data.description: data['description'] = update_data.description
        client.table('test_suites').update(data).eq('id', suite_id).execute()
        
    # Update Tests (Replace all)
    if update_data.test_case_ids is not None:
        # Delete existing
        client.table('suite_tests').delete().eq('suite_id', suite_id).execute()
        
        # Add new
        if update_data.test_case_ids:
            tests_data = [
                {'suite_id': suite_id, 'test_case_id': tid, 'execution_order': i}
                for i, tid in enumerate(update_data.test_case_ids)
            ]
            client.table('suite_tests').insert(tests_data).execute()
            
    return {"message": "Suite updated successfully"}

@router.delete("/suites/{suite_id}")
async def delete_suite(
    suite_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Delete a test suite"""
    client = create_user_client(current_user['token'])
    client.table('test_suites').delete().eq('id', suite_id).execute()
    return {"message": "Suite deleted"}

@router.post("/suites/{suite_id}/execute")
async def execute_suite(
    suite_id: str,
    background_tasks: BackgroundTasks,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Execute all tests in a suite asynchronously"""
    background_tasks.add_task(
        execute_suite_background,
        suite_id,
        project['id'],
        current_user['token']
    )
    return {"message": "Suite execution started", "status": "running"}

@router.post("/execute-all")
async def execute_all_project_tests(
    background_tasks: BackgroundTasks,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Execute ALL tests in the project asynchronously"""
    background_tasks.add_task(
        execute_all_background,
        project['id'],
        current_user['token']
    )
    return {"message": "Full project execution started", "status": "running"}

@router.get("/batch-runs")
async def list_batch_runs(
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """List recent batch executions"""
    client = create_user_client(current_user['token'])
    res = client.table('batch_runs').select('*').eq('project_id', project['id']).order('created_at', desc=True).limit(20).execute()
    return {"runs": res.data}
