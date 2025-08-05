"""
Direct Live PokerStars Hardware Capture Test
Simple launcher that bypasses optional imports and tests your live setup
"""

import cv2
import numpy as np
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Direct test of live PokerStars capture"""
    print("🎯 LIVE POKERSTARS HARDWARE CAPTURE TEST")
    print("=" * 55)
    print("Testing: Laptop PokerStars → HDMI → Capture Card → OBS → Bot")
    print()
    
    try:
        # Import only what we need
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        from tesseract_config import configure_tesseract
        
        # Configure Tesseract
        configure_tesseract()
        
        print("🔧 Initializing hardware capture system...")
        config = HardwareCaptureConfig(debug_mode=True)
        system = HardwareCaptureSystem(config)
        
        print("🔍 Looking for OBS window...")
        obs_window = system.find_obs_window()
        
        if not obs_window:
            print("❌ OBS window not found!")
            print("   Make sure OBS Studio is running and visible")
            return False
        
        print(f"✅ Found OBS: {obs_window.title}")
        print(f"   Position: ({obs_window.left}, {obs_window.top})")
        print(f"   Size: {obs_window.width} x {obs_window.height}")
        
        print("\n📸 Capturing screenshot from OBS...")
        screenshot = system.capture_obs_window()
        
        if screenshot is None:
            print("❌ Failed to capture screenshot")
            return False
        
        print(f"✅ Screenshot captured: {screenshot.shape}")
        
        # Save the capture
        cv2.imwrite("live_pokerstars_capture.png", screenshot)
        print("💾 Screenshot saved as: live_pokerstars_capture.png")
        
        print("\n🎯 Testing auto-calibration...")
        try:
            calibrated = system.auto_calibrate_from_hardware()
            if calibrated:
                print("✅ Auto-calibration successful!")
                regions = system.enhanced_integration.regions
                print(f"   Detected {len(regions)} regions:")
                for name, data in regions.items():
                    region_type = data.get('type', 'unknown')
                    print(f"   - {name}: {region_type}")
            else:
                print("⚠️  Auto-calibration failed, using default regions")
        except Exception as e:
            print(f"⚠️  Auto-calibration error: {e}")
        
        print("\n🃏 Testing live card recognition...")
        try:
            game_state = system.analyze_current_frame()
            
            if game_state:
                print("✅ Card recognition successful!")
                
                hero_cards = game_state.get('hero_cards', [])
                community_cards = game_state.get('community_cards', [])
                confidence = game_state.get('analysis_confidence', 0)
                
                print("\n📊 CURRENT GAME STATE:")
                print(f"   🂠 Hero Cards: {', '.join(hero_cards) if hero_cards else 'None detected'}")
                print(f"   🃏 Community Cards: {', '.join(community_cards) if community_cards else 'None detected'}")
                print(f"   📈 Confidence: {confidence:.2f}")
                
                # Try to get poker advice
                try:
                    advice = system.get_poker_advice(game_state)
                    print(f"\n🧠 POKER ADVICE:")
                    print(f"   🎯 Recommended Action: {advice.get('action', 'Unknown')}")
                    print(f"   🔢 Confidence: {advice.get('confidence', 0):.2f}")
                    print(f"   💭 Reasoning: {advice.get('reasoning', 'No reasoning provided')}")
                except Exception as e:
                    print(f"⚠️  Poker advice generation failed: {e}")
                
                return True
            else:
                print("⚠️  No game state detected")
                print("   This is normal if:")
                print("   - No cards are currently visible")
                print("   - Table is between hands")
                print("   - Cards are face down")
                return True
                
        except Exception as e:
            print(f"❌ Card recognition failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Some required modules are missing")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def continuous_analysis():
    """Run continuous analysis for live play"""
    print("\n🔄 Starting continuous analysis...")
    print("Press Ctrl+C to stop")
    
    try:
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        
        config = HardwareCaptureConfig(debug_mode=False)  # Less verbose
        system = HardwareCaptureSystem(config)
        
        frame_count = 0
        while True:
            try:
                frame_count += 1
                print(f"\n--- Frame {frame_count} ---")
                
                game_state = system.analyze_current_frame()
                
                if game_state:
                    hero_cards = game_state.get('hero_cards', [])
                    community_cards = game_state.get('community_cards', [])
                    
                    if hero_cards or community_cards:
                        print(f"🂠 Hero: {', '.join(hero_cards) if hero_cards else 'None'}")
                        print(f"🃏 Community: {', '.join(community_cards) if community_cards else 'None'}")
                        
                        # Get advice for current situation
                        advice = system.get_poker_advice(game_state)
                        if advice:
                            print(f"🎯 Action: {advice.get('action', 'Unknown')} ({advice.get('confidence', 0):.2f})")
                    else:
                        print("⏳ Waiting for cards...")
                else:
                    print("⏳ No game state detected...")
                
                time.sleep(2)  # Check every 2 seconds
                
            except KeyboardInterrupt:
                print("\n👋 Stopping continuous analysis...")
                break
            except Exception as e:
                print(f"⚠️  Frame analysis error: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"❌ Continuous analysis failed: {e}")

if __name__ == "__main__":
    print("🎮 Choose test mode:")
    print("1. Single capture test")
    print("2. Continuous live analysis")
    print()
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        success = main()
        if success:
            print("\n🎉 Hardware capture test successful!")
            print("Your setup is ready for live poker analysis!")
        else:
            print("\n❌ Hardware capture test failed")
            print("Check OBS setup and try again")
    elif choice == "2":
        if main():  # First run single test
            continuous_analysis()
    else:
        print("Invalid choice")
