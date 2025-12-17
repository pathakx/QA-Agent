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

    ui_table = "\\n".join(
        [
            f"{e.tag} | {e.element_type} | name={e.name} | id={e.html_id} | selector={e.selector}"
            for e in ui_elements
        ]
    )

    context_text = "\\n".join([c.text for c in context_chunks])

    return f"""
SYSTEM:
You are a Selenium (Python) automation expert. Generate a COMPLETE, RUNNABLE Python test script.

CRITICAL REQUIREMENTS:
1. DO NOT use unittest or pytest - create a simple standalone script
2. Use the EXACT selectors from the UI ELEMENT TABLE below
3. Include proper waits and error handling
4. Add meaningful assertions based on expected behavior
5. If an element is not in the UI table, check the HTML structure or add a TODO comment
6. Use file:// protocol for local HTML files (e.g., "file:///path/to/checkout.html")
7. Include comments explaining each step

CONTEXT DOCUMENTATION:
{context_text}

FULL HTML STRUCTURE:
{html}

UI ELEMENT TABLE (These are the parsed form elements):
{ui_table}

TEST CASE TO IMPLEMENT:
{json.dumps(testcase, indent=2)}

REQUIRED OUTPUT FORMAT:
Generate a complete Python script with:

1. Imports:
   - from selenium import webdriver
   - from selenium.webdriver.common.by import By
   - from selenium.webdriver.chrome.service import Service
   - from webdriver_manager.chrome import ChromeDriverManager
   - from selenium.webdriver.support.ui import WebDriverWait
   - from selenium.webdriver.support import expected_conditions as EC
   - import time

2. Main execution block with try-except-finally:
   - Setup Chrome driver with webdriver_manager
   - Navigate to "file:///" + "absolute_path_to_checkout.html" (add TODO to replace path)
   - Execute test steps from the test case
   - Add assertions for expected results
   - Proper cleanup in finally block

3. For each test step:
   - Add a comment describing the step
   - Find elements using CSS selectors from UI table
   - Add explicit waits where needed
   - Include assertions to verify expected behavior

4. Assertions should check:
   - Element visibility/state changes
   - Text content where applicable
   - Calculated values (like discounts, totals)
   - Success/error messages

5. End with comment: # Test Case: {testcase.get('test_id')}

IMPORTANT:
- Return ONLY the Python code
- NO markdown formatting
- NO explanation text
- Make it immediately executable
"""

def generate_selenium_script(testcase: dict):
    prompt = build_prompt(testcase)
    raw_response = llm.generate(prompt)
    
    # Clean up markdown
    clean_response = raw_response.strip()
    if clean_response.startswith("```python"):
        clean_response = clean_response[9:]
    elif clean_response.startswith("```"):
        clean_response = clean_response[3:]
    
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]
        
    return clean_response.strip()

def validate_script_against_ui(script: str):
    ui_elements = load_ui_elements()
    selectors = [e.selector for e in ui_elements]

    missing = []
    for line in script.split("\\n"):
        if "find_element" in line:
            if not any(sel in line for sel in selectors):
                missing.append(line)

    return missing
