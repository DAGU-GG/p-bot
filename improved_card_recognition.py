"""
Improved Card Recognition System

This module combines template matching with color analysis to provide more accurate card recognition
and prevent issues with duplicate cards and empty slots.
"""

import os
import sys
import logging
import cv2
import numpy as np
import time
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_card_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('improved_recognition')

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

class CardSuitColorDetector:
    """Analyzes card colors to determine suit colors (red for hearts, green for clubs, black for spades, blue for diamonds)."""
    
    def __init__(self):
        # Create output directory
        os.makedirs("debug_cards/color_analysis", exist_ok=True)
    
    def analyze_card(self, card_img, debug=False):
        """
        Analyze a card image to determine suit color.
        
        Args:
            card_img: The card image as a numpy array
            debug: Whether to save debug visualizations
            
        Returns:
            dict: Analysis results with suit color information
        """
        if card_img is None or card_img.size == 0:
            return {
                "is_hearts": False,
                "is_diamonds": False,
                "is_clubs": False,
                "is_spades": False,
                "red_percentage": 0,
                "blue_percentage": 0,
                "green_percentage": 0,
                "black_percentage": 0,
                "suit_color": "unknown",
                "confidence": 0
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
        
        # Determine suit color with improved thresholds for small cards
        suit_color = "unknown"
        is_hearts = False
        is_diamonds = False
        is_clubs = False
        is_spades = False
        confidence = 0.0
        
        # Adjusted thresholds for small card images (like in poker tables)
        color_threshold = 1.5  # Lower for small images
        
        # Find the dominant color
        color_percentages = {
            "hearts": red_percentage,
            "diamonds": blue_percentage,
            "clubs": green_percentage,
            "spades": black_percentage
        }
        
        dominant_suit = max(color_percentages, key=color_percentages.get)
        dominant_percentage = color_percentages[dominant_suit]
        
        if dominant_percentage > color_threshold:
            suit_color = dominant_suit
            confidence = min(1.0, dominant_percentage / 8.0)
            
            # Set the appropriate flag
            if dominant_suit == "hearts":
                is_hearts = True
            elif dominant_suit == "diamonds":
                is_diamonds = True
            elif dominant_suit == "clubs":
                is_clubs = True
            elif dominant_suit == "spades":
                is_spades = True
            
        if debug:
            logger.info(f"Color analysis results:")
            logger.info(f"  - Hearts (red) pixels: {red_pixels} ({red_percentage:.2f}%)")
            logger.info(f"  - Diamonds (blue) pixels: {blue_pixels} ({blue_percentage:.2f}%)")
            logger.info(f"  - Clubs (green) pixels: {green_pixels} ({green_percentage:.2f}%)")
            logger.info(f"  - Spades (black) pixels: {black_pixels} ({black_percentage:.2f}%)")
            logger.info(f"  - Predicted suit: {suit_color} (confidence: {confidence:.2f})")
            
            # Create visualization for debugging
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
            
            # Save debug image
            debug_path = f"debug_cards/color_analysis/card_color_{int(time.time()*1000)}.png"
            cv2.imwrite(debug_path, visualization)
        
        return {
            "is_hearts": is_hearts,
            "is_diamonds": is_diamonds,
            "is_clubs": is_clubs,
            "is_spades": is_spades,
            "red_percentage": red_percentage,
            "blue_percentage": blue_percentage,
            "green_percentage": green_percentage,
            "black_percentage": black_percentage,
            "suit_color": suit_color,
            "confidence": confidence
        }
    
class CardVerifier:
    """
    Verifies card recognition results for consistency and prevents duplicates.
    Used to detect and fix common recognition issues.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('card_verifier')
        
        # Set of valid card ranks
        self.valid_ranks = {'2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'}
        
        # Set of valid card suits
        self.valid_suits = {'h', 'd', 'c', 's'}
        
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
        
        # Reverse mapping from name to code
        self.name_to_code = {v: k for k, v in self.card_names.items()}
        
        # Expected suit colors mapping
        self.suit_to_color = {
            'h': 'hearts',  # Red
            'd': 'diamonds',  # Blue
            'c': 'clubs',  # Green
            's': 'spades'   # Black
        }
    
    def is_valid_card(self, card_code):
        """Check if a card code is valid (e.g., '2h', 'Td', 'Ks')."""
        if len(card_code) != 2:
            return False
            
        rank, suit = card_code[0], card_code[1]
        return rank in self.valid_ranks and suit in self.valid_suits
    
    def get_card_name(self, card_code):
        """Convert a 2-char card code to its full name."""
        if card_code == 'empty':
            return 'Empty'
            
        return self.card_names.get(card_code, 'Unknown Card')
    
    def get_card_code(self, card_name):
        """Convert a card name to its 2-char code."""
        return self.name_to_code.get(card_name, None)
    
    def verify_color_consistency(self, card_code, color_info):
        """
        Verify that the recognized card suit matches the detected color.
        
        Args:
            card_code: The 2-char card code (e.g., '2h', 'Td')
            color_info: Dictionary with color analysis results
            
        Returns:
            float: Confidence adjustment factor (1.0 = no change, <1.0 = reduce confidence)
        """
        if not self.is_valid_card(card_code) or color_info['confidence'] < 0.3:
            return 1.0
            
        suit = card_code[1]
        expected_color = self.suit_to_color.get(suit)
        
        # Check if color detection matches the expected suit color
        is_matching_color = False
        
        if expected_color == 'hearts' and color_info['is_hearts']:
            is_matching_color = True
        elif expected_color == 'diamonds' and color_info['is_diamonds']:
            is_matching_color = True
        elif expected_color == 'clubs' and color_info['is_clubs']:
            is_matching_color = True
        elif expected_color == 'spades' and color_info['is_spades']:
            is_matching_color = True
        
        if is_matching_color:
            # Color matches, increase confidence slightly
            return 1.2
        else:
            # Find if there's a stronger color signal that contradicts
            contradicting_color = None
            max_percentage = 0
            
            color_percentages = {
                'hearts': color_info.get('red_percentage', 0),
                'diamonds': color_info.get('blue_percentage', 0),
                'clubs': color_info.get('green_percentage', 0),
                'spades': color_info.get('black_percentage', 0)
            }
            
            for color, percentage in color_percentages.items():
                if color != expected_color and percentage > max_percentage:
                    max_percentage = percentage
                    contradicting_color = color
            
            # If there's a strong contradicting color, significantly reduce confidence
            if contradicting_color and max_percentage > 3.0:
                return 0.4
            
            # If there's a moderate contradiction, reduce confidence moderately
            if contradicting_color and max_percentage > 1.5:
                return 0.7
            
            # No strong contradicting color signal, minor reduction
            return 0.9
    
    def verify_card_features(self, card_code, confidence):
        """
        Additional verification for commonly confused cards like Aces and face cards.
        
        Args:
            card_code: The 2-char card code (e.g., '2h', 'Td')
            confidence: Original confidence score
            
        Returns:
            float: Adjusted confidence based on card-specific features
        """
        if not self.is_valid_card(card_code):
            return confidence
            
        rank, _ = card_code[0], card_code[1]
        
        # Special handling for commonly confused cards
        problematic_pairs = {
            # Cards that are commonly confused with each other
            'A': ['J', 'K', '2'],   # Aces often confused with Jacks, Kings or 2s
            'J': ['A', 'Q'],        # Jacks confused with Aces or Queens
            'Q': ['3', 'K'],        # Queens confused with 3s or Kings
            'K': ['A', 'Q'],        # Kings confused with Aces or Queens
            '2': ['A', 'J'],        # 2s confused with Aces or Jacks
            '3': ['Q', '8']         # 3s confused with Queens or 8s
        }
        
        # If this is a problematic card with low-medium confidence, reduce confidence
        if rank in problematic_pairs and confidence < 0.85:
            # If it's one of the commonly misidentified cards, be more skeptical
            return confidence * 0.9
            
        # For higher confidence matches on problematic cards, slightly boost confidence
        if rank in problematic_pairs and confidence > 0.85:
            return min(1.0, confidence * 1.1)
            
        return confidence
    
    def check_for_duplicates(self, cards):
        """
        Check for duplicate cards in a list and fix if found.
        
        Args:
            cards: List of card codes
            
        Returns:
            list: Fixed list without duplicates
        """
        if not cards:
            return []
            
        unique_cards = []
        seen_cards = set()
        
        for card in cards:
            if card == 'empty':
                continue
                
            if card in seen_cards:
                self.logger.warning(f"Duplicate card detected: {card} ({self.get_card_name(card)}). Marking as empty.")
                unique_cards.append('empty')
            else:
                seen_cards.add(card)
                unique_cards.append(card)
                
        return unique_cards

class ImprovedCardRecognizer:
    """
    Improved card recognition system that combines template matching with
    color analysis and empty slot detection.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('improved_recognition')
        
        # Initialize components
        self.empty_detector = EmptySlotDetector()
        self.color_detector = CardSuitColorDetector()
        self.verifier = CardVerifier()
        
        # Load original recognizer for template matching
        try:
            from src.card_recognizer import CardRecognizer
            self.card_recognizer = CardRecognizer()
            self.logger.info("Successfully loaded original card recognizer")
        except ImportError as e:
            self.logger.error(f"Failed to import card recognizer: {e}")
            self.logger.error("Make sure the src directory is in the Python path")
            self.logger.warning("Will try alternate import method")
            try:
                # Try direct import in case we're running from project root
                import sys
                sys.path.append("src")
                from card_recognizer import CardRecognizer
                self.card_recognizer = CardRecognizer()
                self.logger.info("Successfully loaded card recognizer (alternate method)")
            except ImportError as e2:
                self.logger.error(f"Failed to import card recognizer (alternate method): {e2}")
                self.logger.error("Critical error: Cannot continue without card recognizer")
                sys.exit(1)
        
        # Copy important attributes and methods from original recognizer
        self.card_regions = getattr(self.card_recognizer, 'card_regions', {})
        self.community_card_regions = getattr(self.card_recognizer, 'community_card_regions', {})
        
        # Create output directories
        os.makedirs("debug_cards/improved", exist_ok=True)
    
    def _check_empty_slot(self, card_img, debug):
        """Check if the card slot is empty"""
        is_empty, empty_confidence, debug_img = self.empty_detector.detect(card_img, debug)
        
        # Save empty detection debug image if requested
        if debug and debug_img is not None:
            timestamp = int(time.time() * 1000)
            debug_path = f"debug_cards/improved/empty_check_{timestamp}.png"
            cv2.imwrite(debug_path, debug_img)
            
        return is_empty, empty_confidence
    
    def _create_empty_result(self, confidence):
        """Create a result dict for an empty card slot"""
        return {
            'card_code': 'empty',
            'card_name': 'Empty',
            'confidence': confidence,
            'method': 'empty_detection',
            'is_empty': True,
            'error': None
        }
    
    def _apply_color_correction(self, card_code, color_info, confidence):
        """Apply color-based corrections to problematic cards"""
        if not card_code or len(card_code) != 2:
            return card_code, confidence
            
        rank, suit = card_code[0], card_code[1]
        
        # Only apply to problematic cards with lower confidence
        if rank not in ['A', 'J', 'Q'] or confidence >= 0.8:
            return card_code, confidence
            
        # Determine expected suit based on color analysis
        expected_suit = self._get_expected_suit_from_color(color_info)
        
        # If we have a strong color signal that differs from recognition
        if expected_suit and expected_suit != suit:
            old_card_code = card_code
            new_card_code = rank + expected_suit
            self.logger.info(f"Adjusted card {old_card_code} to {new_card_code} based on color analysis")
            # Boost confidence slightly since we're using additional color information
            new_confidence = min(1.0, confidence * 1.2)
            return new_card_code, new_confidence
            
        return card_code, confidence
    
    def _get_expected_suit_from_color(self, color_info):
        """Determine the expected suit based on color analysis"""
        if color_info['is_hearts'] and color_info['red_percentage'] > 3.0:
            return 'h'
        if color_info['is_diamonds'] and color_info['blue_percentage'] > 3.0:
            return 'd'
        if color_info['is_clubs'] and color_info['green_percentage'] > 3.0:
            return 'c'
        if color_info['is_spades'] and color_info['black_percentage'] > 3.0:
            return 's'
        return None
        
    def _create_card_result(self, card_code, card_name, confidence, original_confidence, 
                          confidence_adjustment, card_specific_adjustment, method, color_info):
        """Create a result dict for a recognized card"""
        return {
            'card_code': card_code,
            'card_name': card_name,
            'confidence': confidence,
            'original_confidence': original_confidence,
            'confidence_adjustment': confidence_adjustment,
            'card_specific_adjustment': card_specific_adjustment / (original_confidence * confidence_adjustment) 
                                        if original_confidence * confidence_adjustment > 0 else 1.0,
            'method': method,
            'is_empty': False,
            'color_info': color_info,
            'error': None
        }
        
    def update_regions(self, regions):
        """Update the card regions."""
        self.logger.info(f"Updating card regions in improved recognizer: {len(regions)} regions")
        self.card_regions = regions
        # Also update in the original recognizer
        if hasattr(self.card_recognizer, 'update_regions'):
            self.card_recognizer.update_regions(regions)
        else:
            self.card_recognizer.card_regions = regions
    
    def recognize_hero_hole_cards(self, table_image, debug=False):
        """
        Recognize hero's hole cards from the table image.
        This method implements the same interface as the original CardRecognizer.
        
        Args:
            table_image: Full table image
            debug: Whether to enable debug mode
            
        Returns:
            HoleCards: Object containing the recognized hole cards
        """
        try:
            from src.card_recognizer import HoleCards
        except ImportError:
            try:
                import sys
                sys.path.append("src")
                from card_recognizer import HoleCards
            except ImportError:
                self.logger.error("Cannot import HoleCards class - critical error")
                class HoleCards:
                    def __init__(self): self.cards = [None, None]
                    def is_valid(self): return False
                    def __str__(self): return "Unknown"
        
        self.logger.info("IMPROVED SYSTEM: Recognizing hero hole cards")
        
        # Debug: Log current regions
        self.logger.info(f"Available card regions: {list(self.card_regions.keys()) if self.card_regions else 'None'}")
        
        # Extract card regions using original code to maintain compatibility
        card1_img, card2_img = None, None
        
        # Use the regions defined in the original recognizer
        if not hasattr(self, 'card_regions') or not self.card_regions:
            self.logger.warning("No card regions defined - cannot recognize hole cards")
            return HoleCards()
        
        # Extract card images using the regions
        try:
            height, width = table_image.shape[:2]
            self.logger.info(f"Processing table image: {width}x{height}")
            
            # Extract first card
            if 'hero_card1' in self.card_regions:
                region = self.card_regions['hero_card1']
                # Handle both percentage and decimal formats - check multiple possible keys
                x_val = region.get('x', region.get('x_percent', 0))
                y_val = region.get('y', region.get('y_percent', 0))
                w_val = region.get('width', region.get('w', region.get('width_percent', 0)))
                h_val = region.get('height', region.get('h', region.get('height_percent', 0)))
                
                # Convert percentage values to decimals if they're greater than 1
                if x_val > 1:
                    x_val = x_val / 100.0
                if y_val > 1:
                    y_val = y_val / 100.0
                if w_val > 1:
                    w_val = w_val / 100.0
                if h_val > 1:
                    h_val = h_val / 100.0
                
                # Convert to pixels
                x = int(width * x_val)
                y = int(height * y_val)
                w = int(width * w_val)
                h = int(height * h_val)
                
                self.logger.info(f"Hero card 1 region: x={x}, y={y}, w={w}, h={h} (from {x_val:.4f}, {y_val:.4f}, {w_val:.4f}, {h_val:.4f})")
                if x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height:
                    card1_img = table_image[y:y+h, x:x+w]
                    if debug:
                        cv2.imwrite("debug_cards/improved/hero_card1.png", card1_img)
                        self.logger.info("Saved hero card 1 debug image")
                else:
                    self.logger.warning(f"Hero card 1 region out of bounds: x={x}, y={y}, w={w}, h={h}")
            
            # Extract second card
            if 'hero_card2' in self.card_regions:
                region = self.card_regions['hero_card2']
                # Handle both percentage and decimal formats - check multiple possible keys
                x_val = region.get('x', region.get('x_percent', 0))
                y_val = region.get('y', region.get('y_percent', 0))
                w_val = region.get('width', region.get('w', region.get('width_percent', 0)))
                h_val = region.get('height', region.get('h', region.get('height_percent', 0)))
                
                # Convert percentage values to decimals if they're greater than 1
                if x_val > 1:
                    x_val = x_val / 100.0
                if y_val > 1:
                    y_val = y_val / 100.0
                if w_val > 1:
                    w_val = w_val / 100.0
                if h_val > 1:
                    h_val = h_val / 100.0
                
                # Convert to pixels
                x = int(width * x_val)
                y = int(height * y_val)
                w = int(width * w_val)
                h = int(height * h_val)
                
                self.logger.info(f"Hero card 2 region: x={x}, y={y}, w={w}, h={h} (from {x_val:.4f}, {y_val:.4f}, {w_val:.4f}, {h_val:.4f})")
                if x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height:
                    card2_img = table_image[y:y+h, x:x+w]
                    if debug:
                        cv2.imwrite("debug_cards/improved/hero_card2.png", card2_img)
                        self.logger.info("Saved hero card 2 debug image")
                else:
                    self.logger.warning(f"Hero card 2 region out of bounds: x={x}, y={y}, w={w}, h={h}")
            
            # Process each card with improved result handling
            def extract_card_code(result):
                """Extract card code from various result formats"""
                if result is None:
                    return None
                if isinstance(result, tuple) and len(result) >= 1:
                    return result[0] if result[0] not in ('empty', 'error') else None
                elif isinstance(result, dict):
                    card_code = result.get('card_code', 'empty')
                    return card_code if card_code not in ('empty', 'error') else None
                return None
            
            card1_result = self.recognize_card(card1_img, debug) if card1_img is not None else None
            card2_result = self.recognize_card(card2_img, debug) if card2_img is not None else None
            
            self.logger.info(f"Card 1 result: {card1_result}")
            self.logger.info(f"Card 2 result: {card2_result}")
            
            # Create hole cards object
            hole_cards = HoleCards()
            
            # Extract card codes safely
            card1_code = extract_card_code(card1_result)
            card2_code = extract_card_code(card2_result)
            
            if card1_code:
                hole_cards.cards[0] = card1_code
                self.logger.info(f"Hero card 1 recognized: {card1_code}")
                
            if card2_code:
                hole_cards.cards[1] = card2_code
                self.logger.info(f"Hero card 2 recognized: {card2_code}")
                
            self.logger.info(f"IMPROVED SYSTEM: Final hole cards: {hole_cards}")
            return hole_cards
            
        except Exception as e:
            self.logger.error(f"Error in recognize_hero_hole_cards: {e}", exc_info=True)
            return HoleCards()
            
    def recognize_community_card(self, card_img, position, debug=False):
        """
        Recognize a community card with enhanced recognition.
        This ensures compatibility with the original card recognizer interface.
        
        Args:
            card_img: The card image
            position: The position index (1-5)
            debug: Whether to enable debug mode
        
        Returns:
            str: The card code (e.g. 'Ah', 'Tc')
        """
        result = self.recognize_card(card_img, debug)
        if isinstance(result, tuple) and len(result) >= 1:
            return result[0]
        elif isinstance(result, dict) and 'card_code' in result:
            return result['card_code']
        else:
            return 'empty'

    def recognize_card(self, card_img, debug=False):
        """
        Enhanced card recognition with empty slot detection, color validation,
        and duplicate prevention.
        
        Args:
            card_img: The card image to recognize
            debug: Whether to save debug images
            
        Returns:
            dict or tuple: Recognition results with detailed information
                If called from original code, returns a tuple (card_code, confidence, method)
                If called directly, returns a dictionary with detailed information
        """
        # Check if this is being called from our code or from poker_bot.py
        # By examining the call stack, we can determine the appropriate return format
        import inspect
        caller = inspect.currentframe().f_back.f_code.co_name
        
        # Return tuple format if called from standard poker_bot methods
        return_tuple = caller in ('recognize_hero_hole_cards', 'detect_community_cards', 
                                 'analyze_game_state', 'recognize_card_image', '_recognize_card')
        
        try:
            if card_img is None or card_img.size == 0:
                self.logger.warning("Cannot recognize None or empty image")
                return ('empty', 1.0, 'empty_check') if return_tuple else self._create_empty_result(1.0)
                
            # 1. Check if the slot is empty
            is_empty, empty_confidence = self._check_empty_slot(card_img, debug)
            
            # 2. If empty with high confidence, don't process further
            if is_empty and empty_confidence > 0.7:
                self.logger.info(f"Empty slot detected with confidence {empty_confidence:.2f}")
                return ('empty', empty_confidence, 'empty_check') if return_tuple else self._create_empty_result(empty_confidence)
                
            # 3. Analyze card colors for suit validation
            color_info = self.color_detector.analyze_card(card_img, debug)
            
            # 4. Perform template matching with original recognizer
            try:
                # Call the original recognizer with error handling
                if hasattr(self.card_recognizer, 'recognize_card'):
                    orig_result = self.card_recognizer.recognize_card(card_img, debug)
                    if isinstance(orig_result, tuple) and len(orig_result) >= 2:
                        # Standard tuple format (card_code, confidence, method)
                        card_code, confidence = orig_result[0], orig_result[1]
                        method = orig_result[2] if len(orig_result) > 2 else "template_matching"
                    elif isinstance(orig_result, str):
                        # Some versions might just return the card code
                        card_code = orig_result
                        confidence = 0.8  # Assume reasonable confidence
                        method = "template_matching"
                    else:
                        # Unknown format, treat as failed
                        card_code = "empty"
                        confidence = 0.5
                        method = "unknown_format"
                else:
                    # No recognize_card method
                    self.logger.warning("Original recognizer has no recognize_card method")
                    card_code = "empty"
                    confidence = 0.5
                    method = "no_method"
            except Exception as e:
                self.logger.error(f"Error in original recognizer: {e}")
                # Fallback to empty if recognition fails
                card_code = "empty" 
                confidence = 0.5
                method = "failed"
            
            # 5. Verify color consistency and adjust confidence
            confidence_adjustment = self.verifier.verify_color_consistency(card_code, color_info)
            adjusted_confidence = confidence * confidence_adjustment
            
            # 6. Apply additional verification for problematic cards
            card_specific_adjustment = self.verifier.verify_card_features(card_code, adjusted_confidence)
            final_confidence = adjusted_confidence * card_specific_adjustment
            
            # 7. Apply color-based corrections for problematic cards
            card_code, final_confidence = self._apply_color_correction(card_code, color_info, final_confidence)
            
            # 8. Validate the card code - make sure it's a valid code
            if not self.verifier.is_valid_card(card_code):
                self.logger.warning(f"Invalid card code detected: {card_code}, treating as empty")
                return ('empty', 0.9, 'validation_failed') if return_tuple else self._create_empty_result(0.9)
            
            # 9. If confidence is too low or the card looks empty, override
            if final_confidence < 0.6 and empty_confidence > 0.6:
                self.logger.info(f"Overriding low confidence card ({card_code}, {final_confidence:.2f}) with empty slot detection")
                return ('empty', empty_confidence, 'low_confidence_override') if return_tuple else self._create_empty_result(empty_confidence)
            
            # 10. Return the result in the appropriate format
            card_name = self.verifier.get_card_name(card_code)
            if return_tuple:
                return (card_code, final_confidence, method)
            else:
                return self._create_card_result(
                    card_code, card_name, final_confidence, confidence, 
                    confidence_adjustment, card_specific_adjustment, method, color_info
                )
            
        except Exception as e:
            self.logger.error(f"Error in improved card recognition: {e}", exc_info=True)
            if return_tuple:
                return ('error', 0.0, 'error')
            else:
                return {
                    'card_code': 'error',
                    'card_name': 'Error',
                    'confidence': 0.0,
                    'method': 'error',
                    'is_empty': False,
                    'color_info': {},
                    'error': str(e)
                }
    
    def recognize_multiple_cards(self, card_images, debug=False):
        """
        Process multiple card images and prevent duplicates.
        
        Args:
            card_images: List of card images to recognize
            debug: Whether to save debug images
            
        Returns:
            list: Recognition results for each card
        """
        # Process each card individually
        results = []
        card_codes = []
        
        for i, img in enumerate(card_images):
            result = self.recognize_card(img, debug)
            results.append(result)
            
            if not result['is_empty']:
                card_codes.append(result['card_code'])
            else:
                card_codes.append('empty')
                
        # Check for duplicates and fix if needed
        fixed_codes = self.verifier.check_for_duplicates(card_codes)
        
        # Update results if fixes were made
        for i, (fixed, original) in enumerate(zip(fixed_codes, card_codes)):
            if fixed != original:
                results[i]['card_code'] = fixed
                results[i]['card_name'] = self.verifier.get_card_name(fixed)
                results[i]['confidence'] = 0.0
                results[i]['method'] = 'duplicate_correction'
                results[i]['is_empty'] = (fixed == 'empty')
                results[i]['duplicate_of'] = original
                
        return results

def main():
    """Command-line interface for testing the improved card recognition."""
    parser = argparse.ArgumentParser(description='Improved card recognition with empty slot detection and color analysis')
    parser.add_argument('--image', help='Path to card image to analyze')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    if not args.image:
        parser.print_help()
        return
    
    recognizer = ImprovedCardRecognizer()
    
    # Load the image
    image = cv2.imread(args.image)
    if image is None:
        logger.error(f"Failed to load image: {args.image}")
        return
    
    # Run recognition
    result = recognizer.recognize_card(image, debug=True if args.debug else False)
    
    # Print results
    logger.info(f"Recognition results for {args.image}:")
    for key, value in result.items():
        if key != 'color_info':  # Skip detailed color info in output
            logger.info(f"  {key}: {value}")

if __name__ == "__main__":
    import argparse
    main()
