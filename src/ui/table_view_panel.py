"""
Table View Panel Component
Displays the live poker table screenshot and basic controls.
"""

import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np
from .region_calibrator import RegionCalibrator


class TableViewPanel(tk.Frame):
    """Panel for displaying the live poker table view."""
    
    def __init__(self, parent, main_window):
        """Initialize the table view panel."""
        super().__init__(parent, bg='#2b2b2b')
        
        self.main_window = main_window
        self.show_debug_overlay = tk.BooleanVar(value=True)
        self.custom_regions = None
        
        # Initialize region calibrator
        self.region_calibrator = RegionCalibrator(self, main_window)
        
        # Create components
        self.create_table_view()
        self.create_control_frame()
    
    def create_table_view(self):
        """Create the table view section."""
        # Table title
        table_title = tk.Label(
            self, 
            text="🎯 Live Table View", 
            font=("Arial", 16, "bold"),
            bg='#2b2b2b', fg='white'
        )
        table_title.pack(pady=2)  # Minimal padding to maximize image space
        
        # Debug overlay toggle
        debug_frame = tk.Frame(self, bg='#2b2b2b')
        debug_frame.pack(pady=1)
        
        tk.Checkbutton(
            debug_frame,
            text="Show Detection Regions",
            variable=self.show_debug_overlay,
            command=self.refresh_display,  # Refresh when toggled
            bg='#2b2b2b', fg='white', selectcolor='#2b2b2b', 
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            debug_frame,
            text="Calibrate Regions",
            command=self.region_calibrator.open_calibrator,
            bg='#FF9800', fg='white', font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # Screenshot display frame
        self.screenshot_frame = tk.Frame(self, bg='black')
        self.screenshot_frame.pack(fill="both", expand=True, padx=0, pady=0)  # No padding at all
        
        # Create canvas for screenshot
        self.screenshot_canvas = tk.Canvas(
            self.screenshot_frame, 
            bg="black", 
            highlightthickness=0
        )
        self.screenshot_canvas.pack(fill="both", expand=True, padx=0, pady=0)  # No padding
        
        # Placeholder text
        self.placeholder_label = tk.Label(
            self.screenshot_frame,
            text="No screenshot available\nClick 'Find Table' to connect",
            font=("Arial", 14),
            bg='black', fg='white'
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Load saved regions on startup
        self.load_saved_regions()
    
    def create_control_frame(self):
        """Create the control frame for buttons."""
        self.control_frame = tk.Frame(self, bg='#2b2b2b')
        self.control_frame.pack(fill="x", padx=5, pady=2)
    
    def get_control_frame(self):
        """Get the control frame for adding controls."""
        return self.control_frame
    
    def refresh_display(self):
        """Refresh the current display to show/hide regions."""
        if hasattr(self.main_window, 'current_screenshot') and self.main_window.current_screenshot is not None:
            self.display_screenshot(self.main_window.current_screenshot)
    
    def reload_regions(self):
        """Manually reload regions from file."""
        self.load_saved_regions()
        self.refresh_display()
        if hasattr(self.main_window, 'log_message'):
            self.main_window.log_message("🔄 Regions reloaded from file")
    
    def display_screenshot(self, screenshot):
        """Display screenshot in the canvas."""
        try:
            if screenshot is None:
                return
            
            # Hide placeholder
            self.placeholder_label.place_forget()
            
            # Add debug overlay if enabled
            if self.show_debug_overlay.get():
                screenshot = self.add_debug_overlay(screenshot)
            
            # Convert screenshot to PIL Image
            if len(screenshot.shape) == 3:
                screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            else:
                screenshot_rgb = screenshot
            
            pil_image = Image.fromarray(screenshot_rgb)
            
            # Get canvas dimensions
            self.screenshot_canvas.update()
            canvas_width = self.screenshot_canvas.winfo_width()
            canvas_height = self.screenshot_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Fill the entire canvas - stretch to fit if needed for maximum visibility
                img_width, img_height = pil_image.size
                
                # Use full canvas dimensions for maximum table visibility
                new_width = canvas_width
                new_height = canvas_height
                
                # Use high-quality resampling for better image quality
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)
                
                # Clear and display
                self.screenshot_canvas.delete("all")
                # Fill entire canvas
                self.screenshot_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                
                # Keep reference
                self.screenshot_canvas.image = photo
                
        except Exception as e:
            if hasattr(self.main_window, 'log_message'):
                self.main_window.log_message(f"Error displaying screenshot: {e}")
    
    def add_debug_overlay(self, screenshot):
        """Add debug overlay showing detection regions."""
        try:
            debug_image = screenshot.copy()
            height, width = debug_image.shape[:2]
            
            # Use custom regions if available, otherwise show error
            if self.custom_regions:
                regions_to_draw = self.custom_regions
            else:
                # NO MORE HARDCODED FALLBACKS
                self.logger.error("❌ NO REGIONS LOADED - Cannot show overlay")
                return screenshot
            
            # Draw all regions
            for region_name, region in regions_to_draw.items():
                x = int(width * region['x'])
                y = int(height * region['y'])
                w = int(width * region['width'])
                h = int(height * region['height'])
                
                # Get color with support for new color names
                color_map = {
                    'green': (0, 255, 0),
                    'lime': (0, 255, 0),      # Same as green but brighter
                    'blue': (255, 0, 0),
                    'cyan': (255, 255, 0),    # Cyan for hero cards
                    'yellow': (0, 255, 255),
                    'red': (0, 0, 255),
                    'white': (255, 255, 255)
                }
                color = color_map.get(region.get('color', 'green'), (0, 255, 0))
                
                # Draw rectangle
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), color, 2)
                
                # Add label
                label = region_name.replace('_', ' ').title()
                if 'community' in region_name:
                    label = f"C{region_name[-1]}"
                elif 'hero' in region_name:
                    label = f"H{region_name[-1]}"
                elif 'pot' in region_name:
                    label = "POT"
                
                cv2.putText(debug_image, label, (x, y - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            return debug_image
            
        except Exception as e:
            if hasattr(self.main_window, 'log_message'):
                self.main_window.log_message(f"Error adding debug overlay: {e}")
            return screenshot
    
    def load_saved_regions(self):
        """Load saved regions from file and apply them to the display."""
        try:
            import sys
            import os
            # Add src directory to path for importing RegionLoader
            src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            from region_loader import RegionLoader
            
            # Use the same RegionLoader as the rest of the system
            loader = RegionLoader()
            regions = loader.load_regions()
            
            if regions:
                # Convert to the format expected by the overlay (add colors)
                converted_regions = {}
                for region_name, region_data in regions.items():
                    if isinstance(region_data, dict) and 'x' in region_data:
                        # Determine color based on region type
                        if 'community' in region_name:
                            color = 'green'
                        elif 'hero' in region_name:
                            color = 'cyan'
                        elif 'pot' in region_name:
                            color = 'yellow'
                        else:
                            color = 'white'
                            
                        converted_regions[region_name] = {
                            'x': region_data['x'],
                            'y': region_data['y'],
                            'width': region_data['width'],
                            'height': region_data['height'],
                            'color': color
                        }
                
                if converted_regions:
                    self.custom_regions = converted_regions
                    if hasattr(self.main_window, 'log_message'):
                        self.main_window.log_message(f"Successfully loaded {len(converted_regions)} saved regions for overlay")
                        
        except Exception as e:
            if hasattr(self.main_window, 'log_message'):
                self.main_window.log_message(f"Could not load saved regions: {e}")