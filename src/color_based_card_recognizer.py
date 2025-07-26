"""
Color-Based Card Recognizer

This module enhances card recognition by using distinct colors for each suit.
- Clubs: Green
- Hearts: Red  
- Diamonds: Blue
- Spades: Black

This approach provides more reliable suit detection combined with template matching for rank detection.
"""

import cv2
import numpy as np
import logging
import os
import time
from typing import Optional, Dict, List, Tuple

# Add path to the src directory
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from card import Card

class ColorBasedCardRecognizer:
    """
    Enhanced card recognizer that uses color detection for suit identification
    and template matching for rank identification.
    """

    def __init__(self, template_dir="card_templates"):
        """Initialize the color-based card recognizer."""
        self.logger = logging.getLogger('color_card_recognizer')
        
        # Set up template directory
        self.template_dir = template_dir
        self.template_loaded = False
        self.card_templates = {}
        self.rank_templates = {}
        self.load_templates()
        
        # Define color ranges for suits in HSV space
        self.suit_colors = {
            'clubs': {
                'lower': np.array([35, 50, 50]),   # Green
                'upper': np.array([85, 255, 255]), 
                'code': 'c'
            },
            'hearts': {
                'lower': np.array([0, 100, 100]),  # Red (lower range)
                'upper': np.array([10, 255, 255]),
                'code': 'h'
            },
            'hearts2': {  # Second range for red (HSV wraps around)
                'lower': np.array([170, 100, 100]),  # Red (upper range)
                'upper': np.array([180, 255, 255]),
                'code': 'h'
            },
            'diamonds': {
                'lower': np.array([100, 50, 50]),  # Blue
                'upper': np.array([130, 255, 255]),
                'code': 'd'
            },
            'spades': {
                'lower': np.array([0, 0, 0]),      # Black
                'upper': np.array([180, 50, 50]),
                'code': 's'
            }
        }
        
        # Define regions of interest for suit color detection
        # These are normalized coordinates (0-1) relative to card dimensions
        self.suit_regions = [
            # Top left suit
            {'x': 0.05, 'y': 0.05, 'width': 0.2, 'height': 0.2},
            # Bottom right suit
            {'x': 0.75, 'y': 0.75, 'width': 0.2, 'height': 0.2},
            # Center suit (for face cards)
            {'x': 0.3, 'y': 0.3, 'width': 0.4, 'height': 0.4}
        ]
        
        # Create debug directory
        os.makedirs("debug_color_recognition", exist_ok=True)
        
    def load_templates(self):
        """Load card templates from disk."""
        try:
            if not os.path.exists(self.template_dir):
                self.logger.warning(f"Template directory {self.template_dir} not found")
                return
            
            # Load full card templates
            for suit in ['s', 'h', 'd', 'c']:
                for rank in ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']:
                    template_map = {
                        's': 'spades',
                        'h': 'hearts',
                        'd': 'diamonds',
                        'c': 'clubs'
                    }
                    
                    # Try exact file match first
                    template_path = os.path.join(self.template_dir, f"{rank}_{template_map[suit]}.png")
                    if not os.path.exists(template_path):
                        # Try alternative naming pattern
                        template_path = os.path.join(self.template_dir, f"{rank}{suit}.png")
                    
                    if os.path.exists(template_path):
                        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                        if template is not None:
                            self.card_templates[f"{rank}{suit}"] = template
                            self.logger.debug(f"Loaded template: {rank}{suit} from {template_path}")
            
            # Create rank-only template directory if it doesn't exist
            rank_template_dir = os.path.join("debug_color_recognition", "ranks")
            os.makedirs(rank_template_dir, exist_ok=True)
            
            # Extract rank-only templates from full card templates for improved rank detection
            for card_name, template in self.card_templates.items():
                if template is not None:
                    rank = card_name[0]
                    h, w = template.shape
                    
                    # Extract top-left corner for rank
                    rank_img = template[0:int(h*0.25), 0:int(w*0.25)]
                    
                    # Save if not already in rank_templates
                    if rank not in self.rank_templates:
                        self.rank_templates[rank] = rank_img
                        
                        # Save for debugging
                        rank_path = os.path.join(rank_template_dir, f"{rank}.png")
                        cv2.imwrite(rank_path, rank_img)
            
            self.template_loaded = len(self.card_templates) > 0
            self.logger.info(f"Loaded {len(self.card_templates)} card templates and {len(self.rank_templates)} rank templates")
            
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            self.template_loaded = False
    
    def detect_suit_by_color(self, card_img) -> Tuple[str, float]:
        """
        Detect card suit based on color.
        Returns tuple of (suit_code, confidence)
        """
        try:
            if card_img is None or card_img.size == 0:
                return None, 0.0
            
            # Convert to BGR color space if grayscale
            if len(card_img.shape) < 3:
                colored = cv2.cvtColor(card_img, cv2.COLOR_GRAY2BGR)
            else:
                colored = card_img
                
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(colored, cv2.COLOR_BGR2HSV)
            
            # Get card dimensions
            h, w = colored.shape[:2]
            
            # Extract regions of interest for suit detection
            regions = []
            for region in self.suit_regions:
                x = int(w * region['x'])
                y = int(h * region['y'])
                width = int(w * region['width'])
                height = int(h * region['height'])
                
                # Ensure region is within image bounds
                x = max(0, min(x, w-1))
                y = max(0, min(y, h-1))
                width = max(1, min(width, w-x))
                height = max(1, min(height, h-y))
                
                roi = hsv[y:y+height, x:x+width]
                regions.append(roi)
            
            # Check each suit color in each region
            suit_scores = {'c': 0, 'h': 0, 'd': 0, 's': 0}
            total_pixels = sum(r.shape[0] * r.shape[1] for r in regions)
            
            # For debugging
            color_masks = {}
            
            for suit_name, color_range in self.suit_colors.items():
                suit_code = color_range['code']
                color_pixels = 0
                
                for region in regions:
                    if region.size == 0:
                        continue
                    
                    # Create mask for this color range
                    mask = cv2.inRange(region, color_range['lower'], color_range['upper'])
                    color_pixels += cv2.countNonZero(mask)
                    
                    # Store mask for debugging
                    if suit_code not in color_masks:
                        color_masks[suit_code] = mask
                    else:
                        # Try to combine masks if dimensions match
                        if color_masks[suit_code].shape == mask.shape:
                            color_masks[suit_code] = cv2.bitwise_or(color_masks[suit_code], mask)
                
                # Calculate percentage of pixels matching this color
                if total_pixels > 0:
                    color_percentage = color_pixels / total_pixels
                    suit_scores[suit_code] += color_percentage
            
            # Find the dominant suit color
            dominant_suit = max(suit_scores, key=suit_scores.get)
            confidence = suit_scores[dominant_suit]
            
            # Debug logging
            self.logger.debug(f"Suit color scores: {suit_scores}")
            self.logger.debug(f"Detected suit: {dominant_suit} with confidence {confidence:.3f}")
            
            # Save debug visualization
            debug_img = colored.copy()
            h_debug, w_debug = debug_img.shape[:2]
            
            # Add text with color scores
            y_pos = 20
            for suit, score in suit_scores.items():
                text = f"{suit}: {score:.2f}"
                cv2.putText(debug_img, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                y_pos += 20
                
            # Draw regions of interest
            for region in self.suit_regions:
                x = int(w_debug * region['x'])
                y = int(h_debug * region['y'])
                width = int(w_debug * region['width'])
                height = int(h_debug * region['height'])
                
                cv2.rectangle(debug_img, (x, y), (x+width, y+height), (0, 0, 255), 1)
            
            timestamp = int(time.time() * 1000)
            debug_filename = f"debug_color_recognition/suit_color_{dominant_suit}_{confidence:.2f}_{timestamp}.png"
            cv2.imwrite(debug_filename, debug_img)
            
            # Only return if confidence is above threshold
            if confidence > 0.15:  # At least 15% of pixels match the color
                return dominant_suit, confidence
            
            return None, 0.0
            
        except Exception as e:
            self.logger.error(f"Error detecting suit by color: {e}")
            return None, 0.0
    
    def detect_rank(self, card_img) -> Tuple[str, float]:
        """
        Detect card rank using template matching.
        Returns tuple of (rank, confidence)
        """
        try:
            if not self.template_loaded:
                return None, 0.0
                
            if card_img is None or card_img.size == 0:
                return None, 0.0
            
            # Convert to grayscale if needed
            if len(card_img.shape) == 3:
                gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = card_img
            
            # Extract top-left corner for rank detection
            h, w = gray.shape
            top_left = gray[0:int(h*0.25), 0:int(w*0.25)]
            
            # Save the top-left corner for debugging
            timestamp = int(time.time() * 1000)
            tl_debug_path = f"debug_color_recognition/top_left_{timestamp}.png"
            cv2.imwrite(tl_debug_path, top_left)
            
            # Try rank-specific templates first
            best_rank = None
            best_confidence = 0
            best_loc = None
            
            for rank, template in self.rank_templates.items():
                # Resize template to match target (or try multiple scales)
                scales = [0.8, 0.9, 1.0, 1.1, 1.2]
                
                for scale in scales:
                    # Calculate new dimensions
                    new_width = int(template.shape[1] * scale)
                    new_height = int(template.shape[0] * scale)
                    
                    # Skip if new dimensions are invalid
                    if new_width <= 0 or new_height <= 0:
                        continue
                        
                    # Skip if new dimensions are larger than the target image
                    if new_width > top_left.shape[1] or new_height > top_left.shape[0]:
                        continue
                    
                    # Resize template
                    resized_template = cv2.resize(template, (new_width, new_height))
                    
                    # Apply template matching
                    try:
                        result = cv2.matchTemplate(top_left, resized_template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)
                        
                        if max_val > best_confidence:
                            best_confidence = max_val
                            best_rank = rank
                            best_loc = max_loc
                    except Exception as e:
                        self.logger.debug(f"Error matching template for rank {rank} at scale {scale}: {e}")
            
            # Create debug image
            if best_rank and best_confidence > 0.5:
                # Draw bounding box on debug image
                debug_img = cv2.cvtColor(top_left, cv2.COLOR_GRAY2BGR) if len(top_left.shape) < 3 else top_left.copy()
                if best_loc and best_rank in self.rank_templates:
                    template = self.rank_templates[best_rank]
                    h, w = template.shape
                    cv2.rectangle(debug_img, best_loc, (best_loc[0] + w, best_loc[1] + h), (0, 255, 0), 1)
                    
                # Add rank and confidence text
                cv2.putText(debug_img, f"{best_rank}: {best_confidence:.2f}", (10, 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Save debug image
                rank_debug_path = f"debug_color_recognition/rank_match_{best_rank}_{best_confidence:.2f}_{timestamp}.png"
                cv2.imwrite(rank_debug_path, debug_img)
                
                return best_rank, best_confidence
                
            return None, 0.0
            
        except Exception as e:
            self.logger.error(f"Error detecting rank: {e}")
            return None, 0.0
    
    def recognize_card(self, card_img, debug=False):
        """
        Recognize a card using color-based suit detection and template-based rank detection.
        Returns a Card object if recognition is successful, None otherwise.
        """
        try:
            if card_img is None or card_img.size == 0:
                return None
            
            # Save original card image for debugging
            if debug:
                timestamp = int(time.time() * 1000)
                orig_path = f"debug_color_recognition/original_card_{timestamp}.png"
                cv2.imwrite(orig_path, card_img)
            
            # Step 1: Detect suit by color
            suit, suit_confidence = self.detect_suit_by_color(card_img)
            
            # Step 2: Detect rank
            rank, rank_confidence = self.detect_rank(card_img)
            
            # Create card if both components were detected
            if suit and rank:
                combined_confidence = (suit_confidence * 0.6) + (rank_confidence * 0.4)
                card = Card(rank=rank, suit=suit, confidence=combined_confidence)
                
                if debug:
                    # Save debug image
                    self._save_debug_image(card_img, card, suit_confidence, rank_confidence)
                
                self.logger.info(f"Card recognized: {card.rank}{card.suit} (suit conf: {suit_confidence:.2f}, rank conf: {rank_confidence:.2f})")
                return card
                
            # If only suit detected, try to improve rank detection
            elif suit and suit_confidence > 0.6:
                self.logger.debug(f"Suit detected ({suit}, {suit_confidence:.2f}) but rank detection failed")
                
                # Try alternative rank detection with looser threshold
                for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
                    # Check if we have a template for this suit
                    template_name = f"{rank}{suit}"
                    if template_name in self.card_templates:
                        # Use suit confidence as fallback
                        card = Card(rank=rank, suit=suit, confidence=suit_confidence * 0.7)
                        if debug:
                            self._save_debug_image(card_img, card, suit_confidence, 0.0, "suit_only")
                        return card
                
            # If only rank detected, try again with looser color thresholds
            elif rank and rank_confidence > 0.7:
                self.logger.debug(f"Rank detected ({rank}, {rank_confidence:.2f}) but suit detection failed")
                
                # Try different suit color thresholds
                extended_suit_scores = {}
                for suit_code in ['c', 'h', 'd', 's']:
                    # Try template with this suit and the detected rank
                    template_name = f"{rank}{suit_code}"
                    if template_name in self.card_templates:
                        template = self.card_templates[template_name]
                        try:
                            resized_template = cv2.resize(template, (card_img.shape[1], card_img.shape[0]))
                            gray_img = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY) if len(card_img.shape) == 3 else card_img
                            result = cv2.matchTemplate(gray_img, resized_template, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(result)
                            extended_suit_scores[suit_code] = max_val
                        except Exception as e:
                            self.logger.debug(f"Error in template matching for {template_name}: {e}")
                
                if extended_suit_scores:
                    best_suit = max(extended_suit_scores, key=extended_suit_scores.get)
                    best_suit_conf = extended_suit_scores[best_suit]
                    
                    if best_suit_conf > 0.5:
                        card = Card(rank=rank, suit=best_suit, confidence=best_suit_conf * 0.8)
                        if debug:
                            self._save_debug_image(card_img, card, best_suit_conf, rank_confidence, "rank_primary")
                        return card
            
            # No valid card detected
            if debug:
                timestamp = int(time.time() * 1000)
                filename = f"debug_color_recognition/failed_{timestamp}.png"
                cv2.imwrite(filename, card_img)
                self.logger.debug(f"Failed card recognition saved to {filename}")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error in recognize_card: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _save_debug_image(self, card_img, card, suit_confidence, rank_confidence, method="standard"):
        """Save a debug image with detection information."""
        try:
            import time
            
            timestamp = int(time.time() * 1000)
            debug_img = card_img.copy()
            
            # Convert to color if grayscale
            if len(debug_img.shape) < 3:
                debug_img = cv2.cvtColor(debug_img, cv2.COLOR_GRAY2BGR)
            
            # Draw card info on the image
            card_text = f"{card.rank}{card.suit} ({suit_confidence:.2f}/{rank_confidence:.2f})"
            
            # Ensure text fits on the image
            font_scale = debug_img.shape[1] / 200
            thickness = max(1, int(debug_img.shape[1] / 100))
            
            # Add info text at the top
            cv2.putText(debug_img, card_text, (5, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
            
            # Add method info
            cv2.putText(debug_img, method, (5, debug_img.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.8, (255, 0, 0), thickness)
            
            # Save the image
            filename = f"debug_color_recognition/{card.rank}{card.suit}_{timestamp}.png"
            cv2.imwrite(filename, debug_img)
            
        except Exception as e:
            self.logger.error(f"Error saving debug image: {e}")
