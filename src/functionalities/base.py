"""
Base Functionality Abstract Class
Defines the interface for all analysis functionalities (plugin system)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseFunctionality(ABC):
    """
    Abstract base class for all F1 analysis functionalities.
    Each functionality represents a distinct analysis or comparison tool.
    """
    
    def __init__(self):
        """Initialize functionality"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return the display name of this functionality
        Example: "Fastest Lap Comparison", "Driver Development", etc.
        """
        pass
    
    @abstractmethod
    def init_ui(self, parent_widget):
        """
        Initialize the UI components for this functionality.
        Called when user selects this functionality.
        
        Args:
            parent_widget: The container widget where UI should be added
        """
        pass
    
    @abstractmethod
    def on_session_loaded(self, session, drivers: list) -> None:
        """
        Called when a new session is loaded.
        Functionality should update UI with available drivers.
        
        Args:
            session: FastF1 session object
            drivers: List of available driver dicts
        """
        pass
    
    def get_description(self) -> str:
        """Optional: Return a brief description of what this functionality does"""
        return ""
    
    def cleanup(self) -> None:
        """Optional: Clean up resources when functionality is unloaded"""
        pass
