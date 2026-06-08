import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Repo root, so storage/document paths resolve the same regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parent

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# --- Embeddings ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- Vector store ---
CHROMA_COLLECTION = "faang_interviews"
CHROMA_PATH = str(_REPO_ROOT / "chroma_db")

# --- Retrieval ---
N_RESULTS = 5
# Min cosine distance across the top-k chunks above which retrieval is treated as
# low-confidence; the generator is then nudged toward the Rule 2 refusal.
WEAK_DISTANCE_THRESHOLD = 0.55

# --- Documents ---
DOCS_PATH = str(_REPO_ROOT / "documents")
