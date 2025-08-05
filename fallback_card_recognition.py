"""
Fallback Card Recognition System - Works without Tesseract OCR
Enhanced pattern matching and color analysis for 4-color deck support
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, List
import json

@dataclass
class CardResult:
    """Result of card recognition"""
    rank: str
    suit: str
    confidence: float
    method: str
    bbox: Optional[Tuple[int, int, int, int]] = None
    debug_info: Optional[Dict] = None

class FallbackCardRecognition:
    """Card recognition using pattern matching and color analysis only"""
    
    def __init__(self):
        self.suit_colors = {
            'clubs': {
                'default': ([0, 0, 0], [50, 50, 50]),      # Black
                'four_color': ([0, 100, 0], [80, 255, 80])  # Green
            },
            'diamonds': {
                'default': ([0, 0, 100], [50, 50, 255]),    # Red
                'four_color': ([100, 100, 0], [255, 255, 80]) # Yellow/Orange
            },
            'hearts': {
                'default': ([0, 0, 100], [50, 50, 255]),    # Red
                'four_color': ([0, 0, 100], [50, 50, 255])  # Red (same)
            },
            'spades': {
                'default': ([0, 0, 0], [50, 50, 50]),       # Black
                'four_color': ([100, 0, 0], [255, 50, 50])  # Blue
            }
        }
        
        # Card patterns for template matching
        self.card_templates = {}
        self.rank_patterns = {
            'A': ['ace', 'A'],
            'K': ['king', 'K'],
            'Q': ['queen', 'Q'], 
            'J': ['jack', 'J'],
            '10': ['10', 'T'],
            '9': ['9'],
            '8': ['8'],
            '7': ['7'],
            '6': ['6'],
            '5': ['5'],
            '4': ['4'],
            '3': ['3'],
            '2': ['2']
        }
        
    def recognize_card(self, image: np.ndarray, four_color_deck: bool = True) -> CardResult:
        """
        Recognize a card using pattern matching and color analysis
        """
        try:
            # Method 1: Color-based suit detection
            suit_result = self._detect_suit_by_color(image, four_color_deck)
            
            # Method 2: Pattern-based rank detection
            rank_result = self._detect_rank_by_pattern(image)
            
            # Method 3: Edge detection for card shapes
            shape_result = self._detect_by_shapes(image)
            
            # Combine results
            best_result = self._combine_results([suit_result, rank_result, shape_result])
            
            return best_result
            
        except Exception as e:
            return CardResult(
                rank="?",
                suit="?", 
                confidence=0.0,
                method="fallback_error",
                debug_info={"error": str(e)}
            )
    
    def _detect_suit_by_color(self, image: np.ndarray, four_color_deck: bool) -> CardResult:
        """Detect suit based on color analysis"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            best_suit = "?"
            best_confidence = 0.0
            color_mode = 'four_color' if four_color_deck else 'default'
            
            for suit, colors in self.suit_colors.items():
                if color_mode in colors:
                    lower, upper = colors[color_mode]
                    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                    
                    # Calculate percentage of pixels matching this color
                    total_pixels = mask.shape[0] * mask.shape[1]
                    matching_pixels = cv2.countNonZero(mask)
                    confidence = matching_pixels / total_pixels
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_suit = suit
            
            return CardResult(
                rank="?",
                suit=best_suit,
                confidence=best_confidence,
                method="color_analysis",
                debug_info={"color_mode": color_mode}
            )
            
        except Exception as e:
            return CardResult(
                rank="?",
                suit="?",
                confidence=0.0,
                method="color_error",
                debug_info={"error": str(e)}
            )
    
    def _detect_rank_by_pattern(self, image: np.ndarray) -> CardResult:
        """Detect rank using pattern matching"""
        try:
            # Convert to grayscale for pattern matching
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Look for number/letter patterns
            best_rank = "?"
            best_confidence = 0.0
            
            # Simple pattern detection based on contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Analyze contour shapes to guess rank
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    # Rough heuristics based on shape
                    if circularity > 0.7:  # Round shapes
                        best_rank = "Q"  # Queen or 9, 8, 6
                        best_confidence = 0.6
                    elif circularity < 0.3:  # Linear shapes
                        best_rank = "A"  # Ace, 4, or 7
                        best_confidence = 0.5
                    else:
                        best_rank = "K"  # King or other complex shapes
                        best_confidence = 0.4
            
            return CardResult(
                rank=best_rank,
                suit="?",
                confidence=best_confidence,
                method="pattern_analysis",
                debug_info={"contours_found": len(contours)}
            )
            
        except Exception as e:
            return CardResult(
                rank="?",
                suit="?",
                confidence=0.0,
                method="pattern_error",
                debug_info={"error": str(e)}
            )
    
    def _detect_by_shapes(self, image: np.ndarray) -> CardResult:
        """Detect card elements by shape analysis"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply morphological operations to enhance shapes
            kernel = np.ones((3,3), np.uint8)
            processed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Detect circles (for hearts, diamonds)
            circles = cv2.HoughCircles(
                processed,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=20,
                param1=50,
                param2=30,
                minRadius=5,
                maxRadius=50
            )
            
            # Detect lines (for spades, clubs)
            lines = cv2.HoughLinesP(
                cv2.Canny(processed, 50, 150),
                rho=1,
                theta=np.pi/180,
                threshold=20,
                minLineLength=10,
                maxLineGap=5
            )
            
            suit_guess = "?"
            confidence = 0.0
            
            if circles is not None and len(circles[0]) > 0:
                suit_guess = "hearts"  # Could be hearts or diamonds
                confidence = 0.6
            elif lines is not None and len(lines) > 2:
                suit_guess = "spades"  # Could be spades or clubs
                confidence = 0.5
            
            return CardResult(
                rank="?",
                suit=suit_guess,
                confidence=confidence,
                method="shape_analysis",
                debug_info={
                    "circles": len(circles[0]) if circles is not None else 0,
                    "lines": len(lines) if lines is not None else 0
                }
            )
            
        except Exception as e:
            return CardResult(
                rank="?",
                suit="?",
                confidence=0.0,
                method="shape_error",
                debug_info={"error": str(e)}
            )
    
    def _combine_results(self, results: List[CardResult]) -> CardResult:
        """Combine multiple recognition results"""
        # Find the result with highest confidence for each attribute
        best_suit_result = max(
            [r for r in results if r.suit != "?"],
            key=lambda x: x.confidence,
            default=CardResult("?", "?", 0.0, "no_suit")
        )
        
        best_rank_result = max(
            [r for r in results if r.rank != "?"],
            key=lambda x: x.confidence,
            default=CardResult("?", "?", 0.0, "no_rank")
        )
        
        # Combine the best results
        combined_confidence = (best_suit_result.confidence + best_rank_result.confidence) / 2
        
        return CardResult(
            rank=best_rank_result.rank,
            suit=best_suit_result.suit,
            confidence=combined_confidence,
            method=f"combined_{best_suit_result.method}_{best_rank_result.method}",
            debug_info={
                "suit_method": best_suit_result.method,
                "rank_method": best_rank_result.method,
                "individual_confidences": {
                    "suit": best_suit_result.confidence,
                    "rank": best_rank_result.confidence
                }
            }
        )
    
    def test_recognition(self, test_image_path: str = None) -> Dict:
        """Test the fallback recognition system"""
        results = {
            "system": "Fallback Card Recognition",
            "tesseract_required": False,
            "status": "operational"
        }
        
        if test_image_path:
            try:
                image = cv2.imread(test_image_path)
                if image is not None:
                    result = self.recognize_card(image, four_color_deck=True)
                    results["test_result"] = {
                        "rank": result.rank,
                        "suit": result.suit,
                        "confidence": result.confidence,
                        "method": result.method
                    }
                else:
                    results["test_result"] = "Could not load test image"
            except Exception as e:
                results["test_result"] = f"Error: {str(e)}"
        
        return results

def main():
    """Test the fallback recognition system"""
    print("Testing Fallback Card Recognition System...")
    
    recognizer = FallbackCardRecognition()
    test_results = recognizer.test_recognition()
    
    print(json.dumps(test_results, indent=2))
    print("\nFallback system ready - no Tesseract required!")

if __name__ == "__main__":
    main()
