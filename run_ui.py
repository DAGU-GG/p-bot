#!/usr/bin/env python3
"""
UI Launcher Script
Properly launches the Modern UI with correct import paths
"""

import sys
import os
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add src directory to path for imports
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def main():
    """Launch the Modern UI with Hardware Capture Integration"""
    try:
        print("🚀 Starting PokerStars Bot - Modern UI with Live Recognition")
        print("=" * 60)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Test hardware capture connection first
        print("🔧 Initializing Hardware Capture System...")
        try:
            from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
            
            # Create hardware capture config
            config = HardwareCaptureConfig(debug_mode=True)
            hardware_capture = HardwareCaptureSystem(config)
            
            # Test connection
            if hardware_capture.connect_to_virtual_camera():
                print(f"✅ OBS Virtual Camera connected at index {hardware_capture.camera_index}")
            else:
                print("⚠️ OBS Virtual Camera not found - UI will launch without live capture")
                hardware_capture = None
            
            # Test region loading
            if hardware_capture and hardware_capture.auto_calibrate_from_hardware():
                print(f"✅ Loaded {len(hardware_capture.calibrated_regions)} card regions")
            else:
                print("⚠️ No card regions loaded - manual calibration may be needed")
                
        except Exception as e:
            print(f"⚠️ Hardware capture initialization failed: {e}")
            hardware_capture = None
        
        # Import and create the main window
        print("\n🎮 Starting UI Interface...")
        try:
            from ui.main_window import MainWindow
            print("✅ UI modules imported successfully")
        except ImportError:
            # Try alternative path
            from src.ui.main_window import MainWindow
            print("✅ UI modules imported (alternative path)")
        
        print("🎯 Ultimate Card Recognition System ready")
        print("📱 Hardware Capture integration active" if hardware_capture else "📱 Hardware Capture unavailable")
        print("=" * 60)
        
        # Initialize main window with hardware capture
        if hardware_capture:
            app = MainWindow(security_mode='live')  # LIVE MODE for real-time analysis
            # Connect hardware capture to UI for live updates
            app.hardware_capture = hardware_capture
            hardware_capture.set_ui_log_callback(lambda msg: print(f"[LIVE] {msg}"))
            
            # Apply UI fixes after window is created
            def apply_fixes():
                try:
                    from src.ui.fixes.ui_integration_fix import fix_ui_integration
                    fix_ui_integration(app)
                except Exception as e:
                    print(f"Error applying UI fixes: {e}")
            
            app.root.after(1000, apply_fixes)
        else:
            app = MainWindow(security_mode='live')  # LIVE MODE even without hardware capture
        
        # Start the application
        app.run()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nTrying alternative import method...")
        
        # Alternative import method with absolute imports
        try:
            import sys
            import os
            
            # Add both project root and src to path
            project_root = os.path.dirname(os.path.abspath(__file__))
            src_path = os.path.join(project_root, 'src')
            
            for path in [project_root, src_path]:
                if path not in sys.path:
                    sys.path.insert(0, path)
            
            # Try importing with absolute paths
            sys.path.insert(0, os.path.join(project_root, 'src', 'ui'))
            
            from main_window import MainWindow
            
            print("✅ Alternative import successful")
            app = MainWindow()
            app.run()
            
        except Exception as e2:
            print(f"❌ Alternative method failed: {e2}")
            print("\nPlease check that all required modules are available.")
            print("You may need to install dependencies:")
            print("  pip install opencv-python pillow numpy tkinter")
            return False
            
    except Exception as e:
        print(f"❌ Error launching UI: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
        sys.exit(1)
