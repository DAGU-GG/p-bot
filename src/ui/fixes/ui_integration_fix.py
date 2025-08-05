"""
Fix UI integration issues with hardware capture
"""

import tkinter as tk
import time
import threading
from typing import Dict, List, Optional

class UIIntegrationFix:
    """Fixes for UI not displaying hardware capture results"""
    
    def fix_region_overlay_display(self, table_view_panel):
        """Fix region overlay not showing on live view"""
        try:
            # Add logger if missing
            if not hasattr(table_view_panel, 'logger'):
                import logging
                table_view_panel.logger = logging.getLogger('table_view')
            
            # Fix the add_debug_overlay method
            original_add_overlay = getattr(table_view_panel, 'add_debug_overlay', None)
            
            def fixed_add_debug_overlay(regions):
                try:
                    if not regions:
                        return
                    
                    # Clear previous overlays
                    if hasattr(table_view_panel, 'region_overlays'):
                        for overlay in table_view_panel.region_overlays:
                            try:
                                table_view_panel.canvas.delete(overlay)
                            except:
                                pass
                    
                    table_view_panel.region_overlays = []
                    
                    # Get current canvas size
                    canvas_width = table_view_panel.canvas.winfo_width()
                    canvas_height = table_view_panel.canvas.winfo_height()
                    
                    if canvas_width <= 1 or canvas_height <= 1:
                        table_view_panel.logger.warning("Canvas too small for overlay")
                        return
                    
                    # Draw regions
                    for region_name, region_data in regions.items():
                        # Convert coordinates to canvas scale
                        x = int(region_data['x'] * canvas_width / 1920)
                        y = int(region_data['y'] * canvas_height / 1080)
                        w = int(region_data['width'] * canvas_width / 1920)
                        h = int(region_data['height'] * canvas_height / 1080)
                        
                        # Choose color based on region type
                        if 'hero' in region_name:
                            color = '#00ff00'  # Green for hero cards
                        elif 'community' in region_name:
                            color = '#0080ff'  # Blue for community cards
                        else:
                            color = '#ffff00'  # Yellow for others
                        
                        # Draw rectangle
                        rect = table_view_panel.canvas.create_rectangle(
                            x, y, x + w, y + h,
                            outline=color, width=2, tags='region_overlay'
                        )
                        
                        # Draw label
                        text = table_view_panel.canvas.create_text(
                            x + w//2, y - 10,
                            text=region_name, fill=color,
                            font=('Arial', 8, 'bold'),
                            tags='region_overlay'
                        )
                        
                        table_view_panel.region_overlays.extend([rect, text])
                    
                    table_view_panel.logger.info(f"Drew overlay for {len(regions)} regions")
                    
                except Exception as e:
                    if hasattr(table_view_panel, 'logger'):
                        table_view_panel.logger.error(f"Error drawing overlay: {e}")
                    else:
                        print(f"Error drawing overlay: {e}")
            
            # Replace method
            table_view_panel.add_debug_overlay = fixed_add_debug_overlay
            
        except Exception as e:
            print(f"Error fixing region overlay: {e}")
    
    def fix_debug_tab_updates(self, main_window):
        """Fix debug tab not receiving updates"""
        try:
            # Clear any broken after callbacks
            try:
                if hasattr(main_window, '_recognition_update_job'):
                    main_window.root.after_cancel(main_window._recognition_update_job)
            except:
                pass
            
            # Create new update function
            def update_recognition_display():
                try:
                    if not hasattr(main_window, 'hardware_capture') or not main_window.hardware_capture:
                        main_window.root.after(2000, update_recognition_display)
                        return
                    
                    # Get live status
                    status = main_window.hardware_capture.get_live_recognition_status()
                    
                    # Update status label (find it dynamically)
                    for widget_name in ['recognition_status_label', 'status_label', 'live_status_label']:
                        if hasattr(main_window, widget_name):
                            widget = getattr(main_window, widget_name)
                            if status['camera_connected']:
                                status_text = "🟢 Active - Analyzing"
                                status_color = "#00ff00"
                            else:
                                status_text = "🔴 Not Connected"
                                status_color = "#ff0000"
                            
                            widget.config(
                                text=f"Status: {status_text}",
                                fg=status_color
                            )
                            break
                    
                    # Update performance label
                    for widget_name in ['recognition_performance_label', 'performance_label', 'perf_label']:
                        if hasattr(main_window, widget_name):
                            widget = getattr(main_window, widget_name)
                            widget.config(
                                text=f"Performance: {status['performance_summary']}"
                            )
                            break
                    
                    # Update log (find debug log widget)
                    log_widgets = ['debug_recognition_log', 'recognition_log', 'debug_log', 'live_log']
                    for widget_name in log_widgets:
                        if hasattr(main_window, widget_name):
                            log_widget = getattr(main_window, widget_name)
                            try:
                                log_widget.config(state='normal')
                                
                                # Get recent logs
                                recent_logs = status.get('recent_logs', [])
                                if recent_logs:
                                    # Only add new entries
                                    current_text = log_widget.get('1.0', 'end-1c')
                                    for log_entry in recent_logs[-5:]:  # Last 5 entries
                                        if log_entry not in current_text:
                                            log_widget.insert('end', log_entry + '\n')
                                    
                                    # Auto-scroll to bottom
                                    log_widget.see('end')
                                
                                log_widget.config(state='disabled')
                            except Exception as e:
                                print(f"Error updating log widget {widget_name}: {e}")
                            break
                    
                except Exception as e:
                    print(f"Error updating recognition display: {e}")
                finally:
                    # Schedule next update
                    main_window._recognition_update_job = main_window.root.after(
                        1000, update_recognition_display
                    )
            
            # Start update loop
            update_recognition_display()
            
        except Exception as e:
            print(f"Error fixing debug tab: {e}")
    
    def fix_performance_charts(self, main_window):
        """Fix performance charts not updating"""
        try:
            if not hasattr(main_window, 'performance_monitor'):
                print("No performance monitor found")
                return
            
            # Create update function for performance data
            def update_performance_data():
                try:
                    if hasattr(main_window, 'hardware_capture') and main_window.hardware_capture:
                        stats = main_window.hardware_capture.recognition_performance_stats
                        
                        # Update capture times
                        if stats['processing_times']:
                            times = stats['processing_times'][-50:]  # Last 50
                            avg_time = sum(times) / len(times) * 1000  # Convert to ms
                            if hasattr(main_window.performance_monitor, 'update_capture_time'):
                                main_window.performance_monitor.update_capture_time(avg_time)
                        
                        # Update confidence
                        if stats['confidence_scores']:
                            confidences = stats['confidence_scores'][-50:]
                            avg_conf = sum(confidences) / len(confidences)
                            if hasattr(main_window.performance_monitor, 'update_confidence'):
                                main_window.performance_monitor.update_confidence(avg_conf)
                        
                        # Update FPS
                        if stats['total_frames'] > 0:
                            fps = stats['total_frames'] / max(1, time.time() - getattr(main_window, '_start_time', time.time()))
                            if hasattr(main_window.performance_monitor, 'update_fps'):
                                main_window.performance_monitor.update_fps(fps)
                        
                except Exception as e:
                    print(f"Error updating performance: {e}")
                finally:
                    main_window.root.after(1500, update_performance_data)
            
            # Start update loop
            if not hasattr(main_window, '_start_time'):
                main_window._start_time = time.time()
            update_performance_data()
            
        except Exception as e:
            print(f"Error fixing performance charts: {e}")
    
    def fix_game_info_updates(self, main_window):
        """Fix game info panel not showing analysis results"""
        try:
            # Store original update method if it exists
            original_update = getattr(main_window, '_update_hardware_livestream', None)
            
            def fixed_update_hardware_livestream():
                try:
                    # Call original update if it exists
                    if original_update:
                        original_update()
                    
                    # Get hardware capture results
                    if hasattr(main_window, 'hardware_capture') and main_window.hardware_capture:
                        # Get latest game state
                        latest_state = getattr(main_window.hardware_capture, '_last_game_state', None)
                        
                        if latest_state and hasattr(main_window, 'game_info_panel'):
                            # Convert to UI format
                            analysis = {
                                'hero_cards': [],
                                'community_cards': [],
                                'timestamp': time.time()
                            }
                            
                            # Add hero cards
                            for card in latest_state.get('hero_cards', []):
                                card_str = card.get('card', '')
                                if len(card_str) >= 2:
                                    analysis['hero_cards'].append({
                                        'rank': card_str[:-1] if len(card_str) > 1 else card_str[0],
                                        'suit': card_str[-1] if len(card_str) > 1 else '',
                                        'confidence': card.get('confidence', 0.5)
                                    })
                            
                            # Add community cards
                            for card in latest_state.get('community_cards', []):
                                card_str = card.get('card', '')
                                if len(card_str) >= 2:
                                    analysis['community_cards'].append({
                                        'rank': card_str[:-1] if len(card_str) > 1 else card_str[0],
                                        'suit': card_str[-1] if len(card_str) > 1 else '',
                                        'confidence': card.get('confidence', 0.5)
                                    })
                            
                            # Update game info panel
                            if hasattr(main_window.game_info_panel, 'update_game_info'):
                                main_window.game_info_panel.update_game_info(analysis)
                            
                            # Update community cards display
                            if hasattr(main_window, 'update_community_cards'):
                                main_window.update_community_cards(analysis['community_cards'])
                            
                            # Log to UI
                            if analysis['hero_cards'] or analysis['community_cards']:
                                if hasattr(main_window, 'log_message'):
                                    main_window.log_message(
                                        f"[LIVE] Detected {len(analysis['hero_cards'])} hero cards, "
                                        f"{len(analysis['community_cards'])} community cards"
                                    )
                    
                except Exception as e:
                    print(f"Error in fixed livestream update: {e}")
            
            # Replace method
            main_window._update_hardware_livestream = fixed_update_hardware_livestream
            
            # Also create timer for regular updates
            def regular_update():
                try:
                    fixed_update_hardware_livestream()
                except:
                    pass
                finally:
                    main_window.root.after(2000, regular_update)
            
            # Start regular updates
            regular_update()
            
        except Exception as e:
            print(f"Error fixing game info updates: {e}")
    
    def apply_all_fixes(self, main_window):
        """Apply all UI fixes"""
        print("🔧 Applying UI integration fixes...")
        
        # Fix region overlay
        if hasattr(main_window, 'table_view'):
            self.fix_region_overlay_display(main_window.table_view)
            print("✅ Fixed region overlay display")
        
        # Fix debug tab
        self.fix_debug_tab_updates(main_window)
        print("✅ Fixed debug tab updates")
        
        # Fix performance charts
        self.fix_performance_charts(main_window)
        print("✅ Fixed performance chart updates")
        
        # Fix game info updates
        self.fix_game_info_updates(main_window)
        print("✅ Fixed game info panel updates")
        
        # Trigger initial updates
        if hasattr(main_window, 'hardware_capture') and main_window.hardware_capture:
            # Show regions on overlay
            if main_window.hardware_capture.calibrated_regions and hasattr(main_window, 'table_view'):
                try:
                    main_window.table_view.add_debug_overlay(
                        main_window.hardware_capture.calibrated_regions
                    )
                    print("✅ Added region overlay to live view")
                except Exception as e:
                    print(f"Could not add initial overlay: {e}")
            
            # Force an analysis update
            def trigger_analysis():
                try:
                    result = main_window.hardware_capture.analyze_current_frame()
                    if result:
                        main_window.hardware_capture._last_game_state = result
                        print(f"✅ Triggered analysis: {len(result.get('hero_cards', []))} hero, {len(result.get('community_cards', []))} community")
                except Exception as e:
                    print(f"Analysis trigger error: {e}")
            
            threading.Thread(target=trigger_analysis, daemon=True).start()
        
        print("✅ All UI fixes applied!")

# Export fix function
def fix_ui_integration(main_window):
    """Main entry point to fix UI integration issues"""
    fixer = UIIntegrationFix()
    fixer.apply_all_fixes(main_window)
