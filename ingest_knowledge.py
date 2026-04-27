"""
H-RAG Knowledge Ingestion Script
=================================
Ingests PDF documents from the docs/ folder into the Hierarchical RAG system.

Two-level hierarchy:
  Parent chunks (~2000 chars, section-aware)  → stored as context
  Child chunks  (~400 chars, from each parent) → embedded + indexed

Usage:
    # Ingest PDFs (adds to existing, safe to re-run)
    python ingest_knowledge.py

    # Ingest from a custom directory
    python ingest_knowledge.py --docs-dir my_pdfs

    # Clear everything and re-ingest
    python ingest_knowledge.py --clear

    # Test a query against the knowledge base
    python ingest_knowledge.py --query "effects of retrograde Saturn"

    # Show current knowledge base stats only
    python ingest_knowledge.py --stats
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest PDFs into the H-RAG (Hierarchical RAG) knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ingest_knowledge.py                        # ingest docs/ folder
  python ingest_knowledge.py --docs-dir my_pdfs     # custom folder
  python ingest_knowledge.py --clear                # clear + reingest
  python ingest_knowledge.py --query "Moon nakshatra interpretation"
  python ingest_knowledge.py --stats                # show stats only
        """,
    )
    parser.add_argument(
        "--docs-dir",
        default="data/pdfs",
        help="Directory containing PDF/txt files (default: data/pdfs/)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing H-RAG collections before ingesting",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Run a test search query after ingestion",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show knowledge base statistics and exit",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results for test query (default: 3)",
    )

    args = parser.parse_args()

    try:
        from agents.hrag_retriever import HierarchicalRAGRetriever
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Run: pip install langchain-huggingface sentence-transformers chromadb pypdf")
        sys.exit(1)

    # ── Stats only ─────────────────────────────────────────────────────────────
    if args.stats:
        hrag = HierarchicalRAGRetriever()
        stats = hrag.get_stats()
        print("\n" + "=" * 60)
        print("H-RAG KNOWLEDGE BASE STATS")
        print("=" * 60)
        print(f"  Parent chunks : {stats['total_parents']:>6}  (rich context)")
        print(f"  Child chunks  : {stats['total_children']:>6}  (vector-indexed)")
        print("=" * 60)
        return

    # ── Ingest ─────────────────────────────────────────────────────────────────
    docs_path = Path(args.docs_dir)
    if not docs_path.exists():
        logger.warning(f"Directory '{docs_path}' does not exist. Creating it.")
        docs_path.mkdir(parents=True)

    pdf_files = list(docs_path.glob("*.pdf")) + list(docs_path.glob("*.txt"))
    if not pdf_files:
        print("\n" + "=" * 60)
        print("NO PDFs FOUND")
        print("=" * 60)
        print(f"  Add Vedic astrology PDFs/txts to: {docs_path.resolve()}/")
        print("  Suggested texts:")
        print("    • Brihat Parashara Hora Shastra")
        print("    • Nakshatra — The Lunar Mansions (Dennis Harness)")
        print("    • Light on Life (Hart de Fouw)")
        print("    • Fundamentals of Astrology (M. Ramakrishna Bhat)")
        print("\nThen re-run: python ingest_knowledge.py")
        print("=" * 60 + "\n")

    hrag = HierarchicalRAGRetriever()

    if pdf_files:
        hrag.ingest_pdfs(
            docs_dir=str(docs_path),
            clear_existing=args.clear,
        )

        stats = hrag.get_stats()
        print("\n" + "=" * 60)
        print("H-RAG INGESTION COMPLETE")
        print("=" * 60)
        print(f"  Parent chunks : {stats['total_parents']:>6}  (rich context)")
        print(f"  Child chunks  : {stats['total_children']:>6}  (vector-indexed)")
        print("=" * 60 + "\n")

    # ── Test query ─────────────────────────────────────────────────────────────
    if args.query:
        logger.info(f"Testing H-RAG query: '{args.query}'")
        results = hrag.search(args.query, top_k=args.top_k)

        if not results:
            print("No results found (knowledge base may be empty).")
        else:
            print(f"\n{'='*60}")
            print(f"H-RAG RESULTS for: \"{args.query}\"")
            print(f"{'='*60}")
            for i, res in enumerate(results, 1):
                src = res["metadata"].get("source", "Unknown")
                hits = res.get("child_hits", "?")
                dist = res.get("distance")
                dist_str = f"{dist:.4f}" if dist is not None else "N/A"
                print(f"\n[Result {i}] Source: {src} | Child hits: {hits} | Distance: {dist_str}")
                print("-" * 60)
                content = res["content"]
                print(content[:500] + ("..." if len(content) > 500 else ""))
            print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
