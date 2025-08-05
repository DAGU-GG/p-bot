"""
Region Configuration Loader
Centralized loading and management of detection regions.
"""

import os
import json
import logging
from typing import Dict, Optional, Any


class RegionLoader:
    """Centralized region configuration loader."""
    
    def __init__(self, config_file=None):
        """
        Initialize the region loader.
        
        Args:
            config_file: Optional path to the region configuration file.
                         If not provided, defaults to 'regions/region_config.json'
        """
        self.logger = logging.getLogger(__name__)
        self.regions_file = config_file if config_file else 'region_config.json'
        # REMOVED: No more default regions - only use saved regions
        
    def load_regions(self) -> Dict[str, Dict]:
        """Load regions from file with proper coordinate handling."""
        try:
            if os.path.exists(self.regions_file):
                with open(self.regions_file, 'r') as f:
                    saved_data = json.load(f)
                
                # Handle the format from region_config.json (has nested 'regions' key)
                if 'regions' in saved_data:
                    saved_regions = saved_data['regions']
                else:
                    saved_regions = saved_data
                
                # Convert coordinates to decimal format (0.0-1.0) if needed
                # region_config.json already stores as decimal (not percentage)
                converted_regions = {}
                for region_name, region_data in saved_regions.items():
                    if isinstance(region_data, dict) and 'x' in region_data:
                        # No division needed - already in decimal format
                        converted_regions[region_name] = {
                            'x': region_data['x'],
                            'y': region_data['y'],
                            'width': region_data['width'],
                            'height': region_data['height']
                        }
                        self.logger.debug(f"Loaded region {region_name}: x={region_data['x']:.4f}, y={region_data['y']:.4f}")
                
                if converted_regions:
                    self.logger.info(f"Successfully loaded {len(converted_regions)} saved regions from {self.regions_file}")
                    return converted_regions
                    
        except Exception as e:
            self.logger.error(f"Could not load saved regions: {e}")
        
        # NO FALLBACK - If regions don't exist, the system should fail gracefully
        if not os.path.exists(self.config_file):
            self.logger.error("NO SAVED REGIONS FOUND - Please calibrate regions first!")
        return {}
    
    def get_community_card_regions(self) -> Dict[str, Dict]:
        """Get community card regions in the format expected by CommunityCardDetector."""
        regions = self.load_regions()
        community_regions = {}
        
        for i in range(1, 6):
            region_name = f'community_card_{i}'
            card_key = f'card_{i}'
            
            if region_name in regions:
                region = regions[region_name]
                community_regions[card_key] = {
                    'x_percent': region['x'],
                    'y_percent': region['y'],
                    'width_percent': region['width'],
                    'height_percent': region['height']
                }
        
        return community_regions
    
    def get_hero_card_regions(self) -> Dict[str, Dict]:
        """Get hero card regions in the format expected by CardRecognizer."""
        regions = self.load_regions()
        hero_regions = {}
        
        if 'hero_card_1' in regions:
            region = regions['hero_card_1']
            hero_regions['hero_card1'] = {
                'x_percent': region['x'],
                'y_percent': region['y'],
                'width_percent': region['width'],
                'height_percent': region['height']
            }
            
        if 'hero_card_2' in regions:
            region = regions['hero_card_2']
            hero_regions['hero_card2'] = {
                'x_percent': region['x'],
                'y_percent': region['y'],
                'width_percent': region['width'],
                'height_percent': region['height']
            }
        
        return hero_regions
    
    def get_pot_region(self) -> Optional[Dict]:
        """Get pot region for table analyzer."""
        regions = self.load_regions()
        
        if 'pot_area' in regions:
            region = regions['pot_area']
            return {
                'x_percent': region['x'],
                'y_percent': region['y'],
                'width_percent': region['width'],
                'height_percent': region['height']
            }
        
    def regions_exist(self) -> bool:
        """Check if regions file exists and contains valid regions."""
        try:
            if not os.path.exists(self.regions_file):
                return False
                
            with open(self.regions_file, 'r') as f:
                data = json.load(f)
                
            # Check if data has regions
            if 'regions' in data:
                regions = data['regions']
            else:
                regions = data
                
            # Must have at least some regions to be considered valid
            return len(regions) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking regions file: {e}")
            return False
    
    def regions_exist(self) -> bool:
        """Check if saved regions file exists."""
        return os.path.exists(self.regions_file)
