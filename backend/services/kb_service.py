import os
import uuid
import json
from backend.core.models import DocumentMeta
from backend.parsers.docs_parser import parse_document
from backend.parsers.text_chunker import chunk_text
from backend.parsers.html_parser import parse_html
from backend.core.vectorstore import VectorStore

vector_store = VectorStore()

DOC_PATH = "backend/data/docs/"
HTML_PATH = "backend/data/html/ui_elements.json"

def ingest_document(file_path: str) -> DocumentMeta:
    filename = os.path.basename(file_path)
    doc_id = str(uuid.uuid4())

    text = parse_document(file_path)
    chunks = chunk_text(doc_id, text)
    vector_store.add_chunks(chunks)

    return DocumentMeta(id=doc_id, filename=filename, doc_type=filename.split(".")[-1], path=file_path)

def ingest_html(file_path: str):
    elements = parse_html(file_path)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        json.dump([e.dict() for e in elements], f, indent=2)
    return elements

def get_kb_status():
    doc_files = os.listdir(DOC_PATH) if os.path.exists(DOC_PATH) else []
    html_files = os.listdir("backend/data/html/") if os.path.exists("backend/data/html/") else []
    return {
        "doc_count": len(doc_files),
        "doc_files": doc_files,
        "html_parsed": os.path.exists(HTML_PATH),
        "html_files": [f for f in html_files if f.endswith(".html") or f.endswith(".htm")]
    }

def build_knowledge_base():
    # Ingest Docs
    if os.path.exists(DOC_PATH):
        for f in os.listdir(DOC_PATH):
            ingest_document(os.path.join(DOC_PATH, f))
    
    # Ingest HTML
    html_dir = "backend/data/html/"
    if os.path.exists(html_dir):
        for f in os.listdir(html_dir):
            if f.endswith(".html") or f.endswith(".htm"):
                ingest_html(os.path.join(html_dir, f))
    return {"status": "built"}

def reset_knowledge_base():
    # Clear Docs
    if os.path.exists(DOC_PATH):
        for f in os.listdir(DOC_PATH):
            os.remove(os.path.join(DOC_PATH, f))
            
    # Clear HTML
    html_dir = "backend/data/html/"
    if os.path.exists(html_dir):
        for f in os.listdir(html_dir):
            os.remove(os.path.join(html_dir, f))

    # Reset Vector DB
    vector_store.reset()
    return {"status": "reset"}
