"""
Test script to verify the card recognition fixes are working.
This script will test the improved card recognition system with debug output.
"""

import os
import sys
import cv2
import logging
import time

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_card_recognition_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_card_recognition_fix')

def test_improved_recognition():
    """Test the improved card recognition system."""
    logger.info("Testing improved card recognition system...")
    
    try:
        # Import the improved recognizer
        from improved_card_recognition import ImprovedCardRecognizer
        
        # Create recognizer
        recognizer = ImprovedCardRecognizer()
        logger.info("✅ ImprovedCardRecognizer created successfully")
        
        # Test with a card template to verify basic functionality
        template_dir = "card_templates"
        if os.path.exists(template_dir):
            template_files = [f for f in os.listdir(template_dir) if f.endswith('.png')]
            if template_files:
                # Test with first available template
                test_template = os.path.join(template_dir, template_files[0])
                test_img = cv2.imread(test_template)
                
                if test_img is not None:
                    logger.info(f"Testing with template: {template_files[0]}")
                    
                    # Test recognition
                    result = recognizer.recognize_card(test_img, debug=True)
                    logger.info(f"Recognition result: {result}")
                    
                    # Test tuple format (as called by poker bot)
                    if isinstance(result, tuple):
                        card_code, confidence, method = result
                        logger.info(f"Tuple format: card={card_code}, confidence={confidence:.3f}, method={method}")
                        
                        if card_code not in ('empty', 'error', 'unknown'):
                            logger.info("✅ Card recognition is working!")
                            return True
                        else:
                            logger.warning(f"⚠️ Card recognition returned: {card_code}")
                    else:
                        logger.warning(f"⚠️ Unexpected result format: {type(result)}")
                else:
                    logger.error(f"Failed to load template: {test_template}")
            else:
                logger.error("No template files found")
        else:
            logger.error("Template directory not found")
        
        return False
        
    except Exception as e:
        logger.error(f"Error testing improved recognition: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_with_screenshot():
    """Test with a recent screenshot if available."""
    logger.info("Testing with screenshot...")
    
    try:
        # Look for recent screenshots
        screenshot_dirs = ["screenshots", "debug_images"]
        screenshot_path = None
        
        for dir_name in screenshot_dirs:
            if os.path.exists(dir_name):
                files = [f for f in os.listdir(dir_name) if f.endswith('.png')]
                if files:
                    # Get most recent file
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(dir_name, x)), reverse=True)
                    screenshot_path = os.path.join(dir_name, files[0])
                    break
        
        if screenshot_path:
            logger.info(f"Testing with screenshot: {screenshot_path}")
            
            # Load screenshot
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                logger.error("Failed to load screenshot")
                return False
            
            # Import and test with poker bot
            from poker_bot import PokerStarsBot
            
            # Create bot with improved recognition
            bot = PokerStarsBot(recognition_type='improved')
            logger.info("✅ PokerStarsBot created with improved recognition")
            
            # Test analysis
            analysis = bot.analyze_game_state(screenshot, debug=True)
            logger.info("✅ Analysis completed")
            
            # Check results
            if 'hole_cards' in analysis and analysis['hole_cards']:
                hole_cards = analysis['hole_cards']
                if hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                    logger.info(f"✅ Hole cards detected: {hole_cards}")
                    return True
                else:
                    logger.warning(f"⚠️ Hole cards not valid: {hole_cards}")
            
            if 'community_cards' in analysis and analysis['community_cards']:
                community_cards = analysis['community_cards']
                if hasattr(community_cards, 'count') and community_cards.count > 0:
                    logger.info(f"✅ Community cards detected: {community_cards}")
                    return True
                else:
                    logger.warning(f"⚠️ No community cards: {community_cards}")
            
            logger.warning("⚠️ No cards detected in screenshot")
            return False
        else:
            logger.warning("No screenshots found for testing")
            return False
            
    except Exception as e:
        logger.error(f"Error testing with screenshot: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main test function."""
    logger.info("="*60)
    logger.info("CARD RECOGNITION FIX TEST")
    logger.info("="*60)
    
    # Test 1: Basic improved recognition
    test1_result = test_improved_recognition()
    
    # Test 2: Screenshot analysis
    test2_result = test_with_screenshot()
    
    # Summary
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Basic recognition test: {'PASSED' if test1_result else 'FAILED'}")
    logger.info(f"Screenshot analysis test: {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result or test2_result:
        logger.info("✅ At least one test passed - card recognition is working!")
        logger.info("Try running the modern UI with: python src/modern_ui.py --recognition=improved --show-regions")
    else:
        logger.error("❌ All tests failed - card recognition needs more work")
    
    return test1_result or test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)