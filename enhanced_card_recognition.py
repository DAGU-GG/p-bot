"""
Enhanced Card Recognition System
Combines OCR and pattern matching for robust card detection
"""

import cv2
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import time

# Import recognition systems
try:
    from enhanced_ocr_recognition import EnhancedOCRCardRecognition
    from fallback_card_recognition import FallbackCardRecognition
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OCR systems not available: {e}")
    OCR_AVAILABLE = False

@dataclass
class CardResult:
    """Result of card recognition"""
    rank: str
    suit: str
    confidence: float
    method: str
    region: Tuple[int, int, int, int]  # x, y, w, h

class EnhancedCardRecognition:
    """Enhanced card recognition using multiple methods"""
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger("enhanced_card_recognition")
        
        # Initialize recognition systems
        self.ocr_system = None
        self.fallback_system = None
        
        if OCR_AVAILABLE:
            try:
                self.ocr_system = EnhancedOCRCardRecognition()
                self.logger.info("OCR recognition system initialized")
            except Exception as e:
                self.logger.warning(f"OCR system failed to initialize: {e}")
            
            try:
                self.fallback_system = FallbackCardRecognition()
                self.logger.info("Fallback recognition system initialized")
            except Exception as e:
                self.logger.warning(f"Fallback system failed to initialize: {e}")
        
        # Recognition settings
        self.min_confidence = 0.1
        self.ocr_priority = True
        
    def recognize_card(self, card_image: np.ndarray, region: Tuple[int, int, int, int] = None, 
                      four_color_deck: bool = True) -> Optional[CardResult]:
        """
        Recognize a card using available recognition methods
        
        Args:
            card_image: Card image to recognize
            region: (x, y, w, h) region coordinates
            four_color_deck: Whether to use 4-color deck recognition
        
        Returns:
            CardResult if successful, None otherwise
        """
        if card_image is None or card_image.size == 0:
            return None
        
        results = []
        
        # Try OCR recognition first if available and preferred
        if self.ocr_system and self.ocr_priority:
            ocr_result = self._try_ocr_recognition(card_image, region)
            if ocr_result:
                results.append(ocr_result)
        
        # Try fallback recognition
        if self.fallback_system:
            fallback_result = self._try_fallback_recognition(card_image, region, four_color_deck)
            if fallback_result:
                results.append(fallback_result)
        
        # Try OCR as fallback if not tried first
        if self.ocr_system and not self.ocr_priority and not results:
            ocr_result = self._try_ocr_recognition(card_image, region)
            if ocr_result:
                results.append(ocr_result)
        
        # Return best result
        if results:
            best_result = max(results, key=lambda r: r.confidence)
            if best_result.confidence >= self.min_confidence:
                return best_result
        
        return None
    
    def _try_ocr_recognition(self, card_image: np.ndarray, region: Tuple[int, int, int, int]) -> Optional[CardResult]:
        """Try OCR recognition on card image"""
        try:
            result = self.ocr_system.recognize_card(card_image, debug=self.debug_mode)
            if result and result.confidence > 0:
                return CardResult(
                    rank=result.rank,
                    suit=result.suit,
                    confidence=result.confidence,
                    method="OCR",
                    region=region or (0, 0, card_image.shape[1], card_image.shape[0])
                )
        except Exception as e:
            self.logger.warning(f"OCR recognition failed: {e}")
        
        return None
    
    def _try_fallback_recognition(self, card_image: np.ndarray, region: Tuple[int, int, int, int], 
                                 four_color_deck: bool) -> Optional[CardResult]:
        """Try fallback pattern matching recognition"""
        try:
            result = self.fallback_system.recognize_card(card_image, four_color_deck=four_color_deck)
            if result and result.confidence > 0:
                return CardResult(
                    rank=result.rank,
                    suit=result.suit,
                    confidence=result.confidence,
                    method="Pattern",
                    region=region or (0, 0, card_image.shape[1], card_image.shape[0])
                )
        except Exception as e:
            self.logger.warning(f"Fallback recognition failed: {e}")
        
        return None
    
    def recognize_multiple_cards(self, image: np.ndarray, regions: List[Tuple[int, int, int, int]], 
                               four_color_deck: bool = True) -> List[CardResult]:
        """
        Recognize multiple cards from regions in an image
        
        Args:
            image: Full screenshot image
            regions: List of (x, y, w, h) regions containing cards
            four_color_deck: Whether to use 4-color deck recognition
        
        Returns:
            List of CardResult objects
        """
        results = []
        
        for i, region in enumerate(regions):
            x, y, w, h = region
            
            # Extract card region
            if (x + w <= image.shape[1] and y + h <= image.shape[0] and x >= 0 and y >= 0):
                card_image = image[y:y+h, x:x+w]
                
                # Save debug image if enabled
                if self.debug_mode:
                    debug_filename = f"debug_card_region_{i}_{int(time.time())}.png"
                    cv2.imwrite(debug_filename, card_image)
                
                # Recognize card
                result = self.recognize_card(card_image, region, four_color_deck)
                if result:
                    results.append(result)
                    self.logger.info(f"Card {i}: {result.rank}{result.suit} ({result.method}, {result.confidence:.2f})")
        
        return results
    
    def preprocess_card_image(self, card_image: np.ndarray) -> np.ndarray:
        """Preprocess card image for better recognition"""
        if card_image is None or card_image.size == 0:
            return card_image
        
        # Convert to RGB if needed
        if len(card_image.shape) == 3:
            processed = cv2.cvtColor(card_image, cv2.COLOR_BGR2RGB)
        else:
            processed = card_image.copy()
        
        # Enhance contrast
        processed = cv2.convertScaleAbs(processed, alpha=1.2, beta=10)
        
        # Denoise
        if len(processed.shape) == 3:
            processed = cv2.fastNlMeansDenoisingColored(processed, None, 10, 10, 7, 21)
        else:
            processed = cv2.fastNlMeansDenoising(processed, None, 10, 7, 21)
        
        return processed
    
    def get_recognition_stats(self) -> Dict:
        """Get statistics about recognition performance"""
        return {
            'ocr_available': self.ocr_system is not None,
            'fallback_available': self.fallback_system is not None,
            'min_confidence': self.min_confidence,
            'ocr_priority': self.ocr_priority,
            'debug_mode': self.debug_mode
        }

def test_enhanced_recognition():
    """Test enhanced recognition system"""
    print("Testing Enhanced Card Recognition System...")
    
    # Initialize system
    recognizer = EnhancedCardRecognition(debug_mode=True)
    
    # Print stats
    stats = recognizer.get_recognition_stats()
    print(f"Recognition Stats: {stats}")
    
    # Try to load test image
    test_images = ['test_card.png', 'calibration_screenshot.png', 'poker_screenshot.png']
    
    for test_image in test_images:
        try:
            image = cv2.imread(test_image)
            if image is not None:
                print(f"Loaded test image: {test_image}")
                
                # Test on whole image (will likely fail but tests the system)
                result = recognizer.recognize_card(image)
                if result:
                    print(f"Recognition result: {result.rank}{result.suit} ({result.method}, {result.confidence:.2f})")
                else:
                    print("No card recognized in full image")
                
                break
        except Exception as e:
            print(f"Error testing with {test_image}: {e}")
    
    print("Enhanced recognition test complete")

def main():
    """Main function for testing"""
    logging.basicConfig(level=logging.INFO)
    test_enhanced_recognition()

if __name__ == "__main__":
    main()
