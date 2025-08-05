"""
Enhanced OCR Card Recognition System
Works with table reference system for accurate card detection
"""

import cv2
import numpy as np
import pytesseract
from typing import Tuple, Optional, List, Dict
import logging
from dataclasses import dataclass
import time

# Configure Tesseract for this module
from tesseract_config import configure_tesseract
configure_tesseract()

logger = logging.getLogger(__name__)

@dataclass
class CardResult:
    """Result of card recognition"""
    rank: str
    suit: str
    confidence: float
    method: str
    debug_info: Optional[Dict] = None

class EnhancedOCRCardRecognition:
    """Advanced OCR card recognition with multiple methods"""
    
    def __init__(self):
        # Define suit colors for 4-color deck
        self.suit_colors = {
            'hearts': {
                'hsv_lower': np.array([0, 50, 50]),
                'hsv_upper': np.array([10, 255, 255]),
                'rgb_range': ([0, 0, 150], [80, 80, 255]),  # Red
                'symbol': '♥',
                'code': 'h'
            },
            'diamonds': {
                'hsv_lower': np.array([100, 50, 50]),
                'hsv_upper': np.array([130, 255, 255]),
                'rgb_range': ([100, 100, 0], [255, 255, 100]),  # Blue in 4-color
                'symbol': '♦',
                'code': 'd'
            },
            'clubs': {
                'hsv_lower': np.array([40, 50, 50]),
                'hsv_upper': np.array([80, 255, 255]),
                'rgb_range': ([0, 100, 0], [100, 255, 100]),  # Green
                'symbol': '♣',
                'code': 'c'
            },
            'spades': {
                'hsv_lower': np.array([0, 0, 0]),
                'hsv_upper': np.array([180, 255, 50]),
                'rgb_range': ([0, 0, 0], [50, 50, 50]),  # Black
                'symbol': '♠',
                'code': 's'
            }
        }
        
        # Rank patterns for better OCR (order matters - longer patterns first)
        self.rank_patterns = {
            'A': ['A', '4', 'a'],  # Common OCR mistakes
            'K': ['K', 'k'],
            'Q': ['Q', 'q', '0'],
            'J': ['J', 'j'],  # Removed '1' to avoid conflict with 10
            'T': ['10', '1O', 'l0', 'T', 't'],  # 10 patterns first, before single chars
            '9': ['9', 'g'],
            '8': ['8', 'B'],
            '7': ['7'],  # Removed '1' to avoid conflict with 10
            '6': ['6', 'b'],
            '5': ['5', 'S'],
            '4': ['4', 'A'],
            '3': ['3'],
            '2': ['2', 'Z']
        }
        
    def recognize_card(self, card_img: np.ndarray, debug=False) -> Optional[CardResult]:
        """
        Recognize a card using multiple OCR strategies
        
        Args:
            card_img: Image of the card
            debug: Save debug images
            
        Returns:
            CardResult with rank and suit, or None if no card detected
        """
        if card_img is None or card_img.size == 0:
            return None
        
        # Check if card is present
        if not self._is_card_present(card_img):
            return None
        
        # Try multiple recognition methods
        methods = [
            self._recognize_by_corner_ocr,
            self._recognize_by_symbol_matching,
            self._recognize_by_color_and_ocr,
            self._recognize_by_full_ocr
        ]
        
        for method in methods:
            try:
                result = method(card_img)
                if result and result.confidence > 0.6:
                    if debug:
                        self._save_debug_image(card_img, result)
                    return result
            except Exception as e:
                logger.error(f"Recognition method {method.__name__} failed: {e}")
                continue
        
        return None
    
    def _is_card_present(self, img: np.ndarray) -> bool:
        """Check if image contains a card"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Check brightness and contrast
        mean_brightness = np.mean(gray)
        std_dev = np.std(gray)
        
        # Card should have reasonable brightness and contrast
        return mean_brightness > 50 and std_dev > 20
    
    def _recognize_by_corner_ocr(self, card_img: np.ndarray) -> Optional[CardResult]:
        """Recognize by OCR on top-left corner with improved 10 detection"""
        h, w = card_img.shape[:2]
        
        # Extract top-left corner (where rank and suit are)
        corner_region = card_img[0:int(h*0.25), 0:int(w*0.25)]
        
        # Preprocess for OCR
        processed = self._preprocess_for_ocr(corner_region)
        
        # Try multiple OCR configurations for better 10 detection
        ocr_configs = [
            '--psm 8 -c tessedit_char_whitelist=10023456789TJQKA',  # Include '10' specifically
            '--psm 10 -c tessedit_char_whitelist=23456789TJQKA10',  # Single uniform block
            '--psm 13',  # Raw line, treat the image as a single text line
            '--psm 6'   # Single uniform block of text
        ]
        
        rank = None
        best_confidence = 0
        
        for config in ocr_configs:
            try:
                # Get OCR data with confidence
                ocr_data = pytesseract.image_to_data(processed, config=config, output_type=pytesseract.Output.DICT)
                
                # Extract text with confidence
                texts = []
                confidences = []
                for i, conf in enumerate(ocr_data['conf']):
                    if int(conf) > 30:  # Minimum confidence
                        text = ocr_data['text'][i].strip()
                        if text:
                            texts.append(text)
                            confidences.append(int(conf))
                
                # Try each detected text
                for text, conf in zip(texts, confidences):
                    detected_rank = self._match_rank_pattern(text)
                    if detected_rank and conf > best_confidence:
                        rank = detected_rank
                        best_confidence = conf
                
                if rank:
                    break
                    
            except Exception:
                # Fallback to simple OCR
                rank_text = pytesseract.image_to_string(processed, config=config).strip()
                rank = self._match_rank_pattern(rank_text)
                if rank:
                    break
        
        # Detect suit by color
        suit = self._detect_suit_by_color(corner_region)
        
        if rank and suit:
            # Higher confidence for better OCR results
            confidence = 0.9 if best_confidence > 70 else 0.8
            return CardResult(
                rank=rank,
                suit=suit,
                confidence=confidence,
                method='corner_ocr'
            )
        
        return None
    
    def _recognize_by_symbol_matching(self, card_img: np.ndarray) -> Optional[CardResult]:
        """Recognize by matching suit symbols"""
        h, w = card_img.shape[:2]
        
        # Look for suit symbols in typical locations
        symbol_regions = [
            card_img[int(h*0.15):int(h*0.35), int(w*0.15):int(w*0.35)],  # Top-left
            card_img[int(h*0.65):int(h*0.85), int(w*0.65):int(w*0.85)]   # Bottom-right
        ]
        
        suit = None
        for region in symbol_regions:
            # OCR for suit symbols
            symbol_config = '--psm 10 -c tessedit_char_whitelist=♠♥♦♣'
            symbol_text = pytesseract.image_to_string(region, config=symbol_config).strip()
            
            for suit_name, suit_info in self.suit_colors.items():
                if suit_info['symbol'] in symbol_text:
                    suit = suit_info['code']
                    break
            
            if suit:
                break
        
        # Get rank from corner
        corner_region = card_img[0:int(h*0.2), 0:int(w*0.3)]
        processed = self._preprocess_for_ocr(corner_region)
        rank_text = pytesseract.image_to_string(processed, config='--psm 8').strip()
        rank = self._match_rank_pattern(rank_text)
        
        if rank and suit:
            return CardResult(
                rank=rank,
                suit=suit,
                confidence=0.7,
                method='symbol_matching'
            )
        
        return None
    
    def _recognize_by_color_and_ocr(self, card_img: np.ndarray) -> Optional[CardResult]:
        """Recognize using color analysis and OCR combined"""
        # Detect suit by dominant color
        suit = self._detect_suit_by_dominant_color(card_img)
        
        # Get rank by OCR on entire card
        gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        
        # Multiple preprocessing attempts
        preprocessed_images = [
            self._preprocess_for_ocr(gray),
            self._preprocess_with_edge_detection(gray),
            self._preprocess_with_adaptive_threshold(gray)
        ]
        
        rank = None
        for processed in preprocessed_images:
            # OCR with different configs
            configs = [
                '--psm 8 -c tessedit_char_whitelist=23456789TJQKA',
                '--psm 10 -c tessedit_char_whitelist=23456789TJQKA10',
                '--psm 13'
            ]
            
            for config in configs:
                text = pytesseract.image_to_string(processed, config=config).strip()
                rank = self._match_rank_pattern(text)
                if rank:
                    break
            
            if rank:
                break
        
        if rank and suit:
            return CardResult(
                rank=rank,
                suit=suit,
                confidence=0.75,
                method='color_and_ocr'
            )
        
        return None
    
    def _recognize_by_full_ocr(self, card_img: np.ndarray) -> Optional[CardResult]:
        """Last resort: OCR the entire card"""
        # Preprocess
        gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        processed = self._preprocess_for_ocr(gray)
        
        # Full OCR
        full_text = pytesseract.image_to_string(processed).strip().upper()
        
        # Look for rank and suit in text
        rank = None
        suit = None
        
        # Check for ranks
        for r, patterns in self.rank_patterns.items():
            for pattern in patterns:
                if pattern.upper() in full_text:
                    rank = r
                    break
            if rank:
                break
        
        # Check for suit words
        suit_words = {
            'HEART': 'h', 'HEARTS': 'h',
            'DIAMOND': 'd', 'DIAMONDS': 'd',
            'CLUB': 'c', 'CLUBS': 'c',
            'SPADE': 's', 'SPADES': 's'
        }
        
        for word, code in suit_words.items():
            if word in full_text:
                suit = code
                break
        
        # If no suit word found, use color
        if not suit:
            suit = self._detect_suit_by_color(card_img)
        
        if rank and suit:
            return CardResult(
                rank=rank,
                suit=suit,
                confidence=0.6,
                method='full_ocr'
            )
        
        return None
    
    def _preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """Standard preprocessing for OCR"""
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Binary threshold
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _preprocess_with_edge_detection(self, img: np.ndarray) -> np.ndarray:
        """Preprocessing using edge detection"""
        # Edge detection
        edges = cv2.Canny(img, 50, 150)
        
        # Dilate to connect edges
        kernel = np.ones((2,2), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        return dilated
    
    def _preprocess_with_adaptive_threshold(self, img: np.ndarray) -> np.ndarray:
        """Preprocessing using adaptive threshold"""
        # Adaptive threshold
        adaptive = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return adaptive
    
    def _detect_suit_by_color(self, img: np.ndarray) -> Optional[str]:
        """Detect suit by analyzing dominant color"""
        # Convert to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Check each suit color
        max_pixels = 0
        detected_suit = None
        
        for suit_name, suit_info in self.suit_colors.items():
            # Create mask
            mask = cv2.inRange(hsv, suit_info['hsv_lower'], suit_info['hsv_upper'])
            pixel_count = cv2.countNonZero(mask)
            
            if pixel_count > max_pixels:
                max_pixels = pixel_count
                detected_suit = suit_info['code']
        
        # Need minimum pixels to be confident
        if max_pixels > 50:
            return detected_suit
        
        return None
    
    def _detect_suit_by_dominant_color(self, img: np.ndarray) -> Optional[str]:
        """Detect suit by the most dominant color in the image"""
        # Get average color in HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        avg_color = np.mean(hsv.reshape(-1, 3), axis=0)
        
        # Check which suit color range it falls into
        for suit_name, suit_info in self.suit_colors.items():
            lower = suit_info['hsv_lower']
            upper = suit_info['hsv_upper']
            
            if all(lower[i] <= avg_color[i] <= upper[i] for i in range(3)):
                return suit_info['code']
        
        return None
    
    def _match_rank_pattern(self, text: str) -> Optional[str]:
        """Match OCR text to known rank patterns with improved 10 vs 7 handling"""
        if not text:
            return None
        
        text = text.strip().upper()
        
        # Special handling for 10 detection
        if '10' in text or '1O' in text or 'L0' in text or '10' == text:
            return 'T'
        
        # Check for clear two-character patterns that indicate 10
        if len(text) >= 2:
            # Look for patterns that strongly suggest 10
            ten_indicators = ['10', '1O', 'L0', 'IO', '1Q', 'LO']
            for indicator in ten_indicators:
                if indicator in text:
                    return 'T'
        
        # Direct match first
        if text in self.rank_patterns:
            return text
        
        # Pattern matching - prioritize longer patterns first
        # Sort patterns by length (longest first) to avoid conflicts
        all_patterns = []
        for rank, patterns in self.rank_patterns.items():
            for pattern in patterns:
                all_patterns.append((len(pattern.upper()), rank, pattern.upper()))
        
        # Sort by length descending, then by rank
        all_patterns.sort(key=lambda x: (-x[0], x[1]))
        
        # Match patterns
        for length, rank, pattern in all_patterns:
            if pattern == text or pattern in text:
                return rank
        
        # Last resort: single character matching for clear cases
        if len(text) == 1:
            single_char_matches = {
                'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J',
                '9': '9', '8': '8', '6': '6', '5': '5',
                '4': '4', '3': '3', '2': '2'
            }
            # Note: We avoid '7' and '1' single char matches to prevent 10 confusion
            if text in single_char_matches:
                return single_char_matches[text]
            
            # Only match '7' if we're confident it's not part of '10'
            if text == '7':
                return '7'
        
        return None
    
    def _save_debug_image(self, img: np.ndarray, result: CardResult):
        """Save debug image with recognition result"""
        timestamp = int(time.time() * 1000)
        filename = f"debug_ocr_{result.rank}{result.suit}_{timestamp}.png"
        cv2.imwrite(filename, img)
        logger.info(f"Saved debug image: {filename}")

def integrate_with_bot(poker_bot):
    """Integrate the enhanced OCR system with the poker bot"""
    from table_reference_system import TableReferenceSystem
    
    # Initialize systems
    table_ref = TableReferenceSystem()
    ocr_recognizer = EnhancedOCRCardRecognition()
    
    def enhanced_analyze_game_state(screenshot=None):
        """Enhanced game state analysis with auto-calibration"""
        try:
            # Get screenshot
            screenshot = _get_screenshot(poker_bot, screenshot)
            if screenshot is None:
                return None
            
            # Ensure calibration
            if not _ensure_calibration(poker_bot, table_ref, screenshot):
                return None
            
            # Analyze cards
            return _analyze_cards(poker_bot, ocr_recognizer, screenshot)
            
        except Exception as e:
            logger.error(f"Enhanced analysis error: {e}")
            return None
    
    # Replace the bot's analyze method
    poker_bot.analyze_game_state = enhanced_analyze_game_state
    logger.info("Enhanced OCR system integrated with auto-calibration")

def _get_screenshot(poker_bot, screenshot):
    """Get screenshot from bot or provided source"""
    if screenshot is None:
        return poker_bot.window_capture.capture_window()
    return screenshot

def _ensure_calibration(poker_bot, table_ref, screenshot):
    """Ensure bot has calibrated regions"""
    if not hasattr(poker_bot, 'regions') or not poker_bot.regions:
        logger.info("No regions found, auto-calibrating...")
        regions = table_ref.auto_calibrate_from_screenshot(screenshot)
        poker_bot.regions = regions
        return regions is not None
    return True

def _analyze_cards(poker_bot, ocr_recognizer, screenshot):
    """Analyze cards from screenshot using regions"""
    hero_cards = []
    community_cards = []
    height, width = screenshot.shape[:2]
    
    # Process each region
    for region_name, region_data in poker_bot.regions.items():
        card_str = _process_region(region_data, screenshot, ocr_recognizer, width, height)
        if card_str:
            if 'hero' in region_name:
                hero_cards.append(card_str)
            elif 'card' in region_name:
                community_cards.append(card_str)
    
    # Build result
    return {
        'hero_cards': hero_cards if hero_cards else None,
        'community_cards': community_cards,
        'valid': len(hero_cards) == 2 or len(hero_cards) == 0,
        'auto_calibrated': True
    }

def _process_region(region_data, screenshot, ocr_recognizer, width, height):
    """Process a single region and return recognized card string"""
    x = int(region_data['x_percent'] * width)
    y = int(region_data['y_percent'] * height)
    w = int(region_data['width_percent'] * width)
    h = int(region_data['height_percent'] * height)
    
    # Extract region if valid
    if 0 <= x < width and 0 <= y < height and x+w <= width and y+h <= height:
        card_img = screenshot[y:y+h, x:x+w]
        result = ocr_recognizer.recognize_card(card_img, debug=True)
        
        if result:
            return f"{result.rank}{result.suit}"
    
    return None

if __name__ == "__main__":
    # Test the enhanced OCR system
    recognizer = EnhancedOCRCardRecognition()
    
    # Test with a sample card image
    test_img = cv2.imread('test_card.png')
    if test_img is not None:
        result = recognizer.recognize_card(test_img, debug=True)
        if result:
            print(f"Recognized: {result.rank}{result.suit} (confidence: {result.confidence}, method: {result.method})")
        else:
            print("No card recognized")
    else:
        print("Please provide a test_card.png file")
