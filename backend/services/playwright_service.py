"""
Playwright Script Generation Service
=======================================

Generates Playwright (Python) automation scripts from test cases,
mirroring the existing Selenium script generation in selenium_service.py.

Design Decisions:
- Uses the SAME LLM, RAG context, and UI element parsing as Selenium.
- Generates async Playwright scripts using playwright.sync_api
  (sync API for subprocess compatibility — same as Selenium's sync driver).
- Uses data-testid selectors when available (superior to CSS selectors).
- Includes built-in screenshot capture, video recording metadata,
  and Playwright-native waiting (no explicit waits needed).
- Scripts are standalone — no dependency on the automation package.
  They run in isolated subprocesses via dual_engine.py.

Script Output Format:
- Uses SAME stdout metadata format as Selenium scripts
  (SCREENSHOT_PATH:, VIDEO_PATH:, BROWSER:, etc.)
  so the execution_service parser works identically.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from backend.services.rag_service import retrieve_context
from backend.core.llm_client import LLMClient
import glob
from backend.core.models import UIElement

HTML_DIR = "backend/data/html"
UI_PATH = "backend/data/html/ui_elements.json"

def get_html_file_path():
    """Find the first HTML file in the directory"""
    if not os.path.exists(HTML_DIR):
        return None
    
    files = glob.glob(os.path.join(HTML_DIR, "*.html"))
    if files:
        return os.path.abspath(files[0])
    return None

def load_ui_elements(html_path=None) -> list[UIElement]:
    if html_path and os.path.exists(html_path):
         from backend.parsers.html_parser import parse_html
         return parse_html(html_path)

    if not os.path.exists(UI_PATH):
        return []

    with open(UI_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return [UIElement(**r) for r in raw]

def load_html(html_path=None):
    path = html_path if html_path else get_html_file_path()
    
    if not path or not os.path.exists(path):
        return "No HTML file found."
        
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

llm = LLMClient()


def build_playwright_prompt(
    testcase: dict,
    html_path: Optional[str] = None,
    collection_name: Optional[str] = None,
) -> str:
    """
    Build a prompt for the LLM to generate a Playwright Python script.
    
    Uses the same UI elements, HTML, and RAG context as the Selenium prompt,
    but instructs the LLM to generate Playwright code instead.
    
    Args:
        testcase: Test case dict with test_id, scenario, steps, expected_result
        html_path: Path to the HTML file under test
        collection_name: Vector store collection for RAG retrieval
    
    Returns:
        Complete prompt string for the LLM
    """
    ui_elements = load_ui_elements(html_path)
    html = load_html(html_path)

    # Resolve target URL
    html_abs_path = html_path
    if html_abs_path:
        import pathlib
        html_abs_path = os.path.abspath(html_abs_path)
        # Proper file:// URI generation across OSes (handles Windows drives correctly)
        target_url = pathlib.Path(html_abs_path).as_uri()
    else:
        target_url = "about:blank"

    # RAG context
    context_chunks = retrieve_context(
        testcase.get("scenario", ""),
        top_k=5,
        collection_name=collection_name,
    )

    ui_table = "\n".join(
        [
            f"{e.tag} | {e.element_type} | name={e.name} | id={e.html_id} | "
            f"selector={e.selector} | data-testid={getattr(e, 'data_testid', 'none')}"
            for e in ui_elements
        ]
    )

    context_text = "\n".join([c.text for c in context_chunks])

    test_id = testcase.get("test_id", "unknown")

    return f"""
SYSTEM:
You are a Playwright (Python) automation expert. Generate a COMPLETE, RUNNABLE Python test script
using the Playwright SYNC API (from playwright.sync_api import sync_playwright).

CRITICAL REQUIREMENTS:
1. DO NOT use unittest, pytest, or async - create a simple standalone SYNCHRONOUS script
2. Use the Playwright sync_api (sync_playwright) — NOT async_playwright
3. Use data-testid selectors when available (page.get_by_test_id("xxx"))
4. Use semantic locators when possible: get_by_role, get_by_label, get_by_text, get_by_placeholder
5. Fall back to CSS selectors ONLY when no semantic locator is available
6. Playwright has BUILT-IN auto-waiting — do NOT add time.sleep() or explicit waits
7. Navigate explicitly to the local test file: "{target_url}"
8. Include comments explaining each step
9. MANDATORY: Capture screenshot on ANY failure and save to specific path
10. Print metadata in the EXACT format shown below (for result parsing)

CONTEXT DOCUMENTATION:
{context_text}

FULL HTML STRUCTURE:
{html}

UI ELEMENT TABLE (parsed form elements — prefer data-testid selectors):
{ui_table}

TEST CASE TO IMPLEMENT:
{json.dumps(testcase, indent=2)}

REQUIRED OUTPUT FORMAT:
Generate a complete Python script with:

1. Imports:
   from playwright.sync_api import sync_playwright
   import os
   import time
   import platform

2. Helper functions (REQUIRED — copy these exactly):

   def save_screenshot_on_failure(page, test_id):
       try:
           screenshot_dir = os.path.abspath(f"test_results/{{test_id}}/screenshots")
           os.makedirs(screenshot_dir, exist_ok=True)
           timestamp = int(time.time())
           filepath = os.path.join(screenshot_dir, f"failure_{{timestamp}}.png")
           page.screenshot(path=filepath, full_page=True)
           print(f"SCREENSHOT_PATH: {{filepath}}")
           return filepath
       except Exception as e:
           print(f"Screenshot failed: {{e}}")
           return None

   def print_metadata(browser):
       try:
           print(f"BROWSER: {{browser.browser_type.name}}")
           print(f"BROWSER_VERSION: {{browser.version}}")
           print(f"OS_INFO: {{platform.system()}} {{platform.version()}}")
       except:
           pass

3. Main execution block:

   with sync_playwright() as p:
       browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox"])
       context = browser.new_context()
       page = context.new_page()
       
       try:
           print_metadata(browser)
           
           # Verify HTML file exists before navigating to prevent ERR_FILE_NOT_FOUND
           target_path = r"{html_abs_path}"
           if target_path and target_path != "None" and not os.path.exists(target_path):
               raise FileNotFoundError(f"ERR_FILE_NOT_FOUND: Expected HTML file at '{{target_path}}' does not exist. Ensure the generated checkout.html is actually created and saved in the project's html directory before Playwright tries to open it.")
           
           page.goto("{target_url}")
           
           # Test steps using Playwright locators:
           # - page.get_by_test_id("username-input").fill("admin")
           # - page.get_by_role("button", name="Login").click()
           # - page.get_by_label("Email").fill("test@example.com")
           # - page.locator("#submit-btn").click()  # CSS fallback
           
           # Assertions using expect() or manual checks:
           # - assert page.get_by_test_id("result").text_content() == "Success"
           # - assert page.url == "expected_url"
           
           # Handle JavaScript dialogs BEFORE triggering them:
           # page.on("dialog", lambda dialog: dialog.accept())
           # page.get_by_role("button", name="Show Alert").click()
           
           print("Test passed!")
           
       except Exception as e:
           print(f"Test failed: {{e}}")
           save_screenshot_on_failure(page, "{test_id}")
           raise
           
       finally:
           context.close()
           browser.close()

4. For each test step:
   - Add a comment describing the step
   - Use the BEST available locator strategy:
     Priority: data-testid > role > label > placeholder > text > CSS selector
   - Playwright auto-waits — do NOT use time.sleep()
   - Use page.wait_for_selector() ONLY for dynamic content that loads after an action
   - Include assertions to verify expected behavior

5. For dialog/alert handling:
   - Set up dialog handler BEFORE the action that triggers it:
     page.on("dialog", lambda dialog: dialog.accept())
     page.get_by_role("button", name="Show Alert").click()

6. For HTML5 native form validation (CRITICAL — read carefully):
   - Browser-native validation tooltips ("Please include an '@'...", "Please fill out this field", etc.)
     are NOT DOM elements — they are rendered by the browser's own UI layer.
   - DO NOT try to assert their visibility with .is_visible() or .text_content() — those will ALWAYS fail.
   - NEVER pass a Locator object as the second argument to page.evaluate() — it is not serializable
     and will arrive as `undefined` in JavaScript, causing a TypeError.
   - Instead, call .evaluate() DIRECTLY ON the Locator (locator.evaluate()), which correctly
     resolves to the underlying DOM element:
     # ✅ CORRECT: call evaluate on the locator itself
     email_field = page.get_by_label("Email Address")
     is_invalid = email_field.evaluate("el => !el.checkValidity()")
     assert is_invalid, "Expected email field to be invalid"
     # Read the browser's validation message:
     msg = email_field.evaluate("el => el.validationMessage")
     assert msg != "", f"Expected a validation message, got: '{{msg}}'"
   - Alternatively, verify that the FORM was NOT submitted (URL did not change, success element absent):
     page.get_by_role("button", name="Pay Now").click()
     # Form should stay on same page due to validation blocking submission
     assert page.url == expected_url, "Form should not have submitted with invalid data"

7. For form interactions:
   - page.get_by_label("Username").fill("admin")
   - page.get_by_test_id("password-input").fill("password123")
   - page.get_by_role("combobox").select_option("admin")
   - page.get_by_role("checkbox").check()

IMPORTANT:
- Return ONLY the Python code
- NO markdown formatting
- NO explanation text
- Make it immediately executable
- ALWAYS include screenshot capture on failure
- Use sync_playwright (NOT async)
- Playwright auto-waits — NO time.sleep() for element availability
- Print SCREENSHOT_PATH, BROWSER, BROWSER_VERSION, OS_INFO in the exact format shown
"""


def generate_playwright_script(
    testcase: dict,
    html_path: Optional[str] = None,
    collection_name: Optional[str] = None,
) -> str:
    """
    Generate a Playwright Python script for a test case.
    
    Mirror of generate_selenium_script() for the Playwright engine.
    
    Args:
        testcase: Test case dict
        html_path: Path to the HTML file under test
        collection_name: Vector store collection for RAG
    
    Returns:
        Complete Python script string (Playwright sync API)
    """
    prompt = build_playwright_prompt(testcase, html_path, collection_name)
    response = llm.generate(prompt)

    # Strip markdown code fences if present
    response = response.strip()
    if response.startswith("```python"):
        response = response[len("```python"):].strip()
    elif response.startswith("```"):
        response = response[3:].strip()

    if response.endswith("```"):
        response = response[:-3].strip()

    return response
