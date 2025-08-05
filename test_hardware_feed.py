"""
Quick test to verify hardware capture feed is working
"""

import cv2
import time
from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig

def test_hardware_feed():
    """Test if we can capture frames from hardware"""
    print("Testing Hardware Capture Feed...")
    
    # Initialize hardware capture
    config = HardwareCaptureConfig(debug_mode=True)
    capture_system = HardwareCaptureSystem(config)
    
    # Test OBS window detection
    obs_window = capture_system.find_obs_window()
    if obs_window:
        print(f"✅ Found OBS window: {obs_window.title}")
        print(f"   Position: {obs_window.left}, {obs_window.top}")
        print(f"   Size: {obs_window.width} x {obs_window.height}")
    else:
        print("❌ OBS window not found")
        return False
    
    # Test screenshot capture
    print("\nTesting screenshot capture...")
    for i in range(5):
        screenshot = capture_system.capture_obs_window()
        if screenshot is not None:
            print(f"✅ Screenshot {i+1}: Shape {screenshot.shape}")
            
            # Save a test image
            if i == 0:
                cv2.imwrite("test_hardware_feed.png", screenshot)
                print("   Saved as 'test_hardware_feed.png'")
                
                # Check if image is completely black
                avg_pixel = screenshot.mean()
                if avg_pixel < 5:
                    print(f"⚠️  Warning: Image appears mostly black (avg pixel: {avg_pixel:.1f})")
                    print("   This might indicate no video signal in OBS")
                else:
                    print(f"✅ Image has content (avg pixel: {avg_pixel:.1f})")
        else:
            print(f"❌ Screenshot {i+1}: Failed")
        
        time.sleep(0.5)
    
    return True

if __name__ == "__main__":
    test_hardware_feed()
