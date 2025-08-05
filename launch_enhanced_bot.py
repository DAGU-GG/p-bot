"""
Enhanced Bot Launcher
Launches your poker bot with enhanced OCR and auto-calibration features
"""

import os
import sys
import logging
import time

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _print_banner():
    """Print welcome banner with features."""
    print("="*70)
    print("🚀 ENHANCED POKER BOT LAUNCHER 🚀")
    print("="*70)
    print()
    print("Features:")
    print("✅ Automatic table layout detection")
    print("✅ Advanced OCR card recognition")
    print("✅ 4-color deck support") 
    print("✅ Multiple recognition methods")
    print("✅ Debug visualization")
    print("✅ Safe educational branding")
    print()

def _import_enhanced_systems():
    """Import enhanced systems and handle errors."""
    try:
        from enhanced_integration import EnhancedPokerBot, upgrade_existing_bot
        logger.info("Enhanced systems imported successfully")
        return EnhancedPokerBot, upgrade_existing_bot
    except ImportError as e:
        logger.error(f"Failed to import enhanced systems: {e}")
        print("❌ Error: Enhanced systems not available")
        return None, None

def _try_import_existing_bot():
    """Attempt to import existing bot from multiple locations."""
    import_attempts = [
        'poker_bot.PokerStarsBot',
        'src.poker_bot.PokerStarsBot', 
        'poker_bot',
        'src.poker_bot'
    ]
    
    for attempt in import_attempts:
        try:
            if '.' in attempt:
                module_path, class_name = attempt.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                bot_class = getattr(module, class_name)
                existing_bot = bot_class()
                logger.info(f"Existing bot imported from {attempt}")
                return existing_bot
            else:
                module = __import__(attempt)
                if hasattr(module, 'PokerStarsBot'):
                    existing_bot = module.PokerStarsBot()
                    logger.info(f"Existing bot imported from {attempt}")
                    return existing_bot
        except ImportError:
            continue
    return None

def _create_or_upgrade_bot(EnhancedPokerBot, upgrade_existing_bot):
    """Create new enhanced bot or upgrade existing one."""
    existing_bot = None
    try:
        existing_bot = _try_import_existing_bot()
    except Exception as e:
        logger.warning(f"Could not import existing bot: {e}")
    
    if existing_bot:
        print("🔄 Upgrading existing bot with enhanced features...")
        enhanced_bot = upgrade_existing_bot(existing_bot)
        print("✅ Bot upgrade complete!")
    else:
        print("🆕 Creating new enhanced bot...")
        enhanced_bot = EnhancedPokerBot()
        print("✅ Enhanced bot created!")
    
    return enhanced_bot

def _display_menu():
    """Display main menu options."""
    print()
    print("🎯 LAUNCH OPTIONS:")
    print("1. 🔧 Auto-calibrate table layout")
    print("2. 🎮 Launch with modern UI")
    print("3. 🧪 Test with screenshot")
    print("4. 📊 Analyze current game state")
    print("5. 🎨 Create visualization")
    print("0. ❌ Exit")
    print()

def _handle_auto_calibration(enhanced_bot):
    """Handle auto-calibration option."""
    print("\n🔧 Starting auto-calibration...")
    if enhanced_bot.auto_calibrate():
        print("✅ Auto-calibration successful!")
        enhanced_bot.create_visualization()
        print("📊 Visualization saved as 'enhanced_bot_visualization.png'")
    else:
        print("❌ Auto-calibration failed")

def _handle_modern_ui():
    """Handle modern UI launch option."""
    print("\n🎮 Launching modern UI...")
    try:
        from src.modern_ui import main as ui_main
        ui_main()
    except ImportError:
        print("❌ Modern UI not available")
    except Exception as e:
        logger.error(f"UI launch error: {e}")

def _handle_screenshot_test():
    """Handle screenshot test option."""
    print("\n🧪 Testing with screenshot...")
    from enhanced_integration import test_enhanced_system
    test_enhanced_system()

def _handle_game_analysis(enhanced_bot):
    """Handle current game state analysis."""
    print("\n📊 Analyzing current game state...")
    result = enhanced_bot.analyze_game_state(debug=True)
    if result:
        print("✅ Analysis complete!")
        print(f"Hero cards: {result.get('hero_cards', 'None')}")
        print(f"Community cards: {result.get('community_cards', 'None')}")
        print(f"Valid: {result.get('valid', False)}")
    else:
        print("❌ Analysis failed")

def _handle_visualization(enhanced_bot):
    """Handle visualization creation."""
    print("\n🎨 Creating visualization...")
    vis = enhanced_bot.create_visualization()
    if vis is not None:
        print("✅ Visualization created!")
    else:
        print("❌ Visualization failed")

def _process_user_choice(choice, enhanced_bot):
    """Process user menu choice."""
    if choice == '0':
        print("👋 Goodbye!")
        return False
    elif choice == '1':
        _handle_auto_calibration(enhanced_bot)
    elif choice == '2':
        _handle_modern_ui()
    elif choice == '3':
        _handle_screenshot_test()
    elif choice == '4':
        _handle_game_analysis(enhanced_bot)
    elif choice == '5':
        _handle_visualization(enhanced_bot)
    else:
        print("❌ Invalid option. Please try again.")
    return True

def main():
    """Main launcher function"""
    _print_banner()
    
    # Import enhanced systems
    EnhancedPokerBot, upgrade_existing_bot = _import_enhanced_systems()
    if not EnhancedPokerBot:
        return
    
    # Create or upgrade bot
    enhanced_bot = _create_or_upgrade_bot(EnhancedPokerBot, upgrade_existing_bot)
    _display_menu()
    
    while True:
        try:
            choice = input("Select option (0-5): ").strip()
            
            if not _process_user_choice(choice, enhanced_bot):
                break
                
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
