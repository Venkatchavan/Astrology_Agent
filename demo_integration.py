"""
Integration Example: Combining Math, Logic, and RAG
Demonstrates how to use all three layers together.
"""

from datetime import datetime
from engine import EphemerisEngine
from agents import calculate_aspects, perform_structural_analysis
from ingest_knowledge import KnowledgeBase


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print('=' * 70)


def demonstrate_full_pipeline():
    """Demonstrate the complete analysis pipeline."""
    print_section("Astrological Agent: Full Analysis Pipeline")
    
    # Initialize all components
    print("\n1. Initializing Components...")
    print("-" * 70)
    
    # Math Layer
    engine = EphemerisEngine(data_dir="data")
    print("✓ Math Layer: EphemerisEngine initialized")
    
    # Knowledge Layer (RAG)
    kb = KnowledgeBase()
    stats = kb.get_stats()
    print(f"✓ Knowledge Layer: RAG system initialized ({stats['total_chunks']} chunks)")
    
    print("✓ Logic Layer: Expert agents ready")
    
    # Test data
    test_dt = datetime(2025, 12, 15, 12, 0, 0)
    test_lat = 28.6139  # New Delhi
    test_lon = 77.2090
    
    print_section("2. Mathematical Layer: Calculating Positions")
    print(f"Date/Time: {test_dt} UTC")
    print(f"Location: {test_lat}°N, {test_lon}°E (New Delhi)")
    
    # Calculate chart
    chart = engine.calculate_chart(test_dt, test_lat, test_lon)
    
    print("\nPlanetary Positions:")
    print("-" * 70)
    for planet, data in chart.items():
        nak = data['nakshatra']
        retro = " (R)" if data['retrograde'] else ""
        print(f"  {planet:12s}: {data['longitude']:6.2f}° | "
              f"{nak['nakshatra_name']:20s} | Pada {nak['pada']}{retro}")
    
    print_section("3. Logic Layer: Rule-Based Analysis")
    
    # Aspects
    print("\nVedic Aspects (Parashara):")
    print("-" * 70)
    aspects = calculate_aspects(chart)
    for aspect in aspects[:5]:  # Show first 5
        print(f"  {aspect}")
    if len(aspects) > 5:
        print(f"  ... and {len(aspects) - 5} more")
    
    # Structural Analysis
    print("\nStructural Analysis (Nadi & States):")
    print("-" * 70)
    structural = perform_structural_analysis(chart)
    
    print(f"  Dominant Element:    {structural['summary']['dominant_element']}")
    print(f"  Element Groups:      {structural['summary']['total_element_groups']}")
    print(f"  Retrograde Planets:  {structural['summary']['total_retrograde']}")
    print(f"  Gandanta Planets:    {structural['summary']['total_gandanta']}")
    
    # Show element distribution
    print("\n  Element Distribution:")
    for element, planets in structural['nadi_analysis']['distribution'].items():
        if planets:
            print(f"    {element:10s}: {', '.join(planets)}")
    
    print_section("4. Knowledge Layer: RAG Queries")
    
    if stats['total_chunks'] == 0:
        print("\n⚠ Knowledge base is empty.")
        print("  Add PDF files to 'docs/' and run:")
        print("    python ingest_knowledge.py --docs-dir docs")
    else:
        # Query based on chart features
        moon_nak = chart['Moon']['nakshatra']['nakshatra_name']
        
        queries = [
            f"What is the significance of {moon_nak} nakshatra?",
            "How do Mars aspects affect relationships?",
            "What are the effects of retrograde planets?"
        ]
        
        for query in queries:
            print(f"\n{'─' * 70}")
            print(f"Query: {query}")
            print('─' * 70)
            
            results = kb.search_knowledge(query, top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    content = result['content']
                    preview = content[:150] + "..." if len(content) > 150 else content
                    print(f"\n  Result {i}: {preview}")
            else:
                print("  No results found in knowledge base")
    
    print_section("5. Synthesis Example")
    
    print("\nCombining All Layers for Moon Analysis:")
    print("-" * 70)
    
    moon = chart['Moon']
    moon_nak = moon['nakshatra']
    
    print(f"\nMath Layer Output:")
    print(f"  Position: {moon['longitude']:.2f}° (sidereal)")
    print(f"  Nakshatra: {moon_nak['nakshatra_name']}")
    print(f"  Pada: {moon_nak['pada']}")
    print(f"  Ruler: {moon_nak['ruler']}")
    print(f"  Speed: {moon['speed']:+.4f}°/day")
    
    print(f"\nLogic Layer Output:")
    # Check if Moon is in any special state
    moon_states = []
    for state in structural['state_analysis']['special_states']:
        if state['planet'] == 'Moon':
            moon_states.append(state['state'])
    
    if moon_states:
        print(f"  Special States: {', '.join(moon_states)}")
    else:
        print(f"  Special States: None (normal)")
    
    # Check element
    moon_sign = moon_nak['nakshatra_name']
    print(f"  Element Group: {structural['summary']['dominant_element']}")
    
    print(f"\nKnowledge Layer Query:")
    if stats['total_chunks'] > 0:
        query = f"Interpret Moon in {moon_nak['nakshatra_name']} nakshatra"
        results = kb.search_knowledge(query, top_k=1)
        if results:
            content = results[0]['content']
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  {preview}")
        else:
            print(f"  [No specific knowledge found for {moon_nak['nakshatra_name']}]")
    else:
        print(f"  [Knowledge base not populated]")
    
    print_section("✓ Full Pipeline Demonstration Complete")
    
    print("\nThis demonstrates the Mixture of Experts architecture:")
    print("  • Math Layer (EphemerisEngine) provides precise calculations")
    print("  • Logic Layer (Expert Agents) applies rule-based analysis")
    print("  • Knowledge Layer (RAG) retrieves domain expertise")
    print("\nNext: Phase 4 will orchestrate these with LangGraph")


if __name__ == "__main__":
    demonstrate_full_pipeline()
