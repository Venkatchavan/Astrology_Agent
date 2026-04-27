# Phase 3: RAG System - Quick Reference

## Components Created

### 1. Core Module: `ingest_knowledge.py`

**ContextualSplitter Class**
- Smart text splitting that respects document structure
- Keeps paragraphs together
- Handles section boundaries
- Maintains semantic coherence

**KnowledgeBase Class**
- PDF ingestion with PyPDFLoader
- ChromaDB persistence
- Embedding generation (OpenAI or HuggingFace)
- Semantic search functionality

### 2. Knowledge Module: `knowledge/__init__.py`
- Singleton pattern for knowledge base
- Unified interface for RAG access

### 3. Test Suite: `test_rag.py`
- Tests contextual splitter
- Tests knowledge base initialization
- Tests semantic search

### 4. Integration Demo: `demo_integration.py`
- Shows complete pipeline: Math → Logic → RAG

## Usage

### Basic Ingestion
```bash
# Ingest PDFs from docs directory
python ingest_knowledge.py --docs-dir docs

# Clear and reingest
python ingest_knowledge.py --clear --docs-dir docs
```

### Search Knowledge Base
```bash
# Test a query
python ingest_knowledge.py --query "What are nakshatras?"

# More specific query
python ingest_knowledge.py --query "Mars aspects in 7th house"
```

### Python API
```python
from ingest_knowledge import KnowledgeBase

# Initialize
kb = KnowledgeBase()

# Ingest PDFs
kb.ingest_pdfs("docs", chunk_size=1000, chunk_overlap=200)

# Search
results = kb.search_knowledge("explain retrograde planets", top_k=3)

for result in results:
    print(result['content'])
    print(result['metadata'])
```

### Integration with Other Layers
```python
from engine import EphemerisEngine
from agents import calculate_aspects
from ingest_knowledge import KnowledgeBase

# Calculate chart (Math Layer)
engine = EphemerisEngine()
chart = engine.calculate_chart(dt, lat, lon)

# Apply rules (Logic Layer)
aspects = calculate_aspects(chart)

# Query knowledge (RAG Layer)
kb = KnowledgeBase()
moon_nak = chart['Moon']['nakshatra']['nakshatra_name']
results = kb.search_knowledge(f"significance of {moon_nak}")
```

## Key Features

### Contextual Splitting
- **NOT** simple character count splitting
- Respects paragraph boundaries
- Identifies section headers
- Maintains context with overlapping chunks
- Smart handling of large paragraphs (splits by sentences)

### Embedding Options
1. **OpenAI** (requires API key): High quality, cloud-based
   - Set `OPENAI_API_KEY` environment variable
   - Automatic fallback to HuggingFace if not available

2. **HuggingFace** (local): Privacy-friendly, no API needed
   - Uses `sentence-transformers/all-MiniLM-L6-v2`
   - Runs entirely on your machine

### ChromaDB Storage
- Persistent storage in `./chroma_db/`
- Efficient semantic search
- Metadata tracking (source file, chunk index, etc.)
- Can handle large document collections

## File Structure
```
Astrology_Hybrid_Agent/
├── ingest_knowledge.py      # Main RAG module
├── knowledge/
│   └── __init__.py          # Module interface
├── docs/                    # PDF storage
│   └── README.md           # Instructions
├── chroma_db/              # ChromaDB persistence (auto-created)
├── test_chroma_db/         # Test database (from test_rag.py)
├── test_rag.py             # Test suite
└── demo_integration.py      # Full pipeline demo
```

## Next Steps

The RAG system is ready to:
1. Ingest classical astrological texts
2. Provide context-aware retrieval
3. Integrate with LangGraph orchestration (Phase 4)

Add your PDF files to `docs/` directory and run the ingestion script!
