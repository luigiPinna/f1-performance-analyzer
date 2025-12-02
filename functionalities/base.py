from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal


class BaseFunctionality(QWidget):
    """Base class for all analysis functionalities"""

    error = pyqtSignal(str)

    def __init__(self, calendar_data, telemetry_canvas):
        super().__init__()
        self.calendar_data = calendar_data
        self.telemetry_canvas = telemetry_canvas

    def get_name(self):
        """Return functionality name"""
        raise NotImplementedError("Subclasses must implement get_name()")