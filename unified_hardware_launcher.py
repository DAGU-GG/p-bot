"""
Unified Hardware Capture Launcher
Integrates the hardware capture system with the modern UI properly
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Optional, Dict, Any

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import hardware capture system
try:
    from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
    HARDWARE_CAPTURE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Hardware capture not available: {e}")
    HARDWARE_CAPTURE_AVAILABLE = False

# Import enhanced recognition
try:
    from enhanced_card_recognition import EnhancedCardRecognition
    ENHANCED_RECOGNITION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Enhanced recognition not available: {e}")
    ENHANCED_RECOGNITION_AVAILABLE = False

class UnifiedHardwareLauncher:
    """Unified launcher for hardware capture with modern UI integration"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 P-Bot 2 - Unified Hardware Capture")
        self.root.geometry("1000x800")
        
        # Configure logging to avoid encoding issues
        self.setup_logging()
        
        # Initialize systems
        self.hardware_system = None
        self.recognition_system = None
        self.analysis_running = False
        
        # GUI setup
        self.create_gui()
        
        # Status tracking
        self.last_analysis = None
        
    def setup_logging(self):
        """Setup logging with proper encoding"""
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('unified_hardware.log', encoding='utf-8')
            ]
        )
        
        self.logger = logging.getLogger("unified_hardware")
        self.logger.info("Unified hardware launcher initialized")
    
    def create_gui(self):
        """Create the GUI interface"""
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="🎯 P-Bot 2 - Unified Hardware Capture", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, 
                                  text="Hardware HDMI Capture → Analysis → Strategic Advice",
                                  font=("Arial", 10))
        subtitle_label.pack(pady=5)
        
        # Main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_setup_tab()
        self.create_calibration_tab()
        self.create_analysis_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
    def create_setup_tab(self):
        """Create hardware setup tab"""
        setup_frame = ttk.Frame(self.notebook)
        self.notebook.add(setup_frame, text="🔧 Hardware Setup")
        
        # Instructions
        instructions = ttk.LabelFrame(setup_frame, text="Hardware Setup Instructions")
        instructions.pack(fill=tk.X, padx=10, pady=10)
        
        instruction_text = """
1. Connect Laptop HDMI → HDMI Splitter → UGREEN Capture Card → Main PC USB
2. Start OBS Studio on Main PC, configure UGREEN capture as video source
3. Enable OBS Virtual Camera (Tools → Virtual Camera → Start Virtual Camera)
4. Open PokerStars on Laptop with play money table
5. Click "Test Hardware Connection" below to verify setup
6. Proceed to Calibration tab to detect table regions
7. Start analysis in Analysis tab
        """
        
        ttk.Label(instructions, text=instruction_text, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Test buttons
        test_frame = ttk.LabelFrame(setup_frame, text="Hardware Tests")
        test_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(test_frame, text="1. Test OBS Connection", 
                  command=self.test_obs_connection).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(test_frame, text="2. Test Screenshot Capture", 
                  command=self.test_screenshot).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(test_frame, text="3. Test Full System", 
                  command=self.test_full_system).pack(fill=tk.X, padx=10, pady=5)
        
        # Status display
        self.setup_status = scrolledtext.ScrolledText(setup_frame, height=15)
        self.setup_status.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_calibration_tab(self):
        """Create calibration tab"""
        cal_frame = ttk.Frame(self.notebook)
        self.notebook.add(cal_frame, text="📐 Calibration")
        
        # Auto-calibration section
        auto_frame = ttk.LabelFrame(cal_frame, text="Automatic Calibration")
        auto_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(auto_frame, text="Automatically detect poker table regions from hardware capture").pack(padx=10, pady=5)
        
        cal_button_frame = ttk.Frame(auto_frame)
        cal_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(cal_button_frame, text="🎯 Auto-Calibrate Table", 
                  command=self.auto_calibrate).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(cal_button_frame, text="💾 Save Calibration", 
                  command=self.save_calibration).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(cal_button_frame, text="📁 Load Calibration", 
                  command=self.load_calibration).pack(side=tk.LEFT, padx=5)
        
        # Calibration status
        self.cal_status = scrolledtext.ScrolledText(cal_frame, height=20)
        self.cal_status.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_analysis_tab(self):
        """Create analysis tab"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="🎯 Live Analysis")
        
        # Control panel
        control_frame = ttk.LabelFrame(analysis_frame, text="Analysis Control")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Analysis", 
                                   command=self.start_analysis)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop Analysis", 
                                  command=self.stop_analysis, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_indicator = ttk.Label(button_frame, text="● Stopped", foreground="red")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
        
        # Game state display
        game_frame = ttk.LabelFrame(analysis_frame, text="Current Game State")
        game_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Hero cards
        hero_frame = ttk.Frame(game_frame)
        hero_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(hero_frame, text="Hero Cards:").pack(side=tk.LEFT)
        self.hero_label = ttk.Label(hero_frame, text="Not detected", font=("Arial", 12, "bold"))
        self.hero_label.pack(side=tk.LEFT, padx=10)
        
        # Community cards
        community_frame = ttk.Frame(game_frame)
        community_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(community_frame, text="Community:").pack(side=tk.LEFT)
        self.community_label = ttk.Label(community_frame, text="Not detected", font=("Arial", 12))
        self.community_label.pack(side=tk.LEFT, padx=10)
        
        # Advice display
        advice_frame = ttk.LabelFrame(analysis_frame, text="Poker Advice")
        advice_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Action recommendation
        action_frame = ttk.Frame(advice_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(action_frame, text="Recommended Action:").pack(side=tk.LEFT)
        self.action_label = ttk.Label(action_frame, text="No advice", 
                                     font=("Arial", 14, "bold"), foreground="blue")
        self.action_label.pack(side=tk.LEFT, padx=10)
        
        # Reasoning
        self.reasoning_text = scrolledtext.ScrolledText(advice_frame, height=8)
        self.reasoning_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Recognition settings
        rec_frame = ttk.LabelFrame(settings_frame, text="Recognition Settings")
        rec_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.recognition_method = tk.StringVar(value="enhanced")
        ttk.Radiobutton(rec_frame, text="Enhanced OCR + Pattern Matching", 
                       variable=self.recognition_method, value="enhanced").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Radiobutton(rec_frame, text="Pattern Matching Only", 
                       variable=self.recognition_method, value="pattern").pack(anchor=tk.W, padx=10, pady=5)
        
        # Analysis settings
        analysis_frame = ttk.LabelFrame(settings_frame, text="Analysis Settings")
        analysis_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Interval setting
        interval_frame = ttk.Frame(analysis_frame)
        interval_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(interval_frame, text="Analysis Interval (seconds):").pack(side=tk.LEFT)
        self.interval_var = tk.DoubleVar(value=2.0)
        ttk.Scale(interval_frame, from_=0.5, to=5.0, variable=self.interval_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.interval_label = ttk.Label(interval_frame, text="2.0")
        self.interval_label.pack(side=tk.LEFT)
        
        self.interval_var.trace('w', self.update_interval_label)
        
        # Debug mode
        self.debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(analysis_frame, text="Save debug images", 
                       variable=self.debug_var).pack(anchor=tk.W, padx=10, pady=5)
        
    def create_logs_tab(self):
        """Create logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📝 Logs")
        
        # Control buttons
        log_control = ttk.Frame(logs_frame)
        log_control.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_control, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_control, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(logs_frame, height=25)
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def update_interval_label(self, *args):
        """Update interval label"""
        self.interval_label.config(text=f"{self.interval_var.get():.1f}")
        
    def log_message(self, message: str):
        """Add message to both logger and GUI"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        # Add to GUI
        self.log_display.insert(tk.END, formatted_msg + "\n")
        self.log_display.see(tk.END)
        self.root.update()
        
        # Add to logger
        self.logger.info(message)
        
    def test_obs_connection(self):
        """Test OBS connection"""
        self.setup_status.delete(1.0, tk.END)
        self.setup_status.insert(tk.END, "Testing OBS connection...\n")
        
        try:
            if not HARDWARE_CAPTURE_AVAILABLE:
                self.setup_status.insert(tk.END, "❌ Hardware capture system not available\n")
                return
            
            config = HardwareCaptureConfig(debug_mode=True)
            test_system = HardwareCaptureSystem(config)
            
            obs_window = test_system.find_obs_window()
            if obs_window:
                self.setup_status.insert(tk.END, f"✅ Found OBS window: {obs_window.title}\n")
                self.setup_status.insert(tk.END, f"   Size: {obs_window.width}x{obs_window.height}\n")
            else:
                self.setup_status.insert(tk.END, "❌ OBS window not found\n")
                self.setup_status.insert(tk.END, "   Make sure OBS Studio is running with virtual camera active\n")
                
        except Exception as e:
            self.setup_status.insert(tk.END, f"❌ Connection test failed: {e}\n")
    
    def test_screenshot(self):
        """Test screenshot capture"""
        self.setup_status.insert(tk.END, "\nTesting screenshot capture...\n")
        
        try:
            config = HardwareCaptureConfig(debug_mode=True)
            test_system = HardwareCaptureSystem(config)
            
            screenshot = test_system.capture_obs_window()
            if screenshot is not None:
                self.setup_status.insert(tk.END, f"✅ Screenshot captured: {screenshot.shape}\n")
                self.setup_status.insert(tk.END, "   Saved as hardware_capture_test.png\n")
            else:
                self.setup_status.insert(tk.END, "❌ Screenshot capture failed\n")
                
        except Exception as e:
            self.setup_status.insert(tk.END, f"❌ Screenshot test failed: {e}\n")
    
    def test_full_system(self):
        """Test full system integration"""
        self.setup_status.insert(tk.END, "\nTesting full system...\n")
        
        try:
            # Initialize hardware system
            config = HardwareCaptureConfig(
                debug_mode=True,
                recognition_method="both"
            )
            test_system = HardwareCaptureSystem(config)
            
            # Test calibration
            if test_system.auto_calibrate_from_hardware():
                self.setup_status.insert(tk.END, "✅ Auto-calibration successful\n")
                
                # Test analysis
                game_state = test_system.analyze_current_frame()
                if game_state:
                    self.setup_status.insert(tk.END, "✅ Analysis successful\n")
                    self.setup_status.insert(tk.END, f"   Hero cards: {len(game_state.get('hero_cards', []))}\n")
                    self.setup_status.insert(tk.END, f"   Community cards: {len(game_state.get('community_cards', []))}\n")
                else:
                    self.setup_status.insert(tk.END, "⚠️ Analysis returned no results\n")
            else:
                self.setup_status.insert(tk.END, "❌ Auto-calibration failed\n")
                
        except Exception as e:
            self.setup_status.insert(tk.END, f"❌ Full system test failed: {e}\n")
    
    def auto_calibrate(self):
        """Auto-calibrate table regions"""
        self.cal_status.delete(1.0, tk.END)
        self.cal_status.insert(tk.END, "Starting auto-calibration...\n")
        
        try:
            config = HardwareCaptureConfig(debug_mode=self.debug_var.get())
            self.hardware_system = HardwareCaptureSystem(config)
            
            if self.hardware_system.auto_calibrate_from_hardware():
                regions = self.hardware_system.calibrated_regions
                self.cal_status.insert(tk.END, f"✅ Auto-calibration successful! Found {len(regions)} regions:\n")
                
                for region_name, region_data in regions.items():
                    self.cal_status.insert(tk.END, f"   {region_name}: {region_data}\n")
                
                self.log_message("Auto-calibration completed successfully")
            else:
                self.cal_status.insert(tk.END, "❌ Auto-calibration failed\n")
                self.cal_status.insert(tk.END, "   Make sure PokerStars table is visible in OBS\n")
                
        except Exception as e:
            self.cal_status.insert(tk.END, f"❌ Calibration error: {e}\n")
    
    def save_calibration(self):
        """Save calibration to file"""
        if self.hardware_system and self.hardware_system.calibrated_regions:
            try:
                import json
                
                config_data = {
                    'regions': self.hardware_system.calibrated_regions,
                    'timestamp': time.time(),
                    'source': 'hardware_capture'
                }
                
                with open('region_config.json', 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                self.cal_status.insert(tk.END, "\n✅ Calibration saved to region_config.json\n")
                self.log_message("Calibration saved successfully")
                
            except Exception as e:
                self.cal_status.insert(tk.END, f"\n❌ Save failed: {e}\n")
        else:
            self.cal_status.insert(tk.END, "\n❌ No calibration data to save\n")
    
    def load_calibration(self):
        """Load calibration from file"""
        try:
            import json
            
            if os.path.exists('region_config.json'):
                with open('region_config.json', 'r') as f:
                    config_data = json.load(f)
                
                if 'regions' in config_data:
                    # Initialize hardware system if needed
                    if not self.hardware_system:
                        config = HardwareCaptureConfig(debug_mode=self.debug_var.get())
                        self.hardware_system = HardwareCaptureSystem(config)
                    
                    self.hardware_system.calibrated_regions = config_data['regions']
                    
                    self.cal_status.insert(tk.END, f"\n✅ Loaded calibration with {len(config_data['regions'])} regions\n")
                    for region_name in config_data['regions'].keys():
                        self.cal_status.insert(tk.END, f"   {region_name}\n")
                        
                    self.log_message("Calibration loaded successfully")
                else:
                    self.cal_status.insert(tk.END, "\n❌ Invalid calibration file format\n")
            else:
                self.cal_status.insert(tk.END, "\n❌ No calibration file found (region_config.json)\n")
                
        except Exception as e:
            self.cal_status.insert(tk.END, f"\n❌ Load failed: {e}\n")
    
    def start_analysis(self):
        """Start live analysis"""
        try:
            # Ensure hardware system is initialized
            if not self.hardware_system:
                config = HardwareCaptureConfig(
                    debug_mode=self.debug_var.get(),
                    recognition_method=self.recognition_method.get(),
                    analysis_interval=self.interval_var.get()
                )
                self.hardware_system = HardwareCaptureSystem(config)
            
            # Check calibration
            if not self.hardware_system.calibrated_regions:
                messagebox.showerror("Error", "No calibration found. Please calibrate first.")
                return
            
            # Initialize recognition system
            if ENHANCED_RECOGNITION_AVAILABLE and self.recognition_method.get() == "enhanced":
                self.recognition_system = EnhancedCardRecognition(debug_mode=self.debug_var.get())
            
            # Update UI
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_indicator.config(text="● Running", foreground="green")
            self.analysis_running = True
            
            self.log_message("Live analysis started")
            
            # Start analysis loop
            self.analysis_loop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start analysis: {e}")
            self.log_message(f"Analysis start failed: {e}")
    
    def stop_analysis(self):
        """Stop live analysis"""
        self.analysis_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_indicator.config(text="● Stopped", foreground="red")
        self.log_message("Live analysis stopped")
    
    def analysis_loop(self):
        """Main analysis loop"""
        if not self.analysis_running:
            return
        
        try:
            # Analyze current frame
            game_state = self.hardware_system.analyze_current_frame()
            
            if game_state:
                self.update_game_display(game_state)
                
                # Generate advice
                advice = self.hardware_system.get_poker_advice(game_state)
                self.update_advice_display(advice)
                
                # Log analysis
                hero_count = len(game_state.get('hero_cards', []))
                community_count = len(game_state.get('community_cards', []))
                self.log_message(f"Analysis: {hero_count} hero, {community_count} community cards")
                
        except Exception as e:
            self.log_message(f"Analysis error: {e}")
        
        # Schedule next analysis
        if self.analysis_running:
            interval_ms = int(self.interval_var.get() * 1000)
            self.root.after(interval_ms, self.analysis_loop)
    
    def update_game_display(self, game_state: Dict):
        """Update game state display"""
        # Hero cards
        hero_cards = game_state.get('hero_cards', [])
        if hero_cards:
            hero_text = " | ".join([card['card'] for card in hero_cards])
            self.hero_label.config(text=hero_text, foreground="blue")
        else:
            self.hero_label.config(text="Not detected", foreground="gray")
        
        # Community cards
        community_cards = game_state.get('community_cards', [])
        if community_cards:
            community_text = " | ".join([card['card'] for card in community_cards])
            self.community_label.config(text=community_text, foreground="green")
        else:
            self.community_label.config(text="Not detected", foreground="gray")
    
    def update_advice_display(self, advice: Dict):
        """Update advice display"""
        action = advice.get('action', 'unknown')
        confidence = advice.get('confidence', 0)
        reasoning = advice.get('reasoning', 'No reasoning available')
        
        # Update action
        action_text = f"{action.upper()} ({confidence:.1%})"
        color = {"raise": "green", "call": "orange", "fold": "red"}.get(action, "blue")
        self.action_label.config(text=action_text, foreground=color)
        
        # Update reasoning
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.insert(tk.END, reasoning)
    
    def clear_logs(self):
        """Clear log display"""
        self.log_display.delete(1.0, tk.END)
    
    def save_logs(self):
        """Save logs to file"""
        logs = self.log_display.get(1.0, tk.END)
        filename = f"unified_hardware_logs_{int(time.time())}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(logs)
            messagebox.showinfo("Success", f"Logs saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def run(self):
        """Start the application"""
        self.log_message("Unified Hardware Launcher started")
        self.root.mainloop()

def main():
    """Main function"""
    print("🎯 P-Bot 2 - Unified Hardware Capture Launcher")
    print("Starting unified system...")
    
    app = UnifiedHardwareLauncher()
    app.run()

if __name__ == "__main__":
    main()
