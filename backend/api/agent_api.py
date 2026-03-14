"""
Agent API with project isolation
All test case and script generation operations are scoped to the current project
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.services.project_testcase_service import generate_testcases_for_project
from backend.services.selenium_service import generate_selenium_script
from backend.auth.project_helpers import get_current_project, get_project_vector_store
from backend.auth.dependencies import get_current_user
from backend.core.supabase_client import create_user_client
from backend.services.project_kb_service import get_project_paths
import json
import glob
import os

router = APIRouter()

class TestCaseRequest(BaseModel):
    query: str

class ScriptRequest(BaseModel):
    testcase: dict

@router.post("/testcases")
def testcase_generation(
    req: TestCaseRequest,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Generate test cases using the current project's knowledge base"""
    try:
        # Get project-specific vector store
        vector_store = get_project_vector_store(project)
        
        # Fetch existing test cases to prevent duplication
        user_client = create_user_client(current_user['token'])
        # Optimize: Only fetch id, test_id, and scenario to minimize payload
        existing_res = user_client.table('testcases').select('test_id, scenario').eq('project_id', project['id']).execute()
        existing_tcs = existing_res.data if existing_res.data else []
        
        # Generate test cases
        result = generate_testcases_for_project(
            req.query,
            vector_store,
            project_name=project['name'],
            existing_testcases=existing_tcs
        )
        
        # Save test cases to Supabase if generation was successful
        if result.get('testcases') and not result.get('error'):
            user_client = create_user_client(current_user['token'])
            
            for tc in result['testcases']:
                # Prepare data for Supabase
                tc_data = {
                    'project_id': project['id'],
                    'test_id': tc.get('test_id'),
                    'feature': tc.get('feature'),
                    'scenario': tc.get('scenario') or tc.get('scenerio'), # Handle potential typo in LLM output
                    'preconditions': tc.get('preconditions'),
                    'steps': tc.get('steps', []), # storing as JSONB automatically
                    'test_data': tc.get('test_data', {}),
                    'expected_result': tc.get('expected_result'),
                    'grounded_in': tc.get('grounded_in', [])
                }
                
                # Upsert into Supabase (requires unique constraint on project_id, test_id)
                # We use on_conflict parameter if needed, or just insert. 
                # Since we don't have a simple unique constraint index that upsert relies on without explicit conflict_target, 
                # we'll try to insert or update.
                
                # Check existence first to emulate upsert or use upsert if configured in DB
                existing = user_client.table('testcases').select('id').eq('project_id', project['id']).eq('test_id', tc.get('test_id')).execute()
                
                if existing.data:
                    # Update
                    user_client.table('testcases').update(tc_data).eq('id', existing.data[0]['id']).execute()
                else:
                    # Insert
                    user_client.table('testcases').insert(tc_data).execute()
        
        # Add project info to response
        result['project_name'] = project['name']
        result['project_id'] = project['id']
        
        return result
        
    except Exception as e:
        print(f"Error in testcase generation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate test cases: {str(e)}")

@router.get("/testcases")
def get_all_testcases(
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Retrieve all saved test cases for the current project"""
    try:
        user_client = create_user_client(current_user['token'])
        
        response = user_client.table('testcases').select('*').eq(
            'project_id', project['id']
        ).order('created_at', desc=True).execute()
        
        return {
            "testcases": response.data or [],
            "project_name": project['name']
        }
    except Exception as e:
        print(f"Error fetching testcases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/testcases/{test_id}")
def delete_testcase(
    test_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Delete a test case by test_id (scoped to project)"""
    try:
        user_client = create_user_client(current_user['token'])
        
        # Delete using test_id AND project_id to ensure safety
        response = user_client.table('testcases').delete().eq(
            'test_id', test_id
        ).eq('project_id', project['id']).execute()
        
        return {"success": True}
    except Exception as e:
        print(f"Error deleting testcase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/selenium-script")
def create_script(
    req: ScriptRequest,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Generate Selenium script for a test case"""
    try:
        # Determine HTML path for project
        paths = get_project_paths(project)
        html_dir = paths['html_path']
        html_path = None
        
        if os.path.exists(html_dir):
            html_files = glob.glob(os.path.join(html_dir, "*.html"))
            if html_files:
                html_path = os.path.abspath(html_files[0])
                print(f"Using project HTML file: {html_path}")
        
        script = generate_selenium_script(req.testcase, html_path=html_path, collection_name=project.get('chroma_collection_name'))
        
        # Save script to database with project_id
        test_id = req.testcase.get('test_id')
        if test_id and script:
            user_client = create_user_client(current_user['token'])
            
            user_client.table('selenium_scripts').insert({
                'project_id': project['id'],
                'test_case_id': test_id,
                'script_content': script
            }).execute()
        
        return {
            "script": script,
            "project_name": project['name']
        }
    except Exception as e:
        print(f"Error creating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/selenium-scripts")
def get_all_scripts(
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Retrieve all saved selenium scripts for the current project"""
    try:
        user_client = create_user_client(current_user['token'])
        
        response = user_client.table('selenium_scripts').select('*').eq(
            'project_id', project['id']
        ).order('created_at', desc=True).execute()
        
        return {
            "scripts": response.data or [],
            "project_name": project['name']
        }
    except Exception as e:
        print(f"Error fetching scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/selenium-scripts/{test_case_id}")
def get_script_by_id(
    test_case_id: str,
    project: dict = Depends(get_current_project),
    current_user = Depends(get_current_user)
):
    """Retrieve script for a specific test case"""
    try:
        user_client = create_user_client(current_user['token'])
        
        # Get most recent script for this test case in this project
        response = user_client.table('selenium_scripts').select('*').eq(
            'project_id', project['id']
        ).eq('test_case_id', test_case_id).order('created_at', desc=True).limit(1).execute()
        
        script_data = response.data[0] if response.data else None
        
        return {
            "script": script_data,
            "project_name": project['name']
        }
    except Exception as e:
        print(f"Error fetching script: {e}")
        raise HTTPException(status_code=500, detail=str(e))
