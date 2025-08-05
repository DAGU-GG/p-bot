"""
Manual Region Calibrator
Allows users to manually adjust card detection regions and save configurations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import datetime
from typing import Dict, Tuple, Optional, Any
import cv2
import numpy as np
from PIL import Image, ImageTk


class RegionCalibrator:
    """Interactive region calibration tool for manual adjustment of detection areas."""
    
    def __init__(self, parent, main_window):
        """Initialize the region calibrator."""
        self.parent = parent
        self.main_window = main_window
        self.calibration_window = None
        self.canvas = None
        self.current_image = None
        self.photo_image = None
        
        # Store screenshot dimensions for proper scaling
        self.screenshot_width = 1200  # Default dimensions
        self.screenshot_height = 800
        
        # Region definitions with default positions (in percentages)
        self.regions = {
            'community_card_1': {'x': 33.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
            'community_card_2': {'x': 40.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
            'community_card_3': {'x': 47.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
            'community_card_4': {'x': 54.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
            'community_card_5': {'x': 61.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
            'hero_card_1': {'x': 42.0, 'y': 72.0, 'width': 5.5, 'height': 6.0, 'color': 'cyan'},
            'hero_card_2': {'x': 48.5, 'y': 72.0, 'width': 5.5, 'height': 6.0, 'color': 'cyan'},
            'pot_area': {'x': 43.0, 'y': 42.0, 'width': 14.0, 'height': 6.0, 'color': 'yellow'}
        }
        
        # Canvas dimensions and scaling
        self.canvas_width = 1000
        self.canvas_height = 700
        self.image_scale = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0
        
        # Interaction state
        self.selected_region = None
        self.drag_start = None
        self.resize_handle = None
        self.region_rectangles = {}
        
        # Load saved regions if they exist
        self.load_regions()
    
    def open_calibrator(self):
        """Open the region calibration window."""
        if self.calibration_window and self.calibration_window.winfo_exists():
            self.calibration_window.lift()
            return
        
        # Get current screenshot with proper error handling
        screenshot = None
        try:
            # Check capture mode from main window
            capture_mode = getattr(self.main_window, 'capture_mode', 'window')
            
            # Check capture mode from main window
            capture_mode = getattr(self.main_window, 'capture_mode', 'window')
            
            if capture_mode == "obs":
                # Check for hardware capture system (new)
                if hasattr(self.main_window, 'hardware_capture') and self.main_window.hardware_capture:
                    screenshot = self.main_window.hardware_capture.capture_from_virtual_camera()
                # Check for old obs_capture system (fallback)
                elif hasattr(self.main_window, 'obs_capture') and self.main_window.obs_capture:
                    screenshot = self.main_window.obs_capture.capture_single_frame()
                else:
                    messagebox.showerror("Error", "OBS capture not available. Please ensure OBS Virtual Camera is running.")
                    return
            else:  # window mode
                if hasattr(self.main_window, 'window_capture') and self.main_window.window_capture:
                    # Ensure a window is selected before trying to capture
                    if not self.main_window.window_capture.selected_window:
                        # Try to select the best window automatically
                        best_window = self.main_window.window_capture.select_best_window()
                        if not best_window:
                            messagebox.showerror("Error", "No PokerStars table window found. Please ensure a PokerStars table is open and try again.")
                            return
                    
                    screenshot = self.main_window.window_capture.capture_current_window()
                else:
                    messagebox.showerror("Error", "Window capture not available. Please connect to a PokerStars window first.")
                    return
            
            if screenshot is None:
                messagebox.showerror("Error", "Could not capture screenshot. Please ensure table is visible and try again.")
                return
            
            # Store screenshot dimensions for proper scaling
            self.screenshot_height, self.screenshot_width = screenshot.shape[:2]
            self.current_image = screenshot
            self.create_calibration_window()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")
            return
    
    def create_calibration_window(self):
        """Create the calibration window with interactive canvas."""
        self.calibration_window = tk.Toplevel(self.parent)
        self.calibration_window.title("Manual Region Calibration")
        self.calibration_window.geometry("1200x800")
        self.calibration_window.configure(bg='#2b2b2b')
        
        # Create main frame
        main_frame = tk.Frame(self.calibration_window, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create control panel
        self.create_control_panel(main_frame)
        
        # Create canvas frame
        canvas_frame = tk.Frame(main_frame, bg='black')
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg='black',
            highlightthickness=1,
            highlightbackground='white'
        )
        self.canvas.pack(expand=True)
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        
        # Display image and regions
        self.update_canvas()
    
    def create_control_panel(self, parent):
        """Create the control panel with buttons and region list."""
        control_frame = tk.Frame(parent, bg='#2b2b2b')
        control_frame.pack(fill=tk.X, pady=5)
        
        # Title
        title_label = tk.Label(
            control_frame,
            text="🎯 Manual Region Calibration",
            font=("Arial", 16, "bold"),
            bg='#2b2b2b', fg='white'
        )
        title_label.pack(pady=5)
        
        # Instructions
        instructions = tk.Label(
            control_frame,
            text="Click and drag regions to move them. Drag corners/edges to resize. Right-click for options.",
            font=("Arial", 10),
            bg='#2b2b2b', fg='lightgray'
        )
        instructions.pack(pady=2)
        
        # Button frame
        button_frame = tk.Frame(control_frame, bg='#2b2b2b')
        button_frame.pack(pady=10)
        
        # Control buttons
        tk.Button(
            button_frame, text="Reset to Defaults", 
            command=self.reset_regions,
            bg='#f44336', fg='white', font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="Save Configuration", 
            command=self.save_regions,
            bg='#4CAF50', fg='white', font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="Load Configuration", 
            command=self.load_regions_dialog,
            bg='#2196F3', fg='white', font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="Test Recognition", 
            command=self.test_recognition,
            bg='#FF9800', fg='white', font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="Apply & Close", 
            command=self.apply_and_close,
            bg='#9C27B0', fg='white', font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # Region list frame
        list_frame = tk.Frame(control_frame, bg='#2b2b2b')
        list_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(list_frame, text="Regions:", font=("Arial", 12, "bold"), 
                bg='#2b2b2b', fg='white').pack(side=tk.LEFT)
        
        # Region selection
        self.region_var = tk.StringVar()
        self.region_combo = ttk.Combobox(
            list_frame, textvariable=self.region_var,
            values=list(self.regions.keys()),
            state="readonly", width=20
        )
        self.region_combo.pack(side=tk.LEFT, padx=10)
        self.region_combo.bind('<<ComboboxSelected>>', self.on_region_select)
        
        # Position display
        self.position_label = tk.Label(
            list_frame, text="Position: Not selected",
            font=("Arial", 10), bg='#2b2b2b', fg='lightgray'
        )
        self.position_label.pack(side=tk.LEFT, padx=20)
    
    def update_canvas(self):
        """Update the canvas with current image and regions."""
        if self.current_image is None:
            return
        
        # Convert image to RGB
        if len(self.current_image.shape) == 3:
            image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = self.current_image
        
        # Calculate scaling to fit canvas
        img_height, img_width = image_rgb.shape[:2]
        scale_x = self.canvas_width / img_width
        scale_y = self.canvas_height / img_height
        self.image_scale = min(scale_x, scale_y) * 0.95  # Leave some margin
        
        # Calculate new dimensions and offset
        new_width = int(img_width * self.image_scale)
        new_height = int(img_height * self.image_scale)
        self.image_offset_x = (self.canvas_width - new_width) // 2
        self.image_offset_y = (self.canvas_height - new_height) // 2
        
        # Create PIL image and display
        pil_image = Image.fromarray(image_rgb)
        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(pil_image)
        
        # Clear entire canvas and draw image
        self.canvas.delete("all")
        self.canvas.create_image(
            self.image_offset_x, self.image_offset_y,
            anchor=tk.NW, image=self.photo_image, tags="background"
        )
        
        # Draw regions
        self.draw_regions()
    
    def draw_regions(self):
        """Draw all regions on the canvas with proper coordinate conversion."""
        # Clear all existing regions first
        self.canvas.delete("region")
        self.canvas.delete("handle")
        self.canvas.delete("label")
        self.canvas.delete("label_bg")
        self.region_rectangles.clear()
        
        if self.current_image is None:
            return
        
        img_height, img_width = self.current_image.shape[:2]
        
        for region_name, region_data in self.regions.items():
            # Convert percentage coordinates to canvas coordinates
            x1, y1 = self.percentage_to_canvas(region_data['x'], region_data['y'])
            x2, y2 = self.percentage_to_canvas(
                region_data['x'] + region_data['width'],
                region_data['y'] + region_data['height']
            )
            
            # Ensure proper rectangle coordinates
            x, y = min(x1, x2), min(y1, y2)
            width, height = abs(x2 - x1), abs(y2 - y1)
            
            # Draw rectangle with better visibility
            rect_id = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                outline=region_data['color'], width=3,
                fill='', stipple='gray25', tags=(region_name, "region")
            )
            
            # Draw label with background for better visibility
            self.canvas.create_rectangle(
                x, y - 20, x + 100, y,
                fill='black', outline=region_data['color'],
                tags=(region_name, "label_bg")
            )
            
            label_id = self.canvas.create_text(
                x + 2, y - 18, text=region_name.replace('_', ' ').title(),
                anchor=tk.NW, fill=region_data['color'],
                font=("Arial", 8, "bold"), tags=(region_name, "label")
            )
            
            # Draw resize handles - make them bigger and more visible
            handle_size = 8
            handles = []
            
            # Corner handles with better visibility
            for hx, hy in [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]:
                handle = self.canvas.create_rectangle(
                    hx - handle_size//2, hy - handle_size//2,
                    hx + handle_size//2, hy + handle_size//2,
                    fill=region_data['color'], outline='white', width=2,
                    tags=(f"{region_name}_handle", "handle")
                )
                handles.append(handle)
            
            self.region_rectangles[region_name] = {
                'rect': rect_id,
                'label': label_id,
                'handles': handles,
                'coords': (x, y, width, height)
            }
    
    def canvas_to_percentage(self, canvas_x, canvas_y):
        """Convert canvas coordinates to percentage coordinates (0-100) with proper bounds checking."""
        if self.current_image is None:
            return 0, 0
            
        img_height, img_width = self.current_image.shape[:2]
        
        # Convert canvas to image coordinates with proper scaling
        img_x = (canvas_x - self.image_offset_x) / self.image_scale
        img_y = (canvas_y - self.image_offset_y) / self.image_scale
        
        # Ensure coordinates are within image bounds
        img_x = max(0, min(img_x, img_width))
        img_y = max(0, min(img_y, img_height))
        
        # Convert to percentages (0-100 range)
        x_percent = (img_x / img_width) * 100.0
        y_percent = (img_y / img_height) * 100.0
        
        # Clamp to valid percentage range
        x_percent = max(0, min(x_percent, 100))
        y_percent = max(0, min(y_percent, 100))
        
        return x_percent, y_percent
    
    def percentage_to_canvas(self, x_percent, y_percent):
        """Convert percentage coordinates (0-100) to canvas coordinates."""
        if self.current_image is None:
            return 0, 0
            
        img_height, img_width = self.current_image.shape[:2]
        
        # Convert percentages to image coordinates
        img_x = (x_percent / 100.0) * img_width
        img_y = (y_percent / 100.0) * img_height
        
        # Convert to canvas coordinates with scaling and offset
        canvas_x = self.image_offset_x + (img_x * self.image_scale)
        canvas_y = self.image_offset_y + (img_y * self.image_scale)
        
        return canvas_x, canvas_y
    
    def on_canvas_click(self, event):
        """Handle canvas click events."""
        clicked_item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(clicked_item)
        
        if not tags:
            return
        
        # Check if clicked on a region or handle
        for tag in tags:
            if tag.endswith('_handle'):
                # Clicked on resize handle
                region_name = tag.replace('_handle', '')
                self.selected_region = region_name
                self.resize_handle = clicked_item
                self.drag_start = (event.x, event.y)
                break
            elif tag in self.regions:
                # Clicked on region
                self.selected_region = tag
                self.resize_handle = None
                self.drag_start = (event.x, event.y)
                self.region_var.set(tag)
                self.update_position_display()
                break
    
    def on_canvas_drag(self, event):
        """Handle canvas drag events."""
        if not self.selected_region or not self.drag_start:
            return
        
        dx = event.x - self.drag_start[0]
        dy = event.y - self.drag_start[1]
        
        if self.resize_handle:
            # Resize region
            self.resize_region(dx, dy)
        else:
            # Move region
            self.move_region(dx, dy)
        
        self.drag_start = (event.x, event.y)
        self.update_position_display()
    
    def on_canvas_release(self, event):
        """Handle canvas release events."""
        self.selected_region = None
        self.resize_handle = None
        self.drag_start = None
    
    def on_canvas_motion(self, event):
        """Handle canvas motion for cursor changes."""
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        if any(tag.endswith('_handle') for tag in tags):
            self.canvas.configure(cursor="sizing")
        elif any(tag in self.regions for tag in tags):
            self.canvas.configure(cursor="hand2")
        else:
            self.canvas.configure(cursor="")
    
    def move_region(self, dx, dy):
        """Move a region by the specified offset."""
        if not self.selected_region:
            return
        
        # Convert pixel movement to percentage
        img_height, img_width = self.current_image.shape[:2]
        dx_percent = (dx / self.image_scale) / img_width * 100.0
        dy_percent = (dy / self.image_scale) / img_height * 100.0
        
        # Update region data
        self.regions[self.selected_region]['x'] += dx_percent
        self.regions[self.selected_region]['y'] += dy_percent
        
        # Clamp to image bounds (0-100 percentage)
        max_x = 100.0 - self.regions[self.selected_region]['width']
        max_y = 100.0 - self.regions[self.selected_region]['height']
        
        self.regions[self.selected_region]['x'] = max(0, min(max_x, self.regions[self.selected_region]['x']))
        self.regions[self.selected_region]['y'] = max(0, min(max_y, self.regions[self.selected_region]['y']))
        
        # Redraw all regions to prevent trails
        self.draw_regions()
        self.update_position_display()
    
    def resize_region(self, dx, dy):
        """Resize a region by the specified offset."""
        if not self.selected_region or not self.resize_handle:
            return
        
        # Convert pixel movement to percentage
        img_height, img_width = self.current_image.shape[:2]
        dx_percent = (dx / self.image_scale) / img_width * 100.0
        dy_percent = (dy / self.image_scale) / img_height * 100.0
        
        # Update region size (simple resize from bottom-right corner)
        self.regions[self.selected_region]['width'] += dx_percent
        self.regions[self.selected_region]['height'] += dy_percent
        
        # Clamp to reasonable bounds (2% to 30% of image)
        self.regions[self.selected_region]['width'] = max(2.0, min(30.0, self.regions[self.selected_region]['width']))
        self.regions[self.selected_region]['height'] = max(2.0, min(30.0, self.regions[self.selected_region]['height']))
        
        # Redraw all regions to prevent trails
        self.draw_regions()
        self.update_position_display()
    
    def on_region_select(self, event):
        """Handle region selection from dropdown."""
        selected = self.region_var.get()
        if selected in self.regions:
            self.selected_region = selected
            self.update_position_display()
    
    def update_position_display(self):
        """Update the position display label."""
        if self.selected_region and self.selected_region in self.regions:
            region = self.regions[self.selected_region]
            self.position_label.config(
                text=f"Position: ({region['x']:.3f}, {region['y']:.3f}) "
                     f"Size: ({region['width']:.3f}, {region['height']:.3f})"
            )
        else:
            self.position_label.config(text="Position: Not selected")
    
    def reset_regions(self):
        """Reset all regions to default positions."""
        if messagebox.askyesno("Reset Regions", "Reset all regions to default positions?"):
            self.regions = {
                'community_card_1': {'x': 33.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
                'community_card_2': {'x': 40.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
                'community_card_3': {'x': 47.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
                'community_card_4': {'x': 54.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
                'community_card_5': {'x': 61.5, 'y': 35.0, 'width': 6.0, 'height': 8.0, 'color': 'lime'},
                'hero_card_1': {'x': 42.0, 'y': 72.0, 'width': 5.5, 'height': 6.0, 'color': 'cyan'},
                'hero_card_2': {'x': 48.5, 'y': 72.0, 'width': 5.5, 'height': 6.0, 'color': 'cyan'},
                'pot_area': {'x': 43.0, 'y': 42.0, 'width': 14.0, 'height': 6.0, 'color': 'yellow'}
            }
            self.draw_regions()
    
    def save_regions(self):
        """Save current regions to file."""
        try:
            # Create regions directory if it doesn't exist
            os.makedirs('regions', exist_ok=True)
            
            config_data = {
                'regions': {name: {k: v for k, v in data.items() if k != 'color'} 
                           for name, data in self.regions.items()},
                'timestamp': str(datetime.datetime.now()),
                'version': '1.0',
                'image_dimensions': {
                    'width': self.current_image.shape[1] if self.current_image is not None else 1920,
                    'height': self.current_image.shape[0] if self.current_image is not None else 1080
                }
            }
            
            filename = filedialog.asksaveasfilename(
                title="Save Region Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir="regions",
                initialfile="region_config.json"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                # Also save as default config
                with open('regions/region_config.json', 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Region configuration saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_regions(self):
        """Load regions from default config file."""
        try:
            config_paths = ['regions/region_config.json', 'region_config.json']
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    
                    if 'regions' in config_data:
                        # Merge with default colors and ensure all fields exist
                        for name, data in config_data['regions'].items():
                            if name in self.regions:
                                # Update existing region data
                                self.regions[name].update(data)
                                # Ensure color field exists
                                if 'color' not in self.regions[name]:
                                    if 'community' in name:
                                        self.regions[name]['color'] = 'lime'
                                    elif 'hero' in name:
                                        self.regions[name]['color'] = 'cyan'
                                    else:
                                        self.regions[name]['color'] = 'yellow'
                            else:
                                # Add new region with default color
                                self.regions[name] = data.copy()
                                if 'color' not in self.regions[name]:
                                    if 'community' in name:
                                        self.regions[name]['color'] = 'lime'
                                    elif 'hero' in name:
                                        self.regions[name]['color'] = 'cyan'
                                    else:
                                        self.regions[name]['color'] = 'yellow'
                    
                    self.main_window.log_message(f"SUCCESS: Loaded region config from {config_path}")
                    self.update_canvas()  # Refresh the display
                    return
            
            self.main_window.log_message("WARNING: No region config file found, using defaults")
                
        except Exception as e:
            if hasattr(self.main_window, 'log_message'):
                self.main_window.log_message(f"ERROR loading region config: {e}")
                import traceback
                self.main_window.log_message(f"Traceback: {traceback.format_exc()}")
    
    def load_regions_dialog(self):
        """Open a file dialog to load regions from a JSON file."""
        filepath = filedialog.askopenfilename(
            title="Load Regions",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if 'regions' in data:
                self.regions = data['regions']
                self.update_canvas()
                self.main_window.log_message(f"Loaded regions from {filepath}")
            else:
                messagebox.showerror("Error", "Invalid region file format")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load regions: {e}")
            self.main_window.log_message(f"Error loading regions: {e}")
            
    def get_all_regions(self):
        """Return all defined regions.
        
        This method is used by other components that need access to the regions.
        
        Returns:
            dict: A dictionary containing all defined regions
        """
        return self.regions
    
    def test_recognition(self):
        """Test card recognition with current regions."""
        if self.current_image is None:
            messagebox.showerror("Error", "No image available for testing")
            return
        
        try:
            # Check if bot or hardware capture is available
            bot_available = hasattr(self.main_window, 'bot') and self.main_window.bot
            hardware_available = hasattr(self.main_window, 'hardware_capture') and self.main_window.hardware_capture
            
            if not bot_available and not hardware_available:
                messagebox.showerror("Error", "No capture system initialized. Please connect to OBS or PokerStars first.")
                return
            
            # Test recognition using available system
            if hardware_available:
                # Use hardware capture system
                results = []
                for region_name, region_rect in self.region_rectangles.items():
                    if region_rect and 'card' in region_name.lower():
                        # Extract region from current image
                        x, y, w, h = region_rect[:4]
                        if x + w <= self.current_image.shape[1] and y + h <= self.current_image.shape[0]:
                            card_region = self.current_image[y:y+h, x:x+w]
                            result = self.main_window.hardware_capture.recognize_card_from_region(card_region, region_name)
                            if result:
                                results.append(f"{region_name}: {result['rank']}{result['suit']} ({result['method']}, {result['confidence']:.2f})")
                            else:
                                results.append(f"{region_name}: No card detected")
                
                result_text = "Hardware Capture Recognition Test:\n\n"
                if results:
                    result_text += "\n".join(results)
                else:
                    result_text += "No card regions found or no cards detected"
                
                messagebox.showinfo("Recognition Test Results", result_text)
                
            elif bot_available:
                # Apply current regions to bot components first
                self.apply_regions_to_bot()
                
                # Use legacy bot system
                analysis = self.main_window.bot.analyze_game_state(self.current_image)
                
                # Show results
                result_text = "Recognition Test Results:\n\n"
                
                if 'hole_cards' in analysis:
                    hole_cards = analysis['hole_cards']
                    result_text += f"Hole Cards: {hole_cards}\n"
                    result_text += f"Valid: {hole_cards.is_valid()}\n\n"
                
                if 'community_cards' in analysis:
                    community_cards = analysis['community_cards']
                    result_text += f"Community Cards: {community_cards}\n"
                    result_text += f"Count: {community_cards.count}/5\n\n"
                
                if 'table_info' in analysis:
                    table_info = analysis['table_info']
                    result_text += f"Players Detected: {len(table_info.players)}\n"
                    result_text += f"Pot Size: {table_info.pot_size:.1f}BB\n"
                
                messagebox.showinfo("Recognition Test Results", result_text)
                
        except Exception as e:
            messagebox.showerror("Error", f"Recognition test failed: {e}")
    
    def apply_regions_to_bot(self):
        """Apply current regions to bot components."""
        if not hasattr(self.main_window, 'bot') or not self.main_window.bot:
            self.main_window.log_message("[ERROR] Bot not initialized, cannot apply regions")
            return
        
        try:
            # Update community card detector regions
            if hasattr(self.main_window.bot, 'community_detector'):
                community_regions = {}
                for i in range(1, 6):
                    region_name = f'community_card_{i}'
                    if region_name in self.regions:
                        # Convert to decimal format (0.0-1.0)
                        community_regions[f'card_{i}'] = {
                            'x_percent': self.regions[region_name]['x'] / 100.0,
                            'y_percent': self.regions[region_name]['y'] / 100.0,
                            'width_percent': self.regions[region_name]['width'] / 100.0,
                            'height_percent': self.regions[region_name]['height'] / 100.0
                        }
                
                # CRITICAL FIX: Update both the attribute and call the method
                if hasattr(self.main_window.bot.community_detector, 'community_card_regions'):
                    self.main_window.bot.community_detector.community_card_regions = community_regions
                
                # Also use the update_regions method
                if hasattr(self.main_window.bot.community_detector, 'update_regions'):
                    self.main_window.bot.community_detector.update_regions(community_regions)
                
                self.main_window.log_message(f"[SUCCESS] Applied {len(community_regions)} community card regions to detector")
                # Log for debugging
                for name, region in community_regions.items():
                    self.main_window.log_message(f"   [COMMUNITY] {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
            
            # Update card recognizer regions
            if hasattr(self.main_window.bot, 'card_recognizer'):
                card_regions = {}
                if 'hero_card_1' in self.regions:
                    card_regions['hero_card1'] = {
                        'x_percent': self.regions['hero_card_1']['x'] / 100.0,
                        'y_percent': self.regions['hero_card_1']['y'] / 100.0,
                        'width_percent': self.regions['hero_card_1']['width'] / 100.0,
                        'height_percent': self.regions['hero_card_1']['height'] / 100.0
                    }
                
                if 'hero_card_2' in self.regions:
                    card_regions['hero_card2'] = {
                        'x_percent': self.regions['hero_card_2']['x'] / 100.0,
                        'y_percent': self.regions['hero_card_2']['y'] / 100.0,
                        'width_percent': self.regions['hero_card_2']['width'] / 100.0,
                        'height_percent': self.regions['hero_card_2']['height'] / 100.0
                    }
                
                # CRITICAL FIX: Update both the attribute and call the method
                if hasattr(self.main_window.bot.card_recognizer, 'card_regions'):
                    self.main_window.bot.card_recognizer.card_regions = card_regions
                
                # Also use the update_regions method
                if hasattr(self.main_window.bot.card_recognizer, 'update_regions'):
                    self.main_window.bot.card_recognizer.update_regions(card_regions)
                
                self.main_window.log_message(f"[SUCCESS] Applied {len(card_regions)} hero card regions to recognizer")
                # Log for debugging
                for name, region in card_regions.items():
                    self.main_window.log_message(f"   [HERO] {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
            
            # Update table analyzer regions
            if hasattr(self.main_window.bot, 'table_analyzer'):
                if 'pot_area' in self.regions:
                    pot_region = {
                        'x_percent': self.regions['pot_area']['x'] / 100.0,
                        'y_percent': self.regions['pot_area']['y'] / 100.0,
                        'width_percent': self.regions['pot_area']['width'] / 100.0,
                        'height_percent': self.regions['pot_area']['height'] / 100.0
                    }
                    # Apply to table analyzer if it has enhanced_ui_regions
                    if hasattr(self.main_window.bot.table_analyzer, 'enhanced_ui_regions'):
                        self.main_window.bot.table_analyzer.enhanced_ui_regions['pot'] = pot_region
                        self.main_window.log_message("[SUCCESS] Applied pot region to table analyzer")
            
            # CRITICAL FIX: Force a refresh of the last analysis to ensure continuous detection
            if hasattr(self.main_window, 'last_analysis'):
                self.main_window.last_analysis = None
            
            self.main_window.log_message("✅ Regions successfully applied to all bot components")
            
            # CRITICAL FIX: Update the UI display to show the new regions
            if hasattr(self.main_window, 'table_panel'):
                # Convert regions for display
                converted_regions = {}
                for region_name, region_data in self.regions.items():
                    color = 'lime'
                    if 'community' in region_name:
                        color = 'lime'
                    elif 'hero' in region_name:
                        color = 'cyan'
                    else:
                        color = 'yellow'
                    
                    converted_regions[region_name] = {
                        'x': region_data['x'] / 100.0,
                        'y': region_data['y'] / 100.0,
                        'width': region_data['width'] / 100.0,
                        'height': region_data['height'] / 100.0,
                        'color': color
                    }
                self.main_window.table_panel.custom_regions = converted_regions
                self.main_window.log_message("[SUCCESS] Updated regions in UI display")
            
        except Exception as e:
            self.main_window.log_message(f"Error applying regions to bot: {e}")
            import traceback
            self.main_window.log_message(f"Traceback: {traceback.format_exc()}")
    
    def apply_and_close(self):
        """Apply current regions and close calibrator."""
        try:
            self.main_window.log_message("Applying new regions...")
            
            # Save regions first
            self.save_regions()
            self.main_window.log_message("SUCCESS: Regions saved to file")
            
            # Apply to bot (non-blocking)
            self.apply_regions_to_bot()
            self.main_window.log_message("SUCCESS: Regions applied to bot")
            
            # Force region refresh in main window (non-blocking)
            def delayed_refresh():
                try:
                    if hasattr(self.main_window, 'refresh_regions'):
                        self.main_window.refresh_regions()
                        self.main_window.log_message("SUCCESS: Main window regions refreshed")
                    
                    # Clear cached analysis
                    if hasattr(self.main_window, 'last_analysis'):
                        self.main_window.last_analysis = None
                        
                    self.main_window.log_message("SUCCESS: Region update complete - next capture will use new regions")
                except Exception as e:
                    self.main_window.log_message(f"Warning during refresh: {e}")
            
            # Schedule the refresh to run after a brief delay to avoid freezing
            self.main_window.root.after(100, delayed_refresh)
            
            # Close calibrator immediately
            self.close_calibrator()
            self.main_window.log_message("Region calibrator closed successfully")
            
        except Exception as e:
            self.main_window.log_message(f"Error saving and applying regions: {e}")
            import traceback
            self.main_window.log_message(f"Traceback: {traceback.format_exc()}")
    
    def close_calibrator(self):
        """Close the calibration window and show success message."""
        try:
            # Convert regions for table panel display
            all_regions = self.get_all_regions()
            converted_regions = {}
            
            for region_name, region_data in all_regions.items():
                # Set color based on region type
                if 'community' in region_name:
                    color = 'lime'
                elif 'hero' in region_name:
                    color = 'cyan'
                else:
                    color = 'yellow'
                
                converted_regions[region_name] = {
                    'x': region_data['x'] / 100.0,
                    'y': region_data['y'] / 100.0,
                    'width': region_data['width'] / 100.0,
                    'height': region_data['height'] / 100.0,
                    'color': color
                }
                
            # Update main window's debug overlay
            if hasattr(self.main_window, 'table_panel'):
                self.main_window.table_panel.custom_regions = converted_regions
                self.main_window.log_message("✅ Regions applied to live table view")
            
            messagebox.showinfo("Success", "Regions applied successfully!\nRegions are now visible in the live table view.")
            self.calibration_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply regions: {e}")
            if hasattr(self.main_window, 'log_message'):
                self.main_window.log_message(f"Error applying regions: {e}")