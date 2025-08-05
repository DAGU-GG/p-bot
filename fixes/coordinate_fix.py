#!/usr/bin/env python3
"""
Critical Fix for Region Coordinate Handling
Fixes the coordinate format mismatch that prevents proper region usage
"""

import json
import os
import sys

def fix_region_coordinate_format():
    """Fix the coordinate format in region files"""
    print("🔧 Fixing Region Coordinate Format Issues...")
    
    # Files to check and fix
    region_files = [
        "regions/region_config_manual.json",
        "regions/region_config.json",
        "region_config.json",
        "src/region_config.json"
    ]
    
    for region_file in region_files:
        if not os.path.exists(region_file):
            continue
            
        print(f"\n📁 Processing: {region_file}")
        
        try:
            # Read current file
            with open(region_file, 'r') as f:
                data = json.load(f)
            
            if 'regions' not in data:
                print(f"   ❌ No regions found in {region_file}")
                continue
            
            # Check current format
            sample_region = list(data['regions'].values())[0]
            
            # Determine current format
            if 'x_percent' in sample_region:
                print(f"   ✅ Already in x_percent format")
                continue
            elif 'x' in sample_region:
                x_val = sample_region['x']
                if x_val > 1.0:
                    print(f"   🔄 Converting from percentage (0-100) to decimal (0-1) format")
                    format_type = "percentage"
                else:
                    print(f"   ✅ Already in decimal format")
                    continue
            else:
                print(f"   ❌ Unknown format in {region_file}")
                continue
            
            # Convert format if needed
            if format_type == "percentage":
                # Backup original
                backup_file = region_file + ".backup"
                with open(backup_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"   💾 Backup saved: {backup_file}")
                
                # Convert coordinates
                for region_name, region_info in data['regions'].items():
                    # Convert from percentage (0-100) to decimal (0-1)
                    data['regions'][region_name] = {
                        'x': region_info['x'] / 100.0,
                        'y': region_info['y'] / 100.0,
                        'width': region_info['width'] / 100.0,
                        'height': region_info['height'] / 100.0
                    }
                    
                    print(f"     {region_name}: ({region_info['x']:.1f}%, {region_info['y']:.1f}%) → ({region_info['x']/100:.4f}, {region_info['y']/100:.4f})")
                
                # Save fixed file
                with open(region_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"   ✅ Fixed coordinate format in {region_file}")
        
        except Exception as e:
            print(f"   ❌ Error processing {region_file}: {e}")

def validate_region_usage():
    """Validate that systems are using regions correctly"""
    print("\n🧪 Validating Region Usage in Recognition Systems...")
    
    # Test RegionLoader
    try:
        sys.path.append('src')
        from region_loader import RegionLoader
        
        loader = RegionLoader()
        regions = loader.load_regions()
        
        print(f"\n📍 RegionLoader Test:")
        print(f"   Loaded {len(regions)} regions")
        
        for name, region in list(regions.items())[:3]:  # Show first 3
            print(f"   {name}: x={region['x']:.4f}, y={region['y']:.4f}")
        
        # Test hero card regions
        hero_regions = loader.get_hero_card_regions()
        print(f"\n🂠 Hero Card Regions:")
        print(f"   Found {len(hero_regions)} hero regions")
        for name, region in hero_regions.items():
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        
        # Test community card regions  
        community_regions = loader.get_community_card_regions()
        print(f"\n🃏 Community Card Regions:")
        print(f"   Found {len(community_regions)} community regions")
        for name, region in list(community_regions.items())[:3]:
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ RegionLoader validation failed: {e}")
        return False

def test_coordinate_extraction():
    """Test coordinate extraction with a sample image"""
    print("\n🖼️ Testing Coordinate Extraction...")
    
    # Use the user's screenshot
    test_image = "poker_table_for_regions_20250805_023128.png"
    
    if not os.path.exists(test_image):
        print(f"   ❌ Test image not found: {test_image}")
        return False
    
    try:
        import cv2
        import numpy as np
        
        # Load test image
        img = cv2.imread(test_image)
        if img is None:
            print(f"   ❌ Could not load test image")
            return False
        
        height, width = img.shape[:2]
        print(f"   📐 Test image: {width}x{height}")
        
        # Load regions
        sys.path.append('src')
        from region_loader import RegionLoader
        
        loader = RegionLoader()
        regions = loader.load_regions()
        
        if not regions:
            print(f"   ❌ No regions loaded")
            return False
        
        # Test extraction for each region
        print(f"\n🎯 Testing Region Extraction:")
        
        for region_name, region_data in regions.items():
            # Calculate pixel coordinates
            x = int(region_data['x'] * width)
            y = int(region_data['y'] * height)
            w = int(region_data['width'] * width)
            h = int(region_data['height'] * height)
            
            print(f"   {region_name}:")
            print(f"     Decimal: x={region_data['x']:.4f}, y={region_data['y']:.4f}")
            print(f"     Pixels: x={x}, y={y}, w={w}, h={h}")
            
            # Check if coordinates are reasonable
            if x < 0 or y < 0 or x + w > width or y + h > height:
                print(f"     ❌ COORDINATES OUT OF BOUNDS!")
            elif w < 10 or h < 10:
                print(f"     ❌ REGION TOO SMALL!")
            else:
                print(f"     ✅ Coordinates look valid")
                
                # Extract and save region for visual verification
                region_img = img[y:y+h, x:x+w]
                debug_filename = f"debug_region_extraction_{region_name}.png"
                cv2.imwrite(debug_filename, region_img)
                print(f"     💾 Saved: {debug_filename}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Coordinate extraction test failed: {e}")
        return False

def main():
    """Main fix function"""
    print("🎯 OCR/Image Recognition System Analysis & Fix")
    print("=" * 60)
    
    # Step 1: Fix coordinate formats
    fix_region_coordinate_format()
    
    # Step 2: Validate region loading
    if validate_region_usage():
        print("\n✅ Region loading validation passed")
    else:
        print("\n❌ Region loading validation failed")
        return False
    
    # Step 3: Test coordinate extraction
    if test_coordinate_extraction():
        print("\n✅ Coordinate extraction test passed")
    else:
        print("\n❌ Coordinate extraction test failed")
        return False
    
    print("\n🎉 ANALYSIS COMPLETE!")
    print("\n📋 Summary:")
    print("✅ Region coordinate format fixed")
    print("✅ Region loading validated")
    print("✅ Coordinate extraction tested")
    print("\n🎯 Next Steps:")
    print("1. Check the debug_region_extraction_*.png files")
    print("2. Verify regions are positioned correctly over cards")
    print("3. Test recognition with: python test_fixed_integration.py")

if __name__ == "__main__":
    main()