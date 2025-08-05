"""
Integration Script for Enhanced OCR and Auto-Calibration
Upgrades existing poker bot with new table reference and OCR systems
"""

import os
import sys
import cv2
import numpy as np
import logging
from typing import Optional, Dict, Any

# Constants
ENHANCED_REGIONS_CONFIG = 'enhanced_regions_config.json'

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import the new systems
from table_reference_system import TableReferenceSystem
from enhanced_ocr_recognition import EnhancedOCRCardRecognition

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedPokerBot:
    """Enhanced poker bot with auto-calibration and advanced OCR"""
    
    def __init__(self, original_bot=None):
        """Initialize with optional original bot to upgrade"""
        self.original_bot = original_bot
        
        # Initialize new systems
        self.table_ref = TableReferenceSystem()
        self.ocr_recognizer = EnhancedOCRCardRecognition()
        
        # Bot state
        self.regions = {}
        self.auto_calibrated = False
        self.last_screenshot = None
        
        # Import window capture if available
        try:
            if original_bot and hasattr(original_bot, 'window_capture'):
                self.window_capture = original_bot.window_capture
            else:
                # Import window capture system
                from src.window_capture import PokerStarsWindowCapture
                self.window_capture = PokerStarsWindowCapture()
        except ImportError:
            logger.warning("Window capture not available - will need manual screenshots")
            self.window_capture = None
        
        logger.info("Enhanced Poker Bot initialized")
    
    def auto_calibrate(self, screenshot: Optional[np.ndarray] = None) -> bool:
        """Auto-calibrate the bot using table reference system"""
        try:
            # Capture screenshot if not provided
            if screenshot is None:
                if self.window_capture:
                    screenshot = self.window_capture.capture_window()
                else:
                    logger.error("No screenshot provided and no window capture available")
                    return False
            
            if screenshot is None:
                logger.error("Failed to capture screenshot for calibration")
                return False
            
            # Save the screenshot for reference
            cv2.imwrite('calibration_screenshot.png', screenshot)
            logger.info("Saved calibration screenshot as 'calibration_screenshot.png'")
            
            # Auto-calibrate using table reference system
            logger.info("Starting auto-calibration...")
            self.regions = self.table_ref.auto_calibrate_from_screenshot(screenshot)
            
            if self.regions:
                self.auto_calibrated = True
                logger.info(f"Auto-calibration successful! Detected {len(self.regions)} regions:")
                for name, region in self.regions.items():
                    logger.info(f"  {name}: x={region['x_percent']:.3f}, y={region['y_percent']:.3f}")
                
                # Save regions for future use
                self._save_regions_config()
                return True
            else:
                logger.error("Auto-calibration failed - no regions detected")
                return False
                
        except Exception as e:
            logger.error(f"Auto-calibration error: {e}")
            return False
    
    def analyze_game_state(self, screenshot: Optional[np.ndarray] = None, debug: bool = True) -> Optional[Dict[str, Any]]:
        """Enhanced game state analysis with auto-calibration and advanced OCR"""
        try:
            # Get screenshot
            screenshot = self._get_screenshot(screenshot)
            if screenshot is None:
                return None
            
            self.last_screenshot = screenshot
            
            # Ensure calibration
            if not self._ensure_calibration(screenshot):
                return None
            
            # Analyze regions
            return self._analyze_regions(screenshot, debug)
            
        except Exception as e:
            logger.error(f"Enhanced game state analysis error: {e}")
            return None
    
    def _get_screenshot(self, screenshot: Optional[np.ndarray]) -> Optional[np.ndarray]:
        """Get screenshot from parameter or capture from window"""
        if screenshot is None:
            if self.window_capture:
                screenshot = self.window_capture.capture_window()
            else:
                logger.error("No screenshot provided and no window capture available")
                return None
        
        if screenshot is None:
            logger.error("Failed to capture screenshot")
            return None
        
        return screenshot
    
    def _ensure_calibration(self, screenshot: np.ndarray) -> bool:
        """Ensure regions are calibrated, auto-calibrate if needed"""
        if not self.regions:
            logger.info("No regions configured, attempting auto-calibration...")
            if not self.auto_calibrate(screenshot):
                logger.error("Auto-calibration failed")
                return False
        return True
    
    def _analyze_regions(self, screenshot: np.ndarray, debug: bool) -> Dict[str, Any]:
        """Analyze all regions and build game state"""
        hero_cards = []
        community_cards = []
        other_info = {}
        
        height, width = screenshot.shape[:2]
        
        # Process each region
        for region_name, region_data in self.regions.items():
            region_result = self._process_single_region(
                region_name, region_data, screenshot, width, height, debug
            )
            
            if region_result:
                self._add_result_to_state(region_result, hero_cards, community_cards, other_info)
        
        # Build comprehensive result
        return {
            'hero_cards': hero_cards if len(hero_cards) > 0 else None,
            'community_cards': community_cards,
            'valid': len(hero_cards) == 2 or len(hero_cards) == 0,
            'auto_calibrated': self.auto_calibrated,
            'screenshot_shape': screenshot.shape,
            'regions_count': len(self.regions),
            'other_info': other_info
        }
    
    def _process_single_region(self, region_name: str, region_data: Dict, screenshot: np.ndarray, 
                             width: int, height: int, debug: bool) -> Optional[Dict]:
        """Process a single region and return results"""
        try:
            # Calculate absolute coordinates
            x = int(region_data['x_percent'] * width)
            y = int(region_data['y_percent'] * height)
            w = int(region_data['width_percent'] * width)
            h = int(region_data['height_percent'] * height)
            
            # Ensure coordinates are within bounds
            if not (0 <= x < width and 0 <= y < height and x+w <= width and y+h <= height):
                logger.warning(f"Region {region_name} coordinates out of bounds")
                return None
            
            # Extract region image
            region_img = screenshot[y:y+h, x:x+w]
            
            if debug:
                # Save region image for debugging
                debug_filename = f"debug_region_{region_name}.png"
                cv2.imwrite(debug_filename, region_img)
            
            # Process based on region type
            return self._recognize_region_content(region_name, region_data, region_img, debug)
            
        except Exception as e:
            logger.error(f"Error processing region {region_name}: {e}")
            return None
    
    def _recognize_region_content(self, region_name: str, region_data: Dict, 
                                region_img: np.ndarray, debug: bool) -> Optional[Dict]:
        """Recognize content of a region based on its type"""
        if 'hero' in region_name and 'card' in region_name:
            return self._recognize_hero_card(region_img, debug)
        elif 'card' in region_name and 'hero' not in region_name:
            return self._recognize_community_card(region_img, debug)
        elif 'pot' in region_name:
            return self._recognize_pot_info(region_data)
        
        return None
    
    def _recognize_hero_card(self, region_img: np.ndarray, debug: bool) -> Optional[Dict]:
        """Recognize hero card from region image"""
        result = self.ocr_recognizer.recognize_card(region_img, debug=debug)
        if result:
            card_str = f"{result.rank}{result.suit}"
            logger.info(f"Hero card detected: {card_str} (confidence: {result.confidence:.2f})")
            return {'type': 'hero_card', 'card': card_str, 'confidence': result.confidence}
        return None
    
    def _recognize_community_card(self, region_img: np.ndarray, debug: bool) -> Optional[Dict]:
        """Recognize community card from region image"""
        result = self.ocr_recognizer.recognize_card(region_img, debug=debug)
        if result:
            card_str = f"{result.rank}{result.suit}"
            logger.info(f"Community card detected: {card_str} (confidence: {result.confidence:.2f})")
            return {'type': 'community_card', 'card': card_str, 'confidence': result.confidence}
        return None
    
    def _recognize_pot_info(self, region_data: Dict) -> Dict:
        """Recognize pot information from region"""
        pot_info = {'type': 'pot', 'region': region_data}
        if 'ocr_text' in region_data:
            pot_info['text'] = region_data['ocr_text']
        return pot_info
    
    def _add_result_to_state(self, region_result: Dict, hero_cards: list, 
                           community_cards: list, other_info: dict) -> None:
        """Add region result to appropriate state collections"""
        result_type = region_result.get('type')
        
        if result_type == 'hero_card':
            hero_cards.append(region_result['card'])
        elif result_type == 'community_card':
            community_cards.append(region_result['card'])
        elif result_type == 'pot':
            other_info.update(region_result)
    
    def _save_regions_config(self):
        """Save regions configuration to file"""
        try:
            import json
            config = {
                'regions': self.regions,
                'auto_calibrated': self.auto_calibrated,
                'timestamp': int(time.time()) if 'time' in globals() else 0
            }
            
            with open(ENHANCED_REGIONS_CONFIG, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Saved enhanced regions configuration")
            
        except Exception as e:
            logger.error(f"Failed to save regions config: {e}")
    
    def load_regions_config(self) -> bool:
        """Load regions configuration from file"""
        try:
            import json
            
            if os.path.exists(ENHANCED_REGIONS_CONFIG):
                with open(ENHANCED_REGIONS_CONFIG, 'r') as f:
                    config = json.load(f)
                
                self.regions = config.get('regions', {})
                self.auto_calibrated = config.get('auto_calibrated', False)
                
                logger.info(f"Loaded {len(self.regions)} regions from config")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to load regions config: {e}")
            return False
    
    def create_visualization(self, screenshot: Optional[np.ndarray] = None) -> np.ndarray:
        """Create visualization of detected regions"""
        if screenshot is None:
            screenshot = self.last_screenshot
        
        if screenshot is None or not self.regions:
            logger.error("No screenshot or regions available for visualization")
            return None
        
        vis_img = screenshot.copy()
        height, width = vis_img.shape[:2]
        
        # Draw regions
        for name, region in self.regions.items():
            x = int(region['x_percent'] * width)
            y = int(region['y_percent'] * height)
            w = int(region['width_percent'] * width)
            h = int(region['height_percent'] * height)
            
            # Choose color based on region type
            if 'hero' in name:
                color = (0, 255, 0)  # Green for hero cards
            elif 'card' in name:
                color = (255, 0, 0)  # Red for community cards
            elif 'pot' in name:
                color = (0, 0, 255)  # Blue for pot
            else:
                color = (255, 255, 0)  # Yellow for other
            
            # Draw rectangle
            cv2.rectangle(vis_img, (x, y), (x+w, y+h), color, 2)
            
            # Add label
            cv2.putText(vis_img, name, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Save visualization
        cv2.imwrite('enhanced_bot_visualization.png', vis_img)
        logger.info("Saved visualization as 'enhanced_bot_visualization.png'")
        
        return vis_img

def upgrade_existing_bot(original_bot):
    """Upgrade an existing bot with enhanced features"""
    logger.info("Upgrading existing bot with enhanced OCR and auto-calibration...")
    
    # Create enhanced wrapper
    enhanced_bot = EnhancedPokerBot(original_bot)
    
    # Try to load existing regions
    enhanced_bot.load_regions_config()
    
    # Replace the original bot's analyze method
    if hasattr(original_bot, 'analyze_game_state'):
        original_bot.original_analyze = original_bot.analyze_game_state
        original_bot.analyze_game_state = enhanced_bot.analyze_game_state
        logger.info("Replaced original analyze_game_state method")
    
    # Add enhanced methods to original bot
    original_bot.auto_calibrate = enhanced_bot.auto_calibrate
    original_bot.create_visualization = enhanced_bot.create_visualization
    original_bot.enhanced_ocr = enhanced_bot.ocr_recognizer
    original_bot.table_ref = enhanced_bot.table_ref
    
    logger.info("Bot upgrade complete!")
    return enhanced_bot

def test_enhanced_system():
    """Test the enhanced system with a screenshot"""
    # Create test bot
    enhanced_bot = EnhancedPokerBot()
    
    # Try to load a test screenshot
    test_files = ['test_table.png', 'calibration_screenshot.png', 'poker_screenshot.png']
    screenshot = None
    
    for filename in test_files:
        if os.path.exists(filename):
            screenshot = cv2.imread(filename)
            logger.info(f"Loaded test screenshot: {filename}")
            break
    
    if screenshot is None:
        logger.info("No test screenshot found. Please provide one of: " + ", ".join(test_files))
        return
    
    # Test auto-calibration
    if enhanced_bot.auto_calibrate(screenshot):
        logger.info("✅ Auto-calibration successful!")
        
        # Test game state analysis
        result = enhanced_bot.analyze_game_state(screenshot, debug=True)
        
        if result:
            logger.info("✅ Game state analysis successful!")
            logger.info(f"Result: {result}")
            
            # Create visualization
            enhanced_bot.create_visualization(screenshot)
            logger.info("✅ Visualization created!")
        else:
            logger.error("❌ Game state analysis failed")
    else:
        logger.error("❌ Auto-calibration failed")

if __name__ == "__main__":
    import time
    
    print("="*60)
    print("ENHANCED POKER BOT INTEGRATION SYSTEM")
    print("="*60)
    print()
    print("This system provides:")
    print("✅ Automatic table layout detection")
    print("✅ Advanced OCR card recognition") 
    print("✅ 4-color deck support")
    print("✅ Multiple recognition fallback methods")
    print("✅ Debug visualization")
    print()
    
    # Run test
    test_enhanced_system()
