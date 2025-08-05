"""
Project Cleanup Script
Remove redundant files now that we're using hardware capture + OBS approach
"""

import os
import shutil
from pathlib import Path

# Files and directories to KEEP (core system)
KEEP_FILES = {
    # Core new systems
    'hardware_capture_integration.py',
    'launch_hardware_capture.py', 
    'quick_hardware_test.py',
    'enhanced_ocr_recognition.py',
    'fallback_card_recognition.py',
    'table_reference_system.py',
    'enhanced_integration.py',
    'launch_enhanced_bot.py',
    'test_enhanced_systems.py',
    'compare_recognition_systems.py',
    
    # Essential documentation
    'HARDWARE_SETUP_GUIDE.md',
    'ENHANCED_INTEGRATION_GUIDE.md',
    'README.md',
    'CONTRIBUTING.md',
    
    # Configuration files
    'requirements.txt',
    '.gitignore',
    
    # Essential directories
    'src/',
    '.git/',
    'venv/',
    '__pycache__/',
    
    # Current test outputs (can regenerate if needed)
    'test_card_generated.png',
    'test_table_generated.png',
    'enhanced_bot_visualization.png',
    'calibration_screenshot.png',
}

# Files to DELETE (obsolete with hardware capture)
DELETE_FILES = {
    # Old recognition systems
    'behavioral_stealth.py',
    'card_recognition_integration.py', 
    'card_suit_color.py',
    'comprehensive_card_recognition.py',
    'create_simple_recognition.py',
    'debug_card_recognition.py',
    'debug_card_recognition_advanced.py',
    'debug_card_recognition_fixed.py',
    'debug_recognition.py',
    'debug_region_extraction.py',
    'debug_region_overlay.py',
    'direct_card_integration.py',
    'direct_card_recognition.py',
    'enhanced_card_recognition.py',
    'fix_deck_color_issue.py',
    'fix_recognition_urgently.py',
    'improved_card_recognition.py',
    'modern_card_recognition.py',
    'ocr_card_recognition.py',
    'ocr_setup_complete.py',
    'poker_study_tool_demo.py',
    'simple_card_recognition_test.py',
    'simple_color_test.py',
    'simple_test.py',
    'simple_working_recognition.py',
    'template_card_recognition.py',
    'ultimate_card_recognition.py',
    'unified_card_recognition.py',
    'update_card_recognition.py',
    'update_direct_recognition.py',
    'working_card_recognition.py',
    
    # Old test files
    'test_card_color.py',
    'test_card_recognition.py',
    'test_card_recognition_fix.py',
    'test_color_recognition.py',
    'test_comprehensive_recognition.py',
    'test_coordinate_fix.py',
    'test_debug_images.py',
    'test_direct_recognition.py',
    'test_empty_card_detection.py',
    'test_enhanced_recognition.py',
    'test_four_color_suits.py',
    'test_fps_performance.py',
    'test_improved_recognition.py',
    'test_mapping.py',
    'test_ocr.py',
    'test_ocr_recognition.py',
    'test_ocr_with_file.py',
    'test_recognition.py',
    'test_recognition_accuracy.py',
    'test_recognition_simple.py',
    'test_region_calibrator.py',
    'test_region_debug.py',
    'test_region_extraction.py',
    'test_region_fix.py',
    'test_region_integration.py',
    'test_region_loading.py',
    'test_templates.py',
    'test_template_recognition.py',
    'test_ultimate_recognition.py',
    'test_capture_loop.py',
    
    # Old launchers and batch files
    'clean.bat',
    'create_executable.bat',
    'create_ui_executable.bat',
    'direct_recognition_menu.bat',
    'install_direct_recognition.bat',
    'install_manual.bat',
    'LAUNCH_BOT.bat',
    'manual_mode.bat',
    'microsoft_update_service.bat',
    'modern_ui.bat',
    'modern_ui_security.bat',
    'SECURE_BOT.bat',
    'setup.bat',
    'stealth_launcher.bat',
    'ultimate_poker_bot.bat',
    'windows_security_service.bat',
    
    # Old stealth/security systems (replaced by hardware approach)
    'cleanup_for_demo.py',
    'master_launcher.py',
    'process_disguiser.py',
    'process_monitor.py',
    'recalibration_guide.py',
    'restore_after_demo.py',
    'secure_launcher.py',
    'stealth_file_manager.py',
    'stealth_launcher.py',
    'stealth_manager.py',
    'stealth_screenshot.py',
    'ultimate_card_integration.py',
    'ultimate_recognition_config.py',
    'ultimate_stealth_launcher.py',
    'region_verification_tool.py',
    
    # Old documentation (replaced by hardware guides)
    'CARD_RECOGNITION_DEBUG.md',
    'COLOR_RECOGNITION.md',
    'demo_video_script.md',
    'DIRECT_RECOGNITION.md',
    'DIRECT_RECOGNITION_ADVANTAGES.md',
    'ENHANCED_RECOGNITION.md',
    'ENHANCED_RECOGNITION_DOCS.md',
    'FIXES_SUMMARY.md',
    'IMPROVED_RECOGNITION.md',
    'INSTALL_GUIDE.md',
    'MODERN_UI_AUDIT.md',
    'MODERN_UI_FIXES.md',
    'MODERN_UI_IMPLEMENTATION_COMPLETE.md',
    'POKERSTARS_SECURITY_ANALYSIS.md',
    'README_ORIGINAL.md',
    'RECOGNITION_DIAGNOSIS.py',
    'RECOGNITION_STATUS_REPORT.md',
    'REGION_LOADING_DEBUG_FIXES.md',
    'REGION_LOADING_FIXES.md',
    'SECURITY_IMPLEMENTATION_COMPLETE.md',
    'STEALTH_OPERATION_COMPLETE.md',
    
    # Old configuration files
    'enhanced_regions_config.json',
    'region_config.json',
    'regions_auto_calibrated.json',
    'table_reference_auto_detected.json',
    
    # Old log files
    'card_integration.log',
    'card_suit_color.log',
    'comprehensive_recognition.log',
    'debug_card_recognition.log',
    'debug_card_recognition_fixed.log',
    'direct_card_recognition.log',
    'direct_recognition_test.log',
    'enhanced_recognition.log',
    'enhanced_recognition_test.log',
    'improved_card_recognition.log',
    'improved_recognition_test.log',
    'master_launcher.log',
    'poker_bot.log',
    'secure_bot.log',
    'simple_card_recognition_test.log',
    'test_card_recognition.log',
    'ultimate_card_recognition.log',
    
    # Debug images (can regenerate)
    'debug_extraction_community_card_1.png',
    'debug_extraction_community_card_2.png',
    'debug_extraction_community_card_3.png',
    'debug_extraction_community_card_4.png',
    'debug_extraction_community_card_5.png',
    'debug_extraction_hero_card_1.png',
    'debug_extraction_hero_card_2.png',
    'debug_ocr_community_1.png',
    'debug_ocr_community_2.png',
    'debug_ocr_community_3.png',
    'debug_ocr_community_4.png',
    'debug_ocr_community_5.png',
    'debug_ocr_hero_1.png',
    'debug_ocr_hero_2.png',
    'debug_region_card_1.png',
    'debug_region_comparison.png',
    'debug_region_hero_card_1.png',
    'debug_region_hero_card_2.png',
    'debug_region_overlay.png',
    'debug_template_sample.png',
    'debug_test_clubs.png',
    'debug_test_diamonds.png',
    'debug_test_hearts.png',
    'debug_test_spades.png',
    'test_screenshot.png',
    'test_capture_1753421793.png',
    
    # Other obsolete files
    'poker_icon.ico',
    'requirements_fallback.txt',
}

# Directories to DELETE
DELETE_DIRECTORIES = {
    'card_templates/',
    'debug_cards/',
    'debug_color_detection/',
    'debug_community/',
    'debug_enhanced_recognition/',
    'debug_images/',
    'debug_recognition/',
    'debug_regions/',
    'debug_templates/',
    'dist/',
    'logs/',
    'modern_recognition/',
    'recognition_results/',
    'regions/',
    'region_verification/',
    'saved_hands/',
    'screenshots/',
    'templates/',
    'test_cards/',
    'test_output/',
}

def cleanup_project(project_path: str, dry_run: bool = True):
    """Clean up the project directory"""
    project_path = Path(project_path)
    
    if not project_path.exists():
        print(f"Project path {project_path} does not exist!")
        return
    
    print("🧹 PROJECT CLEANUP ANALYSIS")
    print("=" * 50)
    
    # Count current files
    all_files = list(project_path.glob("*"))
    total_files = len([f for f in all_files if f.is_file()])
    total_dirs = len([f for f in all_files if f.is_dir() and f.name not in {'.git', 'venv', '__pycache__', 'src'}])
    
    print(f"Current status:")
    print(f"  📁 Total files: {total_files}")
    print(f"  📂 Total directories: {total_dirs}")
    
    # Files to delete
    files_to_delete = []
    dirs_to_delete = []
    
    for item in project_path.iterdir():
        if item.is_file() and item.name in DELETE_FILES:
            files_to_delete.append(item)
        elif item.is_dir() and f"{item.name}/" in DELETE_DIRECTORIES:
            dirs_to_delete.append(item)
    
    print(f"\n🗑️ Will delete:")
    print(f"  📄 {len(files_to_delete)} files")
    print(f"  📁 {len(dirs_to_delete)} directories")
    
    # Calculate space savings
    total_size = 0
    for file_path in files_to_delete:
        try:
            total_size += file_path.stat().st_size
        except:
            pass
    
    for dir_path in dirs_to_delete:
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        except:
            pass
    
    print(f"  💾 Space to free: {total_size / (1024*1024):.1f} MB")
    
    if dry_run:
        print(f"\n📋 FILES TO DELETE:")
        for file_path in sorted(files_to_delete):
            print(f"  ❌ {file_path.name}")
        
        print(f"\n📂 DIRECTORIES TO DELETE:")
        for dir_path in sorted(dirs_to_delete):
            print(f"  ❌ {dir_path.name}/")
        
        print(f"\n🔄 FILES TO KEEP:")
        kept_files = []
        for item in project_path.iterdir():
            if item.is_file() and item.name not in DELETE_FILES and item.name != 'cleanup_project.py':
                kept_files.append(item.name)
        
        for file_name in sorted(kept_files):
            if file_name in KEEP_FILES:
                print(f"  ✅ {file_name}")
            else:
                print(f"  ⚠️ {file_name} (not in keep list - review)")
        
        print(f"\n💡 To actually delete files, run: cleanup_project('{project_path}', dry_run=False)")
        
    else:
        print(f"\n🚀 DELETING FILES...")
        
        deleted_files = 0
        deleted_dirs = 0
        
        # Delete files
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_files += 1
                print(f"  ❌ Deleted: {file_path.name}")
            except Exception as e:
                print(f"  ⚠️ Failed to delete {file_path.name}: {e}")
        
        # Delete directories
        for dir_path in dirs_to_delete:
            try:
                shutil.rmtree(dir_path)
                deleted_dirs += 1
                print(f"  ❌ Deleted directory: {dir_path.name}/")
            except Exception as e:
                print(f"  ⚠️ Failed to delete {dir_path.name}/: {e}")
        
        print(f"\n✅ CLEANUP COMPLETE!")
        print(f"  📄 Deleted {deleted_files} files")
        print(f"  📁 Deleted {deleted_dirs} directories")
        print(f"  💾 Freed ~{total_size / (1024*1024):.1f} MB")
        
        # Show final status
        remaining_files = list(project_path.glob("*"))
        final_files = len([f for f in remaining_files if f.is_file()])
        final_dirs = len([f for f in remaining_files if f.is_dir() and f.name not in {'.git', 'venv', '__pycache__', 'src'}])
        
        print(f"\n📊 FINAL STATUS:")
        print(f"  📁 Remaining files: {final_files}")
        print(f"  📂 Remaining directories: {final_dirs}")

if __name__ == "__main__":
    # Run cleanup analysis
    project_dir = r"d:\P-bot 2\project"
    
    print("🎯 POKER BOT PROJECT CLEANUP")
    print("Moving to Hardware Capture + OBS approach")
    print("=" * 60)
    
    # First run dry run to show what will be deleted
    cleanup_project(project_dir, dry_run=True)
