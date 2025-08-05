"""
PokerStars Bot - Modern UI Application (Refactored)
Entry point for the modern UI application using modular components.
"""

import sys
import os
import argparse

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Modern PokerStars Bot UI - Security Enhanced')
    parser.add_argument('--recognition', type=str, default='standard', 
                      choices=['standard', 'improved', 'direct'],
                      help='Card recognition system to use')
    parser.add_argument('--show-regions', action='store_true',
                      help='Show card recognition regions on the livestream')
    parser.add_argument('--config', type=str, default='region_config.json',
                      help='Path to the region configuration file')
    parser.add_argument('--security-mode', type=str, default='safe',
                      choices=['safe', 'minimal', 'manual'],
                      help='Security mode: safe (8-12s intervals), minimal (15-30s), manual (no auto capture)')
    return parser.parse_args()


def main():
    """Main entry point for the modern UI application."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Print startup information with security emphasis
        print(f"=== POKERSTARS BOT - SECURITY MODE ===")
        print(f"Recognition system: {args.recognition}")
        print(f"Security mode: {args.security_mode.upper()}")
        print(f"Region visualization: {'Enabled' if args.show_regions else 'Disabled'}")
        print(f"Configuration file: {args.config}")
        
        if args.security_mode == 'safe':
            print("⚠️  SAFE MODE: 8-12 second intervals with session limits")
        elif args.security_mode == 'minimal':
            print("⚠️  MINIMAL MODE: 15-30 second intervals - safest automated option")
        elif args.security_mode == 'manual':
            print("✅ MANUAL MODE: No automatic capture - manual clicks only")
            
        print("="*40)
        
        # Initialize and run the main window
        app = MainWindow(
            recognition_system=args.recognition,
            show_regions=args.show_regions,
            config_path=args.config,
            security_mode=args.security_mode
        )
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        import tkinter.messagebox as messagebox
        messagebox.showerror("Fatal Error", f"Error starting application: {e}")


if __name__ == "__main__":
    main()