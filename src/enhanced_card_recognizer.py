"""
Enhanced Card Recognizer

This class integrates color-based suit detection with the standard template matching approach
to provide more accurate card recognition.
"""

import os
import sys
import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import time

# Ensure src directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try different import strategies
try:
    from src.card import Card
except ImportError:
    try:
        from card import Card
    except ImportError:
        # Define a minimal Card class if the import fails
        class Card:
            def __init__(self, rank, suit, confidence=0.0):
                self.rank = rank
                self.suit = suit
                self.confidence = confidence
                
            def __str__(self):
                return f"{self.rank} of {self.suit} ({self.confidence:.2f})"

try:
    from src.card_recognizer import CardRecognizer
except ImportError:
    from card_recognizer import CardRecognizer

try:
    from src.card_suit_color_detector import CardSuitColorDetector
except ImportError:
    from card_suit_color_detector import CardSuitColorDetector

class EnhancedCardRecognizer(CardRecognizer):
    """
    Enhanced card recognizer that integrates color-based suit detection
    with the standard template matching approach.
    """
    
    def __init__(self):
        """Initialize the enhanced card recognizer."""
        super().__init__()
        self.logger = logging.getLogger('enhanced_card_recognizer')
        
        # Initialize the suit color detector
        self.suit_color_detector = CardSuitColorDetector()
        
        # Performance metrics
        self.recognition_attempts = 0
        self.template_match_success = 0
        self.color_enhanced_success = 0
        
        # Debug settings
        self.debug_dir = "debug_enhanced_recognition"
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def recognize_card(self, card_img, debug=False):
        """
        Recognize a card using both template matching and color-based suit detection.
        
        Args:
            card_img: The card image to recognize
            debug: Whether to save debug images
            
        Returns:
            Card object or None if recognition failed
        """
        self.recognition_attempts += 1
        
        # First try the standard template matching approach
        card = super().recognize_card(card_img, debug)
        
        # If standard recognition is confident, use it
        if card and card.confidence > 0.85:
            self.template_match_success += 1
            self.logger.debug(f"Standard recognition succeeded with high confidence: {card}")
            if debug:
                self._save_debug_image(card_img, card, "standard")
            return card
            
        # If standard recognition failed or has low confidence, try enhanced approach
        suit_color, color_confidence = self.suit_color_detector.detect_suit_color(card_img, debug)
        
        # If we couldn't detect the color, return standard result
        if suit_color == 'unknown' or color_confidence < 0.05:
            self.logger.debug(f"Color detection failed, using standard result: {card}")
            return card
            
        # Try to improve recognition with color information
        enhanced_card = self._enhance_recognition_with_color(card, suit_color, card_img, debug)
        
        if enhanced_card:
            self.color_enhanced_success += 1
            self.logger.debug(f"Enhanced recognition succeeded: {enhanced_card}")
            if debug:
                self._save_debug_image(card_img, enhanced_card, "enhanced")
            return enhanced_card
        
        # If enhancement failed, return the original result
        return card
    
    def _enhance_recognition_with_color(self, original_card, suit_color, card_img, debug=False):
        """
        Enhance card recognition using suit color information.
        
        Args:
            original_card: Card object from standard recognition (may be None)
            suit_color: Detected suit color ('red' or 'black')
            card_img: Original card image
            debug: Whether to save debug images
            
        Returns:
            Enhanced Card object or None if enhancement failed
        """
        # Map color to possible suits
        possible_suits = []
        if suit_color == 'red':
            possible_suits = ['h', 'd']  # hearts, diamonds
        elif suit_color == 'black':
            possible_suits = ['c', 's']  # clubs, spades
        
        # If we have a card from standard recognition
        if original_card:
            # Check if the suit matches the detected color
            if ((suit_color == 'red' and original_card.suit in ['h', 'd']) or
                (suit_color == 'black' and original_card.suit in ['c', 's'])):
                # Suit already matches color, but boost confidence
                enhanced_card = Card(
                    rank=original_card.rank,
                    suit=original_card.suit,
                    confidence=min(original_card.confidence + 0.1, 1.0)
                )
                self.logger.debug(f"Boosted confidence for matching color: {enhanced_card}")
                return enhanced_card
            else:
                # Suit doesn't match color, try to correct it
                self.logger.debug(f"Suit mismatch: card shows {original_card.suit} but color is {suit_color}")
                
                # Try to find a matching suit based on color
                if suit_color == 'red' and original_card.suit in ['c', 's']:
                    # Try to guess the correct red suit based on similarity
                    if original_card.suit == 'c':
                        # Clubs are visually similar to hearts
                        new_suit = 'h'
                    else:
                        # Spades are visually similar to diamonds
                        new_suit = 'd'
                    
                    enhanced_card = Card(
                        rank=original_card.rank,
                        suit=new_suit,
                        confidence=original_card.confidence * 0.9  # Reduce confidence for the correction
                    )
                    self.logger.debug(f"Corrected suit based on color: {enhanced_card}")
                    return enhanced_card
                
                elif suit_color == 'black' and original_card.suit in ['h', 'd']:
                    # Try to guess the correct black suit based on similarity
                    if original_card.suit == 'h':
                        # Hearts are visually similar to clubs
                        new_suit = 'c'
                    else:
                        # Diamonds are visually similar to spades
                        new_suit = 's'
                    
                    enhanced_card = Card(
                        rank=original_card.rank,
                        suit=new_suit,
                        confidence=original_card.confidence * 0.9  # Reduce confidence for the correction
                    )
                    self.logger.debug(f"Corrected suit based on color: {enhanced_card}")
                    return enhanced_card
        
        # If standard recognition completely failed, try OCR-based approach
        # combined with color information
        if original_card is None and hasattr(self, 'recognize_card_by_ocr'):
            try:
                ocr_card = self.recognize_card_by_ocr(card_img, debug)
                if ocr_card:
                    # If OCR detected a rank but the suit doesn't match color
                    if ocr_card.rank and ((suit_color == 'red' and ocr_card.suit not in ['h', 'd']) or
                                         (suit_color == 'black' and ocr_card.suit not in ['c', 's'])):
                        # Try to correct the suit based on color
                        if suit_color == 'red':
                            new_suit = 'h'  # Default to hearts for red
                        else:
                            new_suit = 's'  # Default to spades for black
                        
                        enhanced_card = Card(
                            rank=ocr_card.rank,
                            suit=new_suit,
                            confidence=ocr_card.confidence * 0.8  # Lower confidence for this guess
                        )
                        self.logger.debug(f"Created card from OCR rank and color: {enhanced_card}")
                        return enhanced_card
                    elif ocr_card.suit in possible_suits:
                        # OCR suit matches color, boost confidence
                        enhanced_card = Card(
                            rank=ocr_card.rank,
                            suit=ocr_card.suit,
                            confidence=min(ocr_card.confidence + 0.1, 1.0)
                        )
                        self.logger.debug(f"Boosted confidence for OCR with matching color: {enhanced_card}")
                        return enhanced_card
            except Exception as e:
                self.logger.error(f"Error in OCR enhancement: {e}")
        
        # If we still have no card, try a purely color-based approach
        if original_card is None:
            # This is a last resort with very low confidence
            # We'll try to detect the rank using just the template matching for ranks
            try:
                rank, rank_confidence = self._detect_rank_only(card_img)
                if rank and rank_confidence > 0.5:
                    # Pick the first suit from possible suits
                    suit = possible_suits[0] if possible_suits else 's'
                    
                    enhanced_card = Card(
                        rank=rank,
                        suit=suit,
                        confidence=rank_confidence * 0.6  # Low confidence for this method
                    )
                    self.logger.debug(f"Created card from rank detection and color: {enhanced_card}")
                    return enhanced_card
            except Exception as e:
                self.logger.error(f"Error in rank-only detection: {e}")
        
        # If all enhancement attempts failed, return None
        return None
    
    def _detect_rank_only(self, card_img):
        """
        Detect just the card rank using template matching on the corner of the card.
        
        Args:
            card_img: The card image
            
        Returns:
            Tuple of (rank, confidence) or (None, 0) if detection failed
        """
        if not self.template_loaded:
            self.load_template_images()
            
        if not self.template_loaded:
            return None, 0
            
        try:
            # Ensure we have a grayscale image
            if len(card_img.shape) == 3:
                gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = card_img
                
            # Standardize size
            standard_height = 200
            standard_width = int(standard_height * 0.7)  # Maintain aspect ratio
            resized = cv2.resize(gray, (standard_width, standard_height), interpolation=cv2.INTER_LINEAR)
            
            # Extract top-left corner for rank
            h, w = resized.shape
            corner = resized[0:int(h*0.25), 0:int(w*0.25)]
            
            # Match against rank templates
            best_rank = None
            best_confidence = 0
            
            for rank, template in self.rank_templates.items():
                if template is None or template.size == 0:
                    continue
                    
                # Resize template to match corner size if needed
                if template.shape != corner.shape:
                    template_resized = cv2.resize(template, (corner.shape[1], corner.shape[0]), 
                                                 interpolation=cv2.INTER_LINEAR)
                else:
                    template_resized = template
                    
                # Match template
                result = cv2.matchTemplate(corner, template_resized, cv2.TM_CCOEFF_NORMED)
                _, confidence, _, _ = cv2.minMaxLoc(result)
                
                if confidence > best_confidence:
                    best_rank = rank
                    best_confidence = confidence
            
            return best_rank, best_confidence
            
        except Exception as e:
            self.logger.error(f"Error in rank-only detection: {e}")
            return None, 0
    
    def _save_debug_image(self, card_img, card, method="standard"):
        """
        Save a debug image with recognition information.
        
        Args:
            card_img: The original card image
            card: The recognized Card object
            method: Recognition method used
        """
        try:
            if card_img is None or card is None:
                return
                
            # Make a copy of the image for drawing
            if len(card_img.shape) == 3:
                debug_img = card_img.copy()
            else:
                debug_img = cv2.cvtColor(card_img, cv2.COLOR_GRAY2BGR)
                
            # Add text with card info
            text = f"{card.rank}{card.suit} ({card.confidence:.2f})"
            cv2.putText(debug_img, text, (10, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add method used
            cv2.putText(debug_img, method, (10, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
            # Save the image
            timestamp = int(time.time())
            filename = f"{self.debug_dir}/card_{card.rank}{card.suit}_{method}_{timestamp}.png"
            cv2.imwrite(filename, debug_img)
            
        except Exception as e:
            self.logger.error(f"Error saving debug image: {e}")
            
    def get_recognition_stats(self):
        """
        Get recognition performance statistics.
        
        Returns:
            Dict with recognition statistics
        """
        success_rate = 0
        standard_rate = 0
        enhanced_rate = 0
        
        if self.recognition_attempts > 0:
            success_rate = (self.template_match_success + self.color_enhanced_success) / self.recognition_attempts * 100
            standard_rate = self.template_match_success / self.recognition_attempts * 100
            enhanced_rate = self.color_enhanced_success / self.recognition_attempts * 100
            
        return {
            'attempts': self.recognition_attempts,
            'success_rate': success_rate,
            'standard_success_rate': standard_rate,
            'enhanced_success_rate': enhanced_rate,
            'standard_successes': self.template_match_success,
            'enhanced_successes': self.color_enhanced_success
        }
