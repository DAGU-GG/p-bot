"""
Card Suit Color Detector

This script analyzes card images to determine if they are red suits (hearts/diamonds)
or black suits (clubs/spades) based on color analysis.

Usage:
    python card_suit_color.py [--image PATH_TO_IMAGE] [--directory PATH_TO_CARD_DIRECTORY]
"""

import os
import sys
import argparse
import cv2
import numpy as np
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('card_suit_color.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('card_suit_color')

class CardSuitColorDetector:
    def __init__(self):
        # Create output directory
        os.makedirs("debug_cards/color_analysis", exist_ok=True)
    
    def analyze_card_image(self, image_path, output_prefix=""):
        """Analyze a card image to determine suit color."""
        logger.info(f"Analyzing card image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return None
        
        # Create output path for debug images
        image_name = os.path.basename(image_path)
        output_dir = "debug_cards/color_analysis"
        
        # Save original image
        cv2.imwrite(os.path.join(output_dir, f"{output_prefix}original_{image_name}"), image)
        
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges
        # Red in HSV wraps around the hue space, so we need two ranges
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        # Black in HSV
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 50])
        
        # Create masks
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        
        black_mask = cv2.inRange(hsv, lower_black, upper_black)
        
        # Save mask images
        cv2.imwrite(os.path.join(output_dir, f"{output_prefix}red_mask_{image_name}"), red_mask)
        cv2.imwrite(os.path.join(output_dir, f"{output_prefix}black_mask_{image_name}"), black_mask)
        
        # Count pixels
        red_pixels = np.count_nonzero(red_mask)
        black_pixels = np.count_nonzero(black_mask)
        total_pixels = red_mask.size
        
        # Calculate percentages
        red_percentage = (red_pixels / total_pixels) * 100
        black_percentage = (black_pixels / total_pixels) * 100
        
        # Determine suit color
        suit_color = "unknown"
        if red_percentage > 5 and red_percentage > black_percentage:
            suit_color = "red"  # Hearts or Diamonds
        elif black_percentage > 5 and black_percentage > red_percentage:
            suit_color = "black"  # Clubs or Spades
        
        logger.info(f"Card analysis results:")
        logger.info(f"  - Red pixels: {red_pixels} ({red_percentage:.2f}%)")
        logger.info(f"  - Black pixels: {black_pixels} ({black_percentage:.2f}%)")
        logger.info(f"  - Predicted suit color: {suit_color}")
        
        # Create visualization
        visualization = np.zeros((image.shape[0], image.shape[1] * 3, 3), dtype=np.uint8)
        
        # Original image
        visualization[:, :image.shape[1]] = image
        
        # Red mask (show in red)
        red_mask_vis = np.zeros_like(image)
        red_mask_vis[:, :, 2] = red_mask  # Red channel
        visualization[:, image.shape[1]:image.shape[1]*2] = red_mask_vis
        
        # Black mask (show in gray)
        black_mask_vis = np.zeros_like(image)
        black_mask_vis[:, :, 0] = black_mask  # Blue channel = Gray
        black_mask_vis[:, :, 1] = black_mask  # Green channel = Gray
        black_mask_vis[:, :, 2] = black_mask  # Red channel = Gray
        visualization[:, image.shape[1]*2:] = black_mask_vis
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(visualization, "Original", (10, 20), font, 0.5, (255, 255, 255), 1)
        cv2.putText(visualization, "Red Mask", (image.shape[1] + 10, 20), font, 0.5, (255, 255, 255), 1)
        cv2.putText(visualization, "Black Mask", (image.shape[1] * 2 + 10, 20), font, 0.5, (255, 255, 255), 1)
        
        # Add result text
        result_text = f"Red: {red_percentage:.1f}% | Black: {black_percentage:.1f}% | Color: {suit_color.upper()}"
        cv2.putText(visualization, result_text, (10, image.shape[0] - 10), font, 0.5, (255, 255, 255), 1)
        
        # Save visualization
        cv2.imwrite(os.path.join(output_dir, f"{output_prefix}visualization_{image_name}"), visualization)
        
        return {
            "image_path": image_path,
            "red_percentage": red_percentage,
            "black_percentage": black_percentage,
            "suit_color": suit_color,
            "visualization_path": os.path.join(output_dir, f"{output_prefix}visualization_{image_name}")
        }
    
    def analyze_directory(self, directory_path):
        """Analyze all card images in a directory."""
        logger.info(f"Analyzing all card images in directory: {directory_path}")
        
        results = []
        
        # Get all image files
        image_files = [f for f in os.listdir(directory_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        for i, image_file in enumerate(image_files):
            image_path = os.path.join(directory_path, image_file)
            prefix = f"{i+1:03d}_"  # Add numerical prefix for sorting
            result = self.analyze_card_image(image_path, prefix)
            if result:
                results.append(result)
        
        # Generate summary
        summary_path = os.path.join("debug_cards/color_analysis", "summary.txt")
        with open(summary_path, "w") as f:
            f.write("Card Suit Color Analysis Summary\n")
            f.write("===============================\n\n")
            
            for result in results:
                f.write(f"Image: {os.path.basename(result['image_path'])}\n")
                f.write(f"  - Red: {result['red_percentage']:.2f}%\n")
                f.write(f"  - Black: {result['black_percentage']:.2f}%\n")
                f.write(f"  - Predicted suit color: {result['suit_color'].upper()}\n")
                f.write(f"  - Visualization: {os.path.basename(result['visualization_path'])}\n\n")
        
        logger.info(f"Analysis complete. Summary saved to {summary_path}")
        return results

def main():
    parser = argparse.ArgumentParser(description='Analyze card suit colors')
    parser.add_argument('--image', help='Path to card image for analysis')
    parser.add_argument('--directory', help='Path to directory of card images')
    
    args = parser.parse_args()
    
    detector = CardSuitColorDetector()
    
    if args.image:
        detector.analyze_card_image(args.image)
    elif args.directory:
        detector.analyze_directory(args.directory)
    else:
        logger.error("Please specify either --image or --directory")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
