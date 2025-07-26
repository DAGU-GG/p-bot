"""
Direct Card Recognition System

This module uses color analysis and text/shape detection to directly recognize cards
without relying on template matching. Optimized for four-color decks where:
- Hearts are red
- Diamonds are blue
- Clubs are green
- Spades are black
"""

import os
import sys
import logging
import cv2
import numpy as np
import time
from pathlib import Path
import pytesseract  # For OCR of card ranks

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_card_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('direct_card_recognition')

# Try to set pytesseract path for Windows
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except:
    logger.warning("Warning: pytesseract not available, OCR functionality may be limited")

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
            # Create text with information
            debug_text = f"Edge%: {edge_percentage:.1f}%, Contrast: {contrast:.1f}\n"
            debug_text += f"Hue var: {hue_var:.1f}, Sat var: {sat_var:.1f}\n"
            debug_text += f"Empty: {is_empty}, Conf: {confidence:.2f}"
            
            logger.info(f"Edge percentage: {edge_percentage:.2f}%, contrast: {contrast:.2f}, "
                      f"hue var: {hue_var:.2f}, sat var: {sat_var:.2f}")
            logger.info(f"Empty: {is_empty}, Confidence: {confidence:.2f}")
            
            # Create visualization
            visualization = np.zeros((max(height, 100), width * 2 + 200, 3), dtype=np.uint8)
            
            # Original image
            if height < 100:
                card_vis = cv2.resize(card_img, (int(width * (100/height)), 100))
                edges_vis = cv2.resize(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), (int(width * (100/height)), 100))
            else:
                card_vis = card_img.copy()
                edges_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            # Place images in visualization
            h, w = card_vis.shape[:2]
            visualization[:h, :w] = card_vis
            visualization[:h, w:w*2] = edges_vis
            
            # Add text
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_color = (0, 0, 200) if is_empty else (0, 200, 0)
            y_pos = 30
            for line in debug_text.split('\n'):
                cv2.putText(visualization, line, (w*2 + 10, y_pos), font, 0.5, text_color, 1)
                y_pos += 20
                
            debug_img = visualization
        
        return is_empty, confidence, debug_img

class CardSuitDetector:
    """Detects card suit based on color analysis for four-color decks."""
    
    def __init__(self):
        # Create output directory
        os.makedirs("debug_cards/suit_detection", exist_ok=True)
        
        # Define suit colors
        self.suit_colors = {
            'hearts': 'red',
            'diamonds': 'blue',
            'clubs': 'green',
            'spades': 'black'
        }
        
        # Map suits to their 1-letter codes
        self.suit_codes = {
            'hearts': 'h',
            'diamonds': 'd',
            'clubs': 'c',
            'spades': 's'
        }
    
    def detect_suit(self, card_img, debug=False):
        """
        Detect the card suit based on color analysis.
        
        Args:
            card_img: The card image
            debug: Whether to save debug images
            
        Returns:
            dict: Detection results with suit information
        """
        if card_img is None or card_img.size == 0:
            return {
                'suit': 'unknown',
                'suit_code': '',
                'confidence': 0.0
            }
        
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for each suit
        # Red (Hearts) - red hue
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        # Blue (Diamonds) - blue hue
        lower_blue = np.array([90, 80, 80])
        upper_blue = np.array([130, 255, 255])
        
        # Green (Clubs) - green hue
        lower_green = np.array([40, 80, 80])
        upper_green = np.array([85, 255, 255])
        
        # Black (Spades) - low saturation and value
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 100, 50])
        
        # Create masks for each color
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        black_mask = cv2.inRange(hsv, lower_black, upper_black)
        
        # Count pixels
        red_pixels = np.count_nonzero(red_mask)
        blue_pixels = np.count_nonzero(blue_mask)
        green_pixels = np.count_nonzero(green_mask)
        black_pixels = np.count_nonzero(black_mask)
        total_pixels = red_mask.size
        
        # Calculate percentages
        red_percentage = (red_pixels / total_pixels) * 100
        blue_percentage = (blue_pixels / total_pixels) * 100
        green_percentage = (green_pixels / total_pixels) * 100
        black_percentage = (black_pixels / total_pixels) * 100
        
        # Find the dominant color
        color_percentages = {
            'hearts': red_percentage,
            'diamonds': blue_percentage,
            'clubs': green_percentage,
            'spades': black_percentage
        }
        
        # Adjusted threshold for small card images
        color_threshold = 1.5  # Lower for small images
        
        dominant_suit = max(color_percentages, key=color_percentages.get)
        dominant_percentage = color_percentages[dominant_suit]
        
        # Initialize result
        result = {
            'suit': 'unknown',
            'suit_code': '',
            'confidence': 0.0,
            'color_percentages': color_percentages
        }
        
        # Determine suit if dominant color exceeds threshold
        if dominant_percentage > color_threshold:
            result['suit'] = dominant_suit
            result['suit_code'] = self.suit_codes[dominant_suit]
            result['confidence'] = min(1.0, dominant_percentage / 8.0)  # Scale confidence
        
        # Create debug visualization if requested
        if debug:
            self._create_debug_visualization(
                card_img, 
                red_mask, blue_mask, green_mask, black_mask,
                result, 
                color_percentages
            )
        
        return result
    
    def _create_debug_visualization(self, card_img, red_mask, blue_mask, green_mask, black_mask, 
                                   result, color_percentages):
        """Create debug visualization for suit detection."""
        timestamp = int(time.time() * 1000)
        
        # Create visualization
        visualization = np.zeros((card_img.shape[0], card_img.shape[1] * 5, 3), dtype=np.uint8)
        
        # Original image
        visualization[:, :card_img.shape[1]] = card_img
        
        # Red mask (show in red)
        red_mask_vis = np.zeros_like(card_img)
        red_mask_vis[:, :, 2] = red_mask  # Red channel
        visualization[:, card_img.shape[1]:card_img.shape[1]*2] = red_mask_vis
        
        # Blue mask (show in blue)
        blue_mask_vis = np.zeros_like(card_img)
        blue_mask_vis[:, :, 0] = blue_mask  # Blue channel
        visualization[:, card_img.shape[1]*2:card_img.shape[1]*3] = blue_mask_vis
        
        # Green mask (show in green)
        green_mask_vis = np.zeros_like(card_img)
        green_mask_vis[:, :, 1] = green_mask  # Green channel
        visualization[:, card_img.shape[1]*3:card_img.shape[1]*4] = green_mask_vis
        
        # Black mask (show in gray)
        black_mask_vis = np.zeros_like(card_img)
        black_mask_vis[:, :, 0] = black_mask  # Blue channel = Gray
        black_mask_vis[:, :, 1] = black_mask  # Green channel = Gray
        black_mask_vis[:, :, 2] = black_mask  # Red channel = Gray
        visualization[:, card_img.shape[1]*4:] = black_mask_vis
        
        # Add text with results
        font = cv2.FONT_HERSHEY_SIMPLEX
        height, width = card_img.shape[:2]
        
        # Add text to original image
        text_y = 20
        cv2.putText(visualization, f"Detected: {result['suit']}", 
                   (10, text_y), font, 0.5, (255, 255, 255), 1)
        text_y += 20
        cv2.putText(visualization, f"Conf: {result['confidence']:.2f}", 
                   (10, text_y), font, 0.5, (255, 255, 255), 1)
        
        # Add text to red mask
        cv2.putText(visualization, "Hearts", 
                   (width + 10, 20), font, 0.5, (0, 0, 255), 1)
        cv2.putText(visualization, f"{color_percentages['hearts']:.2f}%", 
                   (width + 10, 40), font, 0.5, (0, 0, 255), 1)
        
        # Add text to blue mask
        cv2.putText(visualization, "Diamonds", 
                   (width*2 + 10, 20), font, 0.5, (255, 0, 0), 1)
        cv2.putText(visualization, f"{color_percentages['diamonds']:.2f}%", 
                   (width*2 + 10, 40), font, 0.5, (255, 0, 0), 1)
        
        # Add text to green mask
        cv2.putText(visualization, "Clubs", 
                   (width*3 + 10, 20), font, 0.5, (0, 255, 0), 1)
        cv2.putText(visualization, f"{color_percentages['clubs']:.2f}%", 
                   (width*3 + 10, 40), font, 0.5, (0, 255, 0), 1)
        
        # Add text to black mask
        cv2.putText(visualization, "Spades", 
                   (width*4 + 10, 20), font, 0.5, (255, 255, 255), 1)
        cv2.putText(visualization, f"{color_percentages['spades']:.2f}%", 
                   (width*4 + 10, 40), font, 0.5, (255, 255, 255), 1)
        
        # Save debug image
        debug_path = f"debug_cards/suit_detection/suit_{timestamp}.png"
        cv2.imwrite(debug_path, visualization)
        
        # Log results
        logger.info(f"Suit detection results:")
        logger.info(f"  - Hearts: {color_percentages['hearts']:.2f}%")
        logger.info(f"  - Diamonds: {color_percentages['diamonds']:.2f}%")
        logger.info(f"  - Clubs: {color_percentages['clubs']:.2f}%")
        logger.info(f"  - Spades: {color_percentages['spades']:.2f}%")
        logger.info(f"  - Detected suit: {result['suit']} (confidence: {result['confidence']:.2f})")

class CardRankDetector:
    """Detects card rank using OCR and contour analysis."""
    
    def __init__(self):
        # Create output directory
        os.makedirs("debug_cards/rank_detection", exist_ok=True)
        
        # Define valid ranks
        self.valid_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        # Map for OCR corrections (common misreadings)
        self.ocr_corrections = {
            '1': 'A',    # Often 'A' is read as '1'
            'I': 'J',    # Often 'J' is read as 'I'
            'O': '0',    # Often '0' is read as 'O'
            'l': '1',    # Often '1' is read as 'l'
            'i': '1',    # Often '1' is read as 'i'
            'D': '0',    # Often '0' is read as 'D'
            'T': '7',    # Sometimes '7' is read as 'T'
            'L': '4',    # Sometimes '4' is read as 'L'
            'B': '8',    # Sometimes '8' is read as 'B'
            'g': '9',    # Sometimes '9' is read as 'g'
            '0': '10'    # Convert single '0' to '10'
        }
        
        # Special conversion for 10
        self.ten_to_t = {
            '10': 'T'   # Convert '10' to 'T' for poker notation
        }
    
    def _preprocess_for_ocr(self, card_img):
        """Preprocess card image for better OCR results."""
        # Convert to grayscale
        gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to isolate the rank
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Invert if needed (black text on white background works best for OCR)
        # Count white and black pixels
        white_pixels = np.count_nonzero(thresh)
        black_pixels = thresh.size - white_pixels
        
        # If more white than black, invert
        if white_pixels > black_pixels:
            thresh = cv2.bitwise_not(thresh)
        
        # Apply morphology to clean up noise
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return thresh
    
    def _extract_rank_region(self, card_img):
        """Extract the top-left region of the card where the rank is typically located."""
        height, width = card_img.shape[:2]
        
        # The rank is usually in the top-left corner
        # Get approximately the top-left 1/4 of the card
        rank_region = card_img[0:int(height/3), 0:int(width/3)]
        
        return rank_region
    
    def _correct_ocr_text(self, text):
        """Correct common OCR misreadings."""
        # Remove whitespace and convert to uppercase
        text = text.strip().upper()
        
        # If empty, return empty string
        if not text:
            return ''
        
        # Take only the first character (most relevant for card rank)
        first_char = text[0]
        
        # Apply corrections
        corrected = self.ocr_corrections.get(first_char, first_char)
        
        # Special case for 10 (either '10' or '1O' or 'IO')
        if text.startswith('10') or text.startswith('1O') or text.startswith('IO'):
            corrected = '10'
        
        # Convert 10 to T for poker notation
        if corrected == '10':
            corrected = 'T'
        
        # Final validation - ensure it's a valid rank
        if corrected in self.valid_ranks or corrected == 'T':
            return corrected
        else:
            return ''
    
    def detect_rank(self, card_img, debug=False):
        """
        Detect the card rank using OCR and contour analysis.
        
        Args:
            card_img: The card image
            debug: Whether to save debug images
            
        Returns:
            dict: Detection results with rank information
        """
        if card_img is None or card_img.size == 0:
            return {
                'rank': '',
                'confidence': 0.0
            }
        
        # Extract rank region
        rank_region = self._extract_rank_region(card_img)
        
        # Preprocess for OCR
        preprocessed = self._preprocess_for_ocr(rank_region)
        
        # Initialize result
        result = {
            'rank': '',
            'confidence': 0.0,
            'ocr_text': ''
        }
        
        try:
            # Use OCR to detect the rank
            ocr_text = pytesseract.image_to_string(
                preprocessed, 
                config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789AJQKT'
            )
            
            # Store raw OCR text
            result['ocr_text'] = ocr_text
            
            # Correct and validate OCR text
            corrected_rank = self._correct_ocr_text(ocr_text)
            
            if corrected_rank:
                result['rank'] = corrected_rank
                result['confidence'] = 0.8  # Default confidence
            else:
                # Try an alternative method with contour analysis
                result = self._detect_rank_by_contours(rank_region, result)
        except Exception as e:
            logger.error(f"OCR error: {e}")
            # Try contour analysis as fallback
            result = self._detect_rank_by_contours(rank_region, result)
        
        # Create debug visualization if requested
        if debug:
            self._create_debug_visualization(card_img, rank_region, preprocessed, result)
        
        return result
    
    def _detect_rank_by_contours(self, rank_region, result):
        """Detect rank by analyzing contours and shapes."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(rank_region, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size
            filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 10]
            
            # If no substantial contours found, return empty result
            if not filtered_contours:
                return result
            
            # Get the largest contour
            largest_contour = max(filtered_contours, key=cv2.contourArea)
            
            # Analyze contour shape to guess rank
            # For simplicity, we'll use basic metrics like area, perimeter, and aspect ratio
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = float(w) / h if h > 0 else 0
            
            # This is a very simplified approach - in practice, you'd need more sophisticated
            # shape analysis or machine learning for accurate rank detection
            
            # Default to low confidence since this is a fallback method
            result['confidence'] = 0.5
            
            return result
        except Exception as e:
            logger.error(f"Contour analysis error: {e}")
            return result
    
    def _create_debug_visualization(self, card_img, rank_region, preprocessed, result):
        """Create debug visualization for rank detection."""
        timestamp = int(time.time() * 1000)
        
        # Create visualization
        height, width = card_img.shape[:2]
        vis_height = max(height, 200)
        visualization = np.ones((vis_height, width * 3, 3), dtype=np.uint8) * 255
        
        # Original image
        if height < vis_height:
            card_vis = cv2.resize(card_img, (int(width * (vis_height/height)), vis_height))
        else:
            card_vis = card_img.copy()
        
        visualization[:card_vis.shape[0], :card_vis.shape[1]] = card_vis
        
        # Rank region
        rank_h, rank_w = rank_region.shape[:2]
        # Resize for visibility
        rank_vis = cv2.resize(rank_region, (rank_w * 2, rank_h * 2), interpolation=cv2.INTER_NEAREST)
        # Place in the visualization
        r_h, r_w = rank_vis.shape[:2]
        visualization[:r_h, width:width+r_w] = rank_vis
        
        # Preprocessed image
        prep_h, prep_w = preprocessed.shape[:2]
        # Convert to color for visualization
        prep_vis = cv2.cvtColor(preprocessed, cv2.COLOR_GRAY2BGR)
        # Resize for visibility
        prep_vis = cv2.resize(prep_vis, (prep_w * 2, prep_h * 2), interpolation=cv2.INTER_NEAREST)
        # Place in the visualization
        p_h, p_w = prep_vis.shape[:2]
        visualization[:p_h, width*2:width*2+p_w] = prep_vis
        
        # Add text with results
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Add rectangle and text to highlight detected rank
        cv2.rectangle(visualization, (10, height + 10), (width - 10, vis_height - 10), (240, 240, 240), -1)
        
        text_y = height + 30
        cv2.putText(visualization, f"Detected Rank: {result['rank']}", 
                   (20, text_y), font, 0.7, (0, 0, 0), 1)
        text_y += 25
        cv2.putText(visualization, f"Confidence: {result['confidence']:.2f}", 
                   (20, text_y), font, 0.7, (0, 0, 0), 1)
        text_y += 25
        cv2.putText(visualization, f"OCR Text: '{result['ocr_text']}'", 
                   (20, text_y), font, 0.7, (0, 0, 0), 1)
        
        # Add titles for the different sections
        cv2.putText(visualization, "Original Card", (10, 20), font, 0.6, (0, 0, 255), 1)
        cv2.putText(visualization, "Rank Region", (width + 10, 20), font, 0.6, (0, 0, 255), 1)
        cv2.putText(visualization, "Preprocessed", (width*2 + 10, 20), font, 0.6, (0, 0, 255), 1)
        
        # Save debug image
        debug_path = f"debug_cards/rank_detection/rank_{timestamp}.png"
        cv2.imwrite(debug_path, visualization)
        
        # Log results
        logger.info(f"Rank detection results:")
        logger.info(f"  - OCR text: '{result['ocr_text']}'")
        logger.info(f"  - Detected rank: {result['rank']} (confidence: {result['confidence']:.2f})")

class DirectCardRecognizer:
    """
    Card recognition using direct color and rank detection instead of template matching.
    Optimized for four-color decks (red hearts, blue diamonds, green clubs, black spades).
    """
    
    def __init__(self):
        self.logger = logging.getLogger('direct_card_recognition')
        
        # Initialize components
        self.empty_detector = EmptySlotDetector()
        self.suit_detector = CardSuitDetector()
        self.rank_detector = CardRankDetector()
        
        # Mapping from 2-char code to longer name
        self.card_names = {
            '2h': 'Two of Hearts', '2d': 'Two of Diamonds', '2c': 'Two of Clubs', '2s': 'Two of Spades',
            '3h': 'Three of Hearts', '3d': 'Three of Diamonds', '3c': 'Three of Clubs', '3s': 'Three of Spades',
            '4h': 'Four of Hearts', '4d': 'Four of Diamonds', '4c': 'Four of Clubs', '4s': 'Four of Spades',
            '5h': 'Five of Hearts', '5d': 'Five of Diamonds', '5c': 'Five of Clubs', '5s': 'Five of Spades',
            '6h': 'Six of Hearts', '6d': 'Six of Diamonds', '6c': 'Six of Clubs', '6s': 'Six of Spades',
            '7h': 'Seven of Hearts', '7d': 'Seven of Diamonds', '7c': 'Seven of Clubs', '7s': 'Seven of Spades',
            '8h': 'Eight of Hearts', '8d': 'Eight of Diamonds', '8c': 'Eight of Clubs', '8s': 'Eight of Spades',
            '9h': 'Nine of Hearts', '9d': 'Nine of Diamonds', '9c': 'Nine of Clubs', '9s': 'Nine of Spades',
            'Th': 'Ten of Hearts', 'Td': 'Ten of Diamonds', 'Tc': 'Ten of Clubs', 'Ts': 'Ten of Spades',
            'Jh': 'Jack of Hearts', 'Jd': 'Jack of Diamonds', 'Jc': 'Jack of Clubs', 'Js': 'Jack of Spades',
            'Qh': 'Queen of Hearts', 'Qd': 'Queen of Diamonds', 'Qc': 'Queen of Clubs', 'Qs': 'Queen of Spades',
            'Kh': 'King of Hearts', 'Kd': 'King of Diamonds', 'Kc': 'King of Clubs', 'Ks': 'King of Spades',
            'Ah': 'Ace of Hearts', 'Ad': 'Ace of Diamonds', 'Ac': 'Ace of Clubs', 'As': 'Ace of Spades'
        }
        
        # Create output directories
        os.makedirs("debug_cards/direct", exist_ok=True)
        
        # Cache for detected cards (to prevent duplicates)
        self.detected_cards = set()
        self.last_detection_time = time.time()
        self.detection_timeout = 5.0  # Reset cache after 5 seconds
    
    def reset_cache_if_needed(self):
        """Reset the detection cache if timeout has elapsed."""
        current_time = time.time()
        if current_time - self.last_detection_time > self.detection_timeout:
            self.detected_cards.clear()
            self.last_detection_time = current_time
            logger.debug("Detection cache cleared due to timeout")
    
    def recognize_card(self, card_img, debug=False):
        """
        Recognize a card using direct color and shape analysis.
        
        Args:
            card_img: The card image
            debug: Whether to save debug images
            
        Returns:
            dict: Recognition results
        """
        try:
            timestamp = int(time.time() * 1000)
            self.reset_cache_if_needed()
            
            # Check if it's an empty slot
            is_empty, empty_confidence, empty_debug = self.empty_detector.detect(card_img, debug)
            
            if debug and empty_debug is not None:
                debug_path = f"debug_cards/direct/empty_check_{timestamp}.png"
                cv2.imwrite(debug_path, empty_debug)
            
            # If empty with high confidence, return empty result
            if is_empty and empty_confidence > 0.7:
                self.logger.info(f"Detected empty slot with confidence {empty_confidence:.2f}")
                return {
                    'card_code': 'empty',
                    'card_name': 'Empty',
                    'confidence': empty_confidence,
                    'method': 'empty_slot_detection',
                    'is_empty': True,
                    'error': None
                }
            
            # Detect the suit
            suit_result = self.suit_detector.detect_suit(card_img, debug)
            
            # Detect the rank
            rank_result = self.rank_detector.detect_rank(card_img, debug)
            
            # Combine results
            if suit_result['suit_code'] and rank_result['rank']:
                # We have both rank and suit, create the card code
                card_code = f"{rank_result['rank']}{suit_result['suit_code']}"
                
                # Calculate combined confidence
                combined_confidence = (suit_result['confidence'] + rank_result['confidence']) / 2.0
                
                # Check if this card was already detected recently
                if card_code in self.detected_cards:
                    self.logger.warning(f"Card {card_code} was already detected recently - possible duplicate")
                    
                    # Handle potential duplicate
                    if combined_confidence < 0.8:
                        # Low confidence and already seen - mark as low confidence
                        self.logger.info(f"Marking potential duplicate card {card_code} as low confidence")
                        combined_confidence *= 0.7
                else:
                    # Add to detected cards
                    self.detected_cards.add(card_code)
                
                # Get card name
                card_name = self.card_names.get(card_code, 'Unknown Card')
                
                # Create result
                result = {
                    'card_code': card_code,
                    'card_name': card_name,
                    'confidence': combined_confidence,
                    'rank': rank_result['rank'],
                    'rank_confidence': rank_result['confidence'],
                    'suit': suit_result['suit'],
                    'suit_code': suit_result['suit_code'],
                    'suit_confidence': suit_result['confidence'],
                    'method': 'direct_recognition',
                    'is_empty': False,
                    'error': None
                }
            else:
                # Missing either rank or suit
                if not suit_result['suit_code']:
                    self.logger.warning("Failed to detect suit")
                if not rank_result['rank']:
                    self.logger.warning("Failed to detect rank")
                
                # Check if it might actually be an empty slot with low confidence
                if empty_confidence > 0.5:
                    self.logger.info(f"Treating as empty slot with moderate confidence {empty_confidence:.2f}")
                    return {
                        'card_code': 'empty',
                        'card_name': 'Empty',
                        'confidence': empty_confidence,
                        'method': 'empty_slot_detection',
                        'is_empty': True,
                        'error': None
                    }
                
                # Create error result
                result = {
                    'card_code': 'error',
                    'card_name': 'Error',
                    'confidence': 0.0,
                    'method': 'direct_recognition',
                    'is_empty': False,
                    'error': 'Failed to detect rank or suit'
                }
            
            # Create debug visualization if requested
            if debug:
                self._create_debug_visualization(card_img, result, timestamp)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in direct card recognition: {e}", exc_info=True)
            return {
                'card_code': 'error',
                'card_name': 'Error',
                'confidence': 0.0,
                'method': 'error',
                'is_empty': False,
                'error': str(e)
            }
    
    def _create_debug_visualization(self, card_img, result, timestamp):
        """Create debug visualization for the complete recognition process."""
        # Create visualization
        height, width = card_img.shape[:2]
        visualization = np.ones((height + 100, width, 3), dtype=np.uint8) * 255
        
        # Original image
        visualization[:height, :width] = card_img
        
        # Draw rectangle around the card
        cv2.rectangle(visualization, (0, 0), (width-1, height-1), (0, 0, 255), 2)
        
        # Add text with results
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Background for text
        cv2.rectangle(visualization, (0, height), (width, height+100), (240, 240, 240), -1)
        
        # Add text
        text_y = height + 20
        cv2.putText(visualization, f"Card: {result.get('card_name', 'Unknown')}", 
                   (10, text_y), font, 0.6, (0, 0, 0), 1)
        text_y += 20
        cv2.putText(visualization, f"Code: {result.get('card_code', 'Unknown')}", 
                   (10, text_y), font, 0.6, (0, 0, 0), 1)
        text_y += 20
        cv2.putText(visualization, f"Confidence: {result.get('confidence', 0.0):.2f}", 
                   (10, text_y), font, 0.6, (0, 0, 0), 1)
        text_y += 20
        cv2.putText(visualization, f"Method: {result.get('method', 'Unknown')}", 
                   (10, text_y), font, 0.6, (0, 0, 0), 1)
        
        # Save debug image
        debug_path = f"debug_cards/direct/card_{timestamp}.png"
        cv2.imwrite(debug_path, visualization)
    
    def recognize_multiple_cards(self, card_images, debug=False):
        """
        Recognize multiple cards and prevent duplicates.
        
        Args:
            card_images: List of card images to recognize
            debug: Whether to save debug images
            
        Returns:
            results: List of recognition results
        """
        # Reset detection cache
        self.detected_cards.clear()
        self.last_detection_time = time.time()
        
        results = []
        for i, card_img in enumerate(card_images):
            result = self.recognize_card(card_img, debug)
            results.append(result)
            
            # Add a small delay to ensure unique timestamps in debug images
            if debug:
                time.sleep(0.01)
        
        # Validate results to avoid duplicates
        return self._validate_results(results)
    
    def _validate_results(self, results):
        """
        Validate recognition results to prevent duplicates.
        
        Args:
            results: List of recognition results
            
        Returns:
            validated_results: List of validated results
        """
        valid_results = []
        seen_cards = set()
        
        # Sort by confidence (highest first)
        sorted_results = sorted(results, key=lambda x: x.get('confidence', 0.0), reverse=True)
        
        for result in sorted_results:
            card_code = result.get('card_code')
            
            # Skip errors and empties for duplicate check
            if card_code in ('error', 'empty'):
                valid_results.append(result)
                continue
            
            # Check for duplicates
            if card_code in seen_cards:
                # This is a duplicate - mark as empty
                self.logger.warning(f"Duplicate card detected: {card_code} - marking as empty")
                result['card_code'] = 'empty'
                result['card_name'] = 'Empty'
                result['is_empty'] = True
                result['confidence'] = 0.5
                result['method'] = 'duplicate_detection'
                valid_results.append(result)
            else:
                # Add to seen cards
                seen_cards.add(card_code)
                valid_results.append(result)
        
        # Resort to original order
        return [r for r in results]  # Keep original order

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Direct card recognition with color and shape analysis')
    parser.add_argument('--image', help='Path to card image to analyze')
    parser.add_argument('--debug', action='store_true', help='Save debug images')
    args = parser.parse_args()
    
    if not args.image:
        parser.print_help()
        return
    
    recognizer = DirectCardRecognizer()
    
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
