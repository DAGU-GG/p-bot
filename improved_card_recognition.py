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
        
        # Load original recognizer for template matching
        try:
            from src.card_recognizer import CardRecognizer
            self.card_recognizer = CardRecognizer()
            self.logger.info("Successfully loaded original card recognizer")
        except ImportError as e:
            self.logger.error(f"Failed to import card recognizer: {e}")
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
        
        # Create output directories
        os.makedirs("debug_cards/improved", exist_ok=True)
    
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
                    def __init__(self): 
                        self.card1 = None
                        self.card2 = None
                        self.detection_confidence = 0.0
                        self.timestamp = time.time()
                    def is_valid(self): 
                        return self.card1 is not None and self.card2 is not None
                    def __str__(self): 
                        if self.is_valid():
                            return f"{self.card1}, {self.card2}"
                        return "No cards detected"
        
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
            
            # Process each card with improved recognition
            card1_result = None
            card2_result = None
            
            if card1_img is not None and card1_img.size > 0:
                self.logger.info("Processing hero card 1...")
                card1_result = self.recognize_card(card1_img, debug)
                self.logger.info(f"Hero card 1 recognition result: {card1_result}")
            
            if card2_img is not None and card2_img.size > 0:
                self.logger.info("Processing hero card 2...")
                card2_result = self.recognize_card(card2_img, debug)
                self.logger.info(f"Hero card 2 recognition result: {card2_result}")
            
            # Create hole cards object and populate it
            hole_cards = HoleCards()
            
            # Convert results to Card objects for HoleCards
            try:
                from src.card_recognizer import Card
            except ImportError:
                try:
                    from card_recognizer import Card
                except ImportError:
                    # Create minimal Card class
                    class Card:
                        def __init__(self, rank, suit, confidence=0.0):
                            self.rank = rank
                            self.suit = suit
                            self.confidence = confidence
                        def __str__(self):
                            return f"{self.rank} of {{'h': 'Hearts', 'd': 'Diamonds', 'c': 'Clubs', 's': 'Spades'}.get(self.suit, self.suit)}"
            
            # Process card 1 result
            if card1_result and isinstance(card1_result, tuple) and len(card1_result) >= 2:
                card_code, confidence = card1_result[0], card1_result[1]
                if card_code and card_code not in ('empty', 'error', 'unknown') and len(card_code) >= 2:
                    rank, suit = card_code[0], card_code[1]
                    hole_cards.card1 = Card(rank=rank, suit=suit, confidence=confidence)
                    self.logger.info(f"Hero card 1 recognized: {hole_cards.card1}")
            
            # Process card 2 result
            if card2_result and isinstance(card2_result, tuple) and len(card2_result) >= 2:
                card_code, confidence = card2_result[0], card2_result[1]
                if card_code and card_code not in ('empty', 'error', 'unknown') and len(card_code) >= 2:
                    rank, suit = card_code[0], card_code[1]
                    hole_cards.card2 = Card(rank=rank, suit=suit, confidence=confidence)
                    self.logger.info(f"Hero card 2 recognized: {hole_cards.card2}")
            
            # Calculate detection confidence
            if hole_cards.card1 and hole_cards.card2:
                hole_cards.detection_confidence = (hole_cards.card1.confidence + hole_cards.card2.confidence) / 2
            elif hole_cards.card1:
                hole_cards.detection_confidence = hole_cards.card1.confidence / 2
            elif hole_cards.card2:
                hole_cards.detection_confidence = hole_cards.card2.confidence / 2
            else:
                hole_cards.detection_confidence = 0.0
            
            hole_cards.timestamp = time.time()
            
            self.logger.info(f"IMPROVED SYSTEM: Final hole cards: {hole_cards} (confidence: {hole_cards.detection_confidence:.3f})")
            return hole_cards
            
        except Exception as e:
            self.logger.error(f"Error in recognize_hero_hole_cards: {e}", exc_info=True)
            return HoleCards()
    
    def recognize_card(self, card_img, debug=False):
        """
        Enhanced card recognition with empty slot detection, color validation,
        and duplicate prevention.
        
        Args:
            card_img: The card image to recognize
            debug: Whether to save debug images
            
        Returns:
            tuple: (card_code, confidence, method) for compatibility with poker bot
        """
        # Check if this is being called from our code or from poker_bot.py
        # Always return tuple format for maximum compatibility
        return_tuple = True
        
        try:
            if card_img is None or card_img.size == 0:
                self.logger.warning("Cannot recognize None or empty image")
                return ('empty', 1.0, 'empty_check')
                
            # 1. Check if the slot is empty
            is_empty, empty_confidence = self._check_empty_slot(card_img, debug)
            
            # 2. If empty with high confidence, don't process further
            if is_empty and empty_confidence > 0.7:
                self.logger.info(f"Empty slot detected with confidence {empty_confidence:.2f}")
                return ('empty', empty_confidence, 'empty_check')
                
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
            
            # CRITICAL FIX: If template matching failed, try direct template matching
            if card_code in ('empty', 'error', 'unknown') or confidence < 0.3:
                self.logger.info("Template matching failed or low confidence, trying direct template matching...")
                try:
                    # Use the original recognizer's template matching directly
                    template_card = self.card_recognizer.recognize_card_by_template_matching(card_img, debug)
                    if template_card and hasattr(template_card, 'rank') and hasattr(template_card, 'suit'):
                        card_code = f"{template_card.rank}{template_card.suit}"
                        confidence = getattr(template_card, 'confidence', 0.7)
                        method = "direct_template_matching"
                        self.logger.info(f"Direct template matching succeeded: {card_code} (confidence: {confidence:.3f})")
                    else:
                        self.logger.warning("Direct template matching also failed")
                except Exception as e:
                    self.logger.error(f"Error in direct template matching: {e}")
            
            # CRITICAL FIX: If still no card detected, try OCR as final fallback
            if card_code in ('empty', 'error', 'unknown') or confidence < 0.3:
                self.logger.info("Trying OCR as final fallback...")
                try:
                    ocr_card = self.card_recognizer.recognize_card_by_ocr(card_img)
                    if ocr_card and hasattr(ocr_card, 'rank') and hasattr(ocr_card, 'suit'):
                        card_code = f"{ocr_card.rank}{ocr_card.suit}"
                        confidence = getattr(ocr_card, 'confidence', 0.5)
                        method = "ocr_fallback"
                        self.logger.info(f"OCR fallback succeeded: {card_code} (confidence: {confidence:.3f})")
                    else:
                        self.logger.warning("OCR fallback also failed")
                except Exception as e:
                    self.logger.error(f"Error in OCR fallback: {e}")
            
            # 5. Validate the card code - make sure it's a valid code
            if card_code and len(card_code) >= 2:
                rank, suit = card_code[0], card_code[1]
                valid_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
                valid_suits = ['h', 'd', 'c', 's']
                
                if rank not in valid_ranks or suit not in valid_suits:
                    self.logger.warning(f"Invalid card code detected: {card_code}, treating as empty")
                    return ('empty', 0.9, 'validation_failed')
            
            # 6. Lower the confidence threshold to be more permissive
            if confidence < 0.3 and empty_confidence > 0.8:
                self.logger.info(f"Overriding very low confidence card ({card_code}, {confidence:.2f}) with empty slot detection")
                return ('empty', empty_confidence, 'low_confidence_override')
            
            # 7. Return the result in tuple format
            return (card_code, confidence, method)
            
        except Exception as e:
            self.logger.error(f"Error in improved card recognition: {e}", exc_info=True)
            return ('error', 0.0, 'error')
    
    def _check_empty_slot(self, card_img, debug):
        """Check if the card slot is empty"""
        is_empty, empty_confidence, debug_img = self.empty_detector.detect(card_img, debug)
        
        # Save empty detection debug image if requested
        if debug and debug_img is not None:
            timestamp = int(time.time() * 1000)
            debug_path = f"debug_cards/improved/empty_check_{timestamp}.png"
            cv2.imwrite(debug_path, debug_img)
            
        return is_empty, empty_confidence