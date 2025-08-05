"""
Simple image checker for virtual camera captures
"""

import cv2
import numpy as np
import os
import glob

def check_latest_captures():
    """Check the latest virtual camera captures"""
    
    # Find all virtual camera captures
    pattern = "virtual_camera_capture_*.png"
    files = glob.glob(pattern)
    
    if not files:
        print("No virtual camera captures found")
        return
    
    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    
    print(f"Found {len(files)} virtual camera captures")
    
    # Check the latest 3 captures
    for i, filename in enumerate(files[:3]):
        print(f"\n📸 Checking: {filename}")
        
        # Get file info
        size = os.path.getsize(filename)
        print(f"   File size: {size} bytes")
        
        # Load and analyze image
        try:
            image = cv2.imread(filename)
            if image is None:
                print("   ❌ Failed to load image")
                continue
                
            print(f"   ✅ Image loaded: {image.shape}")
            
            # Check pixel values
            avg_pixel = np.mean(image)
            min_pixel = np.min(image)
            max_pixel = np.max(image)
            
            print(f"   Avg pixel: {avg_pixel:.2f}")
            print(f"   Min pixel: {min_pixel}")
            print(f"   Max pixel: {max_pixel}")
            
            # Check for content
            if avg_pixel < 5:
                print("   ⚠️ Mostly black image")
            elif avg_pixel > 250:
                print("   ⚠️ Mostly white image")
            else:
                print("   ✅ Has visible content")
                
            # Check for green (poker table)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_green = np.array([40, 40, 40])
            upper_green = np.array([80, 255, 255])
            green_mask = cv2.inRange(hsv, lower_green, upper_green)
            green_pixels = np.sum(green_mask > 0)
            
            if green_pixels > 1000:
                print(f"   🟢 Green detected: {green_pixels} pixels")
            else:
                print(f"   ❌ Little green: {green_pixels} pixels")
                
        except Exception as e:
            print(f"   ❌ Error analyzing image: {e}")

if __name__ == "__main__":
    check_latest_captures()
