"""
Create Regions from Latest Screenshot
Uses the latest poker table screenshot to create regions
"""

import cv2
import json
import os
from datetime import datetime

def create_regions_from_screenshot():
    """Create regions by clicking on the latest screenshot"""
    
    # Find the latest screenshot
    screenshot_file = "poker_table_for_regions_20250805_023128.png"
    
    if not os.path.exists(screenshot_file):
        print(f"❌ Screenshot not found: {screenshot_file}")
        print("Run 'python simple_screenshot.py' first to capture a screenshot")
        return
    
    print(f"🖼️ Using screenshot: {screenshot_file}")
    print()
    print("🎯 Manual Region Creation")
    print("=" * 30)
    print()
    print("Instructions:")
    print("  1. The image will open showing your poker table")
    print("  2. Click on each card position when prompted")
    print("  3. Click the TOP-LEFT corner of each card")
    print("  4. Card regions will be auto-sized from your click")
    print()
    print("Card order:")
    print("  - Community Card 1 (leftmost flop card)")
    print("  - Community Card 2 (middle flop card)")  
    print("  - Community Card 3 (rightmost flop card)")
    print("  - Community Card 4 (turn card)")
    print("  - Community Card 5 (river card)")
    print("  - Hero Card 1 (your left card)")
    print("  - Hero Card 2 (your right card)")
    print()
    
    input("Press Enter to start clicking on card positions...")
    
    # Load image
    image = cv2.imread(screenshot_file)
    if image is None:
        print(f"❌ Could not load image: {screenshot_file}")
        return
    
    height, width = image.shape[:2]
    print(f"📐 Image size: {width}x{height}")
    
    # Card positions to collect
    card_positions = [
        "community_card_1",
        "community_card_2", 
        "community_card_3",
        "community_card_4",
        "community_card_5",
        "hero_card_1",
        "hero_card_2"
    ]
    
    regions = {}
    clicks = []
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            clicks.append((x, y))
            print(f"✅ Click {len(clicks)}: ({x}, {y})")
            
            # Draw a mark where clicked
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(image, f"{len(clicks)}", (x+10, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Click on Cards", image)
    
    # Set up window and mouse callback
    cv2.namedWindow("Click on Cards", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Click on Cards", 1200, 675)  # Scale down for easier viewing
    cv2.setMouseCallback("Click on Cards", mouse_callback)
    cv2.imshow("Click on Cards", image)
    
    print(f"\n🖱️ Click on each card position in order:")
    
    current_card = 0
    while current_card < len(card_positions) and len(clicks) <= current_card:
        card_name = card_positions[current_card]
        print(f"  📍 Click on: {card_name}")
        
        # Wait for click
        while len(clicks) <= current_card:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("❌ Cancelled by user")
                cv2.destroyAllWindows()
                return
        
        # Process the click
        x, y = clicks[current_card]
        
        # Standard card size (adjust these if needed)
        card_width = 60   # pixels
        card_height = 84  # pixels
        
        # Create region from click point
        regions[card_name] = {
            "x": (x / width) * 100,  # Convert to percentage
            "y": (y / height) * 100,
            "width": (card_width / width) * 100,
            "height": (card_height / height) * 100
        }
        
        # Draw the region on image
        x2 = x + card_width
        y2 = y + card_height
        cv2.rectangle(image, (x, y), (x2, y2), (255, 0, 0), 2)
        cv2.putText(image, card_name, (x, y-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        cv2.imshow("Click on Cards", image)
        
        print(f"    ✅ {card_name}: x={regions[card_name]['x']:.1f}%, y={regions[card_name]['y']:.1f}%")
        current_card += 1
    
    cv2.destroyAllWindows()
    
    if len(regions) == len(card_positions):
        # Save regions
        os.makedirs("regions", exist_ok=True)
        
        region_config = {
            "regions": regions,
            "created_timestamp": datetime.now().isoformat(),
            "source_image": screenshot_file,
            "image_dimensions": {"width": width, "height": height},
            "method": "manual_click"
        }
        
        config_file = "regions/region_config_manual.json"
        with open(config_file, 'w') as f:
            json.dump(region_config, f, indent=2)
        
        print(f"\n✅ SUCCESS! Regions saved to: {config_file}")
        print(f"   Total regions created: {len(regions)}")
        
        # Also update the main config file
        main_config_file = "regions/region_config.json"
        with open(main_config_file, 'w') as f:
            json.dump(region_config, f, indent=2)
        print(f"✅ Also saved to: {main_config_file}")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Test regions: python test_enhanced_integration.py")
        print(f"   2. Run full system: python hardware_capture_integration.py")
        
        return True
    else:
        print(f"\n❌ Incomplete region creation")
        print(f"   Expected {len(card_positions)} regions, got {len(regions)}")
        return False

if __name__ == "__main__":
    create_regions_from_screenshot()
