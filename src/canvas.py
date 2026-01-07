from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QFrame, QSizePolicy, QMessageBox)
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from workers import CalendarLoaderThread
from functionalities.fastest_lap_comparison import FastestLapComparison

plt.style.use('dark_background')


class TelemetryCanvas(FigureCanvas):
    """Canvas for displaying telemetry charts"""

    def __init__(self):
        self.fig = Figure(figsize=(14, 10), facecolor='#0d1117')
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.show_welcome()

    def show_welcome(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5,
                'F1 PERFORMANCE ANALYZER\n\n'
                'Select a functionality to begin analysis',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=16, color='#58a6ff', fontweight='bold')
        ax.set_facecolor('#0d1117')
        ax.axis('off')
        self.draw()

    def show_loading(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Loading data...',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=18, color='#58a6ff', fontweight='bold')
        ax.set_facecolor('#0d1117')
        ax.axis('off')
        self.draw()

    def plot_comparison(self, tel1, tel2, lap1_info, lap2_info, gp_name, session_type):
        """Plot telemetry comparison between two laps"""
        self.fig.clear()

        # F1 TV style colors
        color1, color2 = '#58a6ff', '#f85149'

        # Layout: 3 vertical charts
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

        # Header with gap info
        gap = abs(lap1_info['lap_time'] - lap2_info['lap_time'])
        faster = lap1_info['driver'] if lap1_info['lap_time'] < lap2_info['lap_time'] else lap2_info['driver']

        self.fig.suptitle(
            f"TELEMETRY COMPARISON | {gp_name} | {session_type}\n"
            f"{lap1_info['driver']} vs {lap2_info['driver']} | Gap: {gap:.3f}s (Faster: {faster})",
            fontsize=14, fontweight='bold', y=0.98)

        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.88, hspace=0.35)
        self.draw()


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.calendar_data = {}
        self.current_functionality = None
        self.init_ui()
        self.load_calendar()

    def init_ui(self):
        self.setWindowTitle('F1 Performance Analyzer')
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
                background-color: #161b22;
                border: 1px solid #58a6ff;
                border-radius: 6px;
                selection-background-color: #58a6ff;
                selection-color: #0d1117;
                color: #f0f6fc;
                padding: 0px;
                outline: none;
                min-width: 200px;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 15px;
                border-radius: 0px;
                min-height: 28px;
                font-size: 11px;
            }
            QComboBox QAbstractItemView::item:first {
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QComboBox QAbstractItemView::item:last {
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #30363d;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #58a6ff;
                color: #0d1117;
                font-weight: bold;
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
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # TOP: Functionality selector
        self.create_functionality_selector(main_layout)

        # BOTTOM: Content area (control panel + canvas)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Control panel container
        self.control_panel_frame = QFrame()
        self.control_panel_frame.setFixedWidth(400)
        self.control_panel_layout = QVBoxLayout(self.control_panel_frame)
        self.control_panel_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.control_panel_frame, stretch=1)

        # Telemetry canvas
        self.telemetry_canvas = TelemetryCanvas()
        content_layout.addWidget(self.telemetry_canvas, stretch=4)

        main_layout.addLayout(content_layout)

    def create_functionality_selector(self, parent_layout):
        """Create functionality selection dropdown"""
        selector_frame = QFrame()
        selector_frame.setStyleSheet("background-color: #161b22; padding: 15px;")
        selector_layout = QHBoxLayout(selector_frame)
        selector_layout.setContentsMargins(15, 15, 15, 15)

        label = QLabel('FUNCTIONALITY:')
        label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        label.setStyleSheet("color: #8b949e;")
        selector_layout.addWidget(label)

        self.functionality_combo = QComboBox()
        self.functionality_combo.addItem('Fastest Lap Comparison')
        self.functionality_combo.setFixedWidth(300)
        self.functionality_combo.currentTextChanged.connect(self.on_functionality_changed)
        selector_layout.addWidget(self.functionality_combo)

        selector_layout.addStretch()
        parent_layout.addWidget(selector_frame)

    def load_calendar(self):
        """Load race calendar"""
        self.calendar_thread = CalendarLoaderThread()
        self.calendar_thread.finished.connect(self.on_calendar_loaded)
        self.calendar_thread.error.connect(self.on_error)
        self.calendar_thread.start()

    def on_calendar_loaded(self, calendar_data):
        """Callback when calendar is loaded"""
        self.calendar_data = calendar_data
        # Initialize first functionality
        self.on_functionality_changed(self.functionality_combo.currentText())

    def on_functionality_changed(self, functionality_name):
        """Switch functionality"""
        if not self.calendar_data:
            return

        # Clear current functionality
        if self.current_functionality:
            self.current_functionality.setParent(None)
            self.current_functionality.deleteLater()

        # Create new functionality
        if functionality_name == 'Fastest Lap Comparison':
            self.current_functionality = FastestLapComparison(
                self.calendar_data,
                self.telemetry_canvas
            )
            self.current_functionality.error.connect(self.on_error)

        # Add to control panel
        self.control_panel_layout.addWidget(self.current_functionality)

    def on_error(self, error_msg):
        """Handle errors"""
        QMessageBox.critical(self, 'Error', error_msg)