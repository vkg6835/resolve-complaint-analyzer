from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ARTIFACTS = ROOT / "artifacts"
STATIC = ROOT / "static"
DB_PATH = Path(os.environ.get("RESOLVE_DB", str(DATA / "complaints.sqlite3")))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
LLM_MODEL = os.environ.get("OLLAMA_MODEL", "gemma:2b")
EMBED_MODEL = "all-MiniLM-L6-v2 (ONNX int8)"
EMBED_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
EMBED_PATH = ROOT / "models" / "minilm"
DATASET_REVISION = "1846984189f2bc0ac51c6fc3a600fa9e1714e0c6"
SEED = 127
