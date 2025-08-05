"""
Table Screenshot Capture Tool
Captures a screenshot from OBS Virtual Camera for manual region creation
"""

import cv2
import numpy as np
import time
import logging
from datetime import datetime

class TableScreenshotCapture:
    """Simple tool to capture poker table screenshot for region creation"""
    
    def __init__(self):
        self.logger = logging.getLogger("screenshot_capture")
        self.virtual_camera = None
        self.camera_index = None
    
    def find_obs_virtual_camera(self):
        """Find OBS Virtual Camera index"""
        try:
            # Based on testing, camera index 1 works for this setup
            test_index = 1
            
            try:
                cap = cv2.VideoCapture(test_index, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # Try to read a frame to verify it works
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✅ Found working camera at index {test_index}: {frame.shape}")
                        cap.release()
                        return test_index
                cap.release()
            except Exception as e:
                pass
            
            # Fallback: try different camera indices
            for camera_index in range(10):
                if camera_index == test_index:  # Skip already tested
                    continue
                try:
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                    if cap.isOpened():
                        # Try to read a frame to verify it works
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            print(f"✅ Found working camera at index {camera_index}: {frame.shape}")
                            cap.release()
                            return camera_index
                    cap.release()
                except Exception as e:
                    continue
            
            print("❌ No working virtual camera found")
            return None
            
        except Exception as e:
            print(f"❌ Error finding virtual camera: {e}")
            return None
    
    def connect_to_virtual_camera(self):
        """Connect to OBS Virtual Camera"""
        try:
            if self.virtual_camera is not None:
                self.virtual_camera.release()
            
            # Find virtual camera
            self.camera_index = self.find_obs_virtual_camera()
            if self.camera_index is None:
                return False
            
            # Connect to virtual camera
            self.virtual_camera = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            
            if not self.virtual_camera.isOpened():
                print(f"❌ Failed to open virtual camera at index {self.camera_index}")
                return False
            
            # Set camera properties for better quality
            self.virtual_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.virtual_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.virtual_camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Test capture
            ret, frame = self.virtual_camera.read()
            if ret and frame is not None:
                print(f"✅ Connected to OBS Virtual Camera successfully!")
                print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
                return True
            else:
                print("❌ Virtual camera connected but no frame received")
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to virtual camera: {e}")
            return False
    
    def capture_table_screenshot(self, save_preview=True):
        """Capture a screenshot of the current poker table"""
        try:
            # Ensure virtual camera is connected
            if self.virtual_camera is None or not self.virtual_camera.isOpened():
                if not self.connect_to_virtual_camera():
                    return None
            
            print("📸 Capturing screenshot in 3 seconds...")
            print("   Make sure your poker table is visible and cards are dealt!")
            
            # Countdown
            for i in range(3, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            # Capture frame
            ret, frame = self.virtual_camera.read()
            
            if not ret or frame is None:
                print("❌ Failed to capture frame from virtual camera")
                # Try to reconnect
                if self.connect_to_virtual_camera():
                    ret, frame = self.virtual_camera.read()
                    if not ret or frame is None:
                        return None
                else:
                    return None
            
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save the main screenshot
            main_filename = f"poker_table_screenshot_{timestamp}.png"
            cv2.imwrite(main_filename, frame)
            print(f"✅ Screenshot saved as: {main_filename}")
            
            # Also save a copy with annotated regions if we have existing config
            if save_preview:
                self.save_annotated_preview(frame, timestamp)
            
            # Show basic info about the image
            height, width = frame.shape[:2]
            avg_brightness = np.mean(frame)
            
            print(f"📊 Image Info:")
            print(f"   Resolution: {width}x{height}")
            print(f"   Average brightness: {avg_brightness:.1f}")
            
            if avg_brightness < 30:
                print("⚠️  Image appears quite dark - check your OBS settings")
            
            return frame, main_filename
            
        except Exception as e:
            print(f"❌ Error capturing screenshot: {e}")
            return None
    
    def save_annotated_preview(self, frame, timestamp):
        """Save a preview with existing regions marked (if any)"""
        try:
            # Try to load existing region configuration
            region_files = [
                "regions/region_config_corrected.json",
                "regions/region_config.json",
                "region_config.json"
            ]
            
            for region_file in region_files:
                try:
                    import json
                    with open(region_file, 'r') as f:
                        region_data = json.load(f)
                    
                    if 'regions' in region_data:
                        # Create annotated preview
                        annotated = frame.copy()
                        height, width = frame.shape[:2]
                        
                        for region_name, region_info in region_data['regions'].items():
                            # Convert percentage to pixels
                            x = int((region_info['x'] / 100.0) * width)
                            y = int((region_info['y'] / 100.0) * height)
                            w = int((region_info['width'] / 100.0) * width)
                            h = int((region_info['height'] / 100.0) * height)
                            
                            # Draw rectangle
                            color = (0, 255, 0) if 'community' in region_name else (255, 0, 0)
                            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                            
                            # Add label
                            cv2.putText(annotated, region_name, (x, y - 10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        
                        # Save annotated preview
                        preview_filename = f"poker_table_preview_{timestamp}.png"
                        cv2.imwrite(preview_filename, annotated)
                        print(f"✅ Annotated preview saved as: {preview_filename}")
                        print(f"   Green boxes = community cards, Red boxes = hero cards")
                        break
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            pass  # Not critical if this fails
    
    def interactive_region_creator(self, screenshot_filename):
        """Open an interactive tool to create regions from the screenshot"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            from PIL import Image, ImageTk
            
            print(f"\n🎯 Starting interactive region creator...")
            print(f"   Screenshot: {screenshot_filename}")
            print(f"   Click and drag to create regions for each card position")
            
            class RegionCreator:
                def __init__(self, image_path):
                    self.root = tk.Tk()
                    self.root.title("Poker Table Region Creator")
                    
                    # Load and display image
                    self.original_image = cv2.imread(image_path)
                    self.image_height, self.image_width = self.original_image.shape[:2]
                    
                    # Convert for tkinter
                    image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                    self.pil_image = Image.fromarray(image_rgb)
                    
                    # Scale image to fit screen if needed
                    screen_width = self.root.winfo_screenwidth() - 100
                    screen_height = self.root.winfo_screenheight() - 200
                    
                    scale_factor = min(screen_width / self.image_width, screen_height / self.image_height, 1.0)
                    
                    if scale_factor < 1.0:
                        new_width = int(self.image_width * scale_factor)
                        new_height = int(self.image_height * scale_factor)
                        self.pil_image = self.pil_image.resize((new_width, new_height))
                        self.scale_factor = scale_factor
                    else:
                        self.scale_factor = 1.0
                    
                    self.tk_image = ImageTk.PhotoImage(self.pil_image)
                    
                    # Create canvas
                    self.canvas = tk.Canvas(self.root, width=self.pil_image.width, height=self.pil_image.height)
                    self.canvas.pack()
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
                    
                    # Region tracking
                    self.regions = {}
                    self.current_region = None
                    self.start_x = None
                    self.start_y = None
                    self.current_rect = None
                    
                    # Current region type
                    self.region_type = tk.StringVar(value="community_card_1")
                    
                    # Create controls
                    self.create_controls()
                    
                    # Bind mouse events
                    self.canvas.bind("<Button-1>", self.start_selection)
                    self.canvas.bind("<B1-Motion>", self.update_selection)
                    self.canvas.bind("<ButtonRelease-1>", self.end_selection)
                    
                    print("\n📋 Instructions:")
                    print("   1. Select region type from dropdown")
                    print("   2. Click and drag to create region")
                    print("   3. Repeat for all card positions")
                    print("   4. Click 'Save Regions' when done")
                
                def create_controls(self):
                    control_frame = tk.Frame(self.root)
                    control_frame.pack(pady=10)
                    
                    # Region type selector
                    tk.Label(control_frame, text="Region Type:").pack(side=tk.LEFT)
                    
                    region_types = [
                        "community_card_1", "community_card_2", "community_card_3",
                        "community_card_4", "community_card_5",
                        "hero_card_1", "hero_card_2", "pot_area"
                    ]
                    
                    dropdown = tk.OptionMenu(control_frame, self.region_type, *region_types)
                    dropdown.pack(side=tk.LEFT, padx=10)
                    
                    # Buttons
                    tk.Button(control_frame, text="Clear Last", command=self.clear_last).pack(side=tk.LEFT, padx=5)
                    tk.Button(control_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
                    tk.Button(control_frame, text="Save Regions", command=self.save_regions).pack(side=tk.LEFT, padx=10)
                    
                    # Status
                    self.status_var = tk.StringVar(value="Ready to create regions")
                    tk.Label(control_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=20)
                
                def start_selection(self, event):
                    self.start_x = event.x
                    self.start_y = event.y
                    self.current_rect = self.canvas.create_rectangle(
                        self.start_x, self.start_y, self.start_x, self.start_y,
                        outline='red', width=2
                    )
                
                def update_selection(self, event):
                    if self.current_rect:
                        self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)
                
                def end_selection(self, event):
                    if self.current_rect and self.start_x is not None:
                        # Calculate region in original image coordinates
                        x1 = min(self.start_x, event.x) / self.scale_factor
                        y1 = min(self.start_y, event.y) / self.scale_factor
                        x2 = max(self.start_x, event.x) / self.scale_factor
                        y2 = max(self.start_y, event.y) / self.scale_factor
                        
                        # Convert to percentage coordinates
                        x_percent = (x1 / self.image_width) * 100
                        y_percent = (y1 / self.image_height) * 100
                        width_percent = ((x2 - x1) / self.image_width) * 100
                        height_percent = ((y2 - y1) / self.image_height) * 100
                        
                        # Store region
                        region_name = self.region_type.get()
                        self.regions[region_name] = {
                            'x': x_percent,
                            'y': y_percent,
                            'width': width_percent,
                            'height': height_percent
                        }
                        
                        # Update canvas rectangle color to indicate saved
                        self.canvas.itemconfig(self.current_rect, outline='green')
                        
                        # Add label
                        label_x = (self.start_x + event.x) / 2
                        label_y = min(self.start_y, event.y) - 10
                        self.canvas.create_text(label_x, label_y, text=region_name, fill='green', font=('Arial', 8))
                        
                        self.status_var.set(f"Added {region_name} - {len(self.regions)} regions total")
                        
                        # Auto-advance to next region type
                        self.auto_advance_region_type()
                        
                        self.current_rect = None
                        self.start_x = None
                        self.start_y = None
                
                def auto_advance_region_type(self):
                    """Automatically advance to the next logical region type"""
                    current = self.region_type.get()
                    
                    next_mapping = {
                        "community_card_1": "community_card_2",
                        "community_card_2": "community_card_3",
                        "community_card_3": "community_card_4",
                        "community_card_4": "community_card_5",
                        "community_card_5": "hero_card_1",
                        "hero_card_1": "hero_card_2",
                        "hero_card_2": "pot_area"
                    }
                    
                    if current in next_mapping:
                        self.region_type.set(next_mapping[current])
                
                def clear_last(self):
                    if self.regions:
                        last_region = list(self.regions.keys())[-1]
                        del self.regions[last_region]
                        self.redraw_regions()
                        self.status_var.set(f"Removed {last_region} - {len(self.regions)} regions remaining")
                
                def clear_all(self):
                    self.regions.clear()
                    self.redraw_regions()
                    self.status_var.set("All regions cleared")
                
                def redraw_regions(self):
                    # Clear canvas and redraw image
                    self.canvas.delete("all")
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
                    
                    # Redraw all regions
                    for region_name, region_data in self.regions.items():
                        x1 = (region_data['x'] / 100.0) * self.image_width * self.scale_factor
                        y1 = (region_data['y'] / 100.0) * self.image_height * self.scale_factor
                        x2 = x1 + (region_data['width'] / 100.0) * self.image_width * self.scale_factor
                        y2 = y1 + (region_data['height'] / 100.0) * self.image_height * self.scale_factor
                        
                        rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline='green', width=2)
                        label_x = (x1 + x2) / 2
                        label_y = y1 - 10
                        self.canvas.create_text(label_x, label_y, text=region_name, fill='green', font=('Arial', 8))
                
                def save_regions(self):
                    if not self.regions:
                        messagebox.showwarning("No Regions", "Please create at least one region before saving.")
                        return
                    
                    try:
                        import json
                        import os
                        
                        # Create regions directory if it doesn't exist
                        os.makedirs("regions", exist_ok=True)
                        
                        # Save to file
                        region_config = {
                            "regions": self.regions,
                            "created_timestamp": datetime.now().isoformat(),
                            "image_source": screenshot_filename,
                            "image_dimensions": {
                                "width": self.image_width,
                                "height": self.image_height
                            }
                        }
                        
                        config_filename = "regions/region_config_manual.json"
                        with open(config_filename, 'w') as f:
                            json.dump(region_config, f, indent=2)
                        
                        messagebox.showinfo("Success", f"Regions saved to {config_filename}")
                        print(f"✅ Regions saved to {config_filename}")
                        print(f"   Total regions: {len(self.regions)}")
                        
                        for name, data in self.regions.items():
                            print(f"   {name}: x={data['x']:.1f}%, y={data['y']:.1f}%, w={data['width']:.1f}%, h={data['height']:.1f}%")
                        
                        self.root.quit()
                        
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save regions: {e}")
                
                def run(self):
                    self.root.mainloop()
                    self.root.destroy()
            
            # Start the region creator
            creator = RegionCreator(screenshot_filename)
            creator.run()
            
        except ImportError:
            print("⚠️  GUI libraries not available for interactive region creator")
            print("   You can manually edit the regions file or use the manual calibrator")
        except Exception as e:
            print(f"❌ Error starting interactive region creator: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.virtual_camera:
            self.virtual_camera.release()
            print("🧹 Camera resources released")

def main():
    """Main function to capture table screenshot"""
    print("🎯 Poker Table Screenshot Capture Tool")
    print("=" * 50)
    print()
    print("This tool will:")
    print("  1. Connect to your OBS Virtual Camera")
    print("  2. Capture a screenshot of the current poker table")
    print("  3. Open an interactive region creator")
    print()
    print("Make sure before starting:")
    print("  ✓ OBS Studio is running")
    print("  ✓ Virtual Camera is started")
    print("  ✓ Poker table is visible with cards dealt")
    print("  ✓ All cards you want to detect are visible")
    print()
    
    input("Press Enter when ready to start...")
    
    try:
        # Create capture system
        capture = TableScreenshotCapture()
        
        # Capture screenshot
        result = capture.capture_table_screenshot()
        
        if result:
            frame, filename = result
            print(f"\n🎉 Screenshot captured successfully!")
            print(f"   File: {filename}")
            
            # Ask if user wants to use interactive region creator
            print(f"\n🎯 Would you like to create regions interactively?")
            response = input("   Press Enter for YES, or type 'no' to skip: ").strip().lower()
            
            if response != 'no':
                capture.interactive_region_creator(filename)
            else:
                print("\n📝 Manual region creation skipped")
                print(f"   You can manually edit 'regions/region_config.json'")
                print(f"   Or run the manual region calibrator later")
        else:
            print("\n❌ Failed to capture screenshot")
            print("   Check your OBS setup and try again")
        
        # Cleanup
        capture.cleanup()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Capture cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
