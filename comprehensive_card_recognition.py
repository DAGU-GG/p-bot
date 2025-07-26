"""
Comprehensive Card Recognition System

This module integrates multiple recognition approaches with robust empty slot detection
to solve the issues with misidentifying empty slots as cards.

Features:
- Detects empty slots using image analysis
- Integrates multiple recognition methods
- Handles edge cases gracefully
- Provides detailed debugging output
"""

import os
import sys
import cv2
import numpy as np
import logging
import argparse
from pathlib import Path
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('comprehensive_recognition')

class EmptySlotDetector:
    """Detects if a card slot is empty or contains an actual card."""
    
    def __init__(self):
        # Create output directory
        os.makedirs("debug_cards/empty_detection", exist_ok=True)
    
    def detect(self, card_img, debug=False):
        """
        Analyze a card image to determine if it's empty or contains an actual card.
        
        Args:
            card_img: The card image (numpy array)
            debug: Whether to save debug images
            
        Returns:
            is_empty: Boolean indicating if the slot is empty
            confidence: Confidence score (0-1) of the detection
            debug_img: Debug visualization image if debug=True, otherwise None
        """
        if card_img is None or card_img.size == 0:
            return True, 1.0, None
        
        # Get image dimensions
        height, width = card_img.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Count edge pixels
        edge_count = np.count_nonzero(edges)
        edge_percentage = (edge_count / (width * height)) * 100
        
        # Measure standard deviation of pixel values (measure of contrast)
        contrast = np.std(gray)
        
        # Check color variation - convert to HSV and measure standard deviation
        hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
        hue_var = np.std(hsv[:,:,0])
        sat_var = np.std(hsv[:,:,1])
        
        # Calculate feature values
        features = {
            'edge_percentage': edge_percentage,
            'contrast': contrast,
            'hue_var': hue_var,
            'sat_var': sat_var
        }
        
        # Decision thresholds based on empirical testing
        is_empty = (
            edge_percentage < 4.0 and  # Low edge content
            contrast < 25.0 and        # Low contrast
            hue_var < 20.0 and         # Limited color variation
            sat_var < 35.0             # Low saturation variation
        )
        
        # Calculate confidence score (0-1)
        if is_empty:
            # Higher confidence when all metrics are very low
            confidence = min(1.0, (4.0 - edge_percentage) / 4.0 * 
                              (25.0 - contrast) / 25.0 * 
                              (20.0 - hue_var) / 20.0 * 
                              (35.0 - sat_var) / 35.0)
        else:
            # Higher confidence when metrics exceed thresholds
            confidence = min(1.0, edge_percentage / 8.0 * 
                              contrast / 50.0 * 
                              hue_var / 40.0 * 
                              sat_var / 70.0)
        
        # Create debug visualization if requested
        debug_img = None
        if debug:
            # Create visualization with fixed size text area
            text_width = max(width, 200)  # Ensure text area has minimum width
            
            # Handle very small images
            min_height = 100
            if height < min_height:
                scale = min_height / height
                vis_height = min_height
                card_vis = cv2.resize(card_img, (int(width * scale), vis_height), interpolation=cv2.INTER_NEAREST)
                edges_vis = cv2.resize(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), (int(width * scale), vis_height), interpolation=cv2.INTER_NEAREST)
                width_scaled = int(width * scale)
            else:
                vis_height = height
                card_vis = card_img.copy()
                edges_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                width_scaled = width
            
            # Create text area
            text_area = np.ones((vis_height, text_width, 3), dtype=np.uint8) * 255
            
            # Add feature text
            font = cv2.FONT_HERSHEY_SIMPLEX
            y_pos = 20
            cv2.putText(text_area, f"Edge %: {edge_percentage:.2f}%", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            y_pos += 15
            cv2.putText(text_area, f"Contrast: {contrast:.2f}", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            y_pos += 15
            cv2.putText(text_area, f"Hue var: {hue_var:.2f}", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            y_pos += 15
            cv2.putText(text_area, f"Sat var: {sat_var:.2f}", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            
            # Add result
            y_pos += 25
            result_text = "EMPTY SLOT" if is_empty else "CARD DETECTED"
            result_color = (0, 0, 200) if is_empty else (0, 200, 0)
            cv2.putText(text_area, result_text, (10, y_pos), font, 0.7, result_color, 2)
            
            # Add confidence
            y_pos += 20
            cv2.putText(text_area, f"Confidence: {confidence:.2f}", (10, y_pos), font, 0.5, result_color, 1)
            
            # Combine images
            visualization = np.hstack((card_vis, edges_vis, text_area))
            
            debug_img = visualization
        
        return is_empty, confidence, debug_img

class ColorAnalyzer:
    """Analyzes card colors to determine suit (red vs black)."""
    
    def analyze_color(self, card_img):
        """
        Analyze the color distribution of a card to determine if it's red or black.
        
        Args:
            card_img: The card image
            
        Returns:
            is_red: Boolean indicating if the card is red (hearts/diamonds)
            is_black: Boolean indicating if the card is black (clubs/spades)
            confidence: Confidence score of the color detection
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
        
        # Define red color ranges (in HSV)
        # Red wraps around in HSV, so we need two ranges
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([179, 255, 255])
        
        # Create masks for red areas
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # Define black color range
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 50])  # Low value = black
        
        # Create mask for black areas
        mask_black = cv2.inRange(hsv, lower_black, upper_black)
        
        # Count pixels
        total_pixels = card_img.shape[0] * card_img.shape[1]
        red_pixels = np.count_nonzero(mask_red)
        black_pixels = np.count_nonzero(mask_black)
        
        # Calculate ratios
        red_ratio = red_pixels / total_pixels
        black_ratio = black_pixels / total_pixels
        
        # Determine color based on ratios
        is_red = red_ratio > 0.05 and red_ratio > black_ratio
        is_black = black_ratio > 0.1 and black_ratio > red_ratio
        
        # Calculate confidence
        if is_red:
            confidence = min(1.0, red_ratio * 2)
        elif is_black:
            confidence = min(1.0, black_ratio)
        else:
            confidence = 0.0
            
        return is_red, is_black, confidence

class ComprehensiveCardRecognizer:
    """Enhanced card recognizer with multiple detection methods and empty slot detection."""
    
    def __init__(self):
        # Create output directories
        os.makedirs("debug_cards/comprehensive", exist_ok=True)
        
        # Initialize empty slot detector
        self.empty_detector = EmptySlotDetector()
        self.color_analyzer = ColorAnalyzer()
        
        # Load the original card recognizer
        try:
            from src.card_recognizer import CardRecognizer
            self.card_recognizer = CardRecognizer()
            logger.info("Successfully loaded original card recognizer")
        except ImportError as e:
            logger.error(f"Failed to import card recognizer: {e}")
            logger.error("Make sure the src directory is in the Python path")
            sys.exit(1)
    
    def recognize_card(self, card_img, debug=False):
        """
        Enhanced card recognition with empty slot detection.
        
        Args:
            card_img: The card image to recognize
            debug: Whether to save debug images
            
        Returns:
            result: Dictionary with recognition results
        """
        try:
            timestamp = int(time.time() * 1000)
            
            # First check if this is an empty slot
            is_empty, empty_confidence, empty_debug_img = self.empty_detector.detect(card_img, debug)
            
            if debug and empty_debug_img is not None:
                debug_path = f"debug_cards/comprehensive/empty_check_{timestamp}.png"
                cv2.imwrite(debug_path, empty_debug_img)
            
            # Log analysis results
            if debug:
                h, w = card_img.shape[:2]
                logger.info(f"Card image dimensions: {w}x{h}")
                
                if len(card_img.shape) == 3:
                    hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
                    h, s, v = cv2.split(hsv)
                    edge_percentage = np.count_nonzero(cv2.Canny(cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY), 50, 150)) / (card_img.shape[0] * card_img.shape[1]) * 100
                    contrast = np.std(cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY))
                    hue_var = np.std(h)
                    sat_var = np.std(s)
                    
                    logger.info(f"Edge percentage: {edge_percentage:.2f}%, contrast: {contrast:.2f}, "
                               f"hue var: {hue_var:.2f}, sat var: {sat_var:.2f}")
            
            # If empty with high confidence, return empty result
            if is_empty and empty_confidence > 0.7:
                logger.info(f"Detected empty slot with confidence {empty_confidence:.2f}")
                result = {
                    'card_code': 'empty',
                    'confidence': empty_confidence,
                    'method': 'empty_slot_detection',
                    'is_empty': True,
                    'error': None
                }
                return result
            
            # If not empty, proceed with card recognition
            logger.info("Card detected with valid features!")
            
            # First try color analysis to determine suit color
            is_red, is_black, color_confidence = self.color_analyzer.analyze_color(card_img)
            
            # Proceed with template matching
            try:
                card_code, confidence, method = self.card_recognizer.recognize_card(card_img, debug)
                
                # Create the result
                result = {
                    'card_code': card_code,
                    'confidence': confidence,
                    'method': method,
                    'is_empty': False,
                    'color_red': is_red,
                    'color_black': is_black,
                    'color_confidence': color_confidence,
                    'error': None
                }
                
                # Verify color consistency (suit color should match template match)
                if confidence > 0.6 and color_confidence > 0.5:
                    suit = card_code[1] if len(card_code) == 2 else ''
                    expected_red = suit in ['h', 'd']
                    expected_black = suit in ['c', 's']
                    
                    if (expected_red and not is_red) or (expected_black and not is_black):
                        logger.warning(f"Color mismatch: card_code={card_code}, is_red={is_red}, is_black={is_black}")
                        # Decrease confidence if color doesn't match
                        result['confidence'] *= 0.7
                
            except Exception as e:
                logger.error(f"Error in template matching: {e}", exc_info=True)
                result = {
                    'card_code': 'error',
                    'confidence': 0.0,
                    'method': 'error',
                    'is_empty': False,
                    'error': str(e)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive card recognition: {e}", exc_info=True)
            return {
                'card_code': 'error',
                'confidence': 0.0,
                'method': 'error',
                'is_empty': False,
                'error': str(e)
            }

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Comprehensive card recognition with empty slot detection')
    parser.add_argument('--image', help='Path to card image to analyze')
    parser.add_argument('--debug', action='store_true', help='Save debug images')
    args = parser.parse_args()
    
    if not args.image:
        parser.print_help()
        return
    
    recognizer = ComprehensiveCardRecognizer()
    
    # Load the image
    image = cv2.imread(args.image)
    if image is None:
        logger.error(f"Failed to load image: {args.image}")
        return
    
    # Run recognition
    result = recognizer.recognize_card(image, debug=args.debug or True)
    
    # Print results
    logger.info(f"Recognition results for {args.image}:")
    for key, value in result.items():
        logger.info(f"  {key}: {value}")

if __name__ == "__main__":
    main()
