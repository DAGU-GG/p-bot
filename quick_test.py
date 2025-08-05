"""
Quick Hardware Integration Test
Run this in a NEW terminal while the UI is running
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def quick_test():
    """Quick test to verify hardware capture is working"""
    print("🧪 Quick Hardware Capture Test")
    print("=" * 40)
    
    try:
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        
        # Test configuration
        config = HardwareCaptureConfig(debug_mode=False)  # Disable debug to avoid conflicts
        capture_system = HardwareCaptureSystem(config)
        
        print("✅ Hardware capture system imported and initialized")
        
        # Test connection
        if capture_system.connect_to_virtual_camera():
            print(f"✅ Connected to OBS Virtual Camera at index {capture_system.camera_index}")
            
            # Test single screenshot
            screenshot = capture_system.capture_from_virtual_camera()
            if screenshot is not None:
                print(f"✅ Screenshot captured: {screenshot.shape}")
                
                # Test region loading
                if capture_system.auto_calibrate_from_hardware():
                    print(f"✅ Regions loaded: {len(capture_system.calibrated_regions)} regions")
                    
                    # Test analysis
                    game_state = capture_system.analyze_current_frame()
                    if game_state:
                        hero_cards = len(game_state.get('hero_cards', []))
                        community_cards = len(game_state.get('community_cards', []))
                        confidence = game_state.get('analysis_confidence', 0)
                        
                        print(f"✅ Card analysis working:")
                        print(f"   Hero cards detected: {hero_cards}")
                        print(f"   Community cards detected: {community_cards}")
                        print(f"   Analysis confidence: {confidence:.3f}")
                        
                        print("\n🎉 INTEGRATION SUCCESSFUL!")
                        print("The hardware capture system is working correctly.")
                        print("Your Modern UI should now be able to:")
                        print("  • Connect to OBS Virtual Camera")
                        print("  • Display live video feed")
                        print("  • Recognize cards from your laptop")
                        print("  • Provide real-time analysis")
                        
                    else:
                        print("⚠️ Analysis returned no results (normal if no cards visible)")
                else:
                    print("⚠️ Region loading failed")
            else:
                print("❌ Screenshot capture failed")
        else:
            print("❌ Could not connect to OBS Virtual Camera")
            print("Check that OBS is running with Virtual Camera started")
        
        # Cleanup
        if hasattr(capture_system, 'virtual_camera') and capture_system.virtual_camera:
            capture_system.virtual_camera.release()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    quick_test()
