"""
Main Window Class for Modern Poker Bot UI
Handles the primary window setup and coordination between components.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import queue
import datetime
from datetime import datetime

from .header_panel import HeaderPanel
from .table_view_panel import TableViewPanel
from .game_info_panel import GameInfoPanel
from .control_panel import ControlPanel
from .status_bar import StatusBar

# Import the PokerStarsBot from the src directory
import sys
import os
# Add the src directory to the path
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from poker_bot import PokerStarsBot
from window_capture import PokerStarsWindowCapture
from obs_capture import OBSCaptureSystem, OBSIntegratedBot


class MainWindow:
    """Main window class that coordinates all UI components."""
    
    def __init__(self, recognition_system='standard', show_regions=False, config_path='region_config.json'):
        """Initialize the main window and all components."""
        # Store initialization parameters
        self.recognition_system = recognition_system
        self.show_regions = show_regions
        self.config_path = config_path
        
        # Create main window
        self.root = tk.Tk()
        self.root.configure(bg='#2b2b2b')
        self.root.title("PokerStars Bot - Professional Edition v2.0")
        self.root.geometry("2400x1600")  # Even larger window for maximum table display
        
        # Make window resizable and start maximized
        self.root.resizable(True, True)
        self.root.state('zoomed')  # Start maximized on Windows
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg='#2b2b2b')
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.main_frame.grid_columnconfigure(0, weight=6)  # Give maximum space to table view
        self.main_frame.grid_columnconfigure(1, weight=1)  # Less space for info panel
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Bot components
        self.bot = None
        self.window_capture = PokerStarsWindowCapture()
        self.obs_capture = OBSCaptureSystem()
        self.obs_bot = None
        
        # State variables
        self.running = False
        self.capture_thread = None
        self.capture_mode = "window"
        self.capture_interval = 0.5
        self.last_screenshot = None
        self.last_analysis = None
        self.current_screenshot = None  # For region refresh functionality
        self.last_successful_analysis = None  # To store the last successful analysis
        
        # Statistics
        self.capture_count = 0
        self.success_count = 0
        
        # Message queue for thread-safe UI updates
        self.message_queue = queue.Queue()
        
        # Initialize UI components
        self.setup_ui_components()
        
        # Start message processing
        self.process_messages()
        
        # Create necessary directories
        self.create_directories()
        
        # Initialize bot
        self.initialize_bot()
    
    def create_directories(self):
        """Create necessary directories for debug output (from poker_bot.py)."""
        directories = [
            'screenshots', 'debug_images', 'debug_cards', 
            'debug_community', 'card_templates', 'regions',
            'debug_cards/improved', 'debug_cards/empty_detection', 'debug_cards/color_analysis'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        self.log_message(f"Created {len(directories)} debug directories")
    
    def setup_ui_components(self):
        """Setup all UI components."""
        # Header panel
        self.header_panel = HeaderPanel(self.main_frame)
        self.header_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Table view panel (left side)
        self.table_panel = TableViewPanel(self.main_frame, self)
        self.table_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Game info panel (right side)
        self.info_panel = GameInfoPanel(self.main_frame)
        self.info_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Control panel (bottom of table view)
        self.control_panel = ControlPanel(self.table_panel.get_control_frame(), self)
        
        # Status bar
        self.status_bar = StatusBar(self.main_frame)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    
    def initialize_bot(self):
        """Initialize the bot components."""
        try:
            self.log_message("="*60)
            self.log_message("POKERSTARS BOT - MODERN UI INITIALIZATION")
            self.log_message("="*60)
            self.log_message("Features:")
            self.log_message("✓ Modern UI with enhanced visualization")
            self.log_message("✓ Improved card recognition with color analysis")
            self.log_message("✓ Empty slot detection and duplicate prevention")
            self.log_message("✓ Region configuration and calibration")
            self.log_message("✓ Real-time livestream with overlay support")
            self.log_message("✓ OBS Virtual Camera integration")
            self.log_message("✓ Enhanced statistics and logging")
            self.log_message("="*60)
            
            # Import from the src directory
            from region_loader import RegionLoader
            
            # Log which card recognition system we're using
            self.log_message(f"Target: Initializing with {self.recognition_system} card recognition system")
            
            # Initialize the bot with the specified recognition system
            self.bot = PokerStarsBot(recognition_type=self.recognition_system)
            
            # Log the actual recognition system being used
            if hasattr(self.bot, 'card_recognizer'):
                recognizer_type = type(self.bot.card_recognizer).__name__
                self.log_message(f"SUCCESS: {recognizer_type} loaded successfully")
            
            # Load the specified region configuration
            self.log_message(f"Loading regions from: {self.config_path}")
            
            # Ensure the config path is absolute
            if not os.path.isabs(self.config_path):
                # If relative, make it relative to the project root
                project_root = os.path.dirname(os.path.dirname(src_path))
                self.config_path = os.path.join(project_root, self.config_path)
            
            loader = RegionLoader(config_file=self.config_path)
            
            # Check if saved regions exist and log what we're loading
            if loader.regions_exist():
                self.log_message("Loading saved regions for bot components...")
                
                # Load all regions from the config file
                all_regions = loader.load_regions()
                
                # Separate hero and community regions
                hero_regions = {}
                community_regions = {}
                
                for name, region in all_regions.items():
                    if 'hero_card' in name:
                        hero_regions[name] = region
                    elif name.startswith('card_'):
                        community_regions[name] = region
                
                # Force update card recognizer with saved regions
                if hero_regions and hasattr(self.bot, 'card_recognizer'):
                    # Update the card recognizer with hero regions
                    if hasattr(self.bot.card_recognizer, 'update_regions'):
                        self.bot.card_recognizer.update_regions(hero_regions)
                    else:
                        self.bot.card_recognizer.card_regions = hero_regions
                    self.log_message(f"[SUCCESS] Loaded {len(hero_regions)} hero card regions into {type(self.bot.card_recognizer).__name__}")
                    for name, region in hero_regions.items():
                        self.log_message(f"   {name}: x={region.get('x', 0):.4f}, y={region.get('y', 0):.4f}")
                else:
                    self.log_message("[WARNING] Failed to load hero card regions - no hero regions found or card_recognizer unavailable")
                
                # Force update community card detector with saved regions
                if community_regions and hasattr(self.bot, 'community_detector'):
                    # Update the community detector with community regions
                    if hasattr(self.bot.community_detector, 'update_regions'):
                        self.bot.community_detector.update_regions(community_regions)
                    else:
                        self.bot.community_detector.community_card_regions = community_regions
                    self.log_message(f"[SUCCESS] Loaded {len(community_regions)} community card regions into CommunityCardDetector")
                
                # Enable region visualization if requested
                if self.show_regions:
                    self.log_message("Enabling region visualization on livestream")
                    # Update the table panel with all regions for visualization
                    self.table_panel.custom_regions = all_regions
                    self.table_panel.show_debug_overlay.set(True)
                    self.log_message("[SUCCESS] Regions will be displayed on the livestream")
            else:
                self.log_message(f"[WARNING] No saved regions found at path: {self.config_path}")
                
            self.log_message("SUCCESS: Bot initialization complete")
                
        except ImportError as e:
            self.log_message(f"[ERROR] Failed to initialize bot: {e}")
            import traceback
            self.log_message(traceback.format_exc())
        except Exception as e:
            self.log_message(f"[ERROR] Bot initialization error: {e}")
            import traceback
            self.log_message(traceback.format_exc())
    
    def log_message(self, message):
        """Add a message to the log (thread-safe)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.message_queue.put(("log", formatted_message))
    
    def process_messages(self):
        """Process messages from the queue."""
        try:
            while not self.message_queue.empty():
                msg_type, content = self.message_queue.get_nowait()
                
                if msg_type == "log":
                    self.info_panel.add_log_message(content)
                elif msg_type == "status":
                    self.status_bar.update_status(content)
                elif msg_type == "update_display":
                    screenshot, analysis = content
                    self.update_display_internal(screenshot, analysis)
                elif msg_type == "enhanced_update_display":
                    screenshot, analysis = content
                    self.update_display_with_enhanced_info(screenshot, analysis)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def update_display_internal(self, screenshot, analysis):
        """Internal method to update display (called from main thread)."""
        try:
            # Store current screenshot for refresh functionality
            self.current_screenshot = screenshot
            
            # Display screenshot
            self.table_panel.display_screenshot(screenshot)
            
            # Update game information
            self.info_panel.update_game_info(analysis)
            
            # Update statistics
            self.status_bar.update_statistics(self.capture_count, self.success_count)
            
        except Exception as e:
            self.log_message(f"Error updating display: {e}")
    
    def enhanced_analysis_logging(self, analysis):
        """Enhanced logging for improved recognition system results."""
        try:
            if not analysis:
                return
                
            # Log detailed hole card results if using improved recognition
            if (hasattr(self.bot, 'card_recognizer') and 
                hasattr(self.bot.card_recognizer, '__class__') and
                'Improved' in str(self.bot.card_recognizer.__class__)):
                
                if 'hole_cards' in analysis and analysis['hole_cards']:
                    hole_cards = analysis['hole_cards']
                    if hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                        # Get detailed card information if available
                        if hasattr(hole_cards, 'cards') and len(hole_cards.cards) >= 2:
                            card1, card2 = hole_cards.cards[0], hole_cards.cards[1]
                            if card1 and card2:
                                self.log_message(f"IMPROVED RECOGNITION: Hero cards {card1} and {card2}")
                                
                                # Log confidence if available
                                confidence = getattr(hole_cards, 'detection_confidence', 0.0)
                                if confidence > 0:
                                    self.log_message(f"   Recognition confidence: {confidence:.3f}")
                
                # Log community card details
                if 'community_cards' in analysis and analysis['community_cards']:
                    community_cards = analysis['community_cards']
                    if hasattr(community_cards, 'count') and community_cards.count > 0:
                        self.log_message(f"IMPROVED RECOGNITION: {community_cards.count} community cards detected")
                        confidence = getattr(community_cards, 'detection_confidence', 0.0)
                        if confidence > 0:
                            self.log_message(f"   Community cards confidence: {confidence:.3f}")
                
        except Exception as e:
            self.log_message(f"Error in enhanced analysis logging: {e}")

    def update_display_with_enhanced_info(self, screenshot, analysis):
        """Update display with enhanced recognition information."""
        try:
            # Update the standard display
            self.update_display_internal(screenshot, analysis)
            
            # Add enhanced logging for improved recognition
            self.enhanced_analysis_logging(analysis)
            
            # Format and log detailed output
            if analysis:
                formatted_output = self.format_output(analysis)
                # Log key parts of the formatted output
                for line in formatted_output.split('\n'):
                    if line.strip() and 'captured at' not in line:  # Skip timestamp line
                        self.log_message(f"ANALYSIS: {line.strip()}")
                        
        except Exception as e:
            self.log_message(f"Error in enhanced display update: {e}")

    def start_bot(self):
        """Start the bot monitoring."""
        try:
            if self.capture_mode == "obs":
                if not self.obs_capture.get_capture_stats()['connected']:
                    self.log_message("Please connect to OBS Virtual Camera first")
                    return
                
                # Start OBS continuous capture
                if not self.obs_capture.start_capture():
                    self.log_message("Failed to start OBS capture")
                    return
            else:
                if not self.window_capture.selected_window:
                    self.log_message("Please find a table first")
                    return
            
            # Initialize bot if needed
            if not self.bot:
                self.bot = PokerStarsBot()
            
            self.running = True
            self.header_panel.set_bot_status("Running", "green")
            self.header_panel.set_connection_status("Connected", "green")
            
            # Update control panel
            self.control_panel.set_bot_running(True)
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
            self.capture_thread.start()
            
            self.log_message("Bot started successfully")
            
        except Exception as e:
            self.log_message(f"Error starting bot: {e}")
    
    def stop_bot(self):
        """Stop the bot monitoring."""
        try:
            self.running = False
            self.header_panel.set_bot_status("Stopped", "orange")
            
            # Stop OBS capture if running
            if self.capture_mode == "obs":
                self.obs_capture.stop_capture()
            
            # Update control panel
            self.control_panel.set_bot_running(False)
            
            self.log_message("Bot stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping bot: {e}")
    
    def capture_loop(self):
        """Main capture loop running in separate thread."""
        # Ensure we have the time module imported within this method's scope
        import time
        
        # Initialize variables
        last_capture_time = 0
        min_capture_interval = 0.5  # Reduce to half a second for more responsiveness
        last_livestream_update = 0
        livestream_interval = 0.1  # Very short interval just for display updates
        
        while self.running:
            try:
                start_time = time.time()
                current_time = start_time
                
                # Always capture for livestream display
                livestream_screenshot = None
                
                # Get screenshot based on capture mode
                screenshot = None
                if self.capture_mode == "obs":
                    # Get latest frame from OBS continuous capture
                    screenshot = self.obs_capture.get_latest_frame()
                    
                    # Verify frame quality
                    if screenshot is not None and (screenshot.size == 0 or screenshot.shape[0] < 10 or screenshot.shape[1] < 10):
                        self.log_message("⚠️ OBS frame has invalid dimensions, trying fallback")
                        screenshot = None
                    if screenshot is None:
                        # Fallback to single frame capture
                        screenshot = self.obs_capture.capture_single_frame()
                        self.log_message("🔄 Fallback to single frame capture")
                else:
                    screenshot = self.window_capture.capture_current_window()
                
                # Always copy screenshot for livestream
                if screenshot is not None and screenshot.size > 0:
                    livestream_screenshot = screenshot.copy()
                    
                    # Update livestream display more frequently than analysis
                    if current_time - last_livestream_update > livestream_interval:
                        # Just update the display without analysis for smooth video
                        self.message_queue.put(("update_display", (livestream_screenshot, self.last_analysis)))
                        last_livestream_update = current_time
                
                # Check if enough time has passed for full analysis
                full_analysis_due = current_time - last_capture_time >= min_capture_interval
                
                # Only do full analysis at the specified interval
                if full_analysis_due and screenshot is not None and screenshot.size > 0:
                    # Update last capture time
                    last_capture_time = current_time
                    # Ensure bot is properly initialized
                    if not self.bot:
                        self.bot = PokerStarsBot()
                        if self.capture_mode == "obs":
                            self.bot.window_capture = None  # Disable window capture for OBS mode
                        # CRITICAL FIX: Ensure regions are reloaded if bot gets recreated
                        self.refresh_regions()
                        self.log_message("[INFO] Bot recreated and regions reloaded in capture loop")
                    
                    # CRITICAL FIX: Ensure the bot components have valid regions before detection
                    # This prevents false detections with invalid regions and ensures recognition continues after calibration
                    if hasattr(self.bot, 'card_recognizer') and hasattr(self.bot, 'community_detector'):
                        from region_loader import RegionLoader
                        loader = RegionLoader()
                        
                        # Refresh regions in bot components if they exist on disk but aren't set in the recognizers
                        if loader.regions_exist():
                            # Check if card recognizer has empty regions but saved regions exist
                            hero_regions = loader.get_hero_card_regions()
                            if (hero_regions and 
                                (not hasattr(self.bot.card_recognizer, 'card_regions') or 
                                 not self.bot.card_recognizer.card_regions)):
                                self.log_message("[FIX] Reloading hero card regions during capture")
                                self.bot.card_recognizer.update_regions(hero_regions)
                                
                            # Check if community detector has empty regions but saved regions exist
                            community_regions = loader.get_community_card_regions()
                            if (community_regions and 
                                (not hasattr(self.bot.community_detector, 'community_card_regions') or 
                                 not self.bot.community_detector.community_card_regions)):
                                self.log_message("[FIX] Reloading community card regions during capture")
                                self.bot.community_detector.update_regions(community_regions)
                    
                    # Save periodic debug images to help diagnose recognition issues
                    if self.capture_count % 20 == 0:  # Save every 20th frame (reduced frequency)
                        import cv2
                        import os
                        import time
                        
                        os.makedirs("screenshots", exist_ok=True)
                        timestamp = int(time.time())
                        cv2.imwrite(f"screenshots/capture_{timestamp}.png", screenshot)
                    
                    # Only do full analysis if it's time
                    if full_analysis_due:
                        # Analyze the screenshot with proper error handling
                        try:
                            # Run enhanced analysis with debug mode enabled less frequently
                            debug_mode = (self.capture_count % 10 == 0)
                            
                            # Log that analysis is starting
                            self.log_message(f"Starting analysis of frame #{self.capture_count+1}...")
                            
                            # Perform the analysis
                            analysis = self.bot.analyze_game_state(screenshot, debug=debug_mode)
                            
                            # Validate analysis results
                            if analysis and isinstance(analysis, dict):
                                # Store last successful analysis
                                self.last_analysis = analysis
                                
                                # Log successful analysis with detected cards
                                card_info = ""
                                if 'hole_cards' in analysis and analysis['hole_cards'] and hasattr(analysis['hole_cards'], 'is_valid'):
                                    if analysis['hole_cards'].is_valid():
                                        card_info = f"Hole cards: {analysis['hole_cards']}"
                                
                                if 'community_cards' in analysis and analysis['community_cards'] and hasattr(analysis['community_cards'], 'cards'):
                                    comm_cards = [str(c) for c in analysis['community_cards'].cards if c]
                                    if comm_cards:
                                        card_info += f", Community: {', '.join(comm_cards)}"
                                
                                # Log analysis completion with detailed results
                                if card_info:
                                    self.log_message(f"[SUCCESS] Analysis complete: {card_info}")
                                    # Store last successful analysis with card data
                                    self.last_successful_analysis = analysis
                                else:
                                    self.log_message("[WARNING] Analysis complete, but no cards detected")
                                
                                # Update UI in main thread with enhanced analysis
                                self.message_queue.put(("enhanced_update_display", (screenshot, analysis)))
                                
                                # Update statistics
                                self.capture_count += 1
                                if self.has_valid_detection(analysis):
                                    self.success_count += 1
                                    # Update status bar with most recent detection
                                    self.message_queue.put(("status", f"Detection successful: {self.success_count}/{self.capture_count}"))
                            else:
                                self.log_message("[WARNING] Analysis returned invalid results")
                                # Still update the display to keep the livestream going
                                self.message_queue.put(("update_display", (screenshot, self.last_successful_analysis)))
                                
                        except Exception as analysis_error:
                            self.log_message(f"[WARNING] Analysis error: {analysis_error}")
                            # Still update display with screenshot but keep previous analysis
                            self.message_queue.put(("update_display", (screenshot, self.last_successful_analysis)))
                            self.capture_count += 1
                    else:
                        # For frames between analysis intervals, just update the display
                        # This maintains a smooth livestream while only doing analysis at intervals
                        self.message_queue.put(("update_display", (screenshot, self.last_analysis)))
                
                else:
                    # Explicitly log frame issues for debugging
                    if screenshot is None:
                        self.log_message("⚠️ Captured frame was None")
                    elif screenshot.size == 0:
                        self.log_message("⚠️ Captured frame had size 0")
                    
                    # Don't wait the full interval on error - retry more quickly
                    time.sleep(0.1)
                    continue
                
                # Short sleep to prevent CPU overuse, but keep livestream responsive
                time.sleep(0.05)
                
            except Exception as e:
                self.log_message(f"❌ Error in capture loop: {e}")
                # Shorter sleep on error to recover more quickly
                time.sleep(0.5)
    
    def has_valid_detection(self, analysis):
        """Check if analysis contains valid detections."""
        if not analysis:
            return False
        
        # Check for any valid detections
        valid_detections = 0
        
        # Check hole cards
        if 'hole_cards' in analysis and analysis['hole_cards']:
            hole_cards = analysis['hole_cards']
            if hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                valid_detections += 1
        
        # Check community cards
        if 'community_cards' in analysis and analysis['community_cards']:
            community_cards = analysis['community_cards']
            if hasattr(community_cards, 'count') and community_cards.count > 0:
                valid_detections += 1
        
        # Check table info
        if 'table_info' in analysis and analysis['table_info']:
            table_info = analysis['table_info']
            if hasattr(table_info, 'players') and len(table_info.players) > 0:
                valid_detections += 1
        
        return valid_detections > 0
    
    def find_table(self):
        """Find and select poker table."""
        try:
            if self.capture_mode == "obs":
                # OBS mode - check connection
                if not self.obs_capture.get_capture_stats()['connected']:
                    self.log_message("Please connect to OBS Virtual Camera first")
                    return
                
                obs_stats = self.obs_capture.get_capture_stats()
                self.info_panel.set_window_info(f"OBS: {obs_stats['resolution']} @ {obs_stats['fps']}fps")
                self.log_message("Using OBS Virtual Camera as source")
                
                # Update bot to use OBS mode
                if self.bot:
                    self.bot.window_capture = None  # Disable window capture
            else:
                # Window mode - find window
                selected_window = self.window_capture.select_best_window()
                
                if selected_window:
                    self.info_panel.set_window_info(f"Window: {selected_window['title'][:50]}...")
                    self.log_message("PokerStars window found and selected")
                    
                    # Update bot to use window capture
                    if self.bot:
                        self.bot.window_capture = self.window_capture
                else:
                    self.log_message("No PokerStars windows found")
                
        except Exception as e:
            self.log_message(f"Error finding table: {e}")
    
    def test_capture(self):
        """Test screen capture functionality."""
        try:
            if self.capture_mode == "obs":
                if not self.obs_capture.get_capture_stats()['connected']:
                    self.log_message("Please connect to OBS Virtual Camera first")
                    return
                screenshot = self.obs_capture.capture_single_frame()
            else:
                if not self.window_capture.selected_window:
                    self.log_message("Please find a table first")
                    return
                screenshot = self.window_capture.capture_current_window()
            
            if screenshot is not None:
                self.table_panel.display_screenshot(screenshot)
                self.log_message("Screen capture test successful")
            else:
                self.log_message("Screen capture test failed")
                
        except Exception as e:
            self.log_message(f"Error testing capture: {e}")
    
    def connect_obs_camera(self):
        """Connect to OBS Virtual Camera."""
        try:
            self.control_panel.set_obs_status("Connecting...")
            
            # Try to connect
            if self.obs_capture.connect_to_obs_camera():
                self.control_panel.set_obs_connected(True)
                
                # Initialize OBS bot
                self.obs_bot = OBSIntegratedBot()
                self.obs_bot.obs_capture = self.obs_capture
                
                self.log_message("OBS Virtual Camera connected successfully")
            else:
                self.control_panel.set_obs_connected(False)
                self.log_message("Failed to connect to OBS Virtual Camera")
                
        except Exception as e:
            self.control_panel.set_obs_connected(False)
            self.log_message(f"Error connecting to OBS: {e}")
    
    def disconnect_obs_camera(self):
        """Disconnect from OBS Virtual Camera."""
        try:
            self.obs_capture.disconnect()
            self.control_panel.set_obs_connected(False)
            
            if self.obs_bot:
                self.obs_bot.disconnect()
                self.obs_bot = None
            
            self.log_message("OBS Virtual Camera disconnected")
            
        except Exception as e:
            self.log_message(f"Error disconnecting OBS: {e}")
    
    def set_capture_mode(self, mode):
        """Set the capture mode."""
        self.capture_mode = mode
        if mode == "obs":
            self.log_message("Switched to OBS Virtual Camera mode")
        else:
            self.log_message("Switched to Window Capture mode")
    
    def format_output(self, analysis: dict) -> str:
        """Format the analysis results for display (from poker_bot.py)."""
        try:
            if not analysis or 'error' in analysis:
                return f"Analysis Error: {analysis.get('error', 'Unknown error')}"
            
            game_state = analysis.get('game_state')
            hole_cards = analysis.get('hole_cards')
            community_cards = analysis.get('community_cards')
            table_info = analysis.get('table_info')
            
            # Build output string
            output_parts = []
            
            # Timestamp
            timestamp = time.strftime("%H:%M:%S", time.localtime(analysis.get('timestamp', time.time())))
            output_parts.append(f"Table captured at {timestamp}")
            
            # Basic game info
            info_parts = []
            if game_state and hasattr(game_state, 'active_players') and game_state.active_players > 0:
                info_parts.append(f"Players: {game_state.active_players}")
            
            if community_cards and hasattr(community_cards, 'count') and community_cards.count > 0:
                info_parts.append(f"Phase: {getattr(community_cards, 'phase', 'Unknown')}")
            
            if hole_cards and hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                info_parts.append(f"Hole cards: {hole_cards}")
            
            if community_cards and hasattr(community_cards, 'count') and community_cards.count > 0:
                if hasattr(community_cards, 'get_visible_cards'):
                    visible_cards = community_cards.get_visible_cards()
                    if visible_cards:
                        cards_str = ", ".join(str(card) for card in visible_cards)
                        info_parts.append(f"Community: {cards_str}")
            
            # Add table information
            if table_info and hasattr(table_info, 'players') and len(table_info.players) > 0:
                # Try to get hero info if table analyzer is available
                if hasattr(self.bot, 'table_analyzer'):
                    hero = self.bot.table_analyzer.get_hero_info(table_info)
                    if hero:
                        info_parts.append(f"Hero Stack: {hero.stack_size:.1f}BB")
                        info_parts.append(f"Position: {hero.position}")
                
                info_parts.append(f"Pot: {table_info.pot_size:.1f}BB")
                info_parts.append(f"Stakes: {getattr(table_info, 'table_stakes', 'Unknown')}")
            
            if info_parts:
                output_parts.append(" - ".join(info_parts))
            
            # Detailed recognition info
            details = []
            if hole_cards and hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                confidence = getattr(hole_cards, 'detection_confidence', 0.0)
                details.append(f"Hole Cards: {hole_cards} (confidence: {confidence:.3f})")
            
            if community_cards and hasattr(community_cards, 'count') and community_cards.count > 0:
                confidence = getattr(community_cards, 'detection_confidence', 0.0)
                details.append(f"Community Cards: {community_cards} (confidence: {confidence:.3f})")
            
            # Add detailed table analysis
            if table_info and hasattr(table_info, 'players') and len(table_info.players) > 0:
                details.append(f"Table Analysis: {len(table_info.players)} players detected")
                dealer_seat = getattr(table_info, 'dealer_seat', 'Unknown')
                hero_seat = getattr(table_info, 'hero_seat', 'Unknown')
                details.append(f"Dealer: Seat {dealer_seat}, Hero: Seat {hero_seat}")
            
            if details:
                output_parts.extend(details)
            
            return "\n".join(output_parts)
            
        except Exception as e:
            return f"Output formatting error: {e}"
    
    def print_statistics(self):
        """Print bot performance statistics (from poker_bot.py)."""
        try:
            success_rate = (self.success_count / max(self.capture_count, 1)) * 100
            
            stats_message = "\n" + "="*60
            stats_message += "\nPOKERSTARS BOT STATISTICS"
            stats_message += "\n" + "="*60
            stats_message += f"\nTotal captures: {self.capture_count}"
            stats_message += f"\nSuccessful recognitions: {self.success_count}"
            stats_message += f"\nSuccess rate: {success_rate:.1f}%"
            
            # Add bot component stats if available
            if self.bot:
                if hasattr(self.bot, 'image_processor') and hasattr(self.bot.image_processor, 'regions'):
                    stats_message += f"\nImage processor regions: {len(self.bot.image_processor.regions)}"
                
                if hasattr(self.bot, 'card_recognizer'):
                    if hasattr(self.bot.card_recognizer, 'get_recognition_stats'):
                        recognition_stats = self.bot.card_recognizer.get_recognition_stats()
                        stats_message += f"\nCard templates loaded: {recognition_stats.get('templates_loaded', 'Unknown')}"
                    
                if hasattr(self.bot, 'community_detector'):
                    if hasattr(self.bot.community_detector, 'get_detection_stats'):
                        detection_stats = self.bot.community_detector.get_detection_stats()
                        stats_message += f"\nCommunity detection regions: {detection_stats.get('regions_defined', 'Unknown')}"
                
                # Add last analysis info
                if self.last_successful_analysis:
                    analysis = self.last_successful_analysis
                    
                    if 'table_info' in analysis and analysis['table_info']:
                        table_info = analysis['table_info']
                        if hasattr(table_info, 'players'):
                            stats_message += f"\nLast table analysis: {len(table_info.players)} players"
                            
                            if hasattr(self.bot, 'table_analyzer'):
                                hero = self.bot.table_analyzer.get_hero_info(table_info)
                                if hero:
                                    stats_message += f"\nHero: Seat {hero.seat_number}, Stack: {hero.stack_size:.1f}BB, Position: {hero.position}"
                    
                    if 'hole_cards' in analysis and analysis['hole_cards']:
                        hole_cards = analysis['hole_cards']
                        if hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                            stats_message += f"\nLast hole cards: {hole_cards}"
                    
                    if 'community_cards' in analysis and analysis['community_cards']:
                        community_cards = analysis['community_cards']
                        if hasattr(community_cards, 'count') and community_cards.count > 0:
                            stats_message += f"\nLast community cards: {community_cards}"
            
            stats_message += "\n" + "="*60
            
            self.log_message(stats_message)
            
        except Exception as e:
            self.log_message(f"Error printing statistics: {e}")

    def refresh_regions(self):
        """Force reload of regions from saved configuration file."""
        try:
            from region_loader import RegionLoader
            
            self.log_message("🔄 Manually refreshing regions from saved configuration...")
            
            # Create a fresh region loader to ensure we get the latest file data
            loader = RegionLoader()
            
            if not loader.regions_exist():
                self.log_message("⚠️ No region configuration file found. Please calibrate regions first.")
                return False
            
            # Reinitialize the bot to load fresh regions
            if self.bot:
                # Force update card recognizer with saved regions
                hero_regions = loader.get_hero_card_regions()
                if hero_regions and hasattr(self.bot, 'card_recognizer'):
                    # CRITICAL FIX: Update both the attribute and call the method to ensure proper update
                    self.bot.card_recognizer.card_regions = hero_regions
                    # Also call update method if it exists
                    if hasattr(self.bot.card_recognizer, 'update_regions'):
                        self.bot.card_recognizer.update_regions(hero_regions)
                    self.log_message(f"[SUCCESS] Refreshed {len(hero_regions)} hero card regions")
                    # CRITICAL FIX: Log detailed region data to debug problems
                    for name, region in hero_regions.items():
                        self.log_message(f"   [HERO] {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
                else:
                    self.log_message("[WARNING] Could not refresh hero card regions - card_recognizer unavailable")
                
                # Force update community card detector with saved regions
                community_regions = loader.get_community_card_regions()
                if community_regions and hasattr(self.bot, 'community_detector'):
                    # CRITICAL FIX: Update both the attribute and call the method to ensure proper update
                    self.bot.community_detector.community_card_regions = community_regions
                    if hasattr(self.bot.community_detector, 'update_regions'):
                        self.bot.community_detector.update_regions(community_regions)
                    self.log_message(f"[SUCCESS] Refreshed {len(community_regions)} community card regions")
                    # CRITICAL FIX: Log detailed region data to debug problems
                    for name, region in community_regions.items():
                        self.log_message(f"   [COMMUNITY] {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
                else:
                    self.log_message("[WARNING] Could not refresh community card regions - community_detector unavailable")
                
                # CRITICAL FIX: Update the UI component to show regions
                if hasattr(self, 'table_panel'):
                    # Convert regions to the format expected by the table panel
                    all_regions = loader.load_regions()
                    converted_regions = {}
                    for region_name, region_data in all_regions.items():
                        color = 'lime'
                        if 'community' in region_name:
                            color = 'lime' 
                        elif 'hero' in region_name:
                            color = 'cyan'
                        else:
                            color = 'yellow'
                        
                        converted_regions[region_name] = {
                            'x': region_data['x'],
                            'y': region_data['y'],
                            'width': region_data['width'],
                            'height': region_data['height'],
                            'color': color
                        }
                    self.table_panel.custom_regions = converted_regions
                    self.log_message("[SUCCESS] Regions displayed in UI table view")
                
                self.log_message("[SUCCESS] All regions successfully refreshed")
                
                # Test with current screenshot if available
                if self.current_screenshot is not None:
                    self.log_message("[TEST] Testing refreshed regions with current screenshot...")
                    analysis = self.bot.analyze_game_state(self.current_screenshot, debug=True)
                    self.update_display_internal(self.current_screenshot, analysis)
                
                return True
            else:
                self.log_message("[ERROR] Bot not initialized, can't refresh regions")
                return False
        except Exception as e:
            self.log_message(f"[ERROR] Error refreshing regions: {e}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
            return False

    def on_closing(self):
        """Handle application closing."""
        if self.running:
            self.stop_bot()
        
        # Print final statistics
        self.log_message("Generating final bot statistics...")
        self.print_statistics()
        
        # Disconnect OBS if connected
        if self.obs_capture.get_capture_stats()['connected']:
            self.disconnect_obs_camera()
        
        # Wait a moment for threads to stop
        time.sleep(0.5)
        self.log_message("👋 PokerStars Bot shutdown complete")
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()