"""
Ephemeris Engine - Core Mathematical Layer
Handles astronomical calculations using Swiss Ephemeris (sidereal/Lahiri).

IMPORTANT: All datetime inputs should be in IST (Indian Standard Time).
This module automatically converts IST to UTC for Swiss Ephemeris calculations.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import csv

import swisseph as swe


class EphemerisEngine:
    """
    Core engine for calculating planetary positions and mapping to nakshatras.
    Uses Lahiri Ayanamsa (sidereal zodiac) for all calculations.
    """

    # Swiss Ephemeris planet constants
    PLANETS = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,  # North Node
    }

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the ephemeris engine and load nakshatra data.

        Args:
            data_dir: Path to directory containing nakshatra CSV files
        """
        # Set Swiss Ephemeris to use Lahiri Ayanamsa (sidereal)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # Load nakshatra data
        self.data_dir = Path(data_dir)
        self._load_nakshatra_data()

    def _load_nakshatra_data(self) -> None:
        """Load nakshatra longitude ranges and rulers from CSV files."""
        # Load 27 nakshatras with basic info
        self.nakshatras: List[Dict] = []
        nakshatra_file = self.data_dir / "nakshatra_longitudes_27.csv"

        with open(nakshatra_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.nakshatras.append({
                    "index": int(row["index"]),
                    "name": row["nakshatra"],
                    "start": float(row["start_deg_ecliptic"]),
                    "end": float(row["end_deg_ecliptic"])
                })

        # Load rulers
        self.nakshatra_rulers: Dict[str, str] = {}
        ruler_file = self.data_dir / "nakshatra_rulers.csv"

        with open(ruler_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.nakshatra_rulers[row["nakshatra"]] = row["ruler"]

        # Load 108 padas
        self.padas: List[Dict] = []
        pada_file = self.data_dir / "nakshatra_padas_108.csv"

        with open(pada_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.padas.append({
                    "nakshatra_index": int(row["nakshatra_index"]),
                    "nakshatra": row["nakshatra"],
                    "pada": int(row["pada"]),
                    "start": float(row["start_deg_ecliptic"]),
                    "end": float(row["end_deg_ecliptic"])
                })

    def calculate_planets(
        self, dt: datetime, lat: float, lon: float
    ) -> Dict[str, Dict]:
        """
        Calculate sidereal positions of all major planets.

        Args:
            dt: Date and time of calculation (IST - Indian Standard Time)
            lat: Latitude of observer
            lon: Longitude of observer

        Returns:
            Dictionary mapping planet names to position data including:
            - longitude: Sidereal longitude (0-360 degrees)
            - speed: Daily motion in degrees
            - retrograde: Boolean indicating retrograde motion
        """
        # Convert IST to UTC (subtract 5 hours 30 minutes)
        # Swiss Ephemeris REQUIRES UTC for accurate calculations
        if dt.tzinfo is not None:
            raise ValueError(
                "datetime must be a naive IST datetime (no tzinfo). "
                "Do NOT pass UTC or any timezone-aware datetime. "
                "Pass the local IST birth time directly."
            )
        utc_dt = dt - timedelta(hours=5, minutes=30)
        
        # Convert UTC datetime to Julian Day
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0)

        # Calculate Ayanamsa for this date
        ayanamsa = swe.get_ayanamsa(jd)

        results = {}

        # Calculate each planet
        for planet_name, planet_id in self.PLANETS.items():
            # Calculate position with speed
            # FLG_SWIEPH: use Swiss Ephemeris
            # FLG_SPEED: calculate speed as well
            calc_result = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)

            tropical_lon = calc_result[0][0]  # Tropical longitude
            speed = calc_result[0][3]  # Daily motion in longitude

            # Convert tropical to sidereal using Lahiri ayanamsa
            sidereal_lon = tropical_lon - ayanamsa

            # Normalize to 0-360 range
            sidereal_lon = sidereal_lon % 360

            # Determine if retrograde (negative speed)
            is_retrograde = speed < 0

            results[planet_name] = {
                "longitude": sidereal_lon,
                "speed": speed,
                "retrograde": is_retrograde
            }

        # Calculate Ketu (South Node) - 180 degrees opposite to Rahu
        rahu_lon = results["Rahu"]["longitude"]
        ketu_lon = (rahu_lon + 180) % 360

        results["Ketu"] = {
            "longitude": ketu_lon,
            "speed": -results["Rahu"]["speed"],  # Opposite motion
            "retrograde": results["Rahu"]["retrograde"]
        }

        return results

    def get_nakshatra(self, longitude: float) -> Dict[str, any]:
        """
        Determine the nakshatra and pada for a given sidereal longitude.

        Args:
            longitude: Sidereal longitude in degrees (0-360)

        Returns:
            Dictionary containing:
            - nakshatra_index: Index (1-27)
            - nakshatra_name: Name of the nakshatra
            - ruler: Ruling planet
            - pada: Pada number (1-4)
        """
        # Normalize longitude to 0-360 range
        longitude = longitude % 360

        # Find the nakshatra (from 27 nakshatras)
        nakshatra_info = None
        for nak in self.nakshatras:
            # Handle the 360->0 crossover (Revati to Ashwini)
            if nak["start"] <= longitude < nak["end"]:
                nakshatra_info = nak
                break

        if nakshatra_info is None:
            # Edge case: exactly at 360 degrees = 0 degrees = start of Ashwini
            nakshatra_info = self.nakshatras[0]

        # Find the pada (from 108 padas)
        pada_num = None
        for pada in self.padas:
            if (pada["nakshatra_index"] == nakshatra_info["index"] and
                pada["start"] <= longitude < pada["end"]):
                pada_num = pada["pada"]
                break

        # Fallback to pada calculation if not found in lookup
        if pada_num is None:
            # Each nakshatra is 13.333... degrees, divided into 4 padas
            offset_in_nakshatra = longitude - nakshatra_info["start"]
            pada_num = int(offset_in_nakshatra / 3.333333) + 1
            pada_num = min(pada_num, 4)  # Ensure it's 1-4

        nakshatra_name = nakshatra_info["name"]
        ruler = self.nakshatra_rulers.get(nakshatra_name, "Unknown")

        return {
            "nakshatra_index": nakshatra_info["index"],
            "nakshatra_name": nakshatra_name,
            "ruler": ruler,
            "pada": pada_num,
            "longitude": longitude
        }

    def get_sign_name(self, longitude: float) -> str:
        """
        Converts absolute longitude (0-360) to Vedic Sign Name.
        
        Args:
            longitude: Sidereal longitude in degrees (0-360)
        
        Returns:
            Name of the zodiac sign (Aries, Taurus, etc.)
        """
        zodiac = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        # Integer division by 30 gives the index (0 for Aries, 1 for Taurus, etc.)
        index = int(longitude / 30) % 12
        return zodiac[index]
    
    def get_sign_index(self, longitude: float) -> int:
        """
        Get the zodiac sign index (0-11) for a given longitude.
        
        Args:
            longitude: Sidereal longitude in degrees (0-360)
        
        Returns:
            Sign index (0=Aries, 1=Taurus, ..., 11=Pisces)
        """
        return int(longitude / 30) % 12
    
    def calculate_navamsa(self, longitude: float) -> Dict[str, any]:
        """
        Calculate Navamsa (D9) position for a given planetary longitude.
        
        The Navamsa is the 9th divisional chart, considered the "fruit" of the birth chart.
        Each sign (30°) is divided into 9 parts of 3°20' each.
        
        Mapping Rules (based on sign element):
        - Fire Signs (Aries, Leo, Sagittarius): Start from Aries
        - Earth Signs (Taurus, Virgo, Capricorn): Start from Capricorn
        - Air Signs (Gemini, Libra, Aquarius): Start from Libra
        - Water Signs (Cancer, Scorpio, Pisces): Start from Cancer
        
        Args:
            longitude: Sidereal longitude in degrees (0-360)
        
        Returns:
            Dictionary containing:
            - d1_sign: Birth chart (D1) sign name
            - d1_sign_index: D1 sign index (0-11)
            - d9_sign: Navamsa (D9) sign name
            - d9_sign_index: D9 sign index (0-11)
            - navamsa_pada: Which pada (1-9) within the D1 sign
            - d9_longitude: Approximate longitude in D9 chart
            - vargottama: True if D1 and D9 signs match (supreme strength)
        """
        # Normalize longitude
        longitude = longitude % 360
        
        # Get D1 (birth chart) sign
        d1_sign_index = self.get_sign_index(longitude)
        d1_sign_name = self.get_sign_name(longitude)
        
        # Calculate position within the sign (0-30 degrees)
        position_in_sign = longitude % 30
        
        # Determine which navamsa pada (1-9) within the sign
        # Each pada is 3°20' = 3.333... degrees
        navamsa_pada = int(position_in_sign / 3.333333) + 1
        navamsa_pada = min(navamsa_pada, 9)  # Ensure 1-9 range
        
        # Determine element of D1 sign
        # Fire: 0,4,8 (Aries, Leo, Sag)
        # Earth: 1,5,9 (Taurus, Virgo, Cap)
        # Air: 2,6,10 (Gemini, Libra, Aquarius)
        # Water: 3,7,11 (Cancer, Scorpio, Pisces)
        element_map = {
            0: "Fire", 1: "Earth", 2: "Air", 3: "Water",
            4: "Fire", 5: "Earth", 6: "Air", 7: "Water",
            8: "Fire", 9: "Earth", 10: "Air", 11: "Water"
        }
        
        element = element_map[d1_sign_index]
        
        # Starting sign for navamsa based on element
        start_sign_map = {
            "Fire": 0,   # Aries
            "Earth": 9,  # Capricorn
            "Air": 6,    # Libra
            "Water": 3   # Cancer
        }
        
        start_sign = start_sign_map[element]
        
        # Calculate D9 sign index
        # Add (navamsa_pada - 1) to the starting sign, modulo 12
        d9_sign_index = (start_sign + (navamsa_pada - 1)) % 12
        d9_sign_name = self.get_sign_name(d9_sign_index * 30)
        
        # Calculate approximate D9 longitude
        # Each navamsa pada represents a full sign in D9
        # Position within the pada translates to position within D9 sign
        position_in_pada = position_in_sign % 3.333333
        position_in_d9_sign = (position_in_pada / 3.333333) * 30
        d9_longitude = (d9_sign_index * 30) + position_in_d9_sign
        
        # Check for Vargottama (supreme strength)
        # Planet is in same sign in both D1 and D9
        vargottama = (d1_sign_index == d9_sign_index)
        
        return {
            "d1_sign": d1_sign_name,
            "d1_sign_index": d1_sign_index,
            "d9_sign": d9_sign_name,
            "d9_sign_index": d9_sign_index,
            "navamsa_pada": navamsa_pada,
            "d9_longitude": d9_longitude,
            "vargottama": vargottama,
            "element": element
        }

    def calculate_chart(
        self, dt: datetime, lat: float, lon: float
    ) -> Dict[str, Dict]:
        """
        Calculate complete chart with planets and their nakshatras.

        Args:
            dt: Date and time of birth/event (UTC)
            lat: Latitude of location
            lon: Longitude of location

        Returns:
            Dictionary mapping planet names to complete position data including
            nakshatra information.
        """
        planets = self.calculate_planets(dt, lat, lon)

        # Enhance with nakshatra data
        chart = {}
        for planet_name, planet_data in planets.items():
            nakshatra_data = self.get_nakshatra(planet_data["longitude"])

            chart[planet_name] = {
                **planet_data,
                "nakshatra": nakshatra_data
            }

        return chart
