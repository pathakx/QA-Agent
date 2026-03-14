
import json
import os
import glob
from backend.services.rag_service import retrieve_context
from backend.core.llm_client import LLMClient
from backend.core.models import UIElement

llm = LLMClient()

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
    # If a specific HTML path is provided, we should ideally parse it on the fly
    # or load its corresponding UI elements.
    # For now, to keep it simple and consistent with existing logic, 
    # we will just re-parse the HTML if provided.
    
    if html_path and os.path.exists(html_path):
         from backend.parsers.html_parser import parse_html
         return parse_html(html_path)

    if not os.path.exists(UI_PATH):
        return []

    import json
    with open(UI_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return [UIElement(**r) for r in raw]

def load_html(html_path=None):
    path = html_path if html_path else get_html_file_path()
    
    if not path or not os.path.exists(path):
        return "No HTML file found."
        
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(testcase: dict, html_path=None, collection_name=None):
    ui_elements = load_ui_elements(html_path)
    html = load_html(html_path)
    
    # Strictly use provided path, do not fallback to global directory
    html_abs_path = html_path
    
    if html_abs_path:
        # Clean up path for Windows
        html_abs_path = os.path.abspath(html_abs_path)
        # Properly format local file path for Windows
        target_url = f"file:///{html_abs_path.replace(os.sep, '/')}"
    else:
        # No HTML file found. Usage will likely fail if test expects specific elements.
        target_url = "about:blank"

    # Retrieve related documentation context based on test scenario text
    context_chunks = retrieve_context(testcase.get("scenario", ""), top_k=5, collection_name=collection_name)

    ui_table = "\n".join(
        [
            f"{e.tag} | {e.element_type} | name={e.name} | id={e.html_id} | selector={e.selector}"
            for e in ui_elements
        ]
    )

    context_text = "\n".join([c.text for c in context_chunks])

    # Using single-line comments instead of docstrings to avoid f-string issues
    return f"""
SYSTEM:
You are a Selenium (Python) automation expert. Generate a COMPLETE, RUNNABLE Python test script.

CRITICAL REQUIREMENTS:
1. DO NOT use unittest or pytest - create a simple standalone script
2. Use the EXACT selectors from the UI ELEMENT TABLE below
3. Include proper waits and error handling
4. Add meaningful assertions based on expected behavior
5. Navigate explicitly to the local test file: "{target_url}"
6. Include comments explaining each step
7. MANDATORY: Capture screenshot on ANY failure and save to specific path
8. MANDATORY: Call handle_alert(driver) after ANY button click that triggers JavaScript alerts

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
   - import os
   - import sys
   - import platform
   - import sys
   - import platform
   - # Video recording disabled for stability

2. Helper functions (REQUIRED - copy these exactly):
   
   def handle_alert(driver, accept=True):
       # Handle any JavaScript alerts that may appear
       try:
           alert = driver.switch_to.alert
           alert_text = alert.text
           print(f"Alert detected: {{alert_text}}")
           if accept:
               alert.accept()
           else:
               alert.dismiss()
           time.sleep(0.5)
           return alert_text
       except:
           return None
   
   def save_screenshot_on_failure(driver, test_id):
       try:
           screenshot_dir = os.path.abspath(f"test_results/{{test_id}}/screenshots")
           os.makedirs(screenshot_dir, exist_ok=True)
           timestamp = int(time.time())
           filepath = os.path.join(screenshot_dir, f"failure_{{timestamp}}.png")
           driver.save_screenshot(filepath)
           print(f"SCREENSHOT_PATH: {{filepath}}")
           # Wait for screenshot to be fully written
           time.sleep(2)
           return filepath
       except Exception as e:
           print(f"Screenshot failed: {{e}}")
           return None
   
   def print_metadata(driver):
       try:
           caps = driver.capabilities
           print(f"BROWSER: {{caps.get('browserName', 'unknown')}}")
           print(f"BROWSER_VERSION: {{caps.get('browserVersion', 'unknown')}}")
           print(f"OS_INFO: {{platform.system()}} {{platform.version()}}")
       except:
           pass

3. Main execution block with try-except-finally:
   - Setup Chrome driver with webdriver_manager
   - driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
   - Navigate to "{target_url}"
   - Print metadata at start
   
   # Video recording removed as per user request
   
   - Execute test steps from the test case
   - Add assertions for expected results
   - IMPORTANT: After clicking submit/login buttons, call handle_alert(driver) to dismiss success alerts
   - On ANY exception: Call save_screenshot_on_failure(driver, "{testcase.get('test_id', 'unknown')}")
   - Proper cleanup in finally block

4. For each test step:
   - Add a comment describing the step
   - Find elements using CSS selectors from UI table
   - Add explicit waits where needed
   - Include assertions to verify expected behavior
   - If clicking a button that shows an alert, immediately call handle_alert(driver)

5. Exception handling:
   - Wrap main logic in try-except
   - On exception: save screenshot BEFORE raising
   - Print exception details
   - Re-raise exception so script exits with non-zero code

6. Finally block:
   # Video recording cleanup removed
   - if 'driver' in locals():
       driver.quit()

6. End with comment: # Test Case: {testcase.get('test_id')}

EXAMPLE STRUCTURE:
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions as EC
# Video recording disabled
import time
import os
import platform

# ... helper functions ...

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    print_metadata(driver)
    
    # Start Recording
    # Video recording removed

    driver.get("{target_url}")
    
    # Test steps ...
    
    print("Test passed!")
except Exception as e:
    print(f"Test failed: {{e}}")
    if 'driver' in locals():
        save_screenshot_on_failure(driver, "{testcase.get('test_id')}")
    raise
finally:
    # Video recording cleanup removed
    if 'driver' in locals():
        driver.quit()


IMPORTANT:
- Return ONLY the Python code
- NO markdown formatting
- NO explanation text
- Make it immediately executable
- ALWAYS include screenshot capture on failure
- ALWAYS include handle_alert() helper and call it after buttons that trigger alerts
"""

def generate_selenium_script(testcase: dict, html_path=None, collection_name=None):
    prompt = build_prompt(testcase, html_path, collection_name)
    response = llm.generate(prompt)
    
    # Strip markdown code fences if present
    response = response.strip()
    if response.startswith('```python'):
        response = response[len('```python'):].strip()
    elif response.startswith('```'):
        response = response[3:].strip()
    
    if response.endswith('```'):
        response = response[:-3].strip()
    
    return response
