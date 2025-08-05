"""
Project Cleanup Script - Refactored Version
Remove redundant files now that we're using hardware capture + OBS approach
Fixed all SonarQube warnings: reduced complexity, proper exception handling, fixed f-strings
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

class ProjectCleaner:
    """Clean up redundant files from the poker bot project."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.total_files_removed = 0
        self.total_dirs_removed = 0
        self.total_size_freed = 0
        
        # Essential files to keep for hardware capture system
        self.essential_files = {
            # Hardware capture system
            'hardware_capture_integration.py',
            'launch_hardware_capture.py', 
            'quick_hardware_test.py',
            
            # Enhanced recognition
            'enhanced_ocr_recognition.py',
            'fallback_card_recognition.py',
            'table_reference_system.py',
            
            # Integration tools
            'enhanced_integration.py',
            'launch_enhanced_bot.py',
            'compare_recognition_systems.py',
            'test_enhanced_systems.py',
            'simple_ui_launcher.py',
            
            # Core src files (keep most recent versions)
            'src/poker_bot.py',
            'src/card_recognizer.py',
            'src/image_processor.py',
            'src/window_capture.py',
            'src/community_card_detector.py',
            'src/poker_table_analyzer.py',
            'src/region_loader.py',
            'src/modern_ui.py',
            'src/improved_card_recognition.py',
            
            # UI components
            'src/ui/__init__.py',
            'src/ui/main_window.py',
            'src/ui/control_panel.py',
            'src/ui/region_calibrator.py',
            'src/ui/analysis_display.py',
            
            # Documentation
            'README.md',
            'HARDWARE_SETUP_GUIDE.md',
            'ENHANCED_INTEGRATION_GUIDE.md',
            'CONTRIBUTING.md',
            
            # Configuration
            'requirements.txt',
            '.gitignore',
            
            # Generated test files (keep recent)
            'calibration_screenshot.png',
            'enhanced_bot_visualization.png',
            'test_card_generated.png',
            'test_table_generated.png'
        }
        
        # Files to DELETE (obsolete with hardware capture)
        self.delete_files = {
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
            'simple_working_recognition.py',
            
            # Old stealth systems
            'stealth_launcher.py',
            'stealth_launcher.bat',
            'stealth_manager.py',
            'stealth_file_manager.py',
            'process_disguiser.py',
            'process_monitor.py',
            'secure_launcher.py',
            'microsoft_update_service.bat',
            'modern_ui_security.bat',
            'SECURE_BOT.bat',
            
            # Old batch files
            'direct_recognition_menu.bat',
            'install_direct_recognition.bat',
            'manual_mode.bat',
            'modern_ui.bat',
            'recalibration_guide.py',
            'region_verification_tool.py',
            'run_cleanup.py',
            
            # Debug and test files
            'RECOGNITION_DIAGNOSIS.py',
            'simple_ui_launcher.py',
            'cleanup_for_demo.py',
            'poker_icon.ico'
        }
        
        # Directories to preserve
        self.preserve_dirs = {
            '.git', '.vscode', '__pycache__', 'venv', '.env',
            'src', 'src/ui', 'screenshots', 'debug_images'
        }
        
        # Directories to DELETE
        self.delete_directories = {
            'card_templates',
            'debug_cards',
            'debug_color_detection',
            'debug_community',
            'debug_enhanced_recognition',
            'debug_recognition',
            'debug_regions',
            'debug_templates',
            'dist',
            'logs',
            'modern_recognition',
            'recognition_results',
            'regions',
            'region_verification',
            'saved_hands',
            'templates',
            'test_cards',
            'test_output'
        }

    def get_file_size(self, filepath: Path) -> int:
        """Get file size safely."""
        try:
            return filepath.stat().st_size
        except OSError:
            return 0

    def is_essential_file(self, filepath: Path) -> bool:
        """Check if a file is essential and should be kept."""
        relative_path = filepath.relative_to(self.project_root)
        return str(relative_path).replace('\\', '/') in self.essential_files

    def should_preserve_directory(self, dirpath: Path) -> bool:
        """Check if a directory should be preserved."""
        relative_path = dirpath.relative_to(self.project_root)
        dir_name = str(relative_path).replace('\\', '/')
        
        # Check if it's in preserve list
        if dir_name in self.preserve_dirs:
            return True
            
        # Check if any parent directory should be preserved
        for preserve_dir in self.preserve_dirs:
            if dir_name.startswith(preserve_dir + '/'):
                return True
                
        return False

    def analyze_cleanup(self) -> Dict[str, any]:
        """Analyze what would be cleaned up without actually doing it."""
        files_to_remove = self._find_files_to_remove()
        dirs_to_remove = self._find_dirs_to_remove()
        total_size = sum(file_info['size'] for file_info in files_to_remove)
        
        return {
            'files_to_remove': files_to_remove,
            'dirs_to_remove': dirs_to_remove,
            'total_files': len(files_to_remove),
            'total_dirs': len(dirs_to_remove),
            'total_size_mb': total_size / (1024 * 1024)
        }

    def _find_files_to_remove(self) -> List[Dict[str, any]]:
        """Find all files that should be removed."""
        files_to_remove = []
        
        for filepath in self.project_root.rglob('*'):
            if filepath.is_file() and not self.is_essential_file(filepath):
                if not self._should_preserve_file_parent(filepath):
                    file_size = self.get_file_size(filepath)
                    files_to_remove.append({
                        'path': str(filepath.relative_to(self.project_root)),
                        'size': file_size
                    })
        
        return files_to_remove

    def _find_dirs_to_remove(self) -> List[str]:
        """Find all directories that should be removed."""
        dirs_to_remove = []
        
        for dirpath in self.project_root.rglob('*'):
            if dirpath.is_dir() and not self.should_preserve_directory(dirpath):
                dirs_to_remove.append(str(dirpath.relative_to(self.project_root)))
        
        return dirs_to_remove

    def clean_redundant_files(self, dry_run: bool = True) -> bool:
        """Remove redundant files. Refactored to reduce complexity."""
        try:
            logger.info("Starting project cleanup...")
            
            if dry_run:
                analysis = self.analyze_cleanup()
                self._print_cleanup_summary(analysis)
                return True
            
            # Actual cleanup
            return self._perform_cleanup()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False

    def _print_cleanup_summary(self, analysis: Dict[str, any]) -> None:
        """Print cleanup summary."""
        print("\n" + "="*60)
        print("PROJECT CLEANUP ANALYSIS")
        print("="*60)
        print(f"Files to remove: {analysis['total_files']}")
        print(f"Directories to remove: {analysis['total_dirs']}")
        print(f"Space to free: {analysis['total_size_mb']:.1f} MB")
        
        if analysis['total_files'] > 0:
            print("\nFiles that will be removed:")
            for file_info in analysis['files_to_remove'][:10]:  # Show first 10
                size_kb = file_info['size'] / 1024
                print(f"  📄 {file_info['path']} ({size_kb:.1f} KB)")
            
            if analysis['total_files'] > 10:
                print(f"  ... and {analysis['total_files'] - 10} more files")

    def _perform_cleanup(self) -> bool:
        """Perform the actual cleanup."""
        try:
            files_removed = self._remove_redundant_files()
            dirs_removed = self._remove_empty_directories()
            
            print("\n✅ Cleanup complete!")
            print(f"📄 Removed {files_removed} files")
            print(f"📁 Removed {dirs_removed} directories")
            print(f"💾 Freed {self.total_size_freed / (1024 * 1024):.1f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during actual cleanup: {e}")
            return False

    def _remove_redundant_files(self) -> int:
        """Remove redundant files."""
        files_removed = 0
        
        for filepath in self.project_root.rglob('*'):
            if not filepath.is_file():
                continue
                
            if self.is_essential_file(filepath):
                continue
                
            # Check if parent directory should be preserved
            if self._should_preserve_file_parent(filepath):
                continue
                
            try:
                file_size = self.get_file_size(filepath)
                filepath.unlink()
                files_removed += 1
                self.total_size_freed += file_size
                logger.info(f"Removed file: {filepath.relative_to(self.project_root)}")
                
            except OSError as e:
                logger.warning(f"Could not remove file {filepath}: {e}")
                
        return files_removed

    def _should_preserve_file_parent(self, filepath: Path) -> bool:
        """Check if file's parent directory should be preserved."""
        for parent in filepath.parents:
            if parent == self.project_root:
                break
            if self.should_preserve_directory(parent):
                return True
        return False

    def _remove_empty_directories(self) -> int:
        """Remove empty directories."""
        dirs_removed = 0
        
        # Get all directories, sorted by depth (deepest first)
        all_dirs = [d for d in self.project_root.rglob('*') if d.is_dir()]
        all_dirs.sort(key=lambda x: len(x.parts), reverse=True)
        
        for dirpath in all_dirs:
            if self.should_preserve_directory(dirpath):
                continue
                
            try:
                # Check if directory is empty
                if not any(dirpath.iterdir()):
                    dirpath.rmdir()
                    dirs_removed += 1
                    logger.info(f"Removed empty directory: {dirpath.relative_to(self.project_root)}")
                    
            except OSError as e:
                logger.warning(f"Could not remove directory {dirpath}: {e}")
                
        return dirs_removed

def main():
    """Main entry point for cleanup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up redundant project files')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually perform cleanup (default is dry run)')
    parser.add_argument('--project-root', default='.',
                       help='Project root directory (default: current directory)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        cleaner = ProjectCleaner(args.project_root)
        
        if args.execute:
            print("🚨 EXECUTING CLEANUP - Files will be permanently deleted!")
            input("Press Enter to continue or Ctrl+C to cancel...")
            success = cleaner.clean_redundant_files(dry_run=False)
        else:
            print("🔍 DRY RUN - No files will be deleted")
            success = cleaner.clean_redundant_files(dry_run=True)
            print("\n💡 To actually perform cleanup, run with --execute flag")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Cleanup cancelled by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
