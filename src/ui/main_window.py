"""
Main Window Class for Poker Study & Analysis Tool UI
Handles the primary window setup and coordination between components.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import queue
import datetime
from datetime import datetime
import random
import os
import sys

# Add analysis modules to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
src_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, src_path)

# Use absolute imports to avoid relative import issues
try:
    from ui.header_panel import HeaderPanel
    from ui.table_view_panel import TableViewPanel
    from ui.game_info_panel import GameInfoPanel
    from ui.control_panel import ControlPanel
    from ui.status_bar import StatusBar
except ImportError:
    # Fallback to relative imports if absolute imports fail
    from .header_panel import HeaderPanel
    from .table_view_panel import TableViewPanel
    from .game_info_panel import GameInfoPanel
    from .control_panel import ControlPanel
    from .status_bar import StatusBar
# Removed: enhanced_capture_panel, advanced_control_panel (no longer needed for OBS Virtual Camera setup)

# Import analysis modules
try:
    from stealth_manager import StealthProcessManager
    from stealth_screenshot import StealthScreenshotManager
    from behavioral_stealth import BehavioralStealthManager
    ANALYSIS_MODULES_AVAILABLE = True
except ImportError:
    ANALYSIS_MODULES_AVAILABLE = False
    print("⚠️ Advanced analysis modules not available - running in basic mode")

# Optional performance monitor import
try:
    from ui.performance_monitor import PerformanceMonitor
    PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    try:
        from .performance_monitor import PerformanceMonitor
        PERFORMANCE_MONITOR_AVAILABLE = True
    except ImportError:
        PERFORMANCE_MONITOR_AVAILABLE = False
        PerformanceMonitor = None

# Import the PokerStars Analysis Engine from the src directory
import sys
import os
# Add the src directory to the path
# Import enhanced recognition systems
try:
    from improved_card_recognition import ImprovedCardRecognizer
    IMPROVED_RECOGNITION_AVAILABLE = True
except ImportError:
    IMPROVED_RECOGNITION_AVAILABLE = False
    print("Warning: Improved card recognition not available")

try:
    from enhanced_card_recognition import EnhancedCardRecognizer
    ENHANCED_RECOGNITION_AVAILABLE = True
except ImportError:
    ENHANCED_RECOGNITION_AVAILABLE = False
    print("Warning: Enhanced card recognition not available")

try:
    from comprehensive_card_recognition import ComprehensiveCardRecognizer
    COMPREHENSIVE_RECOGNITION_AVAILABLE = True
except ImportError:
    COMPREHENSIVE_RECOGNITION_AVAILABLE = False
    print("Warning: Comprehensive card recognition not available")

try:
    from direct_card_recognition import DirectCardRecognizer
    DIRECT_RECOGNITION_AVAILABLE = True
except ImportError:
    DIRECT_RECOGNITION_AVAILABLE = False
    print("Warning: Direct card recognition not available")

# Import ULTIMATE card recognition system
try:
    from ultimate_card_integration import create_ultimate_integration
    ULTIMATE_RECOGNITION_AVAILABLE = True
    print("✅ Ultimate Card Recognition System available")
except ImportError:
    ULTIMATE_RECOGNITION_AVAILABLE = False
    print("❌ Warning: Ultimate card recognition not available")
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from poker_bot import PokerStarsBot
from window_capture import PokerStarsWindowCapture
from obs_capture import OBSCaptureSystem, OBSIntegratedBot


class MainWindow:
    """Main window class that coordinates all UI components."""
    
    def print_startup_banner(self, recognition_system, security_mode):
        """Print startup banner with appropriate mode information."""
        print("\n" + "="*60)
        print("    � POKERSTARS BOT - ULTIMATE EDITION v2.0 �")
        print("="*60)
        print(f"Recognition System: {recognition_system.upper()}")
        print(f"Analysis Mode: {security_mode.upper()}")
        
        if security_mode == 'live':
            print("🚀 LIVE MODE: Real-time poker analysis")
            print("   • Live OBS Virtual Camera capture")
            print("   • Real-time card recognition")
            print("   • Live strategy recommendations")
            print("   • Hardware capture integration")
        else:
            print("🎓 EDUCATIONAL PURPOSE: Post-game hand analysis")
            print("   • Capture screenshots of completed hands")
            print("   • Practice card recognition algorithms")
            print("   • Study optimal strategy decisions")
            print("   • Learn computer vision techniques")
            
            print("⚠️  IMPORTANT: For educational use only")
            print("   Use only for post-game analysis and study!")
        
        print("="*60 + "\n")
    
    def __init__(self, recognition_system='standard', show_regions=False, config_path='region_config.json', security_mode='safe'):
        """Initialize the main window and all components."""
        # Print enhanced startup information
        self.print_startup_banner(recognition_system, security_mode)
        
        # Store initialization parameters
        self.recognition_system = recognition_system
        self.show_regions = show_regions
        self.config_path = config_path
        self.security_mode = security_mode
        
        # Create main window
        self.root = tk.Tk()
        self.root.configure(bg='#2b2b2b')
        self.root.title("Poker Study & Analysis Tool v1.0")
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
        self.main_frame.grid_columnconfigure(0, weight=5)  # Table view
        self.main_frame.grid_columnconfigure(1, weight=2)  # Info panel (wider for advanced features)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Analysis engine components
        self.bot = None
        self.hardware_capture = None  # Hardware capture from laptop via OBS
        self.obs_capture = None  # Disabled - using hardware capture instead
        self.obs_bot = None
        
        # ANALYSIS: Initialize analysis management systems
        if ANALYSIS_MODULES_AVAILABLE:
            self.analysis_process_manager = StealthProcessManager()
            self.analysis_screenshot_manager = StealthScreenshotManager()
            self.behavioral_analysis_manager = BehavioralStealthManager()
            print("🔮 ANALYSIS MODE: Advanced study systems loaded")
        else:
            self.analysis_process_manager = None
            self.analysis_screenshot_manager = None
            self.behavioral_analysis_manager = None
        
        # State variables
        self.running = False
        self.capture_thread = None
        self.capture_mode = "window"
        # FIXED: Set exactly 10 FPS (0.1 second intervals) for consistent performance
        self.capture_interval = 0.1  # 10 FPS exactly
        self.last_screenshot = None
        self.last_analysis = None
        self.current_screenshot = None  # For region refresh functionality
        self.last_successful_analysis = None  # To store the last successful analysis
        
        # SECURITY: Enhanced capture control variables based on security mode
        # FIXED: All modes now use 10 FPS (0.1 second intervals)
        if security_mode == 'manual':
            self.manual_capture_mode = True
            self.auto_capture_enabled = False
            self.base_capture_interval = 0.1  # 10 FPS
            self.max_interval_variance = 0.0  # No variance for consistent FPS
            self.max_captures_per_session = 1000  # Higher limit since it's fast now
        elif security_mode == 'minimal':
            self.manual_capture_mode = False
            self.auto_capture_enabled = False  # Start disabled by default
            self.base_capture_interval = 0.1  # 10 FPS
            self.max_interval_variance = 0.0  # No variance for consistent FPS
            self.max_captures_per_session = 1000  # Higher limit since it's fast now
        else:  # 'safe' mode (default)
            self.manual_capture_mode = True  # Still default to manual for safety
            self.auto_capture_enabled = False
            self.base_capture_interval = 0.1  # 10 FPS
            self.max_interval_variance = 0.0  # No variance for consistent FPS
            self.max_captures_per_session = 1000  # Higher limit since it's fast now
        
        self.last_capture_time = 0
        self.capture_count = 0
        
        # SECURITY: Session limits
        self.session_start_time = time.time()
        self.max_session_duration = 3600  # 1 hour max session
        self.screenshots_this_hour = 0
        self.hourly_screenshot_limit = 30 if security_mode == 'manual' else (40 if security_mode == 'minimal' else 50)
        
        # Statistics
        self.success_count = 0
        
        # Message queue for thread-safe UI updates
        self.message_queue = queue.Queue()
        
        # Initialize UI components
        self.setup_ui_components()
        
        # Start message processing
        self.process_messages()
        
        # Create necessary directories
        self.create_directories()
        
        # Initialize analysis engine
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
        
        # Create notebook for advanced features in info panel
        self.create_advanced_features_notebook()
        
        # Status bar
        self.status_bar = StatusBar(self.main_frame)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    
    def create_advanced_features_notebook(self):
        """Create notebook with essential features only."""
        # Create notebook in the info panel
        self.advanced_notebook = ttk.Notebook(self.info_panel)
        self.advanced_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Game Info tab (essential for card display)
        game_info_frame = tk.Frame(self.advanced_notebook, bg='#2b2b2b')
        self.advanced_notebook.add(game_info_frame, text="Game Info")
        
        # Move existing game info content to the tab
        for widget in list(self.info_panel.children.values()):
            if widget != self.advanced_notebook:
                widget.pack_forget()
                widget.pack(in_=game_info_frame, fill="both", expand=True)
        
        # SECURITY: Security Controls tab (essential for safe operation)
        security_frame = tk.Frame(self.advanced_notebook, bg='#2b2b2b')
        self.advanced_notebook.add(security_frame, text="🔒 Security")
        self.create_security_controls_tab(security_frame)
        
        # Essential Debug Tools tab (simplified)
        debug_tools_frame = tk.Frame(self.advanced_notebook, bg='#2b2b2b')
        self.advanced_notebook.add(debug_tools_frame, text="Debug")
        self.create_essential_debug_tab(debug_tools_frame)
        
        # Optional Performance Monitor tab (only if available)
        if PERFORMANCE_MONITOR_AVAILABLE:
            performance_frame = tk.Frame(self.advanced_notebook, bg='#2b2b2b')
            self.advanced_notebook.add(performance_frame, text="Performance")
            self.performance_monitor = PerformanceMonitor(performance_frame, self)
    
    def create_essential_debug_tab(self, parent):
        """Create essential debug tools tab - simplified for hardware capture."""
        # Hardware capture status
        status_frame = tk.LabelFrame(parent, text="Hardware Capture Status", 
                                   bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        status_frame.pack(fill="x", padx=5, pady=5)
        
        status_row = tk.Frame(status_frame, bg='#2b2b2b')
        status_row.pack(fill="x", padx=5, pady=5)
        
        tk.Button(status_row, text="� Test Hardware Capture", command=self.test_hardware_capture,
                 bg='#4CAF50', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        tk.Button(status_row, text="� Refresh Regions", command=self.refresh_regions,
                 bg='#2196F3', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        tk.Button(status_row, text="⚙️ Manual Calibration", command=self.open_manual_calibration,
                 bg='#FF9800', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        # Live Recognition Monitor
        recognition_frame = tk.LabelFrame(parent, text="🎯 Live Recognition Monitor", 
                                        bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        recognition_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Recognition system status
        self.recognition_status_label = tk.Label(recognition_frame, text="Recognition System: Not Connected",
                                                bg='#2b2b2b', fg='lightgray', font=("Arial", 10))
        self.recognition_status_label.pack(pady=5)
        
        # Live performance display
        self.performance_label = tk.Label(recognition_frame, text="Performance: No data",
                                        bg='#2b2b2b', fg='lightgray', font=("Arial", 10))
        self.performance_label.pack(pady=5)
        
        # Live recognition log (smaller, focused on current recognition)
        live_log_frame = tk.Frame(recognition_frame, bg='#2b2b2b')
        live_log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(live_log_frame, text="Live Recognition Results:", 
                bg='#2b2b2b', fg='white', font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.live_recognition_text = tk.Text(live_log_frame, height=10, bg='#1e1e1e', fg='lightgreen',
                                           font=("Consolas", 9), wrap=tk.WORD)
        live_scrollbar = tk.Scrollbar(live_log_frame, orient="vertical", command=self.live_recognition_text.yview)
        self.live_recognition_text.configure(yscrollcommand=live_scrollbar.set)
        
        self.live_recognition_text.pack(side="left", fill="both", expand=True)
        live_scrollbar.pack(side="right", fill="y")
        
        # Start live recognition monitoring
        self.start_live_recognition_monitoring()
        
        # Essential logging controls
        log_frame = tk.LabelFrame(parent, text="Logging & Cleanup", 
                                 bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        log_frame.pack(fill="x", padx=5, pady=5)
        
        log_controls = tk.Frame(log_frame, bg='#2b2b2b')
        log_controls.pack(fill="x", padx=5, pady=5)
        
        tk.Button(log_controls, text="🧹 Clear Log", command=self.clear_log,
                 bg='#f44336', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        tk.Button(log_controls, text="🗑️ Clean Screenshots", command=self.cleanup_screenshots,
                 bg='#FF5722', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        tk.Button(log_controls, text="📁 Open Debug Folder", command=self.open_debug_folder,
                 bg='#9C27B0', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
    
    def start_live_recognition_monitoring(self):
        """Start monitoring live recognition results"""
        self.update_live_recognition_display()
    
    def update_live_recognition_display(self):
        """Update the live recognition display with current status"""
        try:
            if hasattr(self, 'hardware_capture') and self.hardware_capture:
                # Get live recognition status from hardware capture
                status = self.hardware_capture.get_live_recognition_status()
                
                # Update status labels
                if status and 'is_active' in status:
                    if status['is_active']:
                        self.recognition_status_label.config(text="Recognition System: ✅ Active", fg='lightgreen')
                        
                        # Update performance
                        fps = status.get('fps', 0)
                        success_rate = status.get('success_rate', 0)
                        last_method = status.get('last_method', 'Unknown')
                        
                        perf_text = f"Performance: {fps:.1f} FPS | Success: {success_rate:.1f}% | Method: {last_method}"
                        self.performance_label.config(text=perf_text, fg='lightgreen')
                        
                        # Update live log with recent recognition results
                        if 'recent_results' in status and status['recent_results']:
                            self.live_recognition_text.config(state=tk.NORMAL)
                            self.live_recognition_text.delete(1.0, tk.END)
                            
                            for result in status['recent_results'][-10:]:  # Show last 10 results
                                timestamp = result.get('timestamp', 'Unknown')
                                method = result.get('method', 'Unknown')
                                confidence = result.get('confidence', 0)
                                cards_found = result.get('cards_found', 0)
                                
                                log_line = f"[{timestamp}] {method}: {cards_found} cards (conf: {confidence:.3f})\n"
                                self.live_recognition_text.insert(tk.END, log_line)
                            
                            self.live_recognition_text.config(state=tk.DISABLED)
                            self.live_recognition_text.see(tk.END)
                    else:
                        self.recognition_status_label.config(text="Recognition System: ⚠️ Inactive", fg='yellow')
                        self.performance_label.config(text="Performance: No data", fg='lightgray')
                else:
                    self.recognition_status_label.config(text="Recognition System: ❌ Not Connected", fg='red')
                    self.performance_label.config(text="Performance: No data", fg='lightgray')
            else:
                self.recognition_status_label.config(text="Recognition System: ❌ Hardware capture not initialized", fg='red')
                self.performance_label.config(text="Performance: No data", fg='lightgray')
                
        except Exception as e:
            self.log_message(f"❌ Error updating live recognition display: {e}")
        
        # Schedule next update
        self.root.after(2000, self.update_live_recognition_display)  # Update every 2 seconds
    
    def test_hardware_capture(self):
        """Test hardware capture system."""
        try:
            if not self.hardware_capture:
                self.log_message("❌ Hardware capture not connected")
                return
                
            self.log_message("🧪 Testing hardware capture system...")
            
            # Test camera connection
            if self.hardware_capture.virtual_camera and self.hardware_capture.virtual_camera.isOpened():
                self.log_message("✅ Virtual camera connected")
            else:
                self.log_message("❌ Virtual camera not connected")
                return
            
            # Test frame capture
            frame = self.hardware_capture.capture_from_virtual_camera()
            if frame is not None:
                self.log_message(f"✅ Frame captured: {frame.shape}")
            else:
                self.log_message("❌ Frame capture failed")
                return
            
            # Test region loading
            if self.hardware_capture.calibrated_regions:
                self.log_message(f"✅ Regions loaded: {len(self.hardware_capture.calibrated_regions)}")
                for region_name in self.hardware_capture.calibrated_regions.keys():
                    self.log_message(f"   - {region_name}")
            else:
                self.log_message("⚠️ No regions loaded")
            
            # Test analysis
            game_state = self.hardware_capture.analyze_current_frame()
            if game_state:
                hero_count = len(game_state.get('hero_cards', []))
                community_count = len(game_state.get('community_cards', []))
                confidence = game_state.get('analysis_confidence', 0)
                self.log_message(f"✅ Analysis successful: {hero_count} hero, {community_count} community (conf: {confidence:.3f})")
            else:
                self.log_message("⚠️ Analysis returned no results")
                
        except Exception as e:
            self.log_message(f"❌ Hardware capture test failed: {e}")
    
    def cleanup_screenshots(self):
        """Clean up excessive screenshot files."""
        try:
            import glob
            
            # Count current files
            png_files = glob.glob("*.png")
            before_count = len(png_files)
            
            if before_count == 0:
                self.log_message("✅ No PNG files found to clean")
                return
            
            # Clean up debug and test screenshots
            patterns_to_clean = [
                "virtual_camera_capture_*.png",
                "debug_*.png", 
                "test_*.png",
                "poker_table_for_regions_*.png"
            ]
            
            cleaned_count = 0
            for pattern in patterns_to_clean:
                files = glob.glob(pattern)
                for file in files:
                    try:
                        os.remove(file)
                        cleaned_count += 1
                    except:
                        pass
            
            self.log_message(f"🧹 Cleaned {cleaned_count} screenshot files")
            self.log_message(f"   Before: {before_count} files, After: {before_count - cleaned_count} files")
            
        except Exception as e:
            self.log_message(f"❌ Screenshot cleanup failed: {e}")
    
    def open_manual_calibration(self):
        """Open the manual region calibration tool."""
        try:
            self.log_message("🔧 Opening manual region calibration...")
            
            # Import and run manual calibration
            import subprocess
            import sys
            
            # Run in separate process to avoid conflicts
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "manual_region_calibrator.py")
            
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
                self.log_message("✅ Manual calibration tool launched")
            else:
                self.log_message("❌ Manual calibration tool not found")
                
        except Exception as e:
            self.log_message(f"❌ Failed to open manual calibration: {e}")
    
    def create_security_controls_tab(self, parent):
        """Create security controls tab."""
        import tkinter.messagebox as messagebox
        
        # Analysis mode display
        if self.security_mode == 'live':
            mode_frame = tk.LabelFrame(parent, text="🔴 LIVE MODE ACTIVE", 
                                      bg='#d32f2f', fg='white', font=("Arial", 12, "bold"))
            mode_color = '#d32f2f'
            mode_text = f"Current Mode: LIVE ANALYSIS"
            mode_desc = "Real-time poker analysis and monitoring"
        else:
            mode_frame = tk.LabelFrame(parent, text="🎓 STUDY MODE ACTIVE", 
                                      bg='#1976d2', fg='white', font=("Arial", 12, "bold"))
            mode_color = '#4caf50'
            mode_text = f"Current Mode: EDUCATIONAL ANALYSIS"
            mode_desc = "Post-game hand analysis and study tool"
            
        mode_frame.pack(fill="x", padx=5, pady=5)
            
        tk.Label(mode_frame, text=mode_text, bg=mode_color, fg='white', 
                font=("Arial", 11, "bold")).pack(padx=10, pady=2)
        tk.Label(mode_frame, text=mode_desc, bg=mode_color, fg='white', 
                font=("Arial", 9)).pack(padx=10, pady=2)
        
        # Mode-specific notice
        if self.security_mode == 'live':
            notice_frame = tk.LabelFrame(parent, text="⚠️ LIVE ANALYSIS MODE", 
                                        bg='#ff9800', fg='white', font=("Arial", 12, "bold"))
            notice_frame.pack(fill="x", padx=5, pady=5)
            
            notice_text = tk.Label(notice_frame, 
                                  text="LIVE MODE: Real-time poker table analysis and monitoring.\n"
                                       "Use responsibly and in accordance with site terms of service.",
                                  bg='#ff9800', fg='white', font=("Arial", 10),
                                  wraplength=400, justify="left")
            notice_text.pack(padx=10, pady=5)
        else:
            notice_frame = tk.LabelFrame(parent, text="📋 EDUCATIONAL PURPOSE", 
                                        bg='#4caf50', fg='white', font=("Arial", 12, "bold"))
            notice_frame.pack(fill="x", padx=5, pady=5)
            
            notice_text = tk.Label(notice_frame, 
                                  text="This tool is designed for educational purposes and post-game analysis.\n"
                                       "Use only to study completed hands and improve strategy understanding.",
                                  bg='#4caf50', fg='white', font=("Arial", 10),
                                  wraplength=400, justify="left")
            notice_text.pack(padx=10, pady=5)
        
        # Manual capture controls
        manual_frame = tk.LabelFrame(parent, text="🔒 Manual Capture (SAFE)", 
                                    bg='#388e3c', fg='white', font=("Arial", 12, "bold"))
        manual_frame.pack(fill="x", padx=5, pady=5)
        
        manual_controls = tk.Frame(manual_frame, bg='#388e3c')
        manual_controls.pack(fill="x", padx=5, pady=5)
        
        self.manual_capture_btn = tk.Button(
            manual_controls, 
            text="📸 Take Manual Screenshot", 
            command=self.manual_capture,
            bg='#4caf50', fg='white', font=("Arial", 11, "bold")
        )
        self.manual_capture_btn.pack(side="left", padx=5, pady=5)
        
        
        # Study mode controls
        study_frame = tk.LabelFrame(parent, text="📚 Study Mode Controls", 
                                   bg='#4caf50', fg='white', font=("Arial", 12, "bold"))
        study_frame.pack(fill="x", padx=5, pady=5)
        
        study_controls = tk.Frame(study_frame, bg='#4caf50')
        study_controls.pack(fill="x", padx=5, pady=5)
        
        tk.Label(study_controls, text="Educational analysis for post-game study", 
                bg='#4caf50', fg='white', font=("Arial", 10)).pack(pady=5)
        
        # Session tracking for educational purposes  
        session_frame = tk.LabelFrame(parent, text="📊 Study Session", 
                                     bg='#1976d2', fg='white', font=("Arial", 12, "bold"))
        session_frame.pack(fill="x", padx=5, pady=5)
        
        self.session_info_label = tk.Label(session_frame, 
                                          text="Session: 0 captures, 0 hours",
                                          bg='#1976d2', fg='white', font=("Arial", 10))
        self.session_info_label.pack(padx=10, pady=5)
    
    def manual_capture(self):
        """Manually trigger a single screenshot - safer for security"""
        try:
            self.log_message("🔒 Manual capture initiated")
            
            # Take a single screenshot using hardware capture
            if self.hardware_capture:
                screenshot = self.hardware_capture.capture_from_virtual_camera()
                
                if screenshot is not None and screenshot.size > 0:
                    # Process this single screenshot using hardware capture analysis
                    game_state = self.hardware_capture.analyze_current_frame()
                    if game_state:
                        # Convert hardware results to UI-compatible format
                        hero_cards = game_state.get('hero_cards', [])
                        community_cards = game_state.get('community_cards', [])
                        confidence = game_state.get('analysis_confidence', 0)
                        
                        # Create card recognition results format
                        card_results = []
                        for i, card in enumerate(hero_cards):
                            card_results.append(type('obj', (object,), {
                                'card_code': card.get('card', 'error'),
                                'confidence': card.get('confidence', 0),
                                'region_name': f'hero_card_{i+1}'
                            })())
                        
                        for i, card in enumerate(community_cards):
                            card_results.append(type('obj', (object,), {
                                'card_code': card.get('card', 'error'),
                                'confidence': card.get('confidence', 0),
                                'region_name': f'community_card_{i+1}'
                            })())
                        
                        # Use the UI conversion method for proper format
                        analysis = self.convert_ultimate_results_to_analysis(card_results)
                        if analysis:
                            # Update UI with proper analysis format
                            self.message_queue.put(("enhanced_update_display", (screenshot, analysis)))
                            self.last_analysis = analysis
                            
                            # Update game info panel
                            self.info_panel.update_game_info(analysis)
                            
                            # Update live recognition status
                            if hasattr(self.info_panel, 'update_live_recognition_status'):
                                self.info_panel.update_live_recognition_status(game_state)
                            
                            self.log_message(f"✅ Manual capture completed successfully")
                            self.log_message(f"   Hero cards: {len(hero_cards)}, Community cards: {len(community_cards)}")
                            self.log_message(f"   Analysis confidence: {confidence:.3f}")
                            
                            # Log individual cards if detected
                            for card in hero_cards:
                                self.log_message(f"   Hero: {card['card']} (conf: {card['confidence']:.3f})")
                            for card in community_cards:
                                self.log_message(f"   Community: {card['card']} (conf: {card['confidence']:.3f})")
                        else:
                            self.log_message("⚠️ Analysis conversion failed")
                            # Still update display with screenshot
                            self.message_queue.put(("update_display", (screenshot, self.last_analysis)))
                    else:
                        self.log_message("⚠️ No game state detected from hardware capture")
                        # Still update display with screenshot
                        self.message_queue.put(("update_display", (screenshot, self.last_analysis)))
                    
                    # Update session info
                    self.screenshots_this_hour += 1
                    self.update_session_info()
                else:
                    self.log_message("❌ No frame captured from OBS Virtual Camera")
            else:
                self.log_message("❌ Hardware capture not connected - please connect to OBS Virtual Camera first")
                
        except Exception as e:
            self.log_message(f"❌ Manual capture failed: {e}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
    
    def toggle_auto_capture(self):
        """Toggle auto capture with security warning"""
        import tkinter.messagebox as messagebox
        
        if self.auto_capture_var.get():
            # Show security warning
            result = messagebox.askquestion(
                "Security Warning",
                "Auto capture increases detection risk by PokerStars security.\n\n"
                "Continuous screenshots can trigger account restrictions.\n\n"
                "Continue with auto capture?",
                icon="warning"
            )
            if result == "yes":
                self.auto_capture_enabled = True
                self.log_message("⚠️ Auto capture enabled - SECURITY RISK")
            else:
                self.auto_capture_var.set(False)
                self.auto_capture_enabled = False
        else:
            self.auto_capture_enabled = False
            self.log_message("🔒 Auto capture disabled - SECURE MODE")
    
    def update_capture_interval(self):
        """Update capture interval from user input"""
        try:
            new_interval = float(self.interval_var.get())
            if new_interval < 5.0:
                self.log_message("⚠️ Minimum interval is 5 seconds for security")
                new_interval = 5.0
                self.interval_var.set(str(new_interval))
            
            self.base_capture_interval = new_interval
            self.log_message(f"🔒 Capture interval updated to {new_interval} seconds")
        except ValueError:
            self.log_message("❌ Invalid interval value")
    
    def update_session_info(self):
        """Update session information display"""
        current_time = time.time()
        session_duration = (current_time - self.session_start_time) / 3600  # Convert to hours
        
        info_text = f"Session: {self.screenshots_this_hour} captures, {session_duration:.1f} hours"
        if hasattr(self, 'session_info_label'):
            self.session_info_label.config(text=info_text)
    
    def is_session_safe(self):
        """Check if current session is within safe limits"""
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        # Reset hourly counter
        if session_duration > 3600:
            self.session_start_time = current_time
            self.screenshots_this_hour = 0
            
        # Check limits
        if session_duration > self.max_session_duration:
            self.log_message("⚠️ Max session duration reached - stopping for security")
            return False
            
        if self.screenshots_this_hour >= self.hourly_screenshot_limit:
            self.log_message("⚠️ Hourly screenshot limit reached - pausing")
            return False
            
        return True
    
    def open_debug_folder(self):
        """Open debug folder in file explorer."""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.Popen(["explorer", "debug_images"])
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "debug_images"])
            else:  # Linux
                subprocess.Popen(["xdg-open", "debug_images"])
                
        except Exception as e:
            self.log_message(f"Error opening debug folder: {e}")
    
    def view_latest_screenshot(self):
        """View latest screenshot."""
        try:
            import glob
            
            screenshots = glob.glob("screenshots/*.png")
            if screenshots:
                latest = max(screenshots, key=os.path.getctime)
                
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.Popen(["start", latest], shell=True)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", latest])
                else:
                    subprocess.Popen(["xdg-open", latest])
            else:
                messagebox.showinfo("Info", "No screenshots found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view screenshot: {e}")
    
    def view_card_debug(self):
        """View card debug images."""
        try:
            import glob
            
            debug_images = glob.glob("debug_cards/*.png")
            if debug_images:
                latest = max(debug_images, key=os.path.getctime)
                
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.Popen(["start", latest], shell=True)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", latest])
                else:
                    subprocess.Popen(["xdg-open", latest])
            else:
                messagebox.showinfo("Info", "No card debug images found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view debug images: {e}")
    
    def apply_log_level(self):
        """Apply log level setting."""
        try:
            import logging
            level = getattr(logging, self.log_level_var.get())
            logging.getLogger().setLevel(level)
            self.log_message(f"✅ Log level set to {self.log_level_var.get()}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set log level: {e}")
    
    def clear_log(self):
        """Clear the activity log."""
        try:
            # Find the log text widget in the game info panel
            for widget in self.info_panel.winfo_children():
                if hasattr(widget, 'log_text'):
                    widget.log_text.delete(1.0, tk.END)
                    break
            self.log_message("Log cleared")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear log: {e}")
    
    def initialize_bot(self):
        """Initialize the analysis engine components with recognition system."""
        try:
            self.log_message("="*60)
            self.log_message("POKERSTARS BOT - ULTIMATE EDITION v2.0 INITIALIZATION")
            self.log_message("="*60)
            self.log_message("Features:")
            self.log_message("✓ Educational UI for post-game study")
            self.log_message("✓ Card recognition system for learning")
            self.log_message("✓ 4-color template matching research")
            self.log_message("✓ Manual screenshot capture")
            self.log_message("✓ Strategy analysis tools")
            self.log_message("✓ Educational purpose only")
            self.log_message("="*60)
            
            # Initialize UNIFIED card recognition system
            try:
                from unified_card_recognition import create_unified_recognizer
                
                self.log_message("Initializing Unified Card Recognition System...")
                self.unified_recognizer = create_unified_recognizer()
                
                if self.unified_recognizer:
                    self.log_message("SUCCESS: Unified Card Recognition System initialized!")
                    self.use_unified_recognition = True
                else:
                    self.log_message("WARNING: Unified recognition failed, using fallback")
                    self.use_unified_recognition = False
                    
            except Exception as e:
                self.log_message(f"WARNING: Unified recognition unavailable: {e}")
                self.use_unified_recognition = False
            
            # Initialize legacy systems as fallback
            if not self.use_unified_recognition:
                # Initialize ULTIMATE card recognition system as fallback
                if ULTIMATE_RECOGNITION_AVAILABLE:
                    self.log_message("Initializing ULTIMATE Card Recognition System as fallback...")
                    self.ultimate_recognition = create_ultimate_integration()
                    
                    if self.ultimate_recognition:
                        self.log_message("SUCCESS: ULTIMATE Card Recognition System initialized as fallback!")
                        
                        # Set debug mode based on security settings
                        debug_enabled = self.security_mode in ['safe', 'minimal']
                        self.ultimate_recognition.set_debug_mode(debug_enabled)
                        self.log_message(f"Debug mode: {'ENABLED' if debug_enabled else 'DISABLED'}")
                        
                    else:
                        self.log_message("ERROR: Failed to initialize ULTIMATE Card Recognition System")
                    self.ultimate_recognition = None
            else:
                self.log_message("❌ ULTIMATE Card Recognition System not available - falling back to standard")
                self.ultimate_recognition = None
            
            # Import from the src directory for fallback
            from region_loader import RegionLoader
            
            # Log which card recognition system we're using
            if self.ultimate_recognition:
                self.log_message(f"🎯 Using ULTIMATE card recognition system")
            else:
                self.log_message(f"Target: Initializing with {self.recognition_system} card recognition system (fallback)")
            
            # Initialize the bot with the specified recognition system (for fallback)
            self.bot = PokerStarsBot(recognition_type=self.recognition_system)
            
            # Log the actual recognition system being used
            if hasattr(self.bot, 'card_recognizer'):
                recognizer_type = type(self.bot.card_recognizer).__name__
                self.log_message(f"SUCCESS: {recognizer_type} loaded successfully (fallback system)")
            
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
                    
                    # CRITICAL FIX: Force immediate region display
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
                    self.log_message("[SUCCESS] Regions configured for immediate display")
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
        """Start the analysis monitoring."""
        try:
            # Check if hardware capture is connected
            if not self.hardware_capture:
                self.log_message("Please connect to hardware capture first")
                return
            
            # No bot initialization needed for hardware capture
            # The hardware capture system handles its own analysis
            
            self.running = True
            self.header_panel.set_bot_status("Analyzing", "green")
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
        """Stop the analysis monitoring."""
        try:
            self.running = False
            self.header_panel.set_bot_status("Stopped", "orange")
            
            # Stop OBS capture if running
            if self.capture_mode == "obs":
                self.obs_capture.stop_capture()
            
            # Update control panel
            self.control_panel.set_bot_running(False)
            
            self.log_message("Analysis stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping analysis: {e}")
    
    def capture_loop(self):
        """STEALTH-ENHANCED capture loop with advanced evasion."""
        import time
        
        # Initialize variables
        last_livestream_update = 0
        livestream_interval = 0.1
        
        while self.running:
            try:
                start_time = time.time()
                current_time = start_time
                
                # FIXED: Removed stealth delays for consistent 10 FPS performance
                # Stealth features available but disabled for performance
                
                # Quick session safety check (no 5-minute delays)
                if not self.is_session_safe():
                    self.log_message("⚠️ Session safety check - continuing at 10 FPS")
                    # Continue without delay for 10 FPS performance
                
                # Get screenshot using hardware capture from laptop
                screenshot = None
                if self.hardware_capture:
                    screenshot = self.hardware_capture.capture_from_virtual_camera()
                else:
                    # Hardware capture is the only method - no local PokerStars needed
                    if not self.hardware_capture:
                        self.log_message("Hardware capture not connected")
                        time.sleep(0.1)
                        continue
                
                # Update livestream display consistently for 10 FPS
                if screenshot is not None and screenshot.size > 0:
                    livestream_screenshot = screenshot.copy()
                    
                    # Update display every frame for 10 FPS performance
                    if current_time - last_livestream_update > livestream_interval:
                        self.message_queue.put(("update_display", (livestream_screenshot, self.last_analysis)))
                        last_livestream_update = current_time
                
                # STEALTH: Enhanced analysis timing
                if self.auto_capture_enabled and screenshot is not None and screenshot.size > 0:
                    current_time = time.time()
                    
                    # FIXED: Use consistent 10 FPS (0.1 second intervals)
                    next_interval = 0.1  # Force 10 FPS regardless of stealth settings
                    
                    if current_time - self.last_capture_time < next_interval:
                        time.sleep(0.01)  # Very short sleep for 10 FPS
                        continue
                    
                    # Check capture limits
                    if self.capture_count >= self.max_captures_per_session:
                        self.log_message("⚠️ Session capture limit reached for security")
                        self.auto_capture_enabled = False
                        self.auto_capture_var.set(False)
                        if ANALYSIS_MODULES_AVAILABLE and self.behavioral_analysis_manager:
                            self.behavioral_stealth_manager.log_human_activity('break')
                        continue
                    
                    # Update timing
                    self.last_capture_time = current_time
                    self.capture_count += 1
                    self.screenshots_this_hour += 1
                    
                    self.log_message(f"🔒 Hardware capture #{self.capture_count} (interval: {next_interval:.1f}s)")
                    self.update_session_info()
                    
                    # Use hardware capture for analysis (no local PokerStars bot needed)
                    if self.hardware_capture:
                        # Get analysis from hardware capture system
                        game_state = self.hardware_capture.analyze_current_frame()
                        if game_state:
                            # Convert to expected format for display
                            analysis = {
                                'hero_cards': game_state.get('hero_cards', []),
                                'community_cards': game_state.get('community_cards', []),
                                'confidence': game_state.get('analysis_confidence', 0),
                                'valid': len(game_state.get('hero_cards', [])) > 0
                            }
                            self.last_analysis = analysis
                        else:
                            self.log_message("No game state detected from hardware capture")
                            continue
                    
                    # Record capture time for performance monitoring
                    capture_start = time.time()
                    
                    # Save periodic debug images to help diagnose recognition issues (REDUCED FREQUENCY)
                    if self.capture_count % 50 == 0:  # Save every 50th frame (reduced from 20)
                        import cv2
                        import os
                        import time
                        
                        os.makedirs("screenshots", exist_ok=True)
                        timestamp = int(time.time())
                        cv2.imwrite(f"screenshots/capture_{timestamp}.png", screenshot)
                    
                    # Record capture time
                    capture_time = time.time() - capture_start
                    if PERFORMANCE_MONITOR_AVAILABLE and hasattr(self, 'performance_monitor'):
                        self.performance_monitor.record_capture_time(capture_time)
                    
                    # Analyze the screenshot with proper error handling
                    try:
                        # Run enhanced analysis with debug mode enabled less frequently (SECURITY)
                        debug_mode = (self.capture_count % 25 == 0)  # Reduced from 10 to 25
                        
                        # Log that analysis is starting
                        self.log_message(f"Starting analysis of frame #{self.capture_count}...")
                        
                        # Record analysis start time
                        analysis_start = time.time()
                        
                        # 🎯 ULTIMATE CARD RECOGNITION SYSTEM
                        if self.ultimate_recognition:
                            self.log_message(f"🎯 Using ULTIMATE recognition system for frame #{self.capture_count}...")
                            
                            try:
                                # Use the ultimate recognition system
                                card_results = self.ultimate_recognition.recognize_all_cards(
                                    screenshot=screenshot, 
                                    use_cache=True
                                )
                                
                                if card_results:
                                    # Convert ultimate results to standard analysis format
                                    analysis = self.convert_ultimate_results_to_analysis(card_results)
                                    
                                    # Log detailed results
                                    recognized_cards = [r for r in card_results if not r.is_empty and r.card_code != 'error']
                                    empty_slots = [r for r in card_results if r.is_empty]
                                    errors = [r for r in card_results if r.card_code == 'error']
                                    
                                    self.log_message(f"✅ ULTIMATE Recognition Results:")
                                    self.log_message(f"   🎯 Recognized: {len(recognized_cards)} cards")
                                    self.log_message(f"   🔳 Empty slots: {len(empty_slots)}")
                                    self.log_message(f"   ❌ Errors: {len(errors)}")
                                    
                                    # Log individual card results
                                    for result in recognized_cards:
                                        conf_str = f"{result.confidence:.3f}"
                                        time_str = f"{result.processing_time*1000:.1f}ms"
                                        self.log_message(f"   {result.region_name}: {result.card_code} (conf: {conf_str}, {time_str})")
                                    
                                    # Get performance stats
                                    perf_stats = self.ultimate_recognition.get_performance_stats()
                                    if perf_stats:
                                        self.log_message(f"📊 Performance: {perf_stats}")
                                    
                                else:
                                    self.log_message("⚠️ ULTIMATE Recognition returned no results")
                                    analysis = None
                                    
                            except Exception as ultimate_error:
                                self.log_message(f"❌ ULTIMATE Recognition error: {ultimate_error}")
                                analysis = None
                        else:
                            # Fallback to standard bot analysis
                            self.log_message(f"🔄 Using fallback recognition for frame #{self.capture_count}...")
                            analysis = self.bot.analyze_game_state(screenshot, debug=debug_mode)
                        
                        # Record analysis time
                        analysis_time = time.time() - analysis_start
                        if PERFORMANCE_MONITOR_AVAILABLE and hasattr(self, 'performance_monitor'):
                            self.performance_monitor.record_analysis_time(analysis_time)
                        
                        # Validate analysis results
                        if analysis and isinstance(analysis, dict):
                            # Store last successful analysis
                            self.last_analysis = analysis
                            
                            # Record recognition confidence for performance monitoring
                            if PERFORMANCE_MONITOR_AVAILABLE and hasattr(self, 'performance_monitor'):
                                confidence = 0.0
                                confidence_count = 0
                                
                                if 'hole_cards' in analysis and analysis['hole_cards']:
                                    if hasattr(analysis['hole_cards'], 'detection_confidence'):
                                        confidence += analysis['hole_cards'].detection_confidence
                                        confidence_count += 1
                                
                                if 'community_cards' in analysis and analysis['community_cards']:
                                    if hasattr(analysis['community_cards'], 'detection_confidence'):
                                        confidence += analysis['community_cards'].detection_confidence
                                        confidence_count += 1
                                
                                if confidence_count > 0:
                                    avg_confidence = confidence / confidence_count
                                    self.performance_monitor.record_recognition_confidence(avg_confidence)
                            
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
                
                elif not self.auto_capture_enabled:
                    # Manual mode - just update livestream display without analysis
                    if screenshot is not None and screenshot.size > 0:
                        # Update display less frequently in manual mode
                        if current_time - last_livestream_update > livestream_interval * 10:  # 10x less frequent
                            self.message_queue.put(("update_display", (screenshot, self.last_analysis)))
                            last_livestream_update = current_time
                    # FIXED: Maintain 10 FPS in manual mode
                    time.sleep(0.01)
                else:
                    # Explicitly log frame issues for debugging
                    if screenshot is None:
                        self.log_message("⚠️ Captured frame was None")
                    elif screenshot.size == 0:
                        self.log_message("⚠️ Captured frame had size 0")
                    
                    # FIXED: Quick retry for 10 FPS
                    time.sleep(0.01)
                    continue
                
                # FIXED: Maintain 10 FPS timing in all modes
                time.sleep(0.01)  # Very short sleep for 10 FPS consistency
                
            except Exception as e:
                self.log_message(f"❌ Error in capture loop: {e}")
                # FIXED: Quick error recovery for 10 FPS
                time.sleep(0.1)
    
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
        """Connect to Hardware Capture System."""
        try:
            self.control_panel.set_obs_status("Connecting...")
            
            # Set capture mode to OBS
            self.set_capture_mode("obs")
            
            # Import hardware capture system
            try:
                # Import from the project root, not src
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
                
                # Initialize hardware capture config
                config = HardwareCaptureConfig(
                    debug_mode=True,
                    recognition_method="enhanced"
                )
                
                # Create hardware capture system
                self.hardware_capture = HardwareCaptureSystem(config)
                
                # Set up live logging callback to connect to UI
                self.hardware_capture.set_ui_log_callback(self.log_message)
                
                # Connect to OBS Virtual Camera
                if self.hardware_capture.connect_to_virtual_camera():
                    self.control_panel.set_obs_connected(True)
                    self.log_message(f"✅ Hardware capture connected to OBS Virtual Camera (index {self.hardware_capture.camera_index})")
                    
                    # Test region loading
                    if self.hardware_capture.auto_calibrate_from_hardware():
                        self.log_message("✅ Region configuration loaded successfully")
                        
                        # Log loaded regions
                        if hasattr(self.hardware_capture, 'calibrated_regions') and self.hardware_capture.calibrated_regions:
                            for region_name, region_data in self.hardware_capture.calibrated_regions.items():
                                self.log_message(f"   {region_name}: x={region_data.get('x', 0)}, y={region_data.get('y', 0)}")
                        else:
                            self.log_message("⚠️ No regions loaded - check region files")
                    else:
                        self.log_message("⚠️ Auto-calibration failed - using default regions")
                    
                    # Start video feed to UI but don't start automatic analysis
                    self.start_hardware_capture_livestream()
                    
                    # Update header with connection status
                    self.header_panel.set_connection_status("Hardware Connected", "green")
                    
                    # Test a single capture to validate everything works
                    self.log_message("🧪 Testing single capture...")
                    test_frame = self.hardware_capture.capture_from_virtual_camera()
                    if test_frame is not None:
                        self.log_message(f"✅ Test capture successful: {test_frame.shape}")
                        # Display the test frame
                        self.table_panel.display_screenshot(test_frame)
                        self.log_message("📱 Ready for manual capture! Click 'Manual Capture' to analyze cards.")
                    else:
                        self.log_message("❌ Test capture failed")
                    
                else:
                    self.control_panel.set_obs_connected(False)
                    self.log_message("❌ OBS Virtual Camera not found")
                    self.log_message("Make sure:")
                    self.log_message("  1. OBS Studio is running")
                    self.log_message("  2. Virtual Camera is started in OBS")
                    self.log_message("  3. UGREEN capture device is working")
                    
            except ImportError as e:
                self.control_panel.set_obs_connected(False)
                self.log_message(f"❌ Hardware capture system not available: {e}")
                
        except Exception as e:
            self.control_panel.set_obs_connected(False)
            self.log_message(f"❌ Error connecting to hardware capture: {e}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
    
    def disconnect_obs_camera(self):
        """Disconnect from Hardware Capture System."""
        try:
            if hasattr(self, 'hardware_capture') and self.hardware_capture:
                # Release virtual camera
                if hasattr(self.hardware_capture, 'virtual_camera') and self.hardware_capture.virtual_camera:
                    self.hardware_capture.virtual_camera.release()
                self.hardware_capture = None
            
            # Stop livestream updates
            self.stop_hardware_capture_livestream()
                
            self.control_panel.set_obs_connected(False)
            self.log_message("Hardware capture disconnected")
            
        except Exception as e:
            self.log_message(f"Error disconnecting hardware capture: {e}")
    
    def start_hardware_capture_livestream(self):
        """Start livestream from hardware capture"""
        if not hasattr(self, '_hardware_livestream_running'):
            self._hardware_livestream_running = True
            self._update_hardware_livestream()
    
    def stop_hardware_capture_livestream(self):
        """Stop hardware capture livestream"""
        self._hardware_livestream_running = False
    
    def _update_hardware_livestream(self):
        """Update livestream display with hardware capture feed and live recognition"""
        if not getattr(self, '_hardware_livestream_running', False):
            return
        
        try:
            if self.hardware_capture:
                # Capture frame from hardware
                frame = self.hardware_capture.capture_from_virtual_camera()
                if frame is not None and frame.size > 0:
                    # Update the livestream display
                    self.message_queue.put(("update_display", (frame, self.last_analysis)))
                    
                    # Get live recognition status
                    live_status = self.hardware_capture.get_live_recognition_status()
                    
                    # Update status bar with live information
                    status_text = f"Live Recognition: {live_status['recognition_system']} | {live_status['performance_summary']}"
                    self.message_queue.put(("status", status_text))
                    
                    # Test hardware capture analysis for live recognition display
                    import time
                    current_time = time.time()
                    if not hasattr(self, '_last_live_recognition') or current_time - self._last_live_recognition > 2.0:
                        self._last_live_recognition = current_time
                        
                        # Perform live recognition analysis
                        game_state = self.hardware_capture.analyze_current_frame()
                        if game_state:
                            # Get detailed recognition logs for live display
                            recent_logs = self.hardware_capture.get_ui_log_entries()
                            for log_entry in recent_logs[-5:]:  # Show last 5 log entries
                                self.log_message(log_entry)
                            
                            # Convert hardware results to UI-compatible format for live display
                            hero_cards = game_state.get('hero_cards', [])
                            community_cards = game_state.get('community_cards', [])
                            confidence = game_state.get('analysis_confidence', 0)
                            processing_time = game_state.get('processing_time', 0)
                            recognition_method = game_state.get('recognition_method', 'Unknown')
                            
                            # Log live recognition results
                            self.log_message(f"🎯 Live Recognition ({recognition_method}): {len(hero_cards)} hero, {len(community_cards)} community")
                            self.log_message(f"   Overall confidence: {confidence:.3f}, Processing: {processing_time*1000:.1f}ms")
                            
                            # Display individual cards detected
                            for i, card in enumerate(hero_cards):
                                method = card.get('method', 'Unknown')
                                conf = card.get('confidence', 0)
                                time_ms = card.get('processing_time', 0) * 1000
                                self.log_message(f"   Hero {i+1}: {card['card']} (conf: {conf:.3f}, {method}, {time_ms:.1f}ms)")
                            
                            for i, card in enumerate(community_cards):
                                method = card.get('method', 'Unknown')
                                conf = card.get('confidence', 0)
                                time_ms = card.get('processing_time', 0) * 1000
                                self.log_message(f"   Community {i+1}: {card['card']} (conf: {conf:.3f}, {method}, {time_ms:.1f}ms)")
                            
                            # Create card recognition results format for UI display
                            card_results = []
                            for i, card in enumerate(hero_cards):
                                card_results.append(type('obj', (object,), {
                                    'card_code': card.get('card', 'error'),
                                    'confidence': card.get('confidence', 0),
                                    'region_name': f'hero_card_{i+1}'
                                })())
                            
                            for i, card in enumerate(community_cards):
                                card_results.append(type('obj', (object,), {
                                    'card_code': card.get('card', 'error'),
                                    'confidence': card.get('confidence', 0),
                                    'region_name': f'community_card_{i+1}'
                                })())
                            
                            # Convert to UI analysis format
                            analysis = self.convert_ultimate_results_to_analysis(card_results)
                            if analysis:
                                self.last_analysis = analysis
                                # Update game info with live analysis
                                self.info_panel.update_game_info(analysis)
                                
                                # Update live recognition status in game info panel
                                if hasattr(self.info_panel, 'update_live_recognition_status'):
                                    self.info_panel.update_live_recognition_status(game_state)
                                
                                self.log_message(f"✅ Live UI analysis updated successfully")
                            else:
                                self.log_message("⚠️ Live analysis conversion failed")
        except Exception as e:
            self.log_message(f"Hardware livestream error: {e}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
        
        # Schedule next update (faster for live recognition)
        if self._hardware_livestream_running:
            self.root.after(500, self._update_hardware_livestream)  # Update every 500ms for live recognition
    
    def set_capture_mode(self, mode):
        """Set the capture mode."""
        self.capture_mode = mode
        if mode == "obs":
            self.log_message("Switched to OBS Virtual Camera mode")
        else:
            self.log_message("Switched to Window Capture mode")
    
    def convert_ultimate_results_to_analysis(self, card_results):
        """
        Convert ultimate recognition results to standard analysis format.
        FIXED: Use proper classes instead of namedtuples for method compatibility.
        """
        try:
            # Create proper classes for UI compatibility
            class HoleCards:
                def __init__(self, card1, card2, confidence):
                    self.card1 = card1
                    self.card2 = card2
                    self.detection_confidence = confidence
                    self.cards = [card1, card2]  # For compatibility
                
                def is_valid(self):
                    return (self.card1 not in ['error', 'empty', None] and 
                           self.card2 not in ['error', 'empty', None] and
                           self.card1 != self.card2)
                
                def __str__(self):
                    return f"{self.card1} {self.card2}"
            
            class CommunityCards:
                def __init__(self, cards, confidence):
                    self.cards = cards
                    self.count = len(cards)
                    self.detection_confidence = confidence
                    
                    # Determine phase
                    if len(cards) >= 5:
                        self.phase = 'river'
                    elif len(cards) >= 4:
                        self.phase = 'turn'
                    elif len(cards) >= 3:
                        self.phase = 'flop'
                    else:
                        self.phase = 'preflop'
                
                def get_visible_cards(self):
                    return self.cards
                
                def __str__(self):
                    return " ".join(self.cards) if self.cards else "? ? ? ? ?"
            
            class GameState:
                def __init__(self, phase):
                    self.phase = phase
                    self.active_players = 1
            
            class TableInfo:
                def __init__(self):
                    self.players = []
                    self.pot_size = 0.0
                    self.dealer_seat = 0
                    self.hero_seat = 0
            
            # Initialize analysis structure
            analysis = {
                'timestamp': time.time(),
                'hole_cards': None,
                'community_cards': None,
                'table_info': TableInfo(),
                'game_state': None
            }
            
            # Separate player cards and community cards
            player_cards = []
            community_cards = []
            
            self.log_message(f"🔍 Converting {len(card_results)} recognition results...")
            
            for result in card_results:
                if result.card_code not in ['empty', 'error']:
                    self.log_message(f"   Card: {result.region_name} = {result.card_code} (conf: {result.confidence:.3f})")
                    
                    if 'hero' in result.region_name.lower():
                        player_cards.append({
                            'card': result.card_code,
                            'confidence': result.confidence,
                            'region': result.region_name
                        })
                    elif 'community' in result.region_name.lower():
                        community_cards.append({
                            'card': result.card_code,
                            'confidence': result.confidence,
                            'region': result.region_name
                        })
            
            # Create hole cards object
            if len(player_cards) >= 2:
                # Sort to ensure consistent order (hero_card_1, hero_card_2)
                player_cards.sort(key=lambda x: x['region'])
                
                avg_confidence = sum(c['confidence'] for c in player_cards[:2]) / 2
                analysis['hole_cards'] = HoleCards(
                    card1=player_cards[0]['card'],
                    card2=player_cards[1]['card'],
                    confidence=avg_confidence
                )
                
                self.log_message(f"✅ Hole cards: {analysis['hole_cards']} (confidence: {avg_confidence:.3f})")
            
            # Create community cards object
            if community_cards:
                # Sort by region name to ensure correct order
                community_cards.sort(key=lambda x: x['region'])
                
                valid_cards = [c['card'] for c in community_cards]
                avg_confidence = sum(c['confidence'] for c in community_cards) / len(community_cards)
                
                analysis['community_cards'] = CommunityCards(valid_cards, avg_confidence)
                
                self.log_message(f"✅ Community cards: {analysis['community_cards']} (confidence: {avg_confidence:.3f})")
            
            # Create game state
            phase = analysis['community_cards'].phase if analysis['community_cards'] else 'preflop'
            analysis['game_state'] = GameState(phase)
            
            self.log_message(f"🎯 Analysis conversion complete: hole_cards={analysis['hole_cards'] is not None}, community_cards={analysis['community_cards'] is not None}")
            
            return analysis
            
        except Exception as e:
            self.log_message(f"❌ Error converting ultimate results: {e}")
            import traceback
            traceback.print_exc()
            return None

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
            
            self.log_message("Manually refreshing regions from saved configuration...")
            
            # Create a fresh region loader to ensure we get the latest file data
            loader = RegionLoader()
            
            if not loader.regions_exist():
                self.log_message("WARNING: No region configuration file found. Please calibrate regions first.")
                return False

            # CRITICAL FIX: Support both traditional bot and hardware capture modes
            if self.bot or self.hardware_capture:
                # Force reload regions in the loader first
                loader._regions = None  # Clear cached regions
                loader._community_regions = None
                loader._hero_regions = None
                loader.load_regions()  # Force fresh load from file
                
                self.log_message("SUCCESS: Region configuration reloaded from file")
                
                # Update traditional bot if it exists
                if self.bot:
                    # Update card recognizer with fresh regions
                    hero_regions = loader.get_hero_card_regions()
                    if hero_regions and hasattr(self.bot, 'card_recognizer'):
                        self.bot.card_recognizer.card_regions = hero_regions
                        if hasattr(self.bot.card_recognizer, 'update_regions'):
                            self.bot.card_recognizer.update_regions(hero_regions)
                        self.log_message(f"SUCCESS: Refreshed {len(hero_regions)} hero card regions for traditional bot")
                        for name, region in hero_regions.items():
                            self.log_message(f"   HERO {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
                    
                    # Update community card detector with fresh regions
                    community_regions = loader.get_community_card_regions()
                    if community_regions and hasattr(self.bot, 'community_detector'):
                        self.bot.community_detector.community_card_regions = community_regions
                        if hasattr(self.bot.community_detector, 'update_regions'):
                            self.bot.community_detector.update_regions(community_regions)
                        self.log_message(f"SUCCESS: Refreshed {len(community_regions)} community card regions for traditional bot")
                        for name, region in community_regions.items():
                            self.log_message(f"   COMMUNITY {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
                    
                    # CRITICAL FIX: Clear last analysis to force new frame processing
                    self.last_analysis = None
                    if hasattr(self.bot, 'last_analysis'):
                        self.bot.last_analysis = None
                    
                    # CRITICAL FIX: Force image processor to reload regions
                    if hasattr(self.bot, 'image_processor'):
                        if hasattr(self.bot.image_processor, 'table_regions'):
                            self.bot.image_processor.table_regions = None  # Force reload
                
                # Update hardware capture system if it exists
                if self.hardware_capture:
                    # Force hardware capture to reload regions
                    if hasattr(self.hardware_capture, 'auto_calibrate_from_hardware'):
                        success = self.hardware_capture.auto_calibrate_from_hardware()
                        if success:
                            self.log_message("SUCCESS: Hardware capture regions refreshed from configuration")
                            # Log loaded hardware regions
                            if hasattr(self.hardware_capture, 'calibrated_regions'):
                                for region_name, region_data in self.hardware_capture.calibrated_regions.items():
                                    self.log_message(f"   HARDWARE {region_name}: x={region_data.get('x', 0)}, y={region_data.get('y', 0)}")
                        else:
                            self.log_message("WARNING: Hardware capture region refresh failed")
                    
                    # Clear hardware capture analysis cache
                    self.last_analysis = None
                
                self.log_message("SUCCESS: Complete region refresh completed - next capture will use new regions")
                return True
            else:
                self.log_message("ERROR: Neither traditional bot nor hardware capture is initialized - cannot refresh regions")
                return False
                
        except Exception as e:
            self.log_message(f"ERROR refreshing regions: {e}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
            return False

    def show_window(self):
        """Show the main window."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_closing(self):
        """Handle application closing."""
        if self.running:
            self.stop_bot()
        
        # Print final statistics
        self.log_message("Generating final bot statistics...")
        self.print_statistics()
        
        # Disconnect hardware capture if connected
        if hasattr(self, 'hardware_capture') and self.hardware_capture:
            self.disconnect_obs_camera()
        
        # Wait a moment for threads to stop
        time.sleep(0.5)
        self.log_message("👋 PokerStars Bot shutdown complete")
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

# Main execution section for standalone running
if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print("🚀 Starting PokerStars Bot - Modern UI")
    print("=" * 50)
    print("✅ Live Recognition System")
    print("📱 Hardware Capture Integration")
    print("🎯 Ultimate Card Recognition")
    print("=" * 50)
    
    try:
        # Create and run the application
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")