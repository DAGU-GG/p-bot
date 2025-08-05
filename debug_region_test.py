#!/usr/bin/env python3
"""
Debug Region Test - Test region extraction and OCR debug images
"""

import cv2
import json
import numpy as np
import time
from hardware_capture_integration import HardwareCaptureSystem

def test_debug_regions():
    """Test region extraction and debug image generation"""
    print("🧪 Testing Region Extraction and Debug Images...")
    
    # Initialize hardware capture system
    capture_system = HardwareCaptureSystem()
    
    # Connect to virtual camera
    if not capture_system.connect_to_virtual_camera():
        print("❌ Failed to connect to virtual camera")
        return
    
    # Get current frame
    frame = capture_system.capture_from_virtual_camera()
    if frame is None:
        print("❌ Failed to capture frame")
        return
    
    print(f"✅ Captured frame: {frame.shape}")
    
    # Load regions manually for verification
    try:
        with open('regions/region_config.json', 'r') as f:
            region_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load region config: {e}")
        return
    
    height, width = frame.shape[:2]
    print(f"📐 Frame dimensions: {width}x{height}")
    
    # Test each card region
    for region_name, region_info in region_data['regions'].items():
        if 'hero_card' in region_name or 'community_card' in region_name:
            # Convert percentage to pixels
            x_pixel = int((region_info['x'] / 100.0) * width)
            y_pixel = int((region_info['y'] / 100.0) * height)
            w_pixel = int((region_info['width'] / 100.0) * width)
            h_pixel = int((region_info['height'] / 100.0) * height)
            
            print(f"\n🎯 Testing {region_name}")
            print(f"   Coordinates: x={x_pixel}, y={y_pixel}, w={w_pixel}, h={h_pixel}")
            
            # Extract region
            region_img = frame[y_pixel:y_pixel+h_pixel, x_pixel:x_pixel+w_pixel]
            
            # Save region for verification
            region_filename = f"test_region_{region_name}_{int(time.time())}.png"
            cv2.imwrite(region_filename, region_img)
            print(f"   💾 Saved region: {region_filename} ({region_img.shape})")
            
            # Test card recognition on this specific region
            try:
                result = capture_system.recognize_card_from_region(region_img, region_name)
                if result:
                    print(f"   🃏 Recognition: {result['rank']}{result['suit']} ({result['method']}, {result['confidence']:.2f})")
                else:
                    print(f"   ❌ No card recognized")
            except Exception as e:
                print(f"   ⚠️ Recognition error: {e}")

if __name__ == "__main__":
    test_debug_regions()
