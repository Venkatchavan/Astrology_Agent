"""
Ephemeris Engine using Skyfield (NASA JPL Ephemeris)
Alternative to Swiss Ephemeris - Pure Python, no C++ compilation needed.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import csv

from skyfield.api import load, wgs84
from skyfield import almanac


class EphemerisEngineSkyfield:
    """
    Ephemeris engine using Skyfield for planetary calculations.
    Uses NASA JPL ephemeris data - highly accurate.
    """

    # Ayanamsa value for Lahiri (as of 2000.0): 23.85°
    # Rate: ~50.27" per year = 0.01397°/year
    LAHIRI_BASE = 23.85  # degrees at J2000.0 (Jan 1, 2000)
    LAHIRI_RATE = 0.01397  # degrees per year
    J2000 = 2000.0

    def __init__(self, data_dir: str = "data"):
        """Initialize Skyfield ephemeris engine."""
        self.data_dir = Path(data_dir)
        
        # Load Skyfield data
        self.ts = load.timescale()
        self.eph = load('de421.bsp')  # JPL ephemeris
        
        # Define planets
        self.sun = self.eph['sun']
        self.moon = self.eph['moon']
        self.earth = self.eph['earth']
        self.mercury = self.eph['mercury']
        self.venus = self.eph['venus']
        self.mars = self.eph['mars']
        self.jupiter = self.eph['jupiter barycenter']
        self.saturn = self.eph['saturn barycenter']
        
        # Load nakshatra data
        self._load_nakshatra_data()

    def _load_nakshatra_data(self) -> None:
        """Load nakshatra longitude ranges and rulers from CSV files."""
        # Load 27 nakshatras
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

    def _calculate_ayanamsa(self, year: float) -> float:
        """
        Calculate Lahiri ayanamsa for given year.
        
        Args:
            year: Decimal year (e.g., 1998.5 for mid-1998)
        
        Returns:
            Ayanamsa in degrees
        """
        years_since_j2000 = year - self.J2000
        ayanamsa = self.LAHIRI_BASE + (self.LAHIRI_RATE * years_since_j2000)
        return ayanamsa

    def _ecliptic_longitude(self, position) -> float:
        """
        Convert rectangular coordinates to ecliptic longitude.
        
        Args:
            position: Skyfield position object
        
        Returns:
            Ecliptic longitude in degrees (0-360)
        """
        lat, lon, distance = position.ecliptic_latlon()
        return lon.degrees % 360

    def calculate_planets(
        self, dt: datetime, lat: float, lon: float
    ) -> Dict[str, Dict]:
        """
        Calculate sidereal positions of all major planets using Skyfield.

        Args:
            dt: Date and time of calculation (IST - Indian Standard Time)
            lat: Latitude of observer
            lon: Longitude of observer

        Returns:
            Dictionary mapping planet names to position data
        """
        # Convert IST to UTC (subtract 5 hours 30 minutes)
        if dt.tzinfo is not None:
            raise ValueError(
                "datetime must be a naive IST datetime (no tzinfo). "
                "Do NOT pass UTC or any timezone-aware datetime. "
                "Pass the local IST birth time directly."
            )
        utc_dt = dt - timedelta(hours=5, minutes=30)
        
        # Create Skyfield time object
        t = self.ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, 
                        utc_dt.hour, utc_dt.minute, utc_dt.second)
        
        # Calculate decimal year for ayanamsa
        day_of_year = utc_dt.timetuple().tm_yday
        days_in_year = 366 if utc_dt.year % 4 == 0 else 365
        decimal_year = utc_dt.year + (day_of_year / days_in_year)
        
        # Get ayanamsa
        ayanamsa = self._calculate_ayanamsa(decimal_year)
        
        results = {}

        # Use geocentric positions (from Earth's centre) — standard in astrology.
        # Topocentric positions introduce a significant parallax error for the Moon
        # (up to ~57' = 0.95°) and are NOT used by any Vedic astrology software.

        # Calculate each planet
        planets = {
            "Sun": self.sun,
            "Moon": self.moon,
            "Mercury": self.mercury,
            "Venus": self.venus,
            "Mars": self.mars,
            "Jupiter": self.jupiter,
            "Saturn": self.saturn
        }

        for planet_name, planet_obj in planets.items():
            # Geocentric apparent position
            astrometric = self.earth.at(t).observe(planet_obj)
            apparent = astrometric.apparent()

            # Get tropical longitude
            tropical_lon = self._ecliptic_longitude(apparent)

            # Convert to sidereal
            sidereal_lon = (tropical_lon - ayanamsa) % 360

            # Calculate speed (approximate - 1 day difference)
            t_next = self.ts.utc(utc_dt.year, utc_dt.month, utc_dt.day + 1,
                                utc_dt.hour, utc_dt.minute, utc_dt.second)
            astrometric_next = self.earth.at(t_next).observe(planet_obj)
            apparent_next = astrometric_next.apparent()
            tropical_lon_next = self._ecliptic_longitude(apparent_next)
            
            # Daily motion
            speed = tropical_lon_next - tropical_lon
            if speed > 180:
                speed -= 360
            elif speed < -180:
                speed += 360
            
            is_retrograde = speed < 0
            
            results[planet_name] = {
                "longitude": sidereal_lon,
                "speed": speed,
                "retrograde": is_retrograde
            }
        
        # Calculate Rahu (Mean North Node)
        # Standard IAU formula: Ω = 125.04452 − 0.0529539°/day × d
        # where d = Julian days from J2000.0  (NOT years — 0.0529539 is deg/day)
        d_j2000 = t.tt - 2451545.0
        mean_node_lon = (125.044522 - 0.0529539 * d_j2000) % 360
        rahu_sidereal = (mean_node_lon - ayanamsa) % 360
        
        results["Rahu"] = {
            "longitude": rahu_sidereal,
            "speed": -0.053,  # Rahu always retrograde, mean motion
            "retrograde": True
        }
        
        # Calculate Ketu (180° opposite to Rahu)
        ketu_sidereal = (rahu_sidereal + 180) % 360
        
        results["Ketu"] = {
            "longitude": ketu_sidereal,
            "speed": -0.053,
            "retrograde": True
        }
        
        return results

    def get_nakshatra(self, longitude: float) -> Dict[str, any]:
        """
        Determine the nakshatra and pada for a given sidereal longitude.

        Args:
            longitude: Sidereal longitude in degrees (0-360)

        Returns:
            Dictionary containing nakshatra info
        """
        longitude = longitude % 360

        # Find nakshatra
        nakshatra_info = None
        for nak in self.nakshatras:
            if nak["start"] <= longitude < nak["end"]:
                nakshatra_info = nak
                break

        if nakshatra_info is None:
            nakshatra_info = self.nakshatras[0]  # Ashwini

        # Find pada
        pada_num = None
        for pada in self.padas:
            if (pada["nakshatra_index"] == nakshatra_info["index"] and
                pada["start"] <= longitude < pada["end"]):
                pada_num = pada["pada"]
                break

        if pada_num is None:
            offset_in_nakshatra = longitude - nakshatra_info["start"]
            pada_num = int(offset_in_nakshatra / 3.333333) + 1
            pada_num = min(pada_num, 4)

        nakshatra_name = nakshatra_info["name"]
        ruler = self.nakshatra_rulers.get(nakshatra_name, "Unknown")

        return {
            "nakshatra_index": nakshatra_info["index"],
            "nakshatra_name": nakshatra_name,
            "ruler": ruler,
            "pada": pada_num,
            "longitude": longitude
        }

    def calculate_chart(
        self, dt: datetime, lat: float, lon: float
    ) -> Dict[str, Dict]:
        """
        Calculate complete chart with planets and their nakshatras.

        Args:
            dt: Date and time of birth (IST - Indian Standard Time)
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

    def calculate_navamsa(self, longitude: float) -> Dict:
        """
        Calculate D9 (Navamsa) position for a given longitude.
        
        Args:
            longitude: Sidereal longitude in degrees
        
        Returns:
            Dictionary with D9 sign, element, and vargottama status
        """
        # D1 sign
        d1_sign_index = int(longitude / 30)
        
        # Navamsa calculation
        # Each sign (30°) divided into 9 parts (3.333° each)
        navamsa_index = int(longitude / (30 / 9))  # 0-107
        d9_sign_index = navamsa_index % 12
        
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        elements = ["Fire", "Earth", "Air", "Water"]
        element_map = {
            "Aries": "Fire", "Taurus": "Earth", "Gemini": "Air", "Cancer": "Water",
            "Leo": "Fire", "Virgo": "Earth", "Libra": "Air", "Scorpio": "Water",
            "Sagittarius": "Fire", "Capricorn": "Earth", "Aquarius": "Air", "Pisces": "Water"
        }
        
        d1_sign = signs[d1_sign_index]
        d9_sign = signs[d9_sign_index]
        
        # Check Vargottama (same sign in D1 and D9)
        vargottama = (d1_sign == d9_sign)
        
        return {
            "d1_sign": d1_sign,
            "d9_sign": d9_sign,
            "element": element_map[d1_sign],
            "vargottama": vargottama
        }

    def calculate_ascendant(self, dt: datetime, lat: float, lon: float) -> dict:
        """
        Calculate the Ascendant (Lagna) — sidereal longitude, Lahiri ayanamsa.

        The Ascendant is the ecliptic degree rising on the eastern horizon at
        the moment of birth.  Formula: standard oblique-angle ascendant from
        the Right Ascension of the MC (= Local Mean Sidereal Time).

        Args:
            dt:  Birth datetime (naive IST — no tzinfo)
            lat: Geographic latitude  (degrees, +N)
            lon: Geographic longitude (degrees, +E)

        Returns:
            Dict with keys: longitude, sign, degree, nakshatra, retrograde, speed
        """
        import math

        if dt.tzinfo is not None:
            raise ValueError(
                "datetime must be a naive IST datetime (no tzinfo). "
                "Pass the local IST birth time directly."
            )

        utc_dt = dt - timedelta(hours=5, minutes=30)
        t = self.ts.utc(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour, utc_dt.minute, utc_dt.second
        )

        # GMST (hours) → RAMC / Local Sidereal Time (degrees)
        ramc_deg = (t.gmst * 15.0 + lon) % 360

        # Obliquity of ecliptic — IAU 1980 formula (degrees)
        T = (t.tt - 2451545.0) / 36525.0
        eps = 23.439291 - 0.013004 * T

        # Standard ascendant formula
        ramc = math.radians(ramc_deg)
        e    = math.radians(eps)
        phi  = math.radians(lat)

        y = -math.cos(ramc)
        x =  math.sin(ramc) * math.cos(e) + math.tan(phi) * math.sin(e)

        # atan2(y, x) can return the Descendant (western horizon) when x < 0.
        # Adding 180° when denominator < 0 gives the correct Ascendant (east).
        asc_tropical = (math.degrees(math.atan2(y, x)) + (180.0 if x < 0 else 0.0)) % 360

        # Lahiri ayanamsa
        day_of_year   = utc_dt.timetuple().tm_yday
        days_in_year  = 366 if utc_dt.year % 4 == 0 else 365
        decimal_year  = utc_dt.year + (day_of_year / days_in_year)
        ayanamsa      = self._calculate_ayanamsa(decimal_year)

        asc_sidereal  = (asc_tropical - ayanamsa) % 360

        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign         = signs[int(asc_sidereal / 30)]
        degree_in_sign = asc_sidereal % 30

        return {
            "longitude":  asc_sidereal,
            "sign":       sign,
            "degree":     degree_in_sign,
            "nakshatra":  self.get_nakshatra(asc_sidereal),
            "retrograde": False,
            "speed":      0.0,
        }

    def get_sign_name(self, longitude: float) -> str:
        """
        Get zodiac sign name for a given longitude.
        
        Args:
            longitude: Sidereal longitude in degrees
        
        Returns:
            Sign name
        """
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign_index = int(longitude / 30) % 12
        return signs[sign_index]
