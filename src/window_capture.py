"""
Enhanced Window Capture System for PokerStars
This module provides robust window detection and capture specifically for PokerStars tables.
Uses multiple methods to ensure we capture the actual poker table, not other windows.
"""

import cv2
import numpy as np
import time
import logging
import os
from typing import Dict, List, Tuple, Optional, Any
import pygetwindow as gw
from mss import mss
from PIL import Image

# Try to import win32 modules, fall back to basic functionality if not available
try:
    import win32gui
    import win32ui
    import win32con
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: pywin32 not available, using fallback capture methods")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available, process detection disabled")

class PokerStarsWindowCapture:
    """
    Advanced window capture system specifically designed for PokerStars.
    Uses multiple detection methods and validation to ensure we capture the correct window.
    """
    
    def __init__(self):
        """Initialize the window capture system."""
        self.logger = logging.getLogger(__name__)
        
        # Window detection settings
        self.target_process_names = [
            'pokerstars.exe', 'pokerstarsuk.exe', 'pokerstarseu.exe',
            'pokerstarsit.exe', 'pokerstarsde.exe', 'pokerstarsdk.exe',
            'pokerstarsbe.exe', 'pokerstarsro.exe', 'pokerstarsrs.exe'
        ]
        
        # Window title patterns for PokerStars tables
        self.table_title_patterns = [
            'hold\'em', 'holdem', 'omaha', 'stud', 'razz', 'badugi',
            'tournament', 'sit & go', 'sit&go', 'cash', 'play money',
            'real money', 'nlhe', 'plo', 'limit', 'pot limit', 'no limit',
            'table', 'zoom', 'spin & go', 'spin&go'
        ]
        
        # Exclude patterns (windows we don't want)
        self.exclude_patterns = [
            'lobby', 'cashier', 'account', 'settings', 'help',
            'tournament lobby', 'sit & go lobby', 'explorer',
            'notepad', 'calculator', 'browser', 'chrome', 'firefox',
            'visual studio code', 'vs code', 'vscode', 'code.exe',
            'project -', 'bot project', 'development', 'editor',
            'ide', 'programming', 'folder', 'file explorer',
            'implementation -', 'stages', 'opera', 'dive analysis'
        ]
        
        # Current capture settings
        self.selected_window = None
        self.capture_method = 'win32'  # 'win32', 'mss', or 'pygetwindow'
        
        self.logger.info("PokerStars window capture system initialized")
    
    def find_pokerstars_processes(self) -> List[Dict]:
        """Find all running PokerStars processes."""
        try:
            if not PSUTIL_AVAILABLE:
                self.logger.warning("psutil not available, skipping process detection")
                return []
            
            pokerstars_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    if any(target in proc_name for target in self.target_process_names):
                        pokerstars_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'exe': proc.info['exe']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.logger.info(f"Found {len(pokerstars_processes)} PokerStars processes")
            return pokerstars_processes
            
        except Exception as e:
            self.logger.error(f"Error finding PokerStars processes: {e}")
            return []
    
    def find_pokerstars_windows(self) -> List[Dict]:
        """Find all PokerStars table windows using multiple methods."""
        try:
            # Method 1: Use pygetwindow
            pygetwindow_results = self._find_windows_pygetwindow()
            
            # Method 2: Use win32gui enumeration
            win32_results = self._find_windows_win32()
            
            # Combine and deduplicate results
            all_windows = []
            seen_titles = set()
            
            for window_list in [pygetwindow_results, win32_results]:
                for window in window_list:
                    if window['title'] not in seen_titles:
                        all_windows.append(window)
                        seen_titles.add(window['title'])
            
            # Filter and rank windows
            filtered_windows = self._filter_and_rank_windows(all_windows)
            
            self.logger.info(f"Found {len(filtered_windows)} potential PokerStars table windows")
            return filtered_windows
            
        except Exception as e:
            self.logger.error(f"Error finding PokerStars windows: {e}")
            return []
    
    def _find_windows_pygetwindow(self) -> List[Dict]:
        """Find windows using pygetwindow library."""
        try:
            windows = []
            all_windows = gw.getAllWindows()
            
            for window in all_windows:
                if not window.title.strip():
                    continue
                
                # Check if it's a potential PokerStars window
                if self._is_potential_pokerstars_window(window.title):
                    windows.append({
                        'title': window.title,
                        'handle': None,
                        'x': window.left,
                        'y': window.top,
                        'width': window.width,
                        'height': window.height,
                        'visible': window.visible,
                        'method': 'pygetwindow',
                        'window_obj': window
                    })
            
            return windows
            
        except Exception as e:
            self.logger.error(f"Error in pygetwindow detection: {e}")
            return []
    
    def _find_windows_win32(self) -> List[Dict]:
        """Find windows using win32gui enumeration."""
        try:
            if not WIN32_AVAILABLE:
                self.logger.warning("win32gui not available, skipping win32 detection")
                return []
            
            windows = []
            
            def enum_windows_callback(hwnd, windows_list):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and self._is_potential_pokerstars_window(title):
                        try:
                            rect = win32gui.GetWindowRect(hwnd)
                            windows_list.append({
                                'title': title,
                                'handle': hwnd,
                                'x': rect[0],
                                'y': rect[1],
                                'width': rect[2] - rect[0],
                                'height': rect[3] - rect[1],
                                'visible': True,
                                'method': 'win32',
                                'window_obj': None
                            })
                        except Exception as e:
                            self.logger.debug(f"Error getting window rect for {title}: {e}")
            
            win32gui.EnumWindows(enum_windows_callback, windows)
            return windows
            
        except Exception as e:
            self.logger.error(f"Error in win32 window detection: {e}")
            return []
    
    def _is_potential_pokerstars_window(self, title: str) -> bool:
        """Check if a window title indicates it might be a PokerStars table."""
        title_lower = title.lower()
        
        # Check exclude patterns first (more specific now)
        for exclude in self.exclude_patterns:
            if exclude in title_lower:
                return False
        
        # Check for PokerStars indicators
        pokerstars_indicators = ['pokerstars', 'poker stars']
        has_pokerstars = any(indicator in title_lower for indicator in pokerstars_indicators)
        
        # Check for table patterns
        has_table_pattern = any(pattern in title_lower for pattern in self.table_title_patterns)
        
        # For windows with "pokerstars" in title, we need additional table indicators
        if has_pokerstars:
            # If it has pokerstars AND table patterns, it's likely a real table
            if has_table_pattern:
                return True
            # If it only has pokerstars but no table patterns, it might be lobby/other
            # Check for session indicators (actual table windows have session info)
            session_indicators = ['session:', 'blinds', 'bb/', 'ante', '$', '/', 'limit', 'no limit', 'pot limit']
            has_session = any(indicator in title_lower for indicator in session_indicators)
            return has_session
        
        # For windows without pokerstars, require strong table patterns
        return has_table_pattern
    
    def _filter_and_rank_windows(self, windows: List[Dict]) -> List[Dict]:
        """Filter and rank windows by likelihood of being a poker table."""
        try:
            filtered_windows = []
            
            for window in windows:
                # Size filtering - poker tables are usually reasonably sized
                if window['width'] < 400 or window['height'] < 300:
                    continue
                
                if window['width'] > 2000 or window['height'] > 1500:
                    continue
                
                # Calculate ranking score
                score = self._calculate_window_score(window)
                window['score'] = score
                
                if score > 0:
                    filtered_windows.append(window)
            
            # Sort by score (highest first)
            filtered_windows.sort(key=lambda x: x['score'], reverse=True)
            
            return filtered_windows
            
        except Exception as e:
            self.logger.error(f"Error filtering windows: {e}")
            return windows
    
    def _calculate_window_score(self, window: Dict) -> int:
        """Calculate a score for how likely this window is to be a poker table."""
        score = 0
        title_lower = window['title'].lower()
        
        # PokerStars branding
        if 'pokerstars' in title_lower:
            score += 50
        
        # Table type indicators
        table_indicators = {
            'hold\'em': 30, 'holdem': 30, 'omaha': 25, 'tournament': 20,
            'cash': 15, 'zoom': 15, 'nlhe': 25, 'plo': 20,
            'sit & go': 20, 'spin & go': 15, 'table': 10
        }
        
        for indicator, points in table_indicators.items():
            if indicator in title_lower:
                score += points
        
        # Size bonus (typical poker table sizes)
        width, height = window['width'], window['height']
        if 800 <= width <= 1200 and 600 <= height <= 900:
            score += 20
        elif 600 <= width <= 1400 and 400 <= height <= 1000:
            score += 10
        
        # Visibility bonus
        if window.get('visible', True):
            score += 5
        
        return score
    
    def select_best_window(self) -> Optional[Dict]:
        """Automatically select the best PokerStars window."""
        try:
            windows = self.find_pokerstars_windows()
            
            if not windows:
                self.logger.warning("No PokerStars windows found")
                return None
            
            # Select the highest scoring window
            best_window = windows[0]
            self.selected_window = best_window
            
            self.logger.info(f"Selected window: '{best_window['title']}' "
                           f"({best_window['width']}x{best_window['height']}) "
                           f"Score: {best_window['score']}")
            
            return best_window
            
        except Exception as e:
            self.logger.error(f"Error selecting window: {e}")
            return None
    
    def capture_window_win32(self, window: Dict) -> Optional[np.ndarray]:
        """Capture window using win32 API (most reliable for specific windows)."""
        try:
            if not WIN32_AVAILABLE:
                return None
            
            hwnd = window.get('handle')
            if not hwnd:
                return None
            
            # Get window dimensions
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            # Create device contexts
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # Create bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # Copy window content
            result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
            
            if result == 0:
                # Fallback to BitBlt if PrintWindow fails
                saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            # Convert to numpy array
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)  # BGRA format
            
            # Convert BGRA to BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Cleanup
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return img
            
        except Exception as e:
            self.logger.error(f"Error in win32 capture: {e}")
            return None
    
    def capture_window_mss(self, window: Dict) -> Optional[np.ndarray]:
        """Capture window using MSS library."""
        try:
            with mss() as sct:
                # Define capture region
                region = {
                    'top': window['y'],
                    'left': window['x'],
                    'width': window['width'],
                    'height': window['height']
                }
                
                # Capture screen region
                screenshot = sct.grab(region)
                
                # Convert to numpy array
                img_array = np.array(screenshot)
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
                
                return img_bgr
                
        except Exception as e:
            self.logger.error(f"Error in MSS capture: {e}")
            return None
    
    def capture_window_pygetwindow(self, window: Dict) -> Optional[np.ndarray]:
        """Capture window using pygetwindow."""
        try:
            window_obj = window.get('window_obj')
            if not window_obj:
                return None
            
            # Bring window to front (optional)
            try:
                window_obj.activate()
                time.sleep(0.1)  # Brief pause for window to activate
            except:
                pass  # Continue even if activation fails
            
            # Use MSS to capture the window region
            with mss() as sct:
                region = {
                    'top': window_obj.top,
                    'left': window_obj.left,
                    'width': window_obj.width,
                    'height': window_obj.height
                }
                
                screenshot = sct.grab(region)
                img_array = np.array(screenshot)
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
                
                return img_bgr
                
        except Exception as e:
            self.logger.error(f"Error in pygetwindow capture: {e}")
            return None
    
    def capture_current_window(self) -> Optional[np.ndarray]:
        """Capture the currently selected window using the best available method."""
        try:
            if not self.selected_window:
                self.logger.warning("No window selected for capture")
                return None
            
            # Try different capture methods in order of preference
            capture_methods = [
                ('win32', self.capture_window_win32),
                ('mss', self.capture_window_mss),
                ('pygetwindow', self.capture_window_pygetwindow)
            ]
            
            for method_name, method_func in capture_methods:
                try:
                    img = method_func(self.selected_window)
                    if img is not None and img.size > 0:
                        self.capture_method = method_name
                        return img
                except Exception as e:
                    self.logger.debug(f"Capture method {method_name} failed: {e}")
                    continue
            
            self.logger.error("All capture methods failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Error capturing current window: {e}")
            return None
    
    def validate_capture(self, img: np.ndarray) -> bool:
        """Validate that the captured image looks like a poker table."""
        try:
            if img is None or img.size == 0:
                return False
            
            height, width = img.shape[:2]
            
            # Size validation
            if width < 400 or height < 300:
                return False
            
            # Check if image is not completely black or white
            mean_intensity = np.mean(img)
            if mean_intensity < 10 or mean_intensity > 245:
                return False
            
            # Check for some color variation (poker tables have green/blue backgrounds)
            if len(img.shape) == 3:
                # Convert to HSV for better color analysis
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                
                # Check for green/blue hues typical of poker tables
                green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
                blue_mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([130, 255, 255]))
                
                green_pixels = np.sum(green_mask > 0)
                blue_pixels = np.sum(blue_mask > 0)
                total_pixels = width * height
                
                # If more than 10% of pixels are green or blue, likely a poker table
                color_ratio = (green_pixels + blue_pixels) / total_pixels
                if color_ratio > 0.1:
                    return True
            
            # Basic validation passed
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating capture: {e}")
            return False
    
    def get_window_info(self) -> Dict:
        """Get information about the currently selected window."""
        if not self.selected_window:
            return {'status': 'No window selected'}
        
        return {
            'title': self.selected_window['title'],
            'dimensions': f"{self.selected_window['width']}x{self.selected_window['height']}",
            'position': f"({self.selected_window['x']}, {self.selected_window['y']})",
            'method': self.selected_window.get('method', 'unknown'),
            'score': self.selected_window.get('score', 0),
            'capture_method': self.capture_method
        }
    
    def refresh_window_list(self) -> List[Dict]:
        """Refresh and return the list of available PokerStars windows."""
        return self.find_pokerstars_windows()
    
    def set_capture_method(self, method: str):
        """Set the preferred capture method."""
        if method in ['win32', 'mss', 'pygetwindow']:
            self.capture_method = method
            self.logger.info(f"Capture method set to: {method}")
        else:
            self.logger.warning(f"Invalid capture method: {method}")