"""
Enhanced Card Recognition Test Tool
----------------------------------
This tool analyzes specific card images and reports detailed recognition results.
"""

import os
import sys
import argparse
import logging
import cv2
import numpy as np
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our card recognition components
from card_recognizer import CardRecognizer
from card_suit_color import CardSuitColorDetector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_recognition_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("enhanced_recognition_test")

def analyze_card_image(image_path):
    """Analyze a single card image and report detailed results."""
    logger.info(f"Analyzing card image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return None
    
    # Create output directory
    os.makedirs("test_output", exist_ok=True)
    
    # Initialize components
    card_recognizer = CardRecognizer()
    color_detector = CardSuitColorDetector()
    
    # 1. Get color analysis
    color_result = color_detector.analyze_card_image(image_path)
    
    if color_result:
        logger.info(f"Card color analysis:")
        logger.info(f"  - Red pixels: {color_result['red_percentage']:.2f}%")
        logger.info(f"  - Black pixels: {color_result['black_percentage']:.2f}%")
        logger.info(f"  - Predicted suit color: {color_result['suit_color']}")
    
    # 2. Run template matching recognition
    card_value, confidence, method = card_recognizer.recognize_card(image, debug=True)
    
    logger.info(f"Card recognition results:")
    logger.info(f"  - Recognized value: {card_value}")
    logger.info(f"  - Confidence: {confidence:.2f}")
    logger.info(f"  - Method: {method}")
    
    # 3. Save a visualization
    result_img = image.copy()
    text = f"{card_value} ({confidence:.2f})"
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(result_img, text, (10, 30), font, 0.7, (0, 255, 0), 2)
    
    output_path = os.path.join("test_output", f"result_{os.path.basename(image_path)}")
    cv2.imwrite(output_path, result_img)
    
    return {
        "image_path": image_path,
        "color_result": color_result,
        "recognized_value": card_value,
        "confidence": confidence,
        "method": method
    }

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
    
    # Generate filename
    output_path = os.path.join("test_output", f"{value}_{suit}_test.png")
    cv2.imwrite(output_path, card)
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Enhanced card recognition test')
    parser.add_argument('--image', help='Path to card image for analysis')
    parser.add_argument('--generate-test', action='store_true', help='Generate test cards')
    parser.add_argument('--dir', help='Path to directory of card images')
    
    args = parser.parse_args()
    
    results = []
    
    if args.generate_test:
        logger.info("Generating test cards...")
        # Generate test cards for all combinations
        suits = ["red", "black"]
        values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        
        for suit in suits:
            for value in values:
                output_path = create_test_card(suit, value)
                logger.info(f"Generated test card: {output_path}")
                
                # Analyze the generated card
                result = analyze_card_image(output_path)
                results.append(result)
    
    elif args.image:
        # Analyze a single image
        result = analyze_card_image(args.image)
        results.append(result)
    
    elif args.dir:
        # Analyze all images in a directory
        if not os.path.exists(args.dir):
            logger.error(f"Directory not found: {args.dir}")
            return
            
        image_files = [f for f in os.listdir(args.dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        for image_file in image_files:
            image_path = os.path.join(args.dir, image_file)
            result = analyze_card_image(image_path)
            results.append(result)
    
    else:
        logger.error("Please specify --image, --dir, or --generate-test")
        parser.print_help()
        return
    
    # Generate summary report
    summary_path = "test_output/recognition_summary.txt"
    with open(summary_path, "w") as f:
        f.write("Enhanced Card Recognition Test Summary\n")
        f.write("====================================\n\n")
        
        for result in results:
            if result:
                f.write(f"Image: {os.path.basename(result['image_path'])}\n")
                
                if result['color_result']:
                    f.write(f"  - Red pixels: {result['color_result']['red_percentage']:.2f}%\n")
                    f.write(f"  - Black pixels: {result['color_result']['black_percentage']:.2f}%\n")
                    f.write(f"  - Predicted suit color: {result['color_result']['suit_color']}\n")
                
                f.write(f"  - Recognized value: {result['recognized_value']}\n")
                f.write(f"  - Confidence: {result['confidence']:.2f}\n")
                f.write(f"  - Method: {result['method']}\n\n")
    
    logger.info(f"Test summary saved to {summary_path}")

if __name__ == "__main__":
    main()
