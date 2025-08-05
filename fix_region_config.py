#!/usr/bin/env python3
"""
Fix Region Configuration
Update the problematic region coordinates based on actual card positions
"""

import json
import cv2
import numpy as np

def fix_region_configuration():
    """Fix the region configuration with corrected coordinates"""
    
    # Load current configuration
    with open('regions/region_config.json', 'r') as f:
        config = json.load(f)
    
    # The working regions (community cards 1-3) as reference
    working_regions = {
        'community_card_1': config['regions']['community_card_1'],  # x=40.2%, y=32.8%
        'community_card_2': config['regions']['community_card_2'],  # x=44.2%, y=33.1%  
        'community_card_3': config['regions']['community_card_3'],  # x=48.1%, y=33.1%
    }
    
    print("Working regions (reference):")
    for name, region in working_regions.items():
        print(f"  {name}: x={region['x']:.1f}%, y={region['y']:.1f}%")
    
    # Calculate spacing between community cards
    spacing_1_to_2 = working_regions['community_card_2']['x'] - working_regions['community_card_1']['x']  # ~4%
    spacing_2_to_3 = working_regions['community_card_3']['x'] - working_regions['community_card_2']['x']  # ~4%
    avg_spacing = (spacing_1_to_2 + spacing_2_to_3) / 2
    
    print(f"Average spacing between community cards: {avg_spacing:.1f}%")
    
    # Extrapolate positions for community cards 4 and 5
    card_4_x = working_regions['community_card_3']['x'] + avg_spacing
    card_5_x = card_4_x + avg_spacing
    
    # Use similar y-position and dimensions as card 3
    card_y = working_regions['community_card_3']['y']
    card_width = working_regions['community_card_3']['width'] 
    card_height = working_regions['community_card_3']['height']
    
    # For hero cards, position them in typical poker positions (bottom center)
    # Based on poker table layouts, hero cards are usually around y=65-75% and centered horizontally
    hero_y = 70.0  # Lower on table (70% down)
    hero_card_width = 4.0  # Slightly wider than community cards
    hero_card_height = 8.0  # Appropriate height
    
    # Center hero cards around the table center (50%)
    hero_spacing = 5.0  # Space between hero cards
    hero_1_x = 45.0  # Left hero card
    hero_2_x = hero_1_x + hero_spacing  # Right hero card
    
    # Create corrected configuration
    corrected_regions = config.copy()
    
    # Fix community cards 4 and 5
    corrected_regions['regions']['community_card_4'] = {
        'x': card_4_x,
        'y': card_y,
        'width': card_width,
        'height': card_height
    }
    
    corrected_regions['regions']['community_card_5'] = {
        'x': card_5_x, 
        'y': card_y,
        'width': card_width,
        'height': card_height
    }
    
    # Fix hero cards
    corrected_regions['regions']['hero_card_1'] = {
        'x': hero_1_x,
        'y': hero_y,
        'width': hero_card_width,
        'height': hero_card_height
    }
    
    corrected_regions['regions']['hero_card_2'] = {
        'x': hero_2_x,
        'y': hero_y, 
        'width': hero_card_width,
        'height': hero_card_height
    }
    
    # Update timestamp
    corrected_regions['timestamp'] = "2025-08-05 02:20:00 (manually corrected)"
    
    print("\nCorrected regions:")
    for name, region in corrected_regions['regions'].items():
        if name in ['community_card_4', 'community_card_5', 'hero_card_1', 'hero_card_2']:
            print(f"  {name}: x={region['x']:.1f}%, y={region['y']:.1f}%, w={region['width']:.1f}%, h={region['height']:.1f}%")
    
    # Save corrected configuration
    with open('regions/region_config_corrected.json', 'w') as f:
        json.dump(corrected_regions, f, indent=2)
    
    print(f"\n✅ Saved corrected configuration to: regions/region_config_corrected.json")
    
    # Test the corrected regions on current image
    test_corrected_regions(corrected_regions)

def test_corrected_regions(config):
    """Test the corrected regions on the current test image"""
    
    # Load test image
    img = cv2.imread('test_enhanced_capture_1754352826.png')
    if img is None:
        print("❌ Could not load test image")
        return
    
    height, width = img.shape[:2]
    print(f"\n🧪 Testing corrected regions on image {width}x{height}")
    
    # Test only the corrected regions
    test_regions = ['community_card_4', 'community_card_5', 'hero_card_1', 'hero_card_2']
    
    for region_name in test_regions:
        region = config['regions'][region_name]
        
        # Convert to pixels
        x = int((region['x'] / 100.0) * width)
        y = int((region['y'] / 100.0) * height)
        w = int((region['width'] / 100.0) * width)
        h = int((region['height'] / 100.0) * height)
        
        # Extract region
        region_img = img[y:y+h, x:x+w]
        
        # Check average color
        avg_color = np.mean(region_img, axis=(0,1))
        
        # Save for inspection
        cv2.imwrite(f'corrected_region_{region_name}.png', region_img)
        
        print(f"  {region_name}: x={x}, y={y}, w={w}, h={h}")
        print(f"    Average color: BGR({avg_color[0]:.0f}, {avg_color[1]:.0f}, {avg_color[2]:.0f})")
        print(f"    Saved: corrected_region_{region_name}.png")

if __name__ == "__main__":
    fix_region_configuration()
