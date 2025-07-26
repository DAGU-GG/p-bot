"""
Update the poker bot to use the direct card recognition system.

This script replaces the card recognition system in the poker bot with the 
direct card recognition system that provides better accuracy and performance.
"""

import os
import sys
import logging
import shutil
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("update_direct_recognition.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("update_direct_recognition")

def backup_files(files):
    """
    Create backups of the specified files.
    
    Args:
        files (list): List of file paths to backup
        
    Returns:
        bool: True if all backups were successful
    """
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    success = True
    for file_path in files:
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} not found, skipping backup")
            continue
            
        backup_path = os.path.join(backup_dir, os.path.basename(file_path) + ".bak")
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup of {file_path} at {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            success = False
    
    return success

def update_poker_bot():
    """
    Update the poker bot to use the direct card recognition system.
    
    Returns:
        bool: True if update was successful
    """
    # Files to update
    files_to_update = [
        "poker_bot.py",
        "run_improved_poker_bot.bat"
    ]
    
    # Create backups
    if not backup_files(files_to_update):
        logger.error("Failed to create backups, aborting update")
        return False
    
    # Check if direct recognition modules exist
    required_files = [
        "direct_card_recognition.py",
        "direct_card_integration.py"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"Required file {file} not found, aborting update")
            return False
    
    # Update poker_bot.py
    try:
        if os.path.exists("poker_bot.py"):
            with open("poker_bot.py", "r") as f:
                content = f.read()
            
            # Add import for direct card recognition
            import_pattern = r"import .*card_recognition.*"
            import_replacement = ("import card_recognition_integration\n"
                                 "import enhanced_card_recognition\n"
                                 "import direct_card_integration")
            content = re.sub(import_pattern, import_replacement, content)
            
            # Update card recognition initialization
            init_pattern = r"(\s+)self\.card_recognizer = .*"
            init_replacement = r"\1# Initialize the selected card recognition system\n"
            init_replacement += r"\1if recognition_type == 'direct':\n"
            init_replacement += r"\1    logger.info('Using direct card recognition')\n"
            init_replacement += r"\1    self.card_recognizer = direct_card_integration.DirectCardIntegration()\n"
            init_replacement += r"\1elif recognition_type == 'enhanced':\n"
            init_replacement += r"\1    logger.info('Using enhanced card recognition')\n"
            init_replacement += r"\1    self.card_recognizer = enhanced_card_recognition.EnhancedCardRecognition()\n"
            init_replacement += r"\1else:\n"
            init_replacement += r"\1    logger.info('Using standard card recognition')\n"
            init_replacement += r"\1    self.card_recognizer = card_recognition_integration.CardRecognitionIntegration()"
            content = re.sub(init_pattern, init_replacement, content)
            
            # Add command line argument for recognition type
            args_pattern = r"(\s+)parser\.add_argument.*"
            args_replacement = r"\1parser.add_argument('--recognition', type=str, default='standard', choices=['standard', 'enhanced', 'direct'], help='Card recognition system to use')"
            if "--recognition" not in content:
                content = re.sub(args_pattern, args_replacement + r"\n\1\g<0>", content, count=1)
            
            # Update argument handling
            arg_pattern = r"(\s+)recognition_type = .*"
            if arg_pattern in content:
                # Replace existing recognition_type assignment
                arg_replacement = r"\1recognition_type = args.recognition"
                content = re.sub(arg_pattern, arg_replacement, content)
            else:
                # Add recognition_type assignment if it doesn't exist
                args_init_pattern = r"(\s+)args = parser\.parse_args\(\)"
                args_init_replacement = r"\1args = parser.parse_args()\n\1recognition_type = args.recognition"
                content = re.sub(args_init_pattern, args_init_replacement, content)
            
            # Write updated content
            with open("poker_bot.py", "w") as f:
                f.write(content)
            
            logger.info("Updated poker_bot.py to use direct card recognition")
        else:
            logger.error("poker_bot.py not found")
            return False
    except Exception as e:
        logger.error(f"Failed to update poker_bot.py: {e}")
        return False
    
    # Create/Update the direct poker bot batch file
    try:
        batch_content = """@echo off
echo Starting poker bot with direct card recognition...
echo Logging to direct_poker_bot.log

python poker_bot.py --recognition=direct --log=direct_poker_bot.log

if %ERRORLEVEL% EQU 0 (
    echo Poker bot completed successfully!
) else (
    echo Poker bot encountered an error. Please check direct_poker_bot.log for details.
)
pause"""
        
        with open("run_direct_poker_bot.bat", "w") as f:
            f.write(batch_content)
        
        logger.info("Created run_direct_poker_bot.bat")
    except Exception as e:
        logger.error(f"Failed to create run_direct_poker_bot.bat: {e}")
        return False
    
    return True

def update_requirements():
    """
    Update requirements.txt to include dependencies for direct recognition.
    
    Returns:
        bool: True if update was successful
    """
    try:
        new_requirements = [
            "opencv-python>=4.5.0",
            "numpy>=1.19.0",
            "pytesseract>=0.3.8"
        ]
        
        if os.path.exists("requirements.txt"):
            # Backup requirements file
            shutil.copy2("requirements.txt", "requirements.txt.bak")
            
            # Read existing requirements
            with open("requirements.txt", "r") as f:
                existing_requirements = f.read().splitlines()
            
            # Add new requirements if they don't exist
            for req in new_requirements:
                package_name = req.split(">=")[0]
                if not any(line.startswith(package_name) for line in existing_requirements):
                    existing_requirements.append(req)
            
            # Write updated requirements
            with open("requirements.txt", "w") as f:
                f.write("\n".join(existing_requirements))
            
            logger.info("Updated requirements.txt with direct recognition dependencies")
        else:
            # Create new requirements file
            with open("requirements.txt", "w") as f:
                f.write("\n".join(new_requirements))
            
            logger.info("Created requirements.txt with direct recognition dependencies")
        
        return True
    except Exception as e:
        logger.error(f"Failed to update requirements.txt: {e}")
        return False

def main():
    """Main update function."""
    logger.info("Starting update to direct card recognition system")
    
    # Update poker bot
    if not update_poker_bot():
        logger.error("Failed to update poker bot")
        return False
    
    # Update requirements
    if not update_requirements():
        logger.warning("Failed to update requirements.txt, but poker bot was updated")
    
    logger.info("Successfully updated poker bot to use direct card recognition system")
    logger.info("Run the poker bot with: run_direct_poker_bot.bat")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
