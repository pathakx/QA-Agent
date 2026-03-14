import cv2
import numpy as np
import threading
import time
import os
from PIL import Image
import io

class ScreenRecorder:
    def __init__(self, driver, output_path, fps=10.0):
        self.driver = driver
        self.output_path = output_path
        self.fps = fps
        self.is_recording = False
        self.thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self.is_recording:
            return
        
        self.is_recording = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()

    def stop(self):
        if not self.is_recording:
            return
        
        self.is_recording = False
        self._stop_event.set()
        if self.thread:
            self.thread.join()

    def _record_loop(self):
        # specific to your selenium driver usage
        # We need to get window size to init video writer
        try:
            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Define the codec and create VideoWriter
            # Using VP80 (WebM) for better browser compatibility
            fourcc = cv2.VideoWriter_fourcc(*'VP80') 
            out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))
            
            while not self._stop_event.is_set():
                try:
                    # Capture screenshot as PNG in memory
                    png_data = self.driver.get_screenshot_as_png()
                    
                    # Convert to numpy array for OpenCV
                    image = Image.open(io.BytesIO(png_data))
                    frame = np.array(image)
                    
                    # Convert RGB to BGR (OpenCV uses BGR)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Resize if needed (though get_screenshot_as_png should match window size mostly, 
                    # but sometimes high-DPI displays affect it. We trust it matches or handle resize)
                    # Let's verify size match
                    if frame.shape[1] != width or frame.shape[0] != height:
                        frame = cv2.resize(frame, (width, height))
                        
                    out.write(frame)
                    
                    # Wait for next frame
                    time.sleep(1.0 / self.fps)
                    
                except Exception as e:
                    print(f"Recording error: {e}")
                    break
                    
            out.release()
            
        except Exception as e:
            print(f"Failed to initialize recording: {e}")
