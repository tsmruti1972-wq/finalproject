from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DIR = BASE_DIR / "data" / "vector_store"
KB_DIR = BASE_DIR / "data" / "knowledge_base"
INDEX_FILE = VECTOR_DIR / "kb.faiss"
META_FILE = VECTOR_DIR / "metadata.json"
EMBED_DIM = 512
TOP_K = 4
MAX_CHARS_PER_CHUNK = 850
