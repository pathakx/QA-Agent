import json
import os
from backend.services.rag_service import retrieve_context
from backend.core.llm_client import LLMClient
from backend.core.models import UIElement

llm = LLMClient()

HTML_PATH = "backend/data/html/checkout.html"
UI_PATH = "backend/data/html/ui_elements.json"

def load_ui_elements() -> list[UIElement]:
    if not os.path.exists(UI_PATH):
        return []

    import json
    with open(UI_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return [UIElement(**r) for r in raw]

def load_html():
    if not os.path.exists(HTML_PATH):
        return "No HTML uploaded yet."
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(testcase: dict):
    ui_elements = load_ui_elements()
    html = load_html()

    # Retrieve related documentation context based on test scenario text
    context_chunks = retrieve_context(testcase.get("scenario", ""), top_k=5)

    ui_table = "\n".join(
        [
            f"{e.tag} | {e.element_type} | name={e.name} | id={e.html_id} | selector={e.selector}"
            for e in ui_elements
        ]
    )

    context_text = "\n".join([c.text for c in context_chunks])

    return f"""
SYSTEM:
You are a Selenium (Python) expert. Generate a complete runnable Python test script using Selenium.

Rules:
- USE ONLY selectors provided in the UI table.
- DO NOT invent IDs, names, or fields.
- If a selector is missing for a required action, add a comment: # TODO: element not found in HTML
- Assertions MUST be included where expected behavior is defined.
- If the expected behavior is unclear or missing, comment: # Expected behavior not defined in documentation.
- If something is undefined in documentation, explicitly state: "Not defined in provided documentation".

CONTEXT DOCUMENTATION:
{context_text}

HTML STRUCTURE (TRUNCATED FOR REFERENCE):
{html[:1800]}

UI ELEMENT TABLE:
{ui_table}

TEST CASE INPUT:
{json.dumps(testcase, indent=2)}

OUTPUT FORMAT:
Return a standalone Python file containing:

- Proper imports
- webdriver manager setup
- Full executable Selenium flow based on the test steps
- Assertions based on expected_result
- Final comment: "# Test Case: {testcase.get('test_id')}"

Return ONLY the code. Nothing else.
"""

def generate_selenium_script(testcase: dict):
    prompt = build_prompt(testcase)
    return llm.generate(prompt)

def validate_script_against_ui(script: str):
    ui_elements = load_ui_elements()
    selectors = [e.selector for e in ui_elements]

    missing = []
    for line in script.split("\n"):
        if "find_element" in line:
            if not any(sel in line for sel in selectors):
                missing.append(line)

    return missing
