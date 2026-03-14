"""
Project helper functions for accessing project-specific resources
"""
from fastapi import Header, HTTPException, Depends
from backend.auth.dependencies import get_current_user
from backend.core.supabase_client import supabase, create_user_client
from backend.core.vectorstore import VectorStore
from typing import Optional

async def get_current_project(
    project_id: Optional[str] = Header(None, alias="project-id"),
    current_user = Depends(get_current_user)
) -> dict:
    """
    Verify that the project exists and belongs to the current user.
    Returns the project data.
    
    Raises:
        HTTPException 400: If  project-id header is missing
        HTTPException 403: If project doesn't belong to user
        HTTPException 404: If project not found
    """
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Missing project-id header. Please select a project."
        )
    
    try:
        # Create authenticated client
        user_client = create_user_client(current_user['token'])
        
        # Fetch project from Supabase
        response = user_client.table('projects').select('*').eq(
            'id', project_id
        ).eq('user_id', current_user['user_id']).eq('is_active', True).single().execute()
        
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or access denied"
            )
        
        return response.data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching project: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify project: {str(e)}"
        )

def get_project_vector_store(project: dict) -> VectorStore:
    """
    Get a VectorStore instance for the specified project.
    Uses the project's unique ChromaDB collection name.
    
    Args:
        project: Project data dict with 'chroma_collection_name' field
        
    Returns:
        VectorStore instance for the project
    """
    collection_name = project['chroma_collection_name']
    print(f"Getting vector store for project '{project['name']}' with collection '{collection_name}'")
    return VectorStore(collection_name=collection_name)

def get_project_data_path(project: dict, data_type: str) -> str:
    """
    Get the data directory path for a specific project.
    Creates project-specific directories if they don't exist.
    
    Args:
        project: Project data dict
        data_type: Type of data ('docs' or 'html')
        
    Returns:
        Path to the project-specific data directory
    """
    import os
    project_id = project['id']
    base_path = f"backend/data/projects/{project_id}/{data_type}"
    os.makedirs(base_path, exist_ok=True)
    return base_path
