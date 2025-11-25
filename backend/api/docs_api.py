import os
from fastapi import APIRouter, UploadFile, File
from backend.services.kb_service import ingest_document, ingest_html, get_kb_status, build_knowledge_base, reset_knowledge_base

router = APIRouter()

@router.post("/docs/upload")
async def upload_doc(file: UploadFile = File(...)):
    path = f"backend/data/docs/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"message": "Document uploaded"}

@router.post("/html/upload")
async def upload_html(file: UploadFile = File(...)):
    path = f"backend/data/html/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"message": "HTML uploaded"}

@router.get("/status")
def kb_status():
    return get_kb_status()

@router.get("/build")
def kb_build():
    return build_knowledge_base()

@router.post("/reset")
def kb_reset():
    return reset_knowledge_base()
