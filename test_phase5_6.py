"""
Test Phase 5 (Numerology) and Phase 6 (Navamsa D9) implementations
"""

from datetime import datetime
from engine.ephemeris import EphemerisEngine
from engine.numerology import NumerologyEngine
from agents.numerology_expert import NumerologyExpert
from agents.parashara import analyze_divisional_strength


def test_numerology():
    """Test numerology calculations."""
    print("=" * 70)
    print("PHASE 5: NUMEROLOGY ENGINE TEST")
    print("=" * 70)
    
    # Test data
    birth_date = datetime(1947, 8, 15)
    full_name = "India Independence"
    
    # Initialize engines
    num_engine = NumerologyEngine()
    num_expert = NumerologyExpert()
    
    # Calculate full profile
    print(f"\nTest Subject: {full_name}")
    print(f"Birth Date: {birth_date.strftime('%B %d, %Y')}")
    print("\n" + "-" * 70)
    
    profile = num_engine.analyze_full_profile(birth_date, full_name)
    
    # Display Life Path
    lp = profile["life_path"]
    print(f"\n1. LIFE PATH NUMBER: {lp['number']}")
    print(f"   Ruler: {lp['ruler']}")
    print(f"   Meaning: {lp['meaning']}")
    print(f"   Calculation: {lp['calculation']}")
    
    # Display Destiny
    dest = profile["destiny"]
    print(f"\n2. DESTINY NUMBER: {dest['number']} (Chaldean)")
    print(f"   Ruler: {dest['ruler']}")
    print(f"   Meaning: {dest['meaning']}")
    print(f"   Name: {dest['name']} → {dest['clean_name']}")
    print(f"   Calculation: {dest['calculation']}")
    
    # Display Attitude
    att = profile["attitude"]
    print(f"\n3. ATTITUDE NUMBER: {att['number']}")
    print(f"   Ruler: {att['ruler']}")
    print(f"   Meaning: {att['meaning']}")
    print(f"   Calculation: {att['calculation']}")
    
    # Summary
    summary = profile["summary"]
    print(f"\n4. SUMMARY")
    print(f"   Core Numbers: {summary['core_numbers']}")
    print(f"   Dominant Rulers: {', '.join(summary['dominant_rulers'])}")
    print(f"   Alignment: {summary['alignment_strength']}")
    
    # Expert interpretation
    print("\n" + "-" * 70)
    print("EXPERT INTERPRETATION")
    print("-" * 70)
    
    tags = num_expert.generate_profile_tags(profile)
    
    print(f"\nLife Path: {tags['life_path']['archetype']}")
    print(f"  Planet: {tags['life_path']['ruler']}, Element: {tags['life_path']['element']}")
    
    print(f"\nDestiny: {tags['destiny']['archetype']}")
    print(f"  Planet: {tags['destiny']['ruler']}, Element: {tags['destiny']['element']}")
    
    print(f"\nSynthesis:")
    syn = tags['synthesis']
    print(f"  Dominant Element: {syn['dominant_element']}")
    print(f"  Master Number: {'Yes' if syn['master_number_present'] else 'No'}")
    print(f"  Overall Theme: {syn['overall_theme']}")
    if syn['patterns']:
        print(f"  Patterns:")
        for pattern in syn['patterns']:
            print(f"    • {pattern}")
    
    # Test harmony check
    print("\n" + "-" * 70)
    print("ASTROLOGY-NUMEROLOGY HARMONY CHECK")
    print("-" * 70)
    
    # Simulated astrological data
    astro_indicators = {
        "sun_ruler": "Mercury",
        "moon_ruler": "Moon",
        "dominant_element": "Earth",
        "sun_archetype": "The Communicator"
    }
    
    harmony = num_expert.check_harmony_with_astrology(tags, astro_indicators)
    print(f"\nHarmony Score: {harmony['harmony_count']}/3")
    print(f"Confidence Multiplier: {harmony['confidence_multiplier']}x")
    print(f"Verdict: {harmony['verdict']}")
    
    if harmony['harmony_points']:
        print(f"\nAlignment Points:")
        for point in harmony['harmony_points']:
            print(f"  ✓ {point}")
    
    print(f"\nInterpretation:\n  {harmony['interpretation']}")


def test_navamsa():
    """Test Navamsa (D9) calculations."""
    print("\n\n" + "=" * 70)
    print("PHASE 6: NAVAMSA (D9) DIVISIONAL CHART TEST")
    print("=" * 70)
    
    # Initialize engine
    engine = EphemerisEngine()
    
    # Test cases with different sign elements
    test_cases = [
        ("Jupiter", 3.0, "Aries (Fire)"),     # Early Aries
        ("Sun", 88.5, "Gemini (Air)"),        # Mid Gemini
        ("Moon", 32.0, "Taurus (Earth)"),     # Early Taurus
        ("Venus", 216.0, "Scorpio (Water)"),  # Early Scorpio
    ]
    
    print("\nTest Cases:")
    print("-" * 70)
    
    for planet, longitude, sign_desc in test_cases:
        d9 = engine.calculate_navamsa(longitude)
        
        print(f"\n{planet} at {longitude}° ({sign_desc})")
        print(f"  D1 Sign: {d9['d1_sign']}")
        print(f"  Navamsa Pada: {d9['navamsa_pada']}/9")
        print(f"  D9 Sign: {d9['d9_sign']}")
        print(f"  D9 Longitude: {d9['d9_longitude']:.2f}°")
        
        if d9['vargottama']:
            print(f"  ⭐ VARGOTTAMA - SUPREME STRENGTH!")
        else:
            print(f"  Standard placement")
    
    # Test with actual chart
    print("\n\n" + "-" * 70)
    print("FULL CHART ANALYSIS (India Independence)")
    print("-" * 70)
    
    birth_dt = datetime(1947, 8, 15, 0, 0, 0)
    lat, lon = 28.6139, 77.2090
    
    # Calculate D1 positions
    chart = engine.calculate_chart(birth_dt, lat, lon)
    
    # Calculate D9 for all planets
    navamsa_data = {}
    for planet_name, planet_data in chart.items():
        longitude = planet_data["longitude"]
        d9_info = engine.calculate_navamsa(longitude)
        navamsa_data[planet_name] = d9_info
    
    # Analyze divisional strength
    strength_analysis = analyze_divisional_strength(chart, navamsa_data)
    
    print(f"\nD1 → D9 Placements:")
    for planet, d9_data in navamsa_data.items():
        varg = "⭐ VARGOTTAMA" if d9_data['vargottama'] else ""
        print(f"  {planet:10s}: {d9_data['d1_sign']:12s} → {d9_data['d9_sign']:12s} {varg}")
    
    print(f"\n" + "-" * 70)
    print("STRENGTH ANALYSIS")
    print("-" * 70)
    
    summary = strength_analysis['summary']
    print(f"\nVargottama Count: {summary['vargottama_count']}")
    print(f"Vargottama Planets: {', '.join(summary['vargottama_planets']) if summary['vargottama_planets'] else 'None'}")
    print(f"Chart Assessment: {summary['interpretation']}")
    
    if strength_analysis['strength_notes']:
        print(f"\nStrength Notes:")
        for note in strength_analysis['strength_notes']:
            print(f"  • {note}")


if __name__ == "__main__":
    test_numerology()
    test_navamsa()
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
