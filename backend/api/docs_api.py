"""
Knowledge Base API with project isolation
All operations are scoped to the current project
"""
import os
from fastapi import APIRouter, UploadFile, File, Depends
from backend.auth.project_helpers import get_current_project, get_project_vector_store, get_project_data_path
from backend.services.project_kb_service import (
    get_project_kb_status,
    build_project_knowledge_base,
    reset_project_knowledge_base,
    get_project_paths # Export this too just in case
)
from backend.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/docs/upload")
async def upload_doc(
    file: UploadFile = File(...),
    project: dict = Depends(get_current_project)
):
    """Upload a document to the current project's knowledge base"""
    # Get project-specific docs path
    docs_path = get_project_data_path(project, 'docs')
    
    file_path = os.path.join(docs_path, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    return {
        "message": "Document uploaded successfully",
        "filename": file.filename,
        "project": project['name']
    }

@router.post("/html/upload")
async def upload_html(
    file: UploadFile = File(...),
    project: dict = Depends(get_current_project)
):
    """Upload HTML file to the current project"""
    # Get project-specific HTML path
    html_path = get_project_data_path(project, 'html')
    
    file_path = os.path.join(html_path, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    return {
        "message": "HTML uploaded successfully",
        "filename": file.filename,
        "project": project['name']
    }

@router.get("/status")
def kb_status(project: dict = Depends(get_current_project)):
    """Get knowledge base status for the current project"""
    vector_store = get_project_vector_store(project)
    return get_project_kb_status(project, vector_store)

@router.get("/build")
def kb_build(project: dict = Depends(get_current_project)):
    """Build knowledge base for the current project"""
    vector_store = get_project_vector_store(project)
    return build_project_knowledge_base(project, vector_store)

@router.post("/reset")
def kb_reset(
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Reset knowledge base for the current project"""
    vector_store = get_project_vector_store(project)
    
    # We need the token to authenticate with Supabase RLS for deletions
    token = user.get('token')
    
    return reset_project_knowledge_base(project, vector_store, access_token=token)
