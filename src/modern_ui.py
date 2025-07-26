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
    parser = argparse.ArgumentParser(description='Modern PokerStars Bot UI')
    parser.add_argument('--recognition', type=str, default='standard', 
                      choices=['standard', 'improved', 'direct'],
                      help='Card recognition system to use')
    parser.add_argument('--show-regions', action='store_true',
                      help='Show card recognition regions on the livestream')
    parser.add_argument('--config', type=str, default='region_config.json',
                      help='Path to the region configuration file')
    return parser.parse_args()


def main():
    """Main entry point for the modern UI application."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Print startup information
        print(f"Starting with recognition system: {args.recognition}")
        print(f"Region visualization: {'Enabled' if args.show_regions else 'Disabled'}")
        print(f"Using configuration file: {args.config}")
        
        # Initialize and run the main window
        app = MainWindow(
            recognition_system=args.recognition,
            show_regions=args.show_regions,
            config_path=args.config
        )
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        import tkinter.messagebox as messagebox
        messagebox.showerror("Fatal Error", f"Error starting application: {e}")


if __name__ == "__main__":
    main()