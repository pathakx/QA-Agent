from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
from backend.auth.project_helpers import get_current_project
from backend.core.supabase_client import create_user_client
import uuid

router = APIRouter()

# Pydantic Models
class TestCase(BaseModel):
    test_id: str
    feature: Optional[str] = None
    scenario: Optional[str] = None
    steps: Optional[List[str]] = None
    expected_result: Optional[str] = None
    
class TestCaseCreate(TestCase):
    pass

class TestCaseUpdate(BaseModel):
    feature: Optional[str] = None
    scenario: Optional[str] = None
    steps: Optional[List[str]] = None
    expected_result: Optional[str] = None

@router.get("/", response_model=List[dict])
def get_test_cases(
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Get all test cases for the current project"""
    client = create_user_client(user['token'])
    res = client.table('testcases').select('*').eq('project_id', project['id']).execute()
    return res.data

@router.post("/", response_model=dict)
def create_test_case(
    test_case: TestCaseCreate,
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Create a new test case"""
    client = create_user_client(user['token'])
    
    # Check if exists
    exists = client.table('testcases').select('id').eq('project_id', project['id']).eq('test_id', test_case.test_id).execute()
    if exists.data:
        raise HTTPException(status_code=400, detail=f"Test case {test_case.test_id} already exists")
    
    data = test_case.dict()
    data['project_id'] = project['id']
    
    res = client.table('testcases').insert(data).execute()
    return res.data[0]

@router.put("/{test_id}", response_model=dict)
def update_test_case(
    test_id: str,
    updates: TestCaseUpdate,
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Update an existing test case"""
    client = create_user_client(user['token'])
    
    # Filter out None values
    data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
        
    res = client.table('testcases').update(data).eq('project_id', project['id']).eq('test_id', test_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Test case not found")
        
    return res.data[0]

@router.delete("/all/clear")
def delete_all_test_cases(
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Delete all test cases for the current project"""
    client = create_user_client(user['token'])
    
    # Also delete associated scripts
    client.table('selenium_scripts').delete().eq('project_id', project['id']).execute()
    
    # Delete all test cases
    res = client.table('testcases').delete().eq('project_id', project['id']).execute()
    
    return {"message": "All test cases deleted", "count": len(res.data) if res.data else 0}

@router.delete("/{test_id}")
def delete_test_case(
    test_id: str,
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Delete a test case"""
    client = create_user_client(user['token'])
    
    # Also delete associated script
    client.table('selenium_scripts').delete().eq('project_id', project['id']).eq('test_case_id', test_id).execute()
    
    res = client.table('testcases').delete().eq('project_id', project['id']).eq('test_id', test_id).execute()
    
    if not res.data:
         # It might just be that it didn't exist, but delete is idempotent mostly. 
         # Supabase delete returns deleted rows.
         pass
         
    return {"message": f"Test case {test_id} deleted"}
