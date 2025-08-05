"""
Test Hardware Capture Integration with Modern UI
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_hardware_integration():
    """Test that hardware capture can be imported and used"""
    print("🧪 Testing Hardware Capture Integration...")
    
    try:
        # Test import
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        print("✅ Hardware capture system imported successfully")
        
        # Test configuration
        config = HardwareCaptureConfig(debug_mode=True)
        print("✅ Configuration created")
        
        # Test initialization  
        capture_system = HardwareCaptureSystem(config)
        print("✅ Hardware capture system initialized")
        
        # Test virtual camera connection
        if capture_system.connect_to_virtual_camera():
            print(f"✅ Connected to OBS Virtual Camera at index {capture_system.camera_index}")
            
            # Test screenshot capture
            screenshot = capture_system.capture_from_virtual_camera()
            if screenshot is not None:
                print(f"✅ Screenshot captured: {screenshot.shape}")
                
                # Test analysis
                if capture_system.auto_calibrate_from_hardware():
                    print("✅ Region calibration loaded")
                    
                    # Test card recognition
                    game_state = capture_system.analyze_current_frame()
                    if game_state:
                        hero_count = len(game_state.get('hero_cards', []))
                        community_count = len(game_state.get('community_cards', []))
                        confidence = game_state.get('analysis_confidence', 0)
                        
                        print(f"✅ Card analysis complete:")
                        print(f"   Hero cards: {hero_count}")
                        print(f"   Community cards: {community_count}")
                        print(f"   Confidence: {confidence:.3f}")
                        
                        # Print individual cards
                        for card in game_state.get('hero_cards', []):
                            print(f"   🃏 Hero: {card['card']} (conf: {card['confidence']:.3f})")
                        for card in game_state.get('community_cards', []):
                            print(f"   🃏 Community: {card['card']} (conf: {card['confidence']:.3f})")
                            
                        print("\n🎉 INTEGRATION TEST SUCCESSFUL!")
                        print("The hardware capture system is fully integrated and working!")
                        
                    else:
                        print("⚠️ No game state detected (normal if no cards are visible)")
                        
                else:
                    print("⚠️ Region calibration failed - but basic capture works")
            else:
                print("❌ Screenshot capture failed")
        else:
            print("❌ Could not connect to OBS Virtual Camera")
            print("Make sure:")
            print("  1. OBS Studio is running")
            print("  2. Virtual Camera is started")
            print("  3. UGREEN capture device is working")
        
        # Cleanup
        if capture_system.virtual_camera:
            capture_system.virtual_camera.release()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_hardware_integration()
