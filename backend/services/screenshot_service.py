"""
Screenshot capture service for test executions
"""
import os
import platform
from PIL import Image
from io import BytesIO

def get_system_info():
    """Get OS and system information"""
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'platform': platform.platform(),
        'machine': platform.machine()
    }

def get_browser_info(driver):
    """Extract browser information from Selenium driver"""
    try:
        capabilities = driver.capabilities
        browser_name = capabilities.get('browserName', 'unknown')
        browser_version = capabilities.get('browserVersion') or capabilities.get('version', 'unknown')
        return {
            'browser': browser_name,
            'version': browser_version
        }
    except Exception as e:
        print(f"Failed to get browser info: {e}")
        return {
            'browser': 'unknown',
            'version': 'unknown'
        }

def capture_screenshot(driver, test_id: str, execution_id: str) -> str:
    """
    Capture screenshot from Selenium driver and save to disk
    
    Returns: relative path to screenshot file
    """
    try:
        # Create directory structure
        screenshot_dir = f"test_results/{test_id}/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Generate filename
        filename = f"{execution_id}.png"
        filepath = os.path.join(screenshot_dir, filename)
        
        # Capture screenshot
        driver.save_screenshot(filepath)
        
        print(f"[SCREENSHOT] Saved to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"[SCREENSHOT] Failed to capture: {e}")
        return None

def optimize_screenshot(filepath: str, max_width: int = 1920):
    """
    Optimize screenshot file size
    """
    try:
        with Image.open(filepath) as img:
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save optimized
            img.save(filepath, 'PNG', optimize=True, quality=85)
            print(f"[SCREENSHOT] Optimized: {filepath}")
    except Exception as e:
        print(f"[SCREENSHOT] Optimization failed: {e}")
