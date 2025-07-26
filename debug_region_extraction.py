#!/usr/bin/env python3
"""
Debug script to test region extraction and see what's being captured
"""

import cv2
import numpy as np
import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.append('src')

def test_region_extraction():
    """Test if regions are being extracted correctly."""
    
    print("=== Region Extraction Debug ===")
    
    # Check if we have a recent screenshot
    screenshots = []
    if os.path.exists('screenshots'):
        screenshots = [f for f in os.listdir('screenshots') if f.endswith('.png')]
        screenshots.sort(key=lambda x: os.path.getmtime(f'screenshots/{x}'), reverse=True)
    
    if not screenshots:
        print("❌ No screenshots found in screenshots/ folder")
        return
    
    latest_screenshot = f'screenshots/{screenshots[0]}'
    print(f"📸 Using latest screenshot: {latest_screenshot}")
    
    # Load screenshot
    image = cv2.imread(latest_screenshot)
    if image is None:
        print("❌ Could not load screenshot")
        return
    
    height, width = image.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    # Load regions from config
    try:
        with open('regions/region_config.json', 'r') as f:
            config = json.load(f)
        
        regions = config['regions']
        print(f"📋 Loaded {len(regions)} regions from config")
        
        # Test hero card extraction
        for i, card_name in enumerate(['hero_card_1', 'hero_card_2'], 1):
            if card_name in regions:
                region = regions[card_name]
                
                # Convert to pixels (values are already in decimal, not percentage)
                x = int(width * region['x'])
                y = int(height * region['y'])
                w = int(width * region['width'])
                h = int(height * region['height'])
                
                print(f"\n🎯 {card_name}:")
                print(f"  Raw region: {region}")
                print(f"  Pixel coords: x={x}, y={y}, w={w}, h={h}")
                
                # Extract region
                if y+h <= height and x+w <= width and x >= 0 and y >= 0:
                    card_region = image[y:y+h, x:x+w]
                    
                    if card_region.size > 0:
                        # Save extracted region for analysis
                        timestamp = int(datetime.now().timestamp())
                        debug_filename = f"debug_cards/extracted_{card_name}_{timestamp}.png"
                        cv2.imwrite(debug_filename, card_region)
                        print(f"  ✅ Extracted and saved to: {debug_filename}")
                        
                        # Analyze the extracted region
                        gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
                        mean_brightness = np.mean(gray)
                        std_brightness = np.std(gray)
                        min_val, max_val = np.min(gray), np.max(gray)
                        
                        print(f"  📊 Analysis:")
                        print(f"    Size: {card_region.shape}")
                        print(f"    Brightness: mean={mean_brightness:.1f}, std={std_brightness:.1f}")
                        print(f"    Range: {min_val}-{max_val}")
                        
                        # Check if this looks like a card
                        if mean_brightness < 30:
                            print(f"    ⚠️  Very dark - might be capturing wrong area")
                        elif mean_brightness > 200:
                            print(f"    ⚠️  Very bright - might be capturing background")
                        elif std_brightness < 15:
                            print(f"    ⚠️  Low contrast - might be blurry or uniform area")
                        else:
                            print(f"    ✅ Looks reasonable for card recognition")
                            
                    else:
                        print(f"  ❌ Extracted region is empty")
                else:
                    print(f"  ❌ Region coordinates out of bounds")
            else:
                print(f"❌ {card_name} not found in regions")
        
        # Test community cards too
        print(f"\n🃏 Community Cards:")
        for i in range(1, 6):
            card_name = f'community_card_{i}'
            if card_name in regions:
                region = regions[card_name]
                x = int(width * region['x'])
                y = int(height * region['y'])
                w = int(width * region['width'])
                h = int(height * region['height'])
                
                if y+h <= height and x+w <= width and x >= 0 and y >= 0:
                    print(f"  {card_name}: x={x}, y={y}, w={w}, h={h} ✅")
                else:
                    print(f"  {card_name}: OUT OF BOUNDS ❌")
                    
    except Exception as e:
        print(f"❌ Error loading regions: {e}")

if __name__ == "__main__":
    test_region_extraction()
