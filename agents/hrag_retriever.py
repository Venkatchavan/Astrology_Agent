"""
H-RAG Retriever — Hierarchical Retrieval Augmented Generation
=============================================================

Architecture (two-level hierarchy):

  PDF ──► Parent chunks (large, ~2000 chars, section-aware)
               └─► Child chunks (small, ~400 chars, for precise search)

Two separate ChromaDB collections:
  • hrag_parents  — stores large context chunks (NOT embedded)
  • hrag_children — stores small search chunks (embedded + indexed)

Retrieval flow:
  Query ─► embed ─► search children ─► collect parent_ids ─► fetch parents
  Returns: parent text (rich context) ranked by child hit count

This gives precise retrieval (child) with full context (parent).
"""

import re
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Optional

from langchain_community.document_loaders import PyPDFLoader
import chromadb

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hierarchical Splitter
# ---------------------------------------------------------------------------

class HierarchicalSplitter:
    """
    Splits a document into parent/child chunk pairs.

    Parent chunks:
      - Large (~2000 chars), section-aware — used for LLM context
    Child chunks:
      - Small (~400 chars) split from each parent — used for vector search
    """

    SECTION_RE = re.compile(
        r'\n\s*(?:Chapter|Section|CHAPTER|SECTION|\d+\.\s+[A-Z])[^\n]*\n',
        re.IGNORECASE,
    )
    SENTENCE_RE = re.compile(r'(?<=[.!?])\s+')
    PARA_RE = re.compile(r'\n\s*\n')

    def __init__(
        self,
        parent_size: int = 2000,
        child_size: int = 400,
        child_overlap: int = 50,
    ):
        self.parent_size = parent_size
        self.child_size = child_size
        self.child_overlap = child_overlap

    # ---- public API --------------------------------------------------------

    def split_into_parents(self, text: str) -> List[str]:
        """Split full document text into large section-aware parent chunks."""
        sections = self._split_by_sections(text)
        parents: List[str] = []
        for section in sections:
            parents.extend(self._chunk_text(section, self.parent_size, overlap=0))
        return [p for p in parents if len(p.strip()) > 60]

    def split_parent_into_children(self, parent: str) -> List[str]:
        """Split a single parent chunk into small child chunks."""
        children = self._chunk_text(parent, self.child_size, self.child_overlap)
        return [c for c in children if len(c.strip()) > 20]

    # ---- private helpers ---------------------------------------------------

    def _split_by_sections(self, text: str) -> List[str]:
        sections: List[str] = []
        last_end = 0
        for match in self.SECTION_RE.finditer(text):
            if match.start() > last_end:
                chunk = text[last_end : match.start()].strip()
                if chunk:
                    sections.append(chunk)
            last_end = match.start()
        tail = text[last_end:].strip()
        if tail:
            sections.append(tail)
        return sections or [text]

    def _chunk_text(self, text: str, size: int, overlap: int) -> List[str]:
        """Paragraph-aware greedy chunker with optional overlap."""
        paragraphs = [p.strip() for p in self.PARA_RE.split(text) if p.strip()]
        chunks: List[str] = []
        current: List[str] = []
        current_size = 0

        for para in paragraphs:
            if len(para) > size:
                # Flush current
                if current:
                    chunks.append('\n\n'.join(current))
                    current, current_size = [], 0
                # Split oversized paragraph by sentence
                chunks.extend(self._split_by_sentences(para, size, overlap))
                continue

            if current_size + len(para) > size and current:
                chunks.append('\n\n'.join(current))
                if overlap > 0 and current:
                    # Keep last paragraph as overlap seed
                    current = [current[-1]]
                    current_size = len(current[0])
                else:
                    current, current_size = [], 0

            current.append(para)
            current_size += len(para)

        if current:
            chunks.append('\n\n'.join(current))
        return chunks

    def _split_by_sentences(self, text: str, size: int, overlap: int) -> List[str]:
        sentences = self.SENTENCE_RE.split(text)
        chunks: List[str] = []
        current: List[str] = []
        current_size = 0

        for sent in sentences:
            if current_size + len(sent) > size and current:
                chunks.append(' '.join(current))
                current, current_size = [], 0
            current.append(sent)
            current_size += len(sent)

        if current:
            chunks.append(' '.join(current))
        return chunks


# ---------------------------------------------------------------------------
# H-RAG Retriever
# ---------------------------------------------------------------------------

class HierarchicalRAGRetriever:
    """
    H-RAG: Hierarchical Retrieval Augmented Generation.

    Two ChromaDB collections:
      • hrag_parents  — large context chunks (stored, not embedded)
      • hrag_children — small search chunks (embedded + indexed)

    Each child carries a ``parent_id`` pointing to its parent.

    Retrieval:
      1. Embed query → search children (top_k * 3 candidates)
      2. Collect parent_ids, count hits per parent
      3. Rank parents by hit count (desc), then by closest child distance (asc)
      4. Fetch & return top_k parent chunks with rich context
    """

    PARENT_COLLECTION = "hrag_astrology_parents"
    CHILD_COLLECTION = "hrag_astrology_children"

    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        parent_size: int = 2000,
        child_size: int = 400,
        child_overlap: int = 50,
    ):
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.parent_size = parent_size
        self.child_size = child_size
        self.child_overlap = child_overlap

        # ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.parent_col = self.client.get_or_create_collection(
            name=self.PARENT_COLLECTION,
            metadata={"description": "H-RAG parent (context) chunks"},
        )
        self.child_col = self.client.get_or_create_collection(
            name=self.CHILD_COLLECTION,
            metadata={"description": "H-RAG child (search) chunks"},
        )

        # Local embeddings — no API key needed
        self.embedding_fn = self._load_embeddings()

        logger.info(
            f"H-RAG initialized — parents: {self.parent_col.count()}, "
            f"children: {self.child_col.count()}"
        )

    # ---- embeddings --------------------------------------------------------

    def _load_embeddings(self):
        """Use local HuggingFace sentence-transformers (no API key required)."""
        from langchain_huggingface import HuggingFaceEmbeddings
        logger.info("H-RAG: loading local embeddings (all-MiniLM-L6-v2)...")
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )

    # ---- ingestion ---------------------------------------------------------

    def ingest_pdfs(
        self,
        docs_dir: str = "data/pdfs",
        clear_existing: bool = False,
    ) -> int:
        """
        Ingest all PDFs and .txt files from docs_dir into the H-RAG hierarchy.

        Returns total number of child chunks created.
        """
        if clear_existing:
            logger.info("H-RAG: clearing existing collections...")
            try:
                self.client.delete_collection(self.PARENT_COLLECTION)
                self.client.delete_collection(self.CHILD_COLLECTION)
            except Exception:
                pass
            self.parent_col = self.client.get_or_create_collection(
                name=self.PARENT_COLLECTION
            )
            self.child_col = self.client.get_or_create_collection(
                name=self.CHILD_COLLECTION
            )

        docs_path = Path(docs_dir)
        pdf_files = list(docs_path.glob("*.pdf")) if docs_path.exists() else []
        txt_files = list(docs_path.glob("*.txt")) if docs_path.exists() else []
        all_files = pdf_files + txt_files

        if not all_files:
            logger.warning(f"H-RAG: no PDFs or .txt files found in '{docs_dir}'. Add files then rerun.")
            return 0

        splitter = HierarchicalSplitter(
            self.parent_size, self.child_size, self.child_overlap
        )
        total_children = 0

        for doc_path in all_files:
            logger.info(f"H-RAG ingesting: {doc_path.name}")
            try:
                if doc_path.suffix.lower() == ".pdf":
                    pages = PyPDFLoader(str(doc_path)).load()
                    full_text = "\n\n".join(p.page_content for p in pages)
                else:  # .txt
                    full_text = doc_path.read_text(encoding="utf-8", errors="ignore")

                parents = splitter.split_into_parents(full_text)
                doc_children = 0

                for parent_text in parents:
                    parent_id = f"parent_{uuid.uuid4().hex[:16]}"

                    # Store parent (no embedding needed)
                    self.parent_col.add(
                        documents=[parent_text],
                        metadatas=[{"source": doc_path.name}],
                        ids=[parent_id],
                    )

                    # Split parent → children, embed, store
                    children = splitter.split_parent_into_children(parent_text)
                    if not children:
                        continue

                    child_embeddings = self.embedding_fn.embed_documents(children)
                    child_ids = [f"child_{uuid.uuid4().hex[:16]}" for _ in children]
                    child_metas = [
                        {"parent_id": parent_id, "source": doc_path.name}
                        for _ in children
                    ]

                    self.child_col.add(
                        documents=children,
                        embeddings=child_embeddings,
                        metadatas=child_metas,
                        ids=child_ids,
                    )
                    doc_children += len(children)

                total_children += doc_children
                logger.info(
                    f"  → {doc_path.name}: {len(parents)} parents, "
                    f"{doc_children} children"
                )

            except Exception as e:
                logger.error(f"Error ingesting {doc_path.name}: {e}")
                continue

        logger.info(
            f"✓ H-RAG ingestion complete — "
            f"{self.parent_col.count()} parents, {self.child_col.count()} children"
        )
        return total_children

    # ---- retrieval ---------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Hierarchical search:
          child vector search → parent_id mapping → ranked parent fetch

        Returns list of dicts with keys: content, metadata, child_hits, distance
        """
        if self.child_col.count() == 0:
            logger.warning("H-RAG: knowledge base is empty — run ingest_knowledge.py first.")
            return []

        query_emb = self.embedding_fn.embed_query(query)
        n_candidates = min(top_k * 4, self.child_col.count())

        child_res = self.child_col.query(
            query_embeddings=[query_emb],
            n_results=n_candidates,
        )

        if not child_res["documents"] or not child_res["documents"][0]:
            return []

        # Aggregate hits and best distance per parent
        parent_hits: Dict[str, int] = {}
        parent_best_dist: Dict[str, float] = {}

        for i, meta in enumerate(child_res["metadatas"][0]):
            pid = meta.get("parent_id")
            if not pid:
                continue
            dist = child_res["distances"][0][i] if child_res.get("distances") else 999.0
            parent_hits[pid] = parent_hits.get(pid, 0) + 1
            if pid not in parent_best_dist or dist < parent_best_dist[pid]:
                parent_best_dist[pid] = dist

        # Rank: most child hits first, then closest distance
        ranked = sorted(
            parent_hits.keys(),
            key=lambda pid: (-parent_hits[pid], parent_best_dist.get(pid, 999.0)),
        )[:top_k]

        if not ranked:
            return []

        fetched = self.parent_col.get(ids=ranked)
        results: List[Dict] = []
        for i, pid in enumerate(fetched["ids"]):
            results.append({
                "content": fetched["documents"][i],
                "metadata": fetched["metadatas"][i],
                "child_hits": parent_hits.get(pid, 1),
                "distance": parent_best_dist.get(pid),
            })

        return results

    # ---- utility -----------------------------------------------------------

    def get_stats(self) -> Dict:
        return {
            "total_chunks": self.child_col.count(),
            "total_parents": self.parent_col.count(),
            "total_children": self.child_col.count(),
        }


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_hrag_instance: Optional[HierarchicalRAGRetriever] = None


def get_hrag_retriever(
    persist_directory: str = "./chroma_db",
) -> HierarchicalRAGRetriever:
    """Return (or create) the singleton H-RAG retriever."""
    global _hrag_instance
    if _hrag_instance is None:
        _hrag_instance = HierarchicalRAGRetriever(persist_directory)
    return _hrag_instance
