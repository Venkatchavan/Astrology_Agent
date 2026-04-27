"""
Mock Swiss Ephemeris module for demonstration when pyswisseph is not available.
This allows the system to run for testing without requiring C++ build tools.
"""

# Constants
SUN = 0
MOON = 1
MERCURY = 2
VENUS = 3
MARS = 4
JUPITER = 5
SATURN = 6
MEAN_NODE = 11  # Rahu

# Ayanamsa
SIDM_LAHIRI = 1

# Flags
FLG_SWIEPH = 2
FLG_SPEED = 256

_ayanamsa_mode = None


def set_sid_mode(mode):
    """Set sidereal mode."""
    global _ayanamsa_mode
    _ayanamsa_mode = mode


def julday(year, month, day, hour):
    """Calculate Julian Day (simplified)."""
    from datetime import datetime
    dt = datetime(year, month, day, int(hour), int((hour % 1) * 60))
    base = datetime(2000, 1, 1, 12, 0)
    delta = (dt - base).total_seconds() / 86400
    return 2451545.0 + delta


def get_ayanamsa(jd):
    """Get ayanamsa value (Lahiri) for given Julian Day."""
    # Simplified calculation for demonstration
    # Real Lahiri ayanamsa for J2000 is approximately 23.85 degrees
    # and increases by about 50.3 arc seconds per year
    days_from_j2000 = jd - 2451545.0
    years_from_j2000 = days_from_j2000 / 365.25
    ayanamsa = 23.85 + (years_from_j2000 * 50.3 / 3600)
    return ayanamsa


def calc_ut(jd, planet_id, flags):
    """
    Calculate planet position (MOCK VERSION).
    Returns: ([longitude, latitude, distance, speed_lon, speed_lat, speed_dist], return_flag)
    """
    import math
    
    # Mock positions based on Julian Day
    # These are approximate and for demonstration only
    days_from_j2000 = jd - 2451545.0
    
    # Different speeds for each planet (degrees per day approximately)
    speeds = {
        SUN: 0.9856,      # ~1 degree/day
        MOON: 13.176,     # ~13 degrees/day
        MERCURY: 1.383,   # Variable
        VENUS: 1.602,     # Variable
        MARS: 0.524,      # Slower
        JUPITER: 0.083,   # Much slower
        SATURN: 0.033,    # Very slow
        MEAN_NODE: -0.053 # Retrograde (Rahu)
    }
    
    # Starting positions (for Dec 15, 2025)
    base_positions = {
        SUN: 248.5,       # Sagittarius
        MOON: 145.0,      # Virgo
        MERCURY: 260.0,   # Sagittarius
        VENUS: 290.0,     # Capricorn
        MARS: 115.0,      # Cancer
        JUPITER: 55.0,    # Taurus
        SATURN: 340.0,    # Pisces
        MEAN_NODE: 15.0   # Aries (Rahu)
    }
    
    # Calculate current position
    speed = speeds.get(planet_id, 0.5)
    base_pos = base_positions.get(planet_id, 0.0)
    
    # Add some variation
    longitude = (base_pos + (days_from_j2000 * speed)) % 360
    
    # Add small retrograde effect for outer planets
    if planet_id in [MARS, JUPITER, SATURN]:
        retrograde_cycle = math.sin(days_from_j2000 / 100) * 0.1
        if retrograde_cycle < -0.05:
            speed = -abs(speed) * 0.3  # Retrograde motion
    
    # Return format: [lon, lat, dist, speed_lon, speed_lat, speed_dist]
    position = [
        longitude,           # Tropical longitude
        0.0,                # Latitude
        1.0,                # Distance (AU)
        speed,              # Daily motion in longitude
        0.0,                # Daily motion in latitude
        0.0                 # Daily motion in distance
    ]
    
    return (position, 0)  # (position_array, return_flag)


# Print warning that this is a mock
print("⚠️  WARNING: Using MOCK Swiss Ephemeris")
print("   This is for demonstration only. Results are approximate.")
print("   For production use, install pyswisseph with C++ build tools:")
print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")
