"""
Manual retrieval-quality inspection (NOT a pytest test).

Runs real queries against the live ChromaDB index and prints the top chunks
with their distances, so you can eyeball how good retrieval actually is.

Run from the repo root (so ./chroma_db resolves):  python scripts/inspect_retrieval.py
"""

import pathlib
import sys
import textwrap

# Make the repo-root modules (retrieve, config, ...) importable when this
# script is launched from scripts/.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from retrieve import retrieve

queries = [
    ("What specific values and behaviors does Netflix prioritize in behavioral interviews?", ["Netflix"]),
    ("What are the key structural elements present in strong technical decision stories?", None),
    ("What specific behavioral patterns and attitudes appear in documented rejection reasons?", None),
]

for q, companies in queries:
    chunks = retrieve(q, k=5, companies=companies)
    scope = "+".join(companies) if companies else "ALL"
    print("=" * 90)
    print(f"Q: {q}")
    print(f"   scope: {scope}")
    print("-" * 90)
    for i, c in enumerate(chunks, 1):
        flag = "  <-- WEAK (>=0.5)" if c["distance"] >= 0.5 else ""
        preview = textwrap.shorten(c["text"].replace("\n", " "), width=120)
        print(f"  [{i}] dist={c['distance']:.3f}  {c['company']:8}  {c['source']}{flag}")
        print(f"      {preview}")
    print()
