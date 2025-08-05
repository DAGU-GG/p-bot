#!/usr/bin/env python3
"""
Start Clean Modern UI
Launches the streamlined Modern UI with only essential tabs
"""

import os
import sys
import subprocess

def main():
    """Launch the cleaned Modern UI"""
    print("🚀 Starting Clean Modern UI...")
    print("=" * 50)
    
    # Change to src directory
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    
    # Build the command
    command = [
        sys.executable, 
        "modern_ui.py",
        "--recognition", "improved",
        "--security-mode", "manual"
    ]
    
    print("📋 Starting with:")
    print("   Recognition: improved")
    print("   Security Mode: manual") 
    print(f"   Working Directory: {src_dir}")
    print()
    print("🎯 Essential Tabs Only:")
    print("   ✅ Game Info - Shows detected cards and game state")
    print("   ✅ Security - Session limits and capture controls")
    print("   ✅ Debug - Hardware capture testing and cleanup")
    print("   ✅ Performance - Optional monitoring (if available)")
    print()
    print("❌ Removed Redundant Tabs:")
    print("   🚫 Capture - Not needed for OBS Virtual Camera")
    print("   🚫 Advanced - Mostly incompatible with hardware capture")
    print()
    print("🔌 Hardware Integration:")
    print("   • Connect to OBS Virtual Camera")
    print("   • Use manually calibrated regions")
    print("   • Real-time card recognition from laptop feed")
    print("=" * 50)
    
    try:
        # Start the UI
        subprocess.run(command, cwd=src_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting UI: {e}")
    except KeyboardInterrupt:
        print("\n👋 UI shut down by user")

if __name__ == "__main__":
    main()
