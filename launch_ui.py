#!/usr/bin/env python3
"""
Simple launcher for the P-Bot 2 Modern UI with Live Recognition
"""

import os
import sys
import logging

# Add the project directory to the path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)
sys.path.insert(0, os.path.join(project_dir, 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def main():
    """Main launcher function"""
    try:
        print("🎯 Starting P-Bot 2 - Modern UI with Live Recognition")
        print("="*60)
        
        # Import and create the main window
        from src.ui.main_window import MainWindow
        
        # Create main window with default settings
        app = MainWindow(
            recognition_system='enhanced',
            show_regions=False,
            config_path='region_config.json',
            security_mode='safe'
        )
        
        print("✅ Main UI initialized successfully")
        print("🚀 Starting application...")
        
        # Run the application
        app.run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print(f"Error details: {type(e).__name__}: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
