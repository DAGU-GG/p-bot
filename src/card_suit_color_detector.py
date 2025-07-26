"""
Enhanced Card Recognition System Integration

This script integrates the color-based suit detection with the standard card recognition system.
The goal is to improve accuracy by combining template matching with color analysis.

Usage:
    - Import to main project
    - Access through CardRecognizerEnhanced class
"""

import os
import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import time

# Import Card class if needed
try:
    from src.card import Card
except ImportError:
    # Define a minimal Card class if the import fails
    class Card:
        def __init__(self, rank, suit, confidence=0.0):
            self.rank = rank
            self.suit = suit
            self.confidence = confidence

class CardSuitColorDetector:
    """
    Utility class for detecting suit color (red or black) based on image analysis.
    Can be used standalone or integrated with card recognizer.
    """

    def __init__(self):
        """Initialize the suit color detector with default settings."""
        self.logger = logging.getLogger('card_suit_color')
        
        # Create debug directory if needed
        os.makedirs("debug_color_detection", exist_ok=True)
        
        # Color ranges for red and black in HSV
        # Red spans two ranges in HSV (wraps around hue value 0)
        self.lower_red1 = np.array([0, 100, 100])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([160, 100, 100])
        self.upper_red2 = np.array([180, 255, 255])
        
        # Black in HSV
        self.lower_black = np.array([0, 0, 0])
        self.upper_black = np.array([180, 255, 50])
        
        # Regions of interest for suit detection (normalized coordinates)
        self.suit_regions = [
            # Top left suit (small for number cards)
            {'x': 0.05, 'y': 0.05, 'width': 0.15, 'height': 0.15},
            # Bottom right suit (small for number cards)
            {'x': 0.80, 'y': 0.80, 'width': 0.15, 'height': 0.15},
            # Center area (for face cards)
            {'x': 0.25, 'y': 0.25, 'width': 0.5, 'height': 0.5}
        ]
    
    def detect_suit_color(self, card_img, debug=False):
        """
        Analyze the card image to determine if it's a red or black suit.
        
        Args:
            card_img: The card image to analyze
            debug: Whether to save debug images
            
        Returns:
            Tuple of (color, confidence) where color is 'red' or 'black'
        """
        try:
            if card_img is None or card_img.size == 0:
                return None, 0.0
            
            # Ensure we have a color image
            if len(card_img.shape) < 3:
                # Convert grayscale to color
                color_img = cv2.cvtColor(card_img, cv2.COLOR_GRAY2BGR)
            else:
                color_img = card_img.copy()
                
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
            
            # Get card dimensions
            h, w = color_img.shape[:2]
            
            # Extract regions of interest for suit detection
            regions = []
            for region in self.suit_regions:
                x = int(w * region['x'])
                y = int(h * region['y'])
                width = int(w * region['width'])
                height = int(h * region['height'])
                
                # Ensure region is within image bounds
                x = max(0, min(x, w-1))
                y = max(0, min(y, h-1))
                width = max(1, min(width, w-x))
                height = max(1, min(height, h-y))
                
                roi = hsv[y:y+height, x:x+width]
                regions.append(roi)
            
            # Create masks for red and black
            red_pixels = 0
            black_pixels = 0
            total_pixels = 0
            
            # For visual debugging
            if debug:
                color_img_debug = color_img.copy()
            
            for i, region in enumerate(regions):
                if region.size == 0:
                    continue
                    
                # Create masks for this region
                red_mask1 = cv2.inRange(region, self.lower_red1, self.upper_red1)
                red_mask2 = cv2.inRange(region, self.lower_red2, self.upper_red2)
                red_mask = cv2.bitwise_or(red_mask1, red_mask2)
                
                black_mask = cv2.inRange(region, self.lower_black, self.upper_black)
                
                # Count pixels
                red_count = cv2.countNonZero(red_mask)
                black_count = cv2.countNonZero(black_mask)
                region_pixels = region.shape[0] * region.shape[1]
                
                # Add to totals
                red_pixels += red_count
                black_pixels += black_count
                total_pixels += region_pixels
                
                # Draw region on debug image
                if debug:
                    x = int(w * self.suit_regions[i]['x'])
                    y = int(h * self.suit_regions[i]['y'])
                    width = int(w * self.suit_regions[i]['width'])
                    height = int(h * self.suit_regions[i]['height'])
                    cv2.rectangle(color_img_debug, (x, y), (x+width, y+height), (0, 255, 0), 1)
                    
                    # Add text with pixel counts
                    text = f"R:{red_count} B:{black_count}"
                    cv2.putText(color_img_debug, text, (x, y-5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
            # Calculate percentages
            red_percentage = (red_pixels / total_pixels) if total_pixels > 0 else 0
            black_percentage = (black_pixels / total_pixels) if total_pixels > 0 else 0
            
            # Determine suit color and confidence
            if red_percentage > black_percentage and red_percentage > 0.05:
                color = 'red'
                confidence = red_percentage
            elif black_percentage > red_percentage and black_percentage > 0.05:
                color = 'black'
                confidence = black_percentage
            else:
                # Default when we can't determine
                color = 'unknown'
                confidence = 0.0
                
            # Map color to suits
            suit_mapping = {
                'red': ['h', 'd'],  # hearts, diamonds
                'black': ['c', 's']  # clubs, spades
            }
            
            # Save debug images
            if debug:
                timestamp = int(time.time())
                debug_dir = "debug_color_detection"
                os.makedirs(debug_dir, exist_ok=True)
                
                # Add color and confidence text
                text = f"{color.upper()} ({confidence:.2f})"
                cv2.putText(color_img_debug, text, (10, 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Add pixel counts
                text = f"Red: {red_pixels}/{total_pixels} ({red_percentage:.2f})"
                cv2.putText(color_img_debug, text, (10, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
                text = f"Black: {black_pixels}/{total_pixels} ({black_percentage:.2f})"
                cv2.putText(color_img_debug, text, (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                
                # Save debug image
                cv2.imwrite(f"{debug_dir}/color_detection_{timestamp}.png", color_img_debug)
                
            self.logger.debug(f"Suit color: {color} (confidence: {confidence:.3f})")
            
            return color, confidence
            
        except Exception as e:
            self.logger.error(f"Error in detect_suit_color: {e}")
            return 'unknown', 0.0
            
    def map_color_to_possible_suits(self, color):
        """
        Map a detected color to possible suits.
        
        Args:
            color: 'red' or 'black'
            
        Returns:
            List of possible suit codes
        """
        if color == 'red':
            return ['h', 'd']  # hearts, diamonds
        elif color == 'black':
            return ['c', 's']  # clubs, spades
        else:
            return ['h', 'd', 'c', 's']  # all suits if unknown
