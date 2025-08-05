"""
Enhanced Screen Capture System
Integrates multiple capture methods with the modern UI for maximum reliability.
"""

import cv2
import numpy as np
import logging
import time
from typing import Optional, Dict, Any, List
import os
import platform

# Import all available capture methods
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

# Windows-specific imports
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


class EnhancedScreenCapture:
    """
    Enhanced screen capture system with multiple methods and automatic fallbacks.
    Designed for integration with the modern UI system.
    """
    
    def __init__(self):
        """Initialize the enhanced screen capture system."""
        self.logger = logging.getLogger(__name__)
        
        # Available capture methods in order of preference
        self.capture_methods = []
        
        if WIN32_AVAILABLE:
            self.capture_methods.append(('win32', self._capture_win32))
        if MSS_AVAILABLE:
            self.capture_methods.append(('mss', self._capture_mss))
        if PYAUTOGUI_AVAILABLE:
            self.capture_methods.append(('pyautogui', self._capture_pyautogui))
        
        # Always have opencv as fallback
        self.capture_methods.append(('opencv', self._capture_opencv))
        
        # Current settings
        self.preferred_method = None
        self.last_successful_method = None
        self.capture_stats = {
            'total_attempts': 0,
            'successful_captures': 0,
            'method_stats': {}
        }
        
        # Quality settings
        self.high_quality_mode = False
        self.validate_captures = True
        self.auto_retry = True
        self.max_retries = 3
        
        self.logger.info(f"Enhanced screen capture initialized with {len(self.capture_methods)} methods")
    
    def set_preferred_method(self, method_name: str):
        """Set the preferred capture method."""
        available_methods = [name for name, _ in self.capture_methods]
        if method_name in available_methods:
            self.preferred_method = method_name
            self.logger.info(f"Preferred capture method set to: {method_name}")
        else:
            self.logger.warning(f"Method {method_name} not available. Available: {available_methods}")
    
    def capture_screen(self, region: Optional[Dict] = None) -> Optional[np.ndarray]:
        """
        Capture screen using the best available method.
        
        Args:
            region: Optional region dict with 'x', 'y', 'width', 'height'
            
        Returns:
            Captured image as numpy array or None if failed
        """
        self.capture_stats['total_attempts'] += 1
        
        # Determine method order
        methods_to_try = self.capture_methods.copy()
        
        # Prioritize preferred method
        if self.preferred_method:
            methods_to_try = [(name, func) for name, func in methods_to_try if name == self.preferred_method] + \
                           [(name, func) for name, func in methods_to_try if name != self.preferred_method]
        
        # Prioritize last successful method
        if self.last_successful_method and not self.preferred_method:
            methods_to_try = [(name, func) for name, func in methods_to_try if name == self.last_successful_method] + \
                           [(name, func) for name, func in methods_to_try if name != self.last_successful_method]
        
        # Try each method
        for method_name, method_func in methods_to_try:
            try:
                start_time = time.time()
                screenshot = method_func(region)
                capture_time = time.time() - start_time
                
                if screenshot is not None and screenshot.size > 0:
                    # Validate capture if enabled
                    if self.validate_captures:
                        if not self._validate_capture(screenshot):
                            self.logger.warning(f"Capture validation failed for method {method_name}")
                            if not self.auto_retry:
                                continue
                    
                    # Update statistics
                    self.capture_stats['successful_captures'] += 1
                    if method_name not in self.capture_stats['method_stats']:
                        self.capture_stats['method_stats'][method_name] = {'attempts': 0, 'successes': 0, 'avg_time': 0}
                    
                    stats = self.capture_stats['method_stats'][method_name]
                    stats['attempts'] += 1
                    stats['successes'] += 1
                    stats['avg_time'] = (stats['avg_time'] * (stats['successes'] - 1) + capture_time) / stats['successes']
                    
                    self.last_successful_method = method_name
                    self.logger.debug(f"Successful capture using {method_name} in {capture_time:.3f}s")
                    
                    return screenshot
                
            except Exception as e:
                self.logger.debug(f"Capture method {method_name} failed: {e}")
                
                # Update failure statistics
                if method_name not in self.capture_stats['method_stats']:
                    self.capture_stats['method_stats'][method_name] = {'attempts': 0, 'successes': 0, 'avg_time': 0}
                self.capture_stats['method_stats'][method_name]['attempts'] += 1
                
                continue
        
        self.logger.error("All capture methods failed")
        return None
    
    def _capture_win32(self, region: Optional[Dict] = None) -> Optional[np.ndarray]:
        """Capture using Win32 API."""
        if not WIN32_AVAILABLE:
            return None
        
        try:
            if region:
                # Capture specific region
                x, y, width, height = region['x'], region['y'], region['width'], region['height']
            else:
                # Capture full screen
                x = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
                y = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
                width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            
            # Create device contexts
            hdc = win32gui.GetDC(0)
            hdc_mem = win32ui.CreateDCFromHandle(hdc)
            hdc_mem_copy = hdc_mem.CreateCompatibleDC()
            
            # Create bitmap
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc_mem, width, height)
            hdc_mem_copy.SelectObject(hbmp)
            
            # Copy screen content
            hdc_mem_copy.BitBlt((0, 0), (width, height), hdc_mem, (x, y), win32con.SRCCOPY)
            
            # Convert to numpy array
            bmp_info = hbmp.GetInfo()
            bmp_bits = hbmp.GetBitmapBits(True)
            img = np.frombuffer(bmp_bits, dtype=np.uint8)
            img = img.reshape((height, width, 4))
            
            # Cleanup
            win32gui.DeleteObject(hbmp.GetHandle())
            hdc_mem_copy.DeleteDC()
            hdc_mem.DeleteDC()
            win32gui.ReleaseDC(0, hdc)
            
            # Convert BGRA to BGR
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
        except Exception as e:
            self.logger.debug(f"Win32 capture failed: {e}")
            return None
    
    def _capture_mss(self, region: Optional[Dict] = None) -> Optional[np.ndarray]:
        """Capture using MSS library."""
        if not MSS_AVAILABLE:
            return None
        
        try:
            with mss() as sct:
                if region:
                    monitor = {
                        'top': region['y'],
                        'left': region['x'],
                        'width': region['width'],
                        'height': region['height']
                    }
                else:
                    monitor = sct.monitors[0]  # Primary monitor
                
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                
                # Convert BGRA to BGR
                return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
        except Exception as e:
            self.logger.debug(f"MSS capture failed: {e}")
            return None
    
    def _capture_pyautogui(self, region: Optional[Dict] = None) -> Optional[np.ndarray]:
        """Capture using PyAutoGUI."""
        if not PYAUTOGUI_AVAILABLE:
            return None
        
        try:
            if region:
                screenshot = pyautogui.screenshot(region=(region['x'], region['y'], 
                                                         region['width'], region['height']))
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert PIL to numpy array and RGB to BGR
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            self.logger.debug(f"PyAutoGUI capture failed: {e}")
            return None
    
    def _capture_opencv(self, region: Optional[Dict] = None) -> Optional[np.ndarray]:
        """Capture using OpenCV (fallback method)."""
        try:
            # This is a basic fallback - limited functionality
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                if region:
                    # Crop to region
                    x, y, w, h = region['x'], region['y'], region['width'], region['height']
                    frame = frame[y:y+h, x:x+w]
                return frame
            
            return None
            
        except Exception as e:
            self.logger.debug(f"OpenCV capture failed: {e}")
            return None
    
    def _validate_capture(self, img: np.ndarray) -> bool:
        """Validate that the captured image is reasonable."""
        try:
            if img is None or img.size == 0:
                return False
            
            height, width = img.shape[:2]
            
            # Check minimum dimensions
            if width < 400 or height < 300:
                return False
            
            # Check if image is not completely black or white
            mean_intensity = np.mean(img)
            if mean_intensity < 10 or mean_intensity > 245:
                return False
            
            # Check for some variation in the image
            std_intensity = np.std(img)
            if std_intensity < 5:
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Capture validation error: {e}")
            return False
    
    def get_capture_stats(self) -> Dict[str, Any]:
        """Get capture statistics."""
        total_attempts = self.capture_stats['total_attempts']
        successful_captures = self.capture_stats['successful_captures']
        
        stats = {
            'total_attempts': total_attempts,
            'successful_captures': successful_captures,
            'success_rate': (successful_captures / max(total_attempts, 1)) * 100,
            'preferred_method': self.preferred_method,
            'last_successful_method': self.last_successful_method,
            'available_methods': [name for name, _ in self.capture_methods],
            'method_details': self.capture_stats['method_stats']
        }
        
        return stats
    
    def reset_stats(self):
        """Reset capture statistics."""
        self.capture_stats = {
            'total_attempts': 0,
            'successful_captures': 0,
            'method_stats': {}
        }
        self.logger.info("Capture statistics reset")
    
    def set_quality_mode(self, high_quality: bool):
        """Set quality mode."""
        self.high_quality_mode = high_quality
        self.logger.info(f"Quality mode set to: {'High' if high_quality else 'Standard'}")
    
    def set_validation(self, validate: bool):
        """Enable/disable capture validation."""
        self.validate_captures = validate
        self.logger.info(f"Capture validation: {'Enabled' if validate else 'Disabled'}")
    
    def set_auto_retry(self, auto_retry: bool):
        """Enable/disable auto retry on failure."""
        self.auto_retry = auto_retry
        self.logger.info(f"Auto retry: {'Enabled' if auto_retry else 'Disabled'}")


class CaptureMethodTester:
    """Test different capture methods for reliability."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enhanced_capture = EnhancedScreenCapture()
    
    def test_all_methods(self) -> Dict[str, Any]:
        """Test all available capture methods."""
        results = {}
        
        for method_name, _ in self.enhanced_capture.capture_methods:
            self.logger.info(f"Testing capture method: {method_name}")
            
            # Set preferred method for testing
            self.enhanced_capture.set_preferred_method(method_name)
            
            # Test multiple captures
            test_results = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'avg_time': 0,
                'errors': []
            }
            
            total_time = 0
            for i in range(5):  # Test 5 captures
                try:
                    start_time = time.time()
                    screenshot = self.enhanced_capture.capture_screen()
                    capture_time = time.time() - start_time
                    
                    test_results['attempts'] += 1
                    
                    if screenshot is not None and screenshot.size > 0:
                        test_results['successes'] += 1
                        total_time += capture_time
                    else:
                        test_results['failures'] += 1
                        
                except Exception as e:
                    test_results['failures'] += 1
                    test_results['errors'].append(str(e))
                
                time.sleep(0.1)  # Brief pause between tests
            
            if test_results['successes'] > 0:
                test_results['avg_time'] = total_time / test_results['successes']
            
            results[method_name] = test_results
            self.logger.info(f"Method {method_name}: {test_results['successes']}/{test_results['attempts']} successful")
        
        return results
    
    def find_best_method(self) -> str:
        """Find the best capture method based on testing."""
        test_results = self.test_all_methods()
        
        best_method = None
        best_score = 0
        
        for method_name, results in test_results.items():
            if results['attempts'] > 0:
                success_rate = results['successes'] / results['attempts']
                speed_score = 1.0 / max(results['avg_time'], 0.001)  # Avoid division by zero
                
                # Combined score: 70% success rate, 30% speed
                score = (success_rate * 0.7) + (min(speed_score, 10) / 10 * 0.3)
                
                if score > best_score:
                    best_score = score
                    best_method = method_name
        
        self.logger.info(f"Best capture method: {best_method} (score: {best_score:.3f})")
        return best_method