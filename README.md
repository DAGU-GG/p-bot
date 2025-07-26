# PokerStars Bot - Professional Edition v2.0

A comprehensive AI-powered poker bot with advanced computer vision, real-time analysis, and professional GUI interface for PokerStars tables.

## 🚀 Quick Start

### Windows (Recommended)
```bash
# 1. Setup environment
setup.bat

# 2. Launch modern GUI
modern_ui.bat

# 3. Connect to OBS or Window capture
# 4. Calibrate regions if needed
# 5. Start bot monitoring
```

### Manual Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run GUI application
python src/modern_ui.py
```

## 📁 Project Structure

```
PokerStars-Bot/
├── 📁 src/                          # Core source code
│   ├── 📄 poker_bot.py              # Main bot engine
│   ├── 📄 modern_ui.py              # GUI application entry point
│   ├── 📄 window_capture.py         # Window detection & capture
│   ├── 📄 obs_capture.py            # OBS Virtual Camera integration
│   ├── 📄 card_recognizer.py        # Card recognition system
│   ├── 📄 community_card_detector.py # Community card detection
│   ├── 📄 poker_table_analyzer.py   # Table analysis & player detection
│   ├── 📄 image_processor.py        # Image processing utilities
│   ├── 📄 test_environment.py       # Environment testing
│   ├── 📁 ui/                       # GUI components
│   │   ├── 📄 main_window.py        # Main window controller
│   │   ├── 📄 header_panel.py       # Header with status
│   │   ├── 📄 table_view_panel.py   # Live table display
│   │   ├── 📄 game_info_panel.py    # Game information panel
│   │   ├── 📄 control_panel.py      # Bot controls
│   │   ├── 📄 status_bar.py         # Status bar
│   │   └── 📄 region_calibrator.py  # Manual region adjustment
│   ├── 📁 components/               # React components (web version)
│   ├── 📁 utils/                    # Utility functions
│   └── 📁 types/                    # TypeScript definitions
├── 📁 regions/                      # Region configurations
│   └── 📄 region_config.json        # Saved region positions
├── 📁 card_templates/               # Card recognition templates
├── 📁 debug_images/                 # Debug output images
├── 📁 debug_cards/                  # Card recognition debug
├── 📁 debug_community/              # Community card debug
├── 📁 screenshots/                  # Captured screenshots
├── 📄 requirements.txt              # Python dependencies
├── 📄 setup.bat                     # Windows setup script
├── 📄 modern_ui.bat                 # Launch modern GUI
├── 📄 poker_bot.bat                 # Launch command-line bot
├── 📄 test_environment.bat          # Test environment
└── 📄 README.md                     # This file
```

## 🏗️ Architecture Overview

### Core Components

#### 1. **Main Bot Engine** (`poker_bot.py`)
- **Purpose**: Central coordination of all bot functionality
- **Key Features**:
  - Window detection and screen capture
  - Image analysis pipeline coordination
  - Statistics tracking and logging
  - Error handling and recovery

#### 2. **GUI Application** (`modern_ui.py` + `ui/`)
- **Purpose**: Professional user interface for bot control
- **Components**:
  - **Main Window**: Application controller and thread management
  - **Table View**: Live poker table display with region overlay
  - **Game Info**: Real-time game state and statistics
  - **Control Panel**: Bot controls and capture mode selection
  - **Region Calibrator**: Interactive region positioning tool

#### 3. **Capture Systems**
- **Window Capture** (`window_capture.py`): Direct PokerStars window capture
- **OBS Capture** (`obs_capture.py`): OBS Virtual Camera integration

#### 4. **Analysis Pipeline**
- **Image Processor** (`image_processor.py`): Basic image preprocessing
- **Card Recognizer** (`card_recognizer.py`): Hole card detection
- **Enhanced Card Recognition** (`enhanced_card_recognizer.py`): Advanced card recognition with color analysis
- **Color Detection** (`card_suit_color_detector.py`): Suit color detection for improved accuracy
- **Community Detector** (`community_card_detector.py`): Community card detection
- **Table Analyzer** (`poker_table_analyzer.py`): Player and game state analysis

## 🔧 Technical Implementation

### Image Processing Pipeline

```python
# 1. Capture
screenshot = capture_system.capture_current_window()

# 2. Analysis
analysis = {
    'game_state': image_processor.analyze_table_state(screenshot),
    'hole_cards': card_recognizer.recognize_hero_hole_cards(screenshot),
    'community_cards': community_detector.detect_community_cards(screenshot),
    'table_info': table_analyzer.analyze_complete_table(screenshot)
}

# 3. UI Update
ui.update_display(screenshot, analysis)
```

### Region Detection System

The bot uses percentage-based coordinates for region detection:

```python
# Example region definition
hero_card_1 = {
    'x_percent': 0.42,      # 42% from left edge
    'y_percent': 0.72,      # 72% from top edge
    'width_percent': 0.055, # 5.5% of total width
    'height_percent': 0.06  # 6% of total height
}
```

### Card Recognition Methods

1. **Template Matching**: Compares card regions against known templates
2. **OCR Fallback**: Uses Tesseract for text-based recognition
3. **Confidence Scoring**: Validates recognition accuracy

## 📋 File Descriptions

### Core Bot Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `poker_bot.py` | Main bot engine | `analyze_game_state()`, `capture_screen()`, `run()` |
| `window_capture.py` | Window detection | `find_pokerstars_windows()`, `capture_current_window()` |
| `obs_capture.py` | OBS integration | `connect_to_obs_camera()`, `capture_single_frame()` |
| `card_recognizer.py` | Card recognition | `recognize_hero_hole_cards()`, `recognize_single_card()` |
| `community_card_detector.py` | Community cards | `detect_community_cards()`, `detect_card_presence()` |
| `poker_table_analyzer.py` | Table analysis | `analyze_complete_table()`, `detect_table_stakes()` |
| `image_processor.py` | Image processing | `preprocess_image()`, `calibrate_table_regions()` |

### GUI Components

| File | Purpose | Key Features |
|------|---------|--------------|
| `ui/main_window.py` | Main controller | Thread management, capture coordination |
| `ui/table_view_panel.py` | Live display | Screenshot display, region overlay |
| `ui/game_info_panel.py` | Information panel | Game state, cards, players, activity log |
| `ui/control_panel.py` | Bot controls | Start/stop, capture mode, OBS connection |
| `ui/region_calibrator.py` | Region editor | Interactive region positioning, save/load |

### Utility Files

| File | Purpose | Usage |
|------|---------|-------|
| `test_environment.py` | Environment testing | Verify all dependencies |
| `setup.bat` | Windows setup | Install dependencies automatically |
| `modern_ui.bat` | GUI launcher | Start modern interface |
| `requirements.txt` | Dependencies | Python package requirements |

## 🎯 Key Features

### Enhanced Card Recognition System

The bot includes a sophisticated card recognition system with multiple detection methods:

1. **Template Matching**: Base recognition using card templates
2. **Color Analysis**: Detects suit color (red/black) to improve recognition
3. **OCR Processing**: Text-based recognition for fallback
4. **Confidence Scoring**: Combines multiple methods for accurate results

The enhanced recognition provides several benefits:
- More accurate suit detection in varying lighting conditions
- Correction of recognition errors when template matching fails
- Higher confidence scores through method agreement
- Detailed debug information for troubleshooting

For more details, see [COLOR_RECOGNITION.md](COLOR_RECOGNITION.md) and [ENHANCED_RECOGNITION.md](ENHANCED_RECOGNITION.md).

### 1. **Dual Capture Modes**
- **Window Capture**: Direct PokerStars window detection
- **OBS Virtual Camera**: Professional streaming integration

### 2. **Advanced Card Recognition**
- **Template Matching**: High-accuracy card identification
- **OCR Fallback**: Robust text-based recognition
- **Confidence Scoring**: Reliability validation

### 3. **Interactive Region Calibration**
- **Visual Editor**: Drag-and-drop region positioning
- **Real-time Preview**: See changes immediately
- **Save/Load**: Persistent configuration storage

### 4. **Comprehensive Analysis**
- **9-Player Support**: Full table analysis
- **Big Blind Calculations**: Automatic stake detection
- **Position Detection**: Player position identification
- **Game Phase Tracking**: Pre-flop through river

### 5. **Professional GUI**
- **Live Display**: Real-time poker table view
- **Statistics Panel**: Success rates and performance
- **Activity Logging**: Detailed operation logs
- **Debug Tools**: Visual debugging and testing

## 🔧 Configuration

### Region Configuration (`regions/region_config.json`)
```json
{
  "regions": {
    "hero_card_1": {
      "x": 0.42,
      "y": 0.72,
      "width": 0.055,
      "height": 0.06
    },
    "community_card_1": {
      "x": 0.335,
      "y": 0.35,
      "width": 0.06,
      "height": 0.08
    }
  },
  "timestamp": "2024-01-01 12:00:00",
  "version": "1.0"
}
```

### Card Templates (`card_templates/`)
- **Format**: PNG images named as `[rank][suit].png`
- **Examples**: `Ah.png`, `Ks.png`, `2c.png`
- **Size**: Recommended 60x80 pixels
- **Quality**: High contrast, clear details

## 🚀 Usage Guide

### 1. **Initial Setup**
```bash
# Run setup
setup.bat

# Test environment
test_environment.bat
```

### 2. **Launch Application**
```bash
# Modern GUI (recommended)
modern_ui.bat

# Command line version
poker_bot.bat
```

### 3. **Connect to Poker Table**
1. **Choose capture mode**: Window or OBS
2. **Connect**: Click "Find Table" or "Connect OBS"
3. **Verify**: Check live display shows poker table

### 4. **Calibrate Regions** (if needed)
1. **Open calibrator**: Click "Calibrate Regions"
2. **Adjust positions**: Drag regions to match card locations
3. **Test recognition**: Click "Test Recognition"
4. **Save**: Click "Apply & Close"

### 5. **Start Monitoring**
1. **Start bot**: Click "Start Bot"
2. **Monitor**: Watch real-time analysis in right panel
3. **Check logs**: Review activity log for detailed information

## 🐛 Debugging

### Debug Output Locations
- **Screenshots**: `screenshots/` - Captured table images
- **Card Debug**: `debug_cards/` - Card recognition analysis
- **Community Debug**: `debug_community/` - Community card analysis
- **Table Debug**: `debug_images/` - Table analysis visualization
- **Logs**: `poker_bot.log` - Detailed operation logs

### Common Issues

#### No Cards Detected
1. **Check regions**: Use region calibrator to position correctly
2. **Verify templates**: Ensure card templates are present
3. **Check lighting**: Ensure good contrast and visibility
4. **Review logs**: Check `poker_bot.log` for errors

#### Window Not Found
1. **PokerStars running**: Ensure PokerStars is open
2. **Table visible**: Open a poker table (not just lobby)
3. **Window focus**: Ensure table window is not minimized
4. **Try OBS mode**: Use OBS Virtual Camera as alternative

#### OBS Connection Failed
1. **OBS running**: Ensure OBS Studio is running
2. **Virtual Camera**: Start OBS Virtual Camera
3. **Camera index**: Try different camera indices
4. **Permissions**: Run as administrator if needed

## 📊 Performance

### System Requirements
- **OS**: Windows 10/11 (primary), Linux/macOS (limited)
- **Python**: 3.8+ required
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: Multi-core recommended for real-time analysis

### Performance Metrics
- **Capture Rate**: 2 FPS (configurable)
- **Card Recognition**: 85-95% accuracy with good templates
- **Analysis Time**: ~200-500ms per frame
- **Memory Usage**: ~200-500MB typical

## 🔒 Security & Compliance

### Important Notes
- **Educational Purpose**: This bot is for educational and research purposes
- **Terms of Service**: Always comply with PokerStars Terms of Service
- **Local Regulations**: Ensure compliance with local gambling regulations
- **Responsible Use**: Use only on play money tables for testing

### Data Privacy
- **No Data Transmission**: All analysis is performed locally
- **No Account Access**: Bot only analyzes visual information
- **Screenshot Storage**: Local debug images only

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd PokerStars-Bot

# Setup development environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run tests
python src/test_environment.py
```

### Code Structure
- **Follow PEP 8**: Python style guidelines
- **Add logging**: Use `self.logger` for all operations
- **Error handling**: Comprehensive try-catch blocks
- **Documentation**: Docstrings for all functions

## 📝 License

This project is for educational purposes only. Please ensure compliance with all applicable terms of service and local regulations.

## 🆘 Support

### Getting Help
1. **Check logs**: Review `poker_bot.log` for detailed errors
2. **Test environment**: Run `test_environment.bat`
3. **Debug images**: Check debug folders for visual analysis
4. **Region calibration**: Use interactive calibrator for positioning

### Reporting Issues
When reporting issues, please include:
- **Error messages**: Full error text from logs
- **Screenshots**: Visual examples of the problem
- **System info**: OS, Python version, PokerStars version
- **Steps to reproduce**: Detailed reproduction steps

---

**Happy Poker Botting! 🎰♠️♥️♦️♣️**