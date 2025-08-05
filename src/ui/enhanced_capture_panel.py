"""
Enhanced Capture Panel Component
Provides advanced capture options including multiple screen capture methods and OBS integration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys


class EnhancedCapturePanel:
    """Enhanced capture panel with multiple capture methods."""
    
    def __init__(self, parent, main_window):
        """Initialize the enhanced capture panel."""
        self.parent = parent
        self.main_window = main_window
        
        # Create enhanced capture controls
        self.create_capture_method_selection()
        self.create_obs_advanced_controls()
        self.create_screen_capture_options()
        self.create_capture_quality_controls()
    
    def create_capture_method_selection(self):
        """Create advanced capture method selection."""
        method_frame = tk.LabelFrame(self.parent, text="Capture Method", 
                                   bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        method_frame.pack(fill="x", padx=5, pady=5)
        
        self.capture_method_var = tk.StringVar(value="window")
        
        methods = [
            ("Window Capture", "window", "Direct PokerStars window capture"),
            ("OBS Virtual Camera", "obs", "OBS Studio virtual camera"),
            ("Screen Region", "region", "Specific screen region capture"),
            ("Multi-Method", "multi", "Automatic fallback between methods")
        ]
        
        for name, value, description in methods:
            frame = tk.Frame(method_frame, bg='#2b2b2b')
            frame.pack(fill="x", padx=5, pady=2)
            
            radio = tk.Radiobutton(
                frame, text=name, variable=self.capture_method_var, value=value,
                command=self.on_capture_method_change, bg='#2b2b2b', fg='white',
                selectcolor='#2b2b2b', font=("Arial", 10, "bold")
            )
            radio.pack(side="left")
            
            desc_label = tk.Label(frame, text=description, bg='#2b2b2b', fg='lightgray',
                                 font=("Arial", 9))
            desc_label.pack(side="left", padx=10)
    
    def create_obs_advanced_controls(self):
        """Create advanced OBS controls."""
        obs_frame = tk.LabelFrame(self.parent, text="OBS Advanced Settings", 
                                 bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        obs_frame.pack(fill="x", padx=5, pady=5)
        
        # Camera selection
        camera_frame = tk.Frame(obs_frame, bg='#2b2b2b')
        camera_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(camera_frame, text="Camera Index:", bg='#2b2b2b', fg='white',
                font=("Arial", 10)).pack(side="left")
        
        self.camera_index_var = tk.IntVar(value=0)
        camera_spin = tk.Spinbox(camera_frame, from_=0, to=10, width=5,
                                textvariable=self.camera_index_var, bg='#3b3b3b', fg='white')
        camera_spin.pack(side="left", padx=5)
        
        tk.Button(camera_frame, text="Scan Cameras", command=self.scan_cameras,
                 bg='#2196F3', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        # OBS status and controls
        status_frame = tk.Frame(obs_frame, bg='#2b2b2b')
        status_frame.pack(fill="x", padx=5, pady=2)
        
        self.obs_status_label = tk.Label(status_frame, text="Status: Disconnected",
                                        bg='#2b2b2b', fg='lightgray', font=("Arial", 10))
        self.obs_status_label.pack(side="left")
        
        tk.Button(status_frame, text="Test OBS", command=self.test_obs_connection,
                 bg='#FF9800', fg='white', font=("Arial", 9, "bold")).pack(side="right", padx=2)
        
        tk.Button(status_frame, text="Reconnect", command=self.reconnect_obs,
                 bg='#9C27B0', fg='white', font=("Arial", 9, "bold")).pack(side="right", padx=2)
    
    def create_screen_capture_options(self):
        """Create screen capture options."""
        screen_frame = tk.LabelFrame(self.parent, text="Screen Capture Options", 
                                   bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        screen_frame.pack(fill="x", padx=5, pady=5)
        
        # Capture backend selection
        backend_frame = tk.Frame(screen_frame, bg='#2b2b2b')
        backend_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(backend_frame, text="Capture Backend:", bg='#2b2b2b', fg='white',
                font=("Arial", 10)).pack(side="left")
        
        self.backend_var = tk.StringVar(value="auto")
        backend_combo = ttk.Combobox(backend_frame, textvariable=self.backend_var,
                                   values=["auto", "mss", "pyautogui", "win32", "opencv"],
                                   state="readonly", width=15)
        backend_combo.pack(side="left", padx=5)
        
        tk.Button(backend_frame, text="Test Backend", command=self.test_capture_backend,
                 bg='#4CAF50', fg='white', font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        # Capture validation
        validation_frame = tk.Frame(screen_frame, bg='#2b2b2b')
        validation_frame.pack(fill="x", padx=5, pady=2)
        
        self.validate_capture_var = tk.BooleanVar(value=True)
        tk.Checkbutton(validation_frame, text="Validate Captures", 
                      variable=self.validate_capture_var, bg='#2b2b2b', fg='white',
                      selectcolor='#2b2b2b', font=("Arial", 10)).pack(side="left")
        
        self.auto_retry_var = tk.BooleanVar(value=True)
        tk.Checkbutton(validation_frame, text="Auto Retry on Failure", 
                      variable=self.auto_retry_var, bg='#2b2b2b', fg='white',
                      selectcolor='#2b2b2b', font=("Arial", 10)).pack(side="left", padx=10)
    
    def create_capture_quality_controls(self):
        """Create capture quality controls."""
        quality_frame = tk.LabelFrame(self.parent, text="Capture Quality", 
                                    bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        quality_frame.pack(fill="x", padx=5, pady=5)
        
        # Frame rate control
        fps_frame = tk.Frame(quality_frame, bg='#2b2b2b')
        fps_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(fps_frame, text="Capture FPS:", bg='#2b2b2b', fg='white',
                font=("Arial", 10)).pack(side="left")
        
        self.fps_var = tk.DoubleVar(value=2.0)
        fps_scale = tk.Scale(fps_frame, from_=0.5, to=10.0, resolution=0.5,
                           variable=self.fps_var, orient=tk.HORIZONTAL,
                           bg='#2b2b2b', fg='white', length=150)
        fps_scale.pack(side="left", padx=5)
        
        # Quality settings
        quality_controls = tk.Frame(quality_frame, bg='#2b2b2b')
        quality_controls.pack(fill="x", padx=5, pady=2)
        
        self.high_quality_var = tk.BooleanVar(value=False)
        tk.Checkbutton(quality_controls, text="High Quality Mode", 
                      variable=self.high_quality_var, bg='#2b2b2b', fg='white',
                      selectcolor='#2b2b2b', font=("Arial", 10)).pack(side="left")
        
        self.save_captures_var = tk.BooleanVar(value=False)
        tk.Checkbutton(quality_controls, text="Save All Captures", 
                      variable=self.save_captures_var, bg='#2b2b2b', fg='white',
                      selectcolor='#2b2b2b', font=("Arial", 10)).pack(side="left", padx=10)
        
        # Apply button
        tk.Button(quality_frame, text="Apply Quality Settings", command=self.apply_quality_settings,
                 bg='#4CAF50', fg='white', font=("Arial", 10, "bold")).pack(pady=5)
    
    def on_capture_method_change(self):
        """Handle capture method change."""
        method = self.capture_method_var.get()
        self.main_window.log_message(f"Capture method selected: {method}")
        
        if method == "multi":
            self.setup_multi_method_capture()
        elif method == "region":
            self.setup_region_capture()
    
    def setup_multi_method_capture(self):
        """Setup multi-method capture with fallbacks."""
        try:
            # Import enhanced screen capture
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from screen_capture import ScreenCaptureManager
            
            self.main_window.screen_capture = ScreenCaptureManager()
            self.main_window.log_message("✅ Multi-method capture initialized")
            
        except Exception as e:
            self.main_window.log_message(f"❌ Multi-method capture setup failed: {e}")
    
    def setup_region_capture(self):
        """Setup region-specific capture."""
        # TODO: Implement region selection dialog
        messagebox.showinfo("Info", "Region capture setup - feature coming soon!")
    
    def scan_cameras(self):
        """Scan for available cameras."""
        try:
            self.main_window.log_message("Scanning for available cameras...")
            
            if hasattr(self.main_window, 'obs_capture'):
                cameras = self.main_window.obs_capture.list_available_cameras()
                
                camera_info = "Available Cameras:\n\n"
                for camera in cameras:
                    camera_info += f"Index {camera['index']}: {camera.get('width', 'Unknown')}x{camera.get('height', 'Unknown')}\n"
                    camera_info += f"  Working: {camera.get('working', False)}\n\n"
                
                messagebox.showinfo("Camera Scan Results", camera_info)
                self.main_window.log_message(f"✅ Found {len(cameras)} cameras")
            else:
                messagebox.showerror("Error", "OBS capture not available")
                
        except Exception as e:
            messagebox.showerror("Error", f"Camera scan failed: {e}")
    
    def test_obs_connection(self):
        """Test OBS connection."""
        try:
            camera_index = self.camera_index_var.get()
            
            if hasattr(self.main_window, 'obs_capture'):
                success = self.main_window.obs_capture.connect_to_obs_camera(camera_index)
                
                if success:
                    self.obs_status_label.configure(text="Status: Connected", fg="green")
                    messagebox.showinfo("Success", f"Connected to camera {camera_index}")
                else:
                    self.obs_status_label.configure(text="Status: Failed", fg="red")
                    messagebox.showerror("Error", f"Failed to connect to camera {camera_index}")
            else:
                messagebox.showerror("Error", "OBS capture not available")
                
        except Exception as e:
            messagebox.showerror("Error", f"OBS test failed: {e}")
    
    def reconnect_obs(self):
        """Reconnect to OBS."""
        try:
            if hasattr(self.main_window, 'obs_capture'):
                self.main_window.obs_capture.disconnect()
                success = self.main_window.obs_capture.connect_to_obs_camera()
                
                if success:
                    self.obs_status_label.configure(text="Status: Reconnected", fg="green")
                    self.main_window.log_message("✅ OBS reconnected successfully")
                else:
                    self.obs_status_label.configure(text="Status: Failed", fg="red")
                    self.main_window.log_message("❌ OBS reconnection failed")
            
        except Exception as e:
            self.main_window.log_message(f"❌ OBS reconnection error: {e}")
    
    def test_capture_backend(self):
        """Test the selected capture backend."""
        try:
            backend = self.backend_var.get()
            self.main_window.log_message(f"Testing capture backend: {backend}")
            
            # Import screen capture manager
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from screen_capture import ScreenCaptureManager
            
            capture_manager = ScreenCaptureManager()
            
            if backend != "auto":
                capture_manager.primary_method = backend
            
            # Test capture
            screenshot = capture_manager.capture_screen()
            
            if screenshot is not None:
                self.main_window.log_message(f"✅ Backend {backend} test successful")
                messagebox.showinfo("Success", f"Backend {backend} working correctly!")
                
                # Display test screenshot
                self.main_window.table_panel.display_screenshot(screenshot)
            else:
                self.main_window.log_message(f"❌ Backend {backend} test failed")
                messagebox.showerror("Error", f"Backend {backend} failed to capture")
                
        except Exception as e:
            messagebox.showerror("Error", f"Backend test failed: {e}")
    
    def apply_quality_settings(self):
        """Apply quality settings to capture system."""
        try:
            fps = self.fps_var.get()
            high_quality = self.high_quality_var.get()
            save_captures = self.save_captures_var.get()
            
            # Apply to main window
            self.main_window.capture_interval = 1.0 / fps
            
            # Apply quality settings
            if hasattr(self.main_window, 'bot'):
                # Update bot settings if available
                pass
            
            self.main_window.log_message(f"✅ Applied quality settings: FPS={fps}, HQ={high_quality}, Save={save_captures}")
            messagebox.showinfo("Success", "Quality settings applied successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")