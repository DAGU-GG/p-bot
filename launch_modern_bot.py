#!/usr/bin/env python3
"""Smart Poker Bot - Virtual Camera OCR Analysis (No Live Feed).

This bot captures single frames from OBS Virtual Camera for OCR analysis.
NO LIVE FEED - Only on-demand capture and analysis.

Usage:
  python launch_modern_bot.py           # GUI mode
  python launch_modern_bot.py --debug   # Debug mode with region overlay
"""
import os
import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import hashlib
from datetime import datetime

print("🔧 Initializing Smart Poker Bot (No Live Feed)...")

# Import the bot
try:
    from SimplePokerBot import SimplePokerBot as SmartPokerBot
except ImportError:
    print("⚠️ Using fallback bot import")
    from SMART_POKER_BOT import SmartPokerBot

class VirtualCameraOCRBot:
    """Simple OCR bot that captures frames from virtual camera on-demand."""
    
    def __init__(self):
        self.camera_index = None
        self.bot = None
        self.root = None
        self.camera_resolution = (640, 480)  # Default resolution
        # No persistent camera - using create-and-release approach
        
        # Auto-scanning state
        self.auto_scan_enabled = False
        self.auto_scan_interval = 2000  # 2 seconds in milliseconds
        self.auto_scan_job = None
        self.last_scan_results = None
        self.last_display_update = 0  # Track when we last updated display
        
        # Card confirmation system
        self.confirmation_mode = False
        self.current_confirmation_data = None
        
    def find_obs_camera(self):
        """Find OBS Virtual Camera with flexible resolution detection."""
        print("🔍 Looking for OBS Virtual Camera...")
        
        # Try different resolutions to find the best match
        target_resolutions = [
            (1920, 1080),
            (1280, 720),
            (1282, 920),  # Your poker table resolution
            (640, 480)
        ]
        
        for i in range(6):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # Try to set higher resolution first
                    for target_w, target_h in target_resolutions:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_w)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_h)
                        
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            height, width = frame.shape[:2]
                            print(f"📹 Camera {i} at {target_w}x{target_h}: got {width}x{height}")
                            
                            # Accept if we got a reasonable resolution
                            if width >= 640 and height >= 480:
                                cap.release()
                                print(f"✅ Using camera at index {i}: {width}x{height}")
                                
                                # Store the actual resolution we got
                                self.camera_resolution = (width, height)
                                return i
                    
                cap.release()
            except Exception as e:
                print(f"❌ Error testing camera {i}: {e}")
                continue
        
        print("❌ No suitable camera found")
        return None
    
    def capture_frame(self):
        """Capture single frame with create-and-release approach to prevent OBS freeze."""
        if self.camera_index is None:
            return None
        
        cap = None
        try:
            # Create new capture for each frame to prevent freezing
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if cap.isOpened():
                # Set the resolution we detected during camera finding
                if hasattr(self, 'camera_resolution'):
                    target_w, target_h = self.camera_resolution
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_w)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_h)
                
                # Set minimal buffer to get latest frame
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Read a frame
                ret, frame = cap.read()
                
                # Immediately release the capture
                cap.release()
                cap = None
                
                if ret and frame is not None:
                    print(f"✅ Captured frame: {frame.shape[1]}x{frame.shape[0]}")
                    return frame
                else:
                    print("❌ Failed to read frame")
                    return None
            else:
                print("❌ Failed to open camera")
                return None
        except Exception as e:
            print(f"❌ Capture error: {e}")
            return None
        finally:
            # Ensure camera is always released
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
    
    def create_gui(self):
        """Create simple GUI for OCR analysis."""
        self.root = tk.Tk()
        self.root.title("🎯 Poker Bot - Virtual Camera OCR")
        self.root.geometry("1000x800")
        self.root.configure(bg='#0d1117')
        
        # Title
        title = tk.Label(
            self.root,
            text="Smart Poker Bot - OCR Analysis Only",
            bg='#0d1117',
            fg='#e6edf3',
            font=('Arial', 18, 'bold')
        )
        title.pack(pady=20)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready - Click 'Fast Analysis' for immediate decisions or 'Full Tournament' for complete tracking",
            bg='#161b22',
            fg='#00ff88',
            font=('Arial', 10)
        )
        self.status_label.pack(fill=tk.X, padx=20, pady=5)
        
        # Control buttons
        button_frame = tk.Frame(self.root, bg='#0d1117')
        button_frame.pack(pady=20)
        
        # Fast analysis button (primary)
        tk.Button(
            button_frame,
            text="⚡ Fast Analysis",
            command=self.analyze_table_fast,
            bg='#00ff88',
            fg='black',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Full analysis button (secondary)
        tk.Button(
            button_frame,
            text="🏆 Full Tournament",
            command=self.analyze_table_full,
            bg='#ff8800',
            fg='black',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-scan toggle button
        self.auto_scan_button = tk.Button(
            button_frame,
            text="🔄 Auto-Scan OFF",
            command=self.toggle_auto_scan,
            bg='#666666',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        )
        self.auto_scan_button.pack(side=tk.LEFT, padx=5)
        
        # Card confirmation button
        self.confirm_button = tk.Button(
            button_frame,
            text="✅ Confirm Cards",
            command=self.start_card_confirmation,
            bg='#aa44ff',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        )
        self.confirm_button.pack(side=tk.LEFT, padx=5)
        
        # Second row of buttons
        button_frame2 = tk.Frame(self.root, bg='#0d1117')
        button_frame2.pack(pady=10)
        
        # Adjust regions button
        tk.Button(
            button_frame2,
            text="🔧 Adjust Regions",
            command=self.adjust_regions,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
        
        # Screenshot button
        tk.Button(
            button_frame,
            text="📷 Take Screenshot",
            command=self.take_screenshot,
            bg='#ffdd33',
            fg='black',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        # Debug overlay button
        tk.Button(
            button_frame,
            text="🔍 Show Regions",
            command=self.show_debug_overlay,
            bg='#ff8800',
            fg='black',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        # Results display
        results_frame = tk.LabelFrame(
            self.root,
            text="OCR Analysis Results",
            bg='#161b22',
            fg='#e6edf3',
            font=('Arial', 12, 'bold')
        )
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.results_text = tk.Text(
            results_frame,
            bg='#161b22',
            fg='#e6edf3',
            font=('Consolas', 11),
            wrap=tk.WORD
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial status
        if self.camera_index is not None:
            self.results_text.insert(tk.END, f"✅ Virtual camera found at index {self.camera_index}\n")
            self.results_text.insert(tk.END, f"📐 {len(self.bot.current_regions)} regions loaded\n")
            if self.bot.tournament_enabled:
                self.results_text.insert(tk.END, f"🏆 Tournament tracking enabled ({len(self.bot.stack_regions)} stack regions)\n")
            self.results_text.insert(tk.END, "💡 Use 'Fast Analysis' for immediate decisions (cards + pot)\n")
            self.results_text.insert(tk.END, "💡 Use 'Full Tournament' for complete player tracking\n\n")
        else:
            self.results_text.insert(tk.END, "❌ No virtual camera found\n")
            self.results_text.insert(tk.END, "💡 Make sure OBS Virtual Camera is running\n\n")
        
    def analyze_table_fast(self):
        """Capture frame and run fast OCR analysis (cards + pot only)."""
        self.status_label.config(text="⚡ Fast analysis - capturing frame...", fg='#ffdd33')
        self.root.update()
        
        frame = self.capture_frame()
        if frame is None:
            self.status_label.config(text="❌ Failed to capture frame", fg='#ff4444')
            return
        
        # Store frame for learning system
        self.current_frame = frame
        
        self.status_label.config(text="� Running fast analysis...", fg='#ffdd33')
        self.root.update()
        
        try:
            # Run fast OCR analysis (cards + pot only)
            results = self.bot.analyze_frame_fast(frame)
            
            # Display results
            self.display_results(results)
            self.status_label.config(text=f"✅ Fast analysis complete ({results.get('phase1_time_ms', 0):.0f}ms)", fg='#00ff88')
            
        except Exception as e:
            self.results_text.insert(tk.END, f"❌ Fast analysis failed: {e}\n\n")
            self.status_label.config(text="❌ Analysis error", fg='#ff4444')
    
    def analyze_table_full(self):
        """Capture frame and run full tournament analysis."""
        self.status_label.config(text="🏆 Full tournament analysis - capturing frame...", fg='#ffdd33')
        self.root.update()
        
        frame = self.capture_frame()
        if frame is None:
            self.status_label.config(text="❌ Failed to capture frame", fg='#ff4444')
            return
        
        # Store frame for learning system
        self.current_frame = frame
        
        self.status_label.config(text="🔍 Running full tournament analysis...", fg='#ffdd33')
        self.root.update()
        
        try:
            # Run full tournament analysis
            results = self.bot.analyze_frame_tournament(frame)
            
            # Display results
            self.display_results(results)
            total_time = results.get('analysis_time_ms', 0)
            phase1_time = results.get('phase1_time_ms', 0)
            phase2_time = results.get('phase2_time_ms', 0)
            self.status_label.config(text=f"✅ Full analysis complete ({total_time:.0f}ms = {phase1_time:.0f}ms + {phase2_time:.0f}ms)", fg='#00ff88')
            
        except Exception as e:
            self.results_text.insert(tk.END, f"❌ Full analysis failed: {e}\n\n")
            self.status_label.config(text="❌ Analysis error", fg='#ff4444')
    
    def analyze_table(self):
        """Legacy method - defaults to fast analysis."""
        self.analyze_table_fast()
    
    def toggle_auto_scan(self):
        """Toggle automatic smart tournament analysis with intelligent updates."""
        if self.auto_scan_enabled:
            # Stop auto-scan
            self.auto_scan_enabled = False
            if self.auto_scan_job:
                self.root.after_cancel(self.auto_scan_job)
                self.auto_scan_job = None
            
            self.auto_scan_button.config(
                text="🔄 Auto-Scan OFF",
                bg='#666666'
            )
            self.status_label.config(text="Auto-scan disabled", fg='#888888')
        else:
            # Start auto-scan
            self.auto_scan_enabled = True
            self.auto_scan_button.config(
                text="🔄 Auto-Scan ON (Smart)",
                bg='#00aa00'
            )
            self.status_label.config(text="Auto-scan enabled (Smart Updates on Game Changes)", fg='#00ff88')
            self.schedule_next_auto_scan()
    
    def schedule_next_auto_scan(self):
        """Schedule the next automatic scan."""
        if self.auto_scan_enabled:
            self.auto_scan_job = self.root.after(self.auto_scan_interval, self.perform_auto_scan)
    
    def perform_auto_scan(self):
        """Perform automatic full tournament analysis with smart GUI updates."""
        if not self.auto_scan_enabled:
            return
        
        # Skip auto-scan if in confirmation mode to prevent frame changes
        if self.confirmation_mode:
            print("⏸️ Skipping auto-scan - in confirmation mode")
            # Schedule next scan anyway for when confirmation is done
            self.schedule_next_scan()
            return
        
        try:
            frame = self.capture_frame()
            if frame is not None:
                # Store frame for learning system
                self.current_frame = frame
                
                # Run FULL tournament analysis for live sessions
                results = self.bot.analyze_frame_tournament(frame)
                
                # Show updates only on significant game changes (cards, hand rank, players)
                if self.has_significant_change(results):
                    self.display_auto_scan_update(results)
                    self.last_display_update = time.time()
                    
                self.last_scan_results = results
                
                # Update status with enhanced analysis timing
                total_time = results.get('total_analysis_time_ms', 0)
                self.status_label.config(
                    text=f"Auto-scan: {total_time:.0f}ms (Full Tournament) | Next in 2s",
                    fg='#00ff88'
                )
            else:
                self.status_label.config(text="Auto-scan: Frame capture failed", fg='#ff8888')
                
        except Exception as e:
            print(f"Auto-scan error: {e}")
            self.status_label.config(text=f"Auto-scan error: {str(e)[:30]}...", fg='#ff4444')
        
        # Schedule next scan
        self.schedule_next_auto_scan()
    
    def has_significant_change(self, new_enhanced_analysis):
        """Check if the new enhanced analysis represents a significant change."""
        if self.last_scan_results is None:
            return True
        
        # Extract OCR results from enhanced analysis
        new_ocr = new_enhanced_analysis.get('ocr_results', {})
        new_poker = new_enhanced_analysis.get('poker_analysis', {})
        new_deck = new_poker.get('deck_analysis', {})
        
        # Compare with previous results
        if isinstance(self.last_scan_results, dict):
            # Handle both enhanced analysis and basic OCR results
            if 'ocr_results' in self.last_scan_results:
                old_ocr = self.last_scan_results.get('ocr_results', {})
                old_poker = self.last_scan_results.get('poker_analysis', {})
                old_deck = old_poker.get('deck_analysis', {})
            else:
                old_ocr = self.last_scan_results
                old_poker = {}
                old_deck = {}
        else:
            old_ocr = {}
            old_poker = {}
            old_deck = {}
        
        # Compare key game elements
        old_hero = old_ocr.get('hero_cards', [])
        new_hero = new_ocr.get('hero_cards', [])
        
        old_community = old_ocr.get('community_cards', [])
        new_community = new_ocr.get('community_cards', [])
        
        old_pot = old_ocr.get('pot', '')
        new_pot = new_ocr.get('pot', '')
        
        old_stage = old_ocr.get('stage', '')
        new_stage = new_ocr.get('stage', '')
        
        # Compare poker analysis elements
        old_hand_rank = old_poker.get('hand_ranking', '')
        new_hand_rank = new_poker.get('hand_ranking', '')
        
        # Compare player count elements
        old_active_players = old_deck.get('active_seated_players', 0)
        new_active_players = new_deck.get('active_seated_players', 0)
        
        # Check for significant changes
        changes = [
            old_hero != new_hero,              # New hero cards
            old_community != new_community,    # New community cards  
            old_pot != new_pot,               # Pot size change
            old_stage != new_stage,           # Game stage change
            old_hand_rank != new_hand_rank,   # Hand ranking change
            old_active_players != new_active_players  # Player count change
        ]
        
        return any(changes)
    
    def display_auto_scan_update(self, enhanced_analysis):
        """Display compact tournament analysis update for auto-scan results."""
        timestamp = time.strftime("%H:%M:%S")
        
        # Extract key data
        ocr_results = enhanced_analysis.get('ocr_results', {})
        poker_analysis = enhanced_analysis.get('poker_analysis', {})
        deck_analysis = poker_analysis.get('deck_analysis', {})
        
        # Hero cards
        hero_cards = [card for card in ocr_results.get('hero_cards', []) if card]
        hero_str = ' '.join(hero_cards) if hero_cards else 'None'
        
        # Community cards
        community_cards = [card for card in ocr_results.get('community_cards', []) if card]
        community_str = ' '.join(community_cards) if community_cards else 'None'
        
        # Pot and stage
        pot = ocr_results.get('pot', 'Unknown')
        stage = ocr_results.get('stage', 'Unknown')
        
        # Poker engine data
        hero_evaluation = poker_analysis.get('hero_hand_evaluation', {})
        hand_ranking = hero_evaluation.get('hand_name', 'Unknown') if hero_evaluation else 'Unknown'
        hand_description = hero_evaluation.get('description', 'Unknown') if hero_evaluation else 'Unknown'
        
        # Deck data
        known_cards = deck_analysis.get('known_cards', 0)
        remaining_deck = deck_analysis.get('remaining_deck_size', 0)
        seated_players = deck_analysis.get('seated_players', 0)
        active_seated = deck_analysis.get('active_seated_players', 0)
        estimated_in_hand = deck_analysis.get('estimated_active_players', 0)
        
        # Total analysis time - get from OCR results total time if available
        total_time = enhanced_analysis.get('total_analysis_time_ms', 0)
        if total_time == 0:
            # Fallback to poker engine processing time
            total_time = poker_analysis.get('processing_time_ms', 0)
        
        # Get probability analysis
        probability_analysis = enhanced_analysis.get('probability_analysis', {})
        prob_text = ""
        if probability_analysis:
            equity = probability_analysis.get('equity', {})
            if equity:
                win_pct = equity.get('win_percentage', 0)
                lose_pct = equity.get('lose_percentage', 0)
                prob_text = f" | 📊 Win: {win_pct:.1f}% | Lose: {lose_pct:.1f}%"
        
        # Compact display
        update_text = f"\n🔄 Auto-Scan - {timestamp} | {total_time:.0f}ms\n"
        update_text += f"   🎯 {stage} | 🃏 {hero_str} | 🌟 {community_str} | 💰 {pot}\n"
        update_text += f"   🎲 {hand_ranking}: {hand_description}{prob_text}\n"
        update_text += f"   📊 {known_cards} known | {remaining_deck} remaining | {seated_players} seated | {active_seated} active | {estimated_in_hand} in hand\n"
        
        # Insert compact update
        self.results_text.insert(tk.END, update_text)
        
        # Limit text area size to prevent performance issues
        content = self.results_text.get("1.0", tk.END)
        lines = content.split('\n')
        if len(lines) > 500:  # Keep only last 500 lines
            self.results_text.delete("1.0", f"{len(lines) - 500}.0")
        
        self.results_text.see(tk.END)
    
    def start_card_confirmation(self):
        """Start the card confirmation process."""
        if not self.last_scan_results:
            self.status_label.config(text="No scan results to confirm - run analysis first", fg='#ff8888')
            return
        
        # Pause auto-scanning during confirmation to prevent frame changes
        was_auto_scan_enabled = self.auto_scan_enabled
        if was_auto_scan_enabled:
            self.toggle_auto_scan()  # This will stop auto-scanning
            print("🔒 Auto-scanning paused during card confirmation")
        
        self.confirmation_mode = True
        
        # Freeze the current frame for confirmation - this ensures the cards being
        # confirmed match exactly what the user is seeing
        self.confirmation_frame = self.current_frame.copy() if self.current_frame is not None else None
        
        self.current_confirmation_data = {
            'original_results': self.last_scan_results.copy(),
            'confirmed_cards': {},
            'corrections': {},
            'was_auto_scan_enabled': was_auto_scan_enabled  # Remember to restore later
        }
        
        print("🎯 Card confirmation started - frame frozen for consistency")
        self.show_card_confirmation_dialog()
    
    def show_card_confirmation_dialog(self):
        """Show card confirmation dialog window."""
        if not self.current_confirmation_data:
            return
        
        # Create confirmation window
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("🃏 Card Confirmation")
        confirm_window.geometry("600x500")
        confirm_window.configure(bg='#0d1117')
        
        # Title
        tk.Label(
            confirm_window,
            text="Confirm Detected Cards",
            bg='#0d1117',
            fg='#e6edf3',
            font=('Arial', 16, 'bold')
        ).pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            confirm_window,
            text="Click ✅ to confirm or ❌ to mark incorrect. Enter correct card if wrong.",
            bg='#0d1117',
            fg='#888888',
            font=('Arial', 10)
        )
        instructions.pack(pady=5)
        
        # Card confirmation frame
        card_frame = tk.Frame(confirm_window, bg='#161b22')
        card_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.create_card_confirmation_ui(card_frame, confirm_window)
    
    def create_card_confirmation_ui(self, parent_frame, confirm_window):
        """Create the card confirmation UI elements."""
        results = self.current_confirmation_data['original_results']
        
        # Hero cards section
        hero_frame = tk.LabelFrame(parent_frame, text="Hero Cards", bg='#161b22', fg='#e6edf3', font=('Arial', 12, 'bold'))
        hero_frame.pack(fill=tk.X, pady=5)
        
        hero_cards = results.get('hero_cards', [])
        for i, card in enumerate(hero_cards):
            if card:
                self.create_card_row(hero_frame, f"Hero Card {i+1}", card, f"hero_card_{i+1}")
        
        # Community cards section  
        community_frame = tk.LabelFrame(parent_frame, text="Community Cards", bg='#161b22', fg='#e6edf3', font=('Arial', 12, 'bold'))
        community_frame.pack(fill=tk.X, pady=5)
        
        community_cards = results.get('community_cards', [])
        for i, card in enumerate(community_cards):
            if card:
                self.create_card_row(community_frame, f"Community {i+1}", card, f"community_card_{i+1}")
        
        # Buttons
        button_frame = tk.Frame(confirm_window, bg='#0d1117')
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="💾 Save Confirmations",
            command=lambda: self.save_confirmations(confirm_window),
            bg='#00ff88',
            fg='black',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=confirm_window.destroy,
            bg='#ff4444',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
    
    def create_card_row(self, parent, label, detected_card, card_id):
        """Create a single card confirmation row."""
        row_frame = tk.Frame(parent, bg='#161b22')
        row_frame.pack(fill=tk.X, pady=2, padx=10)
        
        # Label
        tk.Label(
            row_frame,
            text=f"{label}:",
            bg='#161b22',
            fg='#e6edf3',
            font=('Arial', 10),
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT)
        
        # Detected card display
        card_label = tk.Label(
            row_frame,
            text=detected_card,
            bg='#333333',
            fg='#ffffff',
            font=('Arial', 12, 'bold'),
            width=8,
            relief=tk.RAISED,
            borderwidth=2
        )
        card_label.pack(side=tk.LEFT, padx=5)
        
        # Correction entry (create first)
        correction_entry = tk.Entry(
            row_frame,
            bg='#333333',
            fg='#ffffff',
            font=('Arial', 12),
            width=8,
            state='disabled'
        )
        correction_entry.pack(side=tk.LEFT, padx=5)
        
        # Confirm button  
        confirm_var = tk.BooleanVar(value=True)
        confirm_check = tk.Checkbutton(
            row_frame,
            text="✅",
            variable=confirm_var,
            bg='#161b22',
            fg='#00ff88',
            selectcolor='#333333',
            font=('Arial', 14),
            command=lambda: self.toggle_card_confirmation(card_id, confirm_var.get(), correction_entry)
        )
        confirm_check.pack(side=tk.LEFT, padx=5)
        
        # Incorrect button
        incorrect_check = tk.Checkbutton(
            row_frame,
            text="❌",
            bg='#161b22',
            fg='#ff4444',
            selectcolor='#333333',
            font=('Arial', 14),
            command=lambda: self.mark_card_incorrect(card_id, confirm_var, correction_entry, confirm_check, incorrect_check)
        )
        incorrect_check.pack(side=tk.LEFT, padx=5)
        
        # Store widget references for this card
        if not hasattr(self, 'confirmation_widgets'):
            self.confirmation_widgets = {}
        
        self.confirmation_widgets[card_id] = {
            'confirm_var': confirm_var,
            'confirm_check': confirm_check,
            'incorrect_check': incorrect_check,
            'correction_entry': correction_entry,
            'card_label': card_label,
            'detected': detected_card
        }
        
        # Initialize confirmation states
        if not hasattr(self.current_confirmation_data, 'confirmed_cards'):
            self.current_confirmation_data['confirmed_cards'] = {}
        if not hasattr(self.current_confirmation_data, 'corrections'):
            self.current_confirmation_data['corrections'] = {}
            
        self.current_confirmation_data['confirmed_cards'][card_id] = True
        # Don't initialize corrections - only add when needed
    
    def mark_card_incorrect(self, card_id, confirm_var, correction_entry, confirm_check, incorrect_check):
        """Mark card as incorrect and enable correction entry."""
        # Uncheck the confirm button
        confirm_var.set(False)
        
        # Enable correction entry
        correction_entry.config(state='normal', bg='#444444')
        correction_entry.focus()
        
        # Update confirmation state
        self.current_confirmation_data['confirmed_cards'][card_id] = False
        print(f"🔧 Card {card_id} marked as incorrect - correction entry enabled")
    
    def toggle_card_confirmation(self, card_id, is_confirmed, correction_entry):
        """Toggle card confirmation state."""
        if is_confirmed:
            # Card is confirmed as correct
            correction_entry.config(state='disabled', bg='#333333')
            self.current_confirmation_data['confirmed_cards'][card_id] = True
            # Remove any existing correction entry since card is confirmed correct
            if card_id in self.current_confirmation_data['corrections']:
                del self.current_confirmation_data['corrections'][card_id]
            print(f"✅ Card {card_id} confirmed as correct")
        else:
            # Card needs correction
            correction_entry.config(state='normal', bg='#444444')
            correction_entry.focus()
            self.current_confirmation_data['confirmed_cards'][card_id] = False
            print(f"❌ Card {card_id} marked for correction")
    
    def save_confirmations(self, confirm_window):
        """Save the card confirmations for learning."""
        if not self.current_confirmation_data:
            return
        
        # Collect corrections from entry fields
        for card_id, widgets in self.confirmation_widgets.items():
            # Check if card is marked as incorrect
            if not self.current_confirmation_data['confirmed_cards'].get(card_id, True):
                correction_text = widgets['correction_entry'].get().strip()
                if correction_text:  # Only add if correction text is not empty
                    self.current_confirmation_data['corrections'][card_id] = correction_text
                    print(f"📝 Correction for {card_id}: '{correction_text}'")
                else:
                    print(f"⚠️ Card {card_id} marked incorrect but no correction provided")
        
        # Save to learning data file
        self.save_learning_data()
        
        # Update results display
        self.update_results_with_confirmations()
        
        # Close window
        confirm_window.destroy()
        
        # Restore auto-scanning if it was enabled before confirmation
        was_auto_scan_enabled = self.current_confirmation_data.get('was_auto_scan_enabled', False)
        if was_auto_scan_enabled and not self.auto_scan_enabled:
            self.toggle_auto_scan()  # Restore auto-scanning
            print("🔓 Auto-scanning resumed after card confirmation")
        
        # Reset confirmation state
        self.confirmation_mode = False
        self.current_confirmation_data = None
        self.confirmation_widgets = {}
        self.confirmation_frame = None  # Clear the frozen frame
        
        self.status_label.config(text="✅ Card confirmations saved for learning", fg='#00ff88')
    
    def save_learning_data(self):
        """Save confirmation data for OCR learning with smart duplicate detection."""
        
        learning_file = 'card_learning_data.json'
        
        # Load existing data
        learning_data = {}
        if os.path.exists(learning_file):
            try:
                with open(learning_file, 'r') as f:
                    learning_data = json.load(f)
            except Exception as e:
                print(f"Error loading learning data: {e}")
                learning_data = {}
        
        # Initialize structure if needed
        if 'corrections' not in learning_data:
            learning_data['corrections'] = []
        if 'card_database' not in learning_data:
            learning_data['card_database'] = {}
        if 'stats' not in learning_data:
            learning_data['stats'] = {'total_corrections': 0, 'unique_cards': 0}
        
        # Process each confirmed/corrected card
        cards_processed = 0
        cards_updated = 0
        cards_new = 0
        
        for region, corrected_card in self.current_confirmation_data['corrections'].items():
            if corrected_card and corrected_card.strip():
                # Normalize card notation (converts "Ks" to "K♠", etc.)
                normalized_card = self.normalize_card_notation(corrected_card)
                if not normalized_card:
                    print(f"⚠️ Skipping invalid card notation: {corrected_card}")
                    continue
                
                # Generate card image hash for duplicate detection
                card_hash = self.get_card_image_hash(region)
                
                if card_hash:
                    # Get original OCR result for this region
                    original_ocr = self.get_original_ocr_for_region(region)
                    print(f"🔍 Processing card: {region} = {corrected_card} → {normalized_card} (hash: {card_hash[:8]}...)")
                    
                    # Check if this exact card image already exists
                    if card_hash in learning_data['card_database']:
                        existing_card = learning_data['card_database'][card_hash]['card']
                        card_entry = learning_data['card_database'][card_hash]
                        
                        # Add this region to the list of regions where this card was seen
                        if 'regions_seen' not in card_entry:
                            card_entry['regions_seen'] = [card_entry.get('first_seen_region', region)]
                        if region not in card_entry['regions_seen']:
                            card_entry['regions_seen'].append(region)
                        
                        if existing_card != normalized_card:
                            print(f"📝 Updating card: {existing_card} → {normalized_card} (universal)")
                            card_entry['card'] = normalized_card
                            card_entry['updated'] = datetime.now().isoformat()
                            card_entry['update_count'] = card_entry.get('update_count', 0) + 1
                            cards_updated += 1
                        else:
                            print(f"🔄 Card already learned: {normalized_card} (universal - works for all regions)")
                    else:
                        # New card - add to database (region-agnostic)
                        learning_data['card_database'][card_hash] = {
                            'card': normalized_card,
                            'first_seen_region': region,  # Track where first seen, but use everywhere
                            'regions_seen': [region],  # Track all regions where this card appeared
                            'first_seen': datetime.now().isoformat(),
                            'confidence': 1.0,
                            'usage_count': 1,
                            'original_ocr': original_ocr,
                            'original_input': corrected_card,  # Keep original user input for reference
                            'universal': True  # This card can be used for any region
                        }
                        cards_new += 1
                        print(f"🆕 New card learned: {corrected_card} → {normalized_card}")
                else:
                    print(f"❌ Failed to generate hash for {region}: {corrected_card}")
                
                cards_processed += 1
        
        # Add correction entry for training history
        if cards_processed > 0:
            correction_entry = {
                'timestamp': datetime.now().isoformat(),
                'original_results': self.current_confirmation_data['original_results'],
                'confirmed_cards': self.current_confirmation_data['confirmed_cards'],
                'corrections': self.current_confirmation_data['corrections'],
                'scan_type': 'manual_confirmation',
                'cards_processed': cards_processed,
                'cards_new': cards_new,
                'cards_updated': cards_updated
            }
            
            learning_data['corrections'].append(correction_entry)
        
        # Update stats
        learning_data['stats']['total_corrections'] = len(learning_data['corrections'])
        learning_data['stats']['unique_cards'] = len(learning_data['card_database'])
        
        # Save updated data
        try:
            with open(learning_file, 'w') as f:
                json.dump(learning_data, f, indent=2)
            print(f"📚 Learning database: {learning_data['stats']['unique_cards']} unique cards, {learning_data['stats']['total_corrections']} sessions")
            print(f"✅ Session: {cards_new} new, {cards_updated} updated, {cards_processed - cards_new - cards_updated} duplicates skipped")
        except Exception as e:
            print(f"❌ Error saving learning data: {e}")
    
    def get_original_ocr_for_region(self, region):
        """Extract the original OCR result for a specific region."""
        original_results = self.current_confirmation_data.get('original_results', {})
        
        if region.startswith('hero_card_'):
            # Hero cards are in hero_cards array
            hero_cards = original_results.get('hero_cards', [])
            if region == 'hero_card_1' and len(hero_cards) > 0:
                return hero_cards[0]
            elif region == 'hero_card_2' and len(hero_cards) > 1:
                return hero_cards[1]
        elif region.startswith('community_card_'):
            # Community cards are in community_cards array
            community_cards = original_results.get('community_cards', [])
            card_index = int(region.split('_')[-1]) - 1  # Extract number and convert to 0-based index
            if 0 <= card_index < len(community_cards):
                return community_cards[card_index]
        
        return 'unknown'
    
    def get_card_image_hash(self, region_name):
        """Generate a hash of the card image for duplicate detection."""
        try:
            # Use confirmation frame if in confirmation mode, otherwise use current frame
            frame_to_use = None
            if self.confirmation_mode and hasattr(self, 'confirmation_frame') and self.confirmation_frame is not None:
                frame_to_use = self.confirmation_frame
                print(f"🔒 Using frozen confirmation frame for {region_name}")
            elif self.current_frame is not None:
                frame_to_use = self.current_frame
            
            if frame_to_use is None:
                return None
                
            # Get region coordinates from poker bot
            if hasattr(self.bot, 'current_regions') and region_name in self.bot.current_regions:
                x, y, w, h = self.bot.current_regions[region_name]
                
                # Extract card image from the appropriate frame
                card_img = frame_to_use[y:y+h, x:x+w]
                
                # Resize to standard size for consistent hashing
                card_img = cv2.resize(card_img, (100, 150))
                
                # Convert to grayscale for consistent comparison
                gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
                
                # Apply slight blur to reduce noise differences
                gray = cv2.GaussianBlur(gray, (3, 3), 0)
                
                # Calculate hash using image content
                img_hash = hashlib.md5(gray.tobytes()).hexdigest()
                return img_hash
                
        except Exception as e:
            print(f"❌ Error generating card hash for {region_name}: {e}")
            return None
    
    def lookup_learned_card(self, region_name):
        """Look up a card from the learning database for faster recognition."""
        try:
            learning_file = 'card_learning_data.json'
            if not os.path.exists(learning_file):
                return None
                
            card_hash = self.get_card_image_hash(region_name)
            if not card_hash:
                return None
                
            with open(learning_file, 'r') as f:
                data = json.load(f)
            
            if card_hash in data.get('card_database', {}):
                card_data = data['card_database'][card_hash]
                # Increment usage count
                card_data['usage_count'] = card_data.get('usage_count', 0) + 1
                card_data['last_used'] = datetime.now().isoformat()
                
                # Save updated usage
                with open(learning_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"🎯 Fast lookup: {card_data['card']} (used {card_data['usage_count']} times)")
                return card_data['card']
                
        except Exception as e:
            print(f"❌ Error looking up learned card: {e}")
            
        return None
    
    def update_results_with_confirmations(self):
        """Update the results display with confirmed/corrected cards."""
        timestamp = time.strftime("%H:%M:%S")
        
        confirmed_count = sum(1 for confirmed in self.current_confirmation_data['confirmed_cards'].values() if confirmed)
        total_cards = len(self.current_confirmation_data['confirmed_cards'])
        correction_count = len(self.current_confirmation_data['corrections'])
        
        update_text = f"\n✅ {timestamp} CARD CONFIRMATION:\n"
        update_text += f"   📊 Confirmed: {confirmed_count}/{total_cards} cards\n"
        update_text += f"   🔧 Corrections: {correction_count} cards\n"
        
        if self.current_confirmation_data['corrections']:
            update_text += "   🃏 Corrected cards:\n"
            for card_id, correction in self.current_confirmation_data['corrections'].items():
                original = self.confirmation_widgets[card_id]['detected']
                update_text += f"      {card_id}: {original} → {correction}\n"
        
        self.results_text.insert(tk.END, update_text)
        self.results_text.see(tk.END)
    
    def display_results(self, results):
        """Display OCR results in GUI with poker engine integration."""
        timestamp = time.strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"\n{'='*60}\n")
        self.results_text.insert(tk.END, f"📊 Analysis Results - {timestamp}\n")
        self.results_text.insert(tk.END, f"{'='*60}\n\n")
        
        # Check if this is an enhanced analysis with poker engine
        if isinstance(results, dict) and 'poker_analysis' in results:
            self.display_poker_engine_results(results)
        else:
            self.display_basic_ocr_results(results)
        
        self.results_text.insert(tk.END, "\n")
        self.results_text.see(tk.END)
    
    def display_poker_engine_results(self, enhanced_analysis):
        """Display enhanced poker engine analysis results."""
        # Extract OCR and poker analysis
        ocr_results = enhanced_analysis.get('ocr_results', {})
        poker_analysis = enhanced_analysis.get('poker_analysis', {})
        gui_display = enhanced_analysis.get('gui_display', {})
        
        # Basic OCR results
        self.results_text.insert(tk.END, "🎯 GAME STATE:\n")
        
        # Hero cards
        hero_cards = poker_analysis.get('hero_cards', [])
        if hero_cards and any(hero_cards):
            self.results_text.insert(tk.END, f"🃏 Hero Cards: {' '.join(filter(None, hero_cards))}\n")
        else:
            self.results_text.insert(tk.END, "🃏 Hero Cards: None detected\n")
        
        # Community cards
        community_cards = poker_analysis.get('community_cards', [])
        if community_cards and any(community_cards):
            self.results_text.insert(tk.END, f"🌟 Community Cards: {' '.join(filter(None, community_cards))}\n")
        else:
            self.results_text.insert(tk.END, "🌟 Community Cards: None detected\n")
        
        # Pot and stage
        pot_size = poker_analysis.get('pot_size')
        if pot_size:
            self.results_text.insert(tk.END, f"💰 Pot Size: ${pot_size:.2f}\n")
        else:
            self.results_text.insert(tk.END, "💰 Pot Size: Not detected\n")
        
        stage = poker_analysis.get('stage', 'Unknown')
        self.results_text.insert(tk.END, f"📊 Stage: {stage}\n")
        
        # POKER ENGINE ANALYSIS
        self.results_text.insert(tk.END, f"\n🧠 POKER ENGINE ANALYSIS:\n")
        
        # Hand evaluation
        hand_eval = poker_analysis.get('hero_hand_evaluation')
        if hand_eval:
            self.results_text.insert(tk.END, f"🎲 Hand: {hand_eval['hand_name']}\n")
            self.results_text.insert(tk.END, f"📋 Description: {hand_eval['description']}\n")
            self.results_text.insert(tk.END, f"💪 Strength Score: {hand_eval['rank_score']}\n")
            
            if len(hand_eval.get('best_five_cards', [])) == 5:
                self.results_text.insert(tk.END, f"🏆 Best 5 Cards: {' '.join(hand_eval['best_five_cards'])}\n")
        else:
            self.results_text.insert(tk.END, "🎲 Hand: Not evaluated\n")
        
        # Deck analysis
        deck_analysis = poker_analysis.get('deck_analysis', {})
        if deck_analysis:
            self.results_text.insert(tk.END, f"\n🃏 DECK ANALYSIS:\n")
            self.results_text.insert(tk.END, f"   📊 Known Cards: {deck_analysis.get('known_cards', 0)}\n")
            self.results_text.insert(tk.END, f"   🎲 Remaining Deck: {deck_analysis.get('remaining_deck_size', 0)} cards\n")
            
            # Enhanced player analysis
            seated = deck_analysis.get('seated_players', 0)
            sitting_out = deck_analysis.get('sitting_out_players', 0)
            active_seated = deck_analysis.get('active_seated_players', 0)
            cards_dealt = deck_analysis.get('cards_dealt_to_seated', 0)
            
            self.results_text.insert(tk.END, f"   👥 Seated Players: {seated}\n")
            if sitting_out > 0:
                self.results_text.insert(tk.END, f"   💤 Sitting Out: {sitting_out}\n")
            self.results_text.insert(tk.END, f"   ✅ Active Seated: {active_seated}\n")
            self.results_text.insert(tk.END, f"   🎴 Cards Dealt to Seated: {cards_dealt}\n")
            
            # Opponent card detection results
            if 'opponent_cards' in enhanced_analysis:
                opp_data = enhanced_analysis['opponent_cards']
                active_opponents = opp_data.get('active_opponents', [])
                if active_opponents:
                    positions = ', '.join([pos.replace('Position_', 'P') for pos in active_opponents])
                    self.results_text.insert(tk.END, f"   🎯 Opponents with Cards: {positions}\n")
                    self.results_text.insert(tk.END, f"   🎮 Players in Hand: {opp_data.get('total_active_players', 0)}\n")
        
        # Probability analysis
        probability_analysis = enhanced_analysis.get('probability_analysis')
        if probability_analysis:
            self.results_text.insert(tk.END, f"\n🎲 PROBABILITY ANALYSIS:\n")
            
            # Equity analysis
            if 'equity' in probability_analysis:
                equity = probability_analysis['equity']
                win_pct = equity.get('win_percentage', 0)
                tie_pct = equity.get('tie_percentage', 0)
                lose_pct = equity.get('lose_percentage', 0)
                self.results_text.insert(tk.END, f"   📊 Win: {win_pct:.1f}% | Tie: {tie_pct:.1f}% | Lose: {lose_pct:.1f}%\n")
            
            # Opponent analysis
            if 'opponent_analysis' in probability_analysis:
                opp_analysis = probability_analysis['opponent_analysis']
                if 'average_hand_strength' in opp_analysis:
                    avg_strength = opp_analysis['average_hand_strength']
                    self.results_text.insert(tk.END, f"   🎯 Opponent Avg Strength: {avg_strength:.3f}\n")
                
                if 'hand_combinations' in opp_analysis:
                    combinations = opp_analysis['hand_combinations']
                    self.results_text.insert(tk.END, f"   🃏 Possible Combinations:\n")
                    for hand_type, count in combinations.items():
                        if count > 0:
                            self.results_text.insert(tk.END, f"      {hand_type}: {count}\n")
            
            # Board texture
            if 'board_texture' in probability_analysis:
                texture = probability_analysis['board_texture']
                draws = []
                if texture.get('flush_draw_possible'): draws.append("Flush")
                if texture.get('straight_draw_possible'): draws.append("Straight")
                if texture.get('paired_board'): draws.append("Paired")
                
                if draws:
                    self.results_text.insert(tk.END, f"   ⚠️ Board Texture: {', '.join(draws)}\n")
                
                # Show outs if available
                if 'draws' in probability_analysis:
                    draw_info = probability_analysis['draws']
                    total_outs = draw_info.get('total_outs', 0)
                    if total_outs > 0:
                        self.results_text.insert(tk.END, f"   🎯 Total Outs: {total_outs}\n")
        
        # Performance
        ocr_time = ocr_results.get('analysis_time_ms', 0)
        poker_time = poker_analysis.get('processing_time_ms', 0)
        total_time = ocr_time + poker_time
        self.results_text.insert(tk.END, f"\n⚡ Performance: {total_time:.1f}ms total ({ocr_time:.1f}ms OCR + {poker_time:.1f}ms Engine)\n")
    
    def display_basic_ocr_results(self, results):
        """Display basic OCR results when poker engine is not available."""
        if isinstance(results, dict):
            # Hero cards
            if 'hero_cards' in results and results['hero_cards']:
                hero_list = [card for card in results['hero_cards'] if card]
                if hero_list:
                    self.results_text.insert(tk.END, f"🃏 Hero Cards: {hero_list}\n")
                else:
                    self.results_text.insert(tk.END, "🃏 Hero Cards: None detected\n")
            else:
                self.results_text.insert(tk.END, "🃏 Hero Cards: None detected\n")
            
            # Community cards
            if 'community_cards' in results and results['community_cards']:
                community_list = [card for card in results['community_cards'] if card]
                if community_list:
                    self.results_text.insert(tk.END, f"🌟 Community Cards: {community_list}\n")
                else:
                    self.results_text.insert(tk.END, "🌟 Community Cards: None detected\n")
            else:
                self.results_text.insert(tk.END, "🌟 Community Cards: None detected\n")
            
            # Pot size
            if 'pot' in results and results['pot']:
                self.results_text.insert(tk.END, f"💰 Pot Size: {results['pot']}\n")
            else:
                self.results_text.insert(tk.END, "💰 Pot Size: Not detected\n")
            
            # Stage
            if 'stage' in results and results['stage']:
                self.results_text.insert(tk.END, f"📊 Stage: {results['stage']}\n")
            else:
                self.results_text.insert(tk.END, "📊 Stage: Unknown\n")
                
            # Performance
            if 'analysis_time_ms' in results:
                self.results_text.insert(tk.END, f"⚡ Analysis Time: {results['analysis_time_ms']:.1f}ms\n")
                
        self.results_text.insert(tk.END, "\n")
        self.results_text.see(tk.END)
    
    def adjust_regions(self):
        """Open region adjustment window."""
        self.status_label.config(text="🔧 Opening region adjustment...", fg='#ffdd33')
        
        frame = self.capture_frame()
        if frame is None:
            self.status_label.config(text="❌ Failed to capture for adjustment", fg='#ff4444')
            return
        
        # Open region adjustment in a separate thread to avoid GUI blocking
        import threading
        def run_adjustment():
            try:
                self.open_region_adjustment_gui(frame)
                self.root.after(0, lambda: self.status_label.config(text="✅ Region adjustment complete", fg='#00ff88'))
            except Exception as e:
                print(f"❌ Region adjustment error: {e}")
                self.root.after(0, lambda: self.status_label.config(text="❌ Region adjustment failed", fg='#ff4444'))
        
        threading.Thread(target=run_adjustment, daemon=True).start()

    def open_region_adjustment_gui(self, frame):
        """Open template-based region adjustment window."""
        window_name = "Template Region Adjustment"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1200, 800)
        
        # Template system
        templates = {}  # Store template sizes for each region type
        temp_regions = {}
        drawing = False
        start_point = None
        template_mode = False
        
        # Load existing regions if available
        try:
            if hasattr(self.bot, 'current_regions'):
                for name, coords in self.bot.current_regions.items():
                    x, y, w, h = coords
                    temp_regions[name] = ((x, y), (x + w, y + h))
        except Exception as e:
            print(f"⚠️ Could not load existing regions: {e}")
        
        # Region groups with templates
        region_groups = {
            'hero_cards': {
                'template': None,
                'regions': ['hero_card_1', 'hero_card_2'],
                'color': (0, 255, 0),  # Green
                'description': 'Hero Cards'
            },
            'community_cards': {
                'template': None,
                'regions': ['community_card_1', 'community_card_2', 'community_card_3', 'community_card_4', 'community_card_5'],
                'color': (0, 255, 255),  # Yellow
                'description': 'Community Cards'
            },
            'player_stacks': {
                'template': None,
                'regions': [f'Position_{i}_stack' for i in range(1, 9)],  # 8 opponents (1-8)
                'color': (0, 165, 255),  # Orange
                'description': 'Player Stacks'
            },
            'player_names': {
                'template': None,
                'regions': [f'Position_{i}_name' for i in range(1, 9)],  # 8 opponents (1-8)
                'color': (255, 255, 0),  # Cyan
                'description': 'Player Names'
            },
            'other': {
                'template': None,
                'regions': ['pot_size', 'Hero_stack', 'Hero_name'],
                'color': (255, 0, 255),  # Magenta
                'description': 'Other Elements'
            }
        }
        
        # Current state
        current_group = 'hero_cards'
        current_region_in_group = 0
        
        def get_current_region():
            group = region_groups[current_group]
            if current_region_in_group < len(group['regions']):
                return group['regions'][current_region_in_group]
            return None
        
        def get_template_size(group_name):
            """Get the template size for a group if it exists."""
            return region_groups[group_name]['template']
        
        def set_template_size(group_name, width, height):
            """Set the template size for a group."""
            region_groups[group_name]['template'] = (width, height)
            print(f"📐 Template set for {region_groups[group_name]['description']}: {width}x{height}")
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal drawing, start_point, temp_regions, template_mode
            
            current_region = get_current_region()
            if not current_region:
                return
                
            group = region_groups[current_group]
            template_size = get_template_size(current_group)
            
            if event == cv2.EVENT_LBUTTONDOWN:
                if template_size is None:
                    # First region of this type - create template
                    drawing = True
                    start_point = (x, y)
                    template_mode = False
                    print(f"🎨 Creating template for {group['description']} - drag to set size")
                else:
                    # Use template - just position it
                    width, height = template_size
                    # Center the template on click point
                    start_x = max(0, x - width // 2)
                    start_y = max(0, y - height // 2)
                    end_x = start_x + width
                    end_y = start_y + height
                    
                    temp_regions[current_region] = ((start_x, start_y), (end_x, end_y))
                    print(f"✅ Positioned {current_region} using template")
                    
                    # Move to next region in group
                    next_region()
                    
            elif event == cv2.EVENT_MOUSEMOVE and drawing:
                # Only when creating template
                display_current_drawing(x, y)
                
            elif event == cv2.EVENT_LBUTTONUP and drawing:
                drawing = False
                end_point = (x, y)
                
                # Calculate template size
                width = abs(end_point[0] - start_point[0])
                height = abs(end_point[1] - start_point[1])
                
                if width > 10 and height > 10:  # Minimum size check
                    # Set template for this group
                    set_template_size(current_group, width, height)
                    
                    # Add the first region
                    temp_regions[current_region] = (start_point, end_point)
                    print(f"✅ Created template region: {current_region}")
                    
                    # Move to next region in group
                    next_region()
                else:
                    print("⚠️ Region too small, try again")
        
        def display_current_drawing(mouse_x, mouse_y):
            """Display the frame with current drawing state."""
            display = frame.copy()
            
            # Draw existing regions
            for name, coords in temp_regions.items():
                group_name = next((gname for gname, gdata in region_groups.items() if name in gdata['regions']), 'other')
                color = region_groups[group_name]['color']
                cv2.rectangle(display, coords[0], coords[1], color, 2)
                cv2.putText(display, name, (coords[0][0], coords[0][1] - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Draw current rectangle being drawn
            if drawing and start_point:
                cv2.rectangle(display, start_point, (mouse_x, mouse_y), (255, 0, 0), 2)
            
            # Show current region info
            current_region = get_current_region()
            if current_region:
                group = region_groups[current_group]
                template_size = get_template_size(current_group)
                
                info_text = f"Current: {current_region} ({group['description']})"
                if template_size:
                    info_text += f" [Template: {template_size[0]}x{template_size[1]}]"
                else:
                    info_text += " [Creating Template]"
                    
                cv2.putText(display, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.putText(display, f"Regions: {len(temp_regions)}", (10, display.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow(window_name, display)
        
        def next_region():
            """Move to next region in current group or next group."""
            nonlocal current_group, current_region_in_group
            
            print(f"🔍 DEBUG next_region() called: current_group={current_group}, current_region_in_group={current_region_in_group}")
            
            current_region_in_group += 1
            group = region_groups[current_group]
            
            print(f"🔍 DEBUG after increment: current_region_in_group={current_region_in_group}, group_size={len(group['regions'])}")
            
            if current_region_in_group >= len(group['regions']):
                # Move to next group
                group_names = list(region_groups.keys())
                current_group_index = group_names.index(current_group)
                
                if current_group_index < len(group_names) - 1:
                    current_group = group_names[current_group_index + 1]
                    current_region_in_group = 0
                    next_group = region_groups[current_group]
                    print(f"📂 Moving to {next_group['description']} - starting at index 0")
                    # When moving to new group, display the first region and return
                    current_region = get_current_region()
                    print(f"🔍 NEW GROUP: current_group={current_group}, current_region_in_group={current_region_in_group}, current_region={current_region}")
                    if current_region:
                        group = region_groups[current_group]
                        template_size = get_template_size(current_group)
                        if template_size:
                            print(f"📍 Position {current_region} (click to place)")
                        else:
                            print(f"🎨 Create template for {group['description']} ({current_region})")
                    return  # Exit early to prevent double increment
                    print(f"� Moving to {next_group['description']}")
                else:
                    print("🎉 All regions completed! Press 's' to save or continue adjusting.")
                    return
            
            current_region = get_current_region()
            if current_region:
                group = region_groups[current_group]
                template_size = get_template_size(current_group)
                if template_size:
                    print(f"📍 Position {current_region} (click to place)")
                else:
                    print(f"🎨 Create template for {group['description']} ({current_region})")
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        print("\n🎨 Template-Based Region Adjustment")
        print("=" * 50)
        print("📋 INSTRUCTIONS:")
        print("1️⃣  First region of each type: DRAG to create template size")
        print("2️⃣  Subsequent regions: CLICK to position using template")
        print("3️⃣  Templates are automatically created for each group")
        print("\n🎨 REGION GROUPS:")
        for group_name, group_data in region_groups.items():
            color_name = {(0,255,0): "Green", (0,255,255): "Yellow", (0,165,255): "Orange", 
                         (255,255,0): "Cyan", (255,0,255): "Magenta"}.get(tuple(group_data['color']), "Unknown")
            print(f"   {group_data['description']}: {color_name} ({len(group_data['regions'])} regions)")
        print("\n⌨️  CONTROLS:")
        print("   SPACE: Skip to next group")
        print("   S: Save all regions")
        print("   R: Reset current group template")
        print("   C: Clear all regions")
        print("   Q: Quit without saving")
        print("=" * 50)
        
        # Start with first region - display initial state  
        current_region = get_current_region()
        if current_region:
            group = region_groups[current_group]
            template_size = get_template_size(current_group)
            print(f"🎯 Starting with: {current_region}")
            print(f"🔍 DEBUG: current_group={current_group}, current_region_in_group={current_region_in_group}")
            if template_size:
                print(f"📍 Position {current_region} (click to place)")
            else:
                print(f"🎨 Create template for {group['description']} ({current_region})")
        
        while True:
            current_region = get_current_region()
            if not drawing:
                display_current_drawing(0, 0)
            
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                print(f"🔍 S key pressed! temp_regions count: {len(temp_regions)}")
                if temp_regions:
                    print("� Saving regions...")
                    self.save_comprehensive_regions(temp_regions)
                    print("✅ All regions saved!")
                    break
                else:
                    print("⚠️ No regions defined yet!")
            elif key == ord(' '):  # Space to skip to next group
                group_names = list(region_groups.keys())
                current_group_index = group_names.index(current_group)
                if current_group_index < len(group_names) - 1:
                    current_group = group_names[current_group_index + 1]
                    current_region_in_group = 0
                    next_region()
            elif key == ord('r'):  # Reset current group template
                region_groups[current_group]['template'] = None
                current_region_in_group = 0
                print(f"� Reset template for {region_groups[current_group]['description']}")
                next_region()
            elif key == ord('c'):  # Clear all regions
                temp_regions.clear()
                for group_data in region_groups.values():
                    group_data['template'] = None
                current_group = list(region_groups.keys())[0]
                current_region_in_group = 0
                print("🗑️ Cleared all regions and templates")
                next_region()
        
        cv2.destroyWindow(window_name)
    
    def save_comprehensive_regions(self, regions):
        """Save all regions to appropriate files (cards, names, stacks)."""
        try:
            # Separate regions by type
            card_regions = {}
            stack_regions = {}
            name_regions = {}
            
            for name, coords in regions.items():
                start_x, start_y = coords[0]
                end_x, end_y = coords[1]
                
                x = min(start_x, end_x)
                y = min(start_y, end_y)
                w = abs(end_x - start_x)
                h = abs(end_y - start_y)
                region_data = [x, y, w, h]
                
                if 'card' in name or 'pot' in name:
                    card_regions[name] = region_data
                elif 'stack' in name:
                    stack_regions[name] = region_data
                elif 'name' in name:
                    name_regions[name] = region_data
            
            # Save card regions to corrected_regions.json
            if card_regions:
                card_save_data = {
                    'regions': card_regions,
                    'metadata': {
                        'adjusted': True,
                        'timestamp': time.time(),
                        'source': 'comprehensive_adjustment',
                        'total_regions': len(card_regions)
                    }
                }
                
                with open('corrected_regions.json', 'w') as f:
                    json.dump(card_save_data, f, indent=2)
                print(f"✅ Saved {len(card_regions)} card/pot regions to corrected_regions.json")
            
            # Save stack and name regions to stack_regions.json
            if stack_regions or name_regions:
                stack_save_data = {
                    'stack_regions': stack_regions,
                    'name_regions': name_regions,
                    'metadata': {
                        'description': 'Player name and stack regions for 9-max SNG',
                        'resolution': '1920x1080',
                        'poker_site': 'calibrated',
                        'calibrated_positions': len(stack_regions) + len(name_regions),
                        'created': datetime.now().isoformat(),
                        'source': 'comprehensive_adjustment'
                    }
                }
                
                with open('stack_regions.json', 'w') as f:
                    json.dump(stack_save_data, f, indent=2)
                print(f"✅ Saved {len(stack_regions)} stack regions and {len(name_regions)} name regions to stack_regions.json")
            
            # Reload regions in poker bot
            if hasattr(self.poker_bot, 'load_regions'):
                self.poker_bot.load_regions()
                print("🔄 Reloaded regions in poker bot")
            
            total_saved = len(card_regions) + len(stack_regions) + len(name_regions)
            print(f"🎯 Total regions saved: {total_saved}")
            
        except Exception as e:
            print(f"❌ Error saving comprehensive regions: {e}")
    
    def normalize_card_notation(self, card_input):
        """Convert various card notations to standard format with suit symbols."""
        if not card_input or not card_input.strip():
            return None
            
        card = card_input.strip().upper()
        
        # Mapping for suit conversions
        suit_map = {
            'S': '♠', 'SPADES': '♠', 'SPADE': '♠',
            'H': '♥', 'HEARTS': '♥', 'HEART': '♥', 
            'D': '♦', 'DIAMONDS': '♦', 'DIAMOND': '♦',
            'C': '♣', 'CLUBS': '♣', 'CLUB': '♣'
        }
        
        # If already has suit symbols, return as-is
        if any(suit in card for suit in ['♠', '♥', '♦', '♣']):
            return card
            
        # Handle formats like "Ks", "AH", "10d", etc.
        if len(card) >= 2:
            rank = card[:-1]  # All but last character
            suit_char = card[-1]   # Last character
            
            # Convert rank
            if rank == '1' and len(card) > 2:  # Handle "10"
                rank = '10'
                suit_char = card[-1]
            elif rank in ['J', 'Q', 'K', 'A']:
                pass  # Keep as-is
            elif rank.isdigit() and 2 <= int(rank) <= 9:
                pass  # Keep as-is
            else:
                print(f"⚠️ Invalid rank: {rank}")
                return None
            
            # Convert suit
            if suit_char in suit_map:
                return f"{rank}{suit_map[suit_char]}"
            else:
                print(f"⚠️ Invalid suit: {suit_char}. Use S/H/D/C or symbols ♠♥♦♣")
                return None
        
        print(f"⚠️ Invalid card format: {card}. Use format like 'Ks', 'AH', '10d', etc.")
        return None

    def save_regions_to_file(self, regions):
        """Save regions to corrected_regions.json"""
        try:
            save_data = {
                'regions': {},
                'metadata': {
                    'adjusted': True,
                    'timestamp': time.time(),
                    'source': 'manual_adjustment'
                }
            }
            
            # Convert region format: (start_point, end_point) -> [x, y, w, h]
            for name, coords in regions.items():
                start_x, start_y = coords[0]
                end_x, end_y = coords[1]
                
                x = min(start_x, end_x)
                y = min(start_y, end_y)
                w = abs(end_x - start_x)
                h = abs(end_y - start_y)
                
                save_data['regions'][name] = [x, y, w, h]
            
            # Save to corrected_regions.json
            with open('corrected_regions.json', 'w') as f:
                json.dump(save_data, f, indent=4)
            
            # Reload regions in bot
            self.bot.load_regions()
            
            print(f"✅ Saved {len(regions)} regions to corrected_regions.json")
            
        except Exception as e:
            print(f"❌ Error saving regions: {e}")

    def take_screenshot(self):
        """Take and save a screenshot."""
        frame = self.capture_frame()
        if frame is None:
            self.status_label.config(text="❌ Failed to capture screenshot", fg='#ff4444')
            return
        
        filename = f"poker_screenshot_{int(time.time())}.png"
        cv2.imwrite(filename, frame)
        
        # Also save with regions overlay
        overlay = self.draw_regions_on_frame(frame)
        overlay_filename = f"poker_screenshot_regions_{int(time.time())}.png"
        cv2.imwrite(overlay_filename, overlay)
        
        self.status_label.config(text=f"📸 Screenshots saved: {filename}", fg='#00ff88')
        self.results_text.insert(tk.END, f"📸 Screenshot saved: {filename}\n")
        self.results_text.insert(tk.END, f"📸 With regions: {overlay_filename}\n\n")
        self.results_text.see(tk.END)
    
    def show_debug_overlay(self):
        """Show debug overlay with regions."""
        frame = self.capture_frame()
        if frame is None:
            self.status_label.config(text="❌ No frame for debug overlay", fg='#ff4444')
            return
        
        overlay_frame = self.draw_regions_on_frame(frame)
        
        # Resize for display
        height, width = overlay_frame.shape[:2]
        if width > 1200:
            scale = 1200 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            overlay_frame = cv2.resize(overlay_frame, (new_width, new_height))
        
        cv2.imshow('Region Debug Overlay (Press Q to close)', overlay_frame)
        self.status_label.config(text="🔍 Debug overlay open - Press Q to close", fg='#ffdd33')
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty('Region Debug Overlay (Press Q to close)', cv2.WND_PROP_VISIBLE) < 1:
                break
        
        cv2.destroyAllWindows()
        self.status_label.config(text="✅ Debug overlay closed", fg='#00ff88')
    
    def draw_regions_on_frame(self, frame):
        """Draw regions on frame for visualization."""
        overlay = frame.copy()
        
        if not hasattr(self.bot, 'current_regions'):
            return overlay
        
        colors = {
            'hero': (0, 255, 0),       # Green
            'community': (255, 0, 0),  # Blue
            'pot': (0, 255, 255),      # Yellow
        }
        
        for region_name, coords in self.bot.current_regions.items():
            try:
                # Handle different coordinate formats
                if isinstance(coords, dict):
                    if 'region' in coords:
                        x1, y1, x2, y2 = coords['region']
                    elif all(k in coords for k in ['x', 'y', 'width', 'height']):
                        x, y, w, h = coords['x'], coords['y'], coords['width'], coords['height']
                        x1, y1, x2, y2 = x, y, x+w, y+h
                    else:
                        continue  # Skip invalid format
                elif isinstance(coords, (list, tuple)) and len(coords) >= 4:
                    x, y, w, h = coords[:4]
                    x1, y1, x2, y2 = x, y, x+w, y+h
                else:
                    print(f"⚠️ Skipping invalid region format for {region_name}: {coords}")
                    continue
                
                # Get color
                color = (255, 255, 255)
                for key, col in colors.items():
                    if key in region_name.lower():
                        color = col
                        break
                
                # Draw rectangle and label
                cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
                label = region_name.replace('_', ' ').title()
                cv2.putText(overlay, label, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                           
            except Exception as e:
                print(f"⚠️ Error drawing region {region_name}: {e}")
                continue
        
        return overlay
    
    # === OLD REGION ADJUSTMENT METHODS REMOVED ===
    # The following methods have been replaced with the new GUI-based system:
    # - open_region_adjustment() - old version with input() that caused freezing
    # - save_regions() - old version with different format
    # 
    # Use open_region_adjustment_gui() and save_regions_to_file() instead
    # These new methods don't block the GUI thread and provide better user experience

    def run(self):
        """Run the bot."""
        # Find camera
        self.camera_index = self.find_obs_camera()
        if self.camera_index is None:
            print("❌ No virtual camera found")
            print("💡 Make sure OBS Virtual Camera is running")
            print("⚠️ Falling back to screenshot mode only")
        
        # Initialize bot
        self.bot = SmartPokerBot()
        
        # Create and run GUI
        self.create_gui()
        
        # Add cleanup handler for GUI close (no camera to release in new approach)
        def on_closing():
            # Stop auto-scanning if running
            if self.auto_scan_enabled and self.auto_scan_job:
                self.root.after_cancel(self.auto_scan_job)
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

def main():
    """Main entry point."""
    print("🚀 Smart Poker Bot - Virtual Camera OCR")
    print("="*60)
    print("NO LIVE FEED - Only on-demand capture and analysis")
    print("="*60)
    
    # Configure Tesseract if available
    try:
        import pytesseract
        paths = [
            os.path.join(os.getcwd(), "Tesseract", "tesseract.exe"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ Tesseract found: {path}")
                break
    except Exception:
        print("⚠️ Tesseract not configured")
    
    bot = VirtualCameraOCRBot()
    
    try:
        if '--debug' in sys.argv:
            # Debug mode - command line only
            bot.camera_index = bot.find_obs_camera()
            
            if bot.camera_index is None:
                print("❌ Debug mode requires virtual camera")
                return
                
            bot.bot = SmartPokerBot()
            
            print("\n📋 Debug Commands:")
            print("  a - Analyze current frame")
            print("  s - Take screenshot")
            print("  r - Show regions overlay")
            print("  q - Quit")
            
            while True:
                cmd = input("\nCommand: ").strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == 'a':
                    frame = bot.capture_frame()
                    if frame is not None:
                        results = bot.bot.analyze_frame_ocr(frame)
                        print("\n📊 Results:")
                        for key, value in results.items():
                            if value:
                                print(f"  {key}: {value}")
                elif cmd == 's':
                    frame = bot.capture_frame()
                    if frame is not None:
                        filename = f"debug_screenshot_{int(time.time())}.png"
                        cv2.imwrite(filename, frame)
                        print(f"📸 Saved: {filename}")
                elif cmd == 'r':
                    bot.show_debug_overlay()
        else:
            # Normal GUI mode
            bot.run()
    finally:
        # No camera cleanup needed in create-and-release approach
        print("🔧 Cleanup complete")

if __name__ == "__main__":
    main()
