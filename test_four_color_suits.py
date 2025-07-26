"""
Test the four-color suit detection in the improved card recognition system.

This script tests the improved card recognition system with the four-color suit detection
to verify it correctly identifies the suit colors: hearts (red), diamonds (blue),
clubs (green), and spades (black).
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
        logging.FileHandler('test_four_color_suits.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_four_color_suits')

# Import the improved card recognizer and color detector
from improved_card_recognition import ImprovedCardRecognizer, CardSuitColorDetector
from card_suit_color import SuitColorDetector

def test_color_detector_directly():
    """
    Test the CardSuitColorDetector directly on known card images.
    
    Returns:
        dict: Results with accuracy statistics
    """
    logger.info("Testing CardSuitColorDetector directly")
    
    # Create color detector
    color_detector = CardSuitColorDetector()
    
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
        'correct_colors': 0,
        'incorrect_colors': 0,
        'details': []
    }
    
    # Test each template
    for template_file in template_files:
        # Extract expected suit from filename
        filename = os.path.splitext(template_file)[0]  # Remove extension
        parts = filename.split('_')
        suit = parts[1].lower()
        
        # Determine expected color based on suit
        expected_color = None
        if suit.startswith('h'):  # hearts
            expected_color = 'red'
            expected_is = {'is_hearts': True, 'is_diamonds': False, 'is_clubs': False, 'is_spades': False}
        elif suit.startswith('d'):  # diamonds
            expected_color = 'blue'
            expected_is = {'is_hearts': False, 'is_diamonds': True, 'is_clubs': False, 'is_spades': False}
        elif suit.startswith('c'):  # clubs
            expected_color = 'green'
            expected_is = {'is_hearts': False, 'is_diamonds': False, 'is_clubs': True, 'is_spades': False}
        elif suit.startswith('s'):  # spades
            expected_color = 'black'
            expected_is = {'is_hearts': False, 'is_diamonds': False, 'is_clubs': False, 'is_spades': True}
        
        # Load and test template
        template_path = os.path.join(template_dir, template_file)
        template_img = cv2.imread(template_path)
        
        if template_img is None:
            logger.error(f"Failed to load template: {template_path}")
            continue
        
        # Analyze card colors
        color_info = color_detector.analyze_card(template_img, debug=True)
        
        # Determine detected color
        detected_color = None
        if color_info['is_hearts'] and color_info['red_percentage'] > 3.0:
            detected_color = 'red'
        elif color_info['is_diamonds'] and color_info['blue_percentage'] > 3.0:
            detected_color = 'blue'
        elif color_info['is_clubs'] and color_info['green_percentage'] > 3.0:
            detected_color = 'green'
        elif color_info['is_spades'] and color_info['black_percentage'] > 3.0:
            detected_color = 'black'
        
        # Check if the detected color matches the expected color
        is_correct = detected_color == expected_color
        
        # Check if the is_* flags match the expected values
        flags_correct = True
        for flag, expected_value in expected_is.items():
            if color_info[flag] != expected_value:
                flags_correct = False
                break
        
        # Update statistics
        if is_correct and flags_correct:
            results['correct_colors'] += 1
        else:
            results['incorrect_colors'] += 1
        
        # Add details
        results['details'].append({
            'filename': template_file,
            'suit': suit,
            'expected_color': expected_color,
            'detected_color': detected_color,
            'color_info': {
                'red_percentage': color_info['red_percentage'],
                'green_percentage': color_info['green_percentage'],
                'blue_percentage': color_info['blue_percentage'],
                'black_percentage': color_info['black_percentage'],
                'is_hearts': color_info['is_hearts'],
                'is_diamonds': color_info['is_diamonds'],
                'is_clubs': color_info['is_clubs'],
                'is_spades': color_info['is_spades']
            },
            'is_correct': is_correct and flags_correct
        })
        
        # Log result
        logger.info(f"Template {template_file}: Expected {expected_color}, Detected {detected_color}, Correct: {is_correct and flags_correct}")
        if not is_correct:
            logger.warning(f"  Color mismatch: Expected {expected_color}, got {detected_color}")
        if not flags_correct:
            logger.warning(f"  Flag mismatch: {expected_is} vs. {color_info}")
    
    # Calculate accuracy
    if results['total'] > 0:
        results['accuracy'] = results['correct_colors'] / results['total'] * 100
    else:
        results['accuracy'] = 0
    
    logger.info(f"Color detection results: {results['correct_colors']}/{results['total']} correct ({results['accuracy']:.1f}%)")
    
    return results

def test_full_recognition_with_color():
    """
    Test the full card recognition system with color verification.
    
    Returns:
        dict: Results with accuracy statistics
    """
    logger.info("Testing full recognition with color verification")
    
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
        result = recognizer.recognize_card(template_img, debug=True)
        
        # Check result
        is_correct = result['card_code'] == expected_code
        
        # Get color information
        color_info = result.get('color_info', {})
        
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
            'is_correct': is_correct,
            'color_info': color_info
        })
        
        # Log result
        logger.info(f"Template {template_file}: Expected {expected_code}, Got {result['card_code']}, Correct: {is_correct}")
        if not is_correct:
            logger.warning(f"  Recognition mismatch! Expected: {expected_code}, Got: {result['card_code']}")
            logger.warning(f"  Color info: red={color_info.get('red_percentage', 0):.2f}%, "
                           f"green={color_info.get('green_percentage', 0):.2f}%, "
                           f"blue={color_info.get('blue_percentage', 0):.2f}%, "
                           f"black={color_info.get('black_percentage', 0):.2f}%")
            logger.warning(f"  Is hearts: {color_info.get('is_hearts', False)}, "
                           f"Is diamonds: {color_info.get('is_diamonds', False)}, "
                           f"Is clubs: {color_info.get('is_clubs', False)}, "
                           f"Is spades: {color_info.get('is_spades', False)}")
    
    # Calculate accuracy
    if results['total'] > 0:
        results['accuracy'] = results['correct'] / results['total'] * 100
    else:
        results['accuracy'] = 0
    
    logger.info(f"Full recognition results: {results['correct']}/{results['total']} correct ({results['accuracy']:.1f}%)")
    
    return results

def run_tests():
    """Run all tests and report results."""
    logger.info("Starting four-color suit detection tests")
    
    # Run the tests
    color_results = test_color_detector_directly()
    recognition_results = test_full_recognition_with_color()
    
    # Report results
    logger.info("\n--- TEST SUMMARY ---")
    
    if color_results:
        logger.info(f"Color Detection Accuracy: {color_results['accuracy']:.1f}%")
    else:
        logger.info("Color Detection: FAILED")
    
    if recognition_results:
        logger.info(f"Full Recognition Accuracy: {recognition_results['accuracy']:.1f}%")
    else:
        logger.info("Full Recognition: FAILED")
    
    # Overall success
    success = (color_results is not None and recognition_results is not None and 
               color_results['accuracy'] > 80 and recognition_results['accuracy'] > 80)
    
    logger.info(f"Overall: {'PASSED' if success else 'FAILED'}")
    
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
