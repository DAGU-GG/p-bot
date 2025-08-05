"""
Hardware Capture Poker Bot Launcher
Launch and manage the laptop→main PC poker analysis system
"""

import os
import sys
import time
import logging
import json
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Constants
NO_CARDS_DETECTED = "No cards detected"
ACTION_COLORS = {
    "raise": "green",
    "call": "orange", 
    "fold": "red"
}

# Import hardware capture system
try:
    from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
    from compare_recognition_systems import test_hardware_capture_recognition
except ImportError as e:
    print(f"Error importing hardware capture modules: {e}")
    sys.exit(1)

class HardwareCaptureGUI:
    """GUI for hardware capture poker bot"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Poker Analysis Pro - Hardware Capture Edition")
        self.root.geometry("900x700")
        
        # Initialize systems
        self.capture_system = None
        self.analysis_running = False
        
        # Configure logging
        self.setup_logging()
        
        # Create GUI elements
        self.create_widgets()
        
        # Status tracking
        self.last_game_state = None
        self.last_advice = None
        
    def setup_logging(self):
        """Setup logging for the GUI"""
        self.logger = logging.getLogger("hardware_gui")
        
        # Create log handler that we can capture
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(self.log_handler)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup tab
        self.create_setup_tab(notebook)
        
        # Analysis tab
        self.create_analysis_tab(notebook)
        
        # Logs tab
        self.create_logs_tab(notebook)
        
        # Settings tab
        self.create_settings_tab(notebook)
    
    def create_setup_tab(self, notebook):
        """Create setup and testing tab"""
        setup_frame = ttk.Frame(notebook)
        notebook.add(setup_frame, text="🔧 Setup & Testing")
        
        # Title
        title_label = ttk.Label(setup_frame, text="Hardware Capture Setup", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Instructions
        instructions = """
1. Connect laptop HDMI → Splitter → Capture Card → Main PC
2. Open PokerStars on laptop
3. Start OBS Studio on main PC with UGREEN capture device configured
4. Click 'Test Hardware Setup' to verify everything works
5. Once verified, start analysis in the Analysis tab
        """
        
        instruction_label = ttk.Label(setup_frame, text=instructions, justify=tk.LEFT)
        instruction_label.pack(pady=10, padx=20)
        
        # Test buttons frame
        test_frame = ttk.LabelFrame(setup_frame, text="Hardware Tests")
        test_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Test buttons
        ttk.Button(test_frame, text="1. Test OBS Window Detection", 
                  command=self.test_obs_detection).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(test_frame, text="2. Test Screenshot Capture", 
                  command=self.test_screenshot).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(test_frame, text="3. Test Auto-Calibration", 
                  command=self.test_calibration).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(test_frame, text="4. Test Full Recognition", 
                  command=self.test_full_recognition).pack(fill=tk.X, padx=10, pady=5)
        
        # Status display
        self.setup_status = scrolledtext.ScrolledText(setup_frame, height=10, width=80)
        self.setup_status.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    def create_analysis_tab(self, notebook):
        """Create real-time analysis tab"""
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="🎯 Live Analysis")
        
        # Control frame
        control_frame = ttk.LabelFrame(analysis_frame, text="Analysis Control")
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="▶ Start Analysis", 
                                      command=self.start_analysis)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹ Stop Analysis", 
                                     command=self.stop_analysis, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.status_label = ttk.Label(button_frame, text="● Stopped", foreground="red")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Game state display
        state_frame = ttk.LabelFrame(analysis_frame, text="Current Game State")
        state_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Hero cards
        hero_frame = ttk.Frame(state_frame)
        hero_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(hero_frame, text="Hero Cards:").pack(side=tk.LEFT)
        self.hero_cards_label = ttk.Label(hero_frame, text=NO_CARDS_DETECTED, font=("Arial", 12, "bold"))
        self.hero_cards_label.pack(side=tk.LEFT, padx=10)
        
        # Community cards
        community_frame = ttk.Frame(state_frame)
        community_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(community_frame, text="Community:").pack(side=tk.LEFT)
        self.community_cards_label = ttk.Label(community_frame, text=NO_CARDS_DETECTED, font=("Arial", 12))
        self.community_cards_label.pack(side=tk.LEFT, padx=10)
        
        # Confidence
        confidence_frame = ttk.Frame(state_frame)
        confidence_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(confidence_frame, text="Confidence:").pack(side=tk.LEFT)
        self.confidence_label = ttk.Label(confidence_frame, text="0%")
        self.confidence_label.pack(side=tk.LEFT, padx=10)
        
        # Advice display
        advice_frame = ttk.LabelFrame(analysis_frame, text="Poker Advice")
        advice_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Recommended action
        action_frame = ttk.Frame(advice_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(action_frame, text="Recommended Action:").pack(side=tk.LEFT)
        self.action_label = ttk.Label(action_frame, text="No advice available", 
                                     font=("Arial", 14, "bold"), foreground="blue")
        self.action_label.pack(side=tk.LEFT, padx=10)
        
        # Reasoning
        self.reasoning_text = scrolledtext.ScrolledText(advice_frame, height=6, width=80)
        self.reasoning_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_logs_tab(self, notebook):
        """Create logs display tab"""
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="📝 Logs")
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=30, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control buttons
        log_control_frame = ttk.Frame(logs_frame)
        log_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_control_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(log_control_frame, text="Save Logs", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=5)
    
    def create_settings_tab(self, notebook):
        """Create settings configuration tab"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ Settings")
        
        # Recognition settings
        recog_frame = ttk.LabelFrame(settings_frame, text="Recognition Settings")
        recog_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Recognition method
        ttk.Label(recog_frame, text="Recognition Method:").pack(anchor=tk.W, padx=10, pady=5)
        self.recog_method = tk.StringVar(value="both")
        ttk.Radiobutton(recog_frame, text="Enhanced OCR (when available)", 
                       variable=self.recog_method, value="enhanced").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(recog_frame, text="Fallback Pattern Matching", 
                       variable=self.recog_method, value="fallback").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(recog_frame, text="Both (best result)", 
                       variable=self.recog_method, value="both").pack(anchor=tk.W, padx=20)
        
        # Analysis settings
        analysis_frame = ttk.LabelFrame(settings_frame, text="Analysis Settings")
        analysis_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Analysis interval
        interval_frame = ttk.Frame(analysis_frame)
        interval_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(interval_frame, text="Analysis Interval (seconds):").pack(side=tk.LEFT)
        self.analysis_interval = tk.DoubleVar(value=1.0)
        ttk.Scale(interval_frame, from_=0.5, to=5.0, variable=self.analysis_interval, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.interval_label = ttk.Label(interval_frame, text="1.0")
        self.interval_label.pack(side=tk.LEFT)
        
        # Update interval label
        self.analysis_interval.trace('w', self.update_interval_label)
        
        # Debug mode
        self.debug_mode = tk.BooleanVar(value=True)
        ttk.Checkbutton(analysis_frame, text="Save debug images", 
                       variable=self.debug_mode).pack(anchor=tk.W, padx=10, pady=5)
        
        # OBS settings
        obs_frame = ttk.LabelFrame(settings_frame, text="OBS Configuration")
        obs_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # OBS window title
        window_frame = ttk.Frame(obs_frame)
        window_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(window_frame, text="OBS Window Title:").pack(side=tk.LEFT)
        self.obs_window_title = tk.StringVar(value="OBS Studio")
        ttk.Entry(window_frame, textvariable=self.obs_window_title).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
    
    def update_interval_label(self, *args):
        """Update analysis interval label"""
        self.interval_label.config(text=f"{self.analysis_interval.get():.1f}")
    
    def log_message(self, message: str):
        """Add message to log display"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def test_obs_detection(self):
        """Test OBS window detection"""
        self.setup_status.delete(1.0, tk.END)
        self.setup_status.insert(tk.END, "Testing OBS window detection...\n")
        
        try:
            config = HardwareCaptureConfig(
                obs_window_title=self.obs_window_title.get()
            )
            capture_system = HardwareCaptureSystem(config)
            
            obs_window = capture_system.find_obs_window()
            if obs_window:
                self.setup_status.insert(tk.END, f"✅ SUCCESS: Found OBS window '{obs_window.title}'\n")
                self.setup_status.insert(tk.END, f"   Position: {obs_window.left}, {obs_window.top}\n")
                self.setup_status.insert(tk.END, f"   Size: {obs_window.width} x {obs_window.height}\n")
            else:
                self.setup_status.insert(tk.END, "❌ FAILED: OBS window not found\n")
                self.setup_status.insert(tk.END, "   Make sure OBS Studio is running\n")
                
        except Exception as e:
            self.setup_status.insert(tk.END, f"❌ ERROR: {str(e)}\n")
    
    def test_screenshot(self):
        """Test screenshot capture"""
        self.setup_status.insert(tk.END, "\nTesting screenshot capture...\n")
        
        try:
            config = HardwareCaptureConfig(
                obs_window_title=self.obs_window_title.get(),
                debug_mode=True
            )
            capture_system = HardwareCaptureSystem(config)
            
            screenshot = capture_system.capture_obs_window()
            if screenshot is not None:
                self.setup_status.insert(tk.END, f"✅ SUCCESS: Screenshot captured ({screenshot.shape})\n")
                self.setup_status.insert(tk.END, "   Saved as 'test_hardware_capture.png'\n")
            else:
                self.setup_status.insert(tk.END, "❌ FAILED: Could not capture screenshot\n")
                
        except Exception as e:
            self.setup_status.insert(tk.END, f"❌ ERROR: {str(e)}\n")
    
    def test_calibration(self):
        """Test auto-calibration"""
        self.setup_status.insert(tk.END, "\nTesting auto-calibration...\n")
        
        try:
            config = HardwareCaptureConfig(
                obs_window_title=self.obs_window_title.get(),
                debug_mode=True
            )
            capture_system = HardwareCaptureSystem(config)
            
            if capture_system.auto_calibrate_from_hardware():
                regions = capture_system.calibrated_regions
                self.setup_status.insert(tk.END, f"✅ SUCCESS: Auto-calibration found {len(regions)} regions\n")
                for region_name, region_data in regions.items():
                    self.setup_status.insert(tk.END, f"   {region_name}: {region_data}\n")
            else:
                self.setup_status.insert(tk.END, "❌ FAILED: Auto-calibration unsuccessful\n")
                self.setup_status.insert(tk.END, "   Make sure PokerStars table is visible in OBS\n")
                
        except Exception as e:
            self.setup_status.insert(tk.END, f"❌ ERROR: {str(e)}\n")
    
    def test_full_recognition(self):
        """Test full recognition system"""
        self.setup_status.insert(tk.END, "\nTesting full recognition system...\n")
        
        try:
            result = test_hardware_capture_recognition()
            if result:
                self.setup_status.insert(tk.END, "✅ SUCCESS: Full recognition test passed\n")
                self.setup_status.insert(tk.END, f"   Game state: {result.get('game_state', {})}\n")
                self.setup_status.insert(tk.END, f"   Advice: {result.get('advice', {})}\n")
            else:
                self.setup_status.insert(tk.END, "❌ FAILED: Full recognition test failed\n")
                
        except Exception as e:
            self.setup_status.insert(tk.END, f"❌ ERROR: {str(e)}\n")
    
    def start_analysis(self):
        """Start real-time analysis"""
        try:
            # Create capture system with current settings
            config = HardwareCaptureConfig(
                obs_window_title=self.obs_window_title.get(),
                recognition_method=self.recog_method.get(),
                debug_mode=self.debug_mode.get(),
                analysis_interval=self.analysis_interval.get()
            )
            
            self.capture_system = HardwareCaptureSystem(config)
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="● Running", foreground="green")
            self.analysis_running = True
            
            self.log_message("Analysis started")
            
            # Start analysis loop
            self.analysis_loop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start analysis: {str(e)}")
            self.log_message(f"Failed to start analysis: {str(e)}")
    
    def stop_analysis(self):
        """Stop real-time analysis"""
        self.analysis_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="● Stopped", foreground="red")
        self.log_message("Analysis stopped")
    
    def analysis_loop(self):
        """Main analysis loop"""
        if not self.analysis_running:
            return
        
        try:
            # Analyze current frame
            game_state = self.capture_system.analyze_current_frame()
            
            if game_state:
                self.update_game_state_display(game_state)
                
                # Generate advice
                advice = self.capture_system.get_poker_advice(game_state)
                self.update_advice_display(advice)
                
                self.log_message(f"Analysis: {len(game_state.get('hero_cards', []))} hero, {len(game_state.get('community_cards', []))} community cards")
            
        except Exception as e:
            self.log_message(f"Analysis error: {str(e)}")
        
        # Schedule next analysis
        if self.analysis_running:
            self.root.after(int(self.analysis_interval.get() * 1000), self.analysis_loop)
    
    def update_game_state_display(self, game_state):
        """Update game state display"""
        # Hero cards
        hero_cards = game_state.get('hero_cards', [])
        if hero_cards:
            hero_text = " | ".join([card['card'] for card in hero_cards])
            self.hero_cards_label.config(text=hero_text, foreground="blue")
        else:
            self.hero_cards_label.config(text=NO_CARDS_DETECTED, foreground="gray")
        
        # Community cards
        community_cards = game_state.get('community_cards', [])
        if community_cards:
            community_text = " | ".join([card['card'] for card in community_cards])
            self.community_cards_label.config(text=community_text, foreground="green")
        else:
            self.community_cards_label.config(text=NO_CARDS_DETECTED, foreground="gray")
        
        # Confidence
        confidence = game_state.get('analysis_confidence', 0)
        self.confidence_label.config(text=f"{confidence:.1%}")
    
    def update_advice_display(self, advice):
        """Update advice display"""
        action = advice.get('action', 'unknown')
        confidence = advice.get('confidence', 0)
        reasoning = advice.get('reasoning', 'No reasoning available')
        
        # Update action
        action_text = f"{action.upper()} ({confidence:.1%})"
        color = ACTION_COLORS.get(action, "blue")
        self.action_label.config(text=action_text, foreground=color)
        
        # Update reasoning
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.insert(tk.END, reasoning)
    
    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """Save logs to file"""
        logs = self.log_text.get(1.0, tk.END)
        filename = f"poker_analysis_logs_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write(logs)
        messagebox.showinfo("Success", f"Logs saved to {filename}")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    """Main function"""
    print("🎯 Poker Analysis Pro - Hardware Capture Edition")
    print("Starting GUI...")
    
    # Check if required modules are available
    try:
        import pygetwindow
        import pyautogui
    except ImportError as e:
        print(f"Missing required modules: {e}")
        print("Please install: pip install pygetwindow pyautogui")
        return
    
    # Create and run GUI
    gui = HardwareCaptureGUI()
    gui.run()

if __name__ == "__main__":
    main()
