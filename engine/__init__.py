"""
Astrological Agent - Engine Module
Mathematical core for astronomical calculations and data mapping.
"""

# Use Skyfield (NASA JPL) as the primary ephemeris engine
# Pure Python, no C++ compilation needed, highly accurate
from .ephemeris_skyfield import EphemerisEngineSkyfield as EphemerisEngine
from .data_loader import DataLoader, get_data_loader
from .dasha_engine import DashaEngine
from .numerology import NumerologyEngine
from .prediction_engine import PredictionEngine

__all__ = ["EphemerisEngine", "DataLoader", "get_data_loader", "DashaEngine", "NumerologyEngine", "PredictionEngine"]
