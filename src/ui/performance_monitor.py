"""
Performance Monitor Component
Tracks and displays detailed performance metrics for the poker bot.
"""

import tkinter as tk
from tkinter import ttk
import time
import threading
from collections import deque
import numpy as np

# Optional matplotlib import
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    FigureCanvasTkAgg = None


class PerformanceMonitor:
    """Performance monitoring and visualization component."""
    
    def __init__(self, parent, main_window):
        """Initialize the performance monitor."""
        self.parent = parent
        self.main_window = main_window
        
        # Performance data storage
        self.capture_times = deque(maxlen=100)
        self.analysis_times = deque(maxlen=100)
        self.recognition_confidence = deque(maxlen=100)
        self.timestamps = deque(maxlen=100)
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        
        # Create performance monitoring UI
        self.create_performance_display()
        self.create_performance_controls()
        if MATPLOTLIB_AVAILABLE:
            self.create_performance_charts()
        else:
            self.create_simple_charts()
    
    def create_performance_display(self):
        """Create performance metrics display."""
        metrics_frame = tk.LabelFrame(self.parent, text="Performance Metrics", 
                                    bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        metrics_frame.pack(fill="x", padx=5, pady=5)
        
        # Create metrics grid
        metrics_grid = tk.Frame(metrics_frame, bg='#2b2b2b')
        metrics_grid.pack(fill="x", padx=5, pady=5)
        
        # Metrics labels
        self.metrics = {
            'fps': tk.StringVar(value="FPS: 0.0"),
            'capture_time': tk.StringVar(value="Capture: 0ms"),
            'analysis_time': tk.StringVar(value="Analysis: 0ms"),
            'memory_usage': tk.StringVar(value="Memory: 0MB"),
            'recognition_rate': tk.StringVar(value="Recognition: 0%"),
            'avg_confidence': tk.StringVar(value="Confidence: 0.0")
        }
        
        # Create metric displays in 2x3 grid
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#f44336', '#00BCD4']
        
        for i, (metric_name, metric_var) in enumerate(self.metrics.items()):
            row, col = positions[i]
            color = colors[i]
            
            metric_frame = tk.Frame(metrics_grid, bg=color, relief="raised", bd=2)
            metric_frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            metrics_grid.grid_columnconfigure(col, weight=1)
            
            metric_label = tk.Label(metric_frame, textvariable=metric_var,
                                   bg=color, fg='white', font=("Arial", 10, "bold"))
            metric_label.pack(pady=5)
    
    def create_performance_controls(self):
        """Create performance monitoring controls."""
        controls_frame = tk.LabelFrame(self.parent, text="Monitoring Controls", 
                                     bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        button_frame = tk.Frame(controls_frame, bg='#2b2b2b')
        button_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_monitor_btn = tk.Button(
            button_frame, text="▶ Start Monitoring", command=self.start_monitoring,
            bg='#4CAF50', fg='white', font=("Arial", 10, "bold")
        )
        self.start_monitor_btn.pack(side="left", padx=2)
        
        self.stop_monitor_btn = tk.Button(
            button_frame, text="⏹ Stop Monitoring", command=self.stop_monitoring,
            bg='#f44336', fg='white', font=("Arial", 10, "bold"), state="disabled"
        )
        self.stop_monitor_btn.pack(side="left", padx=2)
        
        tk.Button(button_frame, text="📊 Export Data", command=self.export_performance_data,
                 bg='#2196F3', fg='white', font=("Arial", 10, "bold")).pack(side="left", padx=2)
        
        tk.Button(button_frame, text="🔄 Reset Stats", command=self.reset_performance_stats,
                 bg='#FF9800', fg='white', font=("Arial", 10, "bold")).pack(side="left", padx=2)
        
        # Monitoring interval
        interval_frame = tk.Frame(controls_frame, bg='#2b2b2b')
        interval_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(interval_frame, text="Update Interval (ms):", bg='#2b2b2b', fg='white',
                font=("Arial", 10)).pack(side="left")
        
        self.interval_var = tk.IntVar(value=1000)
        interval_spin = tk.Spinbox(interval_frame, from_=100, to=5000, increment=100,
                                  textvariable=self.interval_var, width=8,
                                  bg='#3b3b3b', fg='white')
        interval_spin.pack(side="left", padx=5)
    
    def create_performance_charts(self):
        """Create performance visualization charts."""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        charts_frame = tk.LabelFrame(self.parent, text="Performance Charts", 
                                   bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        charts_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6), facecolor='#2b2b2b')
        self.fig.patch.set_facecolor('#2b2b2b')
        
        # Configure axes
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
        
        self.ax1.set_title('Capture & Analysis Times', color='white')
        self.ax1.set_ylabel('Time (ms)', color='white')
        
        self.ax2.set_title('Recognition Confidence', color='white')
        self.ax2.set_ylabel('Confidence', color='white')
        self.ax2.set_xlabel('Time', color='white')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, charts_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Initialize empty plots
        self.line1, = self.ax1.plot([], [], 'g-', label='Capture Time')
        self.line2, = self.ax1.plot([], [], 'b-', label='Analysis Time')
        self.line3, = self.ax2.plot([], [], 'r-', label='Confidence')
        
        self.ax1.legend()
        self.ax2.legend()
        
        plt.tight_layout()
    
    def create_simple_charts(self):
        """Create simple text-based charts when matplotlib is not available."""
        charts_frame = tk.LabelFrame(self.parent, text="Performance Data", 
                                   bg='#2b2b2b', fg='white', font=("Arial", 12, "bold"))
        charts_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Simple text display
        self.simple_chart_text = tk.Text(charts_frame, bg='#1e1e1e', fg='white',
                                        font=("Consolas", 10), height=15)
        self.simple_chart_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add note about matplotlib
        note_label = tk.Label(charts_frame, 
                             text="Install matplotlib for advanced charts: pip install matplotlib",
                             bg='#2b2b2b', fg='yellow', font=("Arial", 9))
        note_label.pack(pady=2)
    
    def start_monitoring(self):
        """Start performance monitoring."""
        if not self.monitoring:
            self.monitoring = True
            self.start_monitor_btn.configure(state="disabled")
            self.stop_monitor_btn.configure(state="normal")
            
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.main_window.log_message("✅ Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        self.start_monitor_btn.configure(state="normal")
        self.stop_monitor_btn.configure(state="disabled")
        
        self.main_window.log_message("⏹ Performance monitoring stopped")
    
    def monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self.update_performance_metrics()
                self.update_charts()
                time.sleep(self.interval_var.get() / 1000.0)
            except Exception as e:
                self.main_window.log_message(f"Performance monitoring error: {e}")
                break
    
    def update_performance_metrics(self):
        """Update performance metrics."""
        try:
            current_time = time.time()
            
            # Calculate FPS
            if len(self.timestamps) > 1:
                time_diff = current_time - self.timestamps[-1]
                fps = 1.0 / max(time_diff, 0.001)
                self.metrics['fps'].set(f"FPS: {fps:.1f}")
            
            # Get memory usage
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.metrics['memory_usage'].set(f"Memory: {memory_mb:.1f}MB")
            except ImportError:
                self.metrics['memory_usage'].set("Memory: N/A")
            
            # Calculate average times
            if self.capture_times:
                avg_capture = np.mean(list(self.capture_times)) * 1000
                self.metrics['capture_time'].set(f"Capture: {avg_capture:.0f}ms")
            
            if self.analysis_times:
                avg_analysis = np.mean(list(self.analysis_times)) * 1000
                self.metrics['analysis_time'].set(f"Analysis: {avg_analysis:.0f}ms")
            
            # Calculate recognition rate
            if hasattr(self.main_window, 'capture_count') and self.main_window.capture_count > 0:
                recognition_rate = (self.main_window.success_count / self.main_window.capture_count) * 100
                self.metrics['recognition_rate'].set(f"Recognition: {recognition_rate:.1f}%")
            
            # Calculate average confidence
            if self.recognition_confidence:
                avg_confidence = np.mean(list(self.recognition_confidence))
                self.metrics['avg_confidence'].set(f"Confidence: {avg_confidence:.2f}")
            
            # Store timestamp
            self.timestamps.append(current_time)
            
        except Exception as e:
            self.main_window.log_message(f"Error updating performance metrics: {e}")
    
    def update_charts(self):
        """Update performance charts."""
        if not MATPLOTLIB_AVAILABLE:
            self.update_simple_charts()
            return
            
        try:
            if len(self.timestamps) < 2:
                return
            
            # Convert timestamps to relative time
            base_time = self.timestamps[0]
            relative_times = [(t - base_time) for t in self.timestamps]
            
            # Update capture/analysis times chart
            if self.capture_times and self.analysis_times:
                capture_ms = [t * 1000 for t in self.capture_times]
                analysis_ms = [t * 1000 for t in self.analysis_times]
                
                self.line1.set_data(relative_times[-len(capture_ms):], capture_ms)
                self.line2.set_data(relative_times[-len(analysis_ms):], analysis_ms)
                
                self.ax1.relim()
                self.ax1.autoscale_view()
            
            # Update confidence chart
            if self.recognition_confidence:
                confidence_data = list(self.recognition_confidence)
                self.line3.set_data(relative_times[-len(confidence_data):], confidence_data)
                
                self.ax2.relim()
                self.ax2.autoscale_view()
            
            # Refresh canvas
            self.canvas.draw()
            
        except Exception as e:
            self.main_window.log_message(f"Error updating charts: {e}")
    
    def update_simple_charts(self):
        """Update simple text-based charts."""
        try:
            if len(self.timestamps) < 2:
                return
            
            # Clear and update text display
            self.simple_chart_text.delete(1.0, tk.END)
            
            # Add recent performance data
            self.simple_chart_text.insert(tk.END, "Recent Performance Data:\n")
            self.simple_chart_text.insert(tk.END, "=" * 30 + "\n\n")
            
            # Show last 10 capture times
            if self.capture_times:
                recent_captures = list(self.capture_times)[-10:]
                self.simple_chart_text.insert(tk.END, "Capture Times (ms):\n")
                for i, time_val in enumerate(recent_captures):
                    self.simple_chart_text.insert(tk.END, f"  {i+1:2d}: {time_val*1000:.1f}ms\n")
                self.simple_chart_text.insert(tk.END, "\n")
            
            # Show last 10 analysis times
            if self.analysis_times:
                recent_analysis = list(self.analysis_times)[-10:]
                self.simple_chart_text.insert(tk.END, "Analysis Times (ms):\n")
                for i, time_val in enumerate(recent_analysis):
                    self.simple_chart_text.insert(tk.END, f"  {i+1:2d}: {time_val*1000:.1f}ms\n")
                self.simple_chart_text.insert(tk.END, "\n")
            
            # Show last 10 confidence values
            if self.recognition_confidence:
                recent_confidence = list(self.recognition_confidence)[-10:]
                self.simple_chart_text.insert(tk.END, "Recognition Confidence:\n")
                for i, conf_val in enumerate(recent_confidence):
                    self.simple_chart_text.insert(tk.END, f"  {i+1:2d}: {conf_val:.3f}\n")
            
            # Auto-scroll to bottom
            self.simple_chart_text.see(tk.END)
            
        except Exception as e:
            self.main_window.log_message(f"Error updating simple charts: {e}")
    
    def record_capture_time(self, capture_time: float):
        """Record a capture time measurement."""
        self.capture_times.append(capture_time)
    
    def record_analysis_time(self, analysis_time: float):
        """Record an analysis time measurement."""
        self.analysis_times.append(analysis_time)
    
    def record_recognition_confidence(self, confidence: float):
        """Record a recognition confidence measurement."""
        self.recognition_confidence.append(confidence)
    
    def export_performance_data(self):
        """Export performance data to file."""
        try:
            from tkinter import filedialog
            import json
            
            filename = filedialog.asksaveasfilename(
                title="Export Performance Data",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                data = {
                    'timestamps': list(self.timestamps),
                    'capture_times': list(self.capture_times),
                    'analysis_times': list(self.analysis_times),
                    'recognition_confidence': list(self.recognition_confidence),
                    'capture_count': getattr(self.main_window, 'capture_count', 0),
                    'success_count': getattr(self.main_window, 'success_count', 0)
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.main_window.log_message(f"✅ Performance data exported to {filename}")
                
        except Exception as e:
            self.main_window.log_message(f"❌ Export failed: {e}")
    
    def reset_performance_stats(self):
        """Reset all performance statistics."""
        self.capture_times.clear()
        self.analysis_times.clear()
        self.recognition_confidence.clear()
        self.timestamps.clear()
        
        # Reset main window stats
        if hasattr(self.main_window, 'capture_count'):
            self.main_window.capture_count = 0
        if hasattr(self.main_window, 'success_count'):
            self.main_window.success_count = 0
        
        # Clear charts
        for line in [self.line1, self.line2, self.line3]:
            line.set_data([], [])
        
        self.canvas.draw()
        
        self.main_window.log_message("📊 Performance statistics reset")