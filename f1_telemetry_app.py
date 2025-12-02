#!/usr/bin/env python3
"""
F1 Performance Analyzer
FASTEST LAP COMPARISON - Confronto automatico tra i giri più veloci di due piloti
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QPushButton,
                             QFrame, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import fastf1
import pandas as pd
import os

plt.style.use('dark_background')


class CalendarLoaderThread(QThread):
    """Carica il calendario delle gare per gli anni 2022-2024"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            cache_dir = './fastf1_cache'
            os.makedirs(cache_dir, exist_ok=True)
            fastf1.Cache.enable_cache(cache_dir)

            calendar_data = {}

            for year in [2022, 2023, 2024, 2025]:
                try:
                    schedule = fastf1.get_event_schedule(year)
                    # Filtra solo le gare (esclude testing)
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
    """Carica la sessione specifica e i piloti disponibili"""
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

            # Estrai piloti con dati validi
            drivers_data = []
            results = session.results

            for idx, driver in results.iterrows():
                try:
                    driver_number = int(driver['DriverNumber']) if pd.notna(driver['DriverNumber']) else 0
                    abbreviation = driver['Abbreviation']

                    # Prova a ottenere il nome completo
                    if 'FullName' in driver and pd.notna(driver['FullName']):
                        full_name = driver['FullName']
                    elif 'FirstName' in driver and 'LastName' in driver:
                        first = driver['FirstName'] if pd.notna(driver['FirstName']) else ''
                        last = driver['LastName'] if pd.notna(driver['LastName']) else ''
                        full_name = f"{first} {last}".strip()
                    else:
                        full_name = abbreviation

                    # Verifica che il pilota abbia almeno un giro valido
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

            # Ordina per numero pilota
            drivers_data.sort(key=lambda x: x['number'])

            self.finished.emit(session, drivers_data)

        except Exception as e:
            self.error.emit(f"Session loading failed: {str(e)}")


class FastestLapComparisonThread(QThread):
    """Trova i giri più veloci e carica la telemetria"""
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

            # Trova fastest lap per driver 1
            driver1_laps = laps.pick_drivers(self.driver1_abbr)
            fastest_lap1 = driver1_laps.pick_fastest()

            if fastest_lap1 is None or pd.isna(fastest_lap1['LapTime']):
                self.error.emit(f"No valid fastest lap found for {self.driver1_abbr}")
                return

            # Trova fastest lap per driver 2
            driver2_laps = laps.pick_drivers(self.driver2_abbr)
            fastest_lap2 = driver2_laps.pick_fastest()

            if fastest_lap2 is None or pd.isna(fastest_lap2['LapTime']):
                self.error.emit(f"No valid fastest lap found for {self.driver2_abbr}")
                return

            # Carica telemetria
            tel1 = fastest_lap1.get_car_data().add_distance()
            tel2 = fastest_lap2.get_car_data().add_distance()

            # Info sui giri
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


class TelemetryCanvas(FigureCanvas):
    """Canvas per visualizzare i grafici telemetrici"""

    def __init__(self):
        self.fig = Figure(figsize=(14, 10), facecolor='#0d1117')
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.show_welcome()

    def show_welcome(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5,
                'FASTEST LAP COMPARISON\n\n'
                'Seleziona Anno, Gran Premio, Sessione e due Piloti\n'
                'per confrontare automaticamente i loro giri più veloci',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=16, color='#58a6ff', fontweight='bold')
        ax.set_facecolor('#0d1117')
        ax.axis('off')
        self.draw()

    def show_loading(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Loading telemetry data...',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=18, color='#58a6ff', fontweight='bold')
        ax.set_facecolor('#0d1117')
        ax.axis('off')
        self.draw()

    def plot_comparison(self, tel1, tel2, lap1_info, lap2_info, gp_name, session_type):
        self.fig.clear()

        # Colori F1 TV style
        color1, color2 = '#58a6ff', '#f85149'

        # Layout: 3 grafici verticali
        ax1 = self.fig.add_subplot(311)
        ax2 = self.fig.add_subplot(312)
        ax3 = self.fig.add_subplot(313)

        # SPEED
        ax1.plot(tel1['Distance'] / 1000, tel1['Speed'], color=color1, linewidth=2.5,
                 label=f"{lap1_info['driver']} L{lap1_info['lap_number']} ({lap1_info['lap_time']:.3f}s)")
        ax1.plot(tel2['Distance'] / 1000, tel2['Speed'], color=color2, linewidth=2.5,
                 label=f"{lap2_info['driver']} L{lap2_info['lap_number']} ({lap2_info['lap_time']:.3f}s)")
        ax1.set_ylabel('Speed (km/h)', fontsize=12, fontweight='bold')
        ax1.set_title('SPEED TRACE', fontsize=14, fontweight='bold', pad=15)
        ax1.legend(fontsize=11, loc='upper right')
        ax1.grid(True, alpha=0.3, color='#30363d')
        ax1.set_ylim(50, 350)

        # THROTTLE
        ax2.plot(tel1['Distance'] / 1000, tel1['Throttle'], color=color1, linewidth=2.5)
        ax2.plot(tel2['Distance'] / 1000, tel2['Throttle'], color=color2, linewidth=2.5)
        ax2.set_ylabel('Throttle (%)', fontsize=12, fontweight='bold')
        ax2.set_title('THROTTLE APPLICATION', fontsize=14, fontweight='bold', pad=15)
        ax2.grid(True, alpha=0.3, color='#30363d')
        ax2.set_ylim(0, 100)

        # BRAKE
        ax3.plot(tel1['Distance'] / 1000, tel1['Brake'] * 100, color=color1, linewidth=2.5)
        ax3.plot(tel2['Distance'] / 1000, tel2['Brake'] * 100, color=color2, linewidth=2.5)
        ax3.set_ylabel('Brake (%)', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Track Distance (km)', fontsize=12, fontweight='bold')
        ax3.set_title('BRAKE APPLICATION', fontsize=14, fontweight='bold', pad=15)
        ax3.grid(True, alpha=0.3, color='#30363d')
        ax3.set_ylim(0, 100)

        # Styling F1 TV
        for ax in [ax1, ax2, ax3]:
            ax.set_facecolor('#161b22')
            ax.tick_params(colors='white', labelsize=10)
            for spine in ax.spines.values():
                spine.set_color('#30363d')
                spine.set_linewidth(0.8)

        # Info header
        gap = abs(lap1_info['lap_time'] - lap2_info['lap_time'])
        faster = lap1_info['driver'] if lap1_info['lap_time'] < lap2_info['lap_time'] else lap2_info['driver']

        self.fig.suptitle(
            f"FASTEST LAP COMPARISON | {gp_name} | {session_type}\n"
            f"{lap1_info['driver']} vs {lap2_info['driver']} | Gap: {gap:.3f}s (Faster: {faster})",
            fontsize=14, fontweight='bold', y=0.97)

        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.92, hspace=0.35)
        self.draw()


class F1PerformanceAnalyzer(QMainWindow):
    """Finestra principale dell'applicazione"""

    def __init__(self):
        super().__init__()
        self.calendar_data = {}
        self.current_session = None
        self.current_drivers = []
        self.init_ui()
        self.load_calendar()

    def init_ui(self):
        self.setWindowTitle('F1 Performance Analyzer - Fastest Lap Comparison')
        self.setGeometry(100, 100, 1600, 1000)

        # Dark theme F1 style
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            QWidget { background-color: #0d1117; color: #f0f6fc; font-family: 'Segoe UI'; }
            QLabel { color: #f0f6fc; }
            QComboBox { 
                background-color: #21262d;
                border: 1px solid #30363d;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 11px;
                min-height: 25px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #30363d;
                width: 20px;
                border-radius: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: #21262d;
                border: 1px solid #30363d;
                selection-background-color: #58a6ff;
                color: #f0f6fc;
            }
            QPushButton {
                background-color: #238636;
                border: 1px solid #2ea043;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ea043; }
            QPushButton:pressed { background-color: #1a7f37; }
            QPushButton:disabled { 
                background-color: #30363d;
                border: 1px solid #21262d;
                color: #7d8590;
            }
            QFrame { background-color: #161b22; border-radius: 8px; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # CONTROL PANEL
        self.create_control_panel(layout)

        # TELEMETRY DISPLAY
        self.telemetry_canvas = TelemetryCanvas()
        layout.addWidget(self.telemetry_canvas, stretch=4)

    def create_control_panel(self, parent_layout):
        panel = QFrame()
        panel.setFixedWidth(400)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # TITLE
        title = QLabel('FASTEST LAP COMPARISON')
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setStyleSheet("color: #58a6ff; margin-bottom: 5px;")
        layout.addWidget(title)

        subtitle = QLabel('Formula 1 Telemetry Analysis')
        subtitle.setFont(QFont('Segoe UI', 11))
        subtitle.setStyleSheet("color: #8b949e; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # YEAR SELECTION
        year_label = QLabel('YEAR')
        year_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        year_label.setStyleSheet("color: #8b949e; margin-top: 10px;")
        layout.addWidget(year_label)

        self.year_combo = QComboBox()
        self.year_combo.addItems(['2025', '2024', '2023', '2022'])
        self.year_combo.setCurrentText('2025')
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        layout.addWidget(self.year_combo)

        # GRAND PRIX SELECTION
        gp_label = QLabel('GRAND PRIX')
        gp_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        gp_label.setStyleSheet("color: #8b949e; margin-top: 10px;")
        layout.addWidget(gp_label)

        self.gp_combo = QComboBox()
        self.gp_combo.currentTextChanged.connect(self.on_gp_changed)
        layout.addWidget(self.gp_combo)

        # SESSION TYPE
        session_label = QLabel('SESSION TYPE')
        session_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        session_label.setStyleSheet("color: #8b949e; margin-top: 10px;")
        layout.addWidget(session_label)

        self.session_combo = QComboBox()
        self.session_combo.addItems(['Qualifying', 'Race'])
        self.session_combo.currentTextChanged.connect(self.on_session_changed)
        layout.addWidget(self.session_combo)

        # DRIVER 1 SELECTION
        driver1_label = QLabel('DRIVER 1')
        driver1_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        driver1_label.setStyleSheet("color: #8b949e; margin-top: 10px;")
        layout.addWidget(driver1_label)

        self.driver1_combo = QComboBox()
        layout.addWidget(self.driver1_combo)

        # DRIVER 2 SELECTION
        driver2_label = QLabel('DRIVER 2')
        driver2_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        driver2_label.setStyleSheet("color: #8b949e; margin-top: 10px;")
        layout.addWidget(driver2_label)

        self.driver2_combo = QComboBox()
        layout.addWidget(self.driver2_combo)

        # COMPARE BUTTON
        self.compare_btn = QPushButton('COMPARE FASTEST LAPS')
        self.compare_btn.setFixedHeight(50)
        self.compare_btn.clicked.connect(self.compare_fastest_laps)
        self.compare_btn.setEnabled(False)
        layout.addWidget(self.compare_btn)

        # STATUS
        self.status_label = QLabel('Initializing...')
        self.status_label.setStyleSheet("color: #58a6ff; font-size: 10px; margin-top: 15px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()
        parent_layout.addWidget(panel, stretch=1)

    def load_calendar(self):
        """Carica il calendario delle gare"""
        self.status_label.setText('Loading calendar data...')
        self.status_label.setStyleSheet("color: #58a6ff; font-size: 10px; margin-top: 15px;")

        self.calendar_thread = CalendarLoaderThread()
        self.calendar_thread.finished.connect(self.on_calendar_loaded)
        self.calendar_thread.error.connect(self.on_error)
        self.calendar_thread.start()

    def on_calendar_loaded(self, calendar_data):
        """Callback quando il calendario è caricato"""
        self.calendar_data = calendar_data
        self.status_label.setText('✓ Calendar loaded')
        self.status_label.setStyleSheet("color: #7c3aed; font-size: 10px; margin-top: 15px;")

        # Popola i GP per l'anno corrente
        self.on_year_changed(self.year_combo.currentText())

    def on_year_changed(self, year_text):
        """Aggiorna la lista GP quando cambia l'anno"""
        if not year_text or not self.calendar_data:
            return

        year = int(year_text)
        self.gp_combo.clear()

        if year in self.calendar_data:
            for gp in self.calendar_data[year]:
                self.gp_combo.addItem(gp['display'], gp['name'])

        self.driver1_combo.clear()
        self.driver2_combo.clear()
        self.compare_btn.setEnabled(False)

    def on_gp_changed(self):
        """Carica i piloti quando cambia il GP"""
        if self.gp_combo.currentData():
            self.load_session()

    def on_session_changed(self):
        """Ricarica i piloti quando cambia il tipo di sessione"""
        if self.gp_combo.currentData():
            self.load_session()

    def load_session(self):
        """Carica la sessione e i piloti"""
        year = int(self.year_combo.currentText())
        gp_name = self.gp_combo.currentData()
        session_type = self.session_combo.currentText()

        if not gp_name:
            return

        self.status_label.setText(f'Loading {session_type} data...')
        self.status_label.setStyleSheet("color: #58a6ff; font-size: 10px; margin-top: 15px;")
        self.compare_btn.setEnabled(False)
        self.driver1_combo.clear()
        self.driver2_combo.clear()

        self.session_thread = SessionLoaderThread(year, gp_name, session_type)
        self.session_thread.finished.connect(self.on_session_loaded)
        self.session_thread.error.connect(self.on_error)
        self.session_thread.start()

    def on_session_loaded(self, session, drivers_data):
        """Callback quando la sessione è caricata"""
        self.current_session = session
        self.current_drivers = drivers_data

        # Popola le combo dei piloti
        self.driver1_combo.clear()
        self.driver2_combo.clear()

        for driver in drivers_data:
            self.driver1_combo.addItem(driver['display'], driver['abbreviation'])
            self.driver2_combo.addItem(driver['display'], driver['abbreviation'])

        # Seleziona piloti diversi di default
        if len(drivers_data) >= 2:
            self.driver1_combo.setCurrentIndex(0)
            self.driver2_combo.setCurrentIndex(1)

        self.compare_btn.setEnabled(len(drivers_data) >= 2)
        self.status_label.setText(f'✓ {len(drivers_data)} drivers loaded')
        self.status_label.setStyleSheet("color: #7c3aed; font-size: 10px; margin-top: 15px;")

    def compare_fastest_laps(self):
        """Confronta i giri più veloci dei due piloti selezionati"""
        if not self.current_session:
            return

        driver1_abbr = self.driver1_combo.currentData()
        driver2_abbr = self.driver2_combo.currentData()

        if not driver1_abbr or not driver2_abbr:
            return

        if driver1_abbr == driver2_abbr:
            QMessageBox.warning(self, 'Warning', 'Please select different drivers')
            return

        self.status_label.setText('Finding fastest laps and loading telemetry...')
        self.status_label.setStyleSheet("color: #58a6ff; font-size: 10px; margin-top: 15px;")
        self.telemetry_canvas.show_loading()

        self.comparison_thread = FastestLapComparisonThread(
            self.current_session, driver1_abbr, driver2_abbr
        )
        self.comparison_thread.finished.connect(self.on_comparison_ready)
        self.comparison_thread.error.connect(self.on_error)
        self.comparison_thread.start()

    def on_comparison_ready(self, tel1, tel2, lap1_info, lap2_info):
        """Callback quando il confronto è pronto"""
        gp_name = self.gp_combo.currentText()
        session_type = self.session_combo.currentText()

        self.telemetry_canvas.plot_comparison(
            tel1, tel2, lap1_info, lap2_info, gp_name, session_type
        )

        self.status_label.setText('✓ Comparison complete')
        self.status_label.setStyleSheet("color: #7c3aed; font-size: 10px; margin-top: 15px;")

    def on_error(self, error_msg):
        """Gestione errori"""
        self.status_label.setText(f'✗ Error: {error_msg}')
        self.status_label.setStyleSheet("color: #f85149; font-size: 10px; margin-top: 15px;")
        QMessageBox.critical(self, 'Error', error_msg)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = F1PerformanceAnalyzer()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()