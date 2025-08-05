"""
Manual Region Calibration Tool
Creates default regions when auto-calibration fails
"""

import json
import os

def create_default_regions():
    """Create default poker table regions for manual calibration"""
    
    # Standard poker table layout (percentages of screen)
    default_regions = {
        "hero_card_1": {
            "x_percent": 0.42,
            "y_percent": 0.75,
            "width_percent": 0.06,
            "height_percent": 0.12,
            "type": "hero_card"
        },
        "hero_card_2": {
            "x_percent": 0.52,
            "y_percent": 0.75,
            "width_percent": 0.06,
            "height_percent": 0.12,
            "type": "hero_card"
        },
        "community_card_1": {
            "x_percent": 0.35,
            "y_percent": 0.42,
            "width_percent": 0.06,
            "height_percent": 0.12,
            "type": "community_card"
        },
        "community_card_2": {
            "x_percent": 0.42,
            "y_percent": 0.42,
            "width_percent": 0.06,
            "height_percent": 0.12,
            "type": "community_card"
        },
        "community_card_3": {
            "x_percent": 0.49,
            "y_percent": 0.42,
            "width_percent": 0.06,
            "height_percent": 0.12,
            "type": "community_card"
        },
        "community_card_4": {
            "x_percent": 0.56,
            "y_percent": 0.42,
            "width_percent": 0.06,
            "height_percent": 0.12,
            "type": "community_card"
        },
        "community_card_5": {
            "x_percent": 0.63,
            "y_percent": 0.42,
            "width_percent": 0.06,
            "height_percent": 0.12,
            "type": "community_card"
        }
    }
    
    # Save to region_config.json for the old system
    with open("region_config.json", "w") as f:
        json.dump(default_regions, f, indent=2)
    
    # Also save in the src directory
    src_path = "src/region_config.json"
    with open(src_path, "w") as f:
        json.dump(default_regions, f, indent=2)
    
    print("✅ Default regions created successfully!")
    print("Files created:")
    print("  - region_config.json")
    print("  - src/region_config.json")
    print("\nThese regions are generic placeholders.")
    print("You can adjust them once you have video feed in OBS.")
    
    return default_regions

def main():
    """Main function"""
    print("Creating default poker table regions...")
    create_default_regions()
    print("\nTo get video feed working:")
    print("1. Make sure PokerStars is running on laptop")
    print("2. Check HDMI cable connections")
    print("3. Add UGREEN capture card as video source in OBS")
    print("4. Start Virtual Camera in OBS")

if __name__ == "__main__":
    main()
