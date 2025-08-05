"""
UI Package for Modern Poker Study & Analysis Tool
Contains all UI components split into logical modules.
"""

# Import components (using relative imports within package)
try:
    from .main_window import MainWindow
    from .header_panel import HeaderPanel
    from .table_view_panel import TableViewPanel
    from .game_info_panel import GameInfoPanel
    from .control_panel import ControlPanel
    from .status_bar import StatusBar
except ImportError:
    # Fallback to absolute imports if relative imports fail
    from ui.main_window import MainWindow
    from ui.header_panel import HeaderPanel
    from ui.table_view_panel import TableViewPanel
    from ui.game_info_panel import GameInfoPanel
    from ui.control_panel import ControlPanel
    from ui.status_bar import StatusBar

__all__ = [
    'MainWindow',
    'HeaderPanel', 
    'TableViewPanel',
    'GameInfoPanel',
    'ControlPanel',
    'StatusBar'
]