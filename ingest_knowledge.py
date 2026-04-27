"""
Knowledge Base Ingestion System (Phase 3)
RAG system for ingesting and searching astrological domain knowledge from PDFs.

This module provides:
1. ContextualSplitter - Smart text splitter that respects paragraphs and structure
2. KnowledgeBase - RAG system with ChromaDB storage and semantic search
3. CLI interface for ingesting PDFs and testing queries

Usage:
    # Ingest PDFs
    python ingest_knowledge.py --docs-dir docs
    
    # Test query
    python ingest_knowledge.py --query "explain nakshatras"
    
    # Clear and reingest
    python ingest_knowledge.py --clear --docs-dir docs
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import logging

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings

# Configure embeddings - supports both OpenAI and local HuggingFace
try:
    from langchain_openai import OpenAIEmbeddings
    EMBEDDINGS_AVAILABLE = "openai"
except ImportError:
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        EMBEDDINGS_AVAILABLE = "huggingface"
    except ImportError:
        EMBEDDINGS_AVAILABLE = None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextualSplitter:
    """
    Smart text splitter that respects document structure and keeps paragraphs together.
    
    This splitter is context-aware and tries to:
    1. Keep paragraphs intact
    2. Respect section boundaries
    3. Maintain semantic coherence
    4. Avoid breaking mid-sentence when possible
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """
        Initialize the contextual splitter.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Overlap between chunks to maintain context
            min_chunk_size: Minimum chunk size before forcing a split
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Paragraph boundary patterns (double newline, section headers, etc.)
        self.paragraph_pattern = re.compile(r'\n\s*\n')
        self.section_pattern = re.compile(
            r'\n\s*(?:Chapter|Section|\d+\.)\s+[A-Z][^\n]*\n',
            re.IGNORECASE
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into contextually coherent chunks.
        
        Args:
            text: Input text to split
        
        Returns:
            List of text chunks
        """
        # First, identify major section boundaries
        sections = self._split_by_sections(text)
        
        # Then split each section into paragraph-aware chunks
        all_chunks = []
        for section in sections:
            chunks = self._split_section(section)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split text by major section boundaries."""
        # Look for chapter/section headers
        sections = []
        last_end = 0
        
        for match in self.section_pattern.finditer(text):
            if match.start() > last_end:
                sections.append(text[last_end:match.start()].strip())
            last_end = match.start()
        
        # Add remaining text
        if last_end < len(text):
            sections.append(text[last_end:].strip())
        
        # If no sections found, return whole text as single section
        return sections if sections else [text]
    
    def _split_section(self, section: str) -> List[str]:
        """Split a section into paragraph-aware chunks."""
        # Split by paragraphs
        paragraphs = self.paragraph_pattern.split(section)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # If single paragraph is larger than chunk_size, split it
            if para_size > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph by sentences
                sub_chunks = self._split_large_paragraph(para)
                chunks.extend(sub_chunks)
                continue
            
            # If adding this paragraph exceeds chunk_size
            if current_size + para_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with overlap (last paragraph)
                if self.chunk_overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1]]
                    current_size = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_size = 0
            
            # Add paragraph to current chunk
            current_chunk.append(para)
            current_size += para_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split a large paragraph by sentences."""
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


class KnowledgeBase:
    """
    RAG-based knowledge base for astrological domain knowledge.
    
    Handles PDF ingestion, embedding generation, and semantic search.
    """
    
    def __init__(
        self,
        collection_name: str = "astrology_knowledge",
        persist_directory: str = "./chroma_db",
        embedding_type: str = "auto"
    ):
        """
        Initialize the knowledge base.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data
            embedding_type: Type of embeddings ('openai', 'huggingface', or 'auto')
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )
        
        # Initialize embeddings
        self.embedding_function = self._initialize_embeddings(embedding_type)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Astrological domain knowledge from PDFs"}
        )
        
        logger.info(f"Knowledge base initialized: {collection_name}")
        logger.info(f"Current documents: {self.collection.count()}")
    
    def _initialize_embeddings(self, embedding_type: str):
        """Initialize embedding function based on availability."""
        if embedding_type == "auto":
            embedding_type = EMBEDDINGS_AVAILABLE
        
        if embedding_type == "openai":
            try:
                from langchain_openai import OpenAIEmbeddings
                logger.info("Using OpenAI embeddings")
                return OpenAIEmbeddings()
            except Exception as e:
                logger.warning(f"OpenAI embeddings failed: {e}, falling back to HuggingFace")
                embedding_type = "huggingface"
        
        if embedding_type == "huggingface":
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                logger.info("Using HuggingFace embeddings (local)")
                # Use a lightweight but effective model
                return HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
                raise
        
        raise ValueError(f"Unsupported embedding type: {embedding_type}")
    
    def ingest_pdfs(
        self,
        docs_directory: str = "docs",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> int:
        """
        Ingest all PDF files from a directory.
        
        Args:
            docs_directory: Directory containing PDF files
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between chunks
        
        Returns:
            Number of chunks ingested
        """
        docs_path = Path(docs_directory)
        
        if not docs_path.exists():
            logger.warning(f"Directory not found: {docs_directory}")
            return 0
        
        # Find all PDF files
        pdf_files = list(docs_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {docs_directory}")
            return 0
        
        logger.info(f"Found {len(pdf_files)} PDF files to ingest")
        
        # Initialize contextual splitter
        splitter = ContextualSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        all_chunks = []
        chunk_metadata = []
        
        # Process each PDF
        for pdf_file in pdf_files:
            logger.info(f"Processing: {pdf_file.name}")
            
            try:
                # Load PDF
                loader = PyPDFLoader(str(pdf_file))
                pages = loader.load()
                
                # Extract text from all pages
                full_text = "\n\n".join([page.page_content for page in pages])
                
                # Split using contextual splitter
                chunks = splitter.split_text(full_text)
                
                # Create metadata for each chunk
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    chunk_metadata.append({
                        "source": pdf_file.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk)
                    })
                
                logger.info(f"  → Created {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                continue
        
        if not all_chunks:
            logger.warning("No chunks created from PDFs")
            return 0
        
        # Generate embeddings and store in ChromaDB
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        
        try:
            # Get embeddings
            embeddings = self.embedding_function.embed_documents(all_chunks)
            
            # Add to ChromaDB
            ids = [f"chunk_{i}" for i in range(len(all_chunks))]
            
            self.collection.add(
                documents=all_chunks,
                embeddings=embeddings,
                metadatas=chunk_metadata,
                ids=ids
            )
            
            logger.info(f"✓ Successfully ingested {len(all_chunks)} chunks")
            return len(all_chunks)
            
        except Exception as e:
            logger.error(f"Error storing chunks: {e}")
            raise
    
    def search_knowledge(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, any]]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of dictionaries containing matched chunks and metadata
        """
        if self.collection.count() == 0:
            logger.warning("Knowledge base is empty")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_function.embed_query(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def clear(self):
        """Clear all documents from the knowledge base."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(name=self.collection_name)
        logger.info("Knowledge base cleared")
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about the knowledge base."""
        count = self.collection.count()
        
        # Get sample metadata if documents exist
        sources = set()
        if count > 0:
            sample = self.collection.get(limit=100)
            if sample['metadatas']:
                sources = {meta.get('source', 'unknown') for meta in sample['metadatas']}
        
        return {
            "total_chunks": count,
            "sources": list(sources),
            "source_count": len(sources),
            "collection_name": self.collection_name
        }


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest PDF knowledge into ChromaDB")
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Directory containing PDF files"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing knowledge base before ingesting"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Test query to search the knowledge base"
    )
    
    args = parser.parse_args()
    
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Clear if requested
    if args.clear:
        logger.info("Clearing existing knowledge base...")
        kb.clear()
    
    # Ingest PDFs
    logger.info(f"Ingesting PDFs from: {args.docs_dir}")
    chunks_count = kb.ingest_pdfs(args.docs_dir)
    
    # Show stats
    stats = kb.get_stats()
    logger.info(f"\nKnowledge Base Stats:")
    logger.info(f"  Total chunks: {stats['total_chunks']}")
    logger.info(f"  Sources: {stats['source_count']}")
    for source in stats['sources']:
        logger.info(f"    - {source}")
    
    # Test query if provided
    if args.query:
        logger.info(f"\nTesting query: '{args.query}'")
        results = kb.search_knowledge(args.query, top_k=3)
        
        for i, result in enumerate(results, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"  Source: {result['metadata']['source']}")
            logger.info(f"  Content preview: {result['content'][:200]}...")


if __name__ == "__main__":
    main()
