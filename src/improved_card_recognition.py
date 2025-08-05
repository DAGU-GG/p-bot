"""
Improved Card Recognition System
Enhanced wrapper for card recognition with multiple fallback methods
"""

import os
import sys
import logging
import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict

# Add paths for imports
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
sys.path.append(current_dir)
sys.path.append(project_root)

logger = logging.getLogger(__name__)

class ImprovedCardRecognition:
    """
    Improved card recognition system that wraps the enhanced OCR system
    and provides compatibility with existing bot interfaces
    """
    
    def __init__(self):
        """Initialize the improved card recognition system"""
        self.logger = logging.getLogger(__name__)
        self.card_regions = {}
        self.original_recognizer = None
        
        # Try to import enhanced systems
        try:
            from enhanced_ocr_recognition import EnhancedOCRCardRecognition
            self.enhanced_ocr = EnhancedOCRCardRecognition()
            self.logger.info("Enhanced OCR system loaded successfully")
        except ImportError as e:
            self.logger.error(f"Failed to import enhanced OCR system: {e}")
            self.enhanced_ocr = None
        
        # Try to import original card recognizer for fallback
        try:
            from card_recognizer import CardRecognizer
            self.original_recognizer = CardRecognizer()
            self.logger.info("Original card recognizer loaded as fallback")
        except ImportError as e:
            self.logger.warning(f"Original card recognizer not available: {e}")
    
    def set_card_regions(self, regions: Dict):
        """Set the card regions for recognition"""
        self.card_regions = regions
        if self.original_recognizer and hasattr(self.original_recognizer, 'set_card_regions'):
            self.original_recognizer.set_card_regions(regions)
    
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
            # Import HoleCards class
            try:
                from card_recognizer import HoleCards
            except ImportError:
                self.logger.error("Cannot import HoleCards class")
                # Create a simple HoleCards replacement
                class HoleCards:
                    def __init__(self):
                        self.cards = [None, None]
                        self.detection_confidence = 0.0
                    
                    def is_valid(self):
                        return all(card is not None for card in self.cards)
                    
                    def __str__(self):
                        return f"HoleCards({self.cards})"
            
            self.logger.info("IMPROVED SYSTEM: Recognizing hero hole cards")
            
            # Check if we have card regions
            if not self.card_regions:
                self.logger.warning("No card regions defined - cannot recognize hole cards")
                return HoleCards()
            
            # Extract card images using the regions
            height, width = table_image.shape[:2]
            self.logger.info(f"Processing table image: {width}x{height}")
            
            hole_cards = HoleCards()
            
            # Extract and recognize each card
            for i, region_key in enumerate(['hero_card1', 'hero_card2']):
                if region_key in self.card_regions and i < 2:
                    region = self.card_regions[region_key]
                    
                    # Extract card region
                    x, y, w, h = region
                    card_img = table_image[y:y+h, x:x+w]
                    
                    if card_img.size == 0:
                        self.logger.warning(f"Empty card image for {region_key}")
                        continue
                    
                    # Recognize the card using enhanced methods
                    card = self._recognize_single_card(card_img, debug)
                    if card:
                        hole_cards.cards[i] = card
                        self.logger.info(f"Recognized {region_key}: {card}")
            
            # Set confidence based on how many cards were recognized
            valid_cards = sum(1 for card in hole_cards.cards if card is not None)
            hole_cards.detection_confidence = valid_cards / 2.0
            
            self.logger.info(f"IMPROVED SYSTEM: Final hole cards: {hole_cards} (confidence: {hole_cards.detection_confidence:.3f})")
            return hole_cards
            
        except Exception as e:
            self.logger.error(f"Error in recognize_hero_hole_cards: {e}", exc_info=True)
            return HoleCards()
    
    def _recognize_single_card(self, card_img, debug=False):
        """Recognize a single card using multiple methods"""
        if card_img is None or card_img.size == 0:
            return None
        
        # Try enhanced OCR first
        if self.enhanced_ocr:
            try:
                result = self.enhanced_ocr.recognize_card(card_img, debug=debug)
                if result and result.confidence > 0.3:
                    # Convert to card object format
                    class Card:
                        def __init__(self, rank, suit, confidence=1.0):
                            self.rank = rank
                            self.suit = suit
                            self.confidence = confidence
                        
                        def __str__(self):
                            return f"{self.rank}{self.suit}"
                    
                    return Card(result.rank, result.suit, result.confidence)
            except Exception as e:
                self.logger.error(f"Enhanced OCR recognition failed: {e}")
        
        # Fallback to original recognizer
        if self.original_recognizer:
            try:
                # Try template matching first
                card = self.original_recognizer.recognize_card_by_template_matching(card_img, debug)
                if card and hasattr(card, 'rank') and hasattr(card, 'suit'):
                    return card
                
                # Try OCR as final fallback
                card = self.original_recognizer.recognize_card_by_ocr(card_img)
                if card and hasattr(card, 'rank') and hasattr(card, 'suit'):
                    return card
            except Exception as e:
                self.logger.error(f"Original recognizer fallback failed: {e}")
        
        return None
    
    def recognize_card_by_template_matching(self, card_img, debug=False):
        """
        Recognize a single card image using template matching.
        This method provides compatibility with CommunityCardDetector.
        """
        if not hasattr(self, 'original_recognizer') or self.original_recognizer is None:
            self.logger.warning("No original recognizer available for template matching")
            return None
        
        return self.original_recognizer.recognize_card_by_template_matching(card_img, debug=debug)
    
    def recognize_card_by_ocr(self, card_img):
        """
        Recognize a single card image using OCR.
        This method provides compatibility with CommunityCardDetector.
        """
        if not hasattr(self, 'original_recognizer') or self.original_recognizer is None:
            self.logger.warning("No original recognizer available for OCR")
            return None
        
        return self.original_recognizer.recognize_card_by_ocr(card_img)

# For backward compatibility
def create_improved_recognizer():
    """Factory function to create an improved card recognizer"""
    return ImprovedCardRecognition()

if __name__ == "__main__":
    # Test the improved recognition system
    recognizer = ImprovedCardRecognition()
    print("✅ Improved card recognition system initialized successfully!")