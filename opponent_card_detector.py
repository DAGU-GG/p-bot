#!/usr/bin/env python3
"""
Opponent Card Detector - Detect if opponents have cards in hand

This module detects wine-red card backs above opponent name regions to determine
which players are still active in the current hand.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional

class OpponentCardDetector:
    """Detects opponent cards by analyzing wine-red card backs above name regions."""
    
    def __init__(self):
        # Wine-red color range for card backs (in HSV)
        self.wine_red_lower = np.array([0, 50, 50])    # Lower HSV bound
        self.wine_red_upper = np.array([10, 255, 255]) # Upper HSV bound
        
        # Alternative red range (cards can vary slightly in color)
        self.alt_red_lower = np.array([170, 50, 50])
        self.alt_red_upper = np.array([180, 255, 255])
        
        # Detection thresholds
        self.min_card_area = 200        # Minimum area for card detection
        self.card_confidence_threshold = 0.3  # Minimum confidence for card presence
        
    def generate_card_regions(self, name_regions: Dict[str, List[int]]) -> Dict[str, List[int]]:
        """
        Generate card detection regions above each opponent name region.
        
        Args:
            name_regions: Dictionary of name regions {region_name: [x, y, w, h]}
            
        Returns:
            Dictionary of card detection regions {region_name: [x, y, w, h]}
        """
        card_regions = {}
        
        for region_name, coords in name_regions.items():
            if region_name.startswith('Position_') and region_name.endswith('_name'):
                # Extract position number
                position_num = region_name.split('_')[1]
                card_region_name = f"Position_{position_num}_cards"
                
                x, y, w, h = coords
                
                # Create card detection region above the name
                # Half the width, same height, positioned above the name region
                card_x = x + w // 4  # Center the narrower region
                card_y = y - h - 10  # Position above the name with small gap
                card_w = w // 2      # Half the width of name region
                card_h = h          # Same height as name region
                
                card_regions[card_region_name] = [card_x, card_y, card_w, card_h]
                
        return card_regions
    
    def detect_wine_red_cards(self, frame: np.ndarray, card_regions: Dict[str, List[int]]) -> Dict[str, Dict]:
        """
        Detect wine-red cards in the specified regions.
        
        Args:
            frame: Input frame from camera
            card_regions: Dictionary of card detection regions
            
        Returns:
            Dictionary with detection results for each region
        """
        results = {}
        
        # Convert frame to HSV for better color detection
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        for region_name, coords in card_regions.items():
            x, y, w, h = coords
            
            # Extract region (with bounds checking)
            if x >= 0 and y >= 0 and x + w <= frame.shape[1] and y + h <= frame.shape[0]:
                region = hsv_frame[y:y+h, x:x+w]
                
                # Detect wine-red color
                detection_result = self._analyze_region_for_cards(region, region_name)
                results[region_name] = detection_result
            else:
                # Region is out of bounds
                results[region_name] = {
                    'has_cards': False,
                    'confidence': 0.0,
                    'reason': 'region_out_of_bounds',
                    'wine_red_percentage': 0.0,
                    'area': 0
                }
                
        return results
    
    def _analyze_region_for_cards(self, hsv_region: np.ndarray, region_name: str) -> Dict:
        """
        Analyze a single region for wine-red card presence.
        
        Args:
            hsv_region: HSV color space region to analyze
            region_name: Name of the region being analyzed
            
        Returns:
            Detection result dictionary
        """
        if hsv_region.size == 0:
            return {
                'has_cards': False,
                'confidence': 0.0,
                'reason': 'empty_region',
                'wine_red_percentage': 0.0,
                'area': 0
            }
        
        # Create masks for wine-red color detection
        mask1 = cv2.inRange(hsv_region, self.wine_red_lower, self.wine_red_upper)
        mask2 = cv2.inRange(hsv_region, self.alt_red_lower, self.alt_red_upper)
        
        # Combine masks
        combined_mask = cv2.bitwise_or(mask1, mask2)
        
        # Calculate wine-red percentage
        total_pixels = hsv_region.shape[0] * hsv_region.shape[1]
        wine_red_pixels = cv2.countNonZero(combined_mask)
        wine_red_percentage = (wine_red_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        # Find contours for card shape detection
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze contours for card-like shapes
        card_like_areas = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= self.min_card_area:
                # Check aspect ratio (cards are roughly rectangular)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Cards typically have aspect ratio between 0.6 and 1.8
                if 0.6 <= aspect_ratio <= 1.8:
                    card_like_areas.append(area)
        
        # Determine if cards are present
        has_cards = False
        confidence = 0.0
        reason = "no_cards_detected"
        
        if wine_red_percentage >= 15:  # At least 15% wine-red color
            has_cards = True
            confidence = min(wine_red_percentage / 50, 1.0)  # Scale confidence
            reason = "wine_red_detected"
        elif len(card_like_areas) >= 1:  # At least one card-like shape
            has_cards = True
            confidence = min(sum(card_like_areas) / (total_pixels * 0.3), 1.0)
            reason = "card_shape_detected"
        elif wine_red_percentage >= 8:  # Lower threshold with some red
            has_cards = True
            confidence = wine_red_percentage / 30
            reason = "weak_wine_red_detected"
        
        # Override confidence if below threshold
        if confidence < self.card_confidence_threshold:
            has_cards = False
            reason = f"confidence_too_low_{confidence:.2f}"
        
        return {
            'has_cards': has_cards,
            'confidence': confidence,
            'reason': reason,
            'wine_red_percentage': wine_red_percentage,
            'area': sum(card_like_areas) if card_like_areas else 0,
            'card_shapes_found': len(card_like_areas),
            'total_pixels': total_pixels,
            'wine_red_pixels': wine_red_pixels
        }
    
    def get_active_opponents(self, detection_results: Dict[str, Dict]) -> List[str]:
        """
        Get list of opponents who have cards in hand.
        
        Args:
            detection_results: Results from detect_wine_red_cards()
            
        Returns:
            List of position names with cards
        """
        active_opponents = []
        
        for region_name, result in detection_results.items():
            if result['has_cards']:
                # Extract position name from card region name
                # "Position_1_cards" -> "Position_1"
                position_name = region_name.replace('_cards', '')
                active_opponents.append(position_name)
        
        return active_opponents
    
    def count_active_players(self, detection_results: Dict[str, Dict], include_hero: bool = True) -> int:
        """
        Count total active players in the hand.
        
        Args:
            detection_results: Results from detect_wine_red_cards()
            include_hero: Whether to include hero in count
            
        Returns:
            Number of active players
        """
        active_opponents = len(self.get_active_opponents(detection_results))
        
        # Add hero if requested (hero is always active if we see their cards)
        if include_hero:
            return active_opponents + 1
        else:
            return active_opponents
    
    def visualize_detection(self, frame: np.ndarray, card_regions: Dict[str, List[int]], 
                          detection_results: Dict[str, Dict]) -> np.ndarray:
        """
        Create visualization of card detection regions and results.
        
        Args:
            frame: Original frame
            card_regions: Card detection regions
            detection_results: Detection results
            
        Returns:
            Frame with detection visualization
        """
        vis_frame = frame.copy()
        
        for region_name, coords in card_regions.items():
            x, y, w, h = coords
            result = detection_results.get(region_name, {})
            
            # Choose color based on detection result
            if result.get('has_cards', False):
                color = (0, 255, 0)  # Green for cards detected
                thickness = 3
            else:
                color = (0, 0, 255)  # Red for no cards
                thickness = 2
            
            # Draw region rectangle
            cv2.rectangle(vis_frame, (x, y), (x + w, y + h), color, thickness)
            
            # Add text label
            confidence = result.get('confidence', 0.0)
            wine_red_pct = result.get('wine_red_percentage', 0.0)
            label = f"{region_name}: {confidence:.2f} ({wine_red_pct:.1f}%)"
            
            cv2.putText(vis_frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, color, 1)
        
        return vis_frame
    
    def print_detection_summary(self, detection_results: Dict[str, Dict]):
        """Print a summary of card detection results."""
        print("\n🃏 OPPONENT CARD DETECTION:")
        print("=" * 50)
        
        active_opponents = self.get_active_opponents(detection_results)
        total_active = self.count_active_players(detection_results, include_hero=True)
        
        print(f"👥 Active Players: {total_active} (including hero)")
        print(f"🎯 Active Opponents: {len(active_opponents)}")
        
        if active_opponents:
            print(f"📍 Opponents with cards: {', '.join(active_opponents)}")
        
        print("\n📊 Detection Details:")
        for region_name, result in detection_results.items():
            status = "✅ HAS CARDS" if result['has_cards'] else "❌ NO CARDS"
            confidence = result['confidence']
            wine_red_pct = result['wine_red_percentage']
            reason = result['reason']
            
            print(f"  {region_name}: {status} (conf: {confidence:.2f}, red: {wine_red_pct:.1f}%, {reason})")
