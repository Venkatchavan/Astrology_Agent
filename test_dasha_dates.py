"""Test script to verify dasha calculations"""
from datetime import datetime
from engine.dasha_engine import DashaEngine

# Birth data: July 11, 1998, 18:37 IST (13:07 UTC)
moon_longitude = 289.60  # Capricorn 19.60° (Shravana nakshatra)
birth_dt_utc = datetime(1998, 7, 11, 13, 7, 0)

de = DashaEngine()

# Calculate balance and schedule
balance = de.calculate_dasha_balance(moon_longitude, birth_dt_utc)
schedule = de.generate_mahadasha_schedule(balance, 35)

print("=" * 80)
print("MAHADASHA SCHEDULE")
print("=" * 80)
print(f"Birth Nakshatra: Shravana (Moon ruled)")
print(f"Moon Position: {moon_longitude:.2f}° ({(moon_longitude % 30):.2f}° in sign)")
print(f"\nBalance at Birth: {balance['ruler']} - {balance['balance_str']}")
print("=" * 80)

for i, dasha in enumerate(schedule[:10]):
    lord = dasha['lord']
    start = dasha['start'].strftime('%Y-%m-%d')
    end = dasha['end'].strftime('%Y-%m-%d')
    dtype = dasha['type']
    years = de.dasha_periods[lord]
    
    print(f"{i+1}. {lord:8} ({years:2} yrs) | {start} to {end} | {dtype}")

print("=" * 80)

# Get current dasha
current = de.get_current_dasha(moon_longitude, birth_dt_utc, datetime(2026, 1, 22))
print(f"\nCurrent Dasha (Jan 22, 2026):")
print(f"  Mahadasha: {current['mahadasha']}")
print(f"  Antardasha: {current['antardasha']}")
print(f"  Ends: {current['end_date']}")
print("=" * 80)
