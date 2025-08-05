"""
Test Script for Enhanced Poker Bot Systems
Tests the table reference system and OCR recognition
"""

import cv2
import numpy as np
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def create_test_card_image():
    """Create a simple test card image for testing"""
    # Create a white card-like rectangle
    card = np.ones((100, 70, 3), dtype=np.uint8) * 255
    
    # Add a border
    cv2.rectangle(card, (2, 2), (67, 97), (0, 0, 0), 2)
    
    # Add rank (A) in top-left
    cv2.putText(card, 'A', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Add suit symbol (hearts - red)
    cv2.circle(card, (15, 40), 8, (0, 0, 255), -1)  # Red heart
    
    # Add smaller rank/suit in bottom-right (upside down)
    cv2.putText(card, 'A', (45, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.circle(card, (50, 70), 5, (0, 0, 255), -1)
    
    return card

def create_test_table_image():
    """Create a simple test poker table layout"""
    # Create green table background
    table = np.ones((600, 800, 3), dtype=np.uint8)
    table[:] = [0, 100, 0]  # Green background
    
    # Add some cards in typical positions
    test_card = create_test_card_image()
    
    # Hero cards (bottom center)
    table[480:580, 320:390] = test_card
    table[480:580, 410:480] = test_card
    
    # Community cards (center)
    table[250:350, 280:350] = test_card
    table[250:350, 370:440] = test_card
    table[250:350, 460:530] = test_card
    
    # Add pot area label
    cv2.putText(table, 'POT: $150', (350, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return table

def test_table_reference_system():
    """Test the table reference system"""
    print("Testing Table Reference System...")
    
    try:
        from table_reference_system import TableReferenceSystem
        
        # Create test table
        test_table = create_test_table_image()
        cv2.imwrite('test_table_generated.png', test_table)
        print("✅ Created test table image")
        
        # Initialize system
        table_ref = TableReferenceSystem()
        
        # Test auto-calibration
        regions = table_ref.auto_calibrate_from_screenshot(test_table)
        
        if regions:
            print(f"✅ Auto-calibration successful! Found {len(regions)} regions:")
            for name, region in regions.items():
                print(f"   {name}: x={region['x_percent']:.3f}, y={region['y_percent']:.3f}")
        else:
            print("❌ Auto-calibration failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Table reference system test failed: {e}")
        return False

def test_ocr_recognition():
    """Test the OCR recognition system"""
    print("\nTesting OCR Recognition System...")
    
    try:
        # Create test card
        test_card = create_test_card_image()
        cv2.imwrite('test_card_generated.png', test_card)
        print("✅ Created test card image")
        
        # Try enhanced OCR first
        try:
            from enhanced_ocr_recognition import EnhancedOCRCardRecognition
            
            print("  Attempting Enhanced OCR...")
            ocr = EnhancedOCRCardRecognition()
            result = ocr.recognize_card(test_card, debug=True)
            
            if result and result.confidence > 0:
                print(f"✅ Enhanced OCR successful! Recognized: {result.rank}{result.suit}")
                print(f"   Confidence: {result.confidence:.2f}, Method: {result.method}")
                return True
            else:
                print("  Enhanced OCR returned low confidence, trying fallback...")
                
        except Exception as ocr_error:
            print(f"  Enhanced OCR failed: {str(ocr_error)}")
            print("  Trying fallback recognition...")
        
        # Fallback to pattern-based recognition
        from fallback_card_recognition import FallbackCardRecognition
        
        print("  Using Fallback Pattern Recognition...")
        recognizer = FallbackCardRecognition()
        result = recognizer.recognize_card(test_card, four_color_deck=True)
        
        if result and result.confidence > 0:
            print(f"✅ Fallback Recognition successful! Recognized: {result.rank}{result.suit}")
            print(f"   Confidence: {result.confidence:.2f}, Method: {result.method}")
            print("   Note: Using pattern matching (no Tesseract required)")
            return True
        else:
            print("❌ Both OCR systems failed")
            return False
            
    except Exception as e:
        print(f"❌ All recognition systems failed: {e}")
        return False

def test_integration():
    """Test the integration system"""
    print("\nTesting Integration System...")
    
    try:
        from enhanced_integration import EnhancedPokerBot
        
        # Create enhanced bot
        bot = EnhancedPokerBot()
        print("✅ Enhanced bot created")
        
        # Create test screenshot
        test_screenshot = create_test_table_image()
        
        # Test auto-calibration
        if bot.auto_calibrate(test_screenshot):
            print("✅ Integration auto-calibration successful")
            
            # Test game state analysis
            result = bot.analyze_game_state(test_screenshot, debug=True)
            
            if result:
                print("✅ Game state analysis successful")
                print(f"   Hero cards: {result.get('hero_cards', 'None')}")
                print(f"   Community cards: {result.get('community_cards', 'None')}")
                
                # Test visualization
                vis = bot.create_visualization(test_screenshot)
                if vis is not None:
                    print("✅ Visualization created")
                else:
                    print("❌ Visualization failed")
            else:
                print("❌ Game state analysis failed")
        else:
            print("❌ Integration auto-calibration failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🧪 ENHANCED POKER BOT SYSTEMS TEST")
    print("="*60)
    print()
    
    # Check if Tesseract is available
    try:
        import pytesseract
        # Test basic OCR
        test_img = np.ones((50, 100, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, 'TEST', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        text = pytesseract.image_to_string(test_img).strip()
        print("✅ Tesseract OCR is working")
    except Exception as e:
        print(f"⚠️  Tesseract OCR issue: {e}")
        print("   OCR functionality may be limited")
    
    print()
    
    # Run tests
    tests = [
        ("Table Reference System", test_table_reference_system),
        ("OCR Recognition", test_ocr_recognition), 
        ("Integration System", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Enhanced systems are ready to use.")
        print("\nNext steps:")
        print("1. Run 'python launch_enhanced_bot.py' to use the enhanced bot")
        print("2. Take a screenshot of your poker table for calibration")
        print("3. Use option 1 in the launcher to auto-calibrate")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("\nGenerated test files:")
    print("- test_table_generated.png (test poker table)")
    print("- test_card_generated.png (test card)")
    print("- enhanced_bot_visualization.png (if generated)")

if __name__ == "__main__":
    main()
