"""
Game Information Panel Component
Displays game state, cards, players, and activity log.
"""

import tkinter as tk
from tkinter import scrolledtext


class GameInfoPanel(tk.Frame):
    """Panel for displaying game information and logs."""
    
    def __init__(self, parent):
        """Initialize the game info panel."""
        super().__init__(parent, bg='#2b2b2b')
        
        # Create components
        self.create_game_info_section()
        self.create_cards_section()
        self.create_players_section()
        self.create_log_section()
    
    def create_game_info_section(self):
        """Create the game information section."""
        game_info_frame = tk.Frame(self, bg='#2b2b2b')
        game_info_frame.pack(fill="x", padx=10, pady=10)
        
        info_title = tk.Label(
            game_info_frame, 
            text="🎮 Game Information", 
            font=("Arial", 14, "bold"),
            bg='#2b2b2b', fg='white'
        )
        info_title.pack(pady=10)
        
        # Window info
        self.window_info = tk.Label(
            game_info_frame, 
            text="Window: Not connected", 
            font=("Arial", 12),
            bg='#2b2b2b', fg='lightgray'
        )
        self.window_info.pack(pady=5)
        
        # Game stats grid
        stats_frame = tk.Frame(game_info_frame, bg='#2b2b2b')
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        # Create info cards in a 2x2 grid
        self.create_info_card(stats_frame, "Stakes", "N/A", 0, 0)
        self.create_info_card(stats_frame, "Pot Size", "0 BB", 0, 1)
        self.create_info_card(stats_frame, "Hero Stack", "0 BB", 1, 0)
        self.create_info_card(stats_frame, "Position", "N/A", 1, 1)
    
    def create_info_card(self, parent, title, value, row, col):
        """Create an information card widget."""
        # Color mapping for different card types
        colors = {
            'Stakes': '#2196F3',      # Blue
            'Pot Size': '#4CAF50',    # Green  
            'Hero Stack': '#FF9800',  # Orange
            'Position': '#9C27B0'     # Purple
        }
        
        card_frame = tk.Frame(parent, bg=colors.get(title, '#2b2b2b'))
        card_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)
        
        title_label = tk.Label(card_frame, text=title, font=("Arial", 10, "bold"),
                              bg=colors.get(title, '#2b2b2b'), fg='white')
        title_label.pack(pady=(5, 0))
        
        value_label = tk.Label(card_frame, text=value, font=("Arial", 12, "bold"),
                              bg=colors.get(title, '#2b2b2b'), fg='white')
        value_label.pack(pady=(0, 5))
        
        # Store reference for updates
        setattr(self, f"{title.lower().replace(' ', '_')}_value", value_label)
    
    def create_cards_section(self):
        """Create the cards section."""
        cards_frame = tk.Frame(self, bg='#2b2b2b')
        cards_frame.pack(fill="x", padx=10, pady=10)
        
        cards_title = tk.Label(
            cards_frame, 
            text="🃏 Cards", 
            font=("Arial", 14, "bold"),
            bg='#2b2b2b', fg='white'
        )
        cards_title.pack(pady=10)
        
        # Hero cards
        hero_frame = tk.Frame(cards_frame, bg='#2b2b2b')
        hero_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(hero_frame, text="Hero Cards:", font=("Arial", 12, "bold"),
                bg='#2b2b2b', fg='white').pack()
        self.hero_cards_display = tk.Label(hero_frame, text="? ?", font=("Arial", 14),
                                          bg='#2b2b2b', fg='lightgray')
        self.hero_cards_display.pack(pady=5)
        
        # Community cards
        community_frame = tk.Frame(cards_frame, bg='#2b2b2b')
        community_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(community_frame, text="Community:", font=("Arial", 12, "bold"),
                bg='#2b2b2b', fg='white').pack()
        self.community_cards_display = tk.Label(community_frame, text="? ? ? ? ?", font=("Arial", 14),
                                               bg='#2b2b2b', fg='lightgray')
        self.community_cards_display.pack(pady=5)
    
    def create_players_section(self):
        """Create the players section."""
        players_frame = tk.Frame(self, bg='#2b2b2b')
        players_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        players_title = tk.Label(
            players_frame, 
            text="👥 Players", 
            font=("Arial", 14, "bold"),
            bg='#2b2b2b', fg='white'
        )
        players_title.pack(pady=10)
        
        # Scrollable players list
        players_scroll_frame = tk.Frame(players_frame, bg='#2b2b2b')
        players_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable area
        canvas = tk.Canvas(players_scroll_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = tk.Scrollbar(players_scroll_frame, orient="vertical", command=canvas.yview)
        self.players_scrollable = tk.Frame(canvas, bg='#2b2b2b')
        
        self.players_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.players_scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initialize empty player list
        self.player_labels = []
        for i in range(9):
            player_label = tk.Label(
                self.players_scrollable, 
                text=f"Seat {i+1}: Empty", 
                font=("Arial", 11),
                bg='#2b2b2b', fg='lightgray'
            )
            player_label.pack(pady=2, anchor="w")
            self.player_labels.append(player_label)
    
    def create_log_section(self):
        """Create the activity log section."""
        log_frame = tk.Frame(self, bg='#2b2b2b')
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        log_title = tk.Label(
            log_frame, 
            text="📝 Activity Log", 
            font=("Arial", 14, "bold"),
            bg='#2b2b2b', fg='white'
        )
        log_title.pack(pady=10)
        
        # Log text area
        self.log_text = tk.Text(log_frame, height=8, bg='#1e1e1e', fg='white',
                               font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Live Recognition Status section
        self.create_live_recognition_section()
    
    def create_live_recognition_section(self):
        """Create live recognition status section"""
        live_frame = tk.Frame(self, bg='#2b2b2b')
        live_frame.pack(fill="x", padx=10, pady=10)
        
        live_title = tk.Label(
            live_frame, 
            text="🎯 Live Recognition Status", 
            font=("Arial", 14, "bold"),
            bg='#2b2b2b', fg='white'
        )
        live_title.pack(pady=10)
        
        # Recognition method display
        self.recognition_method_label = tk.Label(
            live_frame,
            text="Recognition Method: Not Connected",
            font=("Arial", 10),
            bg='#2b2b2b', fg='lightgray'
        )
        self.recognition_method_label.pack(pady=2)
        
        # Processing performance
        self.processing_performance_label = tk.Label(
            live_frame,
            text="Processing: No data",
            font=("Arial", 10),
            bg='#2b2b2b', fg='lightgray'
        )
        self.processing_performance_label.pack(pady=2)
        
        # Last recognition results in a compact format
        recognition_results_frame = tk.Frame(live_frame, bg='#444444')
        recognition_results_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(recognition_results_frame, text="Last Recognition:", 
                font=("Arial", 10, "bold"), bg='#444444', fg='white').pack(side="left", padx=5)
        
        self.last_recognition_label = tk.Label(
            recognition_results_frame,
            text="No recent recognition",
            font=("Arial", 9),
            bg='#444444', fg='lightgreen'
        )
        self.last_recognition_label.pack(side="left", padx=5)
    
    def update_live_recognition_status(self, recognition_data):
        """Update the live recognition status display"""
        try:
            if not recognition_data:
                return
            
            # Update recognition method
            method = recognition_data.get('recognition_method', 'Unknown')
            self.recognition_method_label.configure(text=f"Recognition Method: {method}")
            
            # Update processing performance
            processing_time = recognition_data.get('processing_time', 0)
            confidence = recognition_data.get('analysis_confidence', 0)
            performance_text = f"Processing: {processing_time*1000:.1f}ms | Confidence: {confidence:.3f}"
            self.processing_performance_label.configure(text=performance_text)
            
            # Update last recognition summary
            hero_cards = recognition_data.get('hero_cards', [])
            community_cards = recognition_data.get('community_cards', [])
            
            if hero_cards or community_cards:
                hero_summary = f"{len(hero_cards)} hero" if hero_cards else "0 hero"
                community_summary = f"{len(community_cards)} community" if community_cards else "0 community"
                last_recognition_text = f"{hero_summary}, {community_summary} cards detected"
                
                # Add individual card details if available
                if len(hero_cards) > 0:
                    hero_cards_text = ", ".join([card.get('card', '?') for card in hero_cards[:2]])
                    last_recognition_text += f" | Hero: {hero_cards_text}"
                
                if len(community_cards) > 0:
                    community_cards_text = ", ".join([card.get('card', '?') for card in community_cards[:5]])
                    last_recognition_text += f" | Community: {community_cards_text}"
                
                self.last_recognition_label.configure(text=last_recognition_text, fg='lightgreen')
            else:
                self.last_recognition_label.configure(text="No cards detected in last recognition", fg='orange')
                
        except Exception as e:
            self.last_recognition_label.configure(text=f"Recognition status error: {e}", fg='red')
    
    def set_window_info(self, info):
        """Update window information."""
        self.window_info.configure(text=info)
    
    def add_log_message(self, message):
        """Add a message to the log with error handling."""
        try:
            # Check if the widget still exists
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                # Add timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("[%H:%M:%S] ")
                
                # Insert message with timestamp
                self.log_text.insert("end", timestamp + str(message) + "\n")
                self.log_text.see("end")
            else:
                # Widget doesn't exist, just print to console
                print(f"LOG: {message}")
        except Exception as e:
            # Widget might have been destroyed, ignore the error
            print(f"LOG (fallback): {message}")
    
    def update_game_info(self, analysis):
        """Update game information display."""
        try:
            if not analysis:
                # Clear displays when no analysis available
                self.hero_cards_display.configure(text="? ?", fg='lightgray')
                self.community_cards_display.configure(text="? ? ? ? ?", fg='lightgray')
                for i in range(9):
                    if i < len(self.player_labels):
                        self.player_labels[i].configure(text=f"Seat {i+1}: Empty", fg='lightgray')
                return
            
            # Log analysis for debugging
            analysis_keys = list(analysis.keys()) if isinstance(analysis, dict) else []
            self.add_log_message(f"Updating UI with analysis keys: {analysis_keys}\n")
            
            # Update stakes
            if 'table_info' in analysis and analysis['table_info']:
                table_info = analysis['table_info']
                stakes = getattr(table_info, 'table_stakes', 'N/A')
                if hasattr(self, 'stakes_value'):
                    self.stakes_value.configure(text=stakes)
                    self.add_log_message(f"Updated stakes: {stakes}\n")
                
                # Update pot
                pot_size = getattr(table_info, 'pot_size', 0)
                if hasattr(self, 'pot_size_value'):
                    self.pot_size_value.configure(text=f"{pot_size:.1f} BB")
                    self.add_log_message(f"Updated pot: {pot_size:.1f} BB\n")
                
                # Find hero and update info
                hero = None
                for player in getattr(table_info, 'players', []):
                    if getattr(player, 'is_hero', False):
                        hero = player
                        break
                
                if hero:
                    stack = getattr(hero, 'stack_size', 0)
                    position = getattr(hero, 'position', 'N/A')
                    if hasattr(self, 'hero_stack_value'):
                        self.hero_stack_value.configure(text=f"{stack:.1f} BB")
                    if hasattr(self, 'position_value'):
                        self.position_value.configure(text=position)
                    self.add_log_message(f"Updated hero: {stack:.1f} BB at {position}\n")
                
                # Update player list
                players = getattr(table_info, 'players', [])
                self.add_log_message(f"Updating {len(players)} players\n")
                for i in range(9):
                    if i < len(players):
                        player = players[i]
                        name = getattr(player, 'name', f'Player{i+1}')
                        stack = getattr(player, 'stack_size', 0)
                        is_hero = getattr(player, 'is_hero', False)
                        hero_marker = " (HERO)" if is_hero else ""
                        text = f"Seat {i+1}: {name} - {stack:.1f}BB{hero_marker}"
                        color = 'white' if stack > 0 else 'lightgray'
                    else:
                        text = f"Seat {i+1}: Empty"
                        color = 'lightgray'
                    
                    if i < len(self.player_labels):
                        self.player_labels[i].configure(text=text, fg=color)
            else:
                self.add_log_message("No table_info in analysis\n")
            
            # Update cards
            if 'hole_cards' in analysis and analysis['hole_cards']:
                hole_cards = analysis['hole_cards']
                if hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                    card_text = f"{hole_cards.card1} {hole_cards.card2}"
                    self.hero_cards_display.configure(text=card_text, fg='white')
                    self.add_log_message(f"Updated hole cards: {card_text}\n")
                else:
                    self.hero_cards_display.configure(text="? ?", fg='lightgray')
                    self.add_log_message("Hole cards not valid\n")
            else:
                self.hero_cards_display.configure(text="? ?", fg='lightgray')
                self.add_log_message("No hole_cards in analysis\n")
            
            if 'community_cards' in analysis and analysis['community_cards']:
                community = analysis['community_cards']
                if hasattr(community, 'get_visible_cards'):
                    cards = community.get_visible_cards()
                    if cards:
                        card_text = " ".join([str(card) for card in cards])
                        self.community_cards_display.configure(text=card_text, fg='white')
                        self.add_log_message(f"Updated community cards: {card_text}\n")
                    else:
                        self.community_cards_display.configure(text="? ? ? ? ?", fg='lightgray')
                        self.add_log_message("No community cards visible\n")
                else:
                    self.community_cards_display.configure(text="? ? ? ? ?", fg='lightgray')
                    self.add_log_message("Community cards object invalid\n")
            else:
                self.community_cards_display.configure(text="? ? ? ? ?", fg='lightgray')
                self.add_log_message("No community_cards in analysis\n")
            
        except Exception as e:
            self.add_log_message(f"Error updating community cards: {e}\n")