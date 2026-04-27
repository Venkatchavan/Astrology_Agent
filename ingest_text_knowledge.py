"""
Quick script to ingest text files into ChromaDB knowledge base.
"""

import logging
from pathlib import Path
from agents import RAGRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_text_file(text_file: Path):
    """Ingest a text file into the knowledge base."""
    logger.info(f"Reading {text_file}...")
    
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    logger.info(f"Text length: {len(text)} characters")
    
    # Initialize RAG retriever
    logger.info("Initializing RAG retriever...")
    rag = RAGRetriever(
        collection_name="astrology_knowledge",
        persist_directory="chroma_db"
    )
    
    # Clear existing data
    logger.info("Clearing existing knowledge base...")
    try:
        rag.client.delete_collection("astrology_knowledge")
        logger.info("✓ Cleared old collection")
    except Exception as e:
        logger.info(f"No existing collection to clear: {e}")
    
    # Reinitialize
    rag = RAGRetriever(
        collection_name="astrology_knowledge",
        persist_directory="chroma_db"
    )
    
    # Split text into chunks using ContextualSplitter
    logger.info("Splitting text into chunks...")
    from agents.rag_retriever import ContextualSplitter
    
    splitter = ContextualSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    logger.info(f"Created {len(chunks)} chunks")
    
    # Add to knowledge base
    logger.info("Adding chunks to ChromaDB...")
    
    # Generate embeddings
    embeddings = rag.embedding_function.embed_documents(chunks)
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": text_file.name, "chunk_index": i} for i in range(len(chunks))]
    
    rag.collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    logger.info(f"✓ Added {len(chunks)} chunks to knowledge base")
    
    # Verify
    stats = rag.get_stats()
    logger.info(f"✓ Knowledge base ready: {stats['total_chunks']} chunks")
    
    # Test query
    logger.info("\nTesting with sample query...")
    results = rag.search("What are the characteristics of Ashlesha nakshatra?", top_k=2)
    
    for i, result in enumerate(results, 1):
        logger.info(f"\nResult {i}:")
        logger.info(f"  Text: {result['content'][:200]}...")
        logger.info(f"  Source: {result['metadata'].get('source', 'unknown')}")
    
    return stats


if __name__ == "__main__":
    text_file = Path("data/pdfs/sample_vedic_text.txt")
    
    if not text_file.exists():
        logger.error(f"Text file not found: {text_file}")
        exit(1)
    
    stats = ingest_text_file(text_file)
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ Knowledge base successfully initialized!")
    logger.info("=" * 70)
