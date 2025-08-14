#!/usr/bin/env python3
"""
Comprehensive Region Calibration Tool for Smart Poker Bot
Allows manual selection of all OCR regions with visual feedback
"""

import cv2
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pyautogui
import datetime

@dataclass
class RegionInfo:
    name: str
    description: str
    color: Tuple[int, int, int]  # BGR color for OpenCV
    required: bool = True

class RegionCalibrator:
    WINDOW_NAME = 'Poker Bot Region Calibrator'
    
    def __init__(self):
        self.regions = {}
        self.current_region = None
        self.drawing = False
        self.start_point = None
        self.temp_rect = None
        self.screenshot = None
        self.display_image = None
        
        # Define all regions we want to calibrate
        self.region_definitions = [
            # Essential regions
            RegionInfo("hero_card_1", "Hero Card 1 (your first hole card)", (0, 255, 0), True),
            RegionInfo("hero_card_2", "Hero Card 2 (your second hole card)", (0, 255, 0), True),
            RegionInfo("community_card_1", "Community Card 1 (flop left)", (0, 255, 255), True),
            RegionInfo("community_card_2", "Community Card 2 (flop middle)", (0, 255, 255), True),
            RegionInfo("community_card_3", "Community Card 3 (flop right)", (0, 255, 255), True),
            RegionInfo("community_card_4", "Community Card 4 (turn)", (0, 255, 255), True),
            RegionInfo("community_card_5", "Community Card 5 (river)", (0, 255, 255), True),
            RegionInfo("pot", "Main pot amount", (255, 0, 0), True),
            
            # Table structure
            RegionInfo("table_bounds", "Poker table area (green felt)", (128, 128, 128), True),
            
            # Optional regions
            RegionInfo("action_buttons", "Action buttons area (Call/Raise/Fold)", (255, 255, 0), False),
            RegionInfo("player_1_stack", "Player 1 stack amount", (255, 0, 255), False),
            RegionInfo("player_2_stack", "Player 2 stack amount", (255, 0, 255), False),
            RegionInfo("player_3_stack", "Player 3 stack amount", (255, 0, 255), False),
            RegionInfo("player_4_stack", "Player 4 stack amount", (255, 0, 255), False),
            RegionInfo("player_5_stack", "Player 5 stack amount", (255, 0, 255), False),
            RegionInfo("dealer_button", "Dealer button position", (0, 128, 255), False),
        ]
        
        self.current_region_index = 0
        self.instructions_visible = True
        
    def list_available_cameras(self):
        """List all available camera devices"""
        print("🔍 Scanning for available cameras...")
        available_cameras = []
        
        for i in range(5):  # Check first 5 camera indices
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    ret, frame = cap.read()
                    cap.release()
                    
                    if ret and frame is not None:
                        available_cameras.append((i, width, height))
                        print(f"   Camera {i}: {width}x{height} ✅")
                    else:
                        print(f"   Camera {i}: Found but no frame ❌")
                else:
                    print(f"   Camera {i}: Not available ❌")
            except Exception as e:
                print(f"   Camera {i}: Error - {e}")
        
        return available_cameras
    
    def take_screenshot(self) -> np.ndarray:
        """Take a screenshot from OBS Virtual Camera"""
        print("📸 Attempting to capture from OBS Virtual Camera...")
        
        # Try different camera indices
        for camera_index in [0, 1, 2]:
            try:
                print(f"   Trying camera index {camera_index}...")
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                
                if cap.isOpened():
                    # Set preferred resolution
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                    
                    # Get actual resolution
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    # Try to read a frame
                    ret, frame = cap.read()
                    cap.release()
                    
                    if ret and frame is not None:
                        print(f"✅ Successfully captured from camera {camera_index}")
                        print(f"   Resolution: {width}x{height}")
                        print(f"   Frame shape: {frame.shape}")
                        
                        # Check if this looks like OBS (should be 1920x1080 or close)
                        if width >= 1280 and height >= 720:
                            print("🎯 This appears to be OBS Virtual Camera!")
                            return frame
                        else:
                            print(f"⚠️ Camera {camera_index} resolution too low ({width}x{height})")
                    else:
                        print(f"❌ Could not read frame from camera {camera_index}")
                else:
                    print(f"❌ Could not open camera {camera_index}")
                    
            except Exception as e:
                print(f"⚠️ Error with camera {camera_index}: {e}")
        
        print("\n❌ Could not find OBS Virtual Camera!")
        print("Please ensure:")
        print("   1. OBS Studio is running")
        print("   2. Virtual Camera is started in OBS")
        print("   3. A scene with poker content is active")
        
        response = input("\nWould you like to take a desktop screenshot instead? (y/n): ")
        if response.lower() == 'y':
            print("📸 Taking desktop screenshot...")
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot
        else:
            return None
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for region selection"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.temp_rect = (self.start_point, (x, y))
                self.update_display()
                
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing and self.start_point:
                end_point = (x, y)
                self.drawing = False
                
                # Calculate region coordinates
                x1, y1 = self.start_point
                x2, y2 = end_point
                
                # Ensure top-left and bottom-right are correct
                left = min(x1, x2)
                top = min(y1, y2)
                right = max(x1, x2)
                bottom = max(y1, y2)
                
                # Store the region
                if right > left and bottom > top:  # Valid rectangle
                    region_info = self.region_definitions[self.current_region_index]
                    self.regions[region_info.name] = {
                        'x': left,
                        'y': top,
                        'width': right - left,
                        'height': bottom - top
                    }
                    
                    print(f"✅ Saved {region_info.name}: ({left}, {top}, {right-left}, {bottom-top})")
                    
                    # Move to next region
                    self.next_region()
                
                self.temp_rect = None
                self.update_display()
    
    def next_region(self):
        """Move to the next region to calibrate"""
        self.current_region_index += 1
        if self.current_region_index >= len(self.region_definitions):
            print("🎉 All regions calibrated!")
            self.save_regions()
            return False
        return True
    
    def skip_region(self):
        """Skip the current region (for optional regions)"""
        region_info = self.region_definitions[self.current_region_index]
        if not region_info.required:
            print(f"⏭️ Skipped optional region: {region_info.name}")
            return self.next_region()
        else:
            print(f"❌ Cannot skip required region: {region_info.name}")
            return True
    
    def previous_region(self):
        """Go back to previous region"""
        if self.current_region_index > 0:
            self.current_region_index -= 1
            # Remove the current region from saved regions
            region_info = self.region_definitions[self.current_region_index]
            if region_info.name in self.regions:
                del self.regions[region_info.name]
            print(f"⬅️ Back to: {region_info.name}")
            self.update_display()
    
    def update_display(self):
        """Update the display image with current regions and instructions"""
        try:
            self.display_image = self.screenshot.copy()
            
            # Draw all completed regions
            for region_name, coords in self.regions.items():
                # Find the region definition for color
                region_def = next((r for r in self.region_definitions if r.name == region_name), None)
                if region_def:
                    color = region_def.color
                    x, y, w, h = coords['x'], coords['y'], coords['width'], coords['height']
                    cv2.rectangle(self.display_image, (x, y), (x + w, y + h), color, 2)
                    
                    # Add label
                    label_y = y - 10 if y > 20 else y + h + 20
                    cv2.putText(self.display_image, region_name, (x, label_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Draw temporary rectangle being drawn
            if self.temp_rect and self.current_region_index < len(self.region_definitions):
                region_info = self.region_definitions[self.current_region_index]
                color = region_info.color
                pt1, pt2 = self.temp_rect
                cv2.rectangle(self.display_image, pt1, pt2, color, 2)
            
            # Add instructions overlay
            if self.instructions_visible:
                self.draw_instructions()
            
            cv2.imshow(self.WINDOW_NAME, self.display_image)
            
        except Exception as e:
            print(f"⚠️ Error updating display: {e}")
    
    def draw_instructions(self):
        """Draw instructions on the display"""
        if self.current_region_index >= len(self.region_definitions):
            return
            
        region_info = self.region_definitions[self.current_region_index]
        
        # Create semi-transparent overlay for instructions
        overlay = self.display_image.copy()
        
        # Instructions background
        cv2.rectangle(overlay, (10, 10), (700, 220), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, self.display_image, 0.2, 0, self.display_image)
        
        # Current region info
        y_offset = 35
        region_text = f"Region {self.current_region_index + 1}/{len(self.region_definitions)}: {region_info.name}"
        cv2.putText(self.display_image, region_text, 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        y_offset += 25
        cv2.putText(self.display_image, region_info.description, 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        y_offset += 35
        
        # Instructions
        instructions = [
            "• Click and drag to select region",
            "• Press 'n' to skip (optional regions only)", 
            "• Press 'b' to go back",
            "• Press 'h' to toggle help",
            "• Press 'r' to retake screenshot",
            "• Press 's' to save and exit",
            "• Press 'q' to quit without saving"
        ]
        
        for instruction in instructions:
            cv2.putText(self.display_image, instruction, (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            y_offset += 20
        
        # Show region color and status
        color_rect = (600, 35, 620, 55)
        cv2.rectangle(self.display_image, color_rect[0:2], color_rect[2:4], region_info.color, -1)
        
        status = "Required" if region_info.required else "Optional"
        cv2.putText(self.display_image, status, (630, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, region_info.color, 1)
    
    def save_regions(self):
        """Save calibrated regions to file"""
        output_file = "calibrated_regions.json"
        
        # Create a comprehensive regions structure
        regions_data = {
            "metadata": {
                "version": "1.0",
                "calibrated_at": datetime.datetime.now().isoformat(),
                "screen_resolution": f"{self.screenshot.shape[1]}x{self.screenshot.shape[0]}",
                "total_regions": len(self.regions)
            },
            "regions": self.regions
        }
        
        with open(output_file, 'w') as f:
            json.dump(regions_data, f, indent=2)
        
        print(f"💾 Regions saved to {output_file}")
        
        # Also save a backup with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"calibrated_regions_backup_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(regions_data, f, indent=2)
        
        print(f"💾 Backup saved to {backup_file}")
        
        # Save to the legacy filename that the bot expects
        legacy_file = "live_calibrated_regions.json"
        with open(legacy_file, 'w') as f:
            json.dump(self.regions, f, indent=2)
        print(f"💾 Legacy format saved to {legacy_file}")
        
        # Print summary
        print("\n📊 Calibration Summary:")
        print(f"   Total regions: {len(self.regions)}")
        required_count = sum(1 for r in self.region_definitions if r.required and r.name in self.regions)
        optional_count = len(self.regions) - required_count
        print(f"   Required: {required_count}")
        print(f"   Optional: {optional_count}")
        
        for name, coords in self.regions.items():
            print(f"   • {name}: ({coords['x']}, {coords['y']}, {coords['width']}, {coords['height']})")
    
    def run(self):
        """Main calibration loop"""
        print("🎯 Smart Poker Bot - Comprehensive Region Calibrator")
        print("=" * 60)
        
        # List available cameras first
        available_cameras = self.list_available_cameras()
        
        if not available_cameras:
            print("\n❌ No cameras found!")
            print("Please ensure OBS Virtual Camera is running.")
            return
        
        print(f"\n📹 Found {len(available_cameras)} camera(s)")
        for i, (idx, w, h) in enumerate(available_cameras):
            camera_type = "OBS Virtual Camera" if w >= 1280 and h >= 720 else "Regular Camera"
            print(f"   Camera {idx}: {w}x{h} ({camera_type})")
        
        # Take initial screenshot
        self.screenshot = self.take_screenshot()
        if self.screenshot is None:
            print("❌ Failed to take screenshot!")
            return
        
        print(f"📐 Screenshot size: {self.screenshot.shape[1]}x{self.screenshot.shape[0]}")
        print("\n🎮 Starting calibration...")
        print("   Position your poker table and start selecting regions!")
        print("   Make sure to have some cards visible for accurate calibration.")
        
        # Setup window
        try:
            cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.WINDOW_NAME, 1400, 900)
            cv2.setMouseCallback(self.WINDOW_NAME, self.mouse_callback)
            
            self.update_display()
            
            print("\n🎮 Calibration window opened!")
            print("Controls:")
            print("  • Click and drag to select regions")
            print("  • 'n' to skip optional regions")
            print("  • 'b' to go back")
            print("  • 'h' to toggle help")
            print("  • 'r' to retake screenshot")
            print("  • 's' to save and exit")
            print("  • 'q' to quit")
            
            while True:
                try:
                    key = cv2.waitKey(1) & 0xFF
                    
                    if key == ord('q'):
                        print("👋 Calibration cancelled")
                        break
                    elif key == ord('n'):
                        if not self.skip_region():
                            break
                    elif key == ord('b'):
                        self.previous_region()
                    elif key == ord('h'):
                        self.instructions_visible = not self.instructions_visible
                        self.update_display()
                    elif key == ord('r'):
                        print("📸 Retaking screenshot...")
                        new_screenshot = self.take_screenshot()
                        if new_screenshot is not None:
                            self.screenshot = new_screenshot
                            self.update_display()
                    elif key == ord('s'):
                        print("💾 Saving current regions...")
                        self.save_regions()
                        break
                    elif self.current_region_index >= len(self.region_definitions):
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error in main loop: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Error setting up window: {e}")
            return
        
        finally:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        
        if len(self.regions) > 0:
            print(f"\n✅ Calibration complete! {len(self.regions)} regions saved.")
            print("🚀 You can now run the poker bot with the new regions!")
        else:
            print("\n❌ No regions were calibrated.")

def main():
    """Main entry point"""
    print("🃏 Welcome to the Smart Poker Bot Region Calibrator!")
    print("\n📋 This tool will help you calibrate the following regions:")
    print("   • Hero cards (your 2 hole cards)")
    print("   • Community cards (5 cards)")
    print("   • Pot amount")
    print("   • Table bounds")
    print("   • Optional: Action buttons, player stacks, etc.")
    print("\n💡 Tips:")
    print("   • Have a poker hand active while calibrating")
    print("   • Draw tight rectangles around just the card/text content")
    print("   • You can skip optional regions if not needed")
    print("   • Use 'b' to go back if you make a mistake")
    
    input("\nPress Enter to start calibration...")
    
    calibrator = RegionCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()
