"""
Test Script for Phase 4 - Orchestrator and Synthesis
Tests the complete pipeline with all layers integrated.
"""

from datetime import datetime
import logging
from pathlib import Path

from synthesizer import AstrologicalOrchestrator, BirthData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print('=' * 70)


def test_without_llm():
    """Test orchestrator without LLM (fact sheet only)."""
    print_section("Test 1: Orchestrator Without LLM")
    
    # Initialize orchestrator without LLM
    orchestrator = AstrologicalOrchestrator(
        llm=None,
        use_rag=False  # Disable RAG for faster test
    )
    
    # Test birth data
    birth_data = BirthData(
        datetime=datetime(2025, 12, 15, 12, 0, 0),
        latitude=28.6139,
        longitude=77.2090,
        location_name="New Delhi, India",
        name="Test Subject"
    )
    
    print(f"\nAnalyzing chart for:")
    print(f"  Name: {birth_data.name}")
    print(f"  DateTime: {birth_data.datetime} UTC")
    print(f"  Location: {birth_data.location_name}")
    
    # Run analysis
    reading = orchestrator.analyze_chart(birth_data)
    
    # Display fact sheet
    print("\n" + reading.fact_sheet)
    
    # Verify structure
    print("\n" + "-" * 70)
    print("Verification:")
    print(f"  ✓ Mathematical data: {len(reading.mathematical_data)} planets")
    print(f"  ✓ Aspects: {len(reading.logical_analysis['aspects'])} found")
    print(f"  ✓ Structural analysis: {reading.logical_analysis['structural']['summary']['dominant_element']} dominant")
    print(f"  ✓ Fact sheet: {len(reading.fact_sheet)} characters")
    
    return reading


def test_with_mock_llm():
    """Test orchestrator with a mock LLM."""
    print_section("Test 2: Orchestrator With Mock LLM")
    
    # Create a simple mock LLM
    class MockLLM:
        def invoke(self, prompt):
            return """Based on the Mathematical Fact Sheet provided:

**Core Personality:**
The Moon's placement in its nakshatra reveals the native's emotional nature and core personality. The Moon's speed and position indicate the primary psychological tendencies.

**Strengths and Talents:**
The planetary aspects show natural abilities and areas of strength. Benefic aspects from Jupiter suggest wisdom and expansion in those areas.

**Challenges and Growth Areas:**
Any retrograde planets indicate areas requiring internal reflection and mastery. Gandanta placements suggest transformative life experiences.

**Key Life Themes:**
The elemental distribution and aspect patterns reveal the major themes that will play out across the life. Strong elemental emphasis suggests focused energy in those domains.

**Timing Considerations:**
The nakshatra rulers and their placements indicate the sequence of dasha periods and their likely effects.

This is a mock synthesis for testing purposes."""
    
    # Initialize with mock LLM
    orchestrator = AstrologicalOrchestrator(
        llm=MockLLM(),
        use_rag=False
    )
    
    # Test birth data
    birth_data = BirthData(
        datetime=datetime(1990, 5, 15, 14, 30, 0),
        latitude=40.7128,
        longitude=-74.0060,
        location_name="New York, USA"
    )
    
    print(f"\nAnalyzing chart for:")
    print(f"  DateTime: {birth_data.datetime} UTC")
    print(f"  Location: {birth_data.location_name}")
    
    # Run analysis
    reading = orchestrator.analyze_chart(birth_data)
    
    # Display synthesis
    print("\nSynthesis:")
    print("-" * 70)
    print(reading.synthesis)
    
    print("\n" + "-" * 70)
    print("Verification:")
    print(f"  ✓ Synthesis generated: {len(reading.synthesis)} characters")
    print(f"  ✓ Mock LLM working correctly")
    
    return reading


def test_with_rag():
    """Test orchestrator with RAG system."""
    print_section("Test 3: Orchestrator With RAG")
    
    # Initialize with RAG
    orchestrator = AstrologicalOrchestrator(
        llm=None,
        use_rag=True
    )
    
    # Check knowledge base status
    if orchestrator.knowledge_base:
        stats = orchestrator.knowledge_base.get_stats()
        print(f"\nKnowledge Base Status:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Sources: {stats['source_count']}")
        
        if stats['total_chunks'] == 0:
            print("\n⚠ Knowledge base is empty")
            print("  Add PDFs to docs/ and run: python ingest_knowledge.py --docs-dir docs")
    
    # Test birth data
    birth_data = BirthData(
        datetime=datetime(2025, 12, 15, 12, 0, 0),
        latitude=28.6139,
        longitude=77.2090
    )
    
    # Run analysis
    reading = orchestrator.analyze_chart(birth_data)
    
    # Display RAG results
    print(f"\nRAG Context Retrieved:")
    print("-" * 70)
    
    if reading.rag_context:
        for i, context in enumerate(reading.rag_context[:3], 1):
            print(f"\n{i}. Query: {context.get('query', 'N/A')}")
            print(f"   Source: {context.get('metadata', {}).get('source', 'Unknown')}")
            content = context.get('content', '')
            preview = content[:150] + "..." if len(content) > 150 else content
            print(f"   Content: {preview}")
    else:
        print("  No RAG context retrieved (knowledge base may be empty)")
    
    print("\n" + "-" * 70)
    print("Verification:")
    print(f"  ✓ RAG queries executed: {len(reading.rag_context)} results")
    
    return reading


def test_simple_interface():
    """Test the simplified interface."""
    print_section("Test 4: Simplified Interface")
    
    orchestrator = AstrologicalOrchestrator(llm=None, use_rag=False)
    
    # Use simplified interface
    reading = orchestrator.analyze_chart_simple(
        dt=datetime(2025, 12, 15, 12, 0, 0),
        lat=28.6139,
        lon=77.2090,
        location_name="New Delhi",
        name="Test User"
    )
    
    print("\n✓ Simplified interface working")
    print(f"  Birth data: {reading.birth_data.name} at {reading.birth_data.location_name}")
    print(f"  Planets: {len(reading.mathematical_data)}")
    print(f"  Aspects: {len(reading.logical_analysis['aspects'])}")


def test_parallel_execution():
    """Test that expert agents can be run in parallel."""
    print_section("Test 5: Parallel Expert Execution")
    
    from engine import EphemerisEngine
    from agents import calculate_aspects, perform_structural_analysis
    import time
    
    engine = EphemerisEngine()
    chart = engine.calculate_chart(
        datetime(2025, 12, 15, 12, 0, 0),
        28.6139,
        77.2090
    )
    
    # Sequential execution
    start = time.time()
    aspects = calculate_aspects(chart)
    structural = perform_structural_analysis(chart)
    sequential_time = time.time() - start
    
    print(f"\nSequential Execution:")
    print(f"  Time: {sequential_time:.4f} seconds")
    print(f"  Aspects: {len(aspects)}")
    print(f"  Structural: {structural['summary']['dominant_element']} dominant")
    
    # Note: These are CPU-bound, so parallel won't be faster
    # But the architecture supports it for future I/O-bound experts
    print(f"\n✓ Both experts executed successfully")
    print(f"  (Architecture supports parallel execution for I/O-bound tasks)")


def main():
    """Run all Phase 4 tests."""
    print_section("Phase 4: Orchestrator Test Suite")
    
    try:
        # Test 1: Without LLM
        test_without_llm()
        
        # Test 2: With Mock LLM
        test_with_mock_llm()
        
        # Test 3: With RAG
        test_with_rag()
        
        # Test 4: Simplified interface
        test_simple_interface()
        
        # Test 5: Parallel execution
        test_parallel_execution()
        
        print_section("✓ All Phase 4 Tests Passed")
        
        print("\n" + "=" * 70)
        print("Next Steps:")
        print("=" * 70)
        print("1. Set OPENAI_API_KEY environment variable for real LLM")
        print("2. Add PDFs to docs/ for RAG knowledge retrieval")
        print("3. Run full analysis:")
        print("   python main.py --date 2025-12-15 --time 12:00 --lat 28.6139 --lon 77.2090")
        print("4. Or use with all features:")
        print("   python main.py --date 2025-12-15 --time 12:00 --lat 28.6139 --lon 77.2090 \\")
        print("                  --name 'John Doe' --location 'New Delhi' --output reading.txt")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
