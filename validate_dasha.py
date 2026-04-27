"""
Validate and debug Dasha calculations
"""

from datetime import datetime
from engine.dasha_engine import DashaEngine

# Test case: India Independence
birth_date = datetime(1947, 8, 15, 0, 0, 0)
moon_longitude = 32.06  # Taurus 2.06° from the output

print("=" * 70)
print("DASHA CALCULATION VALIDATION")
print("=" * 70)
print(f"\nBirth Date: {birth_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Moon Longitude: {moon_longitude}° (Taurus 2.06°)")

# Manual calculation
nakshatra_span = 13 + (1/3)  # 13.3333°
print(f"\nNakshatra Span: {nakshatra_span:.4f}°")

nakshatra_index_float = moon_longitude / nakshatra_span
nakshatra_index = int(nakshatra_index_float)
print(f"Nakshatra Index (float): {nakshatra_index_float:.4f}")
print(f"Nakshatra Index (int): {nakshatra_index}")

# Nakshatra names
nakshatra_names = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

print(f"Nakshatra Name: {nakshatra_names[nakshatra_index]}")

# Ruler calculation
dasha_order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
ruler_index = nakshatra_index % 9
ruler = dasha_order[ruler_index]
print(f"\nRuler Index (nakshatra_index % 9): {ruler_index}")
print(f"Dasha Ruler: {ruler}")

# Traversal calculation
traversed_deg = moon_longitude % nakshatra_span
remaining_deg = nakshatra_span - traversed_deg
fraction_remaining = remaining_deg / nakshatra_span

print(f"\nTraversed in Nakshatra: {traversed_deg:.4f}°")
print(f"Remaining in Nakshatra: {remaining_deg:.4f}°")
print(f"Fraction Remaining: {fraction_remaining:.4f} ({fraction_remaining * 100:.2f}%)")

# Balance calculation
dasha_periods = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
                 "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
full_years = dasha_periods[ruler]
balance_years_float = full_years * fraction_remaining

print(f"\nFull Period: {full_years} years")
print(f"Balance: {balance_years_float:.4f} years")

b_years = int(balance_years_float)
b_months = int((balance_years_float - b_years) * 12)
b_days = int(((balance_years_float - b_years) * 12 - b_months) * 30.4375)  # More accurate

print(f"Balance: {b_years}y {b_months}m {b_days}d")

# Now test with the engine
print("\n" + "=" * 70)
print("ENGINE OUTPUT")
print("=" * 70)

engine = DashaEngine()
balance = engine.calculate_dasha_balance(moon_longitude, birth_date)

print(f"\nRuler: {balance['ruler']}")
print(f"Balance: {balance['balance_str']}")
print(f"Balance Years: {balance['balance_years']:.4f}")
print(f"Start Date: {balance['start_date'].strftime('%Y-%m-%d')}")
print(f"End Date: {balance['end_date'].strftime('%Y-%m-%d')}")

# Generate schedule
print("\n" + "=" * 70)
print("MAHADASHA SCHEDULE")
print("=" * 70)

schedule = engine.generate_mahadasha_schedule(balance, years_to_generate=100)
print(f"\nShowing first 10 periods:\n")
for i, period in enumerate(schedule[:10]):
    duration_years = dasha_periods[period['lord']]
    print(f"{i+1:2d}. {period['lord']:8s} ({period['type']:7s}) "
          f"{duration_years:2d}y: {period['start'].strftime('%Y-%m-%d')} → {period['end'].strftime('%Y-%m-%d')}")

# Test current period
print("\n" + "=" * 70)
print("CURRENT PERIOD (2025-12-15)")
print("=" * 70)

current = engine.get_current_dasha(moon_longitude, birth_date, datetime(2025, 12, 15))
print(f"\nMahadasha: {current['mahadasha']}")
print(f"Antardasha: {current['antardasha']}")
print(f"Ends: {current['end_date']}")

# Expected output (from traditional Vedic astrology software):
print("\n" + "=" * 70)
print("EXPECTED VALUES (Traditional Vedic Astrology)")
print("=" * 70)
print("""
For Moon at Taurus 2.06° (32.06°):
- Nakshatra: Krittika (2nd nakshatra, index 2)
- Krittika Ruler: Sun (index 2 % 9 = 2)
- Birth Balance: Sun Mahadasha with balance remaining
- Next: Moon → Mars → Rahu → Jupiter → Saturn → Mercury → Ketu → Venus → Sun (cycle)

Standard sequence after Sun balance:
1. Moon (10 years)
2. Mars (7 years)
3. Rahu (18 years)
4. Jupiter (16 years)
5. Saturn (19 years)
6. Mercury (17 years)
7. Ketu (7 years)
8. Venus (20 years)
""")
