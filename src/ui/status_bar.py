"""
Status Bar Component
Displays status information and statistics at the bottom of the window.
"""

import tkinter as tk


class StatusBar(tk.Frame):
    """Status bar for displaying application status and statistics."""
    
    def __init__(self, parent):
        """Initialize the status bar."""
        super().__init__(parent, bg='#2b2b2b')
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Create status variables
        self.status_var = tk.StringVar(value="Ready")
        self.captures_var = tk.StringVar(value="Captures: 0")
        self.success_var = tk.StringVar(value="Success: 0%")
        
        # Create components
        self.create_status_labels()
    
    def create_status_labels(self):
        """Create status labels."""
        # Status label
        self.status_label = tk.Label(self, textvariable=self.status_var,
                                    bg='#2b2b2b', fg='white')
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Captures label
        self.captures_label = tk.Label(self, textvariable=self.captures_var,
                                      bg='#2b2b2b', fg='white')
        self.captures_label.grid(row=0, column=1, padx=10, pady=5)
        
        # Success rate label
        self.success_label = tk.Label(self, textvariable=self.success_var,
                                     bg='#2b2b2b', fg='white')
        self.success_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
    
    def update_status(self, status):
        """Update the main status."""
        self.status_var.set(status)
    
    def update_statistics(self, capture_count, success_count):
        """Update capture statistics."""
        self.captures_var.set(f"Captures: {capture_count}")
        
        success_rate = (success_count / capture_count * 100) if capture_count > 0 else 0
        self.success_var.set(f"Success: {success_rate:.1f}%")