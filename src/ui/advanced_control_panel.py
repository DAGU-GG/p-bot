"""
Advanced Control Panel Component
Provides access to enhanced recognition systems, debugging tools, and advanced features.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys


class AdvancedControlPanel:
    """Advanced control panel with enhanced features."""
    
    def __init__(self, parent, main_window):
        """Initialize the advanced control panel."""
        self.parent = parent
        self.main_window = main_window
        
        # Create advanced controls
        self.create_recognition_system_selection()
        self.create_debugging_tools()
        self.create_testing_tools()
        self.create_configuration_management()
    
    def create_recognition_system_selection(self):
        """Create recognition system selection controls."""
        recognition_frame = tk.LabelFrame(self.parent, text="Recognition System", 
                                        bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        recognition_frame.pack(fill="x", padx=5, pady=5)
        
        # Recognition system selection - SIMPLIFIED for Unified System
        self.recognition_var = tk.StringVar(value="unified")
        
        # Only show the unified system since it's the most reliable
        systems = [
            ("🎯 Unified System", "unified", "Advanced multi-template recognition with 52 cards")
        ]
        
        for i, (name, value, description) in enumerate(systems):
            frame = tk.Frame(recognition_frame, bg='#2b2b2b')
            frame.pack(fill="x", padx=5, pady=2)
            
            radio = tk.Radiobutton(
                frame, text=name, variable=self.recognition_var, value=value,
                command=self.on_recognition_change, bg='#2b2b2b', fg='white',
                selectcolor='#2b2b2b', font=("Arial", 10, "bold"), state="disabled"
            )
            radio.pack(side="left")
            
            desc_label = tk.Label(frame, text=description, bg='#2b2b2b', fg='lightgray',
                                 font=("Arial", 9))
            desc_label.pack(side="left", padx=10)
        
        # Info label
        info_label = tk.Label(
            recognition_frame, 
            text="ℹ️ Unified system is automatically selected for best performance",
            bg='#2b2b2b', fg='yellow', font=("Arial", 9, "italic")
        )
        info_label.pack(pady=5)
    
    def create_debugging_tools(self):
        """Create debugging tools section."""
        debug_frame = tk.LabelFrame(self.parent, text="Debugging Tools", 
                                   bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        debug_frame.pack(fill="x", padx=5, pady=5)
        
        # Debug buttons
        debug_buttons = [
            ("🔍 Visual Debug", self.run_visual_debug, "Step-by-step recognition analysis"),
            ("🎯 Test Recognition", self.test_recognition, "Test current recognition system"),
            ("📊 Recognition Stats", self.show_recognition_stats, "Show detailed statistics"),
            ("🖼️ Save Debug Images", self.save_debug_images, "Save current analysis images"),
            ("🔄 Reset Recognition", self.reset_recognition, "Reset recognition system")
        ]
        
        for text, command, tooltip in debug_buttons:
            btn = tk.Button(debug_frame, text=text, command=command,
                           bg='#FF9800', fg='white', font=("Arial", 9, "bold"))
            btn.pack(side="left", padx=2, pady=5)
            # TODO: Add tooltip functionality
    
    def create_testing_tools(self):
        """Create testing tools section."""
        test_frame = tk.LabelFrame(self.parent, text="Testing Tools", 
                                  bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        test_frame.pack(fill="x", padx=5, pady=5)
        
        # Test buttons
        test_buttons = [
            ("🧪 Template Test", self.test_templates, "Test all card templates"),
            ("📈 Benchmark Systems", self.benchmark_systems, "Compare recognition systems"),
            ("🎲 Generate Test Cards", self.generate_test_cards, "Create test card images"),
            ("📋 Export Test Results", self.export_test_results, "Export test data")
        ]
        
        for text, command, tooltip in test_buttons:
            btn = tk.Button(test_frame, text=text, command=command,
                           bg='#9C27B0', fg='white', font=("Arial", 9, "bold"))
            btn.pack(side="left", padx=2, pady=5)
    
    def create_configuration_management(self):
        """Create configuration management section."""
        config_frame = tk.LabelFrame(self.parent, text="Configuration", 
                                    bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        config_frame.pack(fill="x", padx=5, pady=5)
        
        # Configuration controls
        config_row1 = tk.Frame(config_frame, bg='#2b2b2b')
        config_row1.pack(fill="x", padx=5, pady=2)
        
        tk.Button(config_row1, text="💾 Save Config", command=self.save_configuration,
                 bg='#4CAF50', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        tk.Button(config_row1, text="📁 Load Config", command=self.load_configuration,
                 bg='#2196F3', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        tk.Button(config_row1, text="🔄 Reset to Defaults", command=self.reset_configuration,
                 bg='#f44336', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        # Advanced settings
        config_row2 = tk.Frame(config_frame, bg='#2b2b2b')
        config_row2.pack(fill="x", padx=5, pady=2)
        
        tk.Label(config_row2, text="Confidence Threshold:", bg='#2b2b2b', fg='white',
                font=("Arial", 9)).pack(side="left")
        
        self.confidence_var = tk.DoubleVar(value=0.7)
        confidence_scale = tk.Scale(config_row2, from_=0.3, to=0.95, resolution=0.05,
                                   variable=self.confidence_var, orient=tk.HORIZONTAL,
                                   bg='#2b2b2b', fg='white', length=150)
        confidence_scale.pack(side="left", padx=5)
        
        tk.Button(config_row2, text="Apply", command=self.apply_confidence_threshold,
                 bg='#FF9800', fg='white', font=("Arial", 8, "bold")).pack(side="left", padx=2)
    
    def on_recognition_change(self):
        """Handle recognition system change."""
        selected = self.recognition_var.get()
        self.main_window.log_message(f"Recognition system selected: {selected}")
    
    def apply_recognition_system(self):
        """Apply the selected recognition system."""
        try:
            selected = self.recognition_var.get()
            self.main_window.log_message(f"Applying recognition system: {selected}")
            
            # Stop bot if running
            was_running = self.main_window.running
            if was_running:
                self.main_window.stop_bot()
            
            # Reinitialize bot with new recognition system
            from poker_bot import PokerStarsBot
            
            if selected == "enhanced":
                # Import and use enhanced recognition
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from enhanced_card_recognition import EnhancedCardRecognizer
                self.main_window.bot = PokerStarsBot(recognition_type='enhanced')
                
            elif selected == "comprehensive":
                # Import and use comprehensive recognition
                from comprehensive_card_recognition import ComprehensiveCardRecognizer
                self.main_window.bot = PokerStarsBot(recognition_type='comprehensive')
                
            elif selected == "direct":
                # Import and use direct recognition
                from direct_card_recognition import DirectCardRecognizer
                self.main_window.bot = PokerStarsBot(recognition_type='direct')
                
            else:
                # Use improved or standard
                self.main_window.bot = PokerStarsBot(recognition_type=selected)
            
            # Refresh regions
            self.main_window.refresh_regions()
            
            # Restart bot if it was running
            if was_running:
                self.main_window.start_bot()
            
            self.main_window.log_message(f"✅ Successfully applied {selected} recognition system")
            messagebox.showinfo("Success", f"Applied {selected} recognition system successfully!")
            
        except Exception as e:
            self.main_window.log_message(f"❌ Error applying recognition system: {e}")
            messagebox.showerror("Error", f"Failed to apply recognition system: {e}")
    
    def run_visual_debug(self):
        """Run visual debugging tool."""
        try:
            self.main_window.log_message("Starting visual debug analysis...")
            
            # Import debug tool
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from debug_card_recognition import CardRecognitionDebugger
            
            # Run in separate thread to avoid blocking UI
            def debug_thread():
                try:
                    debugger = CardRecognitionDebugger()
                    debugger.debug_live_capture()
                    self.main_window.log_message("✅ Visual debug completed - check debug_images folder")
                except Exception as e:
                    self.main_window.log_message(f"❌ Visual debug error: {e}")
            
            threading.Thread(target=debug_thread, daemon=True).start()
            
        except Exception as e:
            self.main_window.log_message(f"❌ Error starting visual debug: {e}")
    
    def test_recognition(self):
        """Test current recognition system."""
        try:
            if not self.main_window.bot:
                messagebox.showerror("Error", "Bot not initialized")
                return
            
            # Capture current screenshot
            if self.main_window.capture_mode == "obs":
                screenshot = self.main_window.obs_capture.capture_single_frame()
            else:
                screenshot = self.main_window.window_capture.capture_current_window()
            
            if screenshot is None:
                messagebox.showerror("Error", "Failed to capture screenshot")
                return
            
            self.main_window.log_message("Testing recognition on current screenshot...")
            
            # Run analysis
            analysis = self.main_window.bot.analyze_game_state(screenshot, debug=True)
            
            # Show results
            result_text = "Recognition Test Results:\n\n"
            
            if 'hole_cards' in analysis and analysis['hole_cards']:
                hole_cards = analysis['hole_cards']
                result_text += f"Hole Cards: {hole_cards}\n"
                result_text += f"Valid: {hole_cards.is_valid()}\n"
                if hasattr(hole_cards, 'detection_confidence'):
                    result_text += f"Confidence: {hole_cards.detection_confidence:.3f}\n\n"
            
            if 'community_cards' in analysis and analysis['community_cards']:
                community_cards = analysis['community_cards']
                result_text += f"Community Cards: {community_cards}\n"
                result_text += f"Count: {community_cards.count}/5\n"
                if hasattr(community_cards, 'detection_confidence'):
                    result_text += f"Confidence: {community_cards.detection_confidence:.3f}\n\n"
            
            if 'table_info' in analysis and analysis['table_info']:
                table_info = analysis['table_info']
                result_text += f"Players Detected: {len(table_info.players)}\n"
                result_text += f"Pot Size: {table_info.pot_size:.1f}BB\n"
            
            messagebox.showinfo("Recognition Test Results", result_text)
            self.main_window.log_message("✅ Recognition test completed")
            
        except Exception as e:
            self.main_window.log_message(f"❌ Recognition test error: {e}")
            messagebox.showerror("Error", f"Recognition test failed: {e}")
    
    def show_recognition_stats(self):
        """Show detailed recognition statistics."""
        try:
            if not self.main_window.bot:
                messagebox.showerror("Error", "Bot not initialized")
                return
            
            stats_text = "Recognition System Statistics:\n\n"
            
            # Get card recognizer stats
            if hasattr(self.main_window.bot, 'card_recognizer'):
                if hasattr(self.main_window.bot.card_recognizer, 'get_recognition_stats'):
                    card_stats = self.main_window.bot.card_recognizer.get_recognition_stats()
                    stats_text += "Card Recognizer:\n"
                    for key, value in card_stats.items():
                        stats_text += f"  {key}: {value}\n"
                    stats_text += "\n"
            
            # Get community detector stats
            if hasattr(self.main_window.bot, 'community_detector'):
                if hasattr(self.main_window.bot.community_detector, 'get_detection_stats'):
                    community_stats = self.main_window.bot.community_detector.get_detection_stats()
                    stats_text += "Community Detector:\n"
                    for key, value in community_stats.items():
                        stats_text += f"  {key}: {value}\n"
                    stats_text += "\n"
            
            # Add capture statistics
            stats_text += f"Capture Statistics:\n"
            stats_text += f"  Total Captures: {self.main_window.capture_count}\n"
            stats_text += f"  Successful: {self.main_window.success_count}\n"
            if self.main_window.capture_count > 0:
                success_rate = (self.main_window.success_count / self.main_window.capture_count) * 100
                stats_text += f"  Success Rate: {success_rate:.1f}%\n"
            
            messagebox.showinfo("Recognition Statistics", stats_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get statistics: {e}")
    
    def save_debug_images(self):
        """Save current debug images."""
        try:
            import shutil
            import time
            
            timestamp = int(time.time())
            debug_dir = f"debug_export_{timestamp}"
            os.makedirs(debug_dir, exist_ok=True)
            
            # Copy debug directories
            dirs_to_copy = ['debug_cards', 'debug_community', 'debug_images', 'screenshots']
            
            for dir_name in dirs_to_copy:
                if os.path.exists(dir_name):
                    shutil.copytree(dir_name, os.path.join(debug_dir, dir_name))
            
            self.main_window.log_message(f"✅ Debug images saved to {debug_dir}")
            messagebox.showinfo("Success", f"Debug images saved to {debug_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save debug images: {e}")
    
    def reset_recognition(self):
        """Reset the recognition system."""
        try:
            if messagebox.askyesno("Confirm Reset", "Reset recognition system to defaults?"):
                # Reinitialize bot
                from poker_bot import PokerStarsBot
                self.main_window.bot = PokerStarsBot(recognition_type='improved')
                self.main_window.refresh_regions()
                self.main_window.log_message("✅ Recognition system reset")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset recognition: {e}")
    
    def test_templates(self):
        """Test all card templates."""
        try:
            self.main_window.log_message("Testing all card templates...")
            
            # Import test module
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from test_enhanced_recognition import test_directory
            
            # Run template test in separate thread
            def test_thread():
                try:
                    test_directory("card_templates", method="enhanced", debug=True)
                    self.main_window.log_message("✅ Template test completed")
                except Exception as e:
                    self.main_window.log_message(f"❌ Template test error: {e}")
            
            threading.Thread(target=test_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Template test failed: {e}")
    
    def benchmark_systems(self):
        """Benchmark all recognition systems."""
        try:
            self.main_window.log_message("Starting recognition system benchmark...")
            
            # Import benchmark module
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from compare_recognition_systems import main as benchmark_main
            
            # Run benchmark in separate thread
            def benchmark_thread():
                try:
                    benchmark_main()
                    self.main_window.log_message("✅ Benchmark completed - check results")
                except Exception as e:
                    self.main_window.log_message(f"❌ Benchmark error: {e}")
            
            threading.Thread(target=benchmark_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Benchmark failed: {e}")
    
    def generate_test_cards(self):
        """Generate test card images."""
        try:
            # Import test card generator
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from test_card_color import create_test_card
            
            # Generate test cards
            os.makedirs("test_cards", exist_ok=True)
            
            suits = ["red", "black"]
            ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
            
            for suit in suits:
                for rank in ranks:
                    card_img, card_name = create_test_card(suit, rank)
                    filename = f"test_cards/{card_name}.png"
                    cv2.imwrite(filename, card_img)
            
            self.main_window.log_message("✅ Test cards generated in test_cards folder")
            messagebox.showinfo("Success", "Test cards generated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate test cards: {e}")
    
    def export_test_results(self):
        """Export test results."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Test Results",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write("PokerStars Bot Test Results\n")
                    f.write("=" * 30 + "\n\n")
                    f.write(f"Recognition System: {self.recognition_var.get()}\n")
                    f.write(f"Capture Count: {self.main_window.capture_count}\n")
                    f.write(f"Success Count: {self.main_window.success_count}\n")
                    if self.main_window.capture_count > 0:
                        success_rate = (self.main_window.success_count / self.main_window.capture_count) * 100
                        f.write(f"Success Rate: {success_rate:.1f}%\n")
                
                messagebox.showinfo("Success", f"Results exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def save_configuration(self):
        """Save current configuration."""
        try:
            config = {
                'recognition_system': self.recognition_var.get(),
                'confidence_threshold': self.confidence_var.get(),
                'capture_mode': self.main_window.capture_mode,
                'show_regions': getattr(self.main_window, 'show_regions', False)
            }
            
            filename = filedialog.asksaveasfilename(
                title="Save Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                import json
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                
                messagebox.showinfo("Success", f"Configuration saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")
    
    def load_configuration(self):
        """Load configuration from file."""
        try:
            filename = filedialog.askopenfilename(
                title="Load Configuration",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                import json
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                # Apply configuration
                if 'recognition_system' in config:
                    self.recognition_var.set(config['recognition_system'])
                if 'confidence_threshold' in config:
                    self.confidence_var.set(config['confidence_threshold'])
                
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Load failed: {e}")
    
    def reset_configuration(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?"):
            self.recognition_var.set("improved")
            self.confidence_var.set(0.7)
            messagebox.showinfo("Success", "Configuration reset to defaults")
    
    def apply_confidence_threshold(self):
        """Apply confidence threshold to recognition system."""
        try:
            threshold = self.confidence_var.get()
            
            if hasattr(self.main_window.bot, 'card_recognizer'):
                if hasattr(self.main_window.bot.card_recognizer, 'template_match_threshold'):
                    self.main_window.bot.card_recognizer.template_match_threshold = threshold
                    self.main_window.log_message(f"✅ Applied confidence threshold: {threshold}")
                    messagebox.showinfo("Success", f"Confidence threshold set to {threshold}")
                else:
                    messagebox.showwarning("Warning", "Current recognition system doesn't support threshold adjustment")
            else:
                messagebox.showerror("Error", "Bot not initialized")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply threshold: {e}")