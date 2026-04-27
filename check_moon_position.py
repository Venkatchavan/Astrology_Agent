"""Check actual Moon calculation from Skyfield"""
from datetime import datetime, timedelta
from engine.ephemeris_skyfield import EphemerisEngineSkyfield

# Birth data: July 11, 1998, 18:37 IST
birth_ist = datetime(1998, 7, 11, 18, 37, 0)
lat, lon = 13.0072, 76.1004

engine = EphemerisEngineSkyfield()

# Calculate planets
planets = engine.calculate_planets(birth_ist, lat, lon)

print("=" * 80)
print("SKYFIELD MOON CALCULATION")
print("=" * 80)
print(f"Birth Time IST: {birth_ist.strftime('%Y-%m-%d %H:%M')}")
print(f"Location: Hassan, Karnataka ({lat}, {lon})")
print()

moon_lon = planets['Moon']['longitude']
print(f"Moon Sidereal Longitude: {moon_lon:.4f}°")
print(f"Moon Degree in Sign: {moon_lon % 30:.4f}°")

# Get nakshatra from engine
nakshatra_info = engine.get_nakshatra(moon_lon)
print(f"Moon Nakshatra: {nakshatra_info['nakshatra_name']}")
print(f"Moon Nakshatra Pada: {nakshatra_info['pada']}")
print(f"Moon Nakshatra Ruler: {nakshatra_info['ruler']}")

print("\n" + "=" * 80)
print("REQUIRED FOR DECEMBER 2026")
print("=" * 80)
print(f"Required Moon Longitude: 288.8142°")
print(f"Actual Moon Longitude: {moon_lon:.4f}°")
print(f"Difference: {moon_lon - 288.8142:.4f}°")

# Time adjustment needed (Moon moves ~13° per day)
moon_speed_per_day = 13.176  # Average
degree_difference = moon_lon - 288.8142
time_adjustment_hours = (degree_difference / moon_speed_per_day) * 24

print(f"\nMoon moves ~{moon_speed_per_day:.3f}° per day")
print(f"Time adjustment needed: {time_adjustment_hours:.2f} hours")
print(f"Adjusted birth time would be: {(birth_ist - timedelta(hours=time_adjustment_hours)).strftime('%H:%M IST')}")

# Check if birth time 18:30 vs 18:37 makes a difference
for test_min in [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]:
    test_time = datetime(1998, 7, 11, 18, test_min, 0)
    test_planets = engine.calculate_planets(test_time, lat, lon)
    test_moon_lon = test_planets['Moon']['longitude']
    
    if abs(test_moon_lon - 288.8142) < 0.2:
        print(f"\n✓ At 18:{test_min:02d} IST, Moon = {test_moon_lon:.4f}° (close to required 288.81°)")

print("\n" + "=" * 80)
print("CHECKING PROFESSIONAL CHART DETAILS")
print("=" * 80)
print("Please verify:")
print("1. Exact birth time: Was it 18:37 or 18:30 IST?")
print("2. Ayanamsa used in professional software (Lahiri/KP/Raman)?")
print("3. Professional chart shows Jupiter mahadasha: Dec 2026 or another month?")
