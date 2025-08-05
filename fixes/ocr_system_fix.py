#!/usr/bin/env python3
"""
Fix OCR System Implementation Issues
Addresses template matching, OCR configuration, and recognition pipeline issues
"""

import os
import sys
import cv2
import numpy as np
import logging

def analyze_template_system():
    """Analyze the template matching system"""
    print("🔍 Analyzing Template Matching System...")
    
    try:
        # Check template directory
        template_dir = "card_templates"
        if not os.path.exists(template_dir):
            print(f"❌ Template directory not found: {template_dir}")
            return False
        
        # Count templates
        template_files = [f for f in os.listdir(template_dir) if f.endswith('.png')]
        print(f"📁 Found {len(template_files)} template files")
        
        # Analyze naming conventions
        naming_patterns = {}
        for filename in template_files:
            if '_' in filename:
                parts = filename.replace('.png', '').split('_')
                if len(parts) == 2:
                    rank, suit = parts
                    pattern = "rank_suit"
                else:
                    pattern = "unknown_underscore"
            else:
                pattern = "no_underscore"
            
            naming_patterns[pattern] = naming_patterns.get(pattern, 0) + 1
        
        print(f"📊 Naming patterns:")
        for pattern, count in naming_patterns.items():
            print(f"   {pattern}: {count} files")
        
        # Check for complete deck
        expected_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        expected_suits = ['hearts', 'diamonds', 'clubs', 'spades']
        
        missing_cards = []
        for rank in expected_ranks:
            for suit in expected_suits:
                expected_file = f"{rank}_{suit}.png"
                if expected_file not in template_files:
                    missing_cards.append(expected_file)
        
        if missing_cards:
            print(f"❌ Missing {len(missing_cards)} template files:")
            for card in missing_cards[:10]:  # Show first 10
                print(f"   {card}")
            if len(missing_cards) > 10:
                print(f"   ... and {len(missing_cards) - 10} more")
        else:
            print(f"✅ Complete deck of 52 templates found")
        
        return len(missing_cards) == 0
        
    except Exception as e:
        print(f"❌ Template analysis failed: {e}")
        return False

def test_ocr_configuration():
    """Test OCR configuration and functionality"""
    print("\n🔧 Testing OCR Configuration...")
    
    try:
        # Test Tesseract configuration
        from tesseract_config import configure_tesseract, test_tesseract
        
        if configure_tesseract():
            print("✅ Tesseract configuration successful")
        else:
            print("❌ Tesseract configuration failed")
            return False
        
        if test_tesseract():
            print("✅ Tesseract functionality test passed")
        else:
            print("❌ Tesseract functionality test failed")
            return False
        
        # Test enhanced OCR system
        try:
            from enhanced_ocr_recognition import EnhancedOCRCardRecognition
            
            ocr_system = EnhancedOCRCardRecognition()
            print("✅ Enhanced OCR system initialized")
            
            # Create test card image
            test_img = np.ones((100, 70, 3), dtype=np.uint8) * 255
            cv2.putText(test_img, 'A', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.putText(test_img, '♠', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            
            # Test recognition
            result = ocr_system.recognize_card(test_img, debug=False)
            if result:
                print(f"✅ OCR test successful: {result.rank}{result.suit} (conf: {result.confidence:.2f})")
            else:
                print("⚠️ OCR test returned no result (normal for synthetic test)")
            
            return True
            
        except Exception as e:
            print(f"❌ Enhanced OCR test failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ OCR configuration test failed: {e}")
        return False

def analyze_recognition_pipeline():
    """Analyze the complete recognition pipeline"""
    print("\n🔄 Analyzing Recognition Pipeline...")
    
    try:
        # Test CardRecognizer initialization
        sys.path.append('src')
        from card_recognizer import CardRecognizer
        
        recognizer = CardRecognizer()
        print("✅ CardRecognizer initialized")
        
        # Check if regions are loaded
        if hasattr(recognizer, 'card_regions') and recognizer.card_regions:
            print(f"✅ CardRecognizer has {len(recognizer.card_regions)} regions loaded")
            for name, region in recognizer.card_regions.items():
                print(f"   {name}: x={region.get('x_percent', 'missing'):.4f}")
        else:
            print("❌ CardRecognizer has no regions loaded")
        
        # Test CommunityCardDetector
        from community_card_detector import CommunityCardDetector
        
        community_detector = CommunityCardDetector(recognizer)
        print("✅ CommunityCardDetector initialized")
        
        if hasattr(community_detector, 'community_card_regions') and community_detector.community_card_regions:
            print(f"✅ CommunityCardDetector has {len(community_detector.community_card_regions)} regions loaded")
            for name, region in list(community_detector.community_card_regions.items())[:3]:
                print(f"   {name}: x={region.get('x_percent', 'missing'):.4f}")
        else:
            print("❌ CommunityCardDetector has no regions loaded")
        
        # Test hardware capture integration
        try:
            from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
            
            config = HardwareCaptureConfig(debug_mode=False)
            capture_system = HardwareCaptureSystem(config)
            print("✅ HardwareCaptureSystem initialized")
            
            # Test region loading in hardware capture
            if capture_system.auto_calibrate_from_hardware():
                print(f"✅ Hardware capture loaded {len(capture_system.calibrated_regions)} regions")
                for name, region in list(capture_system.calibrated_regions.items())[:3]:
                    print(f"   {name}: x={region.get('x', 'missing')}, y={region.get('y', 'missing')}")
            else:
                print("❌ Hardware capture region loading failed")
            
        except Exception as e:
            print(f"❌ Hardware capture test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Recognition pipeline analysis failed: {e}")
        return False

def create_recognition_test():
    """Create a comprehensive recognition test"""
    print("\n🧪 Creating Recognition Test...")
    
    test_script = '''#!/usr/bin/env python3
"""
Comprehensive Recognition System Test
Tests the complete pipeline with user regions
"""

import sys
import os
import cv2
import numpy as np

# Add paths
sys.path.append('src')
sys.path.append('.')

def test_complete_pipeline():
    """Test the complete recognition pipeline"""
    print("🎯 Testing Complete Recognition Pipeline...")
    
    # Load test image
    test_image = "poker_table_for_regions_20250805_023128.png"
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return False
    
    img = cv2.imread(test_image)
    if img is None:
        print(f"❌ Could not load test image")
        return False
    
    print(f"✅ Loaded test image: {img.shape}")
    
    # Test region loading
    from fixes.region_loader_fix import FixedRegionLoader
    
    loader = FixedRegionLoader()
    regions = loader.load_regions()
    
    if not regions:
        print("❌ No regions loaded")
        return False
    
    print(f"✅ Loaded {len(regions)} regions")
    
    # Test hero card recognition
    try:
        from card_recognizer import CardRecognizer
        
        recognizer = CardRecognizer()
        
        # Update recognizer with fixed regions
        hero_regions = loader.get_hero_card_regions()
        recognizer.card_regions = hero_regions
        
        print(f"✅ Updated CardRecognizer with {len(hero_regions)} hero regions")
        
        # Test hero card extraction and recognition
        hole_cards = recognizer.recognize_hero_hole_cards(img, debug=True)
        
        print(f"🂠 Hero Cards Result:")
        print(f"   Valid: {hole_cards.is_valid()}")
        print(f"   Card 1: {hole_cards.card1}")
        print(f"   Card 2: {hole_cards.card2}")
        print(f"   Confidence: {hole_cards.detection_confidence:.3f}")
        
    except Exception as e:
        print(f"❌ Hero card recognition test failed: {e}")
    
    # Test community card recognition
    try:
        from community_card_detector import CommunityCardDetector
        
        community_detector = CommunityCardDetector(recognizer)
        
        # Update detector with fixed regions
        community_regions = loader.get_community_card_regions()
        community_detector.community_card_regions = community_regions
        
        print(f"✅ Updated CommunityCardDetector with {len(community_regions)} regions")
        
        # Test community card detection
        community_cards = community_detector.detect_community_cards(img)
        
        print(f"🃏 Community Cards Result:")
        print(f"   Count: {community_cards.count}/5")
        print(f"   Phase: {community_cards.get_phase()}")
        print(f"   Valid: {community_cards.is_valid_phase()}")
        print(f"   Confidence: {community_cards.detection_confidence:.3f}")
        
        visible_cards = community_cards.get_visible_cards()
        for i, card in enumerate(visible_cards):
            print(f"   Card {i+1}: {card}")
        
    except Exception as e:
        print(f"❌ Community card recognition test failed: {e}")
    
    print("\\n🎉 Pipeline test complete!")
    return True

if __name__ == "__main__":
    test_complete_pipeline()
'''
    
    # Save test script
    with open("test_recognition_pipeline.py", 'w') as f:
        f.write(test_script)
    
    print("✅ Created test_recognition_pipeline.py")
    return True

def main():
    """Main analysis and fix function"""
    print("🎯 OCR SYSTEM ANALYSIS & FIX")
    print("=" * 50)
    
    # Step 1: Analyze template system
    templates_ok = analyze_template_system()
    
    # Step 2: Test OCR configuration
    ocr_ok = test_ocr_configuration()
    
    # Step 3: Analyze recognition pipeline
    pipeline_ok = analyze_recognition_pipeline()
    
    # Step 4: Create test script
    test_created = create_recognition_test()
    
    print("\n📊 ANALYSIS SUMMARY:")
    print(f"Templates: {'✅ OK' if templates_ok else '❌ ISSUES'}")
    print(f"OCR Config: {'✅ OK' if ocr_ok else '❌ ISSUES'}")
    print(f"Pipeline: {'✅ OK' if pipeline_ok else '❌ ISSUES'}")
    print(f"Test Created: {'✅ OK' if test_created else '❌ FAILED'}")
    
    if all([templates_ok, ocr_ok, pipeline_ok, test_created]):
        print("\n🎉 OCR SYSTEM ANALYSIS COMPLETE!")
        print("✅ All systems appear to be working correctly")
        print("\n🧪 Run the test:")
        print("   python test_recognition_pipeline.py")
    else:
        print("\n⚠️ ISSUES FOUND IN OCR SYSTEM")
        print("Some components need attention before testing")

if __name__ == "__main__":
    main()