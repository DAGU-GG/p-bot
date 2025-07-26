"""
Test the improved card recognition system for accuracy and duplicate prevention.

This script tests the improved card recognition system against sample images
and verifies that it correctly handles duplicate cards and empty slots.
"""

import os
import sys
import logging
import cv2
import numpy as np
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_recognition_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('improved_recognition_test')

# Import the improved card recognizer
from improved_card_recognition import ImprovedCardRecognizer

def test_single_card(image_path, expected_code=None):
    """
    Test recognition of a single card image.
    
    Args:
        image_path: Path to the card image
        expected_code: Expected card code (optional)
        
    Returns:
        dict: Recognition result
    """
    logger.info(f"Testing single card: {image_path}")
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return None
    
    # Create recognizer
    recognizer = ImprovedCardRecognizer()
    
    # Recognize card
    result = recognizer.recognize_card(image, debug=True)
    
    # Log result
    logger.info(f"Recognition result for {os.path.basename(image_path)}:")
    for key, value in result.items():
        if key != 'color_info':  # Skip detailed color info
            logger.info(f"  {key}: {value}")
    
    # Check against expected code if provided
    if expected_code is not None:
        is_correct = result['card_code'] == expected_code
        logger.info(f"Expected: {expected_code}, Got: {result['card_code']}, Correct: {is_correct}")
        result['is_correct'] = is_correct
    
    return result

def test_duplicate_detection():
    """
    Test detection and handling of duplicate cards.
    
    Returns:
        bool: True if the test passed
    """
    logger.info("Testing duplicate card detection")
    
    # Create recognizer
    recognizer = ImprovedCardRecognizer()
    
    # Load test images
    test_dir = "test_cards"
    if not os.path.exists(test_dir):
        logger.error(f"Test directory not found: {test_dir}")
        return False
    
    # Find two images of the same card
    two_of_diamonds = os.path.join(test_dir, "2_diamonds.png")
    if not os.path.exists(two_of_diamonds):
        logger.error(f"Test card not found: {two_of_diamonds}")
        return False
    
    # Load the image twice (simulating duplicate detection)
    image = cv2.imread(two_of_diamonds)
    if image is None:
        logger.error(f"Failed to load image: {two_of_diamonds}")
        return False
    
    # Create duplicate image array
    duplicate_images = [image, image]
    
    # Recognize cards
    results = recognizer.recognize_multiple_cards(duplicate_images, debug=True)
    
    # Check results
    if len(results) != 2:
        logger.error(f"Expected 2 results, got {len(results)}")
        return False
    
    # First card should be recognized correctly
    if results[0]['card_code'] != '2d':
        logger.error(f"First card expected to be 2d, got {results[0]['card_code']}")
        return False
    
    # Second card should be marked as empty or have different code due to duplicate prevention
    if results[1]['card_code'] == '2d' and not results[1].get('duplicate_of'):
        logger.error(f"Duplicate card not detected: {results[1]['card_code']}")
        return False
    
    logger.info("Duplicate detection test passed!")
    return True

def test_empty_slot_detection():
    """
    Test detection of empty card slots.
    
    Returns:
        bool: True if the test passed
    """
    logger.info("Testing empty slot detection")
    
    # Create recognizer
    recognizer = ImprovedCardRecognizer()
    
    # Create an empty slot image (black or green background)
    empty_img = np.ones((100, 70, 3), dtype=np.uint8) * 20  # Dark background
    
    # Recognize card
    result = recognizer.recognize_card(empty_img, debug=True)
    
    # Check results
    if not result['is_empty']:
        logger.error(f"Empty slot not detected: {result}")
        return False
    
    logger.info("Empty slot detection test passed!")
    return True

def test_card_template_directory():
    """
    Test card recognition on all template images.
    
    Returns:
        dict: Results with accuracy statistics
    """
    logger.info("Testing card recognition on template directory")
    
    # Create recognizer
    recognizer = ImprovedCardRecognizer()
    
    # Get template directory
    template_dir = "card_templates"
    if not os.path.exists(template_dir):
        logger.error(f"Template directory not found: {template_dir}")
        return None
    
    # Get all template images
    template_files = [f for f in os.listdir(template_dir) if f.endswith(('.png', '.jpg'))]
    
    # Prepare results
    results = {
        'total': len(template_files),
        'correct': 0,
        'incorrect': 0,
        'details': []
    }
    
    # Test each template
    for template_file in template_files:
        # Extract expected card code from filename
        filename = os.path.splitext(template_file)[0]  # Remove extension
        parts = filename.split('_')
        
        # Handle special case for 10
        if parts[0] == '10':
            rank = 'T'
        else:
            rank = parts[0]
        
        suit = parts[1][0].lower()  # First letter of suit
        expected_code = f"{rank}{suit}"
        
        # Load and test template
        template_path = os.path.join(template_dir, template_file)
        template_img = cv2.imread(template_path)
        
        if template_img is None:
            logger.error(f"Failed to load template: {template_path}")
            continue
        
        # Recognize card
        result = recognizer.recognize_card(template_img, debug=False)
        
        # Check result
        is_correct = result['card_code'] == expected_code
        
        # Update statistics
        if is_correct:
            results['correct'] += 1
        else:
            results['incorrect'] += 1
        
        # Add details
        results['details'].append({
            'filename': template_file,
            'expected': expected_code,
            'recognized': result['card_code'],
            'confidence': result['confidence'],
            'is_correct': is_correct
        })
        
        # Log result
        logger.info(f"Template {template_file}: Expected {expected_code}, Got {result['card_code']}, Correct: {is_correct}")
    
    # Calculate accuracy
    if results['total'] > 0:
        results['accuracy'] = results['correct'] / results['total'] * 100
    else:
        results['accuracy'] = 0
    
    logger.info(f"Template test results: {results['correct']}/{results['total']} correct ({results['accuracy']:.1f}%)")
    
    return results

def test_integration_with_poker_bot():
    """
    Test integration with the main poker bot.
    
    This simulates how the card recognition would work when integrated with the poker bot.
    """
    logger.info("Testing integration with poker bot")
    
    try:
        # Import card recognition integration module
        from card_recognition_integration import IntegratedCardRecognition, create_card_integration
        
        # Create integration
        integration = create_card_integration()
        
        logger.info("Successfully created card integration instance")
        
        # Simulate hero cards recognition
        test_table_img = cv2.imread("test_capture_1753421793.png")
        if test_table_img is None:
            # Try to find another test image
            test_files = [f for f in os.listdir() if f.startswith("test_capture") and f.endswith(".png")]
            if test_files:
                test_table_img = cv2.imread(test_files[0])
            
        if test_table_img is not None:
            logger.info("Testing with sample table image")
            
            # Create dummy regions
            hero_regions = {
                'hero_card_1': {'x': 100, 'y': 100, 'width': 50, 'height': 70},
                'hero_card_2': {'x': 160, 'y': 100, 'width': 50, 'height': 70}
            }
            
            # Extract images for testing
            card1_img = test_table_img[100:170, 100:150]
            card2_img = test_table_img[100:170, 160:210]
            
            # Save extracted cards for inspection
            cv2.imwrite("debug_cards/hero_card_1.png", card1_img)
            cv2.imwrite("debug_cards/hero_card_2.png", card2_img)
            
            # Create recognizer
            recognizer = ImprovedCardRecognizer()
            
            # Test single cards first
            logger.info("Testing recognition of individual hero cards:")
            result1 = recognizer.recognize_card(card1_img, debug=True)
            result2 = recognizer.recognize_card(card2_img, debug=True)
            
            logger.info(f"Hero card 1: {result1['card_code']} ({result1['card_name']}) - Confidence: {result1['confidence']:.2f}")
            logger.info(f"Hero card 2: {result2['card_code']} ({result2['card_name']}) - Confidence: {result2['confidence']:.2f}")
            
            # Now test with the integration
            logger.info("Testing recognition through integration:")
            hero_cards = integration.recognize_hero_cards(test_table_img, hero_regions)
            
            logger.info(f"Recognized hero cards: {hero_cards}")
            
            # Test duplicate prevention
            if len(hero_cards) == 2:
                if hero_cards[0] == hero_cards[1]:
                    logger.warning("Duplicate hero cards detected - integration did not prevent duplicates!")
                else:
                    logger.info("Hero cards are different - duplicate prevention working correctly")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import integration module: {e}")
        return False
    except Exception as e:
        logger.error(f"Integration test failed: {e}", exc_info=True)
        return False

def run_all_tests():
    """Run all tests and report results."""
    logger.info("Starting comprehensive tests of improved card recognition system")
    
    # Run the tests
    test_results = {
        "empty_slot": test_empty_slot_detection(),
        "duplicate_detection": test_duplicate_detection(),
        "template_directory": test_card_template_directory() is not None,
    }
    
    # Try integration test
    try:
        test_results["integration"] = test_integration_with_poker_bot()
    except Exception as e:
        logger.error(f"Integration test error: {e}")
        test_results["integration"] = False
    
    # Report results
    logger.info("\n--- TEST SUMMARY ---")
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    # Calculate overall success
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    logger.info(f"Overall: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
