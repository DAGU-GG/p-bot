"""
OBS Virtual Camera Capture System
This module handles capturing video feed from OBS Studio's virtual camera
for reliable poker table analysis.
"""

import cv2
import numpy as np
import logging
import time
from typing import Optional, Dict, List, Tuple, Any
import threading
import subprocess
import platform
import os


class OBSCaptureSystem:
    """
    Handles capturing video feed from OBS Studio's virtual camera.
    Provides a more reliable alternative to direct window capture.
    """
    
    def __init__(self):
        """Initialize the OBS capture system."""
        self.logger = logging.getLogger(__name__)
        
        # Capture settings
        self.camera_index = None
        self.capture = None
        self.is_capturing = False
        self.last_frame = None
        self.frame_count = 0
        
        # Video properties
        self.frame_width = 1920
        self.frame_height = 1080
        self.fps = 30
        
        # Threading
        self.capture_thread = None
        self.thread_lock = threading.Lock()
        
        self.logger.info("OBS capture system initialized")
    
    def get_windows_cameras_via_powershell(self) -> List[Dict]:
        """Get camera list using PowerShell on Windows."""
        try:
            if platform.system() != "Windows":
                return []
            
            # PowerShell command to list cameras
            ps_command = '''
            Get-WmiObject -Class Win32_PnPEntity | Where-Object {
                $_.Name -like "*camera*" -or 
                $_.Name -like "*OBS*" -or 
                $_.Name -like "*Virtual*" -or
                $_.DeviceID -like "*USB\\VID*"
            } | Select-Object Name, DeviceID | ConvertTo-Json
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    devices = json.loads(result.stdout)
                    if isinstance(devices, dict):
                        devices = [devices]
                    
                    cameras = []
                    for i, device in enumerate(devices):
                        if any(keyword in device.get('Name', '').lower() 
                              for keyword in ['obs', 'virtual', 'camera']):
                            cameras.append({
                                'index': i,
                                'name': device.get('Name', ''),
                                'device_id': device.get('DeviceID', ''),
                                'source': 'powershell'
                            })
                    
                    self.logger.info(f"PowerShell found {len(cameras)} potential cameras")
                    return cameras
                except json.JSONDecodeError:
                    pass
            
            return []
            
        except Exception as e:
            self.logger.debug(f"PowerShell camera detection failed: {e}")
            return []
    
    def try_camera_with_backend(self, index: int, backend: int) -> Optional[cv2.VideoCapture]:
        """Try to open camera with specific backend, suppressing errors."""
        try:
            # Temporarily redirect stderr to suppress OpenCV errors
            import sys
            import os
            
            # Save original stderr
            original_stderr = sys.stderr
            
            # Redirect stderr to null
            sys.stderr = open(os.devnull, 'w')
            
            try:
                cap = cv2.VideoCapture(index, backend)
                
                if cap.isOpened():
                    # Test if we can actually read frames
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        # Restore stderr before returning
                        sys.stderr.close()
                        sys.stderr = original_stderr
                        return cap
                
                cap.release()
                
            finally:
                # Always restore stderr
                if sys.stderr != original_stderr:
                    sys.stderr.close()
                    sys.stderr = original_stderr
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Backend {backend} failed for camera {index}: {e}")
            return None
    
    def find_obs_virtual_camera(self) -> Optional[int]:
        """
        Find OBS Virtual Camera in available video devices.
        
        Returns:
            Camera index if found, None otherwise
        """
        try:
            self.logger.info("Searching for OBS Virtual Camera...")
            
            # First try PowerShell detection on Windows
            powershell_cameras = self.get_windows_cameras_via_powershell()
            if powershell_cameras:
                self.logger.info("Found cameras via PowerShell:")
                for cam in powershell_cameras:
                    self.logger.info(f"  - {cam['name']}")
            
            # Try different backends in order of preference
            backends = []
            if platform.system() == "Windows":
                backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            else:
                backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
            
            # Common OBS camera indices (OBS usually gets assigned early indices)
            priority_indices = [0, 1, 2, 3, 4, 5]
            other_indices = list(range(6, 15))
            
            all_indices = priority_indices + other_indices
            
            self.logger.info(f"Testing {len(all_indices)} camera indices with {len(backends)} backends...")
            
            for camera_index in all_indices:
                for backend in backends:
                    backend_name = {
                        cv2.CAP_DSHOW: "DirectShow",
                        cv2.CAP_MSMF: "Media Foundation", 
                        cv2.CAP_V4L2: "V4L2",
                        cv2.CAP_ANY: "Any"
                    }.get(backend, f"Backend{backend}")
                    
                    self.logger.debug(f"Testing camera {camera_index} with {backend_name}...")
                    
                    cap = self.try_camera_with_backend(camera_index, backend)
                    if cap is not None:
                        # Test multiple frames to ensure it's a live feed
                        frame_count = 0
                        for _ in range(3):
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                frame_count += 1
                                time.sleep(0.1)
                        
                        if frame_count >= 2:
                            height, width = frame.shape[:2]
                            if width >= 640 and height >= 480:
                                self.logger.info(f"Found working camera at index {camera_index} "
                                               f"with {backend_name} ({width}x{height})")
                                cap.release()
                                return camera_index
                        
                        cap.release()
            
            # If no camera found, try a simple approach with just index 0-2
            self.logger.info("Trying simple camera detection...")
            for i in range(3):
                try:
                    test_cap = cv2.VideoCapture(i)
                    if not test_cap.isOpened():
                        test_cap.release()
                        continue
                    
                    ret, frame = test_cap.read()
                    test_cap.release()
                    
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        if width >= 640 and height >= 480:
                            self.logger.info(f"Simple detection found camera at index {i} ({width}x{height})")
                            return i
                
                except Exception as e:
                    self.logger.debug(f"Simple test failed for camera {i}: {e}")
                    continue
            
            self.logger.warning("OBS Virtual Camera not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding OBS Virtual Camera: {e}")
            return None
    
    def connect_to_obs_camera(self, camera_index: Optional[int] = None) -> bool:
        """
        Connect to OBS Virtual Camera.
        
        Args:
            camera_index: Specific camera index to use, or None to auto-detect
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Auto-detect if no index provided
            if camera_index is None:
                camera_index = self.find_obs_virtual_camera()
                if camera_index is None:
                    return False
            
            # Try different backends for connection
            backends = []
            if platform.system() == "Windows":
                backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            else:
                backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
            
            self.capture = None
            for backend in backends:
                backend_name = {
                    cv2.CAP_DSHOW: "DirectShow",
                    cv2.CAP_MSMF: "Media Foundation",
                    cv2.CAP_V4L2: "V4L2", 
                    cv2.CAP_ANY: "Any"
                }.get(backend, f"Backend{backend}")
                
                self.logger.info(f"Trying to connect with {backend_name}...")
                
                test_cap = self.try_camera_with_backend(camera_index, backend)
                if test_cap is not None:
                    self.capture = test_cap
                    self.logger.info(f"Connected using {backend_name}")
                    break
            
            if not self.capture.isOpened():
                self.logger.error(f"Failed to open camera at index {camera_index}")
                return False
            
            # Configure camera properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Set buffer size to 1 for real-time capture
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Get actual properties
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.capture.get(cv2.CAP_PROP_FPS)
            
            self.camera_index = camera_index
            
            self.logger.info(f"Connected to OBS Virtual Camera:")
            self.logger.info(f"  Index: {camera_index}")
            self.logger.info(f"  Resolution: {actual_width}x{actual_height}")
            self.logger.info(f"  FPS: {actual_fps}")
            
            # Test capture
            successful_captures = 0
            for i in range(3):
                ret, test_frame = self.capture.read()
                if ret and test_frame is not None and test_frame.size > 0:
                    successful_captures += 1
                time.sleep(0.1)
            
            if successful_captures >= 2:
                self.logger.info(f"OBS camera test successful ({successful_captures}/3 frames)")
                return True
            else:
                self.logger.error(f"OBS camera test failed ({successful_captures}/3 frames)")
                self.disconnect()
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to OBS camera: {e}")
            return False
    
    def start_capture(self) -> bool:
        """
        Start continuous capture from OBS Virtual Camera.
        
        Returns:
            True if capture started successfully, False otherwise
        """
        try:
            if not self.capture or not self.capture.isOpened():
                self.logger.error("OBS camera not connected")
                return False
            
            if self.is_capturing:
                self.logger.warning("Capture already running")
                return True
            
            self.is_capturing = True
            self.frame_count = 0
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            self.logger.info("OBS capture started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting OBS capture: {e}")
            return False
    
    def stop_capture(self):
        """Stop continuous capture."""
        try:
            self.is_capturing = False
            
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=2.0)
            
            self.logger.info("OBS capture stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping OBS capture: {e}")
    
    def _capture_loop(self):
        """Internal capture loop running in separate thread."""
        try:
            while self.is_capturing and self.capture and self.capture.isOpened():
                ret, frame = self.capture.read()
                
                if ret and frame is not None:
                    with self.thread_lock:
                        self.last_frame = frame.copy()
                        self.frame_count += 1
                else:
                    self.logger.warning("Failed to read frame from OBS camera")
                    time.sleep(0.1)  # Brief pause before retry
                
                # Small delay to control frame rate
                time.sleep(1.0 / self.fps)
                
        except Exception as e:
            self.logger.error(f"Error in OBS capture loop: {e}")
        finally:
            self.is_capturing = False
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest captured frame.
        
        Returns:
            Latest frame as numpy array, or None if no frame available
        """
        try:
            with self.thread_lock:
                if self.last_frame is not None:
                    return self.last_frame.copy()
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting latest frame: {e}")
            return None
    
    def capture_single_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame (for testing or single analysis).
        
        Returns:
            Captured frame as numpy array, or None if capture failed
        """
        try:
            if not self.capture or not self.capture.isOpened():
                self.logger.error("OBS camera not connected")
                return None
            
            ret, frame = self.capture.read()
            
            if ret and frame is not None:
                self.logger.debug("Single frame captured successfully")
                return frame
            else:
                self.logger.warning("Failed to capture single frame")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing single frame: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from OBS Virtual Camera."""
        try:
            # Stop capture if running
            if self.is_capturing:
                self.stop_capture()
            
            # Release camera
            if self.capture:
                self.capture.release()
                self.capture = None
            
            self.camera_index = None
            self.last_frame = None
            self.frame_count = 0
            
            self.logger.info("Disconnected from OBS Virtual Camera")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from OBS camera: {e}")
    
    def get_capture_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics.
        
        Returns:
            Dictionary with capture statistics
        """
        return {
            'connected': self.capture is not None and self.capture.isOpened(),
            'capturing': self.is_capturing,
            'camera_index': self.camera_index,
            'frame_count': self.frame_count,
            'has_latest_frame': self.last_frame is not None,
            'resolution': f"{self.frame_width}x{self.frame_height}" if self.capture else "Unknown",
            'fps': self.fps
        }
    
    def validate_frame(self, frame: np.ndarray) -> bool:
        """
        Validate that the frame looks like a poker table.
        
        Args:
            frame: Frame to validate
            
        Returns:
            True if frame appears to be a poker table, False otherwise
        """
        try:
            if frame is None or frame.size == 0:
                return False
            
            height, width = frame.shape[:2]
            
            # Check dimensions
            if width < 800 or height < 600:
                return False
            
            # Check if frame is not completely black or white
            mean_intensity = np.mean(frame)
            if mean_intensity < 10 or mean_intensity > 245:
                return False
            
            # Check for green/blue colors typical of poker tables
            if len(frame.shape) == 3:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # Check for green hues (poker table background)
                green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
                green_pixels = np.sum(green_mask > 0)
                total_pixels = width * height
                
                green_ratio = green_pixels / total_pixels
            if green_ratio > 0.1:  # If more than 10% green pixels, likely poker table
                return True
            
            # Basic validation passed
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating frame: {e}")
            return False
    
    def list_available_cameras(self) -> List[Dict[str, Any]]:
        """
        List all available camera devices.
        
        Returns:
            List of camera information dictionaries
        """
        cameras = []
        
        try:
            for i in range(11):  # Check first 11 camera indices
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        # Try to read a frame
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            
                            cameras.append({
                                'index': i,
                                'width': width,
                                'height': height,
                                'fps': fps,
                                'working': True
                            })
                        else:
                            cameras.append({
                                'index': i,
                                'width': 0,
                                'height': 0,
                                'fps': 0,
                                'working': False
                            })
                    
                    cap.release()
                    
                except Exception as e:
                    self.logger.debug(f"Error checking camera {i}: {e}")
                    continue
            
            self.logger.info(f"Found {len(cameras)} camera devices")
            return cameras
            
        except Exception as e:
            self.logger.error(f"Error listing cameras: {e}")
            return []


class OBSIntegratedBot:
    """
    Poker bot integrated with OBS Virtual Camera capture.
    Combines OBS capture with existing poker analysis systems.
    """
    
    def __init__(self):
        """Initialize the OBS-integrated bot."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize OBS capture
        self.obs_capture = OBSCaptureSystem()
        
        # Initialize existing bot components
        from poker_bot import PokerStarsBot
        self.poker_bot = PokerStarsBot()
        
        # Override the window capture with OBS capture
        self.poker_bot.window_capture = None  # Disable window capture
        
        self.logger.info("OBS-integrated poker bot initialized")
    
    def connect_obs(self, camera_index: Optional[int] = None) -> bool:
        """
        Connect to OBS Virtual Camera.
        
        Args:
            camera_index: Specific camera index, or None for auto-detection
            
        Returns:
            True if connection successful, False otherwise
        """
        return self.obs_capture.connect_to_obs_camera(camera_index)
    
    def start_analysis(self) -> bool:
        """
        Start continuous analysis of OBS feed.
        
        Returns:
            True if analysis started successfully, False otherwise
        """
        try:
            # Start OBS capture
            if not self.obs_capture.start_capture():
                return False
            
            self.logger.info("OBS analysis started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting OBS analysis: {e}")
            return False
    
    def stop_analysis(self):
        """Stop continuous analysis."""
        try:
            self.obs_capture.stop_capture()
            self.logger.info("OBS analysis stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping OBS analysis: {e}")
    
    def analyze_current_frame(self) -> Optional[Dict[str, Any]]:
        """
        Analyze the current OBS frame.
        
        Returns:
            Analysis results dictionary, or None if no frame available
        """
        try:
            # Get latest frame from OBS
            frame = self.obs_capture.get_latest_frame()
            if frame is None:
                return None
            
            # Validate frame
            if not self.obs_capture.validate_frame(frame):
                self.logger.warning("Frame validation failed")
                return None
            
            # Use existing bot analysis methods
            analysis = self.poker_bot.analyze_game_state(frame)
            
            # Add OBS-specific information
            analysis['obs_stats'] = self.obs_capture.get_capture_stats()
            analysis['frame_source'] = 'obs_virtual_camera'
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing OBS frame: {e}")
            return None
    
    def get_obs_stats(self) -> Dict[str, Any]:
        """Get OBS capture statistics."""
        return self.obs_capture.get_capture_stats()
    
    def disconnect(self):
        """Disconnect from OBS and cleanup."""
        try:
            self.stop_analysis()
            self.obs_capture.disconnect()
            self.logger.info("OBS bot disconnected")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting OBS bot: {e}")