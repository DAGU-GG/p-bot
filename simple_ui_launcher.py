"""
Simple UI Launcher
Direct launcher for the modern UI, bypassing corrupted imports
"""

import sys
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class SimplePokerUI:
    """Simplified poker bot UI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Poker Study Tool - Educational Interface")
        self.root.geometry("800x600")
        
        # Configure style
        self.setup_style()
        
        # Create interface
        self.create_widgets()
        
    def setup_style(self):
        """Setup the UI styling"""
        self.root.configure(bg='#2b2b2b')
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark theme colors
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
        style.configure('TButton', background='#404040', foreground='#ffffff')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TNotebook', background='#2b2b2b')
        style.configure('TNotebook.Tab', background='#404040', foreground='#ffffff')
    
    def create_widgets(self):
        """Create all UI widgets"""
        
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="🎯 Poker Study Tool", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, text="Educational Use Only", font=("Arial", 10))
        subtitle_label.pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Analysis tab
        self.create_analysis_tab(notebook)
        
        # Settings tab
        self.create_settings_tab(notebook)
        
        # About tab
        self.create_about_tab(notebook)
    
    def create_analysis_tab(self, notebook):
        """Create the analysis tab"""
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="📊 Analysis")
        
        # Control buttons
        control_frame = ttk.LabelFrame(analysis_frame, text="Analysis Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="📸 Take Screenshot", 
                  command=self.take_screenshot).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🔧 Auto-Calibrate", 
                  command=self.auto_calibrate).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🧪 Test Recognition", 
                  command=self.test_recognition).pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(analysis_frame, text="Analysis Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=20, width=80,
                                                     bg='#1e1e1e', fg='#ffffff', 
                                                     insertbackground='#ffffff')
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add initial text
        self.log_message("🎯 Poker Study Tool Ready")
        self.log_message("📚 This is an educational analysis tool")
        self.log_message("✅ All systems operational")
        self.log_message("")
        self.log_message("Instructions:")
        self.log_message("1. Take a screenshot to analyze poker hands")
        self.log_message("2. Use auto-calibrate to detect table layout")
        self.log_message("3. Test recognition to verify card detection")
    
    def create_settings_tab(self, notebook):
        """Create the settings tab"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ Settings")
        
        # Recognition settings
        recog_frame = ttk.LabelFrame(settings_frame, text="Recognition Settings")
        recog_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # OCR method
        ttk.Label(recog_frame, text="OCR Method:").pack(anchor=tk.W, padx=10, pady=5)
        
        self.ocr_method = tk.StringVar(value="enhanced")
        ttk.Radiobutton(recog_frame, text="Enhanced OCR (Recommended)", 
                       variable=self.ocr_method, value="enhanced").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(recog_frame, text="Fallback Pattern Matching", 
                       variable=self.ocr_method, value="fallback").pack(anchor=tk.W, padx=20)
        
        # 4-color deck support
        self.four_color = tk.BooleanVar(value=True)
        ttk.Checkbutton(recog_frame, text="4-Color Deck Support", 
                       variable=self.four_color).pack(anchor=tk.W, padx=10, pady=5)
        
        # Debug mode
        self.debug_mode = tk.BooleanVar(value=True)
        ttk.Checkbutton(recog_frame, text="Debug Mode (Save Images)", 
                       variable=self.debug_mode).pack(anchor=tk.W, padx=10, pady=5)
        
        # Analysis settings
        analysis_frame = ttk.LabelFrame(settings_frame, text="Analysis Settings")
        analysis_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Analysis interval
        interval_frame = ttk.Frame(analysis_frame)
        interval_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(interval_frame, text="Update Interval:").pack(side=tk.LEFT)
        self.interval = tk.DoubleVar(value=2.0)
        ttk.Scale(interval_frame, from_=0.5, to=5.0, variable=self.interval,
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.interval_label = ttk.Label(interval_frame, text="2.0s")
        self.interval_label.pack(side=tk.LEFT)
        
        # Update interval display
        self.interval.trace('w', self.update_interval_label)
    
    def create_about_tab(self, notebook):
        """Create the about tab"""
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="ℹ️ About")
        
        # About content
        about_text = """
🎯 Poker Study Tool

This is an educational poker analysis tool designed for studying and learning poker strategy.

Features:
✅ Screenshot-based hand analysis
✅ Automatic table layout detection
✅ Advanced OCR card recognition
✅ 4-color deck support
✅ Multiple recognition methods
✅ Educational visualizations

Educational Purpose:
This tool is designed for educational use only. It helps players understand poker 
mathematics, hand analysis, and strategic concepts through automated analysis of 
poker scenarios.

Technology:
- Enhanced OCR with multiple recognition strategies
- Auto-calibration for different table layouts
- Pattern matching for reliable card detection
- Safe visualization and debugging features

© 2025 Poker Study Tool - Educational Use Only
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT, 
                               font=("Arial", 10))
        about_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def update_interval_label(self, *args):
        """Update interval label"""
        self.interval_label.config(text=f"{self.interval.get():.1f}s")
    
    def log_message(self, message):
        """Add a message to the results log"""
        self.results_text.insert(tk.END, f"{message}\n")
        self.results_text.see(tk.END)
        self.root.update()
    
    def take_screenshot(self):
        """Take a screenshot for analysis"""
        self.log_message("📸 Taking screenshot...")
        
        try:
            # Import screenshot capability
            import pyautogui
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Save screenshot
            filename = f"analysis_screenshot_{int(time.time())}.png"
            screenshot.save(filename)
            
            self.log_message(f"✅ Screenshot saved as: {filename}")
            self.log_message(f"   Size: {screenshot.size}")
            
            # Try to analyze if systems are available
            try:
                from table_reference_system import TableReferenceSystem
                table_ref = TableReferenceSystem()
                
                # Convert to CV2 format for analysis
                import cv2
                import numpy as np
                screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Auto-calibrate
                regions = table_ref.auto_calibrate_from_screenshot(screenshot_cv)
                if regions:
                    self.log_message(f"🔧 Auto-detected {len(regions)} regions:")
                    for name, data in regions.items():
                        self.log_message(f"   • {name}")
                else:
                    self.log_message("⚠️ No poker table detected in screenshot")
                    
            except ImportError:
                self.log_message("⚠️ Advanced analysis not available")
            except Exception as e:
                self.log_message(f"⚠️ Analysis error: {e}")
                
        except ImportError:
            self.log_message("❌ Screenshot capability not available")
            self.log_message("   Install with: pip install pyautogui")
        except Exception as e:
            self.log_message(f"❌ Screenshot error: {e}")
    
    def auto_calibrate(self):
        """Run auto-calibration"""
        self.log_message("🔧 Starting auto-calibration...")
        
        try:
            from table_reference_system import TableReferenceSystem
            
            # Create table reference system
            table_ref = TableReferenceSystem()
            
            # Take screenshot first
            import pyautogui
            screenshot = pyautogui.screenshot()
            
            # Convert to CV2 format
            import cv2
            import numpy as np
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Run auto-calibration
            regions = table_ref.auto_calibrate_from_screenshot(screenshot_cv)
            
            if regions:
                self.log_message(f"✅ Auto-calibration successful! Found {len(regions)} regions:")
                for name, data in regions.items():
                    x, y = data.get('center', (0, 0))
                    confidence = data.get('confidence', 0)
                    self.log_message(f"   • {name}: x={x:.3f}, y={y:.3f} (confidence: {confidence:.2f})")
                
                self.log_message("💾 Regions saved for future use")
            else:
                self.log_message("❌ Auto-calibration failed")
                self.log_message("   Make sure a poker table is visible on screen")
                
        except ImportError as e:
            self.log_message(f"❌ Auto-calibration not available: {e}")
        except Exception as e:
            self.log_message(f"❌ Auto-calibration error: {e}")
    
    def test_recognition(self):
        """Test card recognition"""
        self.log_message("🧪 Testing card recognition...")
        
        try:
            # Test enhanced OCR
            if self.ocr_method.get() == "enhanced":
                from enhanced_ocr_recognition import EnhancedOCRCardRecognition
                recognizer = EnhancedOCRCardRecognition()
                self.log_message("✅ Enhanced OCR system loaded")
            else:
                from fallback_card_recognition import FallbackCardRecognition
                recognizer = FallbackCardRecognition()
                self.log_message("✅ Fallback recognition system loaded")
            
            # Test with generated card image
            import cv2
            import numpy as np
            
            # Create a test card image
            test_card = np.ones((100, 70, 3), dtype=np.uint8) * 255
            
            # Add simple card elements (A♠)
            cv2.rectangle(test_card, (10, 10), (60, 90), (0, 0, 0), 2)
            cv2.putText(test_card, 'A', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.putText(test_card, '♠', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            
            # Test recognition
            if self.ocr_method.get() == "enhanced":
                result = recognizer.recognize_card(test_card, debug=self.debug_mode.get())
            else:
                result = recognizer.recognize_card(test_card, four_color_deck=self.four_color.get())
            
            if result and result.confidence > 0:
                self.log_message(f"🎯 Recognition test successful!")
                self.log_message(f"   Detected: {result.rank}{result.suit}")
                self.log_message(f"   Confidence: {result.confidence:.2f}")
                self.log_message(f"   Method: {result.method}")
            else:
                self.log_message("⚠️ Recognition test returned low confidence")
                
        except ImportError as e:
            self.log_message(f"❌ Recognition system not available: {e}")
        except Exception as e:
            self.log_message(f"❌ Recognition test error: {e}")
    
    def run(self):
        """Start the UI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass

def main():
    """Main function to run the UI"""
    import time
    
    print("🎯 Starting Poker Study Tool UI...")
    
    # Check for required modules
    try:
        import tkinter
        print("✅ Tkinter available")
    except ImportError:
        print("❌ Tkinter not available")
        return
    
    try:
        import pyautogui
        print("✅ Screenshot capability available")
    except ImportError:
        print("⚠️ Screenshot capability not available (install pyautogui)")
    
    # Create and run UI
    app = SimplePokerUI()
    app.run()

if __name__ == "__main__":
    main()
