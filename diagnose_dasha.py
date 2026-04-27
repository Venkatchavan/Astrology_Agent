"""Diagnose dasha balance calculation"""
from datetime import datetime

# Moon at Capricorn 19.60° = 289.60° absolute
moon_longitude = 289.60

# Nakshatra span: 13°20' = 13.333...°
nakshatra_span = 13 + (1/3)

print("=" * 80)
print("NAKSHATRA ANALYSIS")
print("=" * 80)

# Which nakshatra?
nakshatra_index = int(moon_longitude / nakshatra_span)
print(f"Moon Longitude: {moon_longitude}°")
print(f"Nakshatra Index: {nakshatra_index} (0-based)")
print(f"Nakshatra Span: {nakshatra_span}°")

# Nakshatra names (27 total, 0-indexed)
nakshatras = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

nakshatra_name = nakshatras[nakshatra_index]
print(f"Nakshatra Name: {nakshatra_name}")

# Nakshatra lords (repeat every 9: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury)
lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
lord_index = nakshatra_index % 9
lord_name = lords[lord_index]
print(f"Nakshatra Lord: {lord_name} (index {lord_index})")

print("\n" + "=" * 80)
print("TRAVERSAL WITHIN NAKSHATRA")
print("=" * 80)

# How far into this specific nakshatra?
nakshatra_start = nakshatra_index * nakshatra_span
traversed_deg = moon_longitude - nakshatra_start
remaining_deg = nakshatra_span - traversed_deg

print(f"Nakshatra Start: {nakshatra_start:.4f}°")
print(f"Traversed: {traversed_deg:.4f}° ({(traversed_deg/nakshatra_span)*100:.2f}%)")
print(f"Remaining: {remaining_deg:.4f}° ({(remaining_deg/nakshatra_span)*100:.2f}%)")

fraction_remaining = remaining_deg / nakshatra_span
print(f"Fraction Remaining: {fraction_remaining:.6f}")

print("\n" + "=" * 80)
print("DASHA BALANCE CALCULATION")
print("=" * 80)

# Dasha periods
dasha_periods = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

full_years = dasha_periods[lord_name]
balance_years = full_years * fraction_remaining

print(f"Nakshatra Lord: {lord_name}")
print(f"Full Dasha Period: {full_years} years")
print(f"Balance Years (float): {balance_years:.6f} years")

# Convert to Y/M/D
b_years = int(balance_years)
b_months = int((balance_years - b_years) * 12)
b_days = int(((balance_years - b_years) * 12 - b_months) * 30.4375)

print(f"Balance (Y/M/D): {b_years}y {b_months}m {b_days}d")

# Calculate end date
birth_dt = datetime(1998, 7, 11, 13, 7, 0)
from datetime import timedelta
total_days = balance_years * 365.2422
end_date = birth_dt + timedelta(days=total_days)

print(f"\nBirth Date (UTC): {birth_dt.strftime('%Y-%m-%d %H:%M')}")
print(f"Balance End Date: {end_date.strftime('%Y-%m-%d')}")

# Calculate when Rahu ends (Moon balance + Mars full + Rahu full)
mars_years = 7
rahu_years = 18
total_to_rahu_end = balance_years + mars_years + rahu_years
rahu_end_date = birth_dt + timedelta(days=total_to_rahu_end * 365.2422)

print(f"\nRahu Mahadasha Ends: {rahu_end_date.strftime('%Y-%m-%d')}")
print(f"Jupiter Mahadasha Starts: {rahu_end_date.strftime('%Y-%m-%d')}")

print("\n" + "=" * 80)
print("EXPECTED vs ACTUAL")
print("=" * 80)
print(f"Expected Jupiter Start: December 2026")
print(f"Actual Jupiter Start: {rahu_end_date.strftime('%B %d, %Y')}")
print(f"Difference: ~{(rahu_end_date.year - 2026) * 12 + (rahu_end_date.month - 12)} months")

# What balance would give December 2026?
from datetime import datetime
expected_jupiter_start = datetime(2026, 12, 1, 0, 0, 0)
days_from_birth = (expected_jupiter_start - birth_dt).days
years_from_birth = days_from_birth / 365.2422

# Subtract Mars (7) and Rahu (18) to get Moon balance
required_moon_balance = years_from_birth - mars_years - rahu_years

print(f"\nREQUIRED MOON BALANCE for Dec 2026:")
print(f"  Days from birth to Dec 2026: {days_from_birth}")
print(f"  Years from birth: {years_from_birth:.4f}")
print(f"  Required Moon balance: {required_moon_balance:.4f} years")

req_years = int(required_moon_balance)
req_months = int((required_moon_balance - req_years) * 12)
req_days = int(((required_moon_balance - req_years) * 12 - req_months) * 30.4375)
print(f"  Required balance (Y/M/D): {req_years}y {req_months}m {req_days}d")

# What fraction of Moon's 10 years is this?
req_fraction = required_moon_balance / full_years
print(f"  Required fraction remaining: {req_fraction:.6f} ({req_fraction*100:.2f}%)")

# What degree would give this fraction?
req_remaining_deg = req_fraction * nakshatra_span
req_traversed_deg = nakshatra_span - req_remaining_deg
req_moon_lon = nakshatra_start + req_traversed_deg

print(f"  Required traversed degrees: {req_traversed_deg:.4f}°")
print(f"  Required Moon longitude: {req_moon_lon:.4f}°")
print(f"  Actual Moon longitude: {moon_longitude}°")
print(f"  Difference: {moon_longitude - req_moon_lon:.4f}°")
