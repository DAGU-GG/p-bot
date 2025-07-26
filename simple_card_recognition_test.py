"""
Simple Card Recognition Test
---------------------------
A basic test script that loads an image and runs the card recognition directly.
"""

import os
import sys
import cv2
import logging
import time
import numpy as np
import matplotlib.pyplot as plt
import argparse

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from card_recognizer import CardRecognizer
from card_suit_color import CardSuitColorDetector

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_card_recognition_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple_card_recognition_test')

def analyze_image(image_path):
    """Analyze a single card image using both recognition methods."""
    logger.info(f"Analyzing card image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return None
    
    # Initialize components
    card_recognizer = CardRecognizer()
    color_detector = CardSuitColorDetector()
    
    # Analyze with card recognizer
    card_value, confidence, method = card_recognizer.recognize_card(image, debug=True)
    
    # Analyze color
    color_result = color_detector.analyze_card_image(image_path)
    
    if color_result:
        red_percentage = color_result.get('red_percentage', 0)
        black_percentage = color_result.get('black_percentage', 0)
        suit_color = color_result.get('suit_color', 'unknown')
        
        logger.info("Card color analysis:")
        logger.info(f"  - Red pixels: {red_percentage:.2f}%")
        logger.info(f"  - Black pixels: {black_percentage:.2f}%")
        
        if suit_color == 'red':
            predicted_suit_color = "red (hearts/diamonds)"
        else:
            predicted_suit_color = "black (clubs/spades)"
            
        logger.info(f"  - Predicted suit color: {predicted_suit_color}")
    else:
        predicted_suit_color = "unknown"
        suit_color = "unknown"
        logger.error("Could not analyze card color")
    
    # Print results
    logger.info(f"Recognition Results:")
    logger.info(f"  - Card Value: {card_value}")
    logger.info(f"  - Confidence: {confidence:.2f}")
    logger.info(f"  - Method: {method}")
    logger.info(f"  - Suit Color: {suit_color}")
    
    return {
        'card_value': card_value,
        'confidence': confidence,
        'method': method,
        'suit_color': suit_color,
        'image': image
    }

def analyze_directory(directory_path):
    """Analyze all card images in a directory."""
    logger.info(f"Analyzing all card images in directory: {directory_path}")
    
    results = []
    
    # Get all image files
    image_files = [f for f in os.listdir(directory_path) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    for image_file in image_files:
        image_path = os.path.join(directory_path, image_file)
        result = analyze_image(image_path)
        if result:
            results.append((image_file, result))
    
    # Generate summary
    if results:
        logger.info("\nSummary of results:")
        for image_file, result in results:
            logger.info(f"{image_file}: {result['card_value']} ({result['confidence']:.2f}), {result['suit_color']}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Test card recognition')
    parser.add_argument('--image', help='Path to card image for testing')
    parser.add_argument('--directory', help='Path to directory of card images')
    
    args = parser.parse_args()
    
    if args.image:
        analyze_image(args.image)
    elif args.directory:
        analyze_directory(args.directory)
    elif len(sys.argv) > 1:
        # Legacy support for direct image path
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            analyze_image(image_path)
        else:
            logger.error(f"Image not found: {image_path}")
            sys.exit(1)
    else:
        # If no arguments, look for debug_cards directory
        if os.path.exists('debug_cards'):
            analyze_directory('debug_cards')
        else:
            logger.error("Please specify either --image or --directory, or create a debug_cards directory")
            parser.print_help()
            sys.exit(1)

if __name__ == "__main__":
    main()
