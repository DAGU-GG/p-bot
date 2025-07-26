#!/usr/bin/env python3
"""
Test script specifically for the region calibrator
"""

import sys
import os
import tkinter as tk

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_region_calibrator():
    """Test the region calibrator with a mock setup"""
    print("🧪 Testing Region Calibrator...")
    
    try:
        # Create a mock main window
        class MockMainWindow:
            def __init__(self):
                self.capture_mode = "window"
                
                # Mock window capture
                class MockWindowCapture:
                    def __init__(self):
                        self.selected_window = True
                    
                    def capture_current_window(self):
                        # Return a simple test image (black with white rectangle)
                        import numpy as np
                        image = np.zeros((800, 1200, 3), dtype=np.uint8)
                        # Add a white rectangle to simulate poker table
                        image[100:700, 200:1000] = [50, 100, 50]  # Dark green
                        return image
                    
                    def select_best_window(self):
                        return {"title": "Test PokerStars Window"}
                
                self.window_capture = MockWindowCapture()
                self.obs_capture = None
        
        # Import and create region calibrator
        from ui.region_calibrator import RegionCalibrator
        
        # Create root window
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create mock main window
        mock_window = MockMainWindow()
        
        # Create region calibrator
        calibrator = RegionCalibrator(root, mock_window)
        
        print("✅ Region calibrator created successfully")
        print(f"✅ Found {len(calibrator.regions)} regions:")
        
        for name, region in calibrator.regions.items():
            color = region['color']
            x, y = region['x'], region['y']
            w, h = region['width'], region['height']
            print(f"   {name}: {color} box at ({x:.1f}%, {y:.1f}%) size {w:.1f}% x {h:.1f}%")
        
        # Test opening the calibrator
        print("\n🚀 Opening region calibrator window...")
        calibrator.open_calibrator()
        
        print("✅ Region calibrator opened successfully!")
        print("✅ Check the calibration window - you should see:")
        print("   - Poker table image")
        print("   - Colored rectangles for each region")
        print("   - Resize handles on the corners")
        print("   - Region names as labels")
        
        # Keep the window open for manual testing
        print("\n📝 Manual Test Instructions:")
        print("   1. Look for colored rectangles on the image")
        print("   2. Try clicking and dragging regions to move them")
        print("   3. Try dragging corner handles to resize")
        print("   4. Check that the position updates in the UI")
        print("   5. Close the calibration window when done")
        
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ Region calibrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🤖 Region Calibrator Test")
    print("=" * 40)
    
    success = test_region_calibrator()
    
    if success:
        print("\n🎉 Test completed! Check the calibration window.")
    else:
        print("\n💥 Test failed. Check the error above.")
