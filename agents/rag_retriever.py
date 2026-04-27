"""
RAG Retriever Module
Handles PDF ingestion and knowledge retrieval using ChromaDB.
Consolidates the RAG system from Phase 3.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import logging

from langchain_community.document_loaders import PyPDFLoader
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextualSplitter:
    """
    Smart text splitter that respects document structure.
    Keeps paragraphs intact and respects section boundaries.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.paragraph_pattern = re.compile(r'\n\s*\n')
        self.section_pattern = re.compile(
            r'\n\s*(?:Chapter|Section|\d+\.)\s+[A-Z][^\n]*\n',
            re.IGNORECASE
        )
    
    def split_text(self, text: str) -> List[str]:
        """Split text into contextually coherent chunks."""
        sections = self._split_by_sections(text)
        all_chunks = []
        
        for section in sections:
            chunks = self._split_section(section)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split text by major section boundaries."""
        sections = []
        last_end = 0
        
        for match in self.section_pattern.finditer(text):
            if match.start() > last_end:
                sections.append(text[last_end:match.start()].strip())
            last_end = match.start()
        
        if last_end < len(text):
            sections.append(text[last_end:].strip())
        
        return sections if sections else [text]
    
    def _split_section(self, section: str) -> List[str]:
        """Split a section into paragraph-aware chunks."""
        paragraphs = self.paragraph_pattern.split(section)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if para_size > self.chunk_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                sub_chunks = self._split_large_paragraph(para)
                chunks.extend(sub_chunks)
                continue
            
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                
                if self.chunk_overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1]]
                    current_size = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(para)
            current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split a large paragraph by sentences."""
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


class RAGRetriever:
    """
    RAG-based knowledge retrieval system.
    Handles PDF ingestion, embedding generation, and semantic search.
    """
    
    def __init__(
        self,
        collection_name: str = "astrology_knowledge",
        persist_directory: str = "./chroma_db",
        embedding_type: str = "auto"
    ):
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        
        # Initialize embeddings
        self.embedding_function = self._initialize_embeddings(embedding_type)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Astrological domain knowledge"}
        )
        
        logger.info(f"RAG Retriever initialized: {self.collection.count()} documents")
    
    def _initialize_embeddings(self, embedding_type: str):
        """Initialize embedding function."""
        if embedding_type == "auto":
            # Try OpenAI first, fallback to HuggingFace
            if os.getenv("OPENAI_API_KEY"):
                embedding_type = "openai"
            else:
                embedding_type = "huggingface"
        
        if embedding_type == "openai":
            try:
                from langchain_openai import OpenAIEmbeddings
                logger.info("Using OpenAI embeddings")
                return OpenAIEmbeddings()
            except Exception as e:
                logger.warning(f"OpenAI embeddings failed: {e}")
                embedding_type = "huggingface"
        
        if embedding_type == "huggingface":
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                logger.info("Using HuggingFace embeddings (local)")
                return HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
                raise
        
        raise ValueError(f"Unsupported embedding type: {embedding_type}")
    
    def ingest_pdfs(
        self,
        pdf_directory: str = "data/pdfs",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> int:
        """
        Ingest all PDF files from a directory.
        
        Args:
            pdf_directory: Directory containing PDF files
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between chunks
        
        Returns:
            Number of chunks ingested
        """
        pdf_path = Path(pdf_directory)
        
        if not pdf_path.exists():
            logger.warning(f"Directory not found: {pdf_directory}")
            return 0
        
        pdf_files = list(pdf_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_directory}")
            return 0
        
        logger.info(f"Found {len(pdf_files)} PDF files to ingest")
        
        splitter = ContextualSplitter(chunk_size, chunk_overlap)
        
        all_chunks = []
        chunk_metadata = []
        
        for pdf_file in pdf_files:
            logger.info(f"Processing: {pdf_file.name}")
            
            try:
                loader = PyPDFLoader(str(pdf_file))
                pages = loader.load()
                
                full_text = "\n\n".join([page.page_content for page in pages])
                chunks = splitter.split_text(full_text)
                
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    chunk_metadata.append({
                        "source": pdf_file.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    })
                
                logger.info(f"  → Created {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                continue
        
        if not all_chunks:
            return 0
        
        # Generate embeddings and store
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        
        try:
            embeddings = self.embedding_function.embed_documents(all_chunks)
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
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant chunks with metadata
        """
        if self.collection.count() == 0:
            logger.warning("Knowledge base is empty")
            return []
        
        try:
            query_embedding = self.embedding_function.embed_query(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
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
            logger.error(f"Error searching: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        count = self.collection.count()
        
        sources = set()
        if count > 0:
            sample = self.collection.get(limit=100)
            if sample['metadatas']:
                sources = {meta.get('source', 'unknown') for meta in sample['metadatas']}
        
        return {
            "total_chunks": count,
            "sources": list(sources),
            "source_count": len(sources)
        }


# Singleton instance
_rag_retriever = None


def get_rag_retriever(
    collection_name: str = "astrology_knowledge",
    persist_directory: str = "./chroma_db"
) -> RAGRetriever:
    """
    Get singleton RAGRetriever instance.
    
    Args:
        collection_name: ChromaDB collection name
        persist_directory: Directory for persistence
    
    Returns:
        RAGRetriever instance
    """
    global _rag_retriever
    
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever(collection_name, persist_directory)
    
    return _rag_retriever
