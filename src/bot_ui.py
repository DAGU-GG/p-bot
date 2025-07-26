"""
PokerStars Bot - GUI Application
Complete user interface for testing and monitoring the poker bot functionality.
Includes real-time card recognition, game state monitoring, and comprehensive testing tools.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import json
from datetime import datetime
import logging

# Import bot modules
from poker_bot import PokerStarsBot
from card_recognizer import CardRecognizer, HoleCards
from community_card_detector import CommunityCardDetector, CommunityCards
from image_processor import ImageProcessor, GameState
from window_capture import PokerStarsWindowCapture

class PokerBotUI:
    """Main UI class for the PokerStars bot application."""
    
    def __init__(self):
        """Initialize the bot UI application."""
        self.root = tk.Tk()
        self.root.title("PokerStars Bot - Testing Interface")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        # Bot components
        self.bot = None
        self.window_capture = PokerStarsWindowCapture()
        self.running = False
        self.capture_thread = None
        
        # UI variables
        self.status_var = tk.StringVar(value="Bot Stopped")
        self.window_var = tk.StringVar(value="No window selected")
        self.captures_var = tk.StringVar(value="Captures: 0")
        self.success_var = tk.StringVar(value="Success: 0%")
        
        # Data storage
        self.last_screenshot = None
        self.last_analysis = None
        self.capture_history = []
        
        # Setup UI
        self.setup_ui()
        self.setup_logging()
        
        # Initialize bot
        self.initialize_bot()
    
    def setup_ui(self):
        """Setup the complete user interface."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_control_tab()
        self.create_monitoring_tab()
        self.create_card_recognition_tab()
        self.create_debug_tab()
        self.create_settings_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_control_tab(self):
        """Create the main control tab."""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Control Panel")
        
        # Window selection section
        window_section = ttk.LabelFrame(control_frame, text="Window Selection", padding=10)
        window_section.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(window_section, text="Selected Window:").pack(anchor=tk.W)
        ttk.Label(window_section, textvariable=self.window_var, foreground="blue").pack(anchor=tk.W)
        
        window_buttons = ttk.Frame(window_section)
        window_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(window_buttons, text="Find PokerStars Window", 
                  command=self.find_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(window_buttons, text="Test Capture", 
                  command=self.test_capture).pack(side=tk.LEFT, padx=5)
        ttk.Button(window_buttons, text="Refresh Windows", 
                  command=self.refresh_windows).pack(side=tk.LEFT, padx=5)
        ttk.Button(window_buttons, text="Calibrate Table", 
                  command=self.calibrate_table).pack(side=tk.LEFT, padx=5)
        
        # Window selection dropdown
        ttk.Label(window_section, text="Available Windows:").pack(anchor=tk.W, pady=(10,0))
        self.window_listbox = tk.Listbox(window_section, height=4)
        self.window_listbox.pack(fill=tk.X, pady=5)
        self.window_listbox.bind('<Double-Button-1>', self.on_window_select)
        
        # Bot control section
        control_section = ttk.LabelFrame(control_frame, text="Bot Control", padding=10)
        control_section.pack(fill=tk.X, padx=10, pady=5)
        
        control_buttons = ttk.Frame(control_section)
        control_buttons.pack(fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(control_buttons, text="Start Bot", 
                                      command=self.start_bot, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_buttons, text="Stop Bot", 
                                     command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_buttons, text="Single Capture", 
                  command=self.single_capture).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons, text="Clear History", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        # Settings section
        settings_section = ttk.LabelFrame(control_frame, text="Capture Settings", padding=10)
        settings_section.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(settings_section, text="Capture Interval (seconds):").pack(anchor=tk.W)
        self.interval_var = tk.DoubleVar(value=0.5)
        interval_scale = ttk.Scale(settings_section, from_=0.1, to=5.0, 
                                  variable=self.interval_var, orient=tk.HORIZONTAL)
        interval_scale.pack(fill=tk.X, pady=5)
        
        self.save_debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_section, text="Save Debug Images", 
                       variable=self.save_debug_var).pack(anchor=tk.W)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_section, text="Auto-scroll Log", 
                       variable=self.auto_scroll_var).pack(anchor=tk.W)
    
    def create_monitoring_tab(self):
        """Create the real-time monitoring tab."""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="Live Monitoring")
        
        # Create paned window for layout
        paned = ttk.PanedWindow(monitor_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Screenshot and analysis
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=2)
        
        # Screenshot display
        screenshot_frame = ttk.LabelFrame(left_panel, text="Live Screenshot", padding=5)
        screenshot_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create canvas for better image display
        self.screenshot_canvas = tk.Canvas(screenshot_frame, bg='black')
        self.screenshot_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.screenshot_label = ttk.Label(screenshot_frame, text="No screenshot available")
        self.screenshot_label.pack(expand=True)
        
        # Right panel - Game state and cards
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=1)
        
        # Game state display
        gamestate_frame = ttk.LabelFrame(right_panel, text="Game State", padding=5)
        gamestate_frame.pack(fill=tk.X, pady=5)
        
        self.gamestate_text = scrolledtext.ScrolledText(gamestate_frame, height=8, width=40)
        self.gamestate_text.pack(fill=tk.BOTH, expand=True)
        
        # Hole cards display
        holecards_frame = ttk.LabelFrame(right_panel, text="Hole Cards", padding=5)
        holecards_frame.pack(fill=tk.X, pady=5)
        
        self.holecards_text = scrolledtext.ScrolledText(holecards_frame, height=4, width=40)
        self.holecards_text.pack(fill=tk.BOTH, expand=True)
        
        # Community cards display
        community_frame = ttk.LabelFrame(right_panel, text="Community Cards", padding=5)
        community_frame.pack(fill=tk.X, pady=5)
        
        self.community_text = scrolledtext.ScrolledText(community_frame, height=4, width=40)
        self.community_text.pack(fill=tk.BOTH, expand=True)
        
        # Statistics display
        stats_frame = ttk.LabelFrame(right_panel, text="Statistics", padding=5)
        stats_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(stats_frame, textvariable=self.captures_var).pack(anchor=tk.W)
        ttk.Label(stats_frame, textvariable=self.success_var).pack(anchor=tk.W)
    
    def create_card_recognition_tab(self):
        """Create the card recognition testing tab."""
        card_frame = ttk.Frame(self.notebook)
        self.notebook.add(card_frame, text="Card Recognition")
        
        # Template management section
        template_section = ttk.LabelFrame(card_frame, text="Template Management", padding=10)
        template_section.pack(fill=tk.X, padx=10, pady=5)
        
        template_buttons = ttk.Frame(template_section)
        template_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(template_buttons, text="Load Templates", 
                  command=self.load_templates).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_buttons, text="Test Recognition", 
                  command=self.test_recognition).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_buttons, text="Save Card Template", 
                  command=self.save_card_template).pack(side=tk.LEFT, padx=5)
        
        self.template_status = ttk.Label(template_section, text="Templates: Not loaded")
        self.template_status.pack(anchor=tk.W, pady=5)
        
        # Recognition results section
        results_section = ttk.LabelFrame(card_frame, text="Recognition Results", padding=10)
        results_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.recognition_text = scrolledtext.ScrolledText(results_section, height=20)
        self.recognition_text.pack(fill=tk.BOTH, expand=True)
        
        # Recognition controls
        controls_frame = ttk.Frame(results_section)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text="Clear Results", 
                  command=lambda: self.recognition_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Export Results", 
                  command=self.export_recognition_results).pack(side=tk.LEFT, padx=5)
    
    def create_debug_tab(self):
        """Create the debug and logging tab."""
        debug_frame = ttk.Frame(self.notebook)
        self.notebook.add(debug_frame, text="Debug & Logs")
        
        # Log display
        log_section = ttk.LabelFrame(debug_frame, text="Bot Logs", padding=5)
        log_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_section, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_section)
        log_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(log_controls, text="Clear Logs", 
                  command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Save Logs", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Open Debug Folder", 
                  command=self.open_debug_folder).pack(side=tk.LEFT, padx=5)
        
        # Debug image viewer
        debug_images_section = ttk.LabelFrame(debug_frame, text="Debug Images", padding=5)
        debug_images_section.pack(fill=tk.X, padx=10, pady=5)
        
        debug_buttons = ttk.Frame(debug_images_section)
        debug_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(debug_buttons, text="View Latest Screenshot", 
                  command=self.view_latest_screenshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(debug_buttons, text="View Card Debug", 
                  command=self.view_card_debug).pack(side=tk.LEFT, padx=5)
        ttk.Button(debug_buttons, text="View Community Debug", 
                  command=self.view_community_debug).pack(side=tk.LEFT, padx=5)
    
    def create_settings_tab(self):
        """Create the settings and configuration tab."""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Recognition settings
        recognition_section = ttk.LabelFrame(settings_frame, text="Recognition Settings", padding=10)
        recognition_section.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(recognition_section, text="Template Match Threshold:").pack(anchor=tk.W)
        self.template_threshold_var = tk.DoubleVar(value=0.7)
        ttk.Scale(recognition_section, from_=0.5, to=0.95, 
                 variable=self.template_threshold_var, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)
        
        ttk.Label(recognition_section, text="Card Presence Threshold:").pack(anchor=tk.W)
        self.presence_threshold_var = tk.IntVar(value=50)
        ttk.Scale(recognition_section, from_=20, to=200, 
                 variable=self.presence_threshold_var, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)
        
        # File paths section
        paths_section = ttk.LabelFrame(settings_frame, text="File Paths", padding=10)
        paths_section.pack(fill=tk.X, padx=10, pady=5)
        
        self.template_path_var = tk.StringVar(value="card_templates/")
        ttk.Label(paths_section, text="Template Directory:").pack(anchor=tk.W)
        path_frame = ttk.Frame(paths_section)
        path_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(path_frame, textvariable=self.template_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse", command=self.browse_template_path).pack(side=tk.RIGHT, padx=5)
        
        # Export/Import settings
        export_section = ttk.LabelFrame(settings_frame, text="Configuration", padding=10)
        export_section.pack(fill=tk.X, padx=10, pady=5)
        
        config_buttons = ttk.Frame(export_section)
        config_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(config_buttons, text="Save Configuration", 
                  command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_buttons, text="Load Configuration", 
                  command=self.load_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_buttons, text="Reset to Defaults", 
                  command=self.reset_configuration).pack(side=tk.LEFT, padx=5)
    
    def create_status_bar(self):
        """Create the status bar at the bottom."""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, textvariable=self.status_var, foreground="green").pack(side=tk.LEFT)
        
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.time_label = ttk.Label(status_frame, text="")
        self.time_label.pack(side=tk.RIGHT, padx=5)
        
        # Update time every second
        self.update_time()
    
    def setup_logging(self):
        """Setup logging to display in the UI."""
        class UILogHandler(logging.Handler):
            def __init__(self, text_widget, auto_scroll_var):
                super().__init__()
                self.text_widget = text_widget
                self.auto_scroll_var = auto_scroll_var
            
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + '\n')
                if self.auto_scroll_var.get():
                    self.text_widget.see(tk.END)
        
        # Add UI handler to root logger
        ui_handler = UILogHandler(self.log_text, self.auto_scroll_var)
        ui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(ui_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def initialize_bot(self):
        """Initialize the poker bot components."""
        try:
            self.bot = PokerStarsBot()
            self.log_message("Bot components initialized successfully")
            self.update_template_status()
        except Exception as e:
            self.log_message(f"Error initializing bot: {e}", "ERROR")
    
    def find_window(self):
        """Find and select PokerStars window."""
        try:
            # Use enhanced window detection
            selected_window = self.window_capture.select_best_window()
            
            if selected_window:
                self.window_var.set(f"{selected_window['title']} ({selected_window['width']}x{selected_window['height']})")
                self.log_message("PokerStars window found and selected")
                
                # Update the bot's window capture if bot exists
                if self.bot:
                    self.bot.window_capture = self.window_capture
                
                # Refresh the window list
                self.refresh_windows()
                
                messagebox.showinfo("Success", "PokerStars window found and configured!")
            else:
                # Show available windows for debugging
                all_windows = self.window_capture.find_pokerstars_windows()
                if all_windows:
                    self.refresh_windows()
                    messagebox.showwarning("Multiple Windows", 
                                         f"Found {len(all_windows)} potential windows. "
                                         "Please select one from the list below.")
                else:
                    messagebox.showerror("Error", 
                                       "No PokerStars windows found.\n\n"
                                       "Make sure:\n"
                                       "1. PokerStars is running\n"
                                       "2. A poker table is open (not just lobby)\n"
                                       "3. The table window is visible")
        except Exception as e:
            self.log_message(f"Error finding window: {e}", "ERROR")
            messagebox.showerror("Error", f"Error finding window: {e}")
    
    def refresh_windows(self):
        """Refresh the list of available PokerStars windows."""
        try:
            self.window_listbox.delete(0, tk.END)
            windows = self.window_capture.find_pokerstars_windows()
            
            for i, window in enumerate(windows):
                display_text = f"{window['title']} ({window['width']}x{window['height']}) [Score: {window.get('score', 0)}]"
                self.window_listbox.insert(tk.END, display_text)
            
            if windows:
                self.log_message(f"Found {len(windows)} PokerStars windows")
            else:
                self.log_message("No PokerStars windows found")
                
        except Exception as e:
            self.log_message(f"Error refreshing windows: {e}", "ERROR")
    
    def on_window_select(self, event):
        """Handle window selection from listbox."""
        try:
            selection = self.window_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            windows = self.window_capture.find_pokerstars_windows()
            
            if index < len(windows):
                selected_window = windows[index]
                self.window_capture.selected_window = selected_window
                
                self.window_var.set(f"{selected_window['title']} ({selected_window['width']}x{selected_window['height']})")
                self.log_message(f"Selected window: {selected_window['title']}")
                
                # Update bot's window capture
                if self.bot:
                    self.bot.window_capture = self.window_capture
                
        except Exception as e:
            self.log_message(f"Error selecting window: {e}", "ERROR")
    
    def test_capture(self):
        """Test screen capture functionality."""
        try:
            if not self.window_capture.selected_window:
                messagebox.showerror("Error", "Please find a PokerStars window first")
                return
            
            screenshot = self.window_capture.capture_current_window()
            if screenshot is not None:
                # Validate the capture
                is_valid = self.window_capture.validate_capture(screenshot)
                validation_msg = "✓ Valid poker table" if is_valid else "⚠ May not be poker table"
                
                self.display_screenshot(screenshot)
                self.log_message(f"Screen capture test successful - {validation_msg}")
                
                # Show capture info
                window_info = self.window_capture.get_window_info()
                info_msg = (f"Screen capture working correctly!\n\n"
                           f"Capture method: {window_info.get('capture_method', 'auto')}\n"
                           f"Validation: {validation_msg}")
                messagebox.showinfo("Success", info_msg)
            else:
                messagebox.showerror("Error", "Failed to capture screen")
        except Exception as e:
            self.log_message(f"Error testing capture: {e}", "ERROR")
            messagebox.showerror("Error", f"Error testing capture: {e}")
    
    def calibrate_table(self):
        """Calibrate table regions."""
        try:
            if not self.window_capture.selected_window:
                messagebox.showerror("Error", "Please find a PokerStars window first")
                return
            
            screenshot = self.window_capture.capture_current_window()
            if screenshot is not None:
                # Initialize image processor if needed
                if not hasattr(self, 'image_processor'):
                    from image_processor import ImageProcessor
                    self.image_processor = ImageProcessor()
                
                success = self.image_processor.calibrate_table_regions(screenshot)
                if success:
                    self.log_message("Table calibration successful")
                    messagebox.showinfo("Success", "Table regions calibrated successfully!")
                else:
                    messagebox.showerror("Error", "Table calibration failed")
            else:
                messagebox.showerror("Error", "Failed to capture screen for calibration")
        except Exception as e:
            self.log_message(f"Error calibrating table: {e}", "ERROR")
            messagebox.showerror("Error", f"Error calibrating table: {e}")
    
    def start_bot(self):
        """Start the bot monitoring."""
        try:
            if not self.window_capture.selected_window:
                messagebox.showerror("Error", "Please find a PokerStars window first")
                return
            
            # Initialize bot if needed
            if not self.bot:
                self.bot = PokerStarsBot()
            
            # Set the window capture
            self.bot.window_capture = self.window_capture
            
            self.running = True
            self.status_var.set("Bot Running")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
            self.capture_thread.start()
            
            self.log_message("Bot started successfully")
        except Exception as e:
            self.log_message(f"Error starting bot: {e}", "ERROR")
            messagebox.showerror("Error", f"Error starting bot: {e}")
    
    def stop_bot(self):
        """Stop the bot monitoring."""
        self.running = False
        self.status_var.set("Bot Stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("Bot stopped")
    
    def capture_loop(self):
        """Main capture loop running in separate thread."""
        while self.running:
            try:
                # Capture and analyze
                screenshot = self.window_capture.capture_current_window()
                if screenshot is not None:
                    analysis = self.bot.analyze_game_state(screenshot)
                    
                    # Update UI in main thread
                    self.root.after(0, self.update_monitoring_display, screenshot, analysis)
                    
                    # Store for history
                    self.capture_history.append({
                        'timestamp': time.time(),
                        'analysis': analysis
                    })
                    
                    # Limit history size
                    if len(self.capture_history) > 100:
                        self.capture_history.pop(0)
                
                time.sleep(self.interval_var.get())
                
            except Exception as e:
                self.log_message(f"Error in capture loop: {e}", "ERROR")
                time.sleep(1)
    
    def single_capture(self):
        """Perform a single capture and analysis."""
        try:
            if not self.window_capture.selected_window:
                messagebox.showerror("Error", "Please find a PokerStars window first")
                return
            
            # Initialize bot if needed
            if not self.bot:
                self.bot = PokerStarsBot()
                self.bot.window_capture = self.window_capture
            
            screenshot = self.window_capture.capture_current_window()
            if screenshot is not None:
                analysis = self.bot.analyze_game_state(screenshot)
                self.update_monitoring_display(screenshot, analysis)
                self.log_message("Single capture completed")
            else:
                messagebox.showerror("Error", "Failed to capture screen")
        except Exception as e:
            self.log_message(f"Error in single capture: {e}", "ERROR")
            messagebox.showerror("Error", f"Error in single capture: {e}")
    
    def update_monitoring_display(self, screenshot, analysis):
        """Update the monitoring display with new data."""
        try:
            # Update screenshot display
            self.display_screenshot(screenshot)
            
            # Update game state
            if 'game_state' in analysis:
                game_state = analysis['game_state']
                gamestate_info = f"""Timestamp: {datetime.fromtimestamp(analysis['timestamp']).strftime('%H:%M:%S')}
Active Players: {game_state.active_players}
Pot Amount: {game_state.pot_amount or 'Unknown'}
Current Bet: {game_state.current_bet or 'Unknown'}
Dealer Position: {game_state.dealer_button_position or 'Unknown'}
Table Detected: {game_state.table_detected}
"""
                self.gamestate_text.delete(1.0, tk.END)
                self.gamestate_text.insert(1.0, gamestate_info)
            
            # Update hole cards
            if 'hole_cards' in analysis:
                hole_cards = analysis['hole_cards']
                if hole_cards.is_valid():
                    holecards_info = f"""Card 1: {hole_cards.card1}
Card 2: {hole_cards.card2}
Confidence: {hole_cards.detection_confidence:.3f}
Valid: {hole_cards.is_valid()}
"""
                else:
                    holecards_info = "No hole cards detected"
                
                self.holecards_text.delete(1.0, tk.END)
                self.holecards_text.insert(1.0, holecards_info)
            
            # Update community cards
            if 'community_cards' in analysis:
                community_cards = analysis['community_cards']
                if community_cards.count > 0:
                    visible_cards = community_cards.get_visible_cards()
                    cards_str = "\n".join([f"Card {i+1}: {card}" for i, card in enumerate(visible_cards)])
                    community_info = f"""Phase: {community_cards.phase}
Count: {community_cards.count}/5
Confidence: {community_cards.detection_confidence:.3f}
Valid Phase: {community_cards.is_valid_phase()}

{cards_str}
"""
                else:
                    community_info = "No community cards (Pre-flop)"
                
                self.community_text.delete(1.0, tk.END)
                self.community_text.insert(1.0, community_info)
            
            # Update table analysis
            if 'table_info' in analysis:
                table_info = analysis['table_info']
                if len(table_info.players) > 0:
                    table_analysis = self.bot.table_analyzer.format_table_summary(table_info)
                else:
                    table_analysis = "No players detected"
                
                self.table_text.delete(1.0, tk.END)
                self.table_text.insert(1.0, table_analysis)
            
            # Update statistics
            self.captures_var.set(f"Captures: {self.bot.captures_count}")
            success_rate = (self.bot.successful_recognitions / max(self.bot.captures_count, 1)) * 100
            self.success_var.set(f"Success: {success_rate:.1f}%")
            
        except Exception as e:
            self.log_message(f"Error updating display: {e}", "ERROR")
    
    def display_screenshot(self, screenshot):
        """Display screenshot in the UI."""
        try:
            # Resize screenshot to larger display
            height, width = screenshot.shape[:2]
            max_width, max_height = 800, 600  # Larger display
            
            if width > max_width or height > max_height:
                scale = min(max_width/width, max_height/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                screenshot = cv2.resize(screenshot, (new_width, new_height))
            
            # Convert to PIL Image
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(screenshot_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update canvas for better display
            self.screenshot_canvas.delete("all")
            canvas_width = self.screenshot_canvas.winfo_width()
            canvas_height = self.screenshot_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Center the image on canvas
                x = (canvas_width - screenshot.shape[1]) // 2
                y = (canvas_height - screenshot.shape[0]) // 2
                self.screenshot_canvas.create_image(max(0, x), max(0, y), anchor=tk.NW, image=photo)
            
            # Keep reference to prevent garbage collection
            self.screenshot_canvas.image = photo
            
            self.last_screenshot = screenshot
            
        except Exception as e:
            self.log_message(f"Error displaying screenshot: {e}", "ERROR")
    
    def load_templates(self):
        """Load card templates."""
        try:
            if self.bot:
                self.bot.card_recognizer._load_existing_templates()
                self.update_template_status()
                self.log_message("Card templates reloaded")
                messagebox.showinfo("Success", "Card templates loaded successfully!")
        except Exception as e:
            self.log_message(f"Error loading templates: {e}", "ERROR")
            messagebox.showerror("Error", f"Error loading templates: {e}")
    
    def update_template_status(self):
        """Update template status display."""
        try:
            if self.bot:
                stats = self.bot.card_recognizer.get_recognition_stats()
                template_count = stats['templates_loaded']
                self.template_status.config(text=f"Templates: {template_count}/52 loaded")
        except Exception as e:
            self.log_message(f"Error updating template status: {e}", "ERROR")
    
    def test_recognition(self):
        """Test card recognition on current screenshot."""
        try:
            if self.last_screenshot is None:
                messagebox.showerror("Error", "No screenshot available. Capture a screenshot first.")
                return
            
            # Initialize components if needed
            if not self.bot:
                self.bot = PokerStarsBot()
            
            # Test hole card recognition
            hole_cards = self.bot.card_recognizer.recognize_hero_hole_cards(self.last_screenshot)
            
            # Test community card recognition
            community_cards = self.bot.community_detector.detect_community_cards(self.last_screenshot)
            
            # Test table analysis
            table_info = self.bot.table_analyzer.analyze_complete_table(self.last_screenshot)
            
            # Display results
            results = f"""Recognition Test Results:
{datetime.now().strftime('%H:%M:%S')}

Hole Cards:
{hole_cards if hole_cards.is_valid() else 'No hole cards detected'}
Confidence: {hole_cards.detection_confidence:.3f}

Community Cards:
{community_cards}
Count: {community_cards.count}/5
Confidence: {community_cards.detection_confidence:.3f}

Table Analysis:
Players Detected: {len(table_info.players)}
Stakes: {table_info.table_stakes}
Hero Seat: {table_info.hero_seat}
Dealer Seat: {table_info.dealer_seat}
Pot Size: {table_info.pot_size:.1f}BB

"""
            
            self.recognition_text.insert(tk.END, results)
            self.recognition_text.see(tk.END)
            
            self.log_message("Recognition test completed")
            
        except Exception as e:
            self.log_message(f"Error testing recognition: {e}", "ERROR")
            messagebox.showerror("Error", f"Error testing recognition: {e}")
    
    def save_card_template(self):
        """Save current card regions as templates."""
        try:
            if self.last_screenshot is None:
                messagebox.showerror("Error", "No screenshot available")
                return
            
            # Extract card regions
            card1_img, card2_img = self.bot.card_recognizer.extract_hero_cards_region(self.last_screenshot)
            
            if card1_img.size > 0:
                timestamp = int(time.time())
                filename1 = f"card_templates/manual_card1_{timestamp}.png"
                cv2.imwrite(filename1, card1_img)
                self.log_message(f"Saved card 1 template: {filename1}")
            
            if card2_img.size > 0:
                timestamp = int(time.time())
                filename2 = f"card_templates/manual_card2_{timestamp}.png"
                cv2.imwrite(filename2, card2_img)
                self.log_message(f"Saved card 2 template: {filename2}")
            
            messagebox.showinfo("Success", "Card templates saved for manual processing")
            
        except Exception as e:
            self.log_message(f"Error saving card template: {e}", "ERROR")
            messagebox.showerror("Error", f"Error saving card template: {e}")
    
    def clear_history(self):
        """Clear capture history."""
        self.capture_history.clear()
        self.log_message("Capture history cleared")
    
    def export_recognition_results(self):
        """Export recognition results to file."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.recognition_text.get(1.0, tk.END))
                
                self.log_message(f"Recognition results exported to: {filename}")
                messagebox.showinfo("Success", f"Results exported to {filename}")
                
        except Exception as e:
            self.log_message(f"Error exporting results: {e}", "ERROR")
            messagebox.showerror("Error", f"Error exporting results: {e}")
    
    def save_logs(self):
        """Save logs to file."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                
                messagebox.showinfo("Success", f"Logs saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving logs: {e}")
    
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
            self.log_message(f"Error opening debug folder: {e}", "ERROR")
            messagebox.showerror("Error", f"Error opening debug folder: {e}")
    
    def view_latest_screenshot(self):
        """View latest screenshot in external viewer."""
        try:
            screenshots_dir = "screenshots"
            if os.path.exists(screenshots_dir):
                files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
                if files:
                    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(screenshots_dir, x)))
                    filepath = os.path.join(screenshots_dir, latest_file)
                    
                    import subprocess
                    import platform
                    
                    if platform.system() == "Windows":
                        subprocess.Popen(["start", filepath], shell=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.Popen(["open", filepath])
                    else:  # Linux
                        subprocess.Popen(["xdg-open", filepath])
                else:
                    messagebox.showinfo("Info", "No screenshots found")
            else:
                messagebox.showinfo("Info", "Screenshots directory not found")
                
        except Exception as e:
            self.log_message(f"Error viewing screenshot: {e}", "ERROR")
            messagebox.showerror("Error", f"Error viewing screenshot: {e}")
    
    def view_card_debug(self):
        """View card debug images."""
        try:
            debug_dir = "debug_cards"
            if os.path.exists(debug_dir):
                files = [f for f in os.listdir(debug_dir) if f.endswith('.png')]
                if files:
                    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(debug_dir, x)))
                    filepath = os.path.join(debug_dir, latest_file)
                    
                    import subprocess
                    import platform
                    
                    if platform.system() == "Windows":
                        subprocess.Popen(["start", filepath], shell=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.Popen(["open", filepath])
                    else:  # Linux
                        subprocess.Popen(["xdg-open", filepath])
                else:
                    messagebox.showinfo("Info", "No card debug images found")
            else:
                messagebox.showinfo("Info", "Card debug directory not found")
                
        except Exception as e:
            self.log_message(f"Error viewing card debug: {e}", "ERROR")
            messagebox.showerror("Error", f"Error viewing card debug: {e}")
    
    def view_community_debug(self):
        """View community card debug images."""
        try:
            debug_dir = "debug_community"
            if os.path.exists(debug_dir):
                files = [f for f in os.listdir(debug_dir) if f.endswith('.png')]
                if files:
                    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(debug_dir, x)))
                    filepath = os.path.join(debug_dir, latest_file)
                    
                    import subprocess
                    import platform
                    
                    if platform.system() == "Windows":
                        subprocess.Popen(["start", filepath], shell=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.Popen(["open", filepath])
                    else:  # Linux
                        subprocess.Popen(["xdg-open", filepath])
                else:
                    messagebox.showinfo("Info", "No community debug images found")
            else:
                messagebox.showinfo("Info", "Community debug directory not found")
                
        except Exception as e:
            self.log_message(f"Error viewing community debug: {e}", "ERROR")
            messagebox.showerror("Error", f"Error viewing community debug: {e}")
    
    def browse_template_path(self):
        """Browse for template directory."""
        directory = filedialog.askdirectory(initialdir=self.template_path_var.get())
        if directory:
            self.template_path_var.set(directory)
    
    def save_configuration(self):
        """Save current configuration to file."""
        try:
            config = {
                'capture_interval': self.interval_var.get(),
                'template_threshold': self.template_threshold_var.get(),
                'presence_threshold': self.presence_threshold_var.get(),
                'template_path': self.template_path_var.get(),
                'save_debug': self.save_debug_var.get(),
                'auto_scroll': self.auto_scroll_var.get()
            }
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                
                messagebox.showinfo("Success", f"Configuration saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")
    
    def load_configuration(self):
        """Load configuration from file."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                # Apply configuration
                self.interval_var.set(config.get('capture_interval', 0.5))
                self.template_threshold_var.set(config.get('template_threshold', 0.7))
                self.presence_threshold_var.set(config.get('presence_threshold', 50))
                self.template_path_var.set(config.get('template_path', 'card_templates/'))
                self.save_debug_var.set(config.get('save_debug', True))
                self.auto_scroll_var.set(config.get('auto_scroll', True))
                
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading configuration: {e}")
    
    def reset_configuration(self):
        """Reset configuration to defaults."""
        self.interval_var.set(0.5)
        self.template_threshold_var.set(0.7)
        self.presence_threshold_var.set(50)
        self.template_path_var.set('card_templates/')
        self.save_debug_var.set(True)
        self.auto_scroll_var.set(True)
        
        messagebox.showinfo("Success", "Configuration reset to defaults")
    
    def update_time(self):
        """Update the time display."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def log_message(self, message, level="INFO"):
        """Log a message to the UI and file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        # Log to file
        logging.getLogger().info(formatted_message)
    
    def on_closing(self):
        """Handle application closing."""
        if self.running:
            self.stop_bot()
        
        # Wait a moment for threads to stop
        time.sleep(0.5)
        
        self.root.destroy()
    
    def run(self):
        """Run the UI application."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main entry point for the UI application."""
    try:
        app = PokerBotUI()
        app.run()
    except Exception as e:
        print(f"Error starting UI application: {e}")
        messagebox.showerror("Fatal Error", f"Error starting application: {e}")

if __name__ == "__main__":
    main()