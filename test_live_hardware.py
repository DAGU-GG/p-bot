"""
Direct Hardware Capture Test for Live PokerStars Analysis
"""

from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
import cv2
import time

def test_obs_detection():
    """Test OBS window detection"""
    print("🔍 Testing OBS Window Detection...")
    
    try:
        config = HardwareCaptureConfig(debug_mode=True)
        system = HardwareCaptureSystem(config)
        
        obs_window = system.find_obs_window()
        
        if obs_window:
            print(f"✅ OBS Window Found: {obs_window.title}")
            print(f"   Window Position: ({obs_window.left}, {obs_window.top})")
            print(f"   Window Size: {obs_window.width} x {obs_window.height}")
            return system
        else:
            print("❌ OBS Window Not Found")
            print("   Make sure OBS Studio is running and visible")
            return None
            
    except Exception as e:
        print(f"❌ Error detecting OBS: {e}")
        return None

def test_capture(system):
    """Test screenshot capture from OBS"""
    print("\n📸 Testing Screenshot Capture...")
    
    try:
        screenshot = system.capture_obs_window()
        
        if screenshot is not None:
            print(f"✅ Screenshot Captured: {screenshot.shape}")
            
            # Save the screenshot
            cv2.imwrite("live_pokerstars_capture.png", screenshot)
            print("💾 Screenshot saved as: live_pokerstars_capture.png")
            
            return screenshot
        else:
            print("❌ Failed to capture screenshot")
            return None
            
    except Exception as e:
        print(f"❌ Capture error: {e}")
        return None

def test_auto_calibration(system):
    """Test auto-calibration on the live capture"""
    print("\n🎯 Testing Auto-Calibration...")
    
    try:
        success = system.auto_calibrate_from_hardware()
        
        if success:
            print("✅ Auto-calibration successful!")
            print(f"   Detected {len(system.enhanced_integration.regions)} regions")
            
            # List detected regions
            for region_name, region_data in system.enhanced_integration.regions.items():
                print(f"   - {region_name}: {region_data.get('type', 'unknown')}")
                
            return True
        else:
            print("⚠️  Auto-calibration failed - will use manual regions")
            return False
            
    except Exception as e:
        print(f"❌ Auto-calibration error: {e}")
        return False

def test_card_recognition(system):
    """Test card recognition on live capture"""
    print("\n🃏 Testing Card Recognition...")
    
    try:
        game_state = system.analyze_current_frame()
        
        if game_state:
            print("✅ Card Recognition Results:")
            
            hero_cards = game_state.get('hero_cards', [])
            community_cards = game_state.get('community_cards', [])
            
            if hero_cards:
                print(f"   🂠 Hero Cards: {', '.join(hero_cards)}")
            else:
                print("   🂠 Hero Cards: None detected")
                
            if community_cards:
                print(f"   🃏 Community Cards: {', '.join(community_cards)}")
            else:
                print("   🃏 Community Cards: None detected")
                
            confidence = game_state.get('analysis_confidence', 0)
            print(f"   📊 Analysis Confidence: {confidence:.2f}")
            
            return game_state
        else:
            print("⚠️  No game state detected")
            return None
            
    except Exception as e:
        print(f"❌ Recognition error: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 LIVE POKERSTARS HARDWARE CAPTURE TEST")
    print("=" * 50)
    print("Testing HDMI Splitter → Capture Card → OBS → Bot")
    print()
    
    # Test 1: OBS Detection
    system = test_obs_detection()
    if not system:
        print("\n❌ Hardware test failed - OBS not detected")
        return
    
    # Test 2: Screenshot Capture
    screenshot = test_capture(system)
    if screenshot is None:
        print("\n❌ Hardware test failed - capture not working")
        return
    
    # Test 3: Auto-calibration
    calibrated = test_auto_calibration(system)
    
    # Test 4: Card Recognition
    game_state = test_card_recognition(system)
    
    print("\n" + "=" * 50)
    if game_state:
        print("🎉 HARDWARE CAPTURE TEST SUCCESSFUL!")
        print("Your setup is ready for live PokerStars analysis!")
        
        print("\n📋 Next Steps:")
        print("1. Open PokerStars on your laptop")
        print("2. Join a play money table")
        print("3. Run: python launch_hardware_capture.py")
        print("4. Start live analysis!")
    else:
        print("⚠️  Hardware capture working, but no cards detected")
        print("This is normal if no poker table is currently visible")
        
        print("\n📋 To test with live poker:")
        print("1. Open PokerStars on your laptop")
        print("2. Join a play money table")
        print("3. Run this test again")

if __name__ == "__main__":
    main()
