#!/usr/bin/env python3
"""
Visual Region Validator - Shows exactly what regions are capturing
"""

import cv2
import numpy as np
import os
import sys
import json

# Add src to path
sys.path.append('src')

def create_region_overlay():
    """Create a visual overlay showing what regions are capturing."""
    
    print("=== Creating Visual Region Overlay ===")
    
    # Load latest screenshot
    screenshots = []
    if os.path.exists('screenshots'):
        screenshots = [f for f in os.listdir('screenshots') if f.endswith('.png')]
        screenshots.sort(key=lambda x: os.path.getmtime(f'screenshots/{x}'), reverse=True)
    
    if not screenshots:
        print("❌ No screenshots found")
        return
    
    latest_screenshot = f'screenshots/{screenshots[0]}'
    image = cv2.imread(latest_screenshot)
    if image is None:
        print("❌ Could not load screenshot")
        return
    
    height, width = image.shape[:2]
    overlay = image.copy()
    
    # Load regions
    try:
        with open('regions/region_config.json', 'r') as f:
            config = json.load(f)
        regions = config['regions']
        
        # Draw hero card regions
        for i, card_name in enumerate(['hero_card_1', 'hero_card_2']):
            if card_name in regions:
                region = regions[card_name]
                x = int(width * region['x'] / 100.0)
                y = int(height * region['y'] / 100.0)
                w = int(width * region['width'] / 100.0)
                h = int(height * region['height'] / 100.0)
                
                # Draw rectangle
                color = (0, 255, 0) if i == 0 else (0, 255, 255)  # Green for card1, Yellow for card2
                cv2.rectangle(overlay, (x, y), (x+w, y+h), color, 3)
                cv2.putText(overlay, f"Hero {i+1}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw community card regions
        for i in range(1, 6):
            card_name = f'community_card_{i}'
            if card_name in regions:
                region = regions[card_name]
                x = int(width * region['x'] / 100.0)
                y = int(height * region['y'] / 100.0)
                w = int(width * region['width'] / 100.0)
                h = int(height * region['height'] / 100.0)
                
                # Draw rectangle
                color = (255, 0, 0)  # Blue for community
                cv2.rectangle(overlay, (x, y), (x+w, y+h), color, 2)
                cv2.putText(overlay, f"C{i}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Save overlay
        output_file = "debug_region_overlay.png"
        cv2.imwrite(output_file, overlay)
        print(f"✅ Region overlay saved to: {output_file}")
        print("📋 Check this file to see if regions are positioned correctly over the cards")
        
        # Also create a side-by-side comparison
        combined = np.hstack([image, overlay])
        combined_file = "debug_region_comparison.png"
        cv2.imwrite(combined_file, combined)
        print(f"✅ Comparison saved to: {combined_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_region_overlay()
