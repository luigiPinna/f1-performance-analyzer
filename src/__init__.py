"""
F1 Analytics - Modular architecture for F1 telemetry analysis
"""

from .data_service import F1DataService
from .functionalities import BaseFunctionality, FastestLapComparison, AVAILABLE_FUNCTIONALITIES
from .constants import COLORS, STREAMLIT_DARK_THEME, PLOTLY_DARK_CONFIG

__version__ = "1.0.0"
__all__ = [
    'F1DataService',
    'BaseFunctionality',
    'FastestLapComparison',
    'AVAILABLE_FUNCTIONALITIES',
    'COLORS',
    'STREAMLIT_DARK_THEME',
    'PLOTLY_DARK_CONFIG'
]
