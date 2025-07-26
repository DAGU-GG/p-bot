#!/usr/bin/env python3
"""Simple test to verify template name mapping logic"""

import os

def test_name_mapping():
    print("Testing card template name mapping...")
    
    # This is the mapping logic from the CardRecognizer
    rank_mapping = {
        '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
        '10': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
    }
    suit_mapping = {
        'hearts': 'h', 'diamonds': 'd', 'clubs': 'c', 'spades': 's'
    }
    
    # Check existing files
    template_dir = "card_templates"
    if os.path.exists(template_dir):
        files = [f for f in os.listdir(template_dir) if f.endswith('.png')]
        print(f'Found {len(files)} template files')
        
        mapped_count = 0
        print("\nFile -> Internal mapping:")
        
        for file_rank, internal_rank in rank_mapping.items():
            for file_suit, internal_suit in suit_mapping.items():
                template_file = f"{file_rank}_{file_suit}.png"
                if template_file in files:
                    internal_name = f"{internal_rank}{internal_suit}"
                    print(f"  {template_file} -> {internal_name}")
                    mapped_count += 1
        
        print(f"\n✅ Successfully mapped {mapped_count}/52 card templates")
        
        if mapped_count == 52:
            print("🎉 All card templates found and mapped correctly!")
        elif mapped_count > 40:
            print("✅ Most card templates found - good for testing")
        else:
            print("⚠️  Some card templates missing")
            
    else:
        print("❌ Template directory not found")

if __name__ == "__main__":
    test_name_mapping()
