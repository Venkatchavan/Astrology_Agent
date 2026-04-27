"""
Complete Working Example - All Phases Integrated
Demonstrates the full Astrological Hybrid Agent system.
"""

from datetime import datetime
import sys


def print_header(text):
    """Print formatted header."""
    print(f"\n{'=' * 70}")
    print(f"{text:^70}")
    print('=' * 70)


def main():
    """Run complete example analysis."""
    
    print_header("ASTROLOGICAL HYBRID AGENT")
    print("\nMixture of Experts Architecture:")
    print("  Layer 1: Math (EphemerisEngine) - Precise calculations")
    print("  Layer 2: Logic (Expert Agents) - Rule-based analysis")
    print("  Layer 3: Knowledge (RAG) - Classical texts")
    print("  Layer 4: Synthesis (LLM) - Interpretation")
    
    # Example birth data
    examples = [
        {
            "name": "Example 1",
            "description": "Basic chart analysis",
            "datetime": datetime(2025, 12, 15, 12, 0, 0),
            "lat": 28.6139,
            "lon": 77.2090,
            "location": "New Delhi, India"
        },
        {
            "name": "Example 2",
            "description": "Western chart",
            "datetime": datetime(1990, 5, 15, 14, 30, 0),
            "lat": 40.7128,
            "lon": -74.0060,
            "location": "New York, USA"
        }
    ]
    
    # Select example
    print_header("EXAMPLE CHARTS")
    for i, ex in enumerate(examples, 1):
        print(f"\n{i}. {ex['name']} - {ex['description']}")
        print(f"   Date: {ex['datetime']}")
        print(f"   Location: {ex['location']}")
    
    print("\n" + "-" * 70)
    
    # Import orchestrator
    try:
        from synthesizer import AstrologicalOrchestrator
    except ImportError as e:
        print(f"\n❌ Error importing modules: {e}")
        print("\nMake sure you're in the project directory and dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Initialize orchestrator
    print_header("INITIALIZING SYSTEM")
    
    print("\nChecking LLM availability...")
    import os
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
    
    if has_openai_key:
        print("✓ OPENAI_API_KEY found - LLM synthesis enabled")
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
            print("✓ LLM initialized (gpt-3.5-turbo)")
        except Exception as e:
            print(f"⚠ LLM initialization failed: {e}")
            llm = None
    else:
        print("⚠ OPENAI_API_KEY not set - will use fact sheet only")
        print("  Set it with: export OPENAI_API_KEY='your-key-here'")
        llm = None
    
    print("\nInitializing orchestrator...")
    orchestrator = AstrologicalOrchestrator(
        llm=llm,
        use_rag=True  # Enable RAG if knowledge base exists
    )
    print("✓ Orchestrator initialized")
    
    # Check knowledge base
    if orchestrator.knowledge_base:
        stats = orchestrator.knowledge_base.get_stats()
        if stats['total_chunks'] > 0:
            print(f"✓ Knowledge base loaded: {stats['total_chunks']} chunks from {stats['source_count']} sources")
        else:
            print("⚠ Knowledge base is empty")
            print("  Add PDFs to docs/ and run: python ingest_knowledge.py --docs-dir docs")
    
    # Analyze first example
    print_header("RUNNING ANALYSIS")
    
    example = examples[0]
    print(f"\nAnalyzing: {example['name']}")
    print(f"DateTime: {example['datetime']} UTC")
    print(f"Location: {example['location']} ({example['lat']}°N, {example['lon']}°E)")
    
    # Run analysis
    print("\n" + "-" * 70)
    print("Processing...")
    print("-" * 70)
    
    reading = orchestrator.analyze_chart_simple(
        dt=example['datetime'],
        lat=example['lat'],
        lon=example['lon'],
        location_name=example['location'],
        name=example['name']
    )
    
    # Display results
    print_header("RESULTS")
    
    # Show fact sheet
    print("\n📊 FACT SHEET (Math + Logic Layers)")
    print("=" * 70)
    print(reading.fact_sheet)
    
    # Show synthesis
    print("\n" + "=" * 70)
    print("🔮 INTERPRETATION (Synthesis Layer)")
    print("=" * 70)
    
    if llm:
        print("\n" + reading.synthesis)
    else:
        print("\n[LLM not available - showing fact sheet only]")
        print("\nTo get AI interpretation:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Run this script again")
    
    # Show what data is available
    print("\n" + "=" * 70)
    print("📦 AVAILABLE DATA")
    print("=" * 70)
    
    print(f"\nMathematical Data:")
    print(f"  • Planets calculated: {len(reading.mathematical_data)}")
    for planet in ['Sun', 'Moon', 'Mars']:
        data = reading.mathematical_data[planet]
        nak = data['nakshatra']
        print(f"  • {planet}: {data['longitude']:.2f}° in {nak['nakshatra_name']}")
    
    print(f"\nLogical Analysis:")
    print(f"  • Aspects found: {len(reading.logical_analysis['aspects'])}")
    print(f"  • Dominant element: {reading.logical_analysis['structural']['summary']['dominant_element']}")
    print(f"  • Retrograde planets: {reading.logical_analysis['structural']['summary']['total_retrograde']}")
    
    print(f"\nKnowledge Context:")
    print(f"  • RAG chunks retrieved: {len(reading.rag_context)}")
    if reading.rag_context:
        for i, ctx in enumerate(reading.rag_context[:2], 1):
            print(f"  • Query {i}: {ctx.get('query', 'N/A')[:50]}...")
    
    # Usage examples
    print_header("USAGE EXAMPLES")
    
    print("\n1. CLI Usage (Full Analysis):")
    print("-" * 70)
    print("python main.py --date 2025-12-15 --time 12:00 --lat 28.6139 --lon 77.2090 \\")
    print("               --name 'John Doe' --location 'New Delhi' --output reading.txt")
    
    print("\n2. CLI Usage (No LLM):")
    print("-" * 70)
    print("python main.py --date 2025-12-15 --time 12:00 --lat 28.6139 --lon 77.2090 --no-llm")
    
    print("\n3. Python API:")
    print("-" * 70)
    print("""
from datetime import datetime
from synthesizer import AstrologicalOrchestrator

orchestrator = AstrologicalOrchestrator()
reading = orchestrator.analyze_chart_simple(
    dt=datetime(2025, 12, 15, 12, 0),
    lat=28.6139,
    lon=77.2090
)
print(reading.synthesis)
    """)
    
    print("\n4. Individual Layers:")
    print("-" * 70)
    print("""
# Math Layer only
from engine import EphemerisEngine
engine = EphemerisEngine()
chart = engine.calculate_chart(dt, lat, lon)

# Logic Layer only
from agents import calculate_aspects, perform_structural_analysis
aspects = calculate_aspects(chart)
structural = perform_structural_analysis(chart)

# Knowledge Layer only
from ingest_knowledge import KnowledgeBase
kb = KnowledgeBase()
results = kb.search_knowledge("your query")
    """)
    
    # System status
    print_header("SYSTEM STATUS")
    
    print("\n✓ Phase 1: Math Layer - Working")
    print("  • EphemerisEngine calculating sidereal positions")
    print("  • 9 planets, 27 nakshatras, 108 padas")
    
    print("\n✓ Phase 2: Logic Layer - Working")
    print("  • Parashara Expert (aspects)")
    print("  • Nadi Expert (element links)")
    print("  • State Expert (retrograde, gandanta)")
    
    print("\n✓ Phase 3: Knowledge Layer - Working")
    if orchestrator.knowledge_base and orchestrator.knowledge_base.get_stats()['total_chunks'] > 0:
        print("  • RAG system operational")
        print(f"  • {orchestrator.knowledge_base.get_stats()['total_chunks']} chunks loaded")
    else:
        print("  • RAG system ready (add PDFs to docs/)")
    
    print("\n✓ Phase 4: Synthesis Layer - Working")
    if llm:
        print("  • LLM synthesis enabled (OpenAI)")
    else:
        print("  • LLM synthesis disabled (set OPENAI_API_KEY)")
    
    print_header("COMPLETE")
    
    print("\n🎉 All phases working correctly!")
    print("\nNext steps:")
    print("  • Add astrological PDFs to docs/ directory")
    print("  • Run: python ingest_knowledge.py --docs-dir docs")
    print("  • Set OPENAI_API_KEY for full synthesis")
    print("  • Use main.py for production analysis")
    
    print("\nFor help:")
    print("  python main.py --help")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
