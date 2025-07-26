"""
Card Recognition Debug Tool (Fixed Version)
--------------------------
This tool helps diagnose card recognition issues by:
1. Running card recognition on sample images
2. Showing each stage of the recognition process
3. Displaying detailed debug information
4. Saving debug images for analysis

Usage:
    python debug_card_recognition_fixed.py [--image PATH_TO_IMAGE]
    
    --image: Path to a card image for testing
"""

import os
import sys
import time
import argparse
import logging
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from card_recognizer import CardRecognizer
from community_card_detector import CommunityCardDetector
from region_loader import RegionLoader

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_card_recognition_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('debug_card_recognition_fixed')

class CardRecognitionDebugger:
    def __init__(self):
        self.card_recognizer = CardRecognizer()
        self.region_loader = RegionLoader()
        self.community_card_detector = CommunityCardDetector(self.card_recognizer)
        
        # Ensure debug directories exist
        os.makedirs("debug_images", exist_ok=True)
        os.makedirs("debug_cards", exist_ok=True)
        
        logger.info("Card Recognition Debugger initialized")
        
    def process_and_display(self, image_path, save_results=True):
        """Process a card image and display all recognition steps."""
        logger.info(f"Processing image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return None
            
        # Start timing
        start_time = time.time()
        os.makedirs('debug_images', exist_ok=True)
        os.makedirs('debug_cards', exist_ok=True)
        os.makedirs('debug_community', exist_ok=True)
        
        # Store preprocessing variants
        self.preprocessing_variants = []
        
    def debug_single_image(self, image_path):
        """Debug card recognition on a single image."""
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return
            
        logger.info(f"Debugging card recognition for image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return
            
        # Process image
        self._process_and_display(image, os.path.basename(image_path))
    
    def _process_and_display(self, image, image_name):
        """Process an image through all recognition steps and display debug info."""
        timestamp = int(time.time())
        
        # 1. Extract card regions from image or use the full image if no regions
        card_images = []
        
        # Check if we should try to extract regions or use the whole image
        if image.shape[0] > 200:  # If it's a large image, try to extract regions
            regions = self.region_loader.get_community_card_regions()
            
            # Extract each card region
            for i, region in enumerate(regions):
                try:
                    x, y, w, h = region
                    card_img = image[y:y+h, x:x+w]
                    card_images.append((f"Community Card {i+1}", card_img))
                    
                    # Save extracted card region
                    cv2.imwrite(f"debug_cards/card_region_{i+1}_{timestamp}.png", card_img)
                except Exception as e:
                    logger.error(f"Error extracting card region {i+1}: {e}")
            
            # Add hero cards if available
            hero_regions = self.region_loader.get_hero_card_regions()
            for i, region in enumerate(hero_regions):
                try:
                    x, y, w, h = region
                    card_img = image[y:y+h, x:x+w]
                    card_images.append((f"Hero Card {i+1}", card_img))
                    
                    # Save extracted card region
                    cv2.imwrite(f"debug_cards/card_hero_card{i+1}_{timestamp}.png", card_img)
                except Exception as e:
                    logger.error(f"Error extracting hero card region {i+1}: {e}")
        else:
            # Treat the input as a single card image
            card_images.append(("Input Card", image))
            cv2.imwrite(f"debug_cards/single_card_{timestamp}.png", image)
        
        # 2. Process each card
        if not card_images:
            logger.warning("No card images extracted. Check if the image contains valid card regions.")
            plt.figure(figsize=(10, 5))
            plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            plt.title("Input Image - No Cards Detected")
            plt.savefig(f"debug_images/no_cards_detected_{timestamp}.png")
            return
            
        recognition_results = []
        
        # For each card image, perform recognition and collect results
        for card_name, card_img in card_images:
            if card_img is None or card_img.size == 0:
                logger.warning(f"Empty card image for {card_name}")
                continue
                
            # Save card image
            cv2.imwrite(f"debug_cards/{card_name.replace(' ', '_').lower()}_{timestamp}.png", card_img)
            
            # Check if card is present
            is_present = True  # Assume presence for now
            if hasattr(self.community_card_detector, '_is_card_present'):
                is_present = self.community_card_detector._is_card_present(card_img)
            
            # Process card for recognition if present
            if is_present:
                # Recognize card
                card_value, confidence, method = self.card_recognizer.recognize_card(card_img, debug=True)
                
                # Get template matching results if available
                template_results = getattr(self.card_recognizer, 'debug_template_results', [])
                
                logger.info(f"Card {card_name}: Recognized as {card_value} (confidence: {confidence:.2f}, method: {method})")
                
                # Create visualization with the recognition result
                result_img = card_img.copy()
                text = f"{card_value} ({confidence:.2f})"
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(result_img, text, (10, 30), font, 0.7, (0, 255, 0), 2)
                
                # Save result image
                cv2.imwrite(f"debug_cards/{card_name.replace(' ', '_').lower()}_result_{timestamp}.png", result_img)
                
                recognition_results.append({
                    'card_name': card_name,
                    'is_present': is_present,
                    'card_value': card_value,
                    'confidence': confidence,
                    'method': method,
                    'template_results': template_results[:5] if template_results else []  # Top 5 matches
                })
            else:
                logger.info(f"Card {card_name}: No card detected")
        
        # Generate summary file
        summary_path = f"debug_cards/summary_{timestamp}.txt"
        with open(summary_path, "w") as f:
            f.write("Card Recognition Debug Summary\n")
            f.write("=============================\n\n")
            
            for result in recognition_results:
                f.write(f"Card: {result['card_name']}\n")
                f.write(f"  - Recognized as: {result['card_value']}\n")
                f.write(f"  - Confidence: {result['confidence']:.2f}\n")
                f.write(f"  - Method: {result['method']}\n")
                
                if result['template_results']:
                    f.write("  - Top template matches:\n")
                    for i, (template, score) in enumerate(result['template_results']):
                        f.write(f"    {i+1}. {template}: {score:.2f}\n")
                
                f.write("\n")
        
        logger.info(f"Debug summary saved to {summary_path}")

def main():
    parser = argparse.ArgumentParser(description='Debug card recognition')
    parser.add_argument('--image', help='Path to image for analysis')
    
    args = parser.parse_args()
    
    debugger = CardRecognitionDebugger()
    
    if args.image:
        debugger.debug_single_image(args.image)
    else:
        logger.error("Please specify an image with --image")
        parser.print_help()
        sys.exit(1)
    
    logger.info("Debug complete. Check debug_images directory for results.")

if __name__ == "__main__":
    main()
