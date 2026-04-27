"""
Test script for Knowledge Base RAG System (Phase 3)
Tests PDF ingestion, contextual splitting, and semantic search.
"""

import logging
from pathlib import Path
from ingest_knowledge import KnowledgeBase, ContextualSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print('=' * 70)


def test_contextual_splitter():
    """Test the contextual text splitter."""
    print_section("Testing Contextual Splitter")
    
    # Sample astrological text with clear structure
    sample_text = """Chapter 1: Introduction to Nakshatras

Nakshatras are the 27 lunar mansions in Vedic astrology. Each nakshatra 
spans 13 degrees and 20 minutes of the ecliptic.

The Moon's position in a particular nakshatra at birth is considered 
highly significant for determining one's nature and destiny.

Section 1.1: The First Nakshatra

Ashwini, the first nakshatra, is ruled by Ketu. It spans from 0° to 
13°20' in sidereal Aries.

People born under Ashwini are known for their swift nature, healing 
abilities, and pioneering spirit. They are often doctors, healers, or 
those who work in emergency services.

The deity associated with Ashwini is the Ashwini Kumaras, the divine 
physicians of the gods. This connection gives Ashwini natives their 
natural healing abilities.

Section 1.2: Planetary Aspects

In Vedic astrology, planets cast aspects to specific houses from their 
position. This is different from Western astrology.

Mars aspects the 4th, 7th, and 8th houses from its position. This gives 
Mars its aggressive and protective nature in these areas.

Jupiter aspects the 5th, 7th, and 9th houses. These are considered 
benefic aspects that bring wisdom and expansion.

Saturn aspects the 3rd, 7th, and 10th houses. Saturn's aspects bring 
discipline, delay, and lessons in these areas of life."""
    
    # Initialize splitter
    splitter = ContextualSplitter(chunk_size=300, chunk_overlap=50)
    
    # Split text
    chunks = splitter.split_text(sample_text)
    
    print(f"\nOriginal text length: {len(sample_text)} characters")
    print(f"Number of chunks: {len(chunks)}")
    print("\nChunks:")
    print("-" * 70)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i} ({len(chunk)} chars):")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)


def test_knowledge_base():
    """Test the knowledge base functionality."""
    print_section("Testing Knowledge Base")
    
    # Initialize knowledge base with test collection
    kb = KnowledgeBase(
        collection_name="test_astrology_kb",
        persist_directory="./test_chroma_db"
    )
    
    # Clear any existing data
    print("\nClearing test knowledge base...")
    kb.clear()
    
    # Check docs directory
    docs_path = Path("docs")
    if not docs_path.exists():
        print(f"\nCreating docs directory...")
        docs_path.mkdir(exist_ok=True)
        print("⚠ No PDF files found. Please add PDF files to the 'docs' directory.")
        print("  Example: Place astrological texts, Parashara Hora, etc.")
        return kb
    
    # List PDF files
    pdf_files = list(docs_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n⚠ No PDF files found in 'docs' directory")
        print("  To test ingestion, add some PDF files to the docs/ folder")
        
        # Create a test document instead
        print("\nCreating test knowledge from sample text...")
        test_chunks = [
            "Ashwini nakshatra is ruled by Ketu and spans from 0 to 13.33 degrees in Aries. "
            "The natives are swift, pioneering, and often work as healers.",
            
            "Mars aspects the 4th, 7th, and 8th houses from its position. "
            "This gives Mars aggressive and protective influence in relationships and hidden matters.",
            
            "Jupiter aspects the 5th, 7th, and 9th houses, bringing wisdom, "
            "expansion, and benefic influence to children, partnerships, and dharma.",
            
            "Gandanta zones are critical junctions between water and fire signs. "
            "Planets in Gandanta experience transformation and karmic intensity.",
            
            "The Moon's nakshatra at birth determines the dasha periods. "
            "Each nakshatra is ruled by a planet that influences the native's destiny."
        ]
        
        # Manually add test documents
        embeddings = kb.embedding_function.embed_documents(test_chunks)
        ids = [f"test_chunk_{i}" for i in range(len(test_chunks))]
        metadata = [
            {"source": "test_data", "chunk_index": i, "total_chunks": len(test_chunks)}
            for i in range(len(test_chunks))
        ]
        
        kb.collection.add(
            documents=test_chunks,
            embeddings=embeddings,
            metadatas=metadata,
            ids=ids
        )
        
        print(f"✓ Added {len(test_chunks)} test chunks")
    else:
        print(f"\nFound {len(pdf_files)} PDF files:")
        for pdf in pdf_files:
            print(f"  - {pdf.name}")
        
        # Ingest PDFs
        print("\nIngesting PDFs...")
        chunks_count = kb.ingest_pdfs("docs", chunk_size=1000, chunk_overlap=200)
        print(f"✓ Ingested {chunks_count} chunks")
    
    # Get stats
    stats = kb.get_stats()
    print(f"\nKnowledge Base Statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Number of sources: {stats['source_count']}")
    print(f"  Sources: {', '.join(stats['sources'])}")
    
    return kb


def test_search(kb: KnowledgeBase):
    """Test semantic search functionality."""
    print_section("Testing Semantic Search")
    
    if kb.collection.count() == 0:
        print("\n⚠ Knowledge base is empty. Skipping search tests.")
        return
    
    # Test queries
    test_queries = [
        "What is the significance of Ashwini nakshatra?",
        "How does Mars aspect other planets?",
        "Explain Gandanta zones in astrology",
        "What are the planetary dasha periods?",
        "Jupiter's special aspects"
    ]
    
    for query in test_queries:
        print(f"\n{'─' * 70}")
        print(f"Query: {query}")
        print('─' * 70)
        
        results = kb.search_knowledge(query, top_k=3)
        
        if not results:
            print("  No results found")
            continue
        
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Source: {result['metadata']['source']}")
            print(f"  Distance: {result['distance']:.4f}" if result['distance'] else "")
            
            # Show content preview
            content = result['content']
            preview_length = 150
            if len(content) > preview_length:
                print(f"  Content: {content[:preview_length]}...")
            else:
                print(f"  Content: {content}")


def main():
    """Run all Phase 3 tests."""
    print_section("Phase 3: RAG System Test Suite")
    
    # Test 1: Contextual Splitter
    test_contextual_splitter()
    
    # Test 2: Knowledge Base Initialization
    kb = test_knowledge_base()
    
    # Test 3: Semantic Search
    if kb:
        test_search(kb)
    
    print_section("✓ Phase 3 Tests Completed")
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Add PDF files to the 'docs' directory")
    print("2. Run: python ingest_knowledge.py --docs-dir docs")
    print("3. Test queries: python ingest_knowledge.py --query 'your question'")
    print("4. Clear and reingest: python ingest_knowledge.py --clear --docs-dir docs")


if __name__ == "__main__":
    main()
