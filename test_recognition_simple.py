"""
Simple test script to check if the card recognition is working.
This script loads a sample image from debug_images and processes it.
"""

import os
import sys
import cv2
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.card_recognizer import CardRecognizer
from card_suit_color import CardSuitColorDetector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_recognition_simple')

def test_with_image(image_path):
    """Test card recognition with a single image."""
    logger.info(f"Testing card recognition with image: {os.path.basename(image_path)}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return
    
    # Initialize card recognizer
    card_recognizer = CardRecognizer()
    
    # Initialize color detector
    color_detector = CardSuitColorDetector()
    
    # Perform card recognition
    try:
        card_value, confidence, method = card_recognizer.recognize_card(image, debug=True)
        logger.info(f"Card recognition result: {card_value} (confidence: {confidence:.2f}, method: {method})")
        
        # Analyze color
        color_result = color_detector.analyze_card_image(image_path)
        if color_result:
            logger.info(f"Color analysis: red={color_result['red_percentage']:.2f}%, black={color_result['black_percentage']:.2f}%")
            logger.info(f"Predicted suit color: {color_result['suit_color']}")
        
        # Check if color matches the recognized card
        if card_value and len(card_value) >= 2:
            suit = card_value[-1]
            expected_color = "red" if suit in ['h', 'd'] else "black"
            actual_color = color_result['suit_color'] if color_result else "unknown"
            
            if expected_color == actual_color:
                logger.info(f"✅ Color verification passed: {expected_color}")
            else:
                logger.info(f"❌ Color verification failed: expected {expected_color}, got {actual_color}")
        
        return card_value, confidence, method
        
    except Exception as e:
        logger.error(f"Error during card recognition: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, 0.0, "error"

def main():
    # Get a sample image from debug_images
    debug_dir = "debug_images"
    analysis_images = [f for f in os.listdir(debug_dir) if f.startswith('analysis_') and f.endswith('.png')]
    
    if not analysis_images:
        logger.error(f"No analysis images found in {debug_dir}")
        return
    
    # Use the first image for testing
    test_image = os.path.join(debug_dir, analysis_images[0])
    logger.info(f"Using test image: {test_image}")
    
    # Test recognition
    result = test_with_image(test_image)
    
    # Log result
    if result and result[0]:
        logger.info(f"Test completed successfully: {result[0]}")
    else:
        logger.info("Test completed with errors")

if __name__ == "__main__":
    main()
