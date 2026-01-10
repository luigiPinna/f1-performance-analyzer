"""
F1 Data Service - FastF1 logic independent from UI framework
All data loading and processing happens here, reusable by any UI (PyQt5, Streamlit, Web, etc.)
"""

import fastf1
import pandas as pd
import os
from typing import Dict, List, Tuple, Optional, Any
from .constants import DEFAULT_CACHE_DIR, DEFAULT_SEASONS


class F1DataService:
    """Core service for F1 data operations using FastF1"""
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        """Initialize data service with cache configuration"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
        self.current_session: Optional[Any] = None
        self.current_drivers: List[Dict] = []
    
    def load_calendar(self, years: List[int] = None) -> Dict[int, List[Dict]]:
        """
        Load F1 calendar for specified years
        Returns: dict mapping year -> list of GP dicts
        """
        if years is None:
            years = DEFAULT_SEASONS
            
        calendar_data = {}
        
        for year in years:
            try:
                schedule = fastf1.get_event_schedule(year)
                # Filter out testing sessions
                races = schedule[schedule['EventFormat'] != 'testing']
                
                calendar_data[year] = []
                for idx, event in races.iterrows():
                    calendar_data[year].append({
                        'round': event['RoundNumber'],
                        'name': event['EventName'],
                        'location': event['Location'],
                        'display': f"R{event['RoundNumber']:02d} - {event['EventName']}"
                    })
            except Exception as e:
                print(f"Error loading calendar for {year}: {e}")
                calendar_data[year] = []
        
        return calendar_data
    
    def load_session(self, year: int, gp_name: str, session_type: str) -> Tuple[Any, List[Dict]]:
        """
        Load a specific session and extract available drivers
        Returns: (session object, list of driver dicts)
        """
        try:
            session = fastf1.get_session(year, gp_name, session_type)
            session.load()
            
            # Extract drivers with valid data
            drivers_data = []
            results = session.results
            
            for idx, driver in results.iterrows():
                try:
                    driver_number = int(driver['DriverNumber']) if pd.notna(driver['DriverNumber']) else 0
                    abbreviation = driver['Abbreviation']
                    
                    # Try to get full name
                    if 'FullName' in driver and pd.notna(driver['FullName']):
                        full_name = driver['FullName']
                    elif 'FirstName' in driver and 'LastName' in driver:
                        first = driver['FirstName'] if pd.notna(driver['FirstName']) else ''
                        last = driver['LastName'] if pd.notna(driver['LastName']) else ''
                        full_name = f"{first} {last}".strip()
                    else:
                        full_name = abbreviation
                    
                    # Verify driver has at least one valid lap
                    driver_laps = session.laps.pick_drivers(abbreviation)
                    if len(driver_laps) > 0 and driver_laps['LapTime'].notna().any():
                        drivers_data.append({
                            'number': driver_number,
                            'abbreviation': abbreviation,
                            'full_name': full_name,
                            'display': f"#{driver_number} {abbreviation} - {full_name}"
                        })
                except Exception as e:
                    print(f"Error processing driver {driver.get('Abbreviation', 'Unknown')}: {e}")
                    continue
            
            # Sort by driver number
            drivers_data.sort(key=lambda x: x['number'])
            
            self.current_session = session
            self.current_drivers = drivers_data
            
            return session, drivers_data
        
        except Exception as e:
            raise Exception(f"Session loading failed: {str(e)}")
    
    def compare_fastest_laps(self, driver1_abbr: str, driver2_abbr: str) -> Tuple[pd.DataFrame, pd.DataFrame, Dict, Dict]:
        """
        Find and compare fastest laps between two drivers
        Returns: (tel1, tel2, lap1_info, lap2_info)
        """
        if self.current_session is None:
            raise Exception("No session loaded. Call load_session() first.")
        
        try:
            laps = self.current_session.laps
            
            # Find fastest lap for driver 1
            driver1_laps = laps.pick_drivers(driver1_abbr)
            fastest_lap1 = driver1_laps.pick_fastest()
            
            if fastest_lap1 is None or pd.isna(fastest_lap1['LapTime']):
                raise Exception(f"No valid fastest lap found for {driver1_abbr}")
            
            # Find fastest lap for driver 2
            driver2_laps = laps.pick_drivers(driver2_abbr)
            fastest_lap2 = driver2_laps.pick_fastest()
            
            if fastest_lap2 is None or pd.isna(fastest_lap2['LapTime']):
                raise Exception(f"No valid fastest lap found for {driver2_abbr}")
            
            # Load telemetry
            tel1 = fastest_lap1.get_car_data().add_distance()
            tel2 = fastest_lap2.get_car_data().add_distance()
            
            # Lap info
            lap1_info = {
                'driver': driver1_abbr,
                'lap_number': fastest_lap1['LapNumber'],
                'lap_time': fastest_lap1['LapTime'].total_seconds()
            }
            
            lap2_info = {
                'driver': driver2_abbr,
                'lap_number': fastest_lap2['LapNumber'],
                'lap_time': fastest_lap2['LapTime'].total_seconds()
            }
            
            return tel1, tel2, lap1_info, lap2_info
        
        except Exception as e:
            raise Exception(f"Fastest lap comparison failed: {str(e)}")
