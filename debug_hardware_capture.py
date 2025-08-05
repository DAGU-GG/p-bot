#!/usr/bin/env python3
"""
Debug Hardware Capture
Simple test script to debug hardware capture issues
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_hardware_capture():
    """Test hardware capture with detailed debugging"""
    print("HARDWARE CAPTURE DEBUG TEST")
    print("=" * 50)
    
    try:
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        
        # Create config
        config = HardwareCaptureConfig(
            debug_mode=True,
            recognition_method="enhanced"
        )
        
        # Initialize system
        capture_system = HardwareCaptureSystem(config)
        print("SUCCESS: Hardware capture system initialized")
        
        # Test connection
        if capture_system.connect_to_virtual_camera():
            print(f"SUCCESS: Connected to virtual camera at index {capture_system.camera_index}")
        else:
            print("ERROR: Failed to connect to virtual camera")
            return
        
        # Test frame capture
        frame = capture_system.capture_from_virtual_camera()
        if frame is not None:
            print(f"SUCCESS: Frame captured: {frame.shape}")
        else:
            print("ERROR: Frame capture failed")
            return
        
        # Test region loading with detailed output
        print("\nTesting region loading...")
        success = capture_system.auto_calibrate_from_hardware()
        print(f"Region loading result: {success}")
        
        if hasattr(capture_system, 'calibrated_regions') and capture_system.calibrated_regions:
            print(f"\nLoaded {len(capture_system.calibrated_regions)} regions:")
            for name, data in capture_system.calibrated_regions.items():
                print(f"   {name}: x={data.get('x', 'ERROR')}, y={data.get('y', 'ERROR')}, w={data.get('width', 'ERROR')}, h={data.get('height', 'ERROR')}")
        else:
            print("ERROR: No regions loaded")
        
        # Test analysis
        print("\nTesting card analysis...")
        game_state = capture_system.analyze_current_frame()
        
        if game_state:
            hero_cards = game_state.get('hero_cards', [])
            community_cards = game_state.get('community_cards', [])
            confidence = game_state.get('analysis_confidence', 0)
            
            print(f"SUCCESS: Analysis completed:")
            print(f"   Hero cards: {len(hero_cards)}")
            print(f"   Community cards: {len(community_cards)}")
            print(f"   Confidence: {confidence:.3f}")
            
            for i, card in enumerate(hero_cards):
                print(f"   Hero {i+1}: {card}")
            for i, card in enumerate(community_cards):
                print(f"   Community {i+1}: {card}")
        else:
            print("ERROR: Analysis failed or no cards detected")
        
        # Cleanup
        if hasattr(capture_system, 'virtual_camera'):
            capture_system.virtual_camera.release()
        
        print("\nDebug test completed!")
        
    except Exception as e:
        print(f"ERROR: Debug test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hardware_capture()
