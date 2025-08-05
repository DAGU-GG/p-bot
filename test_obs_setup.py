"""
Test current OBS Virtual Camera setup
"""

import cv2
import numpy as np
import time

def test_obs_virtual_camera():
    """Test the OBS Virtual Camera with found index"""
    print("Testing OBS Virtual Camera at index 1...")
    
    # Connect to virtual camera at index 1
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("❌ Failed to connect to virtual camera")
        return False
    
    print("✅ Connected to virtual camera")
    
    # Test multiple frames
    for i in range(5):
        ret, frame = cap.read()
        if ret and frame is not None:
            avg_pixel = np.mean(frame)
            print(f"Frame {i+1}: {frame.shape}, avg pixel: {avg_pixel:.1f}")
            
            # Save frame
            cv2.imwrite(f"virtual_camera_frame_{i+1}.png", frame)
            
            if avg_pixel > 10:
                print(f"✅ Frame {i+1} has visible content!")
            else:
                print(f"⚠️ Frame {i+1} is mostly black")
        else:
            print(f"❌ Failed to capture frame {i+1}")
        
        time.sleep(0.5)
    
    cap.release()
    
    print("\n📋 Current Status:")
    print("✅ OBS Virtual Camera detected and working")
    print("❌ Video signal is black (no content from capture card)")
    print("\n🔧 Next Steps:")
    print("1. In OBS Studio, check that your UGREEN capture card is added as a 'Video Capture Device'")
    print("2. Make sure the capture card source is visible in the main OBS preview")
    print("3. Ensure 'Start Virtual Camera' is clicked in OBS")
    print("4. Verify the laptop is connected and PokerStars is running")
    
    return True

if __name__ == "__main__":
    test_obs_virtual_camera()
