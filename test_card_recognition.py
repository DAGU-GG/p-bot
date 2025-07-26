"""
Card Recognition Verification Tool

This script allows you to test the card recognition system on individual card images
or captured screenshots to verify accuracy and diagnose problems.

Usage:
    python test_card_recognition.py [--image PATH_TO_IMAGE] [--live]
"""

import os
import sys
import time
import argparse
import logging
import cv2
import numpy as np

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from card_recognizer import CardRecognizer
from region_loader import RegionLoader
from screen_capture import ScreenCaptureManager

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_card_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_card_recognition')

def test_card_recognition_on_image(image_path):
    """Test card recognition on a single image."""
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return
        
    logger.info(f"Testing card recognition on image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return
    
    # Initialize card recognizer
    card_recognizer = CardRecognizer()
    
    # Extract and test hero cards
    region_loader = RegionLoader()
    hero_regions = region_loader.get_hero_card_regions()
    
    if not hero_regions:
        logger.error("No hero card regions defined")
        return
    
    height, width = image.shape[:2]
    logger.info(f"Image dimensions: {width}x{height}")
    
    # Extract and recognize hero cards
    logger.info("Extracting hero cards...")
    
    for name, region in hero_regions.items():
        try:
            # Calculate pixel coordinates - convert percentage to decimals
            x_percent = region['x_percent'] / 100.0 if region['x_percent'] > 1 else region['x_percent']
            y_percent = region['y_percent'] / 100.0 if region['y_percent'] > 1 else region['y_percent']
            w_percent = region['width_percent'] / 100.0 if region['width_percent'] > 1 else region['width_percent']
            h_percent = region['height_percent'] / 100.0 if region['height_percent'] > 1 else region['height_percent']
            
            x = int(width * x_percent)
            y = int(height * y_percent)
            w = int(width * w_percent)
            h = int(height * h_percent)
            
            logger.info(f"Processing hero {name} region: x={x}, y={y}, w={w}, h={h}")
            
            # Ensure coordinates are within image bounds
            if x < 0 or y < 0 or x + w > width or y + h > height:
                logger.error(f"Region {name} is outside image bounds: {x},{y},{w},{h} - Image: {width}x{height}")
                continue
                
            # Extract card
            card_img = image[y:y+h, x:x+w].copy()
            
            if card_img.size == 0:
                logger.error(f"Extracted card image for {name} is empty")
                continue
                
            # Save extracted card
            timestamp = int(time.time() * 1000)
            cv2.imwrite(f"debug_cards/extracted_{name}_{timestamp}.png", card_img)
            
            # Recognize card
            logger.info(f"Recognizing card: {name}")
            card_value, confidence, method = card_recognizer.recognize_card(card_img, debug=True)
            
            logger.info(f"Card {name}: {card_value} (Confidence: {confidence:.3f}, Method: {method})")
        except Exception as e:
            logger.error(f"Error processing hero card {name}: {e}")
    
    # Test community cards
    community_regions = region_loader.get_community_card_regions()
    
    if not community_regions:
        logger.warning("No community card regions defined")
    else:
        logger.info(f"Extracting community cards... (found {len(community_regions)} regions)")
        
        for name, region in community_regions.items():
            try:
                # Calculate pixel coordinates - convert percentage to decimals
                x_percent = region['x_percent'] / 100.0 if region['x_percent'] > 1 else region['x_percent']
                y_percent = region['y_percent'] / 100.0 if region['y_percent'] > 1 else region['y_percent']
                w_percent = region['width_percent'] / 100.0 if region['width_percent'] > 1 else region['width_percent']
                h_percent = region['height_percent'] / 100.0 if region['height_percent'] > 1 else region['height_percent']
                
                x = int(width * x_percent)
                y = int(height * y_percent)
                w = int(width * w_percent)
                h = int(height * h_percent)
                
                logger.info(f"Processing community {name} region: x={x}, y={y}, w={w}, h={h}")
                
                # Ensure region is within image bounds
                if x >= 0 and y >= 0 and x+w <= width and y+h <= height:
                    card_img = image[y:y+h, x:x+w].copy()
                    
                    if card_img.size == 0:
                        logger.error(f"Extracted card image for {name} is empty")
                        continue
                    
                    # Save extracted card
                    timestamp = int(time.time() * 1000)
                    output_path = f"debug_cards/extracted_{name}_{timestamp}.png"
                    cv2.imwrite(output_path, card_img)
                    logger.info(f"Saved extracted card to {output_path}")
                    
                    # Recognize card
                    logger.info(f"Recognizing card: {name}")
                    card_value, confidence, method = card_recognizer.recognize_card(card_img, debug=True)
                    
                    logger.info(f"Card {name}: {card_value} (Confidence: {confidence:.3f}, Method: {method})")
                else:
                    logger.error(f"Region for {name} is outside image bounds: img={width}x{height}, region={x},{y},{w},{h}")
            except Exception as e:
                logger.error(f"Error processing card {name}: {e}")

def test_live_capture():
    """Test card recognition on live screen capture."""
    logger.info("Testing card recognition on live screen capture")
    
    # Initialize screen capture
    screen_capture = ScreenCaptureManager()
    
    # Create debug directories if they don't exist
    os.makedirs("debug_images", exist_ok=True)
    os.makedirs("debug_cards", exist_ok=True)
    
    # Capture screen
    logger.info("Capturing screen...")
    screen = screen_capture.capture_screen()
    if screen is None:
        logger.error("Failed to capture screen")
        return
    
    logger.info(f"Screen captured successfully. Size: {screen.shape}")
    
    # Save captured screen
    timestamp = int(time.time())
    output_path = f"debug_images/screen_capture_{timestamp}.png"
    cv2.imwrite(output_path, screen)
    logger.info(f"Saved screen capture to {output_path}")
    
    # Process the captured screen
    test_card_recognition_on_image(output_path)

def main():
    parser = argparse.ArgumentParser(description='Test card recognition')
    parser.add_argument('--image', help='Path to image for testing')
    parser.add_argument('--live', action='store_true', help='Use live screen capture')
    
    args = parser.parse_args()
    
    if args.image:
        test_card_recognition_on_image(args.image)
    elif args.live:
        test_live_capture()
    else:
        # If no arguments, use live capture
        test_live_capture()
        
    logger.info("Test complete. Check debug_cards directory for results.")

if __name__ == "__main__":
    main()
