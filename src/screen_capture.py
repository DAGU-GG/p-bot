"""
Screen Capture Manager for Poker Bot
Provides a unified interface for capturing screenshots regardless of method.
"""

import cv2
import numpy as np
import logging
import time
from typing import Optional, Dict, Any
import os
import platform

# Try to import platform-specific modules
try:
    from mss import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Try to import win32 modules on Windows
WIN32_AVAILABLE = False
if platform.system() == 'Windows':
    try:
        import win32gui
        import win32ui
        import win32con
        import win32api
        WIN32_AVAILABLE = True
    except ImportError:
        pass


class ScreenCaptureManager:
    """
    Unified screen capture manager that works across platforms.
    Provides methods for capturing the screen using various methods.
    """
    
    def __init__(self):
        """Initialize the screen capture manager."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ScreenCaptureManager")
        
        # Determine best capture method based on available libraries
        if MSS_AVAILABLE:
            self.primary_method = "mss"
            self.logger.info("Using MSS for screen capture (primary)")
        elif PYAUTOGUI_AVAILABLE:
            self.primary_method = "pyautogui"
            self.logger.info("Using PyAutoGUI for screen capture (primary)")
        elif WIN32_AVAILABLE:
            self.primary_method = "win32"
            self.logger.info("Using Win32 API for screen capture (primary)")
        else:
            self.primary_method = "opencv"
            self.logger.info("Using OpenCV for screen capture (fallback)")
        
        # Initialize capture tools based on availability
        if MSS_AVAILABLE:
            self.mss_instance = mss()
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """
        Capture the entire screen using the best available method.
        
        Returns:
            np.ndarray: The screenshot as a numpy array in BGR format (OpenCV compatible)
        """
        try:
            self.logger.info(f"Capturing screen using {self.primary_method} method")
            
            if self.primary_method == "mss":
                return self._capture_with_mss()
            elif self.primary_method == "pyautogui":
                return self._capture_with_pyautogui()
            elif self.primary_method == "win32":
                return self._capture_with_win32()
            else:
                return self._capture_with_opencv()
                
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")
            return None
    
    def _capture_with_mss(self) -> np.ndarray:
        """Capture screen using MSS library."""
        monitor = self.mss_instance.monitors[0]  # Use the primary monitor
        screenshot = self.mss_instance.grab(monitor)
        img = np.array(screenshot)
        # Convert from BGRA to BGR (remove alpha channel)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    def _capture_with_pyautogui(self) -> np.ndarray:
        """Capture screen using PyAutoGUI."""
        screenshot = pyautogui.screenshot()
        # Convert PIL Image to numpy array and from RGB to BGR (for OpenCV)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def _capture_with_win32(self) -> np.ndarray:
        """Capture screen using Win32 API (Windows only)."""
        # Get screen dimensions
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        
        # Create device context and bitmap
        hdc = win32gui.GetDC(0)
        hdc_mem = win32ui.CreateDCFromHandle(hdc)
        hdc_mem_copy = hdc_mem.CreateCompatibleDC()
        
        # Create bitmap and select it into our device context
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc_mem, width, height)
        hdc_mem_copy.SelectObject(hbmp)
        
        # Copy screen into bitmap
        hdc_mem_copy.BitBlt((0, 0), (width, height), hdc_mem, (left, top), win32con.SRCCOPY)
        
        # Convert bitmap to numpy array
        bmp_info = hbmp.GetInfo()
        bmp_bits = hbmp.GetBitmapBits(True)
        img = np.frombuffer(bmp_bits, dtype=np.uint8)
        img = img.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))
        
        # Free resources
        win32gui.DeleteObject(hbmp.GetHandle())
        hdc_mem_copy.DeleteDC()
        hdc_mem.DeleteDC()
        win32gui.ReleaseDC(0, hdc)
        
        # Convert from BGRA to BGR (remove alpha channel)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    def _capture_with_opencv(self) -> np.ndarray:
        """Capture screen using OpenCV (limited functionality)."""
        # This is a fallback method and may not work on all platforms
        self.logger.warning("Using OpenCV for screen capture, which has limited functionality")
        
        # Try to capture from default screen capture device
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return frame
        else:
            self.logger.error("Failed to capture screen with OpenCV")
            # Return a blank image as fallback
            return np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """
        Capture a specific region of the screen.
        
        Args:
            x: Left coordinate of the region
            y: Top coordinate of the region
            width: Width of the region
            height: Height of the region
            
        Returns:
            np.ndarray: The captured region as a numpy array in BGR format
        """
        try:
            # First capture the full screen
            full_screen = self.capture_screen()
            
            if full_screen is None:
                self.logger.error("Failed to capture full screen")
                return None
                
            # Then crop to the desired region
            # Make sure the region is within bounds
            screen_height, screen_width = full_screen.shape[:2]
            
            # Adjust coordinates if they're out of bounds
            x = max(0, min(x, screen_width - 1))
            y = max(0, min(y, screen_height - 1))
            width = min(width, screen_width - x)
            height = min(height, screen_height - y)
            
            # Crop and return the region
            return full_screen[y:y+height, x:x+width].copy()
            
        except Exception as e:
            self.logger.error(f"Error capturing region: {e}")
            return None
    
    def save_screenshot(self, file_path: str) -> bool:
        """
        Capture and save a screenshot to the specified file path.
        
        Args:
            file_path: Path where the screenshot should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            screenshot = self.capture_screen()
            
            if screenshot is None:
                self.logger.error("Failed to capture screenshot for saving")
                return False
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save the image
            cv2.imwrite(file_path, screenshot)
            self.logger.info(f"Screenshot saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving screenshot: {e}")
            return False


# Test function
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create capture manager
    capture = ScreenCaptureManager()
    
    # Test capturing the screen
    screenshot = capture.capture_screen()
    
    if screenshot is not None:
        print(f"Captured screenshot with shape: {screenshot.shape}")
        
        # Save the screenshot
        timestamp = int(time.time())
        cv2.imwrite(f"test_screenshot_{timestamp}.png", screenshot)
        print(f"Screenshot saved as test_screenshot_{timestamp}.png")
    else:
        print("Failed to capture screenshot")
