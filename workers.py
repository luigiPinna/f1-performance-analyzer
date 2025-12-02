from PyQt5.QtCore import QThread, pyqtSignal
import fastf1
import pandas as pd
import os


class CalendarLoaderThread(QThread):
    """Load race calendar for years 2022-2025"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            # Setup FastF1 cache
            cache_dir = './fastf1_cache'
            os.makedirs(cache_dir, exist_ok=True)
            fastf1.Cache.enable_cache(cache_dir)

            calendar_data = {}

            # Load calendar for each year
            for year in [2022, 2023, 2024, 2025]:
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

            self.finished.emit(calendar_data)

        except Exception as e:
            self.error.emit(f"Calendar loading failed: {str(e)}")


class SessionLoaderThread(QThread):
    """Load specific session and available drivers"""
    finished = pyqtSignal(object, list)
    error = pyqtSignal(str)

    def __init__(self, year, gp_name, session_type):
        super().__init__()
        self.year = year
        self.gp_name = gp_name
        self.session_type = session_type

    def run(self):
        try:
            session = fastf1.get_session(self.year, self.gp_name, self.session_type)
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

            self.finished.emit(session, drivers_data)

        except Exception as e:
            self.error.emit(f"Session loading failed: {str(e)}")


class FastestLapComparisonThread(QThread):
    """Find fastest laps and load telemetry data"""
    finished = pyqtSignal(object, object, dict, dict)
    error = pyqtSignal(str)

    def __init__(self, session, driver1_abbr, driver2_abbr):
        super().__init__()
        self.session = session
        self.driver1_abbr = driver1_abbr
        self.driver2_abbr = driver2_abbr

    def run(self):
        try:
            laps = self.session.laps

            # Find fastest lap for driver 1
            driver1_laps = laps.pick_drivers(self.driver1_abbr)
            fastest_lap1 = driver1_laps.pick_fastest()

            if fastest_lap1 is None or pd.isna(fastest_lap1['LapTime']):
                self.error.emit(f"No valid fastest lap found for {self.driver1_abbr}")
                return

            # Find fastest lap for driver 2
            driver2_laps = laps.pick_drivers(self.driver2_abbr)
            fastest_lap2 = driver2_laps.pick_fastest()

            if fastest_lap2 is None or pd.isna(fastest_lap2['LapTime']):
                self.error.emit(f"No valid fastest lap found for {self.driver2_abbr}")
                return

            # Load telemetry
            tel1 = fastest_lap1.get_car_data().add_distance()
            tel2 = fastest_lap2.get_car_data().add_distance()

            # Lap info
            lap1_info = {
                'driver': self.driver1_abbr,
                'lap_number': fastest_lap1['LapNumber'],
                'lap_time': fastest_lap1['LapTime'].total_seconds()
            }

            lap2_info = {
                'driver': self.driver2_abbr,
                'lap_number': fastest_lap2['LapNumber'],
                'lap_time': fastest_lap2['LapTime'].total_seconds()
            }

            self.finished.emit(tel1, tel2, lap1_info, lap2_info)

        except Exception as e:
            self.error.emit(f"Fastest lap comparison failed: {str(e)}")