"""
PokerStars Bot - Advanced Table Analysis System
Enhanced module handles comprehensive automatic detection of all poker table elements
including hero position, stack sizes, blinds, dealer button, and converts to BB units.
"""

import cv2
import numpy as np
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from PIL import Image

# Optional pytesseract import
try:
    import pytesseract
    # Configure Tesseract path for Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available, OCR functionality may be limited")


@dataclass
class PlayerInfo:
    """Information about a player at the table."""
    seat_number: int
    name: str
    stack_size: float  # In BB units
    is_hero: bool = False
    is_active: bool = True
    current_bet: float = 0.0  # In BB units
    position: str = ""  # UTG, MP, CO, BTN, SB, BB


@dataclass
class TableInfo:
    """Complete table information."""
    players: List[PlayerInfo]
    hero_seat: int
    dealer_seat: int
    small_blind: float
    big_blind: float
    pot_size: float  # In BB units
    current_bet: float  # In BB units
    game_phase: str  # pre-flop, flop, turn, river
    table_stakes: str  # e.g., "NL25", "NL50"
    max_players: int = 9


class PokerTableAnalyzer:
    """
    Comprehensive poker table analyzer that automatically detects all table elements.
    Converts all monetary values to Big Blind (BB) units for strategic calculations.
    """
    
    def __init__(self):
        """Initialize the table analyzer."""
        self.logger = logging.getLogger(__name__)
        
        # Table layout for 9-max PokerStars
        self.seat_regions = self._define_seat_regions()
        self.enhanced_seat_regions = self._define_enhanced_seat_regions()
        self.ui_regions = self._define_ui_regions()
        self.enhanced_ui_regions = self._define_enhanced_ui_regions()
        
        # OCR configuration
        self.ocr_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.$,KMkm'
        
        # Cached values
        self.big_blind_value = None
        self.small_blind_value = None
        self.table_stakes = None
        
        self.logger.info("Poker table analyzer initialized")
    
    def _define_enhanced_seat_regions(self) -> Dict[int, Dict]:
        """Enhanced seat regions based on the actual PokerStars layout from the image."""
        return {
            1: {  # Bottom left (Rafatunte)
                'name': {'x_percent': 0.12, 'y_percent': 0.72, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.12, 'y_percent': 0.77, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.12, 'y_percent': 0.62, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            2: {  # Left middle (Allythump)
                'name': {'x_percent': 0.12, 'y_percent': 0.42, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.12, 'y_percent': 0.47, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.12, 'y_percent': 0.32, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            3: {  # Top left (DanielParis79)
                'name': {'x_percent': 0.28, 'y_percent': 0.12, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.28, 'y_percent': 0.17, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.28, 'y_percent': 0.02, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            4: {  # Top right (Check player)
                'name': {'x_percent': 0.57, 'y_percent': 0.12, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.57, 'y_percent': 0.17, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.57, 'y_percent': 0.02, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            5: {  # Right middle top (TopgunSmurf)
                'name': {'x_percent': 0.73, 'y_percent': 0.32, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.73, 'y_percent': 0.37, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.73, 'y_percent': 0.22, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            6: {  # Right middle (yhpwnthop)
                'name': {'x_percent': 0.73, 'y_percent': 0.52, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.73, 'y_percent': 0.57, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.73, 'y_percent': 0.42, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            7: {  # Right bottom (Kituzk)
                'name': {'x_percent': 0.73, 'y_percent': 0.72, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.73, 'y_percent': 0.77, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.73, 'y_percent': 0.62, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            8: {  # Bottom right (Oliver3313)
                'name': {'x_percent': 0.57, 'y_percent': 0.82, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.57, 'y_percent': 0.87, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.57, 'y_percent': 0.72, 'width_percent': 0.10, 'height_percent': 0.12},
            },
            9: {  # Bottom center (Tacamahaca - Hero position)
                'name': {'x_percent': 0.42, 'y_percent': 0.82, 'width_percent': 0.15, 'height_percent': 0.05},
                'stack': {'x_percent': 0.42, 'y_percent': 0.87, 'width_percent': 0.15, 'height_percent': 0.05},
                'cards': {'x_percent': 0.42, 'y_percent': 0.72, 'width_percent': 0.10, 'height_percent': 0.12},
            }
        }
    
    def _define_enhanced_ui_regions(self) -> Dict[str, Dict]:
        """Enhanced UI regions based on actual PokerStars layout."""
        return {
            'pot': {
                'x_percent': 0.43, 'y_percent': 0.42, 
                'width_percent': 0.14, 'height_percent': 0.06
            },
            'community_cards': {
                'x_percent': 0.35, 'y_percent': 0.48, 
                'width_percent': 0.30, 'height_percent': 0.15
            },
            'hero_cards': {
                'x_percent': 0.42, 'y_percent': 0.72, 
                'width_percent': 0.10, 'height_percent': 0.12
            },
            'table_info': {
                'x_percent': 0.02, 'y_percent': 0.02, 
                'width_percent': 0.25, 'height_percent': 0.08
            }
        }
    
    def _define_seat_regions(self) -> Dict[int, Dict]:
        """Define regions for each seat position (1-9) on PokerStars 9-max table."""
        return {
            1: {  # Hero seat (bottom center)
                'name': {'x_percent': 0.42, 'y_percent': 0.85, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.42, 'y_percent': 0.89, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.42, 'y_percent': 0.75, 'width_percent': 0.16, 'height_percent': 0.12},
                'bet': {'x_percent': 0.42, 'y_percent': 0.70, 'width_percent': 0.16, 'height_percent': 0.04}
            },
            2: {  # Left middle
                'name': {'x_percent': 0.15, 'y_percent': 0.65, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.15, 'y_percent': 0.69, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.15, 'y_percent': 0.55, 'width_percent': 0.16, 'height_percent': 0.10},
                'bet': {'x_percent': 0.25, 'y_percent': 0.60, 'width_percent': 0.12, 'height_percent': 0.04}
            },
            3: {  # Left top
                'name': {'x_percent': 0.15, 'y_percent': 0.25, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.15, 'y_percent': 0.29, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.15, 'y_percent': 0.15, 'width_percent': 0.16, 'height_percent': 0.10},
                'bet': {'x_percent': 0.25, 'y_percent': 0.35, 'width_percent': 0.12, 'height_percent': 0.04}
            },
            4: {  # Top left
                'name': {'x_percent': 0.35, 'y_percent': 0.10, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.35, 'y_percent': 0.14, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.35, 'y_percent': 0.05, 'width_percent': 0.16, 'height_percent': 0.08},
                'bet': {'x_percent': 0.35, 'y_percent': 0.20, 'width_percent': 0.12, 'height_percent': 0.04}
            },
            5: {  # Top center
                'name': {'x_percent': 0.42, 'y_percent': 0.05, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.42, 'y_percent': 0.09, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.42, 'y_percent': 0.02, 'width_percent': 0.16, 'height_percent': 0.06},
                'bet': {'x_percent': 0.42, 'y_percent': 0.15, 'width_percent': 0.12, 'height_percent': 0.04}
            },
            6: {  # Top right
                'name': {'x_percent': 0.49, 'y_percent': 0.10, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.49, 'y_percent': 0.14, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.49, 'y_percent': 0.05, 'width_percent': 0.16, 'height_percent': 0.08},
                'bet': {'x_percent': 0.53, 'y_percent': 0.20, 'width_percent': 0.12, 'height_percent': 0.04}
            },
            7: {  # Right top
                'name': {'x_percent': 0.69, 'y_percent': 0.25, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.69, 'y_percent': 0.29, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.69, 'y_percent': 0.15, 'width_percent': 0.16, 'height_percent': 0.10},
                'bet': {'x_percent': 0.63, 'y_percent': 0.35, 'width_percent': 0.12, 'height_percent': 0.04}
            },
            8: {  # Right middle
                'name': {'x_percent': 0.69, 'y_percent': 0.65, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.69, 'y_percent': 0.69, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.69, 'y_percent': 0.55, 'width_percent': 0.16, 'height_percent': 0.10},
                'bet': {'x_percent': 0.63, 'y_percent': 0.60, 'width_percent': 0.12, 'height_percent': 0.04}
            },
            9: {  # Right bottom (small blind typically)
                'name': {'x_percent': 0.55, 'y_percent': 0.80, 'width_percent': 0.16, 'height_percent': 0.04},
                'stack': {'x_percent': 0.55, 'y_percent': 0.84, 'width_percent': 0.16, 'height_percent': 0.04},
                'cards': {'x_percent': 0.55, 'y_percent': 0.70, 'width_percent': 0.16, 'height_percent': 0.10},
                'bet': {'x_percent': 0.55, 'y_percent': 0.75, 'width_percent': 0.12, 'height_percent': 0.04}
            }
        }
    
    def _define_ui_regions(self) -> Dict[str, Dict]:
        """Define regions for UI elements like pot, blinds, dealer button."""
        return {
            'pot': {
                'x_percent': 0.40, 'y_percent': 0.25, 
                'width_percent': 0.20, 'height_percent': 0.06
            },
            'dealer_button': {
                'x_percent': 0.20, 'y_percent': 0.20, 
                'width_percent': 0.60, 'height_percent': 0.60
            },
            'table_info': {  # Usually shows stakes like "NL25"
                'x_percent': 0.02, 'y_percent': 0.02, 
                'width_percent': 0.20, 'height_percent': 0.08
            },
            'community_cards': {
                'x_percent': 0.25, 'y_percent': 0.35, 
                'width_percent': 0.50, 'height_percent': 0.15
            }
        }
    
    def extract_text_from_region(self, image: np.ndarray, region: Dict) -> str:
        """Extract text from a specific region using OCR."""
        try:
            height, width = image.shape[:2]
            
            # Calculate pixel coordinates
            x = int(width * region['x_percent'])
            y = int(height * region['y_percent'])
            w = int(width * region['width_percent'])
            h = int(height * region['height_percent'])
            
            # Extract region
            roi = image[y:y+h, x:x+w]
            
            if roi.size == 0:
                return ""
            
            # Preprocess for OCR
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi
            
            # Enhance contrast
            enhanced = cv2.equalizeHist(gray)
            
            # Apply threshold
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Use OCR if available
            if PYTESSERACT_AVAILABLE:
                text = pytesseract.image_to_string(binary, config=self.ocr_config).strip()
                return text
            else:
                self.logger.debug("OCR (pytesseract) not available, returning empty text")
                return ""
            
        except Exception as e:
            self.logger.debug(f"Error extracting text from region: {e}")
            return ""
    
    def extract_text_with_enhanced_ocr(self, image: np.ndarray, region: Dict) -> str:
        """Enhanced text extraction with better preprocessing."""
        try:
            height, width = image.shape[:2]
            
            # Calculate pixel coordinates
            x = int(width * region['x_percent'])
            y = int(height * region['y_percent'])
            w = int(width * region['width_percent'])
            h = int(height * region['height_percent'])
            
            # Extract region
            roi = image[y:y+h, x:x+w]
            
            if roi.size == 0:
                return ""
            
            # Enhanced preprocessing
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi
            
            # Multiple preprocessing attempts
            results = []
            
            # Method 1: Standard processing
            enhanced = cv2.equalizeHist(gray)
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            if PYTESSERACT_AVAILABLE:
                text1 = pytesseract.image_to_string(binary, config=self.ocr_config).strip()
                if text1: results.append(text1)
                
                # Method 2: Inverted
                inverted = cv2.bitwise_not(binary)
                text2 = pytesseract.image_to_string(inverted, config=self.ocr_config).strip()
                if text2: results.append(text2)
            else:
                self.logger.debug("OCR (pytesseract) not available, stack/pot detection may be limited")
            
            # Return best result
            return max(results, key=len) if results else ""
            
        except Exception as e:
            self.logger.debug(f"Error in enhanced OCR: {e}")
            return ""
    
    def detect_table_stakes_from_window_title(self, window_title: str) -> Tuple[float, float, str]:
        """Detect stakes from window title or other sources."""
        try:
            # Extract stakes from "No Limit Hold'em 100/200 Play Money" format
            import re
            
            # Pattern for "100/200" format
            stakes_pattern = r'(\d+)/(\d+)'
            match = re.search(stakes_pattern, window_title)
            if match:
                sb = float(match.group(1)) / 100  # Convert from cents to dollars
                bb = float(match.group(2)) / 100
                stake_name = f"NL{int(bb*100)}"
                
                self.small_blind_value = sb
                self.big_blind_value = bb
                self.table_stakes = stake_name
                self.logger.info(f"Detected stakes from window: {stake_name} (SB: ${sb}, BB: ${bb})")
                return sb, bb, stake_name
            
            # Common PokerStars stake patterns in window titles
            stake_patterns = {
                'NL2': (0.01, 0.02), 'NL5': (0.02, 0.05), 'NL10': (0.05, 0.10),
                'NL25': (0.10, 0.25), 'NL50': (0.25, 0.50), 'NL100': (0.50, 1.00),
                'NL200': (1.00, 2.00), 'NL400': (2.00, 4.00), 'NL600': (3.00, 6.00),
                'NL1000': (5.00, 10.00)
            }
            
            # Check window title for stakes
            if window_title:
                title_upper = window_title.upper()
                for stake_name, (sb, bb) in stake_patterns.items():
                    if stake_name in title_upper:
                        self.small_blind_value = sb
                        self.big_blind_value = bb
                        self.table_stakes = stake_name
                        self.logger.info(f"Detected stakes from window title: {stake_name} (SB: ${sb}, BB: ${bb})")
                        return sb, bb, stake_name
            
            # Try to extract from "No Limit Hold'em $0.25/$0.50" format
            import re
            money_pattern = r'\$(\d+\.?\d*)/\$(\d+\.?\d*)'
            match = re.search(money_pattern, window_title) if window_title else None
            if match:
                sb = float(match.group(1))
                bb = float(match.group(2))
                stake_name = f"NL{int(bb*100)}"
                
                self.small_blind_value = sb
                self.big_blind_value = bb
                self.table_stakes = stake_name
                self.logger.info(f"Detected stakes from window format: {stake_name} (SB: ${sb}, BB: ${bb})")
                return sb, bb, stake_name
            
            # Try to extract from "100/200 Play Money" format
            play_money_pattern = r'(\d+)/(\d+)\s+Play\s+Money'
            match = re.search(play_money_pattern, window_title, re.IGNORECASE) if window_title else None
            if match:
                sb = float(match.group(1)) / 100  # Convert from cents
                bb = float(match.group(2)) / 100
                stake_name = f"NL{int(bb*100)}"
                
                self.small_blind_value = sb
                self.big_blind_value = bb
                self.table_stakes = stake_name
                self.logger.info(f"Detected play money stakes: {stake_name} (SB: ${sb}, BB: ${bb})")
                return sb, bb, stake_name
            
            return None, None, None
            
        except Exception as e:
            self.logger.error(f"Error detecting stakes from window title: {e}")
            return None, None, None
    
    def parse_monetary_value(self, text: str) -> float:
        """Parse monetary value from text and return as float."""
        try:
            if not text:
                return 0.0
            
            # Remove common prefixes/suffixes
            text = text.replace('$', '').replace(',', '').replace(' ', '')
            
            # Handle K/M suffixes
            multiplier = 1.0
            if text.endswith('K') or text.endswith('k'):
                multiplier = 1000.0
                text = text[:-1]
            elif text.endswith('M') or text.endswith('m'):
                multiplier = 1000000.0
                text = text[:-1]
            
            # Extract numeric value
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                value = float(match.group(1)) * multiplier
                return value
            
            return 0.0
            
        except Exception as e:
            self.logger.debug(f"Error parsing monetary value '{text}': {e}")
            return 0.0
    
    def detect_table_stakes(self, image: np.ndarray) -> Tuple[float, float, str]:
        """Detect table stakes and blind levels."""
        try:
            # First try to get from window title if available
            window_title = getattr(self, 'current_window_title', '')
            stakes_from_title = self.detect_table_stakes_from_window_title(window_title)
            if stakes_from_title[0] is not None:
                return stakes_from_title
            
            # Extract table info region
            table_info_text = self.extract_text_with_enhanced_ocr(image, self.enhanced_ui_regions['table_info'])
            if not table_info_text:
                table_info_text = self.extract_text_from_region(image, self.enhanced_ui_regions['table_info'])
            
            # Also try enhanced regions
            if not table_info_text:
                # Try window title or other sources
                pass
            
            # Common PokerStars stake patterns
            stake_patterns = {
                'NL2': (0.01, 0.02), 'NL5': (0.02, 0.05), 'NL10': (0.05, 0.10),
                'NL25': (0.10, 0.25), 'NL50': (0.25, 0.50), 'NL100': (0.50, 1.00),
                'NL200': (1.00, 2.00), 'NL400': (2.00, 4.00), 'NL600': (3.00, 6.00),
                'NL1000': (5.00, 10.00)
            }
            
            # Try to match stake pattern
            for stake_name, (sb, bb) in stake_patterns.items():
                if stake_name in table_info_text.upper():
                    self.small_blind_value = sb
                    self.big_blind_value = bb
                    self.table_stakes = stake_name
                    self.logger.info(f"Detected stakes: {stake_name} (SB: ${sb}, BB: ${bb})")
                    return sb, bb, stake_name
            
            # Fallback: try to detect from actual blind posts
            # This would require analyzing betting actions, which is more complex
            # For now, assume common stakes
            self.small_blind_value = 0.25
            self.big_blind_value = 0.50
            self.table_stakes = "NL50"
            
            self.logger.warning("Could not detect stakes, assuming NL50")
            return 0.25, 0.50, "NL50"
            
        except Exception as e:
            self.logger.error(f"Error detecting table stakes: {e}")
            return 0.25, 0.50, "NL50"
    
    def detect_dealer_button(self, image: np.ndarray) -> int:
        """Detect dealer button position and return seat number."""
        try:
            height, width = image.shape[:2]
            region = self.ui_regions['dealer_button']
            
            # Extract dealer button search area
            x = int(width * region['x_percent'])
            y = int(height * region['y_percent'])
            w = int(width * region['width_percent'])
            h = int(height * region['height_percent'])
            
            roi = image[y:y+h, x:x+w]
            
            if roi.size == 0:
                return 1  # Default to seat 1
            
            # Convert to grayscale
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi
            
            # Detect circular objects (dealer button)
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                param1=50, param2=30, minRadius=8, maxRadius=25
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                
                if len(circles) > 0:
                    # Find the circle closest to each seat
                    button_x, button_y = circles[0][:2]
                    
                    # Convert back to full image coordinates
                    abs_x = x + button_x
                    abs_y = y + button_y
                    
                    # Determine which seat the button is closest to
                    min_distance = float('inf')
                    dealer_seat = 1
                    
                    for seat_num, seat_regions in self.seat_regions.items():
                        seat_center_x = width * (seat_regions['name']['x_percent'] + seat_regions['name']['width_percent'] / 2)
                        seat_center_y = height * (seat_regions['name']['y_percent'] + seat_regions['name']['height_percent'] / 2)
                        
                        distance = np.sqrt((abs_x - seat_center_x)**2 + (abs_y - seat_center_y)**2)
                        
                        if distance < min_distance:
                            min_distance = distance
                            dealer_seat = seat_num
                    
                    self.logger.debug(f"Dealer button detected at seat {dealer_seat}")
                    return dealer_seat
            
            # Fallback: assume dealer is at seat 1
            return 1
            
        except Exception as e:
            self.logger.error(f"Error detecting dealer button: {e}")
            return 1
    
    def detect_hero_seat(self, image: np.ndarray) -> int:
        """Detect which seat is the hero (player) seat."""
        try:
            # Hero seat is typically the one with visible hole cards
            # and usually at the bottom of the screen (seat 1)
            
            # Check for cards in seat 1 (most common hero position)
            seat_1_cards = self.seat_regions[1]['cards']
            height, width = image.shape[:2]
            
            x = int(width * seat_1_cards['x_percent'])
            y = int(height * seat_1_cards['y_percent'])
            w = int(width * seat_1_cards['width_percent'])
            h = int(height * seat_1_cards['height_percent'])
            
            cards_roi = image[y:y+h, x:x+w]
            
            if cards_roi.size > 0:
                # Check if there are visible cards (not face down)
                # Face-up cards have more color variation than face-down cards
                if len(cards_roi.shape) == 3:
                    # Check for white/colored areas (face-up cards)
                    hsv = cv2.cvtColor(cards_roi, cv2.COLOR_BGR2HSV)
                    
                    # Look for white areas (card faces)
                    white_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
                    white_pixels = np.sum(white_mask > 0)
                    
                    if white_pixels > 100:  # Threshold for visible cards
                        self.logger.debug("Hero detected at seat 1 (visible cards)")
                        return 1
            
            # If no clear indication, assume seat 1 is hero
            return 1
            
        except Exception as e:
            self.logger.error(f"Error detecting hero seat: {e}")
            return 1
    
    def analyze_player_info(self, image: np.ndarray, seat_number: int, is_hero: bool = False) -> Optional[PlayerInfo]:
        """Analyze information for a specific player seat."""
        try:
            if seat_number not in self.seat_regions:
                # Try enhanced regions
                if seat_number not in self.enhanced_seat_regions:
                    return None
                seat_regions = self.enhanced_seat_regions[seat_number]
            else:
                seat_regions = self.seat_regions[seat_number]
            
            # Extract player name
            name_text = self.extract_text_with_enhanced_ocr(image, seat_regions['name'])
            if not name_text:
                name_text = self.extract_text_from_region(image, seat_regions['name'])
            
            # Enhanced empty seat detection
            if not name_text or len(name_text.strip()) < 2:
                # Check if there are cards visible (for hero detection)
                if is_hero:
                    cards_region = seat_regions.get('cards')
                    if cards_region:
                        cards_roi = self.extract_region_image(image, cards_region)
                        if self.has_visible_cards(cards_roi):
                            name_text = "Hero"  # Default name for hero
                        else:
                            return None
                else:
                    # Check for chip stack or other indicators
                    stack_text = self.extract_text_from_region(image, seat_regions['stack'])
                    if not stack_text or self.parse_monetary_value(stack_text) <= 0:
                        return None
                    name_text = f"Player{seat_number}"  # Default name
            
            # Extract stack size
            stack_text = self.extract_text_with_enhanced_ocr(image, seat_regions['stack'])
            if not stack_text:
                stack_text = self.extract_text_from_region(image, seat_regions['stack'])
            stack_value = self.parse_monetary_value(stack_text)
            
            # Skip if no meaningful stack detected
            if stack_value <= 0 and not is_hero:
                return None
            
            # Convert to BB units
            stack_bb = stack_value / self.big_blind_value if self.big_blind_value else stack_value
            
            # Extract current bet
            bet_text = self.extract_text_with_enhanced_ocr(image, seat_regions.get('bet', seat_regions['stack']))
            bet_value = self.parse_monetary_value(bet_text)
            bet_bb = bet_value / self.big_blind_value if self.big_blind_value else bet_value
            
            # Determine position based on dealer button
            position = self.calculate_position(seat_number, self.detect_dealer_button(image))
            
            # Enhanced activity detection
            is_active = self.is_player_active(image, seat_regions)
            
            player_info = PlayerInfo(
                seat_number=seat_number,
                name=name_text.strip(),
                stack_size=stack_bb,
                is_hero=is_hero,
                is_active=is_active,
                current_bet=bet_bb,
                position=position
            )
            
            self.logger.debug(f"Player {seat_number}: {player_info.name}, Stack: {stack_bb:.1f}BB, Position: {position}")
            return player_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing player {seat_number}: {e}")
            return None
    
    def extract_region_image(self, image: np.ndarray, region: Dict) -> np.ndarray:
        """Extract image region based on percentage coordinates."""
        try:
            height, width = image.shape[:2]
            
            x = int(width * region['x_percent'])
            y = int(height * region['y_percent'])
            w = int(width * region['width_percent'])
            h = int(height * region['height_percent'])
            
            return image[y:y+h, x:x+w]
        except Exception:
            return np.array([])
    
    def has_visible_cards(self, cards_roi: np.ndarray) -> bool:
        """Check if there are visible cards in the region."""
        try:
            if cards_roi.size == 0:
                return False
            
            # Convert to HSV for better color detection
            if len(cards_roi.shape) == 3:
                hsv = cv2.cvtColor(cards_roi, cv2.COLOR_BGR2HSV)
                
                # Look for white areas (card faces)
                white_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
                white_pixels = np.sum(white_mask > 0)
                
                # If significant white area, likely has visible cards
                return white_pixels > (cards_roi.shape[0] * cards_roi.shape[1] * 0.1)
            
            return False
        except Exception:
            return False
    
    def is_player_active(self, image: np.ndarray, seat_regions: Dict) -> bool:
        """Enhanced check if player is active at the table."""
        try:
            # Check multiple indicators
            indicators = 0
            
            # 1. Check for name text
            name_text = self.extract_text_from_region(image, seat_regions['name'])
            if name_text and len(name_text.strip()) > 1:
                indicators += 1
            
            # 2. Check for stack amount
            stack_text = self.extract_text_from_region(image, seat_regions['stack'])
            if stack_text and self.parse_monetary_value(stack_text) > 0:
                indicators += 1
            
            # 3. Check for visual activity in the seat area
            name_roi = self.extract_region_image(image, seat_regions['name'])
            if name_roi.size > 0:
                variance = np.var(name_roi)
                if variance > 50:  # Some visual activity
                    indicators += 1
            
            # Player is active if at least 2 indicators are present
            return indicators >= 2
            
        except Exception:
            return False
    
    def calculate_position(self, seat_number: int, dealer_seat: int) -> str:
        """Calculate player position based on seat and dealer button."""
        try:
            # Calculate relative position from dealer
            seats_from_dealer = (seat_number - dealer_seat) % 9
            
            # Position mapping for 9-max table
            position_map = {
                1: "SB",    # Small Blind
                2: "BB",    # Big Blind  
                3: "UTG",   # Under the Gun
                4: "UTG+1", # UTG+1
                5: "MP",    # Middle Position
                6: "MP+1",  # Middle Position
                7: "CO",    # Cutoff
                8: "BTN",   # Button
                0: "BTN"    # Button (when seats_from_dealer = 0)
            }
            
            return position_map.get(seats_from_dealer, f"Seat{seats_from_dealer}")
            
        except Exception as e:
            self.logger.error(f"Error calculating position: {e}")
            return "Unknown"
    
    def analyze_complete_table(self, image: np.ndarray) -> TableInfo:
        """Perform complete table analysis and return all information."""
        try:
            self.logger.info("Starting complete table analysis")
            
            # Store current window title for stake detection
            if hasattr(self, 'window_capture') and self.window_capture.selected_window:
                self.current_window_title = self.window_capture.selected_window.get('title', '')
            else:
                self.current_window_title = ""
            
            # Detect table stakes and blinds
            small_blind, big_blind, stakes = self.detect_table_stakes(image)
            self.logger.info(f"Stakes detected: {stakes} (SB: {small_blind}, BB: {big_blind})")
            
            # Detect dealer button
            dealer_seat = self.detect_dealer_button(image)
            self.logger.info(f"Dealer button detected at seat: {dealer_seat}")
            
            # Detect hero seat
            hero_seat = self.detect_hero_seat(image)
            self.logger.info(f"Hero seat detected: {hero_seat}")
            
            # Analyze all players
            players = []
            for seat_num in range(1, 10):  # Seats 1-9
                # Try both region sets
                is_hero = (seat_num == hero_seat)
                player_info = self.analyze_player_info(image, seat_num, is_hero)
                
                if player_info:
                    players.append(player_info)
                    self.logger.debug(f"Player detected at seat {seat_num}: {player_info.name}")
            
            self.logger.info(f"Total players detected: {len(players)}")
            
            # Extract pot size
            pot_text = self.extract_text_with_enhanced_ocr(image, self.enhanced_ui_regions['pot'])
            if not pot_text:
                pot_text = self.extract_text_from_region(image, self.enhanced_ui_regions['pot'])
            pot_value = self.parse_monetary_value(pot_text)
            pot_bb = pot_value / big_blind if big_blind else pot_value
            self.logger.info(f"Pot detected: {pot_text} -> {pot_bb:.1f}BB")
            
            # Determine current bet (highest bet among all players)
            current_bet_bb = max([p.current_bet for p in players] + [0.0])
            
            # Determine game phase based on community cards
            # This would integrate with the community card detector
            game_phase = "pre-flop"  # Default, would be updated by community card analysis
            
            table_info = TableInfo(
                players=players,
                hero_seat=hero_seat,
                dealer_seat=dealer_seat,
                small_blind=small_blind,
                big_blind=big_blind,
                pot_size=pot_bb,
                current_bet=current_bet_bb,
                game_phase=game_phase,
                table_stakes=stakes,
                max_players=9
            )
            
            self.logger.info(f"Table analysis complete: {len(players)} players, "
                           f"Hero: Seat {hero_seat}, Dealer: Seat {dealer_seat}, "
                           f"Stakes: {stakes}, Pot: {pot_bb:.1f}BB")
            
            return table_info
            
        except Exception as e:
            self.logger.error(f"Error in complete table analysis: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return TableInfo(
                players=[],
                hero_seat=1,
                dealer_seat=1,
                small_blind=0.25,
                big_blind=0.50,
                pot_size=0.0,
                current_bet=0.0,
                game_phase="pre-flop",
                table_stakes="NL50"
            )
    
    def get_hero_info(self, table_info: TableInfo) -> Optional[PlayerInfo]:
        """Get hero player information from table analysis."""
        for player in table_info.players:
            if player.is_hero:
                return player
        return None
    
    def get_effective_stack_sizes(self, table_info: TableInfo) -> Dict[int, float]:
        """Calculate effective stack sizes between hero and each opponent."""
        hero = self.get_hero_info(table_info)
        if not hero:
            return {}
        
        effective_stacks = {}
        for player in table_info.players:
            if not player.is_hero:
                # Effective stack is the smaller of the two stacks
                effective_stack = min(hero.stack_size, player.stack_size)
                effective_stacks[player.seat_number] = effective_stack
        
        return effective_stacks
    
    def format_table_summary(self, table_info: TableInfo) -> str:
        """Format table information for display."""
        try:
            hero = self.get_hero_info(table_info)
            hero_info = f"Hero (Seat {hero.seat_number}): {hero.stack_size:.1f}BB" if hero else "Hero: Not found"
            
            summary = f"""Table Analysis Summary:
Stakes: {table_info.table_stakes} (SB: ${table_info.small_blind}, BB: ${table_info.big_blind})
Players: {len(table_info.players)}/9
{hero_info}
Dealer: Seat {table_info.dealer_seat}
Pot: {table_info.pot_size:.1f}BB
Current Bet: {table_info.current_bet:.1f}BB
Phase: {table_info.game_phase}

Active Players:"""
            
            for player in table_info.players:
                marker = " (HERO)" if player.is_hero else ""
                summary += f"\nSeat {player.seat_number}: {player.name} - {player.stack_size:.1f}BB ({player.position}){marker}"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error formatting table summary: {e}")
            return "Error formatting table information"