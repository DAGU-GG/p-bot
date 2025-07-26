"""
Integration module for the improved card recognition system.

This module provides a simple interface to integrate the improved card
recognition system with the main poker bot.
"""

import logging
from pathlib import Path
import cv2
import numpy as np
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('card_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('card_integration')

class IntegratedCardRecognition:
    """
    Integrates the improved card recognition system with the poker bot
    while maintaining compatibility with the original system.
    """
    
    def __init__(self):
        """Initialize the integrated card recognition system."""
        try:
            # Import the improved recognizer
            from improved_card_recognition import ImprovedCardRecognizer
            self.improved_recognizer = ImprovedCardRecognizer()
            logger.info("Successfully initialized improved card recognition system")
            
            # Create cache for recognition results
            self.card_cache = {}
            self.cache_lifetime = 5.0  # Cache results for 5 seconds
            self.last_cards = []
            self.last_community_cards = []
            
        except ImportError as e:
            logger.error(f"Failed to import improved card recognizer: {e}")
            self.improved_recognizer = None
    
    def recognize_hero_cards(self, table_image, hero_regions):
        """
        Recognize hero cards from table image.
        
        Args:
            table_image: The full table screenshot
            hero_regions: Dictionary of hero card regions
            
        Returns:
            list: List of recognized hero cards
        """
        # Extract card images from regions
        card_images = []
        region_keys = []
        
        for region_name, region_data in hero_regions.items():
            if 'hero_card' not in region_name:
                continue
                
            # Extract coordinates
            x = int(region_data.get('x', 0))
            y = int(region_data.get('y', 0))
            w = int(region_data.get('width', 0))
            h = int(region_data.get('height', 0))
            
            # Skip invalid regions
            if x <= 0 or y <= 0 or w <= 0 or h <= 0:
                logger.warning(f"Skipping invalid region: {region_name} ({x}, {y}, {w}, {h})")
                continue
                
            # Extract card image from region
            try:
                card_img = table_image[y:y+h, x:x+w]
                card_images.append(card_img)
                region_keys.append(region_name)
            except Exception as e:
                logger.error(f"Error extracting region {region_name}: {e}")
        
        # No cards found
        if not card_images:
            logger.warning("No hero card regions found or all regions were invalid")
            return []
            
        # Recognize all cards
        recognition_results = self.improved_recognizer.recognize_multiple_cards(card_images, debug=True)
        
        # Process results
        hero_cards = []
        for result in recognition_results:
            if not result['is_empty'] and result['card_code'] != 'error':
                hero_cards.append(result['card_code'])
        
        # Check for consistency with previous results
        if self.last_cards:
            if set(hero_cards) == set(self.last_cards):
                # Same cards, no change needed
                logger.debug("Hero cards unchanged from last detection")
            else:
                # Cards changed, verify the change
                logger.info(f"Hero cards changed: {self.last_cards} -> {hero_cards}")
                
                # If only some cards changed or confidence is low, be cautious
                card_count = len(hero_cards)
                if card_count == 1 and len(self.last_cards) == 2:
                    # One card disappeared, likely misdetection
                    logger.warning("Only one hero card detected when previously had two - possible misdetection")
                    
                    # Keep both cards if they were detected recently
                    if time.time() - self.card_cache.get('last_full_detection', 0) < 3.0:
                        logger.info("Using cached hero cards due to possible misdetection")
                        hero_cards = self.last_cards
                
                # Update cache timestamp if we have the expected number of cards (typically 2)
                if card_count == 2:
                    self.card_cache['last_full_detection'] = time.time()
        
        # Update last cards
        self.last_cards = hero_cards
        
        return hero_cards
    
    def recognize_community_cards(self, table_image, community_regions):
        """
        Recognize community cards from table image.
        
        Args:
            table_image: The full table screenshot
            community_regions: Dictionary of community card regions
            
        Returns:
            list: List of recognized community cards
        """
        # Extract card images from regions
        card_images = []
        region_keys = []
        
        for region_name, region_data in community_regions.items():
            if 'community_card' not in region_name:
                continue
                
            # Extract coordinates
            x = int(region_data.get('x', 0))
            y = int(region_data.get('y', 0))
            w = int(region_data.get('width', 0))
            h = int(region_data.get('height', 0))
            
            # Skip invalid regions
            if x <= 0 or y <= 0 or w <= 0 or h <= 0:
                logger.warning(f"Skipping invalid community region: {region_name} ({x}, {y}, {w}, {h})")
                continue
                
            # Extract card image from region
            try:
                card_img = table_image[y:y+h, x:x+w]
                card_images.append(card_img)
                region_keys.append(region_name)
            except Exception as e:
                logger.error(f"Error extracting community region {region_name}: {e}")
        
        # No cards found
        if not card_images:
            logger.warning("No community card regions found or all regions were invalid")
            return []
            
        # Recognize all cards
        recognition_results = self.improved_recognizer.recognize_multiple_cards(card_images, debug=True)
        
        # Process results
        community_cards = []
        for i, result in enumerate(recognition_results):
            if not result['is_empty'] and result['card_code'] != 'error':
                community_cards.append(result['card_code'])
            else:
                # For community cards, we keep empty slots in the results
                # but represent them as None to maintain the correct positions
                community_cards.append(None)
        
        # Validate community card sequence (must follow poker rules)
        # Pre-flop: 0 cards
        # Flop: 3 cards
        # Turn: 4 cards
        # River: 5 cards
        non_empty_cards = [c for c in community_cards if c is not None]
        card_count = len(non_empty_cards)
        
        if card_count > 0 and card_count != 3 and card_count != 4 and card_count != 5:
            logger.warning(f"Invalid community card count: {card_count} (must be 0, 3, 4, or 5)")
            
            # Check if previous detection was valid
            if self.last_community_cards and len(self.last_community_cards) in (3, 4, 5):
                # Use previous valid detection
                logger.info("Using previous valid community card detection")
                community_cards = self.last_community_cards
        
        # Save last valid community cards
        if card_count in (0, 3, 4, 5):
            self.last_community_cards = community_cards
        
        return community_cards
    
    def get_card_name(self, card_code):
        """
        Get the full name of a card from its code.
        
        Args:
            card_code: Two-character card code (e.g., '2h', 'Td', 'Ac')
            
        Returns:
            str: Full card name (e.g., 'Two of Hearts', 'Ten of Diamonds')
        """
        if self.improved_recognizer:
            return self.improved_recognizer.verifier.get_card_name(card_code)
        else:
            # Fallback mapping if improved recognizer not available
            card_names = {
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
            return card_names.get(card_code, 'Unknown Card')

def create_card_integration():
    """
    Create and return an integrated card recognition system instance.
    
    Returns:
        IntegratedCardRecognition: Integrated card recognition system
    """
    try:
        integrated_system = IntegratedCardRecognition()
        logger.info("Successfully created integrated card recognition system")
        
        # Check if the integrated system is properly initialized
        if integrated_system.improved_recognizer is None:
            logger.error("Failed to initialize integrated card recognition system")
            return None
            
        # Log the four-color suit configuration
        logger.info("Four-color suit configuration: hearts (red), clubs (green), spades (black), diamonds (blue)")
        
        return integrated_system
    except Exception as e:
        logger.error(f"Error creating integrated card recognition system: {e}")
        return None

def integrate_with_poker_bot(bot):
    """
    Integrate improved card recognition with an existing poker bot.
    
    Args:
        bot: The poker bot instance
        
    Returns:
        bool: True if integration was successful
    """
    try:
        # Create integration
        integration = create_card_integration()
        
        # Store original methods for hero card recognition
        original_recognize_hero_cards = bot.card_recognizer.recognize_hero_cards
        
        # Override recognition methods
        def improved_recognize_hero_cards(table_image):
            """Improved hero card recognition."""
            hero_regions = bot.card_recognizer.card_regions
            hero_cards = integration.recognize_hero_cards(table_image, hero_regions)
            
            # Convert to original format expected by the poker bot
            result = []
            for card_code in hero_cards:
                card_name = integration.get_card_name(card_code)
                result.append(card_name)
            
            return result
        
        # Replace method
        bot.card_recognizer.recognize_hero_cards = improved_recognize_hero_cards
        
        # Handle community cards
        original_recognize_community_cards = bot.community_detector.detect_community_cards
        
        def improved_recognize_community_cards(table_image):
            """Improved community card recognition."""
            community_regions = bot.community_detector.community_card_regions
            community_cards = integration.recognize_community_cards(table_image, community_regions)
            
            # Convert to original format expected by the poker bot
            from src.community_card_detector import CommunityCards
            
            # Convert to Card objects or None
            from dataclasses import dataclass
            
            @dataclass
            class Card:
                name: str
                code: str
                
            card_objects = []
            for card_code in community_cards:
                if card_code is not None:
                    card_name = integration.get_card_name(card_code)
                    card_objects.append(Card(name=card_name, code=card_code))
                else:
                    card_objects.append(None)
            
            result = CommunityCards(cards=card_objects)
            return result
        
        # Replace method
        bot.community_detector.detect_community_cards = improved_recognize_community_cards
        
        logger.info("Successfully integrated improved card recognition with poker bot")
        return True
        
    except Exception as e:
        logger.error(f"Failed to integrate with poker bot: {e}")
        return False
