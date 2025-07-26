"""
PokerStars Bot - Stage 4: Community Card Detection System
This module handles detection and recognition of community cards on the poker table.
"""

import cv2
import numpy as np
import logging
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Any
import json
from enum import Enum
from card_recognizer import Card, CardRecognizer

@dataclass
class CommunityCards:
    """Represents the community cards on the table."""
    cards: List[Optional[Card]]
    detection_confidence: float = 0.0
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    @property
    def count(self) -> int:
        """Number of visible community cards."""
        return len([card for card in self.cards if card is not None])
    
    def get_phase(self) -> str:
        """Get the current phase name based on card count."""
        count = self.count
        if count == 0:
            return "pre-flop"
        elif count == 3:
            return "flop"
        elif count == 4:
            return "turn"
        elif count == 5:
            return "river"
        else:
            return "unknown"
    
    def get_visible_cards(self) -> List[Card]:
        """Get only the visible (non-None) cards."""
        return [card for card in self.cards if card is not None]
    
    def is_valid_phase(self) -> bool:
        """Check if the current card count represents a valid poker phase."""
        return self.count in [0, 3, 4, 5]
    
    def __str__(self):
        visible = self.get_visible_cards()
        if not visible:
            return "No community cards (Pre-flop)"
        
        phase_name = self.get_phase().title()
        cards_str = ", ".join(str(card) for card in visible)
        return f"{phase_name}: {cards_str}"


class CommunityCardDetector:
    """
    Handles detection and recognition of community cards from PokerStars table screenshots.
    Supports progressive revelation (flop -> turn -> river) and various table themes.
    """
    
    def __init__(self, card_recognizer: CardRecognizer):
        """Initialize the community card detector."""
        self.logger = logging.getLogger(__name__)
        self.card_recognizer = card_recognizer
        
        # Community card detection settings
        self.card_presence_threshold = 30  # Lower minimum variance threshold for better detection
        self.recognition_confidence_threshold = 0.6
        
        # Load regions from saved configuration using RegionLoader
        from region_loader import RegionLoader
        self.region_loader = RegionLoader()
        self.community_card_regions = self.region_loader.get_community_card_regions()
        
        # Log what regions we loaded with exact coordinates
        if self.community_card_regions:
            self.logger.info(f"CommunityCardDetector loaded {len(self.community_card_regions)} saved community card regions:")
            for name, region in self.community_card_regions.items():
                self.logger.info(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}, "
                               f"w={region['width_percent']:.4f}, h={region['height_percent']:.4f}")
        else:
            # Fallback to defaults only if no saved regions exist
            self.community_card_regions = self._define_community_card_regions()
            self.logger.warning("⚠️ No saved community card regions found, using defaults")
        
        # Detection state
        self.last_community_cards = []
        self.last_detection_time = 0
        self.detection_cooldown = 0.5  # seconds
    
    def update_regions(self, new_regions: Dict[str, Dict]):
        """Update community card regions dynamically."""
        try:
            self.community_card_regions = new_regions
            self.logger.info(f"[SUCCESS] Updated community card regions: {len(new_regions)} regions")
            for name, region in new_regions.items():
                self.logger.debug(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        except Exception as e:
            self.logger.error(f"Error updating community card regions: {e}")
    
    def _define_community_card_regions(self) -> Dict[str, Dict]:
        """This method is deprecated - regions should only come from RegionLoader."""
        self.logger.warning("❌ Using hardcoded fallback regions - Please calibrate regions!")
        return {}  # Return empty - no more hardcoded regions
    
    def extract_card_region(self, table_image: np.ndarray, region: Dict[str, float], 
                           card_name: str = "unknown") -> Optional[np.ndarray]:
        """Extract a card region from the table image."""
        try:
            height, width = table_image.shape[:2]
            
            # Convert percentage coordinates to pixels
            x = int(region['x_percent'] * width)
            y = int(region['y_percent'] * height)
            w = int(region['width_percent'] * width)
            h = int(region['height_percent'] * height)
            
            # Ensure coordinates are within bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            # Extract the card region
            card_img = table_image[y:y+h, x:x+w].copy()
            
            # Log extraction details
            self.logger.debug(f"Extracted {card_name}: region ({x},{y},{w},{h}) -> image shape {card_img.shape}")
            
            # Save debug image
            timestamp = int(time.time() * 1000)
            debug_filename = f"debug_community/{card_name}_{timestamp}.png"
            os.makedirs("debug_community", exist_ok=True)
            cv2.imwrite(debug_filename, card_img)
            
            return card_img
            
        except Exception as e:
            self.logger.error(f"Error extracting card region {card_name}: {e}")
            return None
    
    def detect_community_cards(self, table_image: np.ndarray, debug=False) -> CommunityCards:
        """
        Detect and recognize community cards from a table screenshot.
        """
        try:
            # Check detection cooldown
            current_time = time.time()
            if current_time - self.last_detection_time < self.detection_cooldown:
                if self.last_community_cards:
                    return self.last_community_cards
            
            if debug:
                self.logger.info("Starting community card detection with debug mode enabled")
                
            self.last_detection_time = current_time
            
            # Initialize card list (5 positions for flop, turn, river)
            cards = [None] * 5
            total_confidence = 0.0
            detected_count = 0
            
            # Process each community card position
            for i in range(1, 6):
                card_key = f'card_{i}'
                
                if card_key not in self.community_card_regions:
                    self.logger.warning(f"No region defined for {card_key}")
                    continue
                
                region = self.community_card_regions[card_key]
                
                # Extract card region
                card_img = self.extract_card_region(table_image, region, card_key)
                if card_img is None or card_img.size == 0:
                    continue
                
                # Check if a card is present (detect card-like pattern)
                if not self._is_card_present(card_img):
                    continue
                
                # Recognize the card
                if debug:
                    self.logger.debug(f"Recognizing community card {i}")
                card = self.card_recognizer.recognize_card_by_template_matching(card_img, debug=debug)
                
                if card:
                    cards[i-1] = card
                    total_confidence += 0.8  # Base confidence for template match
                    detected_count += 1
                    if debug:
                        self.logger.info(f"Community card {i}: {card}")
                    else:
                        self.logger.debug(f"Community card {i}: {card}")
                else:
                    # Try OCR as fallback
                    ocr_card = self.card_recognizer.recognize_card_by_ocr(card_img)
                    if ocr_card:
                        cards[i-1] = ocr_card
                        total_confidence += 0.6  # Lower confidence for OCR
                        detected_count += 1
                        self.logger.debug(f"Community card {i} (OCR): {ocr_card}")
            
            # Calculate overall confidence
            if detected_count > 0:
                avg_confidence = total_confidence / detected_count
            else:
                avg_confidence = 0.0
            
            # Create result
            community_cards = CommunityCards(
                cards=cards,
                detection_confidence=avg_confidence,
                timestamp=current_time
            )
            
            # Cache the result
            self.last_community_cards = community_cards
            
            # Log results
            if community_cards.count > 0:
                self.logger.info(f"Community Cards Detected: {community_cards} (confidence: {avg_confidence:.3f})")
            else:
                self.logger.debug("No community cards detected")
            
            return community_cards
            
        except Exception as e:
            self.logger.error(f"Error detecting community cards: {e}")
            import traceback
            traceback.print_exc()
            return CommunityCards(cards=[None] * 5, timestamp=time.time())
    
    def _is_card_present(self, card_img: np.ndarray) -> bool:
        """Improved check if the region contains a card using multiple methods."""
        try:
            if card_img is None or card_img.size == 0:
                return False
            
            # Convert to grayscale if needed
            if len(card_img.shape) == 3:
                gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
                bgr = card_img.copy()
            else:
                gray = card_img
                bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            # Method 1: Calculate variance - cards should have texture/patterns
            variance = np.var(gray)
            variance_check = variance > self.card_presence_threshold
            
            # Method 2: Color analysis - cards should have white/light areas (cards are mostly white)
            mean_value = np.mean(gray)
            color_check = mean_value > 100  # Cards have significant white/light areas
            
            # Method 3: Edge detection - cards have defined edges
            edges = cv2.Canny(gray, 50, 150)
            edge_count = np.count_nonzero(edges)
            edge_percentage = edge_count / (gray.shape[0] * gray.shape[1])
            edge_check = edge_percentage > 0.05  # At least 5% edges
            
            # Method 4: Check for card-like aspect ratio (should be roughly rectangular)
            height, width = gray.shape[:2]
            aspect = width / max(1, height)  # Avoid division by zero
            aspect_check = 0.6 <= aspect <= 0.9  # Most cards have aspect ratio in this range
            
            # Method 5: Color differentiation (cards have both dark and light areas)
            std_value = np.std(gray)
            contrast_check = std_value > 40  # Cards should have good contrast between elements
            
            # Method 6: Check for card corners (white background with edges)
            # Take small corner regions and check for white areas with some edges
            if height > 10 and width > 10:
                corners = [
                    gray[:int(height*0.2), :int(width*0.2)],  # Top-left
                    gray[:int(height*0.2), -int(width*0.2):],  # Top-right
                    gray[-int(height*0.2):, :int(width*0.2)],  # Bottom-left
                    gray[-int(height*0.2):, -int(width*0.2):]   # Bottom-right
                ]
                
                corner_scores = []
                for corner in corners:
                    if corner.size > 0:
                        corner_mean = np.mean(corner)
                        corner_scores.append(corner_mean > 150)  # Card corners are usually white
                
                corner_check = sum(corner_scores) >= 2  # At least 2 corners should be white
            else:
                corner_check = False
                
            # Combine methods - need at least 3 of 6 methods to agree
            # Weight the methods differently based on reliability
            methods = [
                (variance_check, 1),    # Variance is very reliable
                (color_check, 1),       # Mean value is reliable
                (edge_check, 1),        # Edge detection is reliable
                (aspect_check, 0.5),    # Aspect ratio is somewhat reliable
                (contrast_check, 0.5),  # Contrast is somewhat reliable
                (corner_check, 0.5)     # Corner detection is somewhat reliable
            ]
            
            weighted_sum = sum(value * weight for value, weight in methods)
            total_weight = sum(weight for _, weight in methods)
            confidence = weighted_sum / total_weight
            
            # Need at least 60% confidence to say a card is present
            is_present = confidence >= 0.6
            
            self.logger.debug(f"Card presence check: variance={variance:.2f} ({variance_check}), "
                            f"mean={mean_value:.1f} ({color_check}), "
                            f"edge%={edge_percentage*100:.1f}% ({edge_check}), "
                            f"aspect={aspect:.2f} ({aspect_check}), "
                            f"contrast={std_value:.1f} ({contrast_check}), "
                            f"corners={sum(corner_scores if 'corner_scores' in locals() else [])}/4 ({corner_check}), "
                            f"confidence={confidence:.2f}, result={is_present}")
            
            # Save debug image if configured
            timestamp = int(time.time() * 1000)
            debug_path = f"debug_community/presence_check_{timestamp}_{is_present}.png"
            cv2.imwrite(debug_path, card_img)
            
            return is_present
            
        except Exception as e:
            self.logger.error(f"Error checking card presence: {e}")
            return False
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get statistics about community card detection."""
        return {
            'regions_defined': len(self.community_card_regions),
            'presence_threshold': self.card_presence_threshold,
            'recognition_threshold': self.recognition_confidence_threshold,
            'last_detection_time': self.last_detection_time,
            'detection_cooldown': self.detection_cooldown
        }
