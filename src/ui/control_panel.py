"""
Control Panel Component
Handles bot controls, capture mode selection, and OBS integration.
"""

import tkinter as tk
from tkinter import ttk


class ControlPanel:
    """Control panel for bot operations and settings."""
    
    def __init__(self, parent, main_window):
        """Initialize the control panel."""
        self.parent = parent
        self.main_window = main_window
        
        # Create components
        self.create_capture_mode_selection()
        self.create_main_controls()
    
    def create_capture_mode_selection(self):
        """Create capture mode selection UI."""
        mode_frame = tk.Frame(self.parent, bg='#2b2b2b')
        mode_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(mode_frame, text="Capture Mode:", font=("Arial", 14, "bold"), 
                bg='#2b2b2b', fg='white').pack(side="left", padx=5)
        
        # Mode selection
        self.mode_var = tk.StringVar(value="window")
        
        window_radio = tk.Radiobutton(
            mode_frame, text="Window Capture", variable=self.mode_var, 
            value="window", command=self.on_mode_change,
            bg='#2b2b2b', fg='white', selectcolor='#2b2b2b'
        )
        window_radio.pack(side="left", padx=10)
        
        obs_radio = tk.Radiobutton(
            mode_frame, text="OBS Virtual Camera", variable=self.mode_var, 
            value="obs", command=self.on_mode_change,
            bg='#2b2b2b', fg='white', selectcolor='#2b2b2b'
        )
        obs_radio.pack(side="left", padx=10)
        
        # OBS specific controls
        self.obs_controls = tk.Frame(mode_frame, bg='#2b2b2b')
        self.obs_controls.pack(side="right", padx=5)
        
        self.obs_connect_btn = tk.Button(
            self.obs_controls, text="Connect OBS", width=12,
            command=self.main_window.connect_obs_camera,
            bg='#9C27B0', fg='white', font=("Arial", 9, "bold")
        )
        self.obs_connect_btn.pack(side="left", padx=2)
        
        # Manual capture button for hardware capture
        self.manual_capture_btn = tk.Button(
            self.obs_controls, text="📸 Manual Capture", width=15,
            command=self.main_window.manual_capture,
            bg='#4CAF50', fg='white', font=("Arial", 9, "bold"),
            state="disabled"
        )
        self.manual_capture_btn.pack(side="left", padx=2)
        
        self.obs_status = tk.Label(self.obs_controls, text="Not Connected",
                                  bg='#2b2b2b', fg='lightgray')
        self.obs_status.pack(side="left", padx=5)
        
        # Initially hide OBS controls
        self.obs_controls.pack_forget()
    
    def create_main_controls(self):
        """Create main control buttons."""
        button_frame = tk.Frame(self.parent, bg='#2b2b2b')
        button_frame.pack(fill="x", padx=5, pady=5)
        
        self.find_button = tk.Button(
            button_frame, text="🔍 Find Table", 
            command=self.main_window.find_table, width=15,
            bg='#4CAF50', fg='white', font=("Arial", 10, "bold")
        )
        self.find_button.pack(side="left", padx=5)
        
        # Start/Stop controls
        self.start_button = ttk.Button(button_frame, text="🚀 Start Analysis", command=self.toggle_bot, style="Accent.TButton")
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(
            button_frame, text="⏹ Stop Analysis", 
            command=self.main_window.stop_bot, width=15, state="disabled",
            bg='#f44336', fg='white', font=("Arial", 10, "bold")
        )
        self.stop_button.pack(side="left", padx=5)
        
        self.test_button = tk.Button(
            button_frame, text="🧪 Test", 
            command=self.main_window.test_capture, width=12,
            bg='#FF9800', fg='white', font=("Arial", 10, "bold")
        )
        self.test_button.pack(side="left", padx=5)
        
        # Add a Refresh Regions button
        self.refresh_regions_button = tk.Button(
            button_frame, text="🔄 Refresh Regions", 
            command=self.main_window.refresh_regions, width=15,
            bg='#9C27B0', fg='white', font=("Arial", 10, "bold")
        )
        self.refresh_regions_button.pack(side="left", padx=5)
    
    def toggle_bot(self):
        """Toggle bot start/stop."""
        # Delegate to main window
        if hasattr(self.main_window, 'start_bot'):
            self.main_window.start_bot()
        else:
            print("Start bot functionality not implemented")
    
    def on_mode_change(self):
        """Handle capture mode change."""
        mode = self.mode_var.get()
        self.main_window.set_capture_mode(mode)
        
        if mode == "obs":
            self.obs_controls.pack(side="right", padx=5)
        else:
            self.obs_controls.pack_forget()
    
    def set_bot_running(self, running):
        """Update button states based on bot running status."""
        if running:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
        else:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
    
    def set_obs_connected(self, connected):
        """Update OBS connection status."""
        if connected:
            self.obs_status.configure(text="Connected", fg="green")
            self.obs_connect_btn.configure(text="Disconnect", bg='#f44336')
            if hasattr(self, 'manual_capture_btn'):
                self.manual_capture_btn.configure(state="normal")
        else:
            self.obs_status.configure(text="Not Connected", fg="lightgray")
            self.obs_connect_btn.configure(text="Connect OBS", bg='#9C27B0')
            if hasattr(self, 'manual_capture_btn'):
                self.manual_capture_btn.configure(state="disabled")
    
    def set_obs_status(self, status):
        """Set OBS status text."""
        self.obs_status.configure(text=status)
    
    def on_mode_change(self):
        """Handle capture mode change."""
        mode = self.mode_var.get()
        if mode == "obs":
            self.obs_controls.pack(side="right", padx=5)
            self.main_window.set_capture_mode("obs")
        else:
            self.obs_controls.pack_forget()
            self.main_window.set_capture_mode("window")
    
    def toggle_bot(self):
        """Toggle bot start/stop."""
        if not self.main_window.running:
            self.main_window.start_bot()
        else:
            self.main_window.stop_bot()
    
    def update_button_states(self, running):
        """Update button states based on bot running state."""
        if running:
            self.start_button.configure(text="⏸ Pause Analysis")
            self.stop_button.configure(state="normal")
        else:
            self.start_button.configure(text="🚀 Start Analysis")
            self.stop_button.configure(state="disabled")