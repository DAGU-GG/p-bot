# Contributing to PokerStars Bot

## Project Status

This project is currently in development with a working modern UI and enhanced card recognition system. The bot successfully connects to PokerStars tables and performs real-time card recognition.

## Recent Work Completed

### ✅ Modern UI Integration (July 2025)
- Integrated improved card recognition system into modern UI
- Added complete feature parity with poker_bot.py
- Fixed critical region loading and coordinate conversion bugs
- Implemented Unicode-compatible logging for Windows
- Enhanced debugging and statistics reporting

### ✅ Core Systems Working
- **Region Loading**: Successfully loads from `regions/region_config.json`
- **Card Recognition**: 52 card templates with improved matching
- **Window Capture**: Automatic PokerStars window detection
- **Community Cards**: 5-card detection with proper region handling
- **Hero Cards**: 2-card detection with enhanced algorithms

## Current Issues to Address

### 1. Live Testing Required
The system starts correctly and loads all components, but needs live testing with actual poker gameplay to verify:
- Card recognition accuracy during real games
- Performance under different lighting conditions
- Region visibility and accuracy

### 2. Recognition Enhancement
While the improved recognition system is integrated, consider:
- Template matching threshold optimization
- Color detection accuracy improvements
- Empty slot detection refinement

## Development Setup

### Prerequisites
- Python 3.8+
- Windows OS (primary target)
- PokerStars client
- OBS Studio (optional for streaming)

### Quick Start
```bash
# Clone and setup
git clone <repository-url>
cd project
setup.bat

# Launch modern UI
modern_ui.bat
```

### Key Files to Understand

#### Core Recognition
- `improved_card_recognition.py` - Enhanced recognition with color analysis
- `src/card_recognizer.py` - Original template matching system
- `src/community_card_detector.py` - Community card detection

#### UI System
- `src/modern_ui.py` - Main application entry point
- `src/ui/main_window.py` - Primary window controller with full feature integration

#### Configuration
- `regions/region_config.json` - Card region definitions
- `requirements.txt` - Python dependencies

## Testing Framework

### Available Test Scripts
```bash
# Test enhanced recognition
test_enhanced_recognition.py

# Test direct recognition
test_direct_recognition.py

# Color detection testing
test_card_color.py

# Comprehensive testing
test_comprehensive_recognition.py
```

### Debug Tools
- `debug_card_recognition.py` - Visual debugging
- `debug_region_extraction.py` - Region calibration
- All debug tools save images to `debug_cards/` directory

## Known Working Configuration

### Startup Command
```bash
python src/modern_ui.py --recognition=improved --show-regions --config=regions/region_config.json
```

### Expected Output
```
Starting with recognition system: improved
Region visualization: Enabled
Using configuration file: regions/region_config.json
Successfully loaded 8 saved regions from regions/region_config.json
CardRecognizer loaded 2 saved hero card regions
Loaded 52 card templates
Found 1 potential PokerStars table windows
```

## Architecture Notes

### Recognition Pipeline
1. **Window Capture** → Screen capture from PokerStars
2. **Region Extraction** → Extract card regions using JSON config
3. **Template Matching** → Compare against 52 card templates
4. **Color Analysis** → Enhanced suit detection
5. **Confidence Scoring** → Match quality assessment

### Recent Bug Fixes
- **Region Coordinates**: Fixed percentage-to-decimal conversion (e.g., 43.4007 → 0.434)
- **Unicode Logging**: Removed emoji characters causing Windows encoding errors
- **Region Loading**: Proper JSON parsing and validation

## Development Priorities

### High Priority
1. **Live Testing** - Verify recognition during actual gameplay
2. **Performance Optimization** - Ensure smooth real-time operation
3. **Error Handling** - Robust error recovery and logging

### Medium Priority
1. **Recognition Accuracy** - Fine-tune template matching thresholds
2. **UI Polish** - Enhance user experience and feedback
3. **Documentation** - Complete API documentation

### Low Priority
1. **Additional Features** - Hand strength analysis, betting logic
2. **Multi-table Support** - Support for multiple simultaneous tables
3. **Configuration UI** - Visual region calibration tool

## Code Style

- Follow PEP 8 guidelines
- Use descriptive variable names
- Add logging for debugging
- Include error handling
- Document complex algorithms

## Debugging Tips

### Common Issues
1. **Regions not loading** - Check JSON syntax in `region_config.json`
2. **Cards not recognized** - Verify template images in `card_templates/`
3. **Window not found** - Ensure PokerStars is running and visible

### Debug Output
Enable verbose logging by setting log level to DEBUG in the main modules.

### Test Data
Use the debug image saves to collect test cases for recognition improvement.

## Contact

This project was developed with assistance from GitHub Copilot. For technical questions, refer to the extensive documentation in the markdown files within the project.
