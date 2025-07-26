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