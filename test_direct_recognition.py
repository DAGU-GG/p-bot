"""
Test script for the direct card recognition system.

This script tests the direct card recognition approach that uses color analysis
for suit detection and OCR/shape analysis for rank detection.
"""

import os
import sys
import logging
import cv2
import numpy as np
import time
from pathlib import Path
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_recognition_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('direct_recognition_test')

# Import direct card recognition system
try:
    from direct_card_recognition import DirectCardRecognition
    from direct_card_integration import DirectCardIntegration
except ImportError as e:
    logger.error(f"Failed to import direct card recognition: {e}")
    logger.error("Make sure direct_card_recognition.py is in the same directory")
    sys.exit(1)
except ImportError as e:
    logger.error(f"Failed to import direct card recognition: {e}")
    logger.error("Make sure direct_card_recognition.py is in the same directory")
    sys.exit(1)

def test_empty_slot_detection(recognizer, debug=False):
    """Test the empty slot detection."""
    logger.info("Testing empty slot detection")
    
    # Create a black image (empty slot)
    empty_img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Recognize the empty slot
    result = recognizer.recognize_card(empty_img, debug=debug)
    
    # Check the result
    if result['is_empty'] and result['card_code'] == 'empty':
        logger.info("Empty slot detection test passed!")
        return True
    else:
        logger.error(f"Empty slot detection test failed: {result}")
        return False

def test_on_template_directory(recognizer, template_dir='card_templates', debug=False):
    """Test recognition on template directory."""
    logger.info("Testing card recognition on template directory")
    
    # Check if template directory exists
    if not os.path.isdir(template_dir):
        logger.error(f"Template directory '{template_dir}' not found")
        return False
    
    # Get all template files
    template_files = [f for f in os.listdir(template_dir) if f.endswith('.png')]
    
    if not template_files:
        logger.error(f"No template files found in '{template_dir}'")
        return False
    
    correct_count = 0
    total_count = 0
    
    # Test each template
    for template_file in template_files:
        # Extract expected card code from filename
        # Filename format: <rank>_<suit>.png, e.g., 10_hearts.png, A_spades.png
        parts = template_file.split('_')
        if len(parts) != 2:
            logger.warning(f"Skipping file with invalid format: {template_file}")
            continue
        
        rank, suit = parts[0], parts[1].split('.')[0]
        
        # Convert rank and suit to the format used in card_code
        rank_map = {
            '10': 'T',
            'jack': 'J',
            'queen': 'Q',
            'king': 'K',
            'ace': 'A'
        }
        
        suit_map = {
            'hearts': 'h',
            'diamonds': 'd',
            'clubs': 'c',
            'spades': 's'
        }
        
        # Convert rank if needed
        expected_rank = rank_map.get(rank.lower(), rank)
        
        # Convert suit
        expected_suit = suit_map.get(suit.lower(), suit[0].lower())
        
        # Create expected card code
        expected_card = f"{expected_rank}{expected_suit}"
        
        # Load the template image
        template_path = os.path.join(template_dir, template_file)
        template_img = cv2.imread(template_path)
        
        if template_img is None:
            logger.warning(f"Failed to load template image: {template_path}")
            continue
        
        # Recognize the card
        result = recognizer.recognize_card(template_img, debug=debug)
        
        # Check the result
        got_card = result['card_code']
        is_correct = got_card == expected_card
        
        if is_correct:
            correct_count += 1
        
        total_count += 1
        
        logger.info(f"Template {template_file}: Expected {expected_card}, Got {got_card}, Correct: {is_correct}")
    
    # Calculate accuracy
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    logger.info(f"Template test results: {correct_count}/{total_count} correct ({accuracy:.1f}%)")
    
    return accuracy >= 70  # Pass if accuracy is at least 70%

def test_duplicate_detection(recognizer, debug=False):
    """Test the duplicate card detection."""
    logger.info("Testing duplicate card detection")
    
    # Create a test directory if it doesn't exist
    os.makedirs("test_cards", exist_ok=True)
    
    # Check if a sample card exists
    sample_path = "test_cards/2_diamonds.png"
    if not os.path.exists(sample_path):
        # Create a red rectangle with a "2" in it (simple representation of 2 of diamonds)
        sample_img = np.ones((100, 80, 3), dtype=np.uint8) * 255
        sample_img[:, :, 0] = 100  # Blue channel (for diamonds)
        cv2.putText(sample_img, "2", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.imwrite(sample_path, sample_img)
    
    # Load the sample card
    sample_img = cv2.imread(sample_path)
    
    if sample_img is None:
        logger.error(f"Failed to load or create sample card image")
        return False
    
    # Create a list with duplicate cards
    card_list = [sample_img, sample_img.copy()]
    
    # Recognize the cards
    results = recognizer.recognize_multiple_cards(card_list, debug=debug)
    
    # Check the results - second card should be marked as empty due to duplicate detection
    if len(results) != 2:
        logger.error(f"Expected 2 results, got {len(results)}")
        return False
    
    # First card should be recognized
    if results[0]['is_empty']:
        logger.error(f"First card was incorrectly marked as empty")
        return False
    
    # Second card should be marked as empty or with method 'duplicate_detection'
    if not results[1]['is_empty'] and results[1]['method'] != 'duplicate_detection':
        logger.error(f"Duplicate detection failed: {results[1]}")
        return False
    
    logger.info("Duplicate detection test passed!")
    return True

def test_integration(recognizer, debug=False):
    """Test integration with sample images."""
    logger.info("Testing integration with poker bot")
    
    # Create test directory if it doesn't exist
    os.makedirs("test_images", exist_ok=True)
    
    # Create a sample poker table image with multiple cards
    # For simplicity, we'll create 2 hero cards (different suits)
    # and 3 community cards
    
    # Hero card 1 - Clubs (green)
    hero1_img = np.ones((100, 80, 3), dtype=np.uint8) * 255
    hero1_img[:, :, 1] = 200  # Green channel (for clubs)
    cv2.putText(hero1_img, "3", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    
    # Hero card 2 - Clubs (green) - different rank
    hero2_img = np.ones((100, 80, 3), dtype=np.uint8) * 255
    hero2_img[:, :, 1] = 200  # Green channel (for clubs)
    cv2.putText(hero2_img, "2", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    
    # Test recognizing individual hero cards
    logger.info("Testing recognition of individual hero cards:")
    hero1_result = recognizer.recognize_card(hero1_img, debug=debug)
    hero2_result = recognizer.recognize_card(hero2_img, debug=debug)
    
    logger.info(f"Hero card 1: {hero1_result['card_code']} ({hero1_result['card_name']}) - "
                f"Confidence: {hero1_result['confidence']:.2f}")
    logger.info(f"Hero card 2: {hero2_result['card_code']} ({hero2_result['card_name']}) - "
                f"Confidence: {hero2_result['confidence']:.2f}")
    
    # Test recognizing multiple cards through integration
    logger.info("Testing recognition through integration:")
    hero_cards = [hero1_img, hero2_img]
    results = recognizer.recognize_multiple_cards(hero_cards, debug=debug)
    
    recognized_cards = [r['card_code'] for r in results if not r['is_empty']]
    logger.info(f"Recognized hero cards: {recognized_cards}")
    
    # Check that the cards are different - duplicate prevention
    if len(set(recognized_cards)) == len(recognized_cards) and len(recognized_cards) == 2:
        logger.info("Hero cards are different - duplicate prevention working correctly")
        return True
    else:
        logger.error(f"Hero cards not recognized correctly or duplicate prevention failed")
        return False

def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test the direct card recognition system')
    parser.add_argument('--debug', action='store_true', help='Save debug images')
    parser.add_argument('--template-dir', default='card_templates', help='Directory with card templates')
    parser.add_argument('--test', choices=['all', 'empty', 'template', 'duplicate', 'integration'],
                       default='all', help='Which test to run')
    args = parser.parse_args()
    
    # Create recognizer
    recognizer = DirectCardRecognizer()
    
    # Run the requested tests
    tests_to_run = []
    if args.test == 'all':
        tests_to_run = ['empty', 'duplicate', 'template', 'integration']
    else:
        tests_to_run = [args.test]
    
    # Store test results
    test_results = {}
    
    # Run tests
    if 'empty' in tests_to_run:
        test_results['empty_slot'] = test_empty_slot_detection(recognizer, args.debug)
    
    if 'duplicate' in tests_to_run:
        test_results['duplicate_detection'] = test_duplicate_detection(recognizer, args.debug)
    
    if 'template' in tests_to_run:
        test_results['template_directory'] = test_on_template_directory(
            recognizer, args.template_dir, args.debug)
    
    if 'integration' in tests_to_run:
        test_results['integration'] = test_integration(recognizer, args.debug)
    
    # Print summary
    logger.info("\n--- TEST SUMMARY ---")
    all_passed = True
    for test_name, passed in test_results.items():
        result = "PASSED" if passed else "FAILED"
        logger.info(f"{test_name}: {result}")
        if not passed:
            all_passed = False
    
    logger.info(f"Overall: {sum(test_results.values())}/{len(test_results)} tests passed")
    
    # Return success/failure
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
