"""
Manager classes for YSA GUI application.

This package contains manager classes that handle different aspects of the application:
- MenuManager: Handles menu bar setup and actions
- UIManager: Manages UI layout and widget setup
- DataManager: Handles data loading, processing and management
- AnalysisManager: Manages analysis operations and threads
- EventHandler: Handles user input events
- PlaybackManager: Manages playback controls and timing
- VisualizationManager: Handles visualization rendering and display
"""

from .menu_manager import MenuManager
from .ui_manager import UIManager
from .data_manager import DataManager
from .analysis_manager import AnalysisManager
from .event_handler import EventHandler
from .playback_manager import PlaybackManager
from .visualization_manager import VisualizationManager

__all__ = [
    'MenuManager',
    'UIManager',
    'DataManager',
    'AnalysisManager',
    'EventHandler',
    'PlaybackManager',
    'VisualizationManager'
]