from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
from backend.auth.project_helpers import get_current_project
from backend.core.supabase_client import create_user_client

router = APIRouter()

class SeleniumScript(BaseModel):
    test_case_id: str
    script_content: str

@router.get("/", response_model=List[dict])
def get_scripts(
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Get all scripts for the current project"""
    client = create_user_client(user['token'])
    res = client.table('selenium_scripts').select('*').eq('project_id', project['id']).execute()
    return res.data

@router.post("/", response_model=dict)
def create_or_update_script(
    script: SeleniumScript,
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Create or update a Selenium script for a test case"""
    client = create_user_client(user['token'])
    
    data = script.dict()
    data['project_id'] = project['id']
    
    # Upsert based on project_id and test_case_id
    res = client.table('selenium_scripts').upsert(data, on_conflict='project_id,test_case_id').execute()
    return res.data[0]

@router.delete("/{test_case_id}")
def delete_script(
    test_case_id: str,
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Delete a script"""
    client = create_user_client(user['token'])
    res = client.table('selenium_scripts').delete().eq('project_id', project['id']).eq('test_case_id', test_case_id).execute()
    return {"message": f"Script for {test_case_id} deleted"}
