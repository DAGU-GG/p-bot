"""
PokerStars Bot - Main Application
Stages 1-4: Complete poker bot implementation with table capture, 
image processing, hole card recognition, and community card detection.
"""

import cv2
import numpy as np
import time
import logging
import os
import sys
from typing import Dict, List, Tuple, Optional, Any

# Optional keyboard import
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: keyboard module not available, hotkey functionality disabled")

# OCR-based card recognition system  
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from ocr_card_recognition import ocr_recognizer
    OCR_RECOGNITION_AVAILABLE = True
    print("✅ OCR recognition system loaded")
except ImportError:
    OCR_RECOGNITION_AVAILABLE = False
    print("❌ OCR recognition not available - using old system")

# Import our custom modules
from image_processor import ImageProcessor, GameState
from card_recognizer import CardRecognizer, HoleCards
from community_card_detector import CommunityCardDetector, CommunityCards
from window_capture import PokerStarsWindowCapture
from poker_table_analyzer import PokerTableAnalyzer, TableInfo

class PokerStarsBot:
    """
    Main PokerStars bot class that coordinates all functionality.
    Handles window detection, screen capture, image processing, and card recognition.
    """
    
    def __init__(self, recognition_type='standard'):
        """
        Initialize the poker bot with all required components.
        
        Args:
            recognition_type: Type of card recognition system to use:
                - 'standard': Default card recognition
                - 'improved': Improved card recognition with color analysis
                - 'direct': Direct card recognition with shape detection
        """
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Store the recognition type
        self.recognition_type = recognition_type
        self.logger.info(f"Using {recognition_type} card recognition system")
        
        # Initialize components based on recognition type
        self.image_processor = ImageProcessor()
        
        # Initialize the appropriate card recognizer
        if self.recognition_type == 'improved':
            try:
                # Import and use improved card recognition system
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from improved_card_recognition import ImprovedCardRecognizer
                self.logger.info("Initializing Improved Card Recognition system")
                self.card_recognizer = ImprovedCardRecognizer()
            except ImportError as e:
                self.logger.error(f"Failed to import Improved Card Recognition: {e}")
                self.logger.warning("Falling back to standard card recognition")
                self.card_recognizer = CardRecognizer()
                self.recognition_type = 'standard'
                
        elif self.recognition_type == 'direct':
            try:
                # Import and use direct card recognition system
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from direct_card_recognition import DirectCardRecognizer
                self.logger.info("Initializing Direct Card Recognition system")
                self.card_recognizer = DirectCardRecognizer()
            except ImportError as e:
                self.logger.error(f"Failed to import Direct Card Recognition: {e}")
                self.logger.warning("Falling back to improved card recognition")
                try:
                    from improved_card_recognition import ImprovedCardRecognizer
                    self.card_recognizer = ImprovedCardRecognizer()
                    self.recognition_type = 'improved'
                except ImportError:
                    self.logger.warning("Falling back to standard card recognition")
                    self.card_recognizer = CardRecognizer()
                    self.recognition_type = 'standard'
        else:
            # Use standard card recognition
            self.card_recognizer = CardRecognizer()
        
        # Initialize remaining components
        # For community card detection, always use the original CardRecognizer
        # as it has the required template matching methods
        if hasattr(self.card_recognizer, 'original_recognizer') and self.card_recognizer.original_recognizer:
            community_recognizer = self.card_recognizer.original_recognizer
        else:
            community_recognizer = CardRecognizer()
        
        self.community_detector = CommunityCardDetector(community_recognizer)
        self.window_capture = PokerStarsWindowCapture()
        self.table_analyzer = PokerTableAnalyzer()
        
        # Bot settings
        # FIXED: Set exactly 10 FPS (0.1 second intervals) for consistent performance
        self.capture_interval = 0.1  # 10 FPS exactly
        self.running = False
        
        # Statistics
        self.captures_count = 0
        self.successful_recognitions = 0
        self.last_hole_cards = None
        self.last_community_cards = None
        self.last_table_info = None
        
        # Create directories
        self.create_directories()
        
        self.logger.info("PokerStars Bot initialized - Stages 1-4 complete")
    
    def setup_logging(self):
        """Setup comprehensive logging for the bot."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('poker_bot.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def create_directories(self):
        """Create necessary directories for debug output."""
        directories = [
            'screenshots', 'debug_images', 'debug_cards', 
            'debug_community', 'card_templates', 'regions'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def find_pokerstars_window(self) -> bool:
        """Find and setup the PokerStars window for capture using enhanced detection."""
        try:
            self.logger.info("Searching for PokerStars window...")
            
            # Use enhanced window detection
            selected_window = self.window_capture.select_best_window()
            
            if not selected_window:
                self.logger.error("No PokerStars table windows found!")
                self.logger.info("Troubleshooting:")
                self.logger.info("1. Make sure PokerStars is running")
                self.logger.info("2. Open a poker table (not just the lobby)")
                self.logger.info("3. Ensure the table window is visible and not minimized")
                
                # Show available windows for debugging
                all_windows = self.window_capture.find_pokerstars_windows()
                if all_windows:
                    self.logger.info("Found these potential windows:")
                    for i, window in enumerate(all_windows[:5]):
                        self.logger.info(f"  {i+1}. '{window['title']}' "
                                       f"({window['width']}x{window['height']}) "
                                       f"Score: {window.get('score', 0)}")
                return False
            
            # Log window information
            window_info = self.window_capture.get_window_info()
            self.logger.info(f"Selected PokerStars window: '{window_info['title']}'")
            self.logger.info(f"Window size: {window_info['dimensions']}")
            self.logger.info(f"Window position: {window_info['position']}")
            self.logger.info(f"Detection method: {window_info['method']}")
            self.logger.info(f"Window score: {window_info['score']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error finding PokerStars window: {e}")
            return False
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """Capture the current screen of the PokerStars window."""
        try:
            # Capture using enhanced window capture
            img = self.window_capture.capture_current_window()
            
            if img is None:
                self.logger.warning("Failed to capture window - trying to reselect window")
                if self.find_pokerstars_window():
                    img = self.window_capture.capture_current_window()
                
            if img is None:
                return None
            
            # Validate the capture
            if not self.window_capture.validate_capture(img):
                self.logger.warning("Captured image failed validation - may not be a poker table")
            
            # Save screenshot for debugging
            timestamp = int(time.time())
            screenshot_path = f"screenshots/capture_{timestamp}.png"
            cv2.imwrite(screenshot_path, img)
            
            self.captures_count += 1
            return img
                
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")
            return None
    
    def analyze_game_state(self, table_image: np.ndarray, debug=False) -> Dict[str, Any]:
        """Analyze the complete game state from the table image.
        
        Args:
            table_image: The captured table image
            debug: Whether to enable debug mode for more detailed logging
            
        Returns:
            Dictionary with complete game state analysis
        """
        try:
            self.logger.info(f"Starting game state analysis on image shape: {table_image.shape}")
            
            # Get basic game state from image processor
            game_state = self.image_processor.analyze_table_state(table_image)
            self.logger.info(f"Image processor analysis complete: {game_state.active_players} players detected")
            
            # Use OCR recognition system
            if OCR_RECOGNITION_AVAILABLE:
                self.logger.info("Using OCR recognition system")
                hole_cards = ocr_recognizer.recognize_hero_hole_cards(table_image, debug=debug)
                community_cards = ocr_recognizer.detect_community_cards(table_image, debug=debug)
            else:
                self.logger.info("Using old recognition system")
                # Fallback to old system
                hole_cards = self.card_recognizer.recognize_hero_hole_cards(table_image, debug=debug)
                community_cards = self.community_detector.detect_community_cards(table_image, debug=debug)
            
            self.logger.info(f"Hole cards analysis complete: valid={hole_cards.is_valid()}")
            self.logger.info(f"Community cards analysis complete: {community_cards.count} cards detected")
            
            # Analyze complete table information
            table_info = self.table_analyzer.analyze_complete_table(table_image)
            self.logger.info(f"Table analysis complete: {len(table_info.players)} players, pot={table_info.pot_size:.1f}BB")
            
            # Compile complete analysis
            analysis = {
                'timestamp': time.time(),
                'game_state': game_state,
                'hole_cards': hole_cards,
                'community_cards': community_cards,
                'table_info': table_info,
                'capture_count': self.captures_count
            }
            
            # Update statistics
            if hole_cards.is_valid() or community_cards.count > 0 or len(table_info.players) > 0:
                self.successful_recognitions += 1
                self.logger.info("Analysis marked as successful")
            else:
                self.logger.warning("Analysis found no valid detections")
            
            # Store for comparison
            self.last_hole_cards = hole_cards
            self.last_community_cards = community_cards
            self.last_table_info = table_info
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing game state: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return {'error': str(e), 'timestamp': time.time()}
    
    def format_output(self, analysis: Dict[str, Any]) -> str:
        """Format the analysis results for display."""
        try:
            if 'error' in analysis:
                return f"Analysis Error: {analysis['error']}"
            
            game_state = analysis['game_state']
            hole_cards = analysis['hole_cards']
            community_cards = analysis['community_cards']
            table_info = analysis.get('table_info')
            
            # Build output string
            output_parts = []
            
            # Timestamp
            timestamp = time.strftime("%H:%M:%S", time.localtime(analysis['timestamp']))
            output_parts.append(f"Table captured at {timestamp}")
            
            # Basic game info
            info_parts = []
            if game_state.active_players > 0:
                info_parts.append(f"Players: {game_state.active_players}")
            
            if community_cards.count > 0:
                info_parts.append(f"Phase: {community_cards.phase}")
            
            if hole_cards.is_valid():
                info_parts.append(f"Hole cards: {hole_cards}")
            
            if community_cards.count > 0:
                visible_cards = community_cards.get_visible_cards()
                if visible_cards:
                    cards_str = ", ".join(str(card) for card in visible_cards)
                    info_parts.append(f"Community: {cards_str}")
            
            # Add table information
            if table_info and len(table_info.players) > 0:
                hero = self.table_analyzer.get_hero_info(table_info)
                if hero:
                    info_parts.append(f"Hero Stack: {hero.stack_size:.1f}BB")
                    info_parts.append(f"Position: {hero.position}")
                
                info_parts.append(f"Pot: {table_info.pot_size:.1f}BB")
                info_parts.append(f"Stakes: {table_info.table_stakes}")
            
            if info_parts:
                output_parts.append(" - ".join(info_parts))
            
            # Detailed recognition info
            details = []
            if hole_cards.is_valid():
                details.append(f"Hole Cards: {hole_cards} (confidence: {hole_cards.detection_confidence:.3f})")
            
            if community_cards.count > 0:
                details.append(f"Community Cards: {community_cards} (confidence: {community_cards.detection_confidence:.3f})")
            
            # Add detailed table analysis
            if table_info and len(table_info.players) > 0:
                details.append(f"Table Analysis: {len(table_info.players)} players detected")
                details.append(f"Dealer: Seat {table_info.dealer_seat}, Hero: Seat {table_info.hero_seat}")
            
            if details:
                output_parts.extend(details)
            
            return "\n".join(output_parts)
            
        except Exception as e:
            return f"Output formatting error: {e}"
    
    def print_statistics(self):
        """Print bot performance statistics."""
        try:
            success_rate = (self.successful_recognitions / max(self.captures_count, 1)) * 100
            
            print("\n" + "="*60)
            print("POKERSTARS BOT STATISTICS")
            print("="*60)
            print(f"Total captures: {self.captures_count}")
            print(f"Successful recognitions: {self.successful_recognitions}")
            print(f"Success rate: {success_rate:.1f}%")
            print(f"Image processor regions: {len(self.image_processor.regions)}")
            print(f"Card templates loaded: {self.card_recognizer.get_recognition_stats()['templates_loaded']}")
            print(f"Community detection regions: {self.community_detector.get_detection_stats()['regions_defined']}")
            
            if self.last_table_info and len(self.last_table_info.players) > 0:
                print(f"Last table analysis: {len(self.last_table_info.players)} players")
                hero = self.table_analyzer.get_hero_info(self.last_table_info)
                if hero:
                    print(f"Hero: Seat {hero.seat_number}, Stack: {hero.stack_size:.1f}BB, Position: {hero.position}")
            
            if self.last_hole_cards and self.last_hole_cards.is_valid():
                print(f"Last hole cards: {self.last_hole_cards}")
            
            if self.last_community_cards and self.last_community_cards.count > 0:
                print(f"Last community cards: {self.last_community_cards}")
            
            print("="*60)
            
        except Exception as e:
            print(f"Error printing statistics: {e}")
    
    def run(self):
        """Main bot execution loop."""
        try:
            print("="*60)
            print("POKERSTARS BOT - STAGES 1-4 COMPLETE")
            print("="*60)
            print("Features:")
            print("✅ Window detection and screen capture")
            print("✅ Table region identification and calibration")
            print("✅ Hero hole card recognition")
            print("✅ Community card detection (flop/turn/river)")
            print("✅ Progressive revelation support")
            print("✅ Multi-method card presence detection")
            print("✅ Automatic table analysis (stacks, blinds, positions)")
            print("✅ Big Blind unit calculations")
            print("✅ Hero position and stack detection")
            print("="*60)
            print()
            
            # Find PokerStars window
            if not self.find_pokerstars_window():
                print("❌ Could not find PokerStars window!")
                print("\nTroubleshooting:")
                print("1. Make sure PokerStars is running")
                print("2. Open a poker table (not just the lobby)")
                print("3. Ensure the table window is visible (not minimized)")
                print("4. Make sure the table window has focus")
                print("5. Try running window_finder.bat to debug")
                return False
            
            print("✅ PokerStars window found and configured")
            
            # Show capture method being used
            window_info = self.window_capture.get_window_info()
            print(f"📸 Using capture method: {window_info.get('capture_method', 'auto')}")
            print(f"📸 Capture interval: {self.capture_interval}s")
            print("🎯 Starting analysis loop...")
            print("\n💡 Press Ctrl+C to stop the bot\n")
            
            self.running = True
            
            # Main capture and analysis loop
            while self.running:
                try:
                    # Capture screen
                    table_image = self.capture_screen()
                    if table_image is None:
                        print("⚠️  Failed to capture screen, retrying...")
                        time.sleep(1)
                        continue
                    
                    # Analyze the captured image
                    analysis = self.analyze_game_state(table_image)
                    
                    # Display results
                    output = self.format_output(analysis)
                    print(output)
                    print("-" * 40)
                    
                    # Wait before next capture
                    time.sleep(self.capture_interval)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Bot stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    print(f"⚠️  Error: {e}")
                    time.sleep(1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Critical error in bot execution: {e}")
            print(f"❌ Critical error: {e}")
            return False
        
        finally:
            self.running = False
            self.print_statistics()
            print("\n👋 PokerStars Bot shutdown complete")

def main():
    """Main entry point for the poker bot."""
    try:
        # Create and run the bot
        bot = PokerStarsBot()
        success = bot.run()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Bot interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())