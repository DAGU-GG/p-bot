"""
Table Reference System with OCR Integration
Uses reference images to automatically detect and map all table elements
"""

import cv2
import numpy as np
import pytesseract
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging
import os

# Configure Tesseract for this module
from tesseract_config import configure_tesseract
configure_tesseract()

logger = logging.getLogger(__name__)

@dataclass
class TableElement:
    """Represents a detected element on the poker table"""
    name: str
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    element_type: str  # 'card', 'pot', 'stack', 'button', 'action'
    confidence: float
    ocr_text: Optional[str] = None

class TableReferenceSystem:
    """Automated table layout detection using reference images and OCR"""
    
    def __init__(self):
        self.reference_layouts = {}
        self.current_layout = None
        self.ocr_config = '--psm 8 -c tessedit_char_whitelist=0123456789AKQJT♠♥♦♣hdcs$.,/'
        
        # Define standard PokerStars table elements
        self.element_patterns = {
            'hero_cards': {
                'seats': {
                    1: {'x': 0.42, 'y': 0.85, 'w': 0.16, 'h': 0.12},  # Bottom center
                    2: {'x': 0.15, 'y': 0.75, 'w': 0.16, 'h': 0.12},  # Bottom left
                    3: {'x': 0.05, 'y': 0.50, 'w': 0.16, 'h': 0.12},  # Left
                    4: {'x': 0.15, 'y': 0.25, 'w': 0.16, 'h': 0.12},  # Top left
                    5: {'x': 0.42, 'y': 0.15, 'w': 0.16, 'h': 0.12},  # Top center
                    6: {'x': 0.69, 'y': 0.25, 'w': 0.16, 'h': 0.12},  # Top right
                    7: {'x': 0.79, 'y': 0.50, 'w': 0.16, 'h': 0.12},  # Right
                    8: {'x': 0.69, 'y': 0.75, 'w': 0.16, 'h': 0.12},  # Bottom right
                    9: {'x': 0.42, 'y': 0.60, 'w': 0.16, 'h': 0.12},  # Center (6-max)
                }
            },
            'community_cards': {
                'flop1': {'x': 0.35, 'y': 0.45, 'w': 0.08, 'h': 0.12},
                'flop2': {'x': 0.44, 'y': 0.45, 'w': 0.08, 'h': 0.12},
                'flop3': {'x': 0.53, 'y': 0.45, 'w': 0.08, 'h': 0.12},
                'turn':  {'x': 0.62, 'y': 0.45, 'w': 0.08, 'h': 0.12},
                'river': {'x': 0.71, 'y': 0.45, 'w': 0.08, 'h': 0.12},
            },
            'pot_area': {'x': 0.45, 'y': 0.35, 'w': 0.10, 'h': 0.05},
            'dealer_button': {'radius': 0.02, 'color_range': ([20, 100, 100], [30, 255, 255])},  # Yellow
            'action_buttons': {
                'fold':  {'x': 0.55, 'y': 0.90, 'w': 0.08, 'h': 0.05},
                'call':  {'x': 0.64, 'y': 0.90, 'w': 0.08, 'h': 0.05},
                'raise': {'x': 0.73, 'y': 0.90, 'w': 0.08, 'h': 0.05},
            }
        }
        
    def create_reference_layout(self, screenshot: np.ndarray, layout_name: str = "default") -> Dict:
        """Create a reference layout from a screenshot"""
        logger.info(f"Creating reference layout: {layout_name}")
        
        height, width = screenshot.shape[:2]
        detected_elements = {}
        
        # Detect all table elements
        detected_elements['table_size'] = (width, height)
        detected_elements['elements'] = []
        
        # 1. Detect cards using color and shape analysis
        cards = self._detect_cards(screenshot)
        detected_elements['elements'].extend(cards)
        
        # 2. Detect pot area using OCR
        pot_info = self._detect_pot(screenshot)
        if pot_info:
            detected_elements['elements'].append(pot_info)
        
        # 3. Detect player stacks using OCR
        stacks = self._detect_stacks(screenshot)
        detected_elements['elements'].extend(stacks)
        
        # 4. Detect dealer button
        dealer_pos = self._detect_dealer_button(screenshot)
        if dealer_pos:
            detected_elements['dealer_position'] = dealer_pos
        
        # 5. Detect action buttons
        buttons = self._detect_action_buttons(screenshot)
        detected_elements['action_buttons'] = buttons
        
        # Save reference layout
        self.reference_layouts[layout_name] = detected_elements
        self._save_reference(layout_name, detected_elements)
        
        return detected_elements
    
    def _detect_cards(self, img: np.ndarray) -> List[TableElement]:
        """Detect all cards on the table using color and shape analysis"""
        cards = []
        height, width = img.shape[:2]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define card color ranges (white/light backgrounds)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        # Create mask for card-like objects
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by card-like properties
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000 or area > 50000:  # Filter by size
                continue
                
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check aspect ratio (cards are typically 1.4:1)
            aspect_ratio = h / w if w > 0 else 0
            if not (1.2 <= aspect_ratio <= 1.6):
                continue
            
            # Extract card region for OCR
            card_roi = img[y:y+h, x:x+w]
            
            # Try to read card value with OCR
            card_text = self._ocr_card(card_roi)
            
            # Determine card type
            if y < height * 0.6:  # Upper half - likely community cards
                card_type = 'community_card'
            else:  # Lower half - likely player cards
                card_type = 'player_card'
            
            cards.append(TableElement(
                name=f"{card_type}_{len(cards)}",
                bbox=(x, y, w, h),
                element_type='card',
                confidence=0.8,
                ocr_text=card_text
            ))
        
        return cards
    
    def _ocr_card(self, card_img: np.ndarray) -> str:
        """OCR a card image to extract rank and suit"""
        try:
            # Preprocess for better OCR
            gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
            
            # Focus on top-left corner for rank/suit
            h, w = gray.shape
            rank_area = gray[0:int(h*0.3), 0:int(w*0.3)]
            
            # Enhance contrast
            _, binary = cv2.threshold(rank_area, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR with card-specific config
            text = pytesseract.image_to_string(
                binary, 
                config='--psm 8 -c tessedit_char_whitelist=23456789TJQKA♠♥♦♣'
            ).strip()
            
            return text
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""
    
    def _detect_pot(self, img: np.ndarray) -> Optional[TableElement]:
        """Detect pot area and read pot size"""
        height, width = img.shape[:2]
        
        # Expected pot location (center of table)
        pot_region = self.element_patterns['pot_area']
        x = int(pot_region['x'] * width)
        y = int(pot_region['y'] * height)
        w = int(pot_region['w'] * width)
        h = int(pot_region['h'] * height)
        
        # Extract pot region
        pot_roi = img[y:y+h, x:x+w]
        
        # OCR for pot amount
        pot_text = self._ocr_money(pot_roi)
        
        if pot_text:
            return TableElement(
                name="pot",
                bbox=(x, y, w, h),
                element_type='pot',
                confidence=0.9,
                ocr_text=pot_text
            )
        
        return None
    
    def _ocr_money(self, roi: np.ndarray) -> str:
        """OCR money amounts (pot, stacks)"""
        try:
            # Preprocess
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Enhance for white text on dark background
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # OCR with money-specific config
            text = pytesseract.image_to_string(
                binary,
                config='--psm 7 -c tessedit_char_whitelist=0123456789$.,KMB'
            ).strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Money OCR error: {e}")
            return ""
    
    def _detect_stacks(self, img: np.ndarray) -> List[TableElement]:
        """Detect player chip stacks"""
        stacks = []
        height, width = img.shape[:2]
        
        # Check each potential seat position
        for seat, pos in self.element_patterns['hero_cards']['seats'].items():
            # Stack is usually below cards
            x = int(pos['x'] * width)
            y = int((pos['y'] + 0.12) * height)
            w = int(pos['w'] * width)
            h = int(0.05 * height)
            
            # Ensure within bounds
            if y + h > height:
                continue
                
            stack_roi = img[y:y+h, x:x+w]
            stack_text = self._ocr_money(stack_roi)
            
            if stack_text and any(c.isdigit() for c in stack_text):
                stacks.append(TableElement(
                    name=f"stack_seat_{seat}",
                    bbox=(x, y, w, h),
                    element_type='stack',
                    confidence=0.7,
                    ocr_text=stack_text
                ))
        
        return stacks
    
    def _detect_dealer_button(self, img: np.ndarray) -> Optional[int]:
        """Detect dealer button position"""
        # Convert to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Yellow color range for dealer button
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        
        # Create mask
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Find circular objects
        circles = cv2.HoughCircles(
            mask,
            cv2.HOUGH_GRADIENT,
            1,
            20,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=30
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # Find which seat the button is closest to
            # ... (calculate based on position)
            return 1  # Placeholder
        
        return None
    
    def _detect_action_buttons(self, img: np.ndarray) -> Dict:
        """Detect fold/call/raise buttons"""
        buttons = {}
        height, width = img.shape[:2]
        
        for button_name, pos in self.element_patterns['action_buttons'].items():
            x = int(pos['x'] * width)
            y = int(pos['y'] * height)
            w = int(pos['w'] * width)
            h = int(pos['h'] * height)
            
            # Check if region has button-like properties
            button_roi = img[y:y+h, x:x+w]
            
            # Simple color check for buttons
            avg_color = np.mean(button_roi, axis=(0, 1))
            
            buttons[button_name] = {
                'bbox': (x, y, w, h),
                'visible': np.max(avg_color) > 100  # Simple visibility check
            }
        
        return buttons
    
    def auto_calibrate_from_screenshot(self, screenshot: np.ndarray) -> Dict:
        """Automatically calibrate all regions from a screenshot"""
        logger.info("Starting auto-calibration from screenshot")
        
        # Create reference layout
        layout = self.create_reference_layout(screenshot, "auto_detected")
        
        # Convert to region format for the bot
        regions = {}
        
        # Map detected elements to bot regions
        for element in layout['elements']:
            if element.element_type == 'card':
                if 'community' in element.name:
                    # Map to community card positions
                    card_num = len([e for e in regions if 'community' in e]) + 1
                    regions[f'card_{card_num}'] = {
                        'x_percent': element.bbox[0] / layout['table_size'][0],
                        'y_percent': element.bbox[1] / layout['table_size'][1],
                        'width_percent': element.bbox[2] / layout['table_size'][0],
                        'height_percent': element.bbox[3] / layout['table_size'][1]
                    }
                elif 'player' in element.name:
                    # Map to hero cards
                    card_num = len([e for e in regions if 'hero' in e]) + 1
                    if card_num <= 2:  # Only hero's 2 cards
                        regions[f'hero_card_{card_num}'] = {
                            'x_percent': element.bbox[0] / layout['table_size'][0],
                            'y_percent': element.bbox[1] / layout['table_size'][1],
                            'width_percent': element.bbox[2] / layout['table_size'][0],
                            'height_percent': element.bbox[3] / layout['table_size'][1]
                        }
            
            elif element.element_type == 'pot':
                regions['pot'] = {
                    'x_percent': element.bbox[0] / layout['table_size'][0],
                    'y_percent': element.bbox[1] / layout['table_size'][1],
                    'width_percent': element.bbox[2] / layout['table_size'][0],
                    'height_percent': element.bbox[3] / layout['table_size'][1],
                    'ocr_text': element.ocr_text
                }
        
        # Save calibrated regions
        self._save_regions(regions)
        
        return regions
    
    def _save_reference(self, name: str, layout: Dict):
        """Save reference layout to file"""
        filename = f"table_reference_{name}.json"
        with open(filename, 'w') as f:
            # Convert numpy types to native Python types
            json_safe = self._make_json_serializable(layout)
            json.dump(json_safe, f, indent=2)
        logger.info(f"Saved reference layout to {filename}")
    
    def _save_regions(self, regions: Dict):
        """Save calibrated regions"""
        with open('regions_auto_calibrated.json', 'w') as f:
            json.dump(regions, f, indent=2)
        logger.info("Saved auto-calibrated regions")
    
    def _make_json_serializable(self, obj):
        """Convert numpy types to Python native types"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, bool):
            return obj
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(v) for v in obj]
        elif isinstance(obj, TableElement):
            return {
                'name': obj.name,
                'bbox': obj.bbox,
                'element_type': obj.element_type,
                'confidence': obj.confidence,
                'ocr_text': obj.ocr_text
            }
        return obj

def test_auto_calibration():
    """Test the auto-calibration system"""
    # Load a test screenshot
    screenshot = cv2.imread('test_table.png')
    
    if screenshot is None:
        print("Please provide a screenshot named 'test_table.png'")
        return
    
    # Initialize system
    table_ref = TableReferenceSystem()
    
    # Auto-calibrate
    regions = table_ref.auto_calibrate_from_screenshot(screenshot)
    
    # Display results
    print(f"Auto-detected {len(regions)} regions:")
    for name, region in regions.items():
        print(f"  {name}: {region}")
    
    # Visualize detected regions
    vis_img = screenshot.copy()
    height, width = vis_img.shape[:2]
    
    for name, region in regions.items():
        x = int(region['x_percent'] * width)
        y = int(region['y_percent'] * height)
        w = int(region['width_percent'] * width)
        h = int(region['height_percent'] * height)
        
        # Draw rectangle
        color = (0, 255, 0) if 'hero' in name else (255, 0, 0) if 'card' in name else (0, 0, 255)
        cv2.rectangle(vis_img, (x, y), (x+w, y+h), color, 2)
        cv2.putText(vis_img, name, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Save visualization
    cv2.imwrite('auto_calibration_result.png', vis_img)
    print("Saved visualization to auto_calibration_result.png")

if __name__ == "__main__":
    test_auto_calibration()
