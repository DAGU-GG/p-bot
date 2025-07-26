#!/usr/bin/env python3
"""
Simple test script to verify the main fixes without full bot integration.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test 1: Verify all modules can be imported."""
    print("🧪 Test 1: Module Import Test")
    print("-" * 30)
    
    try:
        from window_capture import PokerStarsWindowCapture
        print("✅ window_capture imported successfully")
    except Exception as e:
        print(f"❌ window_capture import failed: {e}")
        return False
    
    try:
        from card_recognizer import CardRecognizer
        print("✅ card_recognizer imported successfully")
    except Exception as e:
        print(f"❌ card_recognizer import failed: {e}")
        return False
    
    try:
        from community_card_detector import CommunityCardDetector
        print("✅ community_card_detector imported successfully")
    except Exception as e:
        print(f"❌ community_card_detector import failed: {e}")
        return False
    
    try:
        from ui.region_calibrator import RegionCalibrator
        print("✅ region_calibrator imported successfully")
    except Exception as e:
        print(f"❌ region_calibrator import failed: {e}")
        return False
    
    return True

def test_window_detection():
    """Test 2: Window detection with enhanced filtering."""
    print("\n🧪 Test 2: Window Detection Test")
    print("-" * 30)
    
    try:
        from window_capture import PokerStarsWindowCapture
        
        capture = PokerStarsWindowCapture()
        windows = capture.find_pokerstars_windows()
        
        print(f"Found {len(windows)} potential PokerStars windows:")
        
        for i, window in enumerate(windows):
            print(f"  {i+1}. {window['title']} (Score: {window.get('score', 'N/A')})")
        
        # Check if VS Code windows are properly filtered out
        vs_code_windows = [w for w in windows if 'visual studio code' in w['title'].lower() or 'vs code' in w['title'].lower()]
        
        if vs_code_windows:
            print(f"⚠️  Warning: {len(vs_code_windows)} VS Code windows still detected")
            for w in vs_code_windows:
                print(f"    - {w['title']}")
        else:
            print("✅ VS Code windows properly filtered out")
        
        # Look for actual poker table windows
        poker_windows = [w for w in windows if 'session:' in w['title'].lower() or 'hold\'em' in w['title'].lower()]
        
        if poker_windows:
            print(f"✅ Found {len(poker_windows)} actual poker table windows:")
            for w in poker_windows:
                print(f"    - {w['title']}")
        else:
            print("⚠️  No actual poker table windows detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Window detection test failed: {e}")
        return False

def test_card_templates():
    """Test 3: Card template loading."""
    print("\n🧪 Test 3: Card Template Loading Test")
    print("-" * 30)
    
    try:
        from card_recognizer import CardRecognizer
        
        recognizer = CardRecognizer()
        
        if recognizer.template_loaded:
            template_count = len(recognizer.card_templates)
            print(f"✅ Loaded {template_count} card templates")
            
            # Test a few specific templates
            test_cards = ['Ah', 'Kd', '2c', 'Ts']
            missing_cards = []
            
            for card in test_cards:
                if card in recognizer.card_templates:
                    template = recognizer.card_templates[card]
                    if template is not None:
                        print(f"  ✅ {card}: {template.shape}")
                    else:
                        print(f"  ❌ {card}: Template is None")
                        missing_cards.append(card)
                else:
                    print(f"  ❌ {card}: Not found")
                    missing_cards.append(card)
            
            if not missing_cards:
                print("✅ All test templates loaded correctly")
            else:
                print(f"⚠️  Missing {len(missing_cards)} templates: {missing_cards}")
            
            return template_count >= 40  # Should have most cards
        else:
            print("❌ Card templates not loaded")
            return False
        
    except Exception as e:
        print(f"❌ Card template test failed: {e}")
        return False

def test_region_calibrator():
    """Test 4: Region calibrator initialization."""
    print("\n🧪 Test 4: Region Calibrator Test")
    print("-" * 30)
    
    try:
        # Create a mock main window
        class MockMainWindow:
            def __init__(self):
                self.capture_mode = "window"
                self.window_capture = None
                self.obs_capture = None
        
        from ui.region_calibrator import RegionCalibrator
        
        mock_window = MockMainWindow()
        calibrator = RegionCalibrator(None, mock_window)
        
        print(f"✅ Region calibrator initialized with {len(calibrator.regions)} regions:")
        for name, region in calibrator.regions.items():
            print(f"  {name}: x={region['x']:.1f}%, y={region['y']:.1f}%, w={region['width']:.1f}%, h={region['height']:.1f}%")
        
        # Test coordinate conversion functions
        test_x, test_y = calibrator.canvas_to_percentage(100, 100)
        print(f"✅ Coordinate conversion test: canvas(100,100) -> percentage({test_x:.1f}%, {test_y:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Region calibrator test failed: {e}")
        return False

def main():
    """Run all simple tests."""
    print("🤖 PokerStars Bot - Simple Test Suite")
    print("=" * 40)
    
    tests = [
        ("Module Import", test_imports),
        ("Window Detection", test_window_detection),
        ("Card Templates", test_card_templates),
        ("Region Calibrator", test_region_calibrator)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")
    
    print("\n📊 Test Summary:")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
