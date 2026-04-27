"""
Test Skyfield ephemeris with Shrey's birth data.
"""

from datetime import datetime
from engine.ephemeris_skyfield import EphemerisEngineSkyfield

print("=" * 80)
print("TESTING SKYFIELD EPHEMERIS ENGINE")
print("=" * 80)

# Initialize engine
print("\nInitializing Skyfield ephemeris engine...")
engine = EphemerisEngineSkyfield(data_dir="data")
print("✓ Engine initialized")

# Birth data (IST)
birth_date = datetime(1998, 7, 11, 18, 37)
lat = 13.0072  # Hassan, Karnataka
lon = 76.1004

print(f"\nBirth Data:")
print(f"  Date/Time: {birth_date.strftime('%Y-%m-%d %H:%M')} IST")
print(f"  Location: Hassan, Karnataka ({lat}°N, {lon}°E)")

# Calculate planets
print("\nCalculating planetary positions...")
planets = engine.calculate_planets(birth_date, lat, lon)

print("\n" + "=" * 80)
print("PLANETARY POSITIONS (Sidereal/Lahiri)")
print("=" * 80)

for planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
    planet_data = planets[planet_name]
    lon_deg = planet_data["longitude"]
    
    # Get nakshatra info
    nak_info = engine.get_nakshatra(lon_deg)
    
    # Determine sign
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_index = int(lon_deg / 30)
    sign_name = signs[sign_index]
    deg_in_sign = lon_deg % 30
    
    retro = " (R)" if planet_data["retrograde"] else ""
    
    print(f"{planet_name:<12} : {sign_name:<12} {deg_in_sign:5.2f}° | "
          f"{nak_info['nakshatra_name']:<20} | Pada {nak_info['pada']}{retro}")

# Check specific values
print("\n" + "=" * 80)
print("VERIFICATION AGAINST PROFESSIONAL CHART")
print("=" * 80)

moon_data = planets["Moon"]
moon_nak = engine.get_nakshatra(moon_data["longitude"])
moon_sign_idx = int(moon_data["longitude"] / 30)
moon_sign = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"][moon_sign_idx]

sun_data = planets["Sun"]
sun_nak = engine.get_nakshatra(sun_data["longitude"])
sun_sign_idx = int(sun_data["longitude"] / 30)
sun_sign = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"][sun_sign_idx]

print(f"\nMoon:")
print(f"  Expected: Capricorn in Sravana")
print(f"  Got:      {moon_sign} in {moon_nak['nakshatra_name']}")
print(f"  Match: {'✓ YES!' if moon_sign == 'Capricorn' and 'Sra' in moon_nak['nakshatra_name'] else '✗ NO'}")

print(f"\nSun:")
print(f"  Expected: Gemini in Punarvasu")
print(f"  Got:      {sun_sign} in {sun_nak['nakshatra_name']}")
print(f"  Match: {'✓ YES!' if sun_sign == 'Gemini' and 'Punar' in sun_nak['nakshatra_name'] else '✗ NO'}")

print("\n" + "=" * 80)
