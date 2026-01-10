"""
Functionalities module - Plugin system for F1 analysis tools
"""

from .base import BaseFunctionality
from .fastest_lap_comparison import FastestLapComparison

# Register all available functionalities here
AVAILABLE_FUNCTIONALITIES = [
    FastestLapComparison,
    # Add new functionalities here
]

__all__ = ['BaseFunctionality', 'FastestLapComparison', 'AVAILABLE_FUNCTIONALITIES']
