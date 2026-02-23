import json
import logging
import re
from dataclasses import dataclass
from hashlib import md5
from pathlib import Path

import faiss
import numpy as np

from .config import EMBED_DIM, INDEX_FILE, KB_DIR, MAX_CHARS_PER_CHUNK, META_FILE, TOP_K

logger = logging.getLogger(__name__)


@dataclass
class ChunkRecord:
    id: str
    title: str
    text: str


class RagStore:
    def __init__(self) -> None:
        self.index: faiss.Index | None = None
        self.metadata: list[dict[str, str]] = []

    def _tokens(self, text: str) -> list[str]:
        base = re.findall(r"[a-z0-9]+", text.lower())
        bigrams = [f"{base[i]}_{base[i + 1]}" for i in range(len(base) - 1)]
        return base + bigrams

    def _embed(self, texts: list[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), EMBED_DIM), dtype=np.float32)
        for row_idx, text in enumerate(texts):
            for token in self._tokens(text):
                digest = md5(token.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % EMBED_DIM
                matrix[row_idx, idx] += 1.0
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def load(self) -> None:
        if not INDEX_FILE.exists() or not META_FILE.exists():
            raise FileNotFoundError("Vector store not found. Run scripts/ingest_kb.py first.")

        self.index = faiss.read_index(str(INDEX_FILE))
        with open(META_FILE, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def query(self, query_text: str, top_k: int = TOP_K) -> list[dict]:
        if self.index is None:
            self.load()

        query_vec = self._embed([query_text])
        scores, indices = self.index.search(query_vec, top_k)

        docs: list[dict] = []
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx < 0 or idx >= len(self.metadata):
                continue
            rec = self.metadata[idx]
            docs.append(
                {
                    "id": rec["id"],
                    "title": rec["title"],
                    "text": rec["text"],
                    "score": float(score),
                }
            )
        return docs


def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    chunks: list[str] = []
    current = ""

    for block in blocks:
        candidate = f"{current}\n\n{block}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(block) <= max_chars:
                current = block
            else:
                for i in range(0, len(block), max_chars):
                    chunks.append(block[i : i + max_chars])
                current = ""

    if current:
        chunks.append(current)

    return chunks


def build_index(kb_dir: Path = KB_DIR) -> tuple[faiss.IndexFlatIP, list[dict[str, str]]]:
    files = sorted([p for p in kb_dir.glob("**/*") if p.suffix in {".md", ".txt"}])
    if not files:
        raise FileNotFoundError(f"No documents found in {kb_dir}")

    records: list[ChunkRecord] = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        title = file_path.stem.replace("_", " ").title()
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks, start=1):
            records.append(
                ChunkRecord(
                    id=f"{file_path.stem}-{i}",
                    title=title,
                    text=chunk,
                )
            )

    if not records:
        raise RuntimeError("Knowledge base files were found but no chunk records were created")

    embedder = RagStore()
    matrix = embedder._embed([r.text for r in records])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms

    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(matrix)

    metadata = [{"id": r.id, "title": r.title, "text": r.text} for r in records]
    logger.info("Built index with %s chunks from %s documents", len(metadata), len(files))
    return index, metadata
