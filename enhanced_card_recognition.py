"""
This script implements enhanced card recognition with empty slot detection
to solve the problem of misidentifying empty slots as cards.
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
        logging.FileHandler('enhanced_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_recognition')

class EmptySlotDetector:
    """Detects if a card slot is empty or contains an actual card."""
    
    def __init__(self):
        # Create output directory
        os.makedirs("debug_cards/empty_detection", exist_ok=True)
    
    def detect_empty_slot(self, card_img, debug=False, threshold=0.4):
        """
        Analyze a card image to determine if it's empty or contains an actual card.
        
        Args:
            card_img: The card image (numpy array)
            debug: Whether to save debug images
            threshold: The threshold for edge percentage to consider a slot not empty
            
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
        edge_percentage = (edge_count / (width * height)) 
        
        # Measure standard deviation of pixel values (measure of contrast)
        std_dev = np.std(gray) / 255.0  # Normalize to 0-1
        
        # Check color variation - convert to HSV and measure standard deviation
        hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
        h_std = np.std(hsv[:,:,0]) / 180.0  # Normalize to 0-1
        s_std = np.std(hsv[:,:,1]) / 255.0  # Normalize to 0-1
        
        # Calculate feature values
        features = {
            'edge_percentage': edge_percentage,
            'std_dev': std_dev,
            'h_std': h_std,
            's_std': s_std
        }
        
        # Calculate detection score 
        # Cards have more edges, higher contrast, more color variation
        card_score = (edge_percentage * 2.5 + std_dev + h_std * 0.5 + s_std * 0.5) / 5.0
        
        # Decision
        is_empty = card_score < threshold
        confidence = 1.0 - card_score if is_empty else card_score
        
        # Create debug visualization if requested
        debug_img = None
        if debug:
            # Create visualization with fixed size text area
            text_width = max(width, 150)  # Ensure text area has minimum width
            
            # Handle very small images
            min_height = 100
            if height < min_height:
                scale = min_height / height
                vis_height = min_height
                card_vis = cv2.resize(card_img, (int(width * scale), vis_height), interpolation=cv2.INTER_NEAREST)
                edges_vis = cv2.resize(edges, (int(width * scale), vis_height), interpolation=cv2.INTER_NEAREST)
                width_scaled = int(width * scale)
            else:
                vis_height = height
                card_vis = card_img.copy()
                edges_vis = edges.copy()
                width_scaled = width
            
            # Ensure proper dimensions for visualization
            vis_width = width_scaled * 2 + text_width
            visualization = np.zeros((vis_height, vis_width, 3), dtype=np.uint8)
            
            # Original image (ensure proper size)
            if width_scaled > 0 and vis_height > 0:
                card_area = visualization[:vis_height, :width_scaled]
                try:
                    if len(card_vis.shape) == 3:
                        # Resize card_vis to match the destination area
                        if card_vis.shape[:2] != card_area.shape[:2]:
                            card_vis_resized = cv2.resize(card_vis, (card_area.shape[1], card_area.shape[0]))
                        else:
                            card_vis_resized = card_vis
                        card_area[:] = card_vis_resized
                    else:
                        card_vis_color = cv2.cvtColor(card_vis, cv2.COLOR_GRAY2BGR)
                        if card_vis_color.shape[:2] != card_area.shape[:2]:
                            card_vis_resized = cv2.resize(card_vis_color, (card_area.shape[1], card_area.shape[0]))
                        else:
                            card_vis_resized = card_vis_color
                        card_area[:] = card_vis_resized
                except Exception as e:
                    logger.error(f"Error rendering original image: {e}")
                    # Fill with gray if error
                    card_area[:] = (128, 128, 128)
            
            # Edge image (convert to color and ensure proper size)
            if width_scaled > 0 and vis_height > 0:
                edge_area = visualization[:vis_height, width_scaled:width_scaled*2]
                try:
                    edge_vis_color = cv2.cvtColor(edges_vis, cv2.COLOR_GRAY2BGR)
                    if edge_vis_color.shape[:2] != edge_area.shape[:2]:
                        edge_vis_resized = cv2.resize(edge_vis_color, (edge_area.shape[1], edge_area.shape[0]))
                    else:
                        edge_vis_resized = edge_vis_color
                    edge_area[:] = edge_vis_resized
                except Exception as e:
                    logger.error(f"Error rendering edge image: {e}")
                    # Fill with gray if error
                    edge_area[:] = (128, 128, 128)
            
            # Add text area
            text_area = np.ones((vis_height, text_width, 3), dtype=np.uint8) * 255
            
            # Add feature text
            font = cv2.FONT_HERSHEY_SIMPLEX
            y_pos = 20
            cv2.putText(text_area, f"Edges: {edge_percentage*100:.1f}%", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            y_pos += 15
            cv2.putText(text_area, f"Contrast: {std_dev:.3f}", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            y_pos += 15
            cv2.putText(text_area, f"Hue var: {h_std:.3f}", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            y_pos += 15
            cv2.putText(text_area, f"Sat var: {s_std:.3f}", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            y_pos += 15
            cv2.putText(text_area, f"Card score: {card_score:.3f}", (10, y_pos), font, 0.5, (0, 0, 0), 1)
            
            # Add result
            y_pos += 25
            result_text = "EMPTY SLOT" if is_empty else "CARD DETECTED"
            result_color = (0, 0, 200) if is_empty else (0, 200, 0)
            cv2.putText(text_area, result_text, (10, y_pos), font, 0.7, result_color, 2)
            
            # Add confidence
            y_pos += 20
            cv2.putText(text_area, f"Confidence: {confidence:.2f}", (10, y_pos), font, 0.5, result_color, 1)
            
            # Add to visualization
            visualization[:vis_height, width_scaled*2:] = text_area[:vis_height, :text_width]
            
            # Add section labels
            cv2.putText(visualization, "Original", (10, 10), font, 0.4, (255, 255, 255), 1)
            cv2.putText(visualization, "Edges", (width_scaled + 10, 10), font, 0.4, (255, 255, 255), 1)
            
            debug_img = visualization
        
        return is_empty, confidence, debug_img

class EnhancedCardRecognizer:
    """Enhanced card recognizer with empty slot detection to prevent false positives."""
    
    def __init__(self):
        # Create output directories
        os.makedirs("debug_cards", exist_ok=True)
        os.makedirs("debug_cards/enhanced", exist_ok=True)
        
        # Initialize empty slot detector
        self.empty_detector = EmptySlotDetector()
        
        # Load the original card recognizer
        try:
            from src.card_recognizer import CardRecognizer
            self.card_recognizer = CardRecognizer()
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
            
            # Check if this is an empty slot
            is_empty, empty_confidence, empty_debug_img = self.empty_detector.detect_empty_slot(card_img, debug)
            
            if debug and empty_debug_img is not None:
                debug_path = f"debug_cards/enhanced/empty_check_{timestamp}.png"
                cv2.imwrite(debug_path, empty_debug_img)
            
            # If it's an empty slot with high confidence, don't try to recognize
            if is_empty and empty_confidence > 0.7:
                logger.info(f"Detected empty slot with confidence {empty_confidence:.2f}")
                result = {
                    'card_code': 'empty',
                    'confidence': empty_confidence,
                    'method': 'empty_slot_detection',
                    'is_empty': True
                }
                return result
            
            # Proceed with normal card recognition if not empty or uncertain
            logger.info(f"Proceeding with card recognition (empty confidence: {empty_confidence:.2f})")
            
            # Call the original recognizer
            card_code, confidence, method = self.card_recognizer.recognize_card(card_img, debug)
            
            # Create the result
            result = {
                'card_code': card_code,
                'confidence': confidence,
                'method': method,
                'is_empty': False,
                'empty_confidence': empty_confidence
            }
            
            # If the recognized card has very low confidence and the empty slot detection
            # was moderately confident, trust the empty slot detection instead
            if confidence < 0.5 and empty_confidence > 0.6:
                logger.info(f"Overriding low confidence card ({card_code}, {confidence:.2f}) with empty slot detection")
                result['card_code'] = 'empty'
                result['confidence'] = empty_confidence
                result['method'] = 'empty_slot_detection'
                result['is_empty'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced card recognition: {e}", exc_info=True)
            return {
                'card_code': 'error',
                'confidence': 0.0,
                'method': 'error',
                'is_empty': False,
                'error': str(e)
            }

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Enhanced card recognition with empty slot detection')
    parser.add_argument('--image', help='Path to card image to analyze')
    args = parser.parse_args()
    
    if not args.image:
        parser.print_help()
        return
    
    recognizer = EnhancedCardRecognizer()
    
    # Load the image
    image = cv2.imread(args.image)
    if image is None:
        logger.error(f"Failed to load image: {args.image}")
        return
    
    # Run recognition
    result = recognizer.recognize_card(image, debug=True)
    
    # Print results
    logger.info(f"Recognition results for {args.image}:")
    for key, value in result.items():
        logger.info(f"  {key}: {value}")

if __name__ == "__main__":
    main()
