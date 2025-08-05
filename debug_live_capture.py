"""
Live Capture Debug Tool
Shows exactly what the bot is seeing and analyzing
"""

import cv2
import numpy as np
import time
import logging
from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
import json

def debug_live_capture():
    """Debug what the bot is actually seeing"""
    print("🔍 Live Capture Debug Tool")
    print("=" * 40)
    
    # Initialize system
    config = HardwareCaptureConfig(debug_mode=True)
    capture_system = HardwareCaptureSystem(config)
    
    # Connect to virtual camera
    if not capture_system.connect_to_virtual_camera():
        print("❌ Failed to connect to virtual camera")
        return
    
    print(f"✅ Connected to camera index {capture_system.camera_index}")
    
    # Load regions
    if not capture_system.auto_calibrate_from_hardware():
        print("❌ Failed to load regions")
        return
    
    print(f"✅ Loaded {len(capture_system.calibrated_regions)} regions")
    
    # Capture current frame
    frame = capture_system.capture_from_virtual_camera()
    if frame is None:
        print("❌ Failed to capture frame")
        return
    
    print(f"✅ Captured frame: {frame.shape}")
    
    # Save the full frame for inspection
    timestamp = int(time.time())
    full_frame_path = f"debug_full_frame_{timestamp}.png"
    cv2.imwrite(full_frame_path, frame)
    print(f"📸 Full frame saved: {full_frame_path}")
    
    # Extract and save each region with overlay
    frame_with_regions = frame.copy()
    
    print("\n🔍 Extracting and analyzing each region:")
    print("-" * 50)
    
    for region_name, region_data in capture_system.calibrated_regions.items():
        x = region_data['x']
        y = region_data['y']
        w = region_data['width']
        h = region_data['height']
        
        print(f"\n📍 {region_name}:")
        print(f"   Position: x={x}, y={y}, w={w}, h={h}")
        
        # Draw rectangle on main frame
        color = (0, 255, 0) if 'hero' in region_name else (255, 0, 0)
        cv2.rectangle(frame_with_regions, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame_with_regions, region_name, (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Extract region
        region_img = frame[y:y+h, x:x+w]
        
        if region_img.size == 0:
            print("   ❌ Empty region!")
            continue
        
        # Save individual region
        region_path = f"debug_{region_name}_{timestamp}.png"
        cv2.imwrite(region_path, region_img)
        print(f"   💾 Region saved: {region_path}")
        
        # Analyze color content
        avg_color = np.mean(region_img, axis=(0,1))
        print(f"   🎨 Average color (BGR): ({avg_color[0]:.0f}, {avg_color[1]:.0f}, {avg_color[2]:.0f})")
        
        # Check if it looks like a card or empty table
        is_green_table = (avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2] and avg_color[1] > 80)
        is_very_dark = np.mean(avg_color) < 30
        is_very_bright = np.mean(avg_color) > 200
        
        if is_green_table:
            print("   🟢 Appears to be empty green table")
        elif is_very_dark:
            print("   ⚫ Appears to be very dark/black")
        elif is_very_bright:
            print("   ⚪ Appears to be very bright/white")
        else:
            print("   🃏 Appears to contain card content")
            
            # Try to recognize the card
            try:
                card_result = capture_system.recognize_card_from_region(region_img, region_name)
                if card_result:
                    print(f"   🎯 Recognition: {card_result['rank']}{card_result['suit']} (conf: {card_result['confidence']:.3f}, {card_result['method']})")
                else:
                    print("   ❌ No card recognized")
            except Exception as e:
                print(f"   ❌ Recognition error: {e}")
    
    # Save frame with region overlays
    frame_with_regions_path = f"debug_frame_with_regions_{timestamp}.png"
    cv2.imwrite(frame_with_regions_path, frame_with_regions)
    print(f"\n📸 Frame with regions overlay saved: {frame_with_regions_path}")
    
    # Show region configuration
    print(f"\n📋 Region Configuration from file:")
    print("-" * 40)
    try:
        with open("regions/region_config_manual.json", 'r') as f:
            region_config = json.load(f)
        print(json.dumps(region_config, indent=2))
    except Exception as e:
        print(f"Could not read region config: {e}")
    
    # Real-time analysis
    print(f"\n🔄 Running real-time analysis:")
    print("-" * 35)
    
    for i in range(3):
        print(f"\nAnalysis #{i+1}:")
        game_state = capture_system.analyze_current_frame()
        
        if game_state:
            print(f"Hero cards: {game_state.get('hero_cards', [])}")
            print(f"Community cards: {game_state.get('community_cards', [])}")
            print(f"Confidence: {game_state.get('analysis_confidence', 0):.3f}")
            print(f"Method: {game_state.get('recognition_method', 'Unknown')}")
        else:
            print("No analysis results")
        
        time.sleep(2)
    
    # Cleanup
    capture_system.virtual_camera.release()
    
    print(f"\n✅ Debug complete! Check these files:")
    print(f"   📸 {full_frame_path} - Full captured frame")
    print(f"   📸 {frame_with_regions_path} - Frame with region overlays") 
    print(f"   📁 debug_{region_name}_*.png - Individual region images")
    print(f"\n💡 Tips:")
    print(f"   • Check if the full frame shows your current PokerStars table")
    print(f"   • Verify regions are positioned correctly over the cards")
    print(f"   • Make sure OBS is capturing your laptop screen, not a static image")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    debug_live_capture()
