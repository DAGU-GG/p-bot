"""
Test script to generate debug images with correct regions
"""
import sys
import os
sys.path.insert(0, 'src')

from poker_bot import PokerStarsBot
import time

def test_debug_generation():
    """Test generating debug images with correct regions."""
    print("Testing debug image generation with saved regions...")
    
    try:
        # Initialize bot (this loads all the correct regions)
        bot = PokerStarsBot()
        print("✅ Bot initialized")
        
        # Take a screenshot and process it
        screenshot = bot.window_capture.capture_current_window()
        if screenshot is not None:
            print(f"✅ Screenshot captured: {screenshot.shape}")
            
            # Force calibration to generate debug image
            result = bot.image_processor.calibrate_table_regions(screenshot)
            print(f"✅ Calibration completed: {result}")
            
            # Also test the analysis function
            analysis_result = bot.image_processor.analyze_table_state(screenshot)
            print(f"✅ Analysis completed")
            
            print("Debug images should now be generated with your calibrated regions!")
            
        else:
            print("❌ No screenshot captured - is PokerStars running?")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_generation()
