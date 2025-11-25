from pydantic import BaseModel
from typing import Optional, Dict, Any

class DocumentMeta(BaseModel):
    id: str
    filename: str
    doc_type: str
    path: str

class Chunk(BaseModel):
    id: str
    doc_id: str
    text: str
    metadata: Dict[str, Any]

class UIElement(BaseModel):
    id: str
    tag: str
    element_type: str
    name: Optional[str] = None
    html_id: Optional[str] = None
    text: Optional[str] = None
    selector: str
