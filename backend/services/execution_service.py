import subprocess
import os
import tempfile
import time
import asyncio
from datetime import datetime
import sys

class ExecutionResult:
    def __init__(self, status, logs, duration, error_message=None, screenshot_path=None, video_path=None, browser=None, browser_version=None, os_info=None):
        self.status = status
        self.logs = logs
        self.duration = duration
        self.error_message = error_message
        self.screenshot_path = screenshot_path
        self.video_path = video_path
        self.browser = browser
        self.browser_version = browser_version
        self.os_info = os_info

async def execute_test_script(script_content: str) -> ExecutionResult:
    """
    Executes a Selenium script asynchronously and returns the result.
    Uses threading to avoid Windows asyncio subprocess limitations.
    """
    start_time = time.time()
    tmp_path = None
    
    def run_script_sync():
        """Synchronous script runner for thread execution"""
        nonlocal tmp_path
        try:
            # Create a temporary file for the script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(script_content)
                tmp_path = tmp_file.name

            print(f"[EXEC] Running script from: {tmp_path}")
            print(f"[EXEC] Using Python: {sys.executable}")
            
            # Get current environment and ensure venv paths are included
            env = os.environ.copy()
            
            # Add site-packages to PYTHONPATH explicitly
            import site
            site_packages = site.getsitepackages()
            
            # Add project root to PYTHONPATH
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
            
            if site_packages:
                current_pythonpath = env.get('PYTHONPATH', '')
                paths = site_packages + [project_root]
                new_pythonpath = os.pathsep.join(paths)
                
                if current_pythonpath:
                    new_pythonpath = f"{new_pythonpath}{os.pathsep}{current_pythonpath}"
                env['PYTHONPATH'] = new_pythonpath
                print(f"[EXEC] PYTHONPATH: {env['PYTHONPATH']}")
            
            # Run the script using subprocess.run (synchronous)
            process = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=60,
                env=env  # Pass environment explicitly
            )
            
            duration = time.time() - start_time
            
            stdout_text = process.stdout if process.stdout else ""
            stderr_text = process.stderr if process.stderr else ""
            
            logs = f"=== STDOUT ===\n{stdout_text}\n\n=== STDERR ===\n{stderr_text}\n\n=== EXIT CODE ===\n{process.returncode}"
            
            print(f"[EXEC] Exit code: {process.returncode}")
            print(f"[EXEC] Duration: {duration:.2f}s")
            
            # Parse metadata from stdout
            screenshot_path = None
            video_path = None
            browser = None
            browser_version = None
            os_info = None
            
            for line in stdout_text.split('\n'):
                line = line.strip()
                if line.startswith('SCREENSHOT_PATH:'):
                    screenshot_path = line.split('SCREENSHOT_PATH:')[1].strip()
                    print(f"[EXEC] Screenshot captured: {screenshot_path}")
                elif line.startswith('VIDEO_PATH:'):
                    video_path = line.split('VIDEO_PATH:')[1].strip()
                    print(f"[EXEC] Video recorded: {video_path}")
                elif line.startswith('BROWSER:'):
                    browser = line.split('BROWSER:')[1].strip()
                elif line.startswith('BROWSER_VERSION:'):
                    browser_version = line.split('BROWSER_VERSION:')[1].strip()
                elif line.startswith('OS_INFO:'):
                    os_info = line.split('OS_INFO:')[1].strip()
            
            if process.returncode == 0:
                return ExecutionResult("passed", logs, duration, 
                                     screenshot_path=screenshot_path,
                                     video_path=video_path,
                                     browser=browser,
                                     browser_version=browser_version,
                                     os_info=os_info)
            else:
                error_msg = stderr_text.strip() if stderr_text.strip() else f"Script exited with code {process.returncode}"
                return ExecutionResult("failed", logs, duration, 
                                     error_message=error_msg,
                                     screenshot_path=screenshot_path,
                                     video_path=video_path,
                                     browser=browser,
                                     browser_version=browser_version,
                                     os_info=os_info)
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Script execution exceeded timeout of 60 seconds"
            print(f"[EXEC] TIMEOUT after {duration:.2f}s")
            return ExecutionResult("failed", error_msg, duration, error_message="TimeoutExpired: Script took too long to execute")
            
        except Exception as e:
            duration = time.time() - start_time
            import traceback
            error_detail = traceback.format_exc()
            print(f"[EXEC] EXCEPTION: {str(e)}")
            print(error_detail)
            return ExecutionResult("error", f"Execution exception:\n{error_detail}", duration, error_message=str(e))
    
    try:
        # Run in thread pool to avoid blocking the event loop
        result = await asyncio.to_thread(run_script_sync)
        return result
        
    finally:
        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                print(f"[EXEC] Cleaned up temp file: {tmp_path}")
            except Exception as e:
                print(f"[EXEC] Failed to cleanup {tmp_path}: {e}")
