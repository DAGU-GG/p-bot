"""
Quick Visual Inspector
Opens the captured images to see what the bot is analyzing
"""

import cv2
import os
import sys

def show_captured_images():
    """Display the captured images for visual inspection"""
    
    # Find the latest debug images
    debug_files = [f for f in os.listdir('.') if f.startswith('debug_') and f.endswith('.png')]
    
    if not debug_files:
        print("❌ No debug images found. Run debug_live_capture.py first.")
        return
    
    # Sort by modification time to get latest
    debug_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    print("🖼️ Found debug images:")
    for i, file in enumerate(debug_files[:10]):  # Show first 10
        print(f"  {i+1}. {file}")
    
    # Show the full frame with regions
    full_frame_files = [f for f in debug_files if 'debug_frame_with_regions_' in f]
    if full_frame_files:
        latest_full = full_frame_files[0]
        print(f"\n📸 Opening: {latest_full}")
        
        try:
            img = cv2.imread(latest_full)
            if img is not None:
                # Resize for display if too large
                height, width = img.shape[:2]
                if width > 1400:
                    scale = 1400 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    img = cv2.resize(img, (new_width, new_height))
                
                cv2.imshow('Poker Table with Regions', img)
                print("📋 Instructions:")
                print("  • Green rectangles = Hero card regions")
                print("  • Red rectangles = Community card regions")
                print("  • Check if regions align with actual cards")
                print("  • Press any key to close")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print(f"❌ Could not load {latest_full}")
        except Exception as e:
            print(f"❌ Error displaying image: {e}")
    
    # Show individual regions that had content
    hero_files = [f for f in debug_files if 'debug_hero_card_' in f]
    community_files = [f for f in debug_files if 'debug_community_card_' in f]
    
    print(f"\n🃏 Hero card regions ({len(hero_files)} found):")
    for file in hero_files[:2]:  # Show latest 2
        print(f"  📁 {file}")
        try:
            img = cv2.imread(file)
            if img is not None:
                # Resize small regions for better viewing
                img = cv2.resize(img, (120, 168))  # 2x scale
                cv2.imshow(f'Hero Card: {file}', img)
            else:
                print(f"    ❌ Could not load {file}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print(f"\n🎴 Community card regions ({len(community_files)} found):")
    for file in community_files[:5]:  # Show latest 5
        print(f"  📁 {file}")
        try:
            img = cv2.imread(file)
            if img is not None:
                img = cv2.resize(img, (120, 168))  # 2x scale
                cv2.imshow(f'Community: {file}', img)
            else:
                print(f"    ❌ Could not load {file}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    if hero_files or community_files:
        print("\n👀 Visual inspection windows opened.")
        print("📋 Check if:")
        print("  1. Hero card regions show your hole cards")
        print("  2. Community regions show the board cards") 
        print("  3. Regions aren't just showing green table")
        print("  4. Cards are clearly visible and not cut off")
        print("\nPress any key in any window to close all...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    show_captured_images()
