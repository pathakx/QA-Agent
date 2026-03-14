"""
Project Management API
Handles CRUD operations for user projects with isolated ChromaDB collections
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
from backend.core.supabase_client import supabase, create_user_client
from typing import Optional
import time

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

@router.post("/projects")
async def create_project(
    req: ProjectCreate,
    current_user = Depends(get_current_user)
):
    """Create a new project for the current user"""
    try:
        # Generate unique collection name
        timestamp = int(time.time())
        user_id_short = current_user['user_id'][:8]  # Use first 8 chars of UUID
        collection_name = f"user_{user_id_short}_proj_{timestamp}"
        
        # Create authenticated client
        user_client = create_user_client(current_user['token'])
        
        # Create project in Supabase
        response = user_client.table('projects').insert({
            'user_id': current_user['user_id'],
            'name': req.name,
            'description': req.description,
            'chroma_collection_name': collection_name,
            'is_active': True
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        project = response.data[0]
        
        return {
            "id": project['id'],
            "name": project['name'],
            "description": project['description'],
            "chroma_collection_name": project['chroma_collection_name'],
            "created_at": project['created_at']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_str = str(e).lower()
        
        print(f"❌ Error creating project: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Check for common database issues
        if "42501" in error_str or "permission denied" in error_str or "insufficient privilege" in error_str:
            raise HTTPException(
                status_code=500,
                detail="Database tables not set up. Please run supabase_schema.sql in your Supabase SQL Editor. See ERROR_FIX_DATABASE.md for instructions."
            )
        elif "42p01" in error_str or "relation" in error_str and "does not exist" in error_str:
            raise HTTPException(
                status_code=500,
                detail="Database table 'projects' does not exist. Please run supabase_schema.sql in Supabase SQL Editor."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@router.get("/projects")
async def get_user_projects(current_user = Depends(get_current_user)):
    """Get all active projects for the current user"""
    print(f"DEBUG: Fetching projects for user {current_user.get('user_id')}...")
    try:
        user_client = create_user_client(current_user['token'])
        
        response = user_client.table('projects').select('*').eq(
            'user_id', current_user['user_id']
        ).eq('is_active', True).order('created_at', desc=True).execute()
        
        print(f"DEBUG: Found {len(response.data or [])} projects")
        return {
            "projects": response.data or []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Error fetching projects: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific project by ID"""
    try:
        user_client = create_user_client(current_user['token'])
        
        response = user_client.table('projects').select('*').eq(
            'id', project_id
        ).eq('user_id', current_user['user_id']).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return response.data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {str(e)}")

@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    req: ProjectUpdate,
    current_user = Depends(get_current_user)
):
    """Update a project's details"""
    try:
        # Build update data
        update_data = {}
        if req.name is not None:
            update_data['name'] = req.name
        if req.description is not None:
            update_data['description'] = req.description
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        user_client = create_user_client(current_user['token'])
        
        # Update in Supabase
        response = user_client.table('projects').update(update_data).eq(
            'id', project_id
        ).eq('user_id', current_user['user_id']).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "success": True,
            "message": "Project updated successfully",
            "project": response.data[0]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user = Depends(get_current_user)
):
    """Soft delete a project (sets is_active to False)"""
    try:
        user_client = create_user_client(current_user['token'])
        
        # Soft delete - set is_active to False
        response = user_client.table('projects').update({
            'is_active': False
        }).eq('id', project_id).eq('user_id', current_user['user_id']).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # TODO: Optionally delete ChromaDB collection
        # collection_name = response.data[0]['chroma_collection_name']
        # Delete from ChromaDB here
        
        return {
            "success": True,
            "message": "Project deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@router.get("/projects/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    current_user = Depends(get_current_user)
):
    """Get statistics for a specific project"""
    try:
        user_client = create_user_client(current_user['token'])
        
        # Verify project ownership
        project_response = user_client.table('projects').select('id').eq(
            'id', project_id
        ).eq('user_id', current_user['user_id']).single().execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get counts
        testcases_response = user_client.table('testcases').select(
            'id', count='exact'
        ).eq('project_id', project_id).execute()
        
        scripts_response = user_client.table('selenium_scripts').select(
            'id', count='exact'
        ).eq('project_id', project_id).execute()
        
        kb_files_response = user_client.table('kb_files').select(
            'id', count='exact'
        ).eq('project_id', project_id).execute()
        
        return {
            "project_id": project_id,
            "testcases_count": testcases_response.count or 0,
            "scripts_count": scripts_response.count or 0,
            "kb_files_count": kb_files_response.count or 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project stats: {str(e)}")
