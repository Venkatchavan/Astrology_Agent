"""
Knowledge Module - RAG System Integration
Provides unified interface for knowledge retrieval.
"""

from .ingest_knowledge import KnowledgeBase, ContextualSplitter

__all__ = ["KnowledgeBase", "ContextualSplitter", "get_knowledge_base"]


# Singleton instance
_kb_instance = None


def get_knowledge_base(
    collection_name: str = "astrology_knowledge",
    persist_directory: str = "./chroma_db",
    embedding_type: str = "auto"
) -> KnowledgeBase:
    """
    Get or create a singleton KnowledgeBase instance.
    
    Args:
        collection_name: Name of the ChromaDB collection
        persist_directory: Directory to persist ChromaDB data
        embedding_type: Type of embeddings ('openai', 'huggingface', or 'auto')
    
    Returns:
        KnowledgeBase instance
    """
    global _kb_instance
    
    if _kb_instance is None:
        _kb_instance = KnowledgeBase(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_type=embedding_type
        )
    
    return _kb_instance
