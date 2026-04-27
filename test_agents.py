"""
Test script for Rule-Based Expert Agents (Phase 2)
Tests Parashara aspects, Nadi links, and special state analysis.
"""

from datetime import datetime
from engine import EphemerisEngine
from agents import (
    calculate_aspects,
    get_planet_relationships,
    analyze_nadi_links,
    analyze_special_states,
    perform_structural_analysis
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print('=' * 70)


def main():
    """Run comprehensive tests on all Phase 2 agents."""
    print_section("Phase 2: Rule-Based Expert Agents Test Suite")
    
    # Initialize engine
    print("\nInitializing EphemerisEngine...")
    engine = EphemerisEngine(data_dir="data")
    
    # Test date and location
    test_dt = datetime(2025, 12, 15, 12, 0, 0)
    test_lat = 28.6139  # New Delhi
    test_lon = 77.2090
    
    print(f"Date/Time: {test_dt} UTC")
    print(f"Location: {test_lat}°N, {test_lon}°E (New Delhi)")
    
    # Calculate complete chart
    print("\nCalculating planetary positions...")
    chart = engine.calculate_chart(test_dt, test_lat, test_lon)
    
    # Display planet positions
    print_section("Planetary Positions (Sidereal)")
    for planet, data in chart.items():
        sign = data['nakshatra']['nakshatra_name']
        retro = " (R)" if data['retrograde'] else ""
        print(f"  {planet:12s}: {data['longitude']:7.2f}° | {sign:20s}{retro}")
    
    # Test Parashara Expert (y₁) - Aspects
    print_section("Parashara Expert (y₁): Vedic Aspects")
    
    print("\nAspect Rules:")
    print("  Mars    : 4th, 7th, 8th houses")
    print("  Jupiter : 5th, 7th, 9th houses")
    print("  Saturn  : 3rd, 7th, 10th houses")
    print("  Others  : 7th house only")
    
    aspects = calculate_aspects(chart)
    
    print(f"\nTotal Aspects Found: {len(aspects)}")
    print("-" * 70)
    for aspect in aspects:
        print(f"  {aspect}")
    
    # Show relationship map
    print("\nPlanet Aspect Relationships:")
    print("-" * 70)
    relationships = get_planet_relationships(chart)
    for planet, aspected_planets in relationships.items():
        if aspected_planets:
            print(f"  {planet:12s} aspects: {', '.join(aspected_planets)}")
    
    # Test Nadi Expert (y₂) - Elemental Links
    print_section("Nadi Expert (y₂): Elemental Groupings")
    
    nadi_analysis = analyze_nadi_links(chart)
    
    print("\nElement Distribution:")
    print("-" * 70)
    for element, planets in nadi_analysis['full_distribution'].items():
        if planets:
            print(f"  {element:10s}: {', '.join(planets)}")
    
    print(f"\nLinked Groups (2+ planets in same element):")
    print("-" * 70)
    if nadi_analysis['element_groups']:
        for group in nadi_analysis['element_groups']:
            print(f"  {group['element']:10s}: {', '.join(group['planets'])} "
                  f"({group['count']} planets)")
    else:
        print("  No element groups with 2+ planets")
    
    print(f"\nLinked Pairs:")
    print("-" * 70)
    if nadi_analysis['linked_pairs']:
        for pair in nadi_analysis['linked_pairs']:
            print(f"  {pair['planet1']} ({pair['sign1']}) <-> "
                  f"{pair['planet2']} ({pair['sign2']}) [{pair['element']}]")
    else:
        print("  No linked pairs found")
    
    # Test State Expert (y₃) - Special States
    print_section("State Expert (y₃): Special Planetary States")
    
    state_analysis = analyze_special_states(chart)
    
    print(f"\nRetrograde Planets:")
    print("-" * 70)
    if state_analysis['retrograde_planets']:
        for planet_info in state_analysis['retrograde_planets']:
            print(f"  {planet_info['planet']:12s} in {planet_info['sign']:15s} "
                  f"@ {planet_info['longitude']:7.2f}° | "
                  f"Speed: {planet_info['speed']:+7.4f}°/day")
    else:
        print("  No retrograde planets")
    
    print(f"\nGandanta Planets (Water-Fire Junctions):")
    print("-" * 70)
    if state_analysis['gandanta_planets']:
        for planet_info in state_analysis['gandanta_planets']:
            print(f"  {planet_info['planet']:12s} @ {planet_info['longitude']:7.2f}° | "
                  f"Zone: {planet_info['zone']}")
    else:
        print("  No planets in Gandanta zones")
    
    print(f"\nSpecial State Summary:")
    print("-" * 70)
    print(f"  Retrograde planets: {state_analysis['counts']['retrograde']}")
    print(f"  Gandanta planets:   {state_analysis['counts']['gandanta']}")
    print(f"  Total special:      {state_analysis['counts']['total_special']}")
    
    # Complete Structural Analysis
    print_section("Complete Structural Analysis")
    
    structural = perform_structural_analysis(chart)
    
    print(f"\nSummary:")
    print("-" * 70)
    print(f"  Dominant Element:        {structural['summary']['dominant_element']}")
    print(f"  Element Groups (2+):     {structural['summary']['total_element_groups']}")
    print(f"  Linked Pairs:            {structural['summary']['total_linked_pairs']}")
    print(f"  Retrograde Planets:      {structural['summary']['total_retrograde']}")
    print(f"  Gandanta Planets:        {structural['summary']['total_gandanta']}")
    
    # Test edge cases
    print_section("Edge Case Tests")
    
    print("\nTesting aspect calculations with manual positions:")
    print("-" * 70)
    
    # Create test positions: Mars in Aries (house 1), Venus in Cancer (house 4)
    test_positions = {
        "Mars": {"longitude": 15.0, "retrograde": False},  # Aries (house 1)
        "Venus": {"longitude": 105.0, "retrograde": False}  # Cancer (house 4)
    }
    
    test_aspects = calculate_aspects(test_positions)
    print("Mars @ 15° (Aries, house 1)")
    print("Venus @ 105° (Cancer, house 4)")
    print(f"Expected: Mars aspects Venus (4th house)")
    print(f"Result: {test_aspects}")
    
    print("\nTesting Gandanta detection at critical junctions:")
    print("-" * 70)
    
    from agents.nadi_expert import is_in_gandanta
    
    test_longitudes = [
        (0.0, "Aries start (Pisces-Aries)"),
        (359.5, "Pisces end (Pisces-Aries)"),
        (121.0, "Leo start (Cancer-Leo)"),
        (241.0, "Sagittarius start (Scorpio-Sagittarius)"),
        (180.0, "Middle of Libra (not Gandanta)")
    ]
    
    for lon, desc in test_longitudes:
        result = is_in_gandanta(lon)
        status = "✓ GANDANTA" if result['in_gandanta'] else "✗ Not Gandanta"
        zone = f" [{result.get('zone', 'N/A')}]" if result['in_gandanta'] else ""
        print(f"  {lon:6.1f}° ({desc:35s}): {status}{zone}")
    
    print_section("✓ Phase 2 Tests Completed Successfully")


if __name__ == "__main__":
    main()
