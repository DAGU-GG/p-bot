# PokerStars Bot - Installation and Usage Guide

## 🚀 Quick Start Guide

### Prerequisites
1. **Python 3.8+** - Download from [python.org](https://python.org)
2. **Tesseract OCR** - Required for card text recognition
3. **PokerStars Client** - For testing the bot

### Installation Steps

#### 1. Install Python
- Download Python 3.8+ from [python.org](https://python.org)
- **IMPORTANT**: Check "Add Python to PATH" during installation
- Verify installation: Open Command Prompt and type `python --version`

#### 2. Install Tesseract OCR
Choose your operating system:

**Windows:**
- Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
- Install to default location (usually `C:\Program Files\Tesseract-OCR\`)
- Add to PATH or the bot will find it automatically

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

#### 3. Setup the Bot
1. Extract the bot files to a folder (e.g., `C:\PokerBot\`)
2. Open Command Prompt in that folder
3. Run the setup script:
```batch
setup.bat
```

This will:
- Create a virtual environment
- Install all required Python packages
- Verify the installation

### 🎮 Usage Instructions

#### Step 1: Test Your Environment
```batch
test_environment.bat
```
This verifies all libraries are working correctly.

#### Step 2: Find PokerStars Window
```batch
window_finder.bat
```
This interactive tool helps you:
- List all open windows
- Find PokerStars windows
- Test screen capture

#### Step 3: Run the Bot
1. Start PokerStars
2. Open a poker table (play money recommended for testing)
3. Run the bot:
```batch
poker_bot.bat
```

The bot will:
- Automatically find the PokerStars window
- Calibrate table regions
- Start recognizing cards and game state
- Display real-time analysis

#### Step 4: Create Executable (Optional)
```batch
create_executable.bat
```
Creates a standalone .exe file in the `dist\` folder.

### 🔧 Troubleshooting

#### Common Issues:

**"Python is not installed or not in PATH"**
- Reinstall Python and check "Add Python to PATH"
- Restart Command Prompt after installation

**"No PokerStars window found"**
- Make sure PokerStars is running
- Open a poker table
- Try the window_finder.bat tool

**"Failed to capture screen"**
- Run as Administrator
- Check window permissions
- Ensure PokerStars window is not minimized

**Card recognition not working**
- Check if Tesseract is installed correctly
- Verify table theme compatibility
- Check debug images in `debug_cards/` folder

#### Debug Information:
- **Logs**: Check `poker_bot.log` for detailed information
- **Screenshots**: Saved in `screenshots/` folder
- **Debug Images**: Card analysis in `debug_cards/` and `debug_community/`
- **Table Analysis**: Region detection in `debug_images/`

### 📁 Project Structure
```
PokerBot/
├── src/                    # Source code
│   ├── poker_bot.py       # Main bot application
│   ├── card_recognizer.py # Card recognition system
│   ├── community_card_detector.py # Community card detection
│   ├── image_processor.py # Image processing utilities
│   ├── test_environment.py # Environment testing
│   └── window_finder.py   # Window detection utility
├── setup.bat              # Installation script
├── poker_bot.bat          # Run the bot
├── test_environment.bat   # Test environment
├── window_finder.bat      # Window finder tool
├── create_executable.bat  # Create .exe file
├── clean.bat             # Cleanup script
├── requirements.txt       # Python dependencies
└── README.md             # Documentation
```

### 🎯 Testing Stages

The bot implements 4 stages of functionality:

**Stage 1**: Basic window detection and screen capture
**Stage 2**: Table region identification and image processing
**Stage 3**: Hero hole card recognition
**Stage 4**: Community card detection (flop, turn, river)

Each stage builds upon the previous one, creating a comprehensive poker bot foundation.

### ⚠️ Important Notes

- **Use Responsibly**: This bot is for educational purposes
- **Play Money**: Test with play money tables first
- **Terms of Service**: Ensure compliance with PokerStars ToS
- **Performance**: Works best with standard PokerStars themes
- **Resolution**: Optimized for common screen resolutions

### 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review log files for error details
3. Test with the provided debugging tools
4. Ensure all prerequisites are correctly installed

The bot provides comprehensive logging and debug output to help identify and resolve any issues.