#!/usr/bin/env python3
"""
Fix RegionLoader to properly handle user-created regions
"""

import os
import json
import logging
from typing import Dict, Optional, Any

class FixedRegionLoader:
    """Fixed region loader that properly handles coordinate formats"""
    
    def __init__(self, config_file=None):
        self.logger = logging.getLogger(__name__)
        
        # Try multiple region file locations
        self.region_files = [
            "regions/region_config_manual.json",  # User-created regions (priority)
            "regions/region_config.json",         # Auto-generated regions
            "region_config.json",                 # Root level config
            "src/region_config.json"              # Src level config
        ]
        
        if config_file:
            self.region_files.insert(0, config_file)
    
    def load_regions(self) -> Dict[str, Dict]:
        """Load regions with proper coordinate format handling"""
        
        for region_file in self.region_files:
            if not os.path.exists(region_file):
                continue
                
            try:
                with open(region_file, 'r') as f:
                    saved_data = json.load(f)
                
                # Handle nested 'regions' key
                if 'regions' in saved_data:
                    saved_regions = saved_data['regions']
                else:
                    saved_regions = saved_data
                
                if not saved_regions:
                    continue
                
                # Convert coordinates to proper decimal format
                converted_regions = {}
                
                for region_name, region_data in saved_regions.items():
                    if not isinstance(region_data, dict):
                        continue
                    
                    # Handle different coordinate formats
                    if 'x_percent' in region_data:
                        # Already in x_percent format
                        x_val = region_data['x_percent']
                        y_val = region_data['y_percent']
                        w_val = region_data['width_percent']
                        h_val = region_data['height_percent']
                    elif 'x' in region_data:
                        # Check if it's percentage (0-100) or decimal (0-1)
                        x_val = region_data['x']
                        y_val = region_data['y']
                        w_val = region_data['width']
                        h_val = region_data['height']
                        
                        # If values are > 1, they're percentages that need conversion
                        if x_val > 1.0:
                            x_val = x_val / 100.0
                            y_val = y_val / 100.0
                            w_val = w_val / 100.0
                            h_val = h_val / 100.0
                    else:
                        continue
                    
                    # Store in standardized format (decimal 0.0-1.0)
                    converted_regions[region_name] = {
                        'x': x_val,
                        'y': y_val,
                        'width': w_val,
                        'height': h_val
                    }
                
                if converted_regions:
                    self.logger.info(f"✅ Loaded {len(converted_regions)} regions from {region_file}")
                    return converted_regions
                    
            except Exception as e:
                self.logger.warning(f"Could not load {region_file}: {e}")
                continue
        
        self.logger.error("❌ No valid region files found!")
        return {}
    
    def get_hero_card_regions(self) -> Dict[str, Dict]:
        """Get hero card regions in CardRecognizer format"""
        regions = self.load_regions()
        hero_regions = {}
        
        # Map user format to system format
        mapping = {
            'hero_card_1': 'hero_card1',
            'hero_card_2': 'hero_card2'
        }
        
        for user_key, system_key in mapping.items():
            if user_key in regions:
                region = regions[user_key]
                hero_regions[system_key] = {
                    'x_percent': region['x'],
                    'y_percent': region['y'],
                    'width_percent': region['width'],
                    'height_percent': region['height']
                }
        
        return hero_regions
    
    def get_community_card_regions(self) -> Dict[str, Dict]:
        """Get community card regions in CommunityCardDetector format"""
        regions = self.load_regions()
        community_regions = {}
        
        # Map user format to system format
        for i in range(1, 6):
            user_key = f'community_card_{i}'
            system_key = f'card_{i}'
            
            if user_key in regions:
                region = regions[user_key]
                community_regions[system_key] = {
                    'x_percent': region['x'],
                    'y_percent': region['y'],
                    'width_percent': region['width'],
                    'height_percent': region['height']
                }
        
        return community_regions

def test_fixed_loader():
    """Test the fixed region loader"""
    print("\n🧪 Testing Fixed Region Loader...")
    
    try:
        loader = FixedRegionLoader()
        
        # Test basic region loading
        regions = loader.load_regions()
        print(f"✅ Loaded {len(regions)} base regions")
        
        # Test hero card regions
        hero_regions = loader.get_hero_card_regions()
        print(f"✅ Mapped {len(hero_regions)} hero card regions:")
        for name, region in hero_regions.items():
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        
        # Test community card regions
        community_regions = loader.get_community_card_regions()
        print(f"✅ Mapped {len(community_regions)} community card regions:")
        for name, region in list(community_regions.items())[:3]:
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fixed loader test failed: {e}")
        return False

def create_visual_validation():
    """Create visual validation of region positions"""
    print("\n🖼️ Creating Visual Validation...")
    
    test_image = "poker_table_for_regions_20250805_023128.png"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return False
    
    try:
        import cv2
        
        # Load image
        img = cv2.imread(test_image)
        height, width = img.shape[:2]
        
        # Load regions using fixed loader
        loader = FixedRegionLoader()
        regions = loader.load_regions()
        
        # Create visualization
        vis_img = img.copy()
        
        for region_name, region_data in regions.items():
            # Calculate pixel coordinates using FIXED method
            x = int(region_data['x'] * width)
            y = int(region_data['y'] * height)
            w = int(region_data['width'] * width)
            h = int(region_data['height'] * height)
            
            # Choose color based on region type
            if 'hero' in region_name:
                color = (0, 255, 255)  # Yellow for hero cards
            elif 'community' in region_name:
                color = (0, 255, 0)    # Green for community cards
            else:
                color = (255, 0, 0)    # Blue for others
            
            # Draw rectangle
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), color, 3)
            
            # Add label
            label = region_name.replace('_', ' ').title()
            cv2.putText(vis_img, label, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Save visualization
        output_file = "region_validation_fixed.png"
        cv2.imwrite(output_file, vis_img)
        
        print(f"✅ Visual validation saved: {output_file}")
        print("   🔍 Check this image to verify regions are positioned correctly over cards")
        
        return True
        
    except Exception as e:
        print(f"❌ Visual validation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 CRITICAL REGION COORDINATE FIX")
    print("=" * 50)
    
    # Fix coordinate formats
    fix_region_coordinate_format()
    
    # Test fixed loader
    if test_fixed_loader():
        print("\n✅ Fixed loader working correctly")
    else:
        print("\n❌ Fixed loader test failed")
        sys.exit(1)
    
    # Create visual validation
    if create_visual_validation():
        print("\n✅ Visual validation created")
    else:
        print("\n❌ Visual validation failed")
    
    print("\n🎯 FIXES COMPLETE!")
    print("Next steps:")
    print("1. Check region_validation_fixed.png to verify positions")
    print("2. Run: python test_fixed_integration.py")
    print("3. Test recognition with corrected regions")