#!/usr/bin/env python3
"""
Fix Hardware Capture Issues
Comprehensive fix for region loading and analysis display problems
"""

import os
import sys
import json

def fix_region_coordinate_format():
    """Fix region coordinate format in manual region file"""
    try:
        region_file = "regions/region_config_manual.json"
        
        if not os.path.exists(region_file):
            print(f"❌ Region file not found: {region_file}")
            return False
        
        print(f"🔧 Fixing region coordinate format in {region_file}")
        
        # Read current file
        with open(region_file, 'r') as f:
            data = json.load(f)
        
        if 'regions' not in data:
            print("❌ No regions found in file")
            return False
        
        # Check current format and convert if needed
        sample_region = list(data['regions'].values())[0]
        if 'x_percent' in sample_region:
            print("✅ Regions already in percentage format")
            return True
        
        # Convert from percentage to explicit percentage format
        print("🔄 Converting coordinate format...")
        
        for region_name, region_info in data['regions'].items():
            # Current format has percentages as decimal values
            x_val = region_info['x']
            y_val = region_info['y']
            w_val = region_info['width']
            h_val = region_info['height']
            
            # Convert to explicit percentage format
            data['regions'][region_name] = {
                'x_percent': x_val / 100.0,  # Convert to decimal
                'y_percent': y_val / 100.0,
                'width_percent': w_val / 100.0,
                'height_percent': h_val / 100.0
            }
            
            print(f"   {region_name}: ({x_val:.1f}, {y_val:.1f}) -> ({x_val/100:.3f}, {y_val/100:.3f})")
        
        # Save fixed file
        backup_file = region_file + ".backup"
        os.rename(region_file, backup_file)
        print(f"💾 Backup saved to {backup_file}")
        
        with open(region_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Fixed region coordinate format")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing region format: {e}")
        return False

def create_debug_test_script():
    """Create a simple debug test script"""
    content = '''#!/usr/bin/env python3
"""
Debug Hardware Capture
Simple test script to debug hardware capture issues
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_hardware_capture():
    """Test hardware capture with detailed debugging"""
    print("🧪 Hardware Capture Debug Test")
    print("=" * 50)
    
    try:
        from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
        
        # Create config
        config = HardwareCaptureConfig(
            debug_mode=True,
            recognition_method="enhanced"
        )
        
        # Initialize system
        capture_system = HardwareCaptureSystem(config)
        print("✅ Hardware capture system initialized")
        
        # Test connection
        if capture_system.connect_to_virtual_camera():
            print(f"✅ Connected to virtual camera at index {capture_system.camera_index}")
        else:
            print("❌ Failed to connect to virtual camera")
            return
        
        # Test frame capture
        frame = capture_system.capture_from_virtual_camera()
        if frame is not None:
            print(f"✅ Frame captured: {frame.shape}")
        else:
            print("❌ Frame capture failed")
            return
        
        # Test region loading with detailed output
        print("\\n🔧 Testing region loading...")
        success = capture_system.auto_calibrate_from_hardware()
        print(f"Region loading result: {success}")
        
        if hasattr(capture_system, 'calibrated_regions') and capture_system.calibrated_regions:
            print(f"\\n📍 Loaded {len(capture_system.calibrated_regions)} regions:")
            for name, data in capture_system.calibrated_regions.items():
                print(f"   {name}: x={data.get('x', 'ERROR')}, y={data.get('y', 'ERROR')}, w={data.get('width', 'ERROR')}, h={data.get('height', 'ERROR')}")
        else:
            print("❌ No regions loaded")
        
        # Test analysis
        print("\\n🎯 Testing card analysis...")
        game_state = capture_system.analyze_current_frame()
        
        if game_state:
            hero_cards = game_state.get('hero_cards', [])
            community_cards = game_state.get('community_cards', [])
            confidence = game_state.get('analysis_confidence', 0)
            
            print(f"✅ Analysis completed:")
            print(f"   Hero cards: {len(hero_cards)}")
            print(f"   Community cards: {len(community_cards)}")
            print(f"   Confidence: {confidence:.3f}")
            
            for i, card in enumerate(hero_cards):
                print(f"   Hero {i+1}: {card}")
            for i, card in enumerate(community_cards):
                print(f"   Community {i+1}: {card}")
        else:
            print("❌ Analysis failed or no cards detected")
        
        # Cleanup
        if hasattr(capture_system, 'virtual_camera'):
            capture_system.virtual_camera.release()
        
        print("\\n🎉 Debug test completed!")
        
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hardware_capture()
'''
    
    with open("debug_hardware_capture.py", 'w') as f:
        f.write(content)
    
    print("✅ Created debug_hardware_capture.py")

def main():
    """Main fix process"""
    print("🔧 HARDWARE CAPTURE FIXES")
    print("=" * 50)
    
    # Fix 1: Region coordinate format
    if fix_region_coordinate_format():
        print("✅ Region coordinate format fixed")
    else:
        print("❌ Region coordinate format fix failed")
    
    # Fix 2: Create debug script
    create_debug_test_script()
    
    print("\\n📋 NEXT STEPS:")
    print("1. Run: python debug_hardware_capture.py")
    print("2. Check if regions load correctly")
    print("3. Test Modern UI: python start_clean_ui.py")
    print("4. Use 'Connect OBS' then 'Manual Capture'")

if __name__ == "__main__":
    main()
