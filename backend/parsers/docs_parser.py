import json
import fitz  # pymupdf

def parse_txt_md(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def parse_pdf(path: str) -> str:
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text

def parse_json(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)

def parse_document(path: str) -> str:
    if path.endswith(".txt") or path.endswith(".md"):
        return parse_txt_md(path)
    if path.endswith(".pdf"):
        return parse_pdf(path)
    if path.endswith(".json"):
        return parse_json(path)
    raise Exception("Unsupported document format")
