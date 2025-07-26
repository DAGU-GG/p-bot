# Card Recognition Debugging and Troubleshooting Guide

This guide provides instructions for troubleshooting and improving card recognition in the PokerStars Bot.

## Table of Contents
1. [Common Recognition Issues](#common-recognition-issues)
2. [Debugging Tools](#debugging-tools)
3. [Recognition Process](#recognition-process)
4. [Improving Recognition](#improving-recognition)
5. [Recent Improvements](#recent-improvements)

## Recent Improvements

Based on recent testing, several improvements have been implemented:

1. **Enhanced Video Capture in main_window.py**:
   - Added frame quality verification to avoid processing invalid frames
   - Added periodic debugging by saving frames for later analysis
   - Enhanced logging with more detailed card information

2. **New Screen Capture Component**:
   - Added new `screen_capture.py` module with `ScreenCaptureManager` class
   - Implemented multiple capture methods (MSS, PyAutoGUI, Win32 API, OpenCV)
   - Added proper error handling and logging
   
3. **Fixed Community Card Region Handling**:
   - Corrected how percentage-based regions are converted to pixel coordinates
   - Added boundary checks to prevent out-of-bounds errors
   - Improved error reporting and exception handling
   
4. **Enhanced Test Framework**:
   - Updated test_recognition.bat to provide a menu of test options
   - Added automatic creation of debug directories
   - Improved logging of recognition results

2. **New Testing Tools**:
   - `test_card_color.py`: Tests the suit color detection
   - Enhanced `simple_card_recognition_test.py`: Provides visual debugging
   - `test_recognition.bat`: Script to run all tests easily

3. **Enhanced Debug Capabilities**:
   - Added visualization of card recognition steps
   - Implemented debug output to show match confidence
   - Added color analysis visualization

## Common Recognition Issues

Card recognition can be affected by several factors:

1. **Card Templates**: Make sure the card templates in `card_templates/` match your poker client.
2. **Region Configuration**: Verify that the card regions in `regions/region_config.json` correctly capture the cards.
3. **Color Issues**: Red suits (hearts/diamonds) and black suits (clubs/spades) can be confused.
4. **Lighting/Resolution**: Different screen resolutions or lighting can affect recognition.

## Debugging Tools

Several debugging tools are available to help diagnose recognition issues:

### 1. Card Recognition Debug Tool
```
python debug_card_recognition.py --live
```
This tool captures the screen and shows the step-by-step recognition process with visualizations.

### 2. Test Card Recognition
```
python test_card_recognition.py --live
```
This tool tests the recognition system on live capture or specific images and logs detailed results.

### 3. Card Suit Color Analyzer
```
python card_suit_color.py --directory debug_cards
```
This tool analyzes card images to determine if they have red or black suits, helping diagnose color-related issues.

### 4. Region Calibration Debug
```
python debug_region_extraction.py
```
This tool helps verify that card regions are correctly defined and extracted.

## Recognition Process

The card recognition system follows these steps:

1. **Region Extraction**: Cards are extracted from defined regions in the poker table.
2. **Card Presence Detection**: The system checks if the region contains a card.
3. **Preprocessing**: The card image is processed to enhance features.
4. **Template Matching**: The card is compared to templates to find a match.
5. **OCR Fallback**: If template matching fails, OCR is used as a fallback.

## Improving Recognition

To improve card recognition:

### 1. Recalibrate Regions
Run the region calibrator to update card regions:
```
python test_region_calibrator.py
```

### 2. Update Card Templates
Update or add new card templates to the `card_templates/` directory.

### 3. Adjust Recognition Thresholds
In `src/card_recognizer.py`, you can adjust:
- `template_match_threshold`: Lower values allow more matches but can be less accurate.
- `card_presence_threshold`: Adjust how aggressively the system detects cards.

### 4. Generate Debug Images
Enable debug mode to generate debug images in the `debug_cards/` directory:
```python
# In your code
card_value, confidence, method = card_recognizer.recognize_card(card_img, debug=True)
```

### 5. Analyze Color Information
Use the color analysis in `card_suit_color.py` to verify that suits are correctly identified.

## Additional Resources

- Check `poker_bot.log` for detailed logging information.
- Review images in `debug_cards/` to see what the system "sees".
- Read `RECOGNITION_STATUS_REPORT.md` for the latest status of the recognition system.

## Troubleshooting Checklist

- [ ] Are the card regions correctly calibrated?
- [ ] Do the card templates match your poker client?
- [ ] Is color detection working properly?
- [ ] Are the confidence thresholds appropriate?
- [ ] Is OCR correctly installed and configured?

If problems persist, collect debug images and logs to help diagnose the issue.
