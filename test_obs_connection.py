"""
OBS Virtual Camera Connection Helper
"""

import cv2
import numpy as np
import time

def test_obs_connection():
    """Test OBS Virtual Camera with detailed diagnostics"""
    print("🔍 Testing OBS Virtual Camera Connection...")
    
    # Test connection
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("❌ Cannot connect to Virtual Camera")
        print("   Make sure OBS Studio is running and Virtual Camera is started")
        return
    
    print("✅ Connected to Virtual Camera")
    
    # Test frame capture
    for attempt in range(5):
        print(f"\n📸 Capture attempt {attempt + 1}/5...")
        
        ret, frame = cap.read()
        if not ret or frame is None:
            print("   ❌ Failed to capture frame")
            continue
            
        print(f"   ✅ Frame captured: {frame.shape}")
        
        # Analyze content
        avg_pixel = np.mean(frame)
        unique_colors = len(np.unique(frame.reshape(-1, frame.shape[-1]), axis=0))
        
        print(f"   Average pixel value: {avg_pixel:.2f}")
        print(f"   Unique colors: {unique_colors}")
        
        if avg_pixel == 0.0 and unique_colors == 1:
            print("   ❌ Frame is completely black")
            print("   🔧 Check OBS Virtual Camera settings:")
            print("      1. Stop Virtual Camera in OBS")
            print("      2. Select the scene with your poker table")
            print("      3. Start Virtual Camera again")
            print("      4. Make sure 'Current Scene' is selected")
        elif avg_pixel > 10:
            print("   ✅ Frame has visible content!")
            filename = f"working_obs_capture_{int(time.time())}.png"
            cv2.imwrite(filename, frame)
            print(f"   💾 Saved working capture: {filename}")
            break
        else:
            print("   ⚠️ Frame has some content but may be dim")
        
        time.sleep(1)
    
    cap.release()
    
    print("\n📋 Summary:")
    print("If all frames are black:")
    print("  1. OBS Virtual Camera is running but not transmitting content")
    print("  2. Check the active scene in OBS contains your poker table")
    print("  3. Restart Virtual Camera after selecting correct scene")
    print("  4. Verify UGREEN capture source is visible (eye icon)")

if __name__ == "__main__":
    test_obs_connection()
