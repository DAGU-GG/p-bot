#!/usr/bin/env python3
"""
Manual Region Calibration Tool
Click on card positions to create accurate region configuration
"""

import cv2
import json
import numpy as np
from typing import List, Tuple, Dict

class ManualRegionCalibrator:
    def __init__(self, image_path: str):
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        self.height, self.width = self.image.shape[:2]
        self.regions = {}
        self.current_region = None
        self.clicks = []
        
        # Region order for calibration
        self.region_order = [
            "community_card_1", "community_card_2", "community_card_3", 
            "community_card_4", "community_card_5",
            "hero_card_1", "hero_card_2"
        ]
        self.current_region_index = 0
        
        print(f"Manual Region Calibrator")
        print(f"Image: {self.width}x{self.height}")
        print(f"Instructions:")
        print(f"  1. Click TOP-LEFT corner of each card")
        print(f"  2. Click BOTTOM-RIGHT corner of each card") 
        print(f"  3. Press SPACE to skip a region")
        print(f"  4. Press ESC to finish")
        print(f"  5. Press 'r' to restart current region")
        print(f"")
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks for region selection"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.clicks.append((x, y))
            print(f"Click {len(self.clicks)}: ({x}, {y})")
            
            # Draw click point
            cv2.circle(self.image, (x, y), 5, (0, 255, 255), -1)
            
            if len(self.clicks) == 2:
                # Two clicks = complete region
                self.save_current_region()
                self.next_region()
    
    def save_current_region(self):
        """Save the current region based on two clicks"""
        if len(self.clicks) != 2:
            return
        
        region_name = self.region_order[self.current_region_index]
        
        # Get corners
        x1, y1 = self.clicks[0]
        x2, y2 = self.clicks[1]
        
        # Ensure correct order (top-left to bottom-right)
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        
        # Calculate region
        x, y = x_min, y_min
        w, h = x_max - x_min, y_max - y_min
        
        # Convert to percentages
        x_percent = (x / self.width) * 100
        y_percent = (y / self.height) * 100
        w_percent = (w / self.width) * 100
        h_percent = (h / self.height) * 100
        
        # Save region
        self.regions[region_name] = {
            'x': x_percent,
            'y': y_percent,
            'width': w_percent,
            'height': h_percent
        }
        
        print(f"✅ {region_name}: x={x_percent:.1f}%, y={y_percent:.1f}%, w={w_percent:.1f}%, h={h_percent:.1f}%")
        
        # Draw rectangle
        cv2.rectangle(self.image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(self.image, region_name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    def next_region(self):
        """Move to next region"""
        self.clicks = []
        self.current_region_index += 1
        
        if self.current_region_index < len(self.region_order):
            region_name = self.region_order[self.current_region_index]
            print(f"\\n📍 Click {region_name} (region {self.current_region_index + 1}/{len(self.region_order)})")
            print(f"   Click TOP-LEFT, then BOTTOM-RIGHT corner")
        else:
            print(f"\\n✅ All regions calibrated!")
            self.save_configuration()
    
    def restart_current_region(self):
        """Restart current region"""
        self.clicks = []
        if self.current_region_index < len(self.region_order):
            region_name = self.region_order[self.current_region_index]
            print(f"\\n🔄 Restarting {region_name}")
            print(f"   Click TOP-LEFT, then BOTTOM-RIGHT corner")
    
    def skip_current_region(self):
        """Skip current region"""
        if self.current_region_index < len(self.region_order):
            region_name = self.region_order[self.current_region_index]
            print(f"⏭️ Skipped {region_name}")
            self.next_region()
    
    def save_configuration(self):
        """Save the calibrated regions to JSON"""
        config = {
            "regions": self.regions,
            "timestamp": "2025-08-05 manually calibrated",
            "version": "1.0",
            "image_dimensions": {
                "width": self.width,
                "height": self.height
            }
        }
        
        output_file = "regions/region_config_manual.json"
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\\n💾 Saved manual calibration to: {output_file}")
        print(f"📊 Calibrated {len(self.regions)} regions")
        
        # Test regions
        self.test_regions()
    
    def test_regions(self):
        """Test the calibrated regions"""
        print(f"\\n🧪 Testing calibrated regions...")
        
        for region_name, region_data in self.regions.items():
            # Convert to pixels
            x = int((region_data['x'] / 100.0) * self.width)
            y = int((region_data['y'] / 100.0) * self.height)
            w = int((region_data['width'] / 100.0) * self.width)
            h = int((region_data['height'] / 100.0) * self.height)
            
            # Extract region
            region_img = self.image[y:y+h, x:x+w]
            
            # Save test image
            cv2.imwrite(f"manual_region_{region_name}.png", region_img)
            
            # Check color
            avg_color = np.mean(region_img, axis=(0,1))
            print(f"  {region_name}: BGR({avg_color[0]:.0f}, {avg_color[1]:.0f}, {avg_color[2]:.0f}) -> manual_region_{region_name}.png")
    
    def run(self):
        """Run the manual calibration interface"""
        # Start with first region
        if self.region_order:
            region_name = self.region_order[0]
            print(f"📍 Click {region_name} (region 1/{len(self.region_order)})")
            print(f"   Click TOP-LEFT, then BOTTOM-RIGHT corner")
        
        # Set up window
        cv2.namedWindow("Manual Region Calibrator", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Manual Region Calibrator", self.mouse_callback)
        
        while True:
            # Display image
            cv2.imshow("Manual Region Calibrator", self.image)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                break
            elif key == ord(' '):  # SPACE - skip region
                self.skip_current_region()
            elif key == ord('r'):  # R - restart current region
                self.restart_current_region()
            elif key == ord('s'):  # S - save current progress
                if self.regions:
                    self.save_configuration()
        
        cv2.destroyAllWindows()

def main():
    """Main function"""
    # Try to load the most recent capture
    image_files = [
        "test_enhanced_capture_1754352826.png",
        "virtual_camera_capture_latest.png",
        "calibration_screenshot.png"
    ]
    
    image_path = None
    for img_file in image_files:
        try:
            img = cv2.imread(img_file)
            if img is not None:
                image_path = img_file
                break
        except:
            continue
    
    if image_path is None:
        print("❌ No suitable image found for calibration")
        print("Available images to try:")
        for img_file in image_files:
            print(f"  - {img_file}")
        return
    
    print(f"🖼️ Using image: {image_path}")
    
    try:
        calibrator = ManualRegionCalibrator(image_path)
        calibrator.run()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
