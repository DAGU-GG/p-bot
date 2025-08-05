"""
Simple Table Screenshot Tool
Takes a screenshot from OBS Virtual Camera for manual region creation
"""

import cv2
import time
from datetime import datetime

def take_table_screenshot():
    """Simple function to take a screenshot of the current poker table"""
    print("🎯 Poker Table Screenshot Tool")
    print("=" * 40)
    print()
    print("This will capture a screenshot from your OBS Virtual Camera")
    print("Make sure:")
    print("  ✓ OBS Studio is running with Virtual Camera started")
    print("  ✓ Poker table is visible with all cards you want to detect")
    print("  ✓ Cards are clearly visible and not covered")
    print()
    
    input("Press Enter when your table is ready for screenshot...")
    
    try:
        # Find OBS Virtual Camera (based on previous testing, index 1 works)
        camera_index = 1
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            print(f"❌ Could not open camera at index {camera_index}")
            print("   Trying other camera indices...")
            
            # Try other indices
            for i in range(10):
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        camera_index = i
                        print(f"✅ Found working camera at index {i}")
                        break
                cap.release()
            else:
                print("❌ No working camera found")
                return None
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("📸 Taking screenshot in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        # Capture frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            print("❌ Failed to capture frame")
            return None
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"poker_table_for_regions_{timestamp}.png"
        
        # Save screenshot
        cv2.imwrite(filename, frame)
        
        print(f"✅ Screenshot saved: {filename}")
        print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
        print(f"   File size: {cv2.imencode('.png', frame)[1].nbytes / 1024:.1f} KB")
        
        # Check if image looks good
        avg_brightness = frame.mean()
        print(f"   Average brightness: {avg_brightness:.1f}")
        
        if avg_brightness < 30:
            print("⚠️  Image appears quite dark - check OBS settings")
        elif avg_brightness > 200:
            print("⚠️  Image appears very bright - check OBS settings")
        else:
            print("✅ Image brightness looks good")
        
        print()
        print("🎯 Next steps:")
        print("   1. Open the screenshot in an image editor")
        print("   2. Note the pixel coordinates of each card")
        print("   3. Run 'python manual_region_calibrator.py' to create regions")
        print("   4. Or manually edit 'regions/region_config.json'")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    take_table_screenshot()
