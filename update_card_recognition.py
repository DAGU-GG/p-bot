"""
Update the poker bot to use the improved card recognition system.

This script replaces the card recognition system in the poker bot with the 
improved version that fixes issues with duplicate cards and community card detection.
"""

import os
import sys
import logging
import shutil
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_card_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('update_card_recognition')

def update_poker_bot():
    """
    Update the poker bot to use the improved card recognition system.
    """
    logger.info("Updating poker bot to use improved card recognition system")
    
    # Check if the necessary files exist
    required_files = [
        "improved_card_recognition.py",
        "card_recognition_integration.py"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"Required file {file} not found")
            return False
    
    try:
        # Create backup of the original poker_bot.py file
        poker_bot_path = "src/poker_bot.py"
        if os.path.exists(poker_bot_path):
            backup_path = f"src/poker_bot.py.bak.{int(time.time())}"
            shutil.copy2(poker_bot_path, backup_path)
            logger.info(f"Created backup of poker_bot.py at {backup_path}")
        
        # Import the integration module
        from card_recognition_integration import IntegratedCardRecognition, integrate_with_poker_bot
        
        # Import the poker bot
        sys.path.append("src")
        from poker_bot import PokerBot
        
        # Create a test instance of the poker bot
        try:
            bot = PokerBot()
            logger.info("Successfully created poker bot instance")
            
            # Integrate improved card recognition
            result = integrate_with_poker_bot(bot)
            
            if result:
                logger.info("Successfully integrated improved card recognition with poker bot")
                return True
            else:
                logger.error("Failed to integrate improved card recognition")
                return False
                
        except Exception as e:
            logger.error(f"Error creating poker bot instance: {e}", exc_info=True)
            return False
        
    except ImportError as e:
        logger.error(f"Import error: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during update: {e}", exc_info=True)
        return False

def create_integration_test_batch():
    """
    Create a batch file to test the integration.
    """
    batch_content = """@echo off
echo Testing improved card recognition integration...
python test_improved_recognition.py
if %ERRORLEVEL% EQU 0 (
    echo Test successful!
) else (
    echo Test failed with error code %ERRORLEVEL%
)
pause
"""
    
    batch_path = "test_improved_recognition.bat"
    with open(batch_path, "w") as f:
        f.write(batch_content)
    
    logger.info(f"Created test batch file at {batch_path}")
    return True

def main():
    """Main function."""
    logger.info("Starting card recognition update process")
    
    # First create test batch file
    create_integration_test_batch()
    
    # Run tests on the improved recognition system
    logger.info("Running tests on improved recognition system")
    from test_improved_recognition import run_all_tests
    test_success = run_all_tests()
    
    if not test_success:
        logger.warning("Tests did not all pass - proceed with caution")
        response = input("Continue with update despite test failures? (y/n): ")
        if response.lower() != 'y':
            logger.info("Update cancelled by user")
            return
    
    # Update the poker bot
    update_success = update_poker_bot()
    
    if update_success:
        logger.info("Poker bot successfully updated to use improved card recognition!")
        logger.info("Run poker_bot.bat to test the updated system")
    else:
        logger.error("Failed to update poker bot")
        logger.info("You can still run test_improved_recognition.bat to test the improved system")

if __name__ == "__main__":
    main()
