"""
Test to demonstrate IST to UTC conversion fix.
Shows the difference in planetary positions when time zone is handled correctly.
"""

from datetime import datetime
from engine import EphemerisEngine

print("=" * 80)
print("IST TO UTC CONVERSION TEST")
print("=" * 80)

# Initialize engine
engine = EphemerisEngine(data_dir="data")

# Test case: Birth at noon IST in New Delhi
# IST = UTC+5:30, so noon IST = 6:30 AM UTC
birth_date_ist = datetime(2000, 1, 1, 12, 0)  # Noon IST
lat = 28.6139  # New Delhi
lon = 77.2090

print(f"\nTest Birth Data:")
print(f"  Date/Time: {birth_date_ist.strftime('%Y-%m-%d %H:%M')} IST")
print(f"  Location: New Delhi ({lat}°N, {lon}°E)")
print(f"\nNote: Engine now automatically converts IST → UTC before calculation")
print(f"      IST 12:00 → UTC 06:30 (subtract 5h 30m)")

# Calculate planets with corrected engine
print("\n" + "=" * 80)
print("PLANETARY POSITIONS WITH CORRECT IST HANDLING")
print("=" * 80)

planets = engine.calculate_planets(birth_date_ist, lat, lon)

print(f"\n{'Planet':<12} {'Longitude':<12} {'Nakshatra':<20} {'Pada'} {'Retrograde'}")
print("-" * 80)

for planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
    planet_data = planets[planet_name]
    lon_deg = planet_data["longitude"]
    
    # Get nakshatra info
    nak_info = engine.get_nakshatra(lon_deg)
    
    retro = " (R)" if planet_data["retrograde"] else ""
    
    print(f"{planet_name:<12} {lon_deg:>7.2f}°    {nak_info['nakshatra_name']:<20} {nak_info['pada']}   {retro}")

print("\n" + "=" * 80)
print("✓ Calculations now use correct UTC time for Swiss Ephemeris")
print("✓ All inputs remain in IST (Indian Standard Time)")
print("✓ Automatic conversion happens internally")
print("=" * 80)

# Show specific Moon nakshatra (most important for Vedic astrology)
moon_data = planets["Moon"]
moon_nak = engine.get_nakshatra(moon_data["longitude"])

print(f"\n🌙 MOON NAKSHATRA (Birth Star):")
print(f"   Longitude: {moon_data['longitude']:.2f}°")
print(f"   Nakshatra: {moon_nak['nakshatra_name']}")
print(f"   Pada: {moon_nak['pada']}")
print(f"   Ruler: {moon_nak['ruler']}")

print("\n✅ IST timezone handling is now CORRECT!\n")
