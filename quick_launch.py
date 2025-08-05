"""
Quick Launch Script for PokerBot with OBS Virtual Camera
"""
import sys
import os
import tkinter as tk
from pathlib import Path
import logging
import time

def setup_environment():
    """Setup the Python environment and paths"""
    project_root = Path(__file__).parent.absolute()
    
    # Add to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Add src directory
    src_path = project_root / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return project_root

def setup_logging():
    """Setup logging for the bot"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pokerbot_live.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("QuickLaunch")

def test_hardware_capture_first():
    """Test hardware capture before launching UI"""
    logger = logging.getLogger("HardwareTest")
    
    try:
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        
        print("🔍 Testing Hardware Capture System...")
        
        # Create config for live use
        config = HardwareCaptureConfig(
            debug_mode=True,
            analysis_interval=1.0,
            auto_calibration=True
        )
        
        # Initialize capture system
        capture_system = HardwareCaptureSystem(config)
        
        # Test OBS Virtual Camera connection
        print("📹 Connecting to OBS Virtual Camera...")
        if capture_system.connect_to_virtual_camera():
            print(f"✅ Connected to OBS Virtual Camera at index {capture_system.camera_index}")
            
            # Test frame capture
            screenshot = capture_system.capture_from_virtual_camera()
            if screenshot is not None:
                print(f"✅ Frame capture successful: {screenshot.shape}")
                
                # Check frame quality
                avg_brightness = screenshot.mean()
                print(f"📊 Frame brightness: {avg_brightness:.1f}")
                
                if avg_brightness < 10:
                    print("⚠️  Frame appears mostly black - check OBS source")
                    return None
                else:
                    print("✅ Frame has visible content")
                
                # Test auto-calibration
                print("🎯 Testing auto-calibration...")
                if capture_system.auto_calibrate_from_hardware():
                    regions = len(capture_system.calibrated_regions) if capture_system.calibrated_regions else 0
                    print(f"✅ Auto-calibration successful: {regions} regions found")
                    return capture_system
                else:
                    print("⚠️  Auto-calibration failed, but continuing...")
                    return capture_system
            else:
                print("❌ Frame capture failed")
                return None
        else:
            print("❌ Could not connect to OBS Virtual Camera")
            print("Make sure:")
            print("  • OBS Studio is running")
            print("  • Virtual Camera is started in OBS")
            print("  • PokerStars table is visible in OBS")
            return None
            
    except Exception as e:
        logger.error(f"Hardware capture test failed: {e}")
        return None

def launch_simple_ui(capture_system=None):
    """Launch a simple UI for monitoring the bot"""
    
    class SimplePokerBotUI:
        def __init__(self, capture_system=None):
            self.capture_system = capture_system
            self.root = tk.Tk()
            self.root.title("PokerBot Live - OBS Virtual Camera")
            self.root.geometry("800x600")
            self.root.configure(bg='#2b2b2b')
            
            self.create_widgets()
            self.running = False
            
        def create_widgets(self):
            # Title
            title_label = tk.Label(
                self.root, 
                text="🎯 PokerBot Live Recognition", 
                font=("Arial", 16, "bold"),
                bg='#2b2b2b', 
                fg='white'
            )
            title_label.pack(pady=10)
            
            # Status frame
            status_frame = tk.Frame(self.root, bg='#2b2b2b')
            status_frame.pack(fill='x', padx=10, pady=5)
            
            # Connection status
            self.connection_label = tk.Label(
                status_frame,
                text="📹 Camera: Connecting...",
                font=("Arial", 10),
                bg='#2b2b2b',
                fg='yellow'
            )
            self.connection_label.pack(anchor='w')
            
            # Recognition status
            self.recognition_label = tk.Label(
                status_frame,
                text="🎯 Recognition: Initializing...",
                font=("Arial", 10),
                bg='#2b2b2b',
                fg='yellow'
            )
            self.recognition_label.pack(anchor='w')
            
            # Control buttons
            button_frame = tk.Frame(self.root, bg='#2b2b2b')
            button_frame.pack(fill='x', padx=10, pady=10)
            
            self.start_button = tk.Button(
                button_frame,
                text="🎮 Start Live Recognition",
                command=self.start_recognition,
                bg='#4CAF50',
                fg='white',
                font=("Arial", 12, "bold"),
                padx=20,
                pady=10
            )
            self.start_button.pack(side='left', padx=5)
            
            self.stop_button = tk.Button(
                button_frame,
                text="⏹️ Stop Recognition",
                command=self.stop_recognition,
                bg='#f44336',
                fg='white',
                font=("Arial", 12, "bold"),
                padx=20,
                pady=10,
                state='disabled'
            )
            self.stop_button.pack(side='left', padx=5)
            
            # Results display
            results_label = tk.Label(
                self.root,
                text="📊 Live Recognition Results:",
                font=("Arial", 12, "bold"),
                bg='#2b2b2b',
                fg='white'
            )
            results_label.pack(anchor='w', padx=10, pady=(20, 5))
            
            # Results text area
            text_frame = tk.Frame(self.root, bg='#2b2b2b')
            text_frame.pack(fill='both', expand=True, padx=10, pady=5)
            
            self.results_text = tk.Text(
                text_frame,
                bg='#1e1e1e',
                fg='white',
                font=("Consolas", 10),
                wrap='word'
            )
            
            scrollbar = tk.Scrollbar(text_frame, orient='vertical', command=self.results_text.yview)
            self.results_text.configure(yscrollcommand=scrollbar.set)
            
            self.results_text.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Initialize status
            self.update_status()
        
        def update_status(self):
            """Update status labels"""
            if self.capture_system:
                if self.capture_system.virtual_camera and self.capture_system.virtual_camera.isOpened():
                    self.connection_label.config(text="📹 Camera: Connected ✅", fg='green')
                else:
                    self.connection_label.config(text="📹 Camera: Disconnected ❌", fg='red')
                
                # Check recognition systems
                if self.capture_system.ultimate_recognition:
                    self.recognition_label.config(text="🎯 Recognition: Ultimate System Ready ✅", fg='green')
                elif self.capture_system.enhanced_recognition:
                    self.recognition_label.config(text="🎯 Recognition: Enhanced System Ready ✅", fg='green')
                elif self.capture_system.ocr_systems:
                    self.recognition_label.config(text="🎯 Recognition: Fallback System Ready ⚠️", fg='orange')
                else:
                    self.recognition_label.config(text="🎯 Recognition: No System Available ❌", fg='red')
            else:
                self.connection_label.config(text="📹 Camera: Not Initialized ❌", fg='red')
                self.recognition_label.config(text="🎯 Recognition: Not Available ❌", fg='red')
            
            # Schedule next update
            self.root.after(2000, self.update_status)
        
        def start_recognition(self):
            """Start live recognition"""
            if not self.capture_system:
                self.add_result("❌ No capture system available")
                return
            
            self.running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            self.add_result("🎮 Starting live recognition...")
            self.add_result("📡 Monitoring OBS Virtual Camera...")
            
            # Set up UI callback for live logging
            self.capture_system.set_ui_log_callback(self.add_result)
            
            # Start recognition loop
            self.recognition_loop()
        
        def stop_recognition(self):
            """Stop live recognition"""
            self.running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
            self.add_result("⏹️ Recognition stopped")
        
        def recognition_loop(self):
            """Main recognition loop"""
            if not self.running:
                return
            
            try:
                # Analyze current frame
                game_state = self.capture_system.analyze_current_frame()
                
                if game_state:
                    # Display results
                    hero_cards = game_state.get('hero_cards', [])
                    community_cards = game_state.get('community_cards', [])
                    confidence = game_state.get('analysis_confidence', 0)
                    
                    if hero_cards or community_cards:
                        result_text = f"🃏 Hero: {[c['card'] for c in hero_cards]} | Community: {[c['card'] for c in community_cards]} | Conf: {confidence:.3f}"
                        self.add_result(result_text)
                
            except Exception as e:
                self.add_result(f"❌ Recognition error: {e}")
            
            # Schedule next recognition
            if self.running:
                self.root.after(1000, self.recognition_loop)
        
        def add_result(self, text):
            """Add result to display"""
            timestamp = time.strftime("%H:%M:%S")
            formatted_text = f"[{timestamp}] {text}\n"
            
            self.results_text.insert(tk.END, formatted_text)
            self.results_text.see(tk.END)
            
            # Keep only last 100 lines
            lines = self.results_text.get("1.0", tk.END).split('\n')
            if len(lines) > 100:
                self.results_text.delete("1.0", "10.0")
        
        def run(self):
            """Start the UI"""
            try:
                self.root.mainloop()
            except Exception as e:
                print(f"UI Error: {e}")
            finally:
                self.running = False
                if self.capture_system and self.capture_system.virtual_camera:
                    self.capture_system.virtual_camera.release()
    
    # Create and run UI
    ui = SimplePokerBotUI(capture_system)
    ui.run()

def main():
    """Main function"""
    print("🚀 PokerBot Quick Launch - OBS Virtual Camera Edition")
    print("=" * 60)
    
    # Setup environment
    logger = setup_logging()
    project_root = setup_environment()
    
    logger.info(f"Project root: {project_root}")
    print(f"📁 Project root: {project_root}")
    
    # Test hardware capture first
    print("\n🔧 Step 1: Testing Hardware Capture System")
    capture_system = test_hardware_capture_first()
    
    if capture_system:
        print("\n🎮 Step 2: Launching Live Recognition UI")
        print("The UI will show live recognition results from your OBS Virtual Camera")
        print("Make sure PokerStars is visible in OBS!")
        
        # Launch UI
        launch_simple_ui(capture_system)
    else:
        print("\n❌ Hardware capture test failed")
        print("Please check:")
        print("  • OBS Studio is running")
        print("  • Virtual Camera is started in OBS (Tools → Virtual Camera → Start)")
        print("  • PokerStars table is visible in OBS preview")
        print("  • UGREEN capture card is working properly")
        
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
