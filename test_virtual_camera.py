"""
Quick test for OBS Virtual Camera functionality
"""

import cv2
import numpy as np
import logging

def test_virtual_camera():
    """Test OBS Virtual Camera"""
    print("Testing OBS Virtual Camera...")
    
    # Try different camera indices
    for camera_index in range(10):
        try:
            print(f"Trying camera index {camera_index}...")
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            
            if cap.isOpened():
                print(f"  Camera {camera_index} opened successfully")
                
                # Try to read a frame
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"  ✅ Camera {camera_index} working: {frame.shape}")
                    
                    # Check if frame has content
                    avg_pixel = np.mean(frame)
                    print(f"  Average pixel value: {avg_pixel:.1f}")
                    
                    # Save test image
                    filename = f"test_camera_{camera_index}.png"
                    cv2.imwrite(filename, frame)
                    print(f"  Saved test image: {filename}")
                    
                    if avg_pixel > 10:
                        print(f"  🎉 Found working camera with content at index {camera_index}!")
                        cap.release()
                        return camera_index
                else:
                    print(f"  ❌ Camera {camera_index} opened but no frame captured")
                
                cap.release()
            else:
                print(f"  ❌ Camera {camera_index} failed to open")
                
        except Exception as e:
            print(f"  ❌ Error with camera {camera_index}: {e}")
    
    print("❌ No working virtual camera found")
    print("\nTroubleshooting:")
    print("1. Make sure OBS Studio is running")
    print("2. In OBS, click 'Start Virtual Camera' button")
    print("3. Make sure UGREEN capture card is added as video source")
    print("4. Verify PokerStars is visible on your laptop")
    
    return None

if __name__ == "__main__":
    test_virtual_camera()
