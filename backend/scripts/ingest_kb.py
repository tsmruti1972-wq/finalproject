import json
from pathlib import Path

import faiss

from app.config import INDEX_FILE, META_FILE, VECTOR_DIR
from app.rag import build_index


def main() -> None:
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    index, metadata = build_index()

    faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Ingested {len(metadata)} chunks into vector store")
    print(f"Index: {INDEX_FILE}")
    print(f"Metadata: {META_FILE}")


if __name__ == "__main__":
    main()
