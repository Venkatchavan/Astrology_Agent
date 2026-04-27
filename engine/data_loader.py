"""
Data Loader Module
Handles loading and managing static data files (nakshatras, numerology, etc.)
"""

import csv
from pathlib import Path
from typing import Dict, List


class DataLoader:
    """
    Centralized data loader for all CSV files.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        
        # Loaded data caches
        self._nakshatras = None
        self._padas = None
        self._nakshatra_rulers = None
        self._numerology_chaldean = None
        self._numerology_pythagorean = None
    
    @property
    def nakshatras(self) -> List[Dict]:
        """Load and cache nakshatra longitudes (27 nakshatras)."""
        if self._nakshatras is None:
            self._nakshatras = []
            filepath = self.data_dir / "nakshatra_longitudes_27.csv"
            
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._nakshatras.append({
                        "index": int(row["index"]),
                        "name": row["nakshatra"],
                        "start": float(row["start_deg_ecliptic"]),
                        "end": float(row["end_deg_ecliptic"])
                    })
        
        return self._nakshatras
    
    @property
    def padas(self) -> List[Dict]:
        """Load and cache nakshatra padas (108 padas)."""
        if self._padas is None:
            self._padas = []
            filepath = self.data_dir / "nakshatra_padas_108.csv"
            
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._padas.append({
                        "nakshatra_index": int(row["nakshatra_index"]),
                        "nakshatra": row["nakshatra"],
                        "pada": int(row["pada"]),
                        "start": float(row["start_deg_ecliptic"]),
                        "end": float(row["end_deg_ecliptic"])
                    })
        
        return self._padas
    
    @property
    def nakshatra_rulers(self) -> Dict[str, str]:
        """Load and cache nakshatra rulers."""
        if self._nakshatra_rulers is None:
            self._nakshatra_rulers = {}
            filepath = self.data_dir / "nakshatra_rulers.csv"
            
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._nakshatra_rulers[row["nakshatra"]] = row["ruler"]
        
        return self._nakshatra_rulers
    
    @property
    def numerology_chaldean(self) -> Dict:
        """Load and cache Chaldean numerology data."""
        if self._numerology_chaldean is None:
            self._numerology_chaldean = {}
            filepath = self.data_dir / "numerology_chaldean.csv"
            
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self._numerology_chaldean[row.get("letter", "")] = row
        
        return self._numerology_chaldean
    
    @property
    def numerology_pythagorean(self) -> Dict:
        """Load and cache Pythagorean numerology data."""
        if self._numerology_pythagorean is None:
            self._numerology_pythagorean = {}
            filepath = self.data_dir / "numerology_pythagorean.csv"
            
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self._numerology_pythagorean[row.get("letter", "")] = row
        
        return self._numerology_pythagorean
    
    def get_nakshatra_by_longitude(self, longitude: float) -> Dict:
        """
        Get nakshatra for a given longitude.
        
        Args:
            longitude: Sidereal longitude (0-360 degrees)
        
        Returns:
            Dictionary with nakshatra info
        """
        longitude = longitude % 360
        
        for nak in self.nakshatras:
            if nak["start"] <= longitude < nak["end"]:
                return {
                    "index": nak["index"],
                    "name": nak["name"],
                    "ruler": self.nakshatra_rulers.get(nak["name"], "Unknown"),
                    "start": nak["start"],
                    "end": nak["end"]
                }
        
        # Edge case: exactly 360 degrees = Ashwini
        return {
            "index": 1,
            "name": self.nakshatras[0]["name"],
            "ruler": self.nakshatra_rulers.get(self.nakshatras[0]["name"], "Unknown"),
            "start": 0.0,
            "end": 13.333333
        }
    
    def get_pada_by_longitude(self, longitude: float) -> int:
        """
        Get pada (1-4) for a given longitude.
        
        Args:
            longitude: Sidereal longitude (0-360 degrees)
        
        Returns:
            Pada number (1-4)
        """
        longitude = longitude % 360
        
        for pada in self.padas:
            if pada["start"] <= longitude < pada["end"]:
                return pada["pada"]
        
        # Fallback calculation
        nakshatra = self.get_nakshatra_by_longitude(longitude)
        offset_in_nakshatra = longitude - nakshatra["start"]
        pada_num = int(offset_in_nakshatra / 3.333333) + 1
        return min(pada_num, 4)


# Singleton instance
_data_loader = None


def get_data_loader(data_dir: str = "data") -> DataLoader:
    """
    Get singleton DataLoader instance.
    
    Args:
        data_dir: Directory containing CSV files
    
    Returns:
        DataLoader instance
    """
    global _data_loader
    
    if _data_loader is None:
        _data_loader = DataLoader(data_dir)
    
    return _data_loader
