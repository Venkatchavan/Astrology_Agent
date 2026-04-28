# Vedic Astrology Agent

Fully local Vedic chart analysis system. No API keys required. Runs entirely on your machine using Ollama and a local vector store.

## Architecture

```
Input (IST datetime + lat/lon)
        │
        ▼
┌─────────────────────────────────────────────┐
│  engine/                Math Layer           │
│  ├── ephemeris_skyfield.py  (Skyfield/JPL)   │
│  ├── dasha_engine.py        (Vimshottari)    │
│  └── numerology.py                           │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  agents/                Logic Layer          │
│  ├── parashara.py    (aspects, D9)           │
│  ├── nadi.py         (elements, states)      │
│  └── numerology_expert.py                   │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  agents/hrag_retriever.py   Knowledge Layer  │
│  Hierarchical RAG — ChromaDB + MiniLM-L6-v2  │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  synthesizer/orchestrator.py  Synthesis      │
│  Ollama LLM (llama3.2 or any local model)   │
└─────────────┬───────────────────────────────┘
              │
              ▼
     output/<name>_<YYYYMMDD>_<HHMM>.md
```

## Prerequisites

```bash
# 1. Pull an Ollama model (one-time, ~2 GB)
ollama pull llama3.2

# 2. Install Python dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Build the H-RAG knowledge base from PDFs (one-time)
#    Place Vedic astrology PDFs in data/pdfs/ first
python ingest_knowledge.py
```

## Usage

All times must be in **IST (Indian Standard Time)**.

```bash
# Full analysis (H-RAG + Ollama synthesis)
python main.py --date "1999-12-16" --time "15:54" \
               --lat 12.9716 --lon 77.5946 \
               --name "Name" --location "Bangalore"

# Fact sheet only — no LLM, instant
python main.py --date "1999-12-16" --time "15:54" \
               --lat 12.9716 --lon 77.5946 --no-llm

# Skip RAG (faster, no knowledge base needed)
python main.py --date "1999-12-16" --time "15:54" \
               --lat 12.9716 --lon 77.5946 --no-rag

# Use a specific Ollama model
python main.py ... --model mistral
```

Output is auto-saved to `output/<name>_<YYYYMMDD>_<HHMM>.md`.

## H-RAG Knowledge Base

```bash
# Rebuild index after adding new PDFs to data/pdfs/
python ingest_knowledge.py --clear

# Check index stats
python ingest_knowledge.py --stats

# Test a query
python ingest_knowledge.py --query "Uttara Bhadrapada nakshatra Moon"
```

## Project Structure

```
Astrology_Agent/
├── main.py                    # CLI entry point
├── ingest_knowledge.py        # H-RAG index builder
├── requirements.txt
├── .env.example
│
├── engine/                    # Math layer
│   ├── ephemeris_skyfield.py  # Planets + Ascendant (Skyfield/NASA JPL de421.bsp)
│   ├── dasha_engine.py        # Vimshottari dasha
│   ├── numerology.py          # Numerology engine
│   └── data_loader.py         # CSV utilities
│
├── agents/                    # Logic + knowledge layers
│   ├── parashara.py           # Aspects, D9, divisional strength
│   ├── nadi.py                # Elements, retrograde, gandanta
│   ├── numerology_expert.py   # Numerology tags and harmony
│   └── hrag_retriever.py      # Hierarchical RAG (ChromaDB)
│
├── synthesizer/               # Synthesis layer
│   └── orchestrator.py        # Master pipeline (H-RAG + Ollama)
│
├── data/                      # Reference tables
│   ├── nakshatra_longitudes_27.csv
│   ├── nakshatra_padas_108.csv
│   ├── nakshatra_rulers.csv
│   ├── numerology_chaldean.csv
│   ├── numerology_pythagorean.csv
│   └── pdfs/                  # Vedic text PDFs (knowledge base source)
│
├── chroma_db/                 # H-RAG vector store (auto-generated, gitignored)
├── de421.bsp                  # NASA JPL ephemeris binary (gitignored)
└── output/                    # Generated chart reports (gitignored)
```

## Ephemeris Accuracy

Engine: Skyfield + NASA JPL de421.bsp, Lahiri ayanamsa. Verified against JHORA/Swiss Ephemeris.

| Planet | Accuracy |
|--------|----------|
| Sun, Mercury, Venus, Mars, Jupiter, Saturn | < 0.02° error |
| Rahu / Ketu | < 0.02° error |
| Ascendant sign / nakshatra / pada | Correct |
| Ascendant exact degree | ~0.75° gap vs Swiss Ephemeris (RAMC precision limit) |

## Notes

- `.env` is gitignored — copy `.env.example` and fill in if needed
- No cloud API keys are required; all LLM inference runs via Ollama
- `chroma_db/` and `de421.bsp` are gitignored (large, regeneratable)
