"""
Fastest Lap Comparison Functionality
Compares telemetry data between two drivers' fastest laps
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from .base import BaseFunctionality


class FastestLapComparison(BaseFunctionality):
    """
    Analyzes and compares the fastest laps of two drivers
    with detailed telemetry visualization (Speed, Throttle, Brake)
    """
    
    def __init__(self):
        super().__init__()
        self.current_session: Optional[Any] = None
        self.current_drivers: List[Dict] = []
        self.selected_driver1: Optional[str] = None
        self.selected_driver2: Optional[str] = None
        self.comparison_data: Optional[Dict] = None
    
    def get_name(self) -> str:
        """Return display name"""
        return "Fastest Lap Comparison"
    
    def get_description(self) -> str:
        """Return brief description"""
        return "Compare telemetry between two drivers' fastest laps"
    
    def init_ui(self, parent_widget) -> None:
        """
        Initialize UI for Streamlit environment.
        In a PyQt5 environment, this would create different widgets.
        
        Args:
            parent_widget: Streamlit or PyQt5 parent container
        """
        # This is called from main.py in Streamlit
        # For Streamlit, the UI is handled in main.py directly
        # For PyQt5, this would create buttons, dropdowns, etc.
        pass
    
    def on_session_loaded(self, session: Any, drivers: List[Dict]) -> None:
        """
        Update when a new session is loaded
        
        Args:
            session: FastF1 session object
            drivers: List of available drivers with keys: abbreviation, full_name, display, number
        """
        self.current_session = session
        self.current_drivers = drivers
        self.selected_driver1 = None
        self.selected_driver2 = None
        self.comparison_data = None
    
    def set_comparison_drivers(self, driver1_abbr: str, driver2_abbr: str) -> None:
        """
        Set the drivers to compare.
        
        Args:
            driver1_abbr: 3-letter abbreviation for driver 1
            driver2_abbr: 3-letter abbreviation for driver 2
        """
        self.selected_driver1 = driver1_abbr
        self.selected_driver2 = driver2_abbr
    
    def perform_comparison(self) -> Dict[str, Any]:
        """
        Execute the fastest lap comparison.
        
        Returns:
            Dict with keys: 'tel1', 'tel2', 'lap1_info', 'lap2_info'
            
        Raises:
            ValueError: If session not loaded or drivers not set
        """
        if self.current_session is None:
            raise ValueError("No session loaded. Please load a session first.")
        
        if not self.selected_driver1 or not self.selected_driver2:
            raise ValueError("Both drivers must be selected before comparison.")
        
        if self.selected_driver1 == self.selected_driver2:
            raise ValueError("Cannot compare a driver with themselves.")
        
        try:
            laps = self.current_session.laps
            
            # Find fastest lap for driver 1
            driver1_laps = laps.pick_drivers(self.selected_driver1)
            fastest_lap1 = driver1_laps.pick_fastest()
            
            if fastest_lap1 is None or pd.isna(fastest_lap1['LapTime']):
                raise ValueError(f"No valid fastest lap found for {self.selected_driver1}")
            
            # Find fastest lap for driver 2
            driver2_laps = laps.pick_drivers(self.selected_driver2)
            fastest_lap2 = driver2_laps.pick_fastest()
            
            if fastest_lap2 is None or pd.isna(fastest_lap2['LapTime']):
                raise ValueError(f"No valid fastest lap found for {self.selected_driver2}")
            
            # Load telemetry
            tel1 = fastest_lap1.get_car_data().add_distance()
            tel2 = fastest_lap2.get_car_data().add_distance()
            
            # Prepare lap info
            lap1_info = {
                'driver': self.selected_driver1,
                'lap_number': fastest_lap1['LapNumber'],
                'lap_time': fastest_lap1['LapTime'].total_seconds()
            }
            
            lap2_info = {
                'driver': self.selected_driver2,
                'lap_number': fastest_lap2['LapNumber'],
                'lap_time': fastest_lap2['LapTime'].total_seconds()
            }
            
            self.comparison_data = {
                'tel1': tel1,
                'tel2': tel2,
                'lap1_info': lap1_info,
                'lap2_info': lap2_info
            }
            
            return self.comparison_data
            
        except Exception as e:
            raise ValueError(f"Fastest lap comparison failed: {str(e)}")
    
    def get_comparison_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the last comparison result without re-running analysis
        
        Returns:
            Comparison data or None if not yet performed
        """
        return self.comparison_data
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.comparison_data = None
        self.current_session = None
        self.current_drivers = []
