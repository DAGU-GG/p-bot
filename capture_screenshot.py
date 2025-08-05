"""
Capture Screenshot for Region Creation
Run this script to capture a screenshot from OBS Virtual Camera
"""

import logging
from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig

def main():
    """Capture screenshot for region creation"""
    print("🎯 P-Bot Table Screenshot Capture")
    print("=" * 40)
    print()
    print("This will capture a screenshot from your OBS Virtual Camera")
    print("for manual region creation.")
    print()
    print("Before starting, make sure:")
    print("  ✓ OBS Studio is running")
    print("  ✓ Virtual Camera is started")
    print("  ✓ Your poker table is visible")
    print("  ✓ All cards you want to detect are dealt and visible")
    print("  ✓ No overlapping windows or popups")
    print()
    
    # Get user confirmation
    response = input("Ready to capture? Press Enter to continue (or 'q' to quit): ").strip().lower()
    if response == 'q':
        print("Cancelled.")
        return
    
    try:
        # Configure logging to be less verbose for this task
        logging.basicConfig(level=logging.WARNING)
        
        # Create hardware capture system
        config = HardwareCaptureConfig(debug_mode=False)
        capture_system = HardwareCaptureSystem(config)
        
        # Capture screenshot
        filename = capture_system.capture_table_screenshot_for_regions()
        
        if filename:
            print(f"\n✅ SUCCESS! Screenshot saved as: {filename}")
            print()
            print("🎯 Next Steps:")
            print("   1. Open the screenshot to verify it shows all cards clearly")
            print("   2. Run: python manual_region_calibrator.py")
            print("   3. Click on each card position when prompted")
            print("   4. Test with: python test_enhanced_integration.py")
            print()
            print("The manual calibrator will let you click on each card")
            print("position to create accurate regions.")
        else:
            print("\n❌ Failed to capture screenshot")
            print("Check that:")
            print("  - OBS Studio is running")
            print("  - Virtual Camera is started in OBS")
            print("  - UGREEN capture device is working")
        
        # Cleanup
        if capture_system.virtual_camera:
            capture_system.virtual_camera.release()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure OBS Virtual Camera is set up correctly.")

if __name__ == "__main__":
    main()
