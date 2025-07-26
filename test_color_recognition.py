"""
Test the color-based card recognition with images from the debug_images directory.
"""

import os
import cv2
import logging
import argparse
import numpy as np
import time
import sys

# Add src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.color_based_card_recognizer import ColorBasedCardRecognizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_color_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_color_recognition')

def test_image(image_path, debug=True):
    """Test card recognition on a single image."""
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Could not load image: {image_path}")
        return None
    
    # Create recognizer
    recognizer = ColorBasedCardRecognizer()
    
    # Process the image
    start_time = time.time()
    card = recognizer.recognize_card(image, debug=debug)
    elapsed = time.time() - start_time
    
    if card:
        logger.info(f"Card recognized: {card.rank}{card.suit} (confidence: {card.confidence:.2f}, time: {elapsed:.3f}s)")
        
        # Create a display image
        display = image.copy()
        h, w = display.shape[:2]
        
        # Add text with card info
        text = f"{card.rank}{card.suit} - {card.confidence:.2f}"
        cv2.putText(display, text, (10, h-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Save the annotated image
        output_path = os.path.join("debug_color_recognition", f"result_{os.path.basename(image_path)}")
        cv2.imwrite(output_path, display)
        logger.info(f"Saved annotated image to {output_path}")
        
        return card
    else:
        logger.warning(f"No card recognized in {image_path}")
        return None

def test_directory(directory_path, debug=True):
    """Test card recognition on all images in a directory."""
    if not os.path.isdir(directory_path):
        logger.error(f"Directory does not exist: {directory_path}")
        return []
    
    # Create recognizer
    recognizer = ColorBasedCardRecognizer()
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = [f for f in os.listdir(directory_path) 
                  if os.path.splitext(f)[1].lower() in image_extensions]
    
    if not image_files:
        logger.error(f"No image files found in {directory_path}")
        return []
        
    logger.info(f"Testing {len(image_files)} images in {directory_path}")
    
    # Process each image
    results = []
    for filename in image_files:
        file_path = os.path.join(directory_path, filename)
        logger.info(f"Processing {filename}...")
        
        card = test_image(file_path, debug=debug)
        if card:
            results.append((filename, card, True))
        else:
            results.append((filename, None, False))
    
    # Display summary
    success_count = sum(1 for _, _, success in results if success)
    logger.info(f"Recognition summary: {success_count}/{len(results)} cards recognized successfully")
    
    # Generate detailed report
    report_path = os.path.join("debug_color_recognition", "recognition_report.txt")
    with open(report_path, "w") as f:
        f.write(f"Color-Based Card Recognition Report\n")
        f.write(f"================================\n\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total images processed: {len(results)}\n")
        f.write(f"Successfully recognized: {success_count}\n")
        f.write(f"Success rate: {success_count/len(results)*100:.1f}%\n\n")
        
        f.write("Detailed Results:\n")
        f.write("-----------------\n\n")
        
        for filename, card, success in results:
            if success:
                f.write(f"{filename}: {card.rank}{card.suit} (confidence: {card.confidence:.2f})\n")
            else:
                f.write(f"{filename}: FAILED\n")
    
    logger.info(f"Detailed report saved to {report_path}")
    return results

def extract_card_regions(image_path, debug=True):
    """Extract individual card regions from a poker table screenshot."""
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Could not load image: {image_path}")
        return []
    
    # TODO: Implement card extraction from full table view
    # For now, just use the whole image as a single card
    card_regions = [image]
    
    if debug:
        # Save the extracted regions
        os.makedirs("debug_color_recognition/extracted_cards", exist_ok=True)
        for i, card in enumerate(card_regions):
            output_path = os.path.join("debug_color_recognition/extracted_cards", f"card_{i}_{os.path.basename(image_path)}")
            cv2.imwrite(output_path, card)
    
    return card_regions

def main():
    parser = argparse.ArgumentParser(description="Test color-based card recognition")
    parser.add_argument("--image", help="Path to a single image file to test")
    parser.add_argument("--dir", help="Path to directory containing images to test")
    parser.add_argument("--extract", action="store_true", help="Extract card regions from table screenshots")
    parser.add_argument("--debug", action="store_true", help="Save debug images", default=True)
    
    args = parser.parse_args()
    
    # Make sure debug directory exists
    os.makedirs("debug_color_recognition", exist_ok=True)
    
    if args.image:
        if args.extract:
            card_regions = extract_card_regions(args.image, debug=args.debug)
            for i, card_img in enumerate(card_regions):
                logger.info(f"Processing extracted card {i+1}...")
                card_path = os.path.join("debug_color_recognition/extracted_cards", f"card_{i}_{os.path.basename(args.image)}")
                test_image(card_path, debug=args.debug)
        else:
            test_image(args.image, debug=args.debug)
    elif args.dir:
        test_directory(args.dir, debug=args.debug)
    else:
        # Default to debug_images directory if it exists
        if os.path.isdir("debug_images"):
            test_directory("debug_images", debug=args.debug)
        # Or screenshots if that exists
        elif os.path.isdir("screenshots"):
            test_directory("screenshots", debug=args.debug)
        else:
            logger.error("No image or directory specified and no default directories found")
            parser.print_help()

if __name__ == "__main__":
    main()
