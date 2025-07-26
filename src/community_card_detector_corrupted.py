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
import time
from card_recognizer import Card, CardRecognizer

@dataclass
class CommunityCards:
    """Represents the community cards on the table."""
        
        # Load regions from saved configuration using RegionLoader
        from region_loader import RegionLoader
        self.region_loader = RegionLoader()
        self.community_card_regions = self.region_loader.get_community_card_regions()
        
        # Log what regions we loaded with exact coordinates
        if self.community_card_regions:
            self.logger.info(f"✅ CommunityCardDetector loaded {len(self.community_card_regions)} saved community card regions:")
            for name, region in self.community_card_regions.items():
                self.logger.info(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}, "
                               f"w={region['width_percent']:.4f}, h={region['height_percent']:.4f}")
        else:
            # Fallback to defaults only if no saved regions exist
            self.community_card_regions = self._define_community_card_regions()
            self.logger.warning("⚠️ No saved community card regions found, using defaults")tion and recognition of community cards (flop, turn, river)
from PokerStars 9-player table screenshots with progressive revelation support.
"""

import cv2
import numpy as np
import os
import time
import logging
from typing import List, Dict, Tuple, Optional, Any
from region_loader import RegionLoader
from dataclasses import dataclass
import time
from card_recognizer import Card, CardRecognizer

@dataclass
class CommunityCards:
    """Represents the community cards on the table."""
    cards: List[Optional[Card]]
    count: int
    phase: str  # 'pre-flop', 'flop', 'turn', 'river'
    detection_confidence: float = 0.0
    timestamp: float = 0.0
    
    def __post_init__(self):
        # Ensure cards list has exactly 5 slots
        while len(self.cards) < 5:
            self.cards.append(None)
        self.cards = self.cards[:5]  # Trim to exactly 5
    
    def get_phase(self) -> str:
        """Determine game phase based on number of cards."""
        if self.count == 0:
            return 'pre-flop'
        elif self.count == 3:
            return 'flop'
        elif self.count == 4:
            return 'turn'
        elif self.count == 5:
            return 'river'
        else:
            return f'unknown-{self.count}'
    
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
        self.card_presence_threshold = 50  # Minimum variance to detect card presence
        self.recognition_confidence_threshold = 0.6
        
        # Load regions from saved configuration
        self.region_loader = RegionLoader()
        self.community_card_regions = self.region_loader.get_community_card_regions()
        
        # If no saved regions, use defaults
        if not self.community_card_regions:
            self.community_card_regions = self._define_community_card_regions()
            self.logger.info("Using default community card regions")
        else:
            self.logger.info(f"Loaded {len(self.community_card_regions)} saved community card regions")
        
        # Table background detection settings
        self.table_color_ranges = self._define_table_color_ranges()
        
        # Create debug directory
        os.makedirs("debug_community", exist_ok=True)
        
        self.logger.info("Community card detector initialized for 9-player PokerStars tables")
    
    def update_regions(self, new_regions: Dict[str, Dict]):
        """Update community card regions dynamically."""
        self.community_card_regions = new_regions
        self.logger.info(f"Updated community card regions: {len(new_regions)} regions loaded")
    
    def _define_community_card_regions(self) -> Dict[str, Dict]:
        """Define precise community card regions based on actual table layout."""
        return {
            'card_1': {  # First community card (leftmost)
                'x_percent': 0.335,
                'y_percent': 0.35,  # Moved up significantly
                'width_percent': 0.06,
                'height_percent': 0.08  # Reduced height for top-half cards
            },
            'card_2': {  # Second community card
                'x_percent': 0.405,
                'y_percent': 0.35,  # Moved up significantly
                'width_percent': 0.06,
                'height_percent': 0.08  # Reduced height for top-half cards
            },
            'card_3': {  # Third community card
                'x_percent': 0.475,
                'y_percent': 0.35,  # Moved up significantly
                'width_percent': 0.06,
                'height_percent': 0.08  # Reduced height for top-half cards
            },
            'card_4': {  # Fourth community card (turn)
                'x_percent': 0.545,
                'y_percent': 0.35,  # Moved up significantly
                'width_percent': 0.06,
                'height_percent': 0.08  # Reduced height for top-half cards
            },
            'card_5': {  # Fifth community card (river)
                'x_percent': 0.615,
                'y_percent': 0.35,  # Moved up significantly
                'width_percent': 0.06,
                'height_percent': 0.08  # Reduced height for top-half cards
            }
        }
    
    def _define_table_color_ranges(self) -> Dict[str, Tuple]:
        """Define color ranges for different PokerStars table themes."""
        return {
            'green_classic': {
                'lower': np.array([35, 40, 40]),   # Lower HSV bound for green table
                'upper': np.array([85, 255, 255])  # Upper HSV bound for green table
            },
            'blue_modern': {
                'lower': np.array([100, 50, 50]),  # Lower HSV bound for blue table
                'upper': np.array([130, 255, 255]) # Upper HSV bound for blue table
            },
            'red_classic': {
                'lower': np.array([0, 50, 50]),    # Lower HSV bound for red table
                'upper': np.array([20, 255, 255])  # Upper HSV bound for red table
            }
        }
    
    def extract_community_card_regions(self, table_image: np.ndarray) -> List[np.ndarray]:
        """Extract all 5 community card regions from the table image."""
        try:
            height, width = table_image.shape[:2]
            card_regions = []
            
            for i in range(1, 6):  # Cards 1-5
                region_key = f'card_{i}'
                region_def = self.community_card_regions[region_key]
                
                # Calculate pixel coordinates
                x = int(width * region_def['x_percent'])
                y = int(height * region_def['y_percent'])
                w = int(width * region_def['width_percent'])
                h = int(height * region_def['height_percent'])
                
                # Extract region
                card_region = table_image[y:y+h, x:x+w]
                card_regions.append(card_region.copy())
            
            return card_regions
            
        except Exception as e:
            self.logger.error(f"Error extracting community card regions: {e}")
            return [np.array([]) for _ in range(5)]
    
    def detect_card_presence(self, card_region: np.ndarray) -> bool:
        """
        Detect if a card is present in the given region.
        Uses variance analysis and color detection to distinguish cards from table background.
        """
        try:
            if card_region.size == 0:
                return False
            
            # Convert to grayscale for variance analysis
            if len(card_region.shape) == 3:
                gray_region = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
            else:
                gray_region = card_region
            
            # Method 1: Variance analysis
            # Cards have more detail/variance than plain table background
            variance = np.var(gray_region)
            variance_indicates_card = variance > self.card_presence_threshold
            
            # Method 2: Color analysis
            # Check if region contains non-table colors (indicating a card)
            color_indicates_card = self._detect_non_table_colors(card_region)
            
            # Method 3: Edge detection
            # Cards have more edges than plain table background
            edges = cv2.Canny(gray_region, 50, 150)
            edge_count = np.sum(edges > 0)
            edge_indicates_card = edge_count > 100  # Threshold for card edges
            
            # Combine methods (at least 2 out of 3 must agree)
            indicators = [variance_indicates_card, color_indicates_card, edge_indicates_card]
            card_present = sum(indicators) >= 2
            
            self.logger.debug(f"Card presence detection - Variance: {variance:.1f} "
                            f"({'✓' if variance_indicates_card else '✗'}), "
                            f"Color: {'✓' if color_indicates_card else '✗'}, "
                            f"Edges: {edge_count} ({'✓' if edge_indicates_card else '✗'}) "
                            f"-> {'CARD' if card_present else 'EMPTY'}")
            
            return card_present
            
        except Exception as e:
            self.logger.error(f"Error detecting card presence: {e}")
            return False
    
    def _detect_non_table_colors(self, card_region: np.ndarray) -> bool:
        """Detect if the region contains colors that are not typical table background."""
        try:
            if len(card_region.shape) != 3:
                return False
            
            # Convert to HSV for better color analysis
            hsv_region = cv2.cvtColor(card_region, cv2.COLOR_BGR2HSV)
            
            # Check against known table color ranges
            table_pixels = 0
            total_pixels = hsv_region.shape[0] * hsv_region.shape[1]
            
            for theme_name, color_range in self.table_color_ranges.items():
                # Create mask for this table color
                mask = cv2.inRange(hsv_region, color_range['lower'], color_range['upper'])
                table_pixels = max(table_pixels, np.sum(mask > 0))
            
            # If less than 70% of pixels are table color, likely contains a card
            table_percentage = table_pixels / total_pixels
            non_table_detected = table_percentage < 0.7
            
            return non_table_detected
            
        except Exception as e:
            self.logger.error(f"Error in color detection: {e}")
            return False
    
    def preprocess_community_card_image(self, card_region: np.ndarray) -> Dict[str, np.ndarray]:
        """Preprocess community card image for better recognition."""
        try:
            if card_region.size == 0:
                return {}
            
            processed = {}
            
            # Original image
            processed['original'] = card_region.copy()
            
            # Convert to grayscale
            if len(card_region.shape) == 3:
                gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
            else:
                gray = card_region.copy()
            
            processed['grayscale'] = gray
            
            # Enhance contrast for better card recognition
            processed['enhanced'] = cv2.equalizeHist(gray)
            
            # Apply Gaussian blur to reduce noise
            processed['blurred'] = cv2.GaussianBlur(processed['enhanced'], (3, 3), 0)
            
            # Binary threshold for clear card features
            _, processed['binary'] = cv2.threshold(processed['blurred'], 0, 255, 
                                                 cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Edge detection for card outline
            processed['edges'] = cv2.Canny(processed['enhanced'], 50, 150)
            
            # Morphological operations to clean up the image
            kernel = np.ones((2, 2), np.uint8)
            processed['morphology'] = cv2.morphologyEx(processed['binary'], 
                                                     cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error preprocessing community card image: {e}")
            return {'original': card_region}
    
    def recognize_community_card(self, card_region: np.ndarray, card_position: int) -> Optional[Card]:
        """Recognize a single community card using the card recognizer."""
        try:
            if card_region.size == 0:
                return None
            
            # Save debug image
            timestamp = int(time.time())
            debug_path = f"debug_community/community_card_{card_position}_{timestamp}.png"
            cv2.imwrite(debug_path, card_region)
            
            # Preprocess the card image
            processed = self.preprocess_community_card_image(card_region)
            if not processed:
                return None
            
            # Use the card recognizer's template matching
            card = self.card_recognizer.recognize_card_by_template_matching(card_region)
            if card and card.confidence > self.recognition_confidence_threshold:
                self.logger.debug(f"Community card {card_position} recognized via template: {card}")
                return card
            
            # Fallback to OCR
            ocr_card = self.card_recognizer.recognize_card_by_ocr(card_region)
            if ocr_card:
                self.logger.debug(f"Community card {card_position} recognized via OCR: {ocr_card}")
                return ocr_card
            
            # If template matching had a low-confidence result, return it anyway
            if card:
                self.logger.debug(f"Community card {card_position} low-confidence recognition: {card}")
                return card
            
            self.logger.debug(f"Community card {card_position} not recognized")
            return None
            
        except Exception as e:
            self.logger.error(f"Error recognizing community card {card_position}: {e}")
            return None
    
    def detect_community_cards(self, table_image: np.ndarray) -> CommunityCards:
        """
        Enhanced detection and recognition of all community cards from the table image.
        Handles progressive revelation (flop -> turn -> river) with better error handling.
        """
        try:
            timestamp = time.time()
            
            if table_image is None or table_image.size == 0:
                self.logger.error("Invalid table image provided")
                return CommunityCards(cards=[None]*5, count=0, phase='pre-flop')
            
            height, width = table_image.shape[:2]
            self.logger.debug(f"Processing table image: {width}x{height}")
            
            # Save debug image of full table
            debug_path = os.path.join("debug_community", f"full_table_{int(timestamp)}.png")
            cv2.imwrite(debug_path, table_image)
            
            # Extract all 5 community card regions with enhanced error handling
            card_regions = self.extract_community_card_regions(table_image)
            
            # Initialize result
            cards = [None] * 5
            detected_count = 0
            total_confidence = 0.0
            
            # Process each card slot with detailed debugging
            for i, card_region in enumerate(card_regions):
                card_position = i + 1
                
                try:
                    # Save debug image of card region
                    region_debug_path = os.path.join("debug_community", 
                                                   f"card_{card_position}_region_{int(timestamp)}.png")
                    if card_region is not None and card_region.size > 0:
                        cv2.imwrite(region_debug_path, card_region)
                    
                    # Enhanced card presence detection
                    is_present, presence_confidence = self.detect_card_presence_enhanced(card_region)
                    
                    if is_present:
                        self.logger.debug(f"Card {card_position} detected as present (confidence: {presence_confidence:.3f})")
                        
                        # Attempt to recognize the card with enhanced processing
                        recognized_card = self.recognize_community_card_enhanced(card_region, card_position)
                        
                        if recognized_card and recognized_card.confidence > self.recognition_confidence_threshold:
                            cards[i] = recognized_card
                            detected_count += 1
                            total_confidence += recognized_card.confidence
                            
                            self.logger.info(f"Community card {card_position}: {recognized_card} "
                                           f"(confidence: {recognized_card.confidence:.3f})")
                        else:
                            # Card present but not recognized - still count it
                            detected_count += 1
                            self.logger.warning(f"Community card {card_position}: present but not recognized reliably")
                    else:
                        self.logger.debug(f"Community card {card_position}: not present")
                        
                except Exception as e:
                    self.logger.error(f"Error processing community card {card_position}: {e}")
                    continue
            
            # Calculate average confidence
            avg_confidence = total_confidence / max(detected_count, 1)
            
            # Validate card count for proper poker phases
            if detected_count not in [0, 3, 4, 5]:
                self.logger.warning(f"Unusual community card count: {detected_count} (expected 0, 3, 4, or 5)")
            
            # Create result object
            community_cards = CommunityCards(
                cards=cards,
                count=detected_count,
                phase='',  # Will be set by get_phase()
                detection_confidence=avg_confidence,
                timestamp=timestamp
            )
            
            # Set the phase based on card count
            community_cards.phase = community_cards.get_phase()
            
            # Log results
            if detected_count > 0:
                visible_cards = [f"{card.rank}{card.suit}" for card in cards if card is not None]
                self.logger.info(f"Community Cards ({community_cards.phase}): {visible_cards} "
                               f"(avg confidence: {avg_confidence:.3f})")
            else:
                self.logger.info("No community cards detected (Pre-flop)")
            
            return community_cards
            
        except Exception as e:
            self.logger.error(f"Error detecting community cards: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return CommunityCards(cards=[None]*5, count=0, phase='pre-flop')
    
    def detect_card_presence_enhanced(self, card_region: np.ndarray) -> Tuple[bool, float]:
        """Enhanced card presence detection with confidence score."""
        try:
            if card_region is None or card_region.size == 0:
                return False, 0.0
            
            # Convert to grayscale if needed
            if len(card_region.shape) == 3:
                gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
            else:
                gray = card_region.copy()
            
            # Multiple presence detection methods
            
            # Method 1: Variance detection (high variance indicates card presence)
            variance = np.var(gray)
            variance_score = min(variance / 1000.0, 1.0)  # Normalize
            
            # Method 2: Edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            edge_score = min(edge_density * 10, 1.0)  # Normalize
            
            # Method 3: Histogram analysis (cards have different distribution than table)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_variance = np.var(hist)
            hist_score = min(hist_variance / 100000.0, 1.0)  # Normalize
            
            # Method 4: Mean brightness analysis
            mean_brightness = np.mean(gray)
            # Cards are typically brighter than the table
            brightness_score = 1.0 if 80 < mean_brightness < 200 else 0.3
            
            # Combine scores with weights
            combined_score = (
                variance_score * 0.4 +
                edge_score * 0.3 +
                hist_score * 0.2 +
                brightness_score * 0.1
            )
            
            # Determine presence
            is_present = combined_score > 0.5
            
            return is_present, combined_score
            
        except Exception as e:
            self.logger.error(f"Error in enhanced presence detection: {e}")
            return False, 0.0
    
    def recognize_community_card_enhanced(self, card_region: np.ndarray, position: int) -> Optional[Card]:
        """Enhanced community card recognition with better preprocessing."""
        try:
            if card_region is None or card_region.size == 0:
                return None
            
            # Use the card recognizer's enhanced template matching
            recognized_card = self.card_recognizer.recognize_card_by_template_matching(card_region)
            
            if recognized_card:
                # Save debug image of successful recognition
                debug_path = os.path.join("debug_community", 
                                        f"recognized_card_{position}_{recognized_card.rank}{recognized_card.suit}.png")
                cv2.imwrite(debug_path, card_region)
                
                return recognized_card
            
            # If template matching fails, try OCR as fallback
            ocr_card = self.card_recognizer.recognize_card_by_ocr(card_region)
            if ocr_card and ocr_card.confidence > 0.4:  # Lower threshold for OCR
                return ocr_card
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error recognizing community card at position {position}: {e}")
            return None
    
    def _save_community_debug(self, table_image: np.ndarray, community_cards: CommunityCards, 
                            card_regions: List[np.ndarray]) -> None:
        """Save debug visualization of community card detection."""
        try:
            # Create debug visualization
            debug_image = table_image.copy()
            height, width = debug_image.shape[:2]
            
            # Draw rectangles around each community card region
            colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
            
            for i in range(5):
                region_def = self.community_card_regions[f'card_{i+1}']
                
                # Calculate coordinates
                x = int(width * region_def['x_percent'])
                y = int(height * region_def['y_percent'])
                w = int(width * region_def['width_percent'])
                h = int(height * region_def['height_percent'])
                
                # Choose color based on card presence
                color = colors[i] if community_cards.cards[i] else (128, 128, 128)
                
                # Draw rectangle
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), color, 2)
                
                # Add label
                label = str(community_cards.cards[i]) if community_cards.cards[i] else "Empty"
                cv2.putText(debug_image, f"C{i+1}: {label}", (x, y - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Add overall info
            info_text = [
                f"Phase: {community_cards.phase}",
                f"Cards: {community_cards.count}/5",
                f"Confidence: {community_cards.detection_confidence:.3f}",
                f"Valid: {community_cards.is_valid_phase()}"
            ]
            
            for i, text in enumerate(info_text):
                cv2.putText(debug_image, text, (10, 30 + i * 20), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Save debug image
            timestamp = int(time.time())
            filename = f"debug_community/community_analysis_{timestamp}.png"
            cv2.imwrite(filename, debug_image)
            
        except Exception as e:
            self.logger.error(f"Error saving community debug: {e}")
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get statistics about community card detection performance."""
        return {
            'regions_defined': len(self.community_card_regions),
            'presence_threshold': self.card_presence_threshold,
            'recognition_threshold': self.recognition_confidence_threshold,
            'table_themes_supported': len(self.table_color_ranges),
            'supported_phases': ['pre-flop', 'flop', 'turn', 'river']
        }