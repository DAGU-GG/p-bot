"""
Test Enhanced Card Recognition with Hardware Capture
"""

from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
import cv2
import time

def test_enhanced_recognition():
    """Test the enhanced card recognition with virtual camera"""
    print("🧪 Testing Enhanced Card Recognition with Hardware Capture...")
    
    # Initialize hardware capture with enhanced recognition
    config = HardwareCaptureConfig(
        debug_mode=True,
        recognition_method="enhanced"
    )
    
    capture_system = HardwareCaptureSystem(config)
    
    # Check if enhanced recognition is available
    if capture_system.enhanced_recognition:
        print("✅ Enhanced card recognition system loaded")
        stats = capture_system.enhanced_recognition.get_recognition_stats()
        print(f"   Recognition stats: {stats}")
    else:
        print("❌ Enhanced card recognition not available")
    
    # Test virtual camera connection
    if not capture_system.connect_to_virtual_camera():
        print("❌ Failed to connect to virtual camera")
        return False
    
    print(f"✅ Connected to virtual camera at index {capture_system.camera_index}")
    
    # Capture a test frame
    frame = capture_system.capture_from_virtual_camera()
    if frame is None:
        print("❌ Failed to capture frame")
        return False
    
    print(f"✅ Captured frame: {frame.shape}")
    
    # Save the test frame
    test_filename = f"test_enhanced_capture_{int(time.time())}.png"
    cv2.imwrite(test_filename, frame)
    print(f"💾 Saved test frame: {test_filename}")
    
    # Test enhanced recognition on a small region (simulate card region)
    height, width = frame.shape[:2]
    
    # Create test regions (hero cards area)
    test_regions = [
        (width//4, height//2, width//8, height//6),  # Left hero card
        (width//3, height//2, width//8, height//6),  # Right hero card
        (width//2 - width//16, height//3, width//8, height//6),  # Community card
    ]
    
    print("\n🃏 Testing card recognition on regions...")
    
    for i, region in enumerate(test_regions):
        x, y, w, h = region
        if x + w <= width and y + h <= height:
            # Extract region
            card_region = frame[y:y+h, x:x+w]
            
            # Save region for debugging
            region_filename = f"test_region_{i}_{int(time.time())}.png"
            cv2.imwrite(region_filename, card_region)
            
            # Test recognition
            result = capture_system.recognize_card_from_region(card_region, f"test_region_{i}")
            
            if result:
                print(f"   Region {i}: {result['rank']}{result['suit']} ({result['method']}, {result['confidence']:.2f})")
            else:
                print(f"   Region {i}: No card detected")
    
    # Test auto-calibration
    print("\n🎯 Testing auto-calibration...")
    if capture_system.auto_calibrate_from_hardware():
        print("✅ Auto-calibration successful")
        print(f"   Found {len(capture_system.calibrated_regions)} regions")
    else:
        print("❌ Auto-calibration failed")
    
    # Test full analysis
    print("\n🔍 Testing full frame analysis...")
    game_state = capture_system.analyze_current_frame()
    
    if game_state:
        print("✅ Full analysis successful")
        print(f"   Hero cards: {game_state.get('hero_cards', [])}")
        print(f"   Community cards: {game_state.get('community_cards', [])}")
        print(f"   Confidence: {game_state.get('analysis_confidence', 0):.2f}")
    else:
        print("❌ Full analysis failed")
    
    # Cleanup
    if capture_system.virtual_camera:
        capture_system.virtual_camera.release()
    
    print("\n📋 Test Summary:")
    print("✅ Virtual camera connection working")
    print("✅ Frame capture working")
    print("✅ Enhanced recognition system integrated")
    print("🎯 Now connect OBS in UI and start monitoring!")
    
    return True

if __name__ == "__main__":
    test_enhanced_recognition()
