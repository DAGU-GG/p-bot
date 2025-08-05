"""
Hardware Capture Integration System
Integrates laptop PokerStars capture with main PC bot analysis
"""

import cv2
import numpy as np
import time
import logging
from typing import Optional, Dict, Any, Tuple, List
import pygetwindow as gw
import pyautogui
from dataclasses import dataclass

# Import your existing systems
try:
    from enhanced_ocr_recognition import EnhancedOCRCardRecognition
    from table_reference_system import TableReferenceSystem
    from enhanced_integration import EnhancedPokerBot
    from fallback_card_recognition import FallbackCardRecognition
    from enhanced_card_recognition import EnhancedCardRecognition
    ENHANCED_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some recognition modules not available: {e}")
    ENHANCED_AVAILABLE = False

@dataclass
class HardwareCaptureConfig:
    """Configuration for hardware capture setup"""
    obs_window_title: str = "OBS Studio"
    capture_source_name: str = "Video Capture Device"
    auto_calibration: bool = True
    debug_mode: bool = True
    recognition_method: str = "enhanced"  # "enhanced", "fallback", or "both"
    capture_fps: int = 30
    analysis_interval: float = 1.0  # Analyze every 1 second

class HardwareCaptureSystem:
    """Main system for analyzing laptop PokerStars via hardware capture"""
    
    def __init__(self, config: Optional[HardwareCaptureConfig] = None):
        self.config = config or HardwareCaptureConfig()
        self.logger = logging.getLogger("hardware_capture")
        
        # Initialize recognition systems
        self.table_ref = TableReferenceSystem()
        
        # Initialize Ultimate Card Recognition System (primary)
        self.ultimate_recognition = None
        try:
            from ultimate_card_integration import UltimateCardIntegration
            self.ultimate_recognition = UltimateCardIntegration(debug_mode=self.config.debug_mode)
            if self.ultimate_recognition:
                self.logger.info("🎯 Ultimate Card Recognition System initialized")
            else:
                self.logger.warning("Ultimate Card Recognition System failed to initialize")
        except ImportError as e:
            self.logger.warning(f"Ultimate Card Recognition not available: {e}")
        
        # Initialize enhanced card recognition system (secondary)
        self.enhanced_recognition = None
        if ENHANCED_AVAILABLE:
            try:
                self.enhanced_recognition = EnhancedCardRecognition(debug_mode=self.config.debug_mode)
                self.logger.info("Enhanced card recognition system initialized")
            except Exception as e:
                self.logger.warning(f"Enhanced card recognition failed to initialize: {e}")
        
        # Initialize OCR systems based on config (legacy fallback)
        self.ocr_systems = {}
        if self.config.recognition_method in ["enhanced", "both"]:
            try:
                self.ocr_systems["enhanced"] = EnhancedOCRCardRecognition()
                self.logger.info("Enhanced OCR system initialized")
            except Exception as e:
                self.logger.warning(f"Enhanced OCR failed to initialize: {e}")
        
        if self.config.recognition_method in ["fallback", "both"] or not self.ocr_systems:
            try:
                self.ocr_systems["fallback"] = FallbackCardRecognition()
                self.logger.info("Fallback recognition system initialized")
            except Exception as e:
                self.logger.error(f"Fallback recognition failed to initialize: {e}")
        
        # State tracking
        self.calibrated_regions = None
        self.last_analysis_time = 0
        self.analysis_history = []
        self._last_game_state = None  # Store for UI access
        
        # Live logging for UI
        self.ui_log_callback = None
        self.detailed_recognition_log = []
        self.recognition_performance_stats = {
            'total_frames': 0,
            'successful_frames': 0,
            'processing_times': [],
            'confidence_scores': []
        }
        
        # Virtual camera capture
        self.virtual_camera = None
        self.camera_index = None
        
    def find_obs_virtual_camera(self) -> Optional[int]:
        """Find OBS Virtual Camera index"""
        try:
            # Based on testing, camera index 1 works for this setup
            test_index = 1
            
            try:
                cap = cv2.VideoCapture(test_index, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # Try to read a frame to verify it works
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.logger.info(f"Found working camera at index {test_index}: {frame.shape}")
                        cap.release()
                        return test_index
                cap.release()
            except Exception as e:
                pass
            
            # Fallback: try different camera indices
            for camera_index in range(10):
                if camera_index == test_index:  # Skip already tested
                    continue
                try:
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                    if cap.isOpened():
                        # Try to read a frame to verify it works
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            self.logger.info(f"Found working camera at index {camera_index}: {frame.shape}")
                            cap.release()
                            return camera_index
                    cap.release()
                except Exception as e:
                    continue
            
            self.logger.error("No working virtual camera found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding virtual camera: {e}")
            return None
    
    def connect_to_virtual_camera(self) -> bool:
        """Connect to OBS Virtual Camera"""
        try:
            if self.virtual_camera is not None:
                self.virtual_camera.release()
            
            # Find virtual camera
            self.camera_index = self.find_obs_virtual_camera()
            if self.camera_index is None:
                return False
            
            # Connect to virtual camera
            self.virtual_camera = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            
            if not self.virtual_camera.isOpened():
                self.logger.error(f"Failed to open virtual camera at index {self.camera_index}")
                return False
            
            # Set camera properties for better quality
            self.virtual_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.virtual_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.virtual_camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Test capture
            ret, frame = self.virtual_camera.read()
            if ret and frame is not None:
                self.logger.info(f"✅ Connected to OBS Virtual Camera: {frame.shape}")
                return True
            else:
                self.logger.error("Virtual camera connected but no frame received")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to virtual camera: {e}")
            return False
    
    def capture_from_virtual_camera(self) -> Optional[np.ndarray]:
        """Capture frame from OBS Virtual Camera"""
        try:
            # Ensure virtual camera is connected
            if self.virtual_camera is None or not self.virtual_camera.isOpened():
                if not self.connect_to_virtual_camera():
                    return None
            
            # Capture frame
            ret, frame = self.virtual_camera.read()
            
            if not ret or frame is None:
                self.logger.warning("Failed to capture frame from virtual camera")
                # Try to reconnect
                if self.connect_to_virtual_camera():
                    ret, frame = self.virtual_camera.read()
                    if not ret or frame is None:
                        return None
                else:
                    return None
            
            # Save debug frame if enabled (disabled by default to prevent spam)
            if getattr(self.config, 'save_debug_frames', False):
                cv2.imwrite(f"virtual_camera_capture_{int(time.time())}.png", frame)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error capturing from virtual camera: {e}")
            return None
    
    def auto_calibrate_from_hardware(self) -> bool:
        """Load existing region configuration or auto-calibrate table regions from hardware capture"""
        try:
            # First, try to load existing region configuration
            region_files = [
                "regions/region_config_manual.json",     # Try manual version first (most accurate)
                "regions/region_config.json",           # Then regular config
                "regions/region_config_corrected.json", # Then corrected version
                "region_config.json",
                "src/region_config.json"
            ]
            
            for region_file in region_files:
                try:
                    import json
                    with open(region_file, 'r') as f:
                        region_data = json.load(f)
                    
                    if 'regions' in region_data:
                        # Handle different coordinate formats
                        self.calibrated_regions = {}
                        
                        # Get current frame to determine dimensions
                        screenshot = self.capture_from_virtual_camera()
                        if screenshot is None:
                            continue
                        
                        height, width = screenshot.shape[:2]
                        self.logger.info(f"Current frame dimensions: {width}x{height}")
                        
                        for region_name, region_info in region_data['regions'].items():
                            # Check if coordinates are already in pixels or percentages
                            if 'x_percent' in region_info:
                                # Already percentage format
                                x_pixel = int(region_info['x_percent'] * width)
                                y_pixel = int(region_info['y_percent'] * height)
                                w_pixel = int(region_info['width_percent'] * width)
                                h_pixel = int(region_info['height_percent'] * height)
                            else:
                                # Pixel format - check if we need to convert from percentages
                                x_val = region_info['x']
                                y_val = region_info['y']
                                w_val = region_info['width']
                                h_val = region_info['height']
                                
                                # If values are small (< 100), they're likely percentages
                                if x_val < 100 and y_val < 100:
                                    # Convert from percentage to pixels
                                    x_pixel = int((x_val / 100.0) * width)
                                    y_pixel = int((y_val / 100.0) * height)
                                    w_pixel = int((w_val / 100.0) * width)
                                    h_pixel = int((h_val / 100.0) * height)
                                else:
                                    # Already in pixels, use directly
                                    x_pixel = int(x_val)
                                    y_pixel = int(y_val)
                                    w_pixel = int(w_val)
                                    h_pixel = int(h_val)
                            
                            # Ensure coordinates are within bounds
                            x_pixel = max(0, min(x_pixel, width - 1))
                            y_pixel = max(0, min(y_pixel, height - 1))
                            w_pixel = max(1, min(w_pixel, width - x_pixel))
                            h_pixel = max(1, min(h_pixel, height - y_pixel))
                            
                            self.calibrated_regions[region_name] = {
                                'x': x_pixel,
                                'y': y_pixel,
                                'width': w_pixel,
                                'height': h_pixel
                            }
                        
                        self.logger.info(f"✅ Loaded {len(self.calibrated_regions)} regions from {region_file}")
                        for region_name, region_data in self.calibrated_regions.items():
                            self.logger.info(f"  {region_name}: x={region_data['x']}, y={region_data['y']}, w={region_data['width']}, h={region_data['height']}")
                        return True
                        
                except Exception as e:
                    self.logger.warning(f"Could not load {region_file}: {e}")
                    continue
            
            # If no existing regions found, try auto-calibration
            self.logger.info("No existing regions found, starting auto-calibration...")
            
            # Capture current frame from virtual camera
            screenshot = self.capture_from_virtual_camera()
            if screenshot is None:
                self.logger.error("Failed to capture from virtual camera for calibration")
                return False
            
            # Use table reference system for auto-calibration
            self.calibrated_regions = self.table_ref.auto_calibrate_from_screenshot(screenshot)
            
            if self.calibrated_regions:
                self.logger.info(f"Auto-calibration successful! Found {len(self.calibrated_regions)} regions")
                for region_name, region_data in self.calibrated_regions.items():
                    self.logger.info(f"  {region_name}: {region_data}")
                return True
            else:
                self.logger.error("Auto-calibration failed - no regions detected")
                return False
                
        except Exception as e:
            self.logger.error(f"Calibration error: {e}")
            return False
    
    def recognize_card_from_region(self, image: np.ndarray, region_name: str) -> Optional[Dict]:
        """Recognize a card from a specific region using enhanced card recognition"""
        # Try enhanced recognition system first (best option)
        if self.enhanced_recognition:
            try:
                result = self.enhanced_recognition.recognize_card(
                    image, 
                    region=(0, 0, image.shape[1], image.shape[0]),
                    four_color_deck=True
                )
                
                if result and result.confidence > 0.1:
                    return {
                        'rank': result.rank,
                        'suit': result.suit,
                        'confidence': result.confidence,
                        'method': result.method
                    }
            except Exception as e:
                self.logger.warning(f"Enhanced recognition failed for {region_name}: {e}")
        
        # Fallback to legacy OCR systems
        results = {}
        for system_name, ocr_system in self.ocr_systems.items():
            try:
                if system_name == "enhanced":
                    result = ocr_system.recognize_card(image, debug=self.config.debug_mode)
                elif system_name == "fallback":
                    result = ocr_system.recognize_card(image, four_color_deck=True)
                
                if result and result.confidence > 0.1:  # Minimum confidence threshold
                    results[system_name] = {
                        'rank': result.rank,
                        'suit': result.suit,
                        'confidence': result.confidence,
                        'method': getattr(result, 'method', system_name)
                    }
                    
            except Exception as e:
                self.logger.warning(f"{system_name} recognition failed for {region_name}: {e}")
        
        # Return best result from legacy systems
        if results:
            best_system = max(results.keys(), key=lambda k: results[k]['confidence'])
            return results[best_system]
        
        return None
    
    def analyze_current_frame(self) -> Optional[Dict]:
        """Analyze current poker state from hardware capture with detailed logging"""
        current_time = time.time()
        
        # Check timing constraints
        if not self._should_analyze_now(current_time):
            return None
        
        # Get screenshot and calibration
        screenshot = self._prepare_analysis()
        if screenshot is None:
            return None
        
        # Perform analysis with detailed logging
        game_state = self._analyze_screenshot_with_logging(screenshot, current_time)
        
        # Store result for UI access
        if game_state:
            self._last_game_state = game_state
            if not hasattr(self, 'analysis_history'):
                self.analysis_history = []
            self.analysis_history.append(game_state)
            if len(self.analysis_history) > 10:
                self.analysis_history.pop(0)
        
        # Update timing
        self.last_analysis_time = current_time
        return game_state
    
    def _analyze_screenshot_with_logging(self, screenshot: np.ndarray, current_time: float) -> Dict:
        """Analyze screenshot with comprehensive logging for UI display"""
        analysis_start_time = time.time()
        
        # Clear previous detailed log
        self.detailed_recognition_log = []
        
        # Add analysis start log
        self._add_ui_log(f"🎯 Starting frame analysis at {time.strftime('%H:%M:%S')}")
        self._add_ui_log(f"📐 Frame dimensions: {screenshot.shape[1]}x{screenshot.shape[0]}")
        self._add_ui_log(f"📍 Processing {len(self.calibrated_regions) if self.calibrated_regions else 0} regions")
        
        game_state = {
            'timestamp': current_time,
            'hero_cards': [],
            'community_cards': [],
            'pot_amount': None,
            'stack_sizes': {},
            'analysis_confidence': 0.0,
            'detailed_results': [],  # For UI display
            'processing_time': 0.0,
            'recognition_method': 'Unknown'
        }
        
        # Use Ultimate Recognition System if available
        if self.ultimate_recognition and self.calibrated_regions:
            self._add_ui_log("🎯 Using Ultimate Card Recognition System")
            game_state = self._analyze_with_ultimate_recognition(screenshot, game_state, current_time)
        else:
            # Fallback to legacy recognition
            self._add_ui_log("🔄 Using legacy recognition system")
            game_state = self._analyze_with_legacy_recognition(screenshot, game_state, current_time)
        
        # Calculate total processing time
        total_time = time.time() - analysis_start_time
        game_state['processing_time'] = total_time
        
        # Update performance stats
        self._update_performance_stats(game_state, total_time)
        
        # Add final summary logs
        hero_count = len(game_state.get('hero_cards', []))
        community_count = len(game_state.get('community_cards', []))
        confidence = game_state.get('analysis_confidence', 0)
        
        self._add_ui_log(f"✅ Analysis complete: {hero_count} hero cards, {community_count} community cards")
        self._add_ui_log(f"📊 Overall confidence: {confidence:.3f}, Processing time: {total_time*1000:.1f}ms")
        
        return game_state
    
    def _analyze_with_ultimate_recognition(self, screenshot: np.ndarray, game_state: Dict, current_time: float) -> Dict:
        """Analyze using Ultimate Card Recognition System with detailed logging"""
        try:
            # Use ultimate recognition system
            card_results = self.ultimate_recognition.recognize_all_cards(
                screenshot=screenshot, 
                regions=self.calibrated_regions
            )
            
            if card_results:
                game_state['recognition_method'] = 'Ultimate'
                
                # Get detailed log entries from ultimate system
                detailed_logs = self.ultimate_recognition.get_detailed_log_entries(card_results)
                for log_entry in detailed_logs:
                    self._add_ui_log(log_entry)
                
                # Convert results to game state format
                total_confidence = 0
                analyzed_cards = 0
                
                for result in card_results:
                    if not result.is_empty and result.card_code != 'error':
                        card_info = {
                            'card': result.card_code,
                            'confidence': result.confidence,
                            'method': result.method,
                            'processing_time': result.processing_time,
                            'region_name': result.region_name
                        }
                        
                        # Add to appropriate category
                        if 'hero_card' in result.region_name:
                            game_state['hero_cards'].append(card_info)
                        elif 'community_card' in result.region_name:
                            game_state['community_cards'].append(card_info)
                        
                        total_confidence += result.confidence
                        analyzed_cards += 1
                        
                        # Log individual card
                        self._add_ui_log(f"   ✅ {result.region_name}: {result.card_code} (conf: {result.confidence:.3f}, {result.method})")
                
                # Calculate overall confidence
                if analyzed_cards > 0:
                    game_state['analysis_confidence'] = total_confidence / analyzed_cards
                
                # Store detailed results for UI
                game_state['detailed_results'] = [
                    {
                        'region': r.region_name,
                        'card': r.card_code,
                        'confidence': r.confidence,
                        'method': r.method,
                        'time': r.processing_time,
                        'is_empty': r.is_empty,
                        'error': r.error_message if r.card_code == 'error' else None
                    }
                    for r in card_results
                ]
                
                # Get and log performance stats
                perf_stats = self.ultimate_recognition.get_performance_stats()
                self._add_ui_log(f"📈 Ultimate Recognition Stats: {perf_stats}")
                
            else:
                self._add_ui_log("⚠️ Ultimate Recognition returned no results")
                game_state['recognition_method'] = 'Ultimate-Failed'
                
        except Exception as e:
            self._add_ui_log(f"❌ Ultimate Recognition error: {e}")
            game_state['recognition_method'] = 'Ultimate-Error'
        
        return game_state
    
    def _analyze_with_legacy_recognition(self, screenshot: np.ndarray, game_state: Dict, current_time: float) -> Dict:
        """Analyze using legacy recognition systems with detailed logging"""
        if not self.calibrated_regions:
            self._add_ui_log("❌ No calibrated regions available")
            return game_state
        
        game_state['recognition_method'] = 'Legacy'
        total_confidence = 0
        analyzed_cards = 0
        
        for region_name, region_data in self.calibrated_regions.items():
            region_start_time = time.time()
            self._add_ui_log(f"🔍 Analyzing {region_name}...")
            
            card_data = self._analyze_region(screenshot, region_name, region_data, current_time)
            region_time = time.time() - region_start_time
            
            if card_data:
                self._add_card_to_game_state(game_state, region_name, card_data)
                total_confidence += card_data['confidence']
                analyzed_cards += 1
                
                self._add_ui_log(f"   ✅ {region_name}: {card_data['rank']}{card_data['suit']} (conf: {card_data['confidence']:.3f}, {card_data['method']}, {region_time*1000:.1f}ms)")
            else:
                self._add_ui_log(f"   ❌ {region_name}: No card detected ({region_time*1000:.1f}ms)")
        
        # Calculate overall confidence
        if analyzed_cards > 0:
            game_state['analysis_confidence'] = total_confidence / analyzed_cards
        
        return game_state
    
    def _add_ui_log(self, message: str):
        """Add a message to the UI log for real-time display"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Store for UI retrieval
        self.detailed_recognition_log.append(formatted_message)
        
        # Keep only last 50 log entries to prevent memory issues
        if len(self.detailed_recognition_log) > 50:
            self.detailed_recognition_log = self.detailed_recognition_log[-50:]
        
        # Call UI callback if available
        if self.ui_log_callback:
            try:
                self.ui_log_callback(formatted_message)
            except Exception as e:
                self.logger.warning(f"UI log callback failed: {e}")
        
        # Also log to standard logger
        self.logger.info(message)
    
    def _update_performance_stats(self, game_state: Dict, processing_time: float):
        """Update performance statistics for monitoring"""
        self.recognition_performance_stats['total_frames'] += 1
        
        # Check if analysis was successful
        hero_cards = len(game_state.get('hero_cards', []))
        community_cards = len(game_state.get('community_cards', []))
        
        if hero_cards > 0 or community_cards > 0:
            self.recognition_performance_stats['successful_frames'] += 1
        
        # Update processing times (keep last 100)
        self.recognition_performance_stats['processing_times'].append(processing_time)
        if len(self.recognition_performance_stats['processing_times']) > 100:
            self.recognition_performance_stats['processing_times'] = self.recognition_performance_stats['processing_times'][-100:]
        
        # Update confidence scores (keep last 100)
        confidence = game_state.get('analysis_confidence', 0)
        if confidence > 0:
            self.recognition_performance_stats['confidence_scores'].append(confidence)
            if len(self.recognition_performance_stats['confidence_scores']) > 100:
                self.recognition_performance_stats['confidence_scores'] = self.recognition_performance_stats['confidence_scores'][-100:]
    
    def get_ui_log_entries(self) -> List[str]:
        """Get current UI log entries for display"""
        return self.detailed_recognition_log.copy()
    
    def get_performance_summary(self) -> str:
        """Get formatted performance summary for UI display"""
        stats = self.recognition_performance_stats
        total = stats['total_frames']
        
        if total == 0:
            return "No frames processed yet"
        
        success_rate = (stats['successful_frames'] / total) * 100
        
        avg_time = 0.0
        if stats['processing_times']:
            avg_time = sum(stats['processing_times']) / len(stats['processing_times'])
        
        avg_confidence = 0.0
        if stats['confidence_scores']:
            avg_confidence = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
        
        return f"Success: {success_rate:.1f}% | Avg Time: {avg_time*1000:.1f}ms | Avg Conf: {avg_confidence:.3f} | Total: {total}"
    
    def set_ui_log_callback(self, callback):
        """Set callback function for real-time UI logging"""
        self.ui_log_callback = callback
    
    def get_live_recognition_status(self) -> Dict:
        """Get current recognition status for live UI updates"""
        camera_connected = (self.virtual_camera is not None and 
                          self.virtual_camera.isOpened() if hasattr(self, 'virtual_camera') else False)
        
        return {
            'total_regions': len(self.calibrated_regions) if self.calibrated_regions else 0,
            'recognition_system': 'Ultimate' if self.ultimate_recognition else 'Legacy',
            'performance_summary': self.get_performance_summary(),
            'recent_logs': self.get_ui_log_entries()[-10:],  # Last 10 log entries
            'camera_connected': camera_connected,
            'regions_loaded': self.calibrated_regions is not None,
            'last_analysis': getattr(self, '_last_game_state', None),
            'analysis_count': len(getattr(self, 'analysis_history', []))
        }
    
    def _should_analyze_now(self, current_time: float) -> bool:
        """Check if enough time has passed for next analysis"""
        return current_time - self.last_analysis_time >= self.config.analysis_interval
    
    def _prepare_analysis(self) -> Optional[np.ndarray]:
        """Prepare for analysis by capturing screenshot and ensuring calibration"""
        screenshot = self.capture_from_virtual_camera()
        if screenshot is None:
            return None
        
        # Auto-calibrate if not done yet
        if self.calibrated_regions is None:
            if not self.auto_calibrate_from_hardware():
                return None
        
        return screenshot
    
    def _analyze_screenshot(self, screenshot: np.ndarray, current_time: float) -> Dict:
        """Analyze screenshot and extract game state"""
        game_state = {
            'timestamp': current_time,
            'hero_cards': [],
            'community_cards': [],
            'pot_amount': None,
            'stack_sizes': {},
            'analysis_confidence': 0.0
        }
        
        total_confidence = 0
        analyzed_cards = 0
        
        for region_name, region_data in self.calibrated_regions.items():
            card_data = self._analyze_region(screenshot, region_name, region_data, current_time)
            if card_data:
                self._add_card_to_game_state(game_state, region_name, card_data)
                total_confidence += card_data['confidence']
                analyzed_cards += 1
        
        # Calculate overall confidence
        if analyzed_cards > 0:
            game_state['analysis_confidence'] = total_confidence / analyzed_cards
        
        return game_state
    
    def _analyze_region(self, screenshot: np.ndarray, region_name: str, region_data: Dict, current_time: float) -> Optional[Dict]:
        """Analyze a single region and return card data if found"""
        try:
            # Extract region from screenshot using direct coordinates
            x = region_data['x']
            y = region_data['y']
            w = region_data['width']
            h = region_data['height']
            
            # Ensure coordinates are within bounds
            height, width = screenshot.shape[:2]
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = min(w, width - x)
            h = min(h, height - y)
            
            # Extract region
            region_img = screenshot[y:y+h, x:x+w]
            
            if region_img is None or region_img.size == 0:
                return None
            
            # Save debug images if enabled (disabled by default to prevent spam)
            if getattr(self.config, 'save_debug_regions', False):
                debug_filename = f"debug_region_{region_name}_{int(current_time)}.png"
                cv2.imwrite(debug_filename, region_img)
                
                # Check if region contains mostly green (empty table)
                avg_color = np.mean(region_img, axis=(0,1))
                is_green_table = (avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2] and avg_color[1] > 80)
                
                if is_green_table:
                    self.logger.warning(f"Region {region_name} appears to be empty table (green): BGR({avg_color[0]:.0f}, {avg_color[1]:.0f}, {avg_color[2]:.0f})")
                else:
                    self.logger.info(f"Region {region_name} contains potential card content: BGR({avg_color[0]:.0f}, {avg_color[1]:.0f}, {avg_color[2]:.0f})")
            
            # Recognize card if this is a card region
            if 'hero_card' in region_name or 'community_card' in region_name or 'card_' in region_name:
                return self.recognize_card_from_region(region_img, region_name)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error analyzing region {region_name}: {e}")
            return None
    
    def _add_card_to_game_state(self, game_state: Dict, region_name: str, card_data: Dict) -> None:
        """Add recognized card to appropriate game state list"""
        card_info = {
            'card': f"{card_data['rank']}{card_data['suit']}",
            'confidence': card_data['confidence'],
            'method': card_data['method']
        }
        
        if 'hero_card' in region_name:
            game_state['hero_cards'].append(card_info)
        elif 'community_card' in region_name or 'card_' in region_name:
            game_state['community_cards'].append(card_info)
    
    def get_poker_advice(self, game_state: Dict) -> Dict:
        """Generate poker advice based on analyzed game state"""
        try:
            advice = {
                'action': 'unknown',
                'confidence': 0.0,
                'reasoning': 'Insufficient information',
                'alternative_actions': []
            }
            
            # Basic advice logic (you can enhance this)
            hero_cards = game_state.get('hero_cards', [])
            
            if len(hero_cards) >= 2:
                # Extract card values for analysis
                hero_card_strings = [card['card'] for card in hero_cards[:2]]
                
                # Simple strength assessment
                if self._is_premium_hand(hero_card_strings):
                    advice['action'] = 'raise'
                    advice['confidence'] = 0.8
                    advice['reasoning'] = 'Premium starting hand detected'
                elif self._is_playable_hand(hero_card_strings):
                    advice['action'] = 'call'
                    advice['confidence'] = 0.6
                    advice['reasoning'] = 'Playable hand, consider position'
                else:
                    advice['action'] = 'fold'
                    advice['confidence'] = 0.7
                    advice['reasoning'] = 'Weak starting hand'
            
            return advice
            
        except Exception as e:
            self.logger.error(f"Error generating advice: {e}")
            return {'action': 'fold', 'confidence': 0.0, 'reasoning': f'Analysis error: {e}'}
    
    def _is_premium_hand(self, cards: list) -> bool:
        """Check if hand contains premium cards"""
        if len(cards) < 2:
            return False
        
        ranks = [card[:-1] for card in cards]  # Remove suit
        
        # Pocket pairs AA, KK, QQ, JJ
        if ranks[0] == ranks[1] and ranks[0] in ['A', 'K', 'Q', 'J']:
            return True
        
        # High suited connectors
        high_cards = ['A', 'K', 'Q', 'J']
        if all(rank in high_cards for rank in ranks):
            return True
        
        return False
    
    def _is_playable_hand(self, cards: list) -> bool:
        """Check if hand is playable"""
        if len(cards) < 2:
            return False
        
        ranks = [card[:-1] for card in cards]
        
        # Any pair
        if ranks[0] == ranks[1]:
            return True
        
        # High cards
        high_cards = ['A', 'K', 'Q', 'J', '10']
        if any(rank in high_cards for rank in ranks):
            return True
        
        return False
    
    def start_analysis_loop(self) -> None:
        """Start continuous analysis loop"""
        self.logger.info("Starting hardware capture analysis loop...")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                # Analyze current frame
                game_state = self.analyze_current_frame()
                
                if game_state:
                    # Generate advice
                    advice = self.get_poker_advice(game_state)
                    
                    # Log results
                    self.logger.info(f"Analysis at {time.strftime('%H:%M:%S')}")
                    self.logger.info(f"  Hero cards: {game_state['hero_cards']}")
                    self.logger.info(f"  Community: {game_state['community_cards']}")
                    self.logger.info(f"  Confidence: {game_state['analysis_confidence']:.2f}")
                    self.logger.info(f"  Advice: {advice['action']} ({advice['confidence']:.2f}) - {advice['reasoning']}")
                    
                    # Save state for GUI display
                    self._save_current_state(game_state, advice)
                
                # Sleep before next analysis
                time.sleep(self.config.analysis_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Analysis loop stopped by user")
        except Exception as e:
            self.logger.error(f"Analysis loop error: {e}")
    
    def _save_current_state(self, game_state: Dict, advice: Dict) -> None:
        """Save current state for GUI or external access"""
        try:
            import json
            
            current_state = {
                'game_state': game_state,
                'advice': advice,
                'timestamp': time.time()
            }
            
            with open('current_poker_state.json', 'w') as f:
                json.dump(current_state, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Failed to save current state: {e}")
    
    def capture_table_screenshot_for_regions(self) -> Optional[str]:
        """Capture a screenshot for manual region creation"""
        try:
            # Ensure virtual camera is connected
            if self.virtual_camera is None or not self.virtual_camera.isOpened():
                if not self.connect_to_virtual_camera():
                    return None
            
            print("📸 Capturing table screenshot for region creation...")
            print("   Make sure all cards you want to detect are visible!")
            
            # Capture frame
            ret, frame = self.virtual_camera.read()
            
            if not ret or frame is None:
                self.logger.error("Failed to capture frame for screenshot")
                return None
            
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"poker_table_for_regions_{timestamp}.png"
            
            # Save screenshot for region creation
            cv2.imwrite(filename, frame)
            
            self.logger.info(f"✅ Table screenshot saved: {filename}")
            self.logger.info(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
            
            # Check image quality
            avg_brightness = np.mean(frame)
            self.logger.info(f"   Average brightness: {avg_brightness:.1f}")
            
            if avg_brightness < 30:
                self.logger.warning("⚠️ Image appears quite dark - check OBS settings")
            elif avg_brightness > 200:
                self.logger.warning("⚠️ Image appears very bright - check OBS settings")
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error capturing table screenshot: {e}")
            return None

def test_hardware_capture():
    """Test function for hardware capture system"""
    print("Testing Hardware Capture System...")
    
    # Initialize system
    config = HardwareCaptureConfig(debug_mode=True)
    capture_system = HardwareCaptureSystem(config)
    
    # Test virtual camera connection
    if capture_system.connect_to_virtual_camera():
        print(f"✅ Connected to OBS Virtual Camera at index {capture_system.camera_index}")
    else:
        print("❌ OBS Virtual Camera not found or not working")
        print("Make sure:")
        print("  1. OBS Studio is running")
        print("  2. Virtual Camera is started in OBS")
        print("  3. UGREEN capture card is added as video source in OBS")
        return False
    
    # Test screenshot capture
    screenshot = capture_system.capture_from_virtual_camera()
    if screenshot is not None:
        print(f"✅ Virtual camera capture successful: {screenshot.shape}")
        # Test screenshot saved only during explicit testing
        
        # Check if image has content (not just black)
        avg_pixel = np.mean(screenshot)
        print(f"Average pixel value: {avg_pixel:.1f}")
        if avg_pixel < 10:
            print("⚠️ Captured image appears mostly black - check video source in OBS")
        else:
            print("✅ Captured image has visible content")
    else:
        print("❌ Virtual camera capture failed")
        return False
    
    # Test auto-calibration
    if capture_system.auto_calibrate_from_hardware():
        print("✅ Auto-calibration successful")
    else:
        print("❌ Auto-calibration failed")
    
    # Test analysis
    game_state = capture_system.analyze_current_frame()
    if game_state:
        print(f"✅ Analysis successful: {len(game_state.get('hero_cards', []))} hero cards, {len(game_state.get('community_cards', []))} community cards")
    else:
        print("⚠️ Analysis returned no results")
    
    # Cleanup
    if capture_system.virtual_camera:
        capture_system.virtual_camera.release()
    
    return True

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run test
    test_hardware_capture()
