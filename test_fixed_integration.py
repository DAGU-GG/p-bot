#!/usr/bin/env python3
"""
Test script for the fixed hardware capture + Modern UI integration
Verifies all systems work correctly before full live testing
"""

import os
import sys
import time

def test_hardware_capture():
    """Test hardware capture system standalone"""
    print("=" * 60)
    print("TESTING HARDWARE CAPTURE SYSTEM")
    print("=" * 60)
    
    try:
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        
        # Create config with debug disabled to prevent screenshot spam
        config = HardwareCaptureConfig(
            debug_mode=True,  # Keep debug logging but no file saving
            recognition_method="enhanced"
        )
        
        # Initialize hardware capture
        capture_system = HardwareCaptureSystem(config)
        print("✅ Hardware capture system initialized")
        
        # Test virtual camera connection
        if capture_system.connect_to_virtual_camera():
            print(f"✅ Connected to OBS Virtual Camera (index {capture_system.camera_index})")
        else:
            print("❌ Could not connect to OBS Virtual Camera")
            print("Make sure:")
            print("  1. OBS Studio is running")
            print("  2. Virtual Camera is started in OBS")
            print("  3. UGREEN capture device is working")
            return False
        
        # Test region loading
        if capture_system.auto_calibrate_from_hardware():
            print("✅ Region configuration loaded successfully")
            region_count = len(capture_system.calibrated_regions)
            print(f"   Loaded {region_count} regions")
            
            for region_name, region_data in list(capture_system.calibrated_regions.items())[:3]:
                print(f"   {region_name}: x={region_data.get('x', 0)}, y={region_data.get('y', 0)}")
        else:
            print("⚠️ Region loading failed - using defaults")
        
        # Test frame capture (no save)
        frame = capture_system.capture_from_virtual_camera()
        if frame is not None:
            print(f"✅ Frame capture working: {frame.shape}")
            
            # Check frame content
            import numpy as np
            avg_pixel = np.mean(frame)
            if avg_pixel < 10:
                print("⚠️ Frame appears mostly black - check OBS video source")
            else:
                print(f"✅ Frame has content (avg brightness: {avg_pixel:.1f})")
        else:
            print("❌ Frame capture failed")
            return False
        
        # Test analysis without saving debug images
        analysis = capture_system.analyze_current_frame()
        if analysis:
            hero_count = len(analysis.get('hero_cards', []))
            community_count = len(analysis.get('community_cards', []))
            print(f"✅ Analysis working: {hero_count} hero, {community_count} community cards")
        else:
            print("⚠️ Analysis returned no results (cards may not be visible)")
        
        # Cleanup
        if hasattr(capture_system, 'virtual_camera'):
            capture_system.virtual_camera.release()
        
        print("✅ Hardware capture test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Hardware capture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_region_config():
    """Test region configuration loading"""
    print("\n" + "=" * 60)
    print("TESTING REGION CONFIGURATION")
    print("=" * 60)
    
    try:
        # Check for region files
        region_files = [
            "regions/region_config_manual.json",
            "regions/region_config.json", 
            "region_config.json"
        ]
        
        found_regions = False
        for region_file in region_files:
            if os.path.exists(region_file):
                print(f"✅ Found region file: {region_file}")
                found_regions = True
                
                # Check file size
                size = os.path.getsize(region_file)
                print(f"   File size: {size} bytes")
                
                # Try to load it
                import json
                with open(region_file, 'r') as f:
                    data = json.load(f)
                    region_count = len(data.get('regions', {}))
                    print(f"   Contains {region_count} regions")
                break
        
        if not found_regions:
            print("❌ No region configuration files found")
            print("You need to run region calibration first")
            return False
        
        print("✅ Region configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Region configuration test failed: {e}")
        return False

def launch_modern_ui():
    """Launch the Modern UI with proper settings"""
    print("\n" + "=" * 60)
    print("LAUNCHING MODERN UI")
    print("=" * 60)
    
    try:
        # Change to src directory
        src_dir = os.path.join(os.path.dirname(__file__), 'src')
        if os.path.exists(src_dir):
            os.chdir(src_dir)
            print(f"✅ Changed to src directory: {src_dir}")
        
        # Launch modern UI
        print("🚀 Starting Modern UI with hardware capture support...")
        print("   Recognition system: IMPROVED")
        print("   Security mode: MANUAL")
        print("   Hardware capture: ENABLED")
        print("\nUI Controls:")
        print("  - Click 'Connect OBS' to connect to virtual camera")
        print("  - Use 'Manual Capture' for safe single screenshots")
        print("  - Check 'Game Info' tab for analysis results")
        print("  - Use 'Test Recognition' if needed")
        print("\n" + "=" * 60)
        
        # Import and run
        import sys
        sys.path.insert(0, os.getcwd())
        from modern_ui import main
        
        # Run with settings
        sys.argv = ['modern_ui.py', '--recognition', 'improved', '--security-mode', 'manual']
        main()
        
    except Exception as e:
        print(f"❌ Modern UI launch failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test and launch sequence"""
    print("🎯 POKERSTARS BOT - FIXED INTEGRATION TEST")
    print("Testing all systems before launch...\n")
    
    # Run tests
    hardware_ok = test_hardware_capture()
    regions_ok = test_region_config()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Hardware Capture: {'✅ PASS' if hardware_ok else '❌ FAIL'}")
    print(f"Region Config:    {'✅ PASS' if regions_ok else '❌ FAIL'}")
    
    if hardware_ok and regions_ok:
        print("\n🎉 All tests passed! Launching Modern UI...")
        time.sleep(2)
        launch_modern_ui()
    else:
        print("\n❌ Some tests failed. Please fix issues before continuing.")
        print("\nCommon fixes:")
        print("  - Make sure OBS Studio is running with Virtual Camera started")
        print("  - Check that UGREEN capture device is connected")
        print("  - Run region calibration if no region files found")
        return False

if __name__ == "__main__":
    main()
