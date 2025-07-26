"""
Basic Color Recognition Test

This script tests the color-based suit detection capabilities.
"""

import os
import sys
import cv2
import numpy as np
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import ColorSuitDetector
try:
    from src.card_suit_color_detector import CardSuitColorDetector
except ImportError:
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
        from card_suit_color_detector import CardSuitColorDetector
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure the src directory contains all required modules.")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('color_detector_test')

def test_image(image_path, debug=False):
    """
    Test color detection on a single image.
    
    Args:
        image_path: Path to the image file
        debug: Enable debug mode
        
    Returns:
        Tuple of (color, confidence)
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Failed to load image: {image_path}")
        return None, 0
    
    # Create detector
    detector = CardSuitColorDetector()
    
    # Detect color
    color, confidence = detector.detect_suit_color(img, debug)
    
    # Log result
    logger.info(f"Image: {os.path.basename(image_path)}")
    logger.info(f"  Detected color: {color}")
    logger.info(f"  Confidence: {confidence:.3f}")
    
    return color, confidence

def test_directory(directory_path, debug=False):
    """
    Test all images in a directory.
    
    Args:
        directory_path: Path to directory with images
        debug: Enable debug mode
    """
    # Find all image files
    image_files = []
    for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        image_files.extend(Path(directory_path).glob(f"*{ext}"))
    
    logger.info(f"Testing {len(image_files)} images in {directory_path}")
    
    # Process each image
    red_count = 0
    black_count = 0
    unknown_count = 0
    
    for image_path in image_files:
        color, _ = test_image(str(image_path), debug)
        
        if color == 'red':
            red_count += 1
        elif color == 'black':
            black_count += 1
        else:
            unknown_count += 1
    
    # Print summary
    logger.info("Results summary:")
    logger.info(f"  Total images: {len(image_files)}")
    logger.info(f"  Red suits: {red_count}")
    logger.info(f"  Black suits: {black_count}")
    logger.info(f"  Unknown: {unknown_count}")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test color-based suit detection")
    parser.add_argument("--image", help="Path to a single image")
    parser.add_argument("--dir", help="Path to a directory with images")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Run test
    if args.image:
        test_image(args.image, args.debug)
    elif args.dir:
        test_directory(args.dir, args.debug)
    else:
        logger.error("No image or directory specified")
        parser.print_help()

if __name__ == "__main__":
    main()
