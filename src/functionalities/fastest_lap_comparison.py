from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QComboBox, QPushButton,
                             QFrame, QMessageBox)
from PyQt5.QtGui import QFont
from .base import BaseFunctionality
from src.workers import SessionLoaderThread, FastestLapComparisonThread


class FastestLapComparison(BaseFunctionality):
    """Compare fastest laps between two drivers"""

    def __init__(self, calendar_data, telemetry_canvas):
        super().__init__(calendar_data, telemetry_canvas)
        self.current_session = None
        self.current_drivers = []
        self.init_ui()

    def get_name(self):
        return "Fastest Lap Comparison"

    def init_ui(self):
        """Initialize UI components"""
        panel = QFrame()
        panel.setStyleSheet("background-color: #161b22; border-radius: 8px;")

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
        self.status_label = QLabel('Ready')
        self.status_label.setStyleSheet("color: #7c3aed; font-size: 10px; margin-top: 15px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Set main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(panel)

        # Initialize with current year
        self.on_year_changed(self.year_combo.currentText())

    def on_year_changed(self, year_text):
        """Update GP list when year changes"""
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
        """Load drivers when GP changes"""
        if self.gp_combo.currentData():
            self.load_session()

    def on_session_changed(self):
        """Reload drivers when session type changes"""
        if self.gp_combo.currentData():
            self.load_session()

    def load_session(self):
        """Load session and drivers"""
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
        """Callback when session is loaded"""
        self.current_session = session
        self.current_drivers = drivers_data

        # Populate driver combos
        self.driver1_combo.clear()
        self.driver2_combo.clear()

        for driver in drivers_data:
            self.driver1_combo.addItem(driver['display'], driver['abbreviation'])
            self.driver2_combo.addItem(driver['display'], driver['abbreviation'])

        # Select different drivers by default
        if len(drivers_data) >= 2:
            self.driver1_combo.setCurrentIndex(0)
            self.driver2_combo.setCurrentIndex(1)

        self.compare_btn.setEnabled(len(drivers_data) >= 2)
        self.status_label.setText(f'✓ {len(drivers_data)} drivers loaded')
        self.status_label.setStyleSheet("color: #7c3aed; font-size: 10px; margin-top: 15px;")

    def compare_fastest_laps(self):
        """Compare fastest laps of selected drivers"""
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
        """Callback when comparison is ready"""
        gp_name = self.gp_combo.currentText()
        session_type = self.session_combo.currentText()

        self.telemetry_canvas.plot_comparison(
            tel1, tel2, lap1_info, lap2_info, gp_name, session_type
        )

        self.status_label.setText('✓ Comparison complete')
        self.status_label.setStyleSheet("color: #7c3aed; font-size: 10px; margin-top: 15px;")

    def on_error(self, error_msg):
        """Handle errors"""
        self.status_label.setText(f'✗ Error: {error_msg}')
        self.status_label.setStyleSheet("color: #f85149; font-size: 10px; margin-top: 15px;")
        self.error.emit(error_msg)