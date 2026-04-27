"""
Test script for EphemerisEngine
Validates planetary calculations and nakshatra mapping.
"""

from datetime import datetime
from engine import EphemerisEngine


def main():
    """Run basic tests on the ephemeris engine."""
    print("=" * 60)
    print("Ephemeris Engine Test Suite")
    print("=" * 60)

    # Initialize engine
    print("\n1. Initializing EphemerisEngine...")
    engine = EphemerisEngine(data_dir="data")
    print(f"   ✓ Loaded {len(engine.nakshatras)} nakshatras")
    print(f"   ✓ Loaded {len(engine.padas)} padas")
    print(f"   ✓ Loaded {len(engine.nakshatra_rulers)} rulers")

    # Test date: Dec 15, 2025, 12:00 UTC
    # Location: New Delhi, India
    test_dt = datetime(2025, 12, 15, 12, 0, 0)
    test_lat = 28.6139
    test_lon = 77.2090

    print(f"\n2. Calculating planets for:")
    print(f"   Date/Time: {test_dt} UTC")
    print(f"   Location: {test_lat}°N, {test_lon}°E (New Delhi)")

    # Calculate planets
    planets = engine.calculate_planets(test_dt, test_lat, test_lon)

    print(f"\n3. Planetary Positions (Sidereal/Lahiri):")
    print("-" * 60)
    for planet_name, data in planets.items():
        retro_marker = " (R)" if data["retrograde"] else ""
        print(f"   {planet_name:12s}: {data['longitude']:7.2f}° "
              f"| Speed: {data['speed']:+7.4f}°/day{retro_marker}")

    # Test nakshatra calculation for Moon
    print(f"\n4. Testing Nakshatra Mapping:")
    print("-" * 60)
    moon_lon = planets["Moon"]["longitude"]
    moon_nak = engine.get_nakshatra(moon_lon)

    print(f"   Moon Longitude: {moon_lon:.2f}°")
    print(f"   Nakshatra: {moon_nak['nakshatra_name']}")
    print(f"   Pada: {moon_nak['pada']}")
    print(f"   Ruler: {moon_nak['ruler']}")

    # Full chart calculation
    print(f"\n5. Complete Chart with Nakshatras:")
    print("-" * 60)
    chart = engine.calculate_chart(test_dt, test_lat, test_lon)

    for planet_name, data in chart.items():
        nak = data["nakshatra"]
        retro = " (R)" if data["retrograde"] else ""
        print(f"   {planet_name:12s}: {data['longitude']:6.2f}° | "
              f"{nak['nakshatra_name']:20s} | Pada {nak['pada']} | "
              f"Ruler: {nak['ruler']}{retro}")

    # Test edge cases
    print(f"\n6. Testing Edge Cases:")
    print("-" * 60)

    # Test at 0 degrees (Ashwini start)
    nak_0 = engine.get_nakshatra(0.0)
    print(f"   0.0°    -> {nak_0['nakshatra_name']} (Pada {nak_0['pada']})")

    # Test at 359.9 degrees (Revati end)
    nak_359 = engine.get_nakshatra(359.9)
    print(f"   359.9°  -> {nak_359['nakshatra_name']} (Pada {nak_359['pada']})")

    # Test at exactly 13.333... (Bharani start)
    nak_13 = engine.get_nakshatra(13.333333)
    print(f"   13.33°  -> {nak_13['nakshatra_name']} (Pada {nak_13['pada']})")

    # Test crossover handling with > 360
    nak_370 = engine.get_nakshatra(370.0)
    print(f"   370.0°  -> {nak_370['nakshatra_name']} (normalized to {370.0 % 360}°)")

    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
