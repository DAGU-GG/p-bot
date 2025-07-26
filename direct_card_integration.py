"""
Integration module for direct card recognition.

This module provides a simple interface to integrate the direct card
recognition system with the main poker bot.
"""

from direct_card_recognition import DirectCardRecognition, CardVerifier
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("direct_card_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("direct_card_integration")

class DirectCardIntegration:
    """
    Integration class for the direct card recognition system.
    
    This class provides a compatible interface for the poker bot to use
    the direct card recognition system.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the direct card integration.
        
        Args:
            config_path (str, optional): Path to config file. Defaults to None.
        """
        self.recognizer = DirectCardRecognition(config_path)
        self.verifier = CardVerifier()
        self.confidence_threshold = 0.7  # Minimum confidence to accept a card
        
        # Load configuration if available
        if config_path and os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'confidence_threshold' in config:
                        self.confidence_threshold = config['confidence_threshold']
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        logger.info("Successfully initialized direct card recognition system")
    
    def recognize_cards(self, image_paths):
        """
        Recognize multiple cards from a list of image paths.
        
        Args:
            image_paths (list): List of image paths
            
        Returns:
            list: List of recognized card codes
        """
        recognized_cards = []
        
        # Reset card history to prevent false duplicates
        self.recognizer.clear_card_history()
        self.verifier.reset()
        
        for path in image_paths:
            card, confidence = self.recognizer.recognize_card_from_image(path)
            
            # Only accept cards with sufficient confidence
            if confidence >= self.confidence_threshold:
                recognized_cards.append(card)
            else:
                logger.warning(f"Low confidence ({confidence:.2f}) for card {card} at {path}")
                recognized_cards.append("empty")
        
        # Verify cards to avoid duplicates
        is_valid, valid_cards = self.verifier.verify_cards(recognized_cards)
        
        if not is_valid:
            logger.warning("Duplicate cards detected and removed")
        
        return valid_cards
    
    def recognize_hero_cards(self, image_paths):
        """
        Recognize hero cards (hole cards).
        
        Args:
            image_paths (list): List of image paths for hero cards
            
        Returns:
            list: List of recognized hero card codes
        """
        # Reset for a new hand
        self.recognizer.clear_card_history()
        self.verifier.reset()
        
        return self.recognize_cards(image_paths)
    
    def recognize_community_cards(self, image_paths):
        """
        Recognize community cards.
        
        Args:
            image_paths (list): List of image paths for community cards
            
        Returns:
            list: List of recognized community card codes
        """
        return self.recognize_cards(image_paths)
    
    def reset(self):
        """
        Reset the recognition system for a new hand.
        """
        self.recognizer.clear_card_history()
        self.verifier.reset()
        logger.info("Recognition system reset")

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python direct_card_integration.py <image_path1> [<image_path2> ...]")
        sys.exit(1)
    
    image_paths = sys.argv[1:]
    integration = DirectCardIntegration()
    
    cards = integration.recognize_cards(image_paths)
    print(f"Recognized cards: {cards}")
