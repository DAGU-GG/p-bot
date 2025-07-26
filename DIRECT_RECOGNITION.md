# Direct Card Recognition System

## Overview
The direct card recognition system uses a combination of color analysis and shape/text detection to identify playing cards directly from captured images without relying on template matching. This approach offers better performance and accuracy, especially in varying lighting conditions.

## Features
- **Color Analysis**: Detects card suits based on dominant colors
- **Shape/Text Detection**: Identifies card ranks through OCR and shape analysis
- **Empty Slot Detection**: Reliably detects when no card is present
- **Duplicate Prevention**: Prevents the same card from being recognized multiple times
- **High Confidence Scoring**: Provides confidence levels for each recognition

## Usage
To use the direct card recognition system in your poker bot:

1. Run the integration script:
```
python update_direct_recognition.py
```

2. Or use the provided batch file:
```
run_direct_poker_bot.bat
```

3. For testing the system independently:
```
test_direct_recognition.bat
```

## Technical Details
The system uses the following approaches:
- Color analysis for suit detection (red for hearts/diamonds, black for clubs/spades)
- Further color differentiation to distinguish between hearts/diamonds and clubs/spades
- OCR for rank detection with confidence scoring
- Image processing to enhance feature detection

## Improvements Over Previous Systems
- More reliable in varying lighting conditions
- Less sensitive to card positioning
- Higher accuracy rates on problematic cards (face cards)
- Faster processing times
- Better duplicate detection

## Integration
The system can be integrated with the existing poker bot through the `direct_card_integration.py` module, which provides a compatible interface to replace the previous recognition systems.
