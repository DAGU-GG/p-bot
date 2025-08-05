"""
Hardware Capture Quick Launcher
Simple command-line interface for testing hardware capture setup
"""

import sys
import time
import logging
from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🎯 POKER ANALYSIS PRO - HARDWARE CAPTURE")
    print("=" * 60)
    print("Laptop PokerStars → Main PC Analysis")
    print("Undetectable | Professional | Educational Use Only")
    print("=" * 60)

def test_hardware_setup():
    """Test the complete hardware setup"""
    print("\n🔧 TESTING HARDWARE SETUP...")
    
    config = HardwareCaptureConfig(debug_mode=True)
    capture_system = HardwareCaptureSystem(config)
    
    # Test 1: OBS Window Detection
    print("\n1. Testing OBS Window Detection...")
    obs_window = capture_system.find_obs_window()
    if obs_window:
        print(f"   ✅ Found: {obs_window.title}")
        print(f"   📍 Position: {obs_window.left}, {obs_window.top}")
        print(f"   📏 Size: {obs_window.width} x {obs_window.height}")
    else:
        print("   ❌ OBS window not found!")
        print("   💡 Make sure OBS Studio is running")
        return False
    
    # Test 2: Screenshot Capture
    print("\n2. Testing Screenshot Capture...")
    screenshot = capture_system.capture_obs_window()
    if screenshot is not None:
        print(f"   ✅ Screenshot captured: {screenshot.shape}")
        print("   💾 Saved as 'test_hardware_capture.png'")
    else:
        print("   ❌ Screenshot capture failed!")
        return False
    
    # Test 3: Auto-Calibration
    print("\n3. Testing Auto-Calibration...")
    if capture_system.auto_calibrate_from_hardware():
        regions = capture_system.calibrated_regions
        print(f"   ✅ Found {len(regions)} regions:")
        for region_name, region_data in regions.items():
            print(f"      • {region_name}")
    else:
        print("   ⚠️ Auto-calibration found no regions")
        print("   💡 Make sure PokerStars table is visible in OBS")
    
    # Test 4: Recognition Test
    print("\n4. Testing Card Recognition...")
    game_state = capture_system.analyze_current_frame()
    if game_state:
        hero_cards = game_state.get('hero_cards', [])
        community_cards = game_state.get('community_cards', [])
        confidence = game_state.get('analysis_confidence', 0)
        
        print(f"   ✅ Analysis successful!")
        print(f"      Hero cards: {len(hero_cards)} detected")
        print(f"      Community cards: {len(community_cards)} detected")
        print(f"      Confidence: {confidence:.1%}")
        
        if hero_cards:
            print("      Hero cards:")
            for i, card in enumerate(hero_cards, 1):
                print(f"        {i}. {card['card']} ({card['confidence']:.2f})")
        
        if community_cards:
            print("      Community cards:")
            for i, card in enumerate(community_cards, 1):
                print(f"        {i}. {card['card']} ({card['confidence']:.2f})")
                
        # Test advice generation
        advice = capture_system.get_poker_advice(game_state)
        print(f"\n   🎯 Advice: {advice['action'].upper()} ({advice['confidence']:.1%})")
        print(f"      Reasoning: {advice['reasoning']}")
        
    else:
        print("   ⚠️ No game state detected")
        print("   💡 Make sure poker table is visible and cards are dealt")
    
    print("\n✅ HARDWARE SETUP TEST COMPLETE!")
    return True

def start_live_analysis():
    """Start live analysis loop"""
    print("\n🎯 STARTING LIVE ANALYSIS...")
    print("Press Ctrl+C to stop\n")
    
    config = HardwareCaptureConfig(
        debug_mode=True,
        analysis_interval=2.0  # Analyze every 2 seconds
    )
    
    capture_system = HardwareCaptureSystem(config)
    
    # Auto-calibrate first
    print("📍 Auto-calibrating...")
    if not capture_system.auto_calibrate_from_hardware():
        print("❌ Auto-calibration failed! Cannot start analysis.")
        return
    
    print("✅ Auto-calibration successful!")
    print("🔄 Starting analysis loop...\n")
    
    try:
        analysis_count = 0
        while True:
            analysis_count += 1
            
            # Analyze current frame
            game_state = capture_system.analyze_current_frame()
            
            if game_state:
                hero_cards = game_state.get('hero_cards', [])
                community_cards = game_state.get('community_cards', [])
                confidence = game_state.get('analysis_confidence', 0)
                
                print(f"📊 Analysis #{analysis_count} - {time.strftime('%H:%M:%S')}")
                print(f"   Hero: {[card['card'] for card in hero_cards]}")
                print(f"   Community: {[card['card'] for card in community_cards]}")
                print(f"   Confidence: {confidence:.1%}")
                
                # Generate advice
                advice = capture_system.get_poker_advice(game_state)
                action_color = "🟢" if advice['action'] == 'raise' else "🟡" if advice['action'] == 'call' else "🔴"
                print(f"   {action_color} Advice: {advice['action'].upper()} ({advice['confidence']:.1%})")
                print(f"   💭 {advice['reasoning']}")
                print()
            else:
                print(f"⏭️ Analysis #{analysis_count} - No cards detected")
            
            # Wait before next analysis
            time.sleep(config.analysis_interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Analysis stopped by user")
    except Exception as e:
        print(f"\n❌ Analysis error: {e}")

def main():
    """Main menu"""
    print_banner()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    while True:
        print("\n📋 MAIN MENU:")
        print("1. Test Hardware Setup")
        print("2. Start Live Analysis")
        print("3. Test Recognition Systems")
        print("4. Launch GUI Version")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            test_hardware_setup()
            
        elif choice == "2":
            start_live_analysis()
            
        elif choice == "3":
            print("\n🧪 Testing recognition systems...")
            try:
                from compare_recognition_systems import test_hardware_capture_recognition
                result = test_hardware_capture_recognition()
                if result:
                    print("✅ Recognition test successful!")
                else:
                    print("❌ Recognition test failed!")
            except Exception as e:
                print(f"❌ Test error: {e}")
                
        elif choice == "4":
            print("\n🖥️ Launching GUI...")
            try:
                from launch_hardware_capture import main as gui_main
                gui_main()
            except Exception as e:
                print(f"❌ GUI launch error: {e}")
                
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main()
