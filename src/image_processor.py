"""
PokerStars Bot - Stage 2: Image Processing and Recognition
This module handles table image capture, region identification, and basic element detection.
"""

import cv2
import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from PIL import Image
import os

@dataclass
class TableRegion:
    """Defines a region of interest on the poker table."""
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str

@dataclass
class GameState:
    """Represents the current state of the poker game."""
    timestamp: float
    table_detected: bool
    dealer_button_position: Optional[int]
    pot_amount: Optional[str]
    community_cards_count: int
    player_cards_detected: bool
    active_players: int
    current_bet: Optional[str]

class ImageProcessor:
    """
    Handles all image processing tasks for the poker bot including
    region identification, preprocessing, and basic element detection.
    """
    
    def __init__(self):
        """Initialize the image processor with default settings."""
        self.logger = logging.getLogger(__name__)
        
        # Table regions - these will be calibrated based on table size
        self.regions = {}
        self.table_calibrated = False
        self.table_template = None
        
        # Image processing parameters
        self.card_detection_threshold = 0.7
        self.text_detection_threshold = 0.8
        
        # Create directories for debug images
        os.makedirs("debug_images", exist_ok=True)
        os.makedirs("regions", exist_ok=True)
        
        self.logger.info("Image processor initialized")
    
    def calibrate_table_regions(self, table_image: np.ndarray) -> bool:
        """
        Calibrate table regions based on the captured table image.
        This identifies key areas like cards, pot, player positions, etc.
        
        Args:
            table_image: The captured table screenshot
            
        Returns:
            True if calibration successful, False otherwise
        """
        try:
            # Use RegionLoader to get the actual calibrated regions
            import sys
            import os
            src_path = os.path.dirname(__file__)
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            from region_loader import RegionLoader
            region_loader = RegionLoader()
            saved_regions = region_loader.load_regions()
            
            if not saved_regions:
                self.logger.error("❌ No saved regions found - cannot calibrate")
                return False
            
            height, width = table_image.shape[:2]
            self.logger.info(f"Calibrating table regions for {width}x{height} table using SAVED regions")
            
            # Convert saved regions to the format expected by image processor
            region_definitions = {}
            for region_name, region_data in saved_regions.items():
                region_definitions[region_name] = {
                    'x_percent': region_data['x'],
                    'y_percent': region_data['y'], 
                    'width_percent': region_data['width'],
                    'height_percent': region_data['height'],
                    'description': f'Calibrated region: {region_name}'
                }
            
            # Convert percentage-based regions to pixel coordinates
            for region_name, region_def in region_definitions.items():
                x = int(width * region_def['x_percent'])
                y = int(height * region_def['y_percent'])
                w = int(width * region_def['width_percent'])
                h = int(height * region_def['height_percent'])
                
                self.regions[region_name] = TableRegion(
                    name=region_name,
                    x=x, y=y, width=w, height=h,
                    description=region_def['description']
                )
            
            # Save calibration visualization
            self._save_calibration_visualization(table_image)
            
            self.table_calibrated = True
            self.logger.info(f"Table calibration complete - {len(self.regions)} regions defined")
            return True
            
        except Exception as e:
            self.logger.error(f"Error calibrating table regions: {e}")
            return False
    
    def _save_calibration_visualization(self, table_image: np.ndarray) -> None:
        """Save a visualization of the calibrated regions for debugging."""
        try:
            # Create a copy for visualization
            vis_image = table_image.copy()
            
            # Draw rectangles for each region
            colors = [
                (0, 255, 0),    # Green
                (255, 0, 0),    # Blue
                (0, 0, 255),    # Red
                (255, 255, 0),  # Cyan
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Yellow
                (128, 0, 128),  # Purple
                (255, 165, 0),  # Orange
                (0, 128, 0),    # Dark Green
                (128, 128, 0),  # Olive
            ]
            
            for i, (region_name, region) in enumerate(self.regions.items()):
                color = colors[i % len(colors)]
                
                # Draw rectangle
                cv2.rectangle(vis_image, 
                            (region.x, region.y), 
                            (region.x + region.width, region.y + region.height), 
                            color, 2)
                
                # Add label
                cv2.putText(vis_image, region_name, 
                          (region.x, region.y - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Save visualization
            timestamp = int(time.time())
            filename = f"debug_images/table_calibration_{timestamp}.png"
            cv2.imwrite(filename, vis_image)
            self.logger.info(f"Calibration visualization saved: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving calibration visualization: {e}")
    
    def preprocess_image(self, image: np.ndarray, region_name: str = "full") -> Dict[str, np.ndarray]:
        """
        Apply various preprocessing techniques to the image for better recognition.
        
        Args:
            image: Input image to preprocess
            region_name: Name of the region being processed
            
        Returns:
            Dictionary containing different preprocessed versions
        """
        try:
            processed = {}
            
            # Original image
            processed['original'] = image.copy()
            
            # Grayscale conversion
            if len(image.shape) == 3:
                processed['grayscale'] = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                processed['grayscale'] = image.copy()
            
            # HSV color space (useful for color-based detection)
            if len(image.shape) == 3:
                processed['hsv'] = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Apply Gaussian blur to reduce noise
            processed['blurred'] = cv2.GaussianBlur(processed['grayscale'], (5, 5), 0)
            
            # Edge detection using Canny
            processed['edges'] = cv2.Canny(processed['blurred'], 50, 150)
            
            # Adaptive thresholding for text detection
            processed['threshold'] = cv2.adaptiveThreshold(
                processed['grayscale'], 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up the image
            kernel = np.ones((3, 3), np.uint8)
            processed['morphology'] = cv2.morphologyEx(
                processed['threshold'], cv2.MORPH_CLOSE, kernel
            )
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image for {region_name}: {e}")
            return {'original': image}
    
    def detect_cards(self, image: np.ndarray, region_name: str) -> Dict[str, Any]:
        """
        Detect cards in the given image region.
        
        Args:
            image: Image region to analyze
            region_name: Name of the region being analyzed
            
        Returns:
            Dictionary with card detection results
        """
        try:
            # Preprocess the image
            processed = self.preprocess_image(image, region_name)
            
            # Use edge detection to find rectangular shapes (cards)
            edges = processed['edges']
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            card_candidates = []
            
            for contour in contours:
                # Calculate contour area
                area = cv2.contourArea(contour)
                
                # Filter by area (cards should be reasonably sized)
                if area > 500 and area < 10000:
                    # Approximate the contour to a polygon
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    # Cards should be roughly rectangular (4 corners)
                    if len(approx) >= 4:
                        # Calculate bounding rectangle
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Check aspect ratio (cards have specific proportions)
                        aspect_ratio = float(w) / h
                        if 0.6 < aspect_ratio < 0.8:  # Typical card aspect ratio
                            card_candidates.append({
                                'contour': contour,
                                'area': area,
                                'bbox': (x, y, w, h),
                                'aspect_ratio': aspect_ratio
                            })
            
            # Sort by area (larger cards are more likely to be actual cards)
            card_candidates.sort(key=lambda x: x['area'], reverse=True)
            
            result = {
                'cards_detected': len(card_candidates),
                'candidates': card_candidates[:5],  # Keep top 5 candidates
                'region': region_name,
                'timestamp': time.time()
            }
            
            self.logger.debug(f"Detected {len(card_candidates)} card candidates in {region_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error detecting cards in {region_name}: {e}")
            return {'cards_detected': 0, 'candidates': [], 'region': region_name}
    
    def detect_dealer_button(self, image: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect the dealer button position on the table.
        
        Args:
            image: Table image to search
            
        Returns:
            (x, y) coordinates of dealer button if found, None otherwise
        """
        try:
            if 'dealer_button' not in self.regions:
                return None
            
            # Extract dealer button search region
            region = self.regions['dealer_button']
            roi = image[region.y:region.y + region.height, 
                       region.x:region.x + region.width]
            
            # Preprocess for circular object detection
            processed = self.preprocess_image(roi, 'dealer_button')
            gray = processed['grayscale']
            
            # Use HoughCircles to detect circular objects (dealer button)
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                param1=50, param2=30, minRadius=10, maxRadius=50
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                
                # Return the first (most confident) circle
                if len(circles) > 0:
                    x, y, r = circles[0]
                    # Convert back to full image coordinates
                    abs_x = region.x + x
                    abs_y = region.y + y
                    
                    self.logger.debug(f"Dealer button detected at ({abs_x}, {abs_y})")
                    return (abs_x, abs_y)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting dealer button: {e}")
            return None
    
    def detect_text_in_region(self, image: np.ndarray, region_name: str) -> str:
        """
        Detect and extract text from a specific region (for pot amounts, bets, etc.).
        
        Args:
            image: Image region to analyze
            region_name: Name of the region
            
        Returns:
            Extracted text string
        """
        try:
            # Preprocess for text detection
            processed = self.preprocess_image(image, region_name)
            
            # Use threshold image for better text recognition
            text_image = processed['threshold']
            
            # For now, we'll use basic contour analysis to detect text-like regions
            # In a full implementation, you'd use OCR libraries like pytesseract
            contours, _ = cv2.findContours(text_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 2000:  # Text-sized regions
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    if 0.2 < aspect_ratio < 5.0:  # Text-like aspect ratio
                        text_regions += 1
            
            # Placeholder text detection - in real implementation use OCR
            if text_regions > 0:
                return f"TEXT_DETECTED_{text_regions}_REGIONS"
            else:
                return "NO_TEXT"
                
        except Exception as e:
            self.logger.error(f"Error detecting text in {region_name}: {e}")
            return "ERROR"
    
    def analyze_table_state(self, table_image: np.ndarray) -> GameState:
        """
        Analyze the complete table state from the captured image.
        
        Args:
            table_image: Full table screenshot
            
        Returns:
            GameState object with detected information
        """
        try:
            timestamp = time.time()
            
            # Ensure table is calibrated
            if not self.table_calibrated:
                self.calibrate_table_regions(table_image)
            
            # Initialize game state
            game_state = GameState(
                timestamp=timestamp,
                table_detected=True,
                dealer_button_position=None,
                pot_amount=None,
                community_cards_count=0,
                player_cards_detected=False,
                active_players=0,
                current_bet=None
            )
            
            # Detect dealer button
            dealer_pos = self.detect_dealer_button(table_image)
            if dealer_pos:
                # Convert position to player number (simplified)
                game_state.dealer_button_position = 1  # Placeholder
            
            # Analyze player cards
            if 'player_cards' in self.regions:
                region = self.regions['player_cards']
                cards_roi = table_image[region.y:region.y + region.height,
                                      region.x:region.x + region.width]
                
                card_detection = self.detect_cards(cards_roi, 'player_cards')
                game_state.player_cards_detected = card_detection['cards_detected'] >= 2
            
            # Analyze community cards
            if 'community_cards' in self.regions:
                region = self.regions['community_cards']
                community_roi = table_image[region.y:region.y + region.height,
                                          region.x:region.x + region.width]
                
                card_detection = self.detect_cards(community_roi, 'community_cards')
                game_state.community_cards_count = min(card_detection['cards_detected'], 5)
            
            # Detect pot amount
            if 'pot_area' in self.regions:
                region = self.regions['pot_area']
                pot_roi = table_image[region.y:region.y + region.height,
                                    region.x:region.x + region.width]
                
                pot_text = self.detect_text_in_region(pot_roi, 'pot_area')
                game_state.pot_amount = pot_text
            
            # Count active players (simplified - check each player region)
            active_count = 0
            for i in range(1, 7):  # Check players 1-6
                player_region_name = f'player_{i}'
                if player_region_name in self.regions:
                    region = self.regions[player_region_name]
                    player_roi = table_image[region.y:region.y + region.height,
                                           region.x:region.x + region.width]
                    
                    # Simple activity detection based on image variance
                    gray_roi = cv2.cvtColor(player_roi, cv2.COLOR_BGR2GRAY) if len(player_roi.shape) == 3 else player_roi
                    variance = np.var(gray_roi)
                    
                    if variance > 100:  # Threshold for "active" player area
                        active_count += 1
            
            game_state.active_players = active_count
            
            # Save debug information
            self._save_analysis_debug(table_image, game_state)
            
            self.logger.info(f"Table analysis complete: {active_count} active players, "
                           f"{game_state.community_cards_count} community cards, "
                           f"player cards: {game_state.player_cards_detected}")
            
            return game_state
            
        except Exception as e:
            self.logger.error(f"Error analyzing table state: {e}")
            return GameState(
                timestamp=time.time(),
                table_detected=False,
                dealer_button_position=None,
                pot_amount=None,
                community_cards_count=0,
                player_cards_detected=False,
                active_players=0,
                current_bet=None
            )
    
    def _save_analysis_debug(self, table_image: np.ndarray, game_state: GameState) -> None:
        """Save debug images showing the analysis results."""
        try:
            # Create debug visualization
            debug_image = table_image.copy()
            
            # Draw detected regions with status
            if 'player_cards' in self.regions:
                region = self.regions['player_cards']
                color = (0, 255, 0) if game_state.player_cards_detected else (0, 0, 255)
                cv2.rectangle(debug_image, 
                            (region.x, region.y), 
                            (region.x + region.width, region.y + region.height), 
                            color, 2)
                cv2.putText(debug_image, f"Cards: {game_state.player_cards_detected}", 
                          (region.x, region.y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            if 'community_cards' in self.regions:
                region = self.regions['community_cards']
                color = (255, 0, 0)
                cv2.rectangle(debug_image, 
                            (region.x, region.y), 
                            (region.x + region.width, region.y + region.height), 
                            color, 2)
                cv2.putText(debug_image, f"Community: {game_state.community_cards_count}", 
                          (region.x, region.y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Add game state info
            info_text = [
                f"Active Players: {game_state.active_players}",
                f"Community Cards: {game_state.community_cards_count}",
                f"Player Cards: {game_state.player_cards_detected}",
                f"Pot: {game_state.pot_amount}",
                f"Dealer: {game_state.dealer_button_position}"
            ]
            
            for i, text in enumerate(info_text):
                cv2.putText(debug_image, text, (10, 30 + i * 25), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Save debug image
            timestamp = int(time.time())
            filename = f"debug_images/analysis_{timestamp}.png"
            cv2.imwrite(filename, debug_image)
            
        except Exception as e:
            self.logger.error(f"Error saving analysis debug: {e}")
    
    def extract_region(self, image: np.ndarray, region_name: str) -> Optional[np.ndarray]:
        """
        Extract a specific region from the table image.
        
        Args:
            image: Full table image
            region_name: Name of the region to extract
            
        Returns:
            Extracted region image or None if region not found
        """
        try:
            if region_name not in self.regions:
                self.logger.warning(f"Region '{region_name}' not found")
                return None
            
            region = self.regions[region_name]
            roi = image[region.y:region.y + region.height,
                       region.x:region.x + region.width]
            
            return roi.copy()
            
        except Exception as e:
            self.logger.error(f"Error extracting region {region_name}: {e}")
            return None
    
    def get_region_info(self) -> Dict[str, Dict]:
        """
        Get information about all calibrated regions.
        
        Returns:
            Dictionary with region information
        """
        region_info = {}
        for name, region in self.regions.items():
            region_info[name] = {
                'coordinates': (region.x, region.y),
                'size': (region.width, region.height),
                'description': region.description
            }
        return region_info