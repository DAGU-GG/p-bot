"""
Direct Hardware Capture Launcher for Live PokerStars Analysis
Bypasses optional imports and focuses on core hardware capture functionality
"""

import sys
import time
import cv2
import numpy as np
from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig

def print_banner():
    """Print the application banner"""
    print("🎯" + "=" * 68 + "🎯")
    print("🚀 LIVE POKERSTARS HARDWARE CAPTURE ANALYSIS 🚀")
    print("🎯" + "=" * 68 + "🎯")
    print("📺 Laptop PokerStars → HDMI Splitter → Capture Card → Main PC")
    print("🔒 Undetectable | 🎓 Educational Use Only | 🏆 Professional Analysis")
    print("🎯" + "=" * 68 + "🎯")
    print()

def test_hardware_setup():
    """Test the hardware capture setup"""
    print("🔧 Testing Hardware Setup...")
    print("-" * 50)
    
    try:
        # Initialize hardware capture system
        config = HardwareCaptureConfig(debug_mode=True)
        system = HardwareCaptureSystem(config)
        
        # Test OBS detection
        print("🔍 Detecting OBS Studio...")
        obs_window = system.find_obs_window()
        
        if not obs_window:
            print("❌ OBS Studio window not found!")
            print("   Make sure OBS is running and showing your laptop feed")
            return None
        
        print(f"✅ OBS Window Found: {obs_window.title}")
        print(f"   Size: {obs_window.width} x {obs_window.height}")
        
        # Test screenshot capture
        print("\n📸 Testing Screenshot Capture...")
        screenshot = system.capture_obs_window()
        
        if screenshot is None:
            print("❌ Failed to capture screenshot from OBS")
            return None
        
        print(f"✅ Screenshot Captured: {screenshot.shape}")
        cv2.imwrite("live_pokerstars_screenshot.png", screenshot)
        print("💾 Screenshot saved: live_pokerstars_screenshot.png")
        
        return system
        
    except Exception as e:
        print(f"❌ Hardware setup error: {e}")
        return None

def run_live_analysis(system):
    """Run continuous live analysis"""
    print("\n🎮 Starting Live Analysis...")
    print("-" * 50)
    print("Press Ctrl+C to stop")
    print()
    
    analysis_count = 0
    
    try:
        while True:
            analysis_count += 1
            print(f"\n🔄 Analysis #{analysis_count} - {time.strftime('%H:%M:%S')}")
            
            # Capture current frame
            screenshot = system.capture_obs_window()
            if screenshot is None:
                print("❌ Failed to capture screenshot")
                time.sleep(2)
                continue
            
            # Auto-calibrate if needed
            if not system.enhanced_integration.regions or analysis_count == 1:
                print("🎯 Auto-calibrating table layout...")
                success = system.auto_calibrate_from_hardware()
                if success:
                    print(f"✅ Auto-calibration successful! Detected {len(system.enhanced_integration.regions)} regions")
                else:
                    print("⚠️  Auto-calibration failed, using default regions")
            
            # Analyze current game state
            game_state = system.analyze_current_frame()
            
            if game_state:
                # Display results
                hero_cards = game_state.get('hero_cards', [])
                community_cards = game_state.get('community_cards', [])
                confidence = game_state.get('analysis_confidence', 0)
                
                print(f"🂠 Hero Cards: {', '.join(hero_cards) if hero_cards else 'None detected'}")
                print(f"🃏 Community Cards: {', '.join(community_cards) if community_cards else 'None detected'}")
                print(f"📊 Confidence: {confidence:.2f}")
                
                # Generate poker advice if cards detected
                if hero_cards or community_cards:
                    try:
                        advice = system.get_poker_advice(game_state)
                        print(f"🧠 Recommendation: {advice['action']} (Confidence: {advice['confidence']:.2f})")
                        print(f"💡 Reasoning: {advice['reasoning']}")
                    except Exception as e:
                        print(f"⚠️  Advice generation error: {e}")
                
                # Save debug screenshot if cards detected
                if hero_cards or community_cards:
                    debug_filename = f"debug_analysis_{analysis_count}.png"
                    cv2.imwrite(debug_filename, screenshot)
                    print(f"🔍 Debug screenshot: {debug_filename}")
            else:
                print("⚠️  No game state detected")
            
            # Wait before next analysis
            time.sleep(3)  # Analyze every 3 seconds
            
    except KeyboardInterrupt:
        print("\n\n👋 Live analysis stopped by user")
    except Exception as e:
        print(f"\n❌ Analysis error: {e}")

def main():
    """Main application function"""
    print_banner()
    
    # Test hardware setup
    system = test_hardware_setup()
    if not system:
        print("\n❌ Hardware setup failed!")
        print("📋 Troubleshooting:")
        print("1. Make sure OBS Studio is running")
        print("2. Verify your laptop feed is visible in OBS")
        print("3. Check that PokerStars table is open on laptop")
        return
    
    print("\n🎉 Hardware setup successful!")
    
    # Ask user if they want to start live analysis
    print("\n📋 Options:")
    print("1. Start Live Analysis")
    print("2. Test Single Analysis")
    print("3. Exit")
    
    try:
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            run_live_analysis(system)
        elif choice == '2':
            print("\n🧪 Running Single Analysis Test...")
            game_state = system.analyze_current_frame()
            
            if game_state:
                print("✅ Single analysis successful!")
                hero_cards = game_state.get('hero_cards', [])
                community_cards = game_state.get('community_cards', [])
                print(f"🂠 Hero Cards: {', '.join(hero_cards) if hero_cards else 'None'}")
                print(f"🃏 Community Cards: {', '.join(community_cards) if community_cards else 'None'}")
            else:
                print("⚠️  No game state detected in single analysis")
        elif choice == '3':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
