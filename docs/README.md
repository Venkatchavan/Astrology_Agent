# Astrology Hybrid Agent - docs Directory

This directory should contain PDF files with astrological domain knowledge.

## Recommended Content

Place PDF files here containing:

1. **Classical Texts**
   - Brihat Parashara Hora Shastra
   - Jataka Parijata
   - Phaladeepika
   - Saravali

2. **Nakshatra Information**
   - Detailed nakshatra descriptions
   - Pada characteristics
   - Ruling planets and deities

3. **Planetary Aspects & Yogas**
   - Aspect rules (Parashara system)
   - Raja Yogas
   - Dhana Yogas
   - Special combinations

4. **Interpretative Guidelines**
   - House significations
   - Planetary significations
   - Dasha interpretations

## Usage

After adding PDF files to this directory, run:

```bash
python ingest_knowledge.py --docs-dir docs
```

This will:
- Load all PDFs using contextual splitting
- Generate embeddings (OpenAI or HuggingFace)
- Store chunks in ChromaDB for semantic search
- Make content available for RAG queries

## Testing

Test the knowledge base with a query:

```bash
python ingest_knowledge.py --query "What are the effects of Mars in 7th house?"
```

## Clear and Reingest

To clear existing data and reingest:

```bash
python ingest_knowledge.py --clear --docs-dir docs
```
