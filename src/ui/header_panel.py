"""
Header Panel Component
Displays title, subtitle, and connection status.
"""

import tkinter as tk


class HeaderPanel(tk.Frame):
    """Header panel with title and status information."""
    
    def __init__(self, parent):
        """Initialize the header panel."""
        super().__init__(parent, bg='#2b2b2b')
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Create components
        self.create_title_section()
        self.create_status_section()
    
    def create_title_section(self):
        """Create the title section."""
        title_frame = tk.Frame(self, bg='#2b2b2b')
        title_frame.grid(row=0, column=0, sticky="w", padx=5, pady=2)  # Minimal padding
        
        title_label = tk.Label(
            title_frame, 
            text="🎰 PokerStars Bot Professional", 
            font=("Arial", 14, "bold"),  # Even smaller to maximize table space
            bg='#2b2b2b', fg='white'
        )
        title_label.pack(side="left", padx=10)
        
        subtitle_label = tk.Label(
            title_frame, 
            text="Advanced AI Poker Analysis & Automation", 
            font=("Arial", 8),  # Tiny subtitle to save space
            bg='#2b2b2b', fg='lightgray'
        )
        subtitle_label.pack(side="left", padx=10)
    
    def create_status_section(self):
        """Create the status section."""
        status_frame = tk.Frame(self, bg='#2b2b2b')
        status_frame.grid(row=0, column=1, sticky="e", padx=5, pady=2)  # Minimal padding
        
        self.connection_status = tk.Label(
            status_frame, 
            text="● Disconnected", 
            font=("Arial", 12, "bold"),
            fg="red", bg='#2b2b2b'
        )
        self.connection_status.pack(pady=2)
        
        self.bot_status = tk.Label(
            status_frame, 
            text="Bot: Stopped", 
            font=("Arial", 10),
            fg="orange", bg='#2b2b2b'
        )
        self.bot_status.pack()
    
    def set_connection_status(self, status, color):
        """Update connection status."""
        self.connection_status.configure(text=f"● {status}", fg=color)
    
    def set_bot_status(self, status, color):
        """Update bot status."""
        self.bot_status.configure(text=f"Bot: {status}", fg=color)