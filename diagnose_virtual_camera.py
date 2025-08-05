"""
Diagnostic tool for OBS Virtual Camera feed
"""

import cv2
import numpy as np
import time
import logging

def diagnose_virtual_camera():
    """Diagnose the OBS Virtual Camera feed"""
    print("🔍 Diagnosing OBS Virtual Camera feed...")
    
    # Connect to virtual camera
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("❌ Failed to connect to virtual camera")
        return False
    
    print("✅ Connected to virtual camera")
    
    # Set resolution to match what we saw in logs
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Capture a frame
    ret, frame = cap.read()
    if not ret or frame is None:
        print("❌ Failed to capture frame")
        cap.release()
        return False
    
    print(f"✅ Frame captured: {frame.shape}")
    
    # Analyze the frame
    avg_pixel = np.mean(frame)
    min_pixel = np.min(frame)
    max_pixel = np.max(frame)
    
    print(f"📊 Frame Analysis:")
    print(f"   Average pixel value: {avg_pixel:.2f}")
    print(f"   Min pixel value: {min_pixel}")
    print(f"   Max pixel value: {max_pixel}")
    
    # Save the frame
    filename = f"obs_virtual_camera_diagnostic_{int(time.time())}.png"
    cv2.imwrite(filename, frame)
    print(f"💾 Saved diagnostic image: {filename}")
    
    # Check for content
    if avg_pixel < 5:
        print("⚠️ Frame appears mostly black")
        print("🔧 Troubleshooting:")
        print("   1. Check OBS Virtual Camera is started")
        print("   2. Verify the active scene in OBS shows your poker table")
        print("   3. Make sure the UGREEN capture device is the active source")
    elif avg_pixel > 250:
        print("⚠️ Frame appears mostly white")
    else:
        print("✅ Frame has visible content!")
    
    # Try to detect edges (poker table detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_count = np.sum(edges > 0)
    
    print(f"🎯 Edge Detection:")
    print(f"   Detected edges: {edge_count} pixels")
    
    if edge_count > 1000:
        print("✅ Significant edges detected - table structure likely visible")
    else:
        print("❌ Few edges detected - table may not be clearly visible")
    
    # Save edge detection
    edge_filename = f"obs_edges_diagnostic_{int(time.time())}.png"
    cv2.imwrite(edge_filename, edges)
    print(f"💾 Saved edge detection: {edge_filename}")
    
    cap.release()
    
    # Check if we can find green table color
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define range for green color (poker table)
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    green_pixels = np.sum(green_mask > 0)
    
    print(f"🟢 Green Detection:")
    print(f"   Green pixels found: {green_pixels}")
    
    if green_pixels > 10000:
        print("✅ Significant green detected - poker table likely visible")
    else:
        print("❌ Little green detected - poker table may not be visible")
    
    green_filename = f"obs_green_diagnostic_{int(time.time())}.png"
    cv2.imwrite(green_filename, green_mask)
    print(f"💾 Saved green detection: {green_filename}")
    
    return True

if __name__ == "__main__":
    diagnose_virtual_camera()
