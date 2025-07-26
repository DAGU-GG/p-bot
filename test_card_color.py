"""
Test the card color detection functionality

This script creates a test image with a red and a black card and tests the color detection.
"""

import os
import sys
import cv2
import numpy as np
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our card recognition components
from card_suit_color import CardSuitColorDetector
from card_recognizer import CardRecognizer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_card_color")

def create_test_card(suit_color, value="Q"):
    """Create a simple test card with either red or black suit."""
    # Create white card
    card_width, card_height = 80, 120
    card = np.ones((card_height, card_width, 3), dtype=np.uint8) * 255
    
    # Add black border
    border_width = 2
    card[0:border_width, :] = [0, 0, 0]  # Top border
    card[-border_width:, :] = [0, 0, 0]  # Bottom border
    card[:, 0:border_width] = [0, 0, 0]  # Left border
    card[:, -border_width:] = [0, 0, 0]  # Right border
    
    # Add symbol in the center
    center_x, center_y = card_width // 2, card_height // 2
    size = min(card_width, card_height) // 4
    
    # Diamond shape for red card, club shape for black card
    if suit_color == "red":
        # Diamond shape (red)
        pts = np.array([
            [center_x, center_y - size],  # Top
            [center_x + size, center_y],  # Right
            [center_x, center_y + size],  # Bottom
            [center_x - size, center_y]   # Left
        ], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.fillPoly(card, [pts], (0, 0, 255))  # Red color
        suit = "diamond"
    else:
        # Club shape (simplified, black)
        radius = size // 2
        cv2.circle(card, (center_x, center_y - radius), radius, (0, 0, 0), -1)  # Top circle
        cv2.circle(card, (center_x - radius, center_y + radius), radius, (0, 0, 0), -1)  # Bottom left
        cv2.circle(card, (center_x + radius, center_y + radius), radius, (0, 0, 0), -1)  # Bottom right
        # Stem
        cv2.rectangle(card, (center_x - radius//2, center_y), (center_x + radius//2, center_y + size), (0, 0, 0), -1)
        suit = "club"
    
    # Add card value (letter)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(card, value, (10, 30), font, 1, (0, 0, 0), 2)
    
    return card, f"{value}_{suit}"

def main():
    # Create output directory
    os.makedirs("test_output", exist_ok=True)
    
    # Create test cards
    red_card, red_card_name = create_test_card("red", "Q")
    black_card, black_card_name = create_test_card("black", "K")
    
    # Save test cards
    cv2.imwrite("test_output/red_card_test.png", red_card)
    cv2.imwrite("test_output/black_card_test.png", black_card)
    
    logger.info("Created test cards")
    
    # Initialize components
    color_detector = CardSuitColorDetector()
    card_recognizer = CardRecognizer()
    
    # Test red card
    logger.info("Testing red card...")
    red_card_path = "test_output/red_card_test.png"
    red_result = color_detector.analyze_card_image(red_card_path)
    
    if red_result:
        logger.info(f"Red card analysis:")
        logger.info(f"  Red: {red_result['red_percentage']:.2f}%")
        logger.info(f"  Black: {red_result['black_percentage']:.2f}%")
        logger.info(f"  Color prediction: {red_result['suit_color']}")
    
    # Test recognition
    card_value, confidence, method = card_recognizer.recognize_card(red_card, debug=True)
    logger.info(f"Red card recognition: {card_value} ({confidence:.2f}) via {method}")
    
    # Test black card
    logger.info("\nTesting black card...")
    black_card_path = "test_output/black_card_test.png"
    black_result = color_detector.analyze_card_image(black_card_path)
    
    if black_result:
        logger.info(f"Black card analysis:")
        logger.info(f"  Red: {black_result['red_percentage']:.2f}%")
        logger.info(f"  Black: {black_result['black_percentage']:.2f}%")
        logger.info(f"  Color prediction: {black_result['suit_color']}")
    
    # Test recognition
    card_value, confidence, method = card_recognizer.recognize_card(black_card, debug=True)
    logger.info(f"Black card recognition: {card_value} ({confidence:.2f}) via {method}")
    
    logger.info("Color detection test complete!")

if __name__ == "__main__":
    main()
