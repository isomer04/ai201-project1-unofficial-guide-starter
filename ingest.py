"""
Build (or rebuild) the persistent ChromaDB collection from documents/*.txt.
Run once after adding or changing documents: python ingest.py
"""

import glob
import os

import chromadb
from chromadb.utils import embedding_functions

from config import CHROMA_COLLECTION, CHROMA_PATH, DOCS_PATH, EMBEDDING_MODEL

COMPANY_BY_FILE = {
    "glassdoor_amazon_sde_interview.txt": "Amazon",
    "glassdoor_amazon_sde2_interview.txt": "Amazon",
    "amazon_leadership_principles_official.txt": "Amazon",
    "glassdoor_google_swe_interview.txt": "Google",
    "blind_meta_e4_onsite.txt": "Meta",
    "netflix_interview_recently.txt": "Netflix",
    "interviewingio_netflix_guide.txt": "Netflix",
    "blind_apple_interview.txt": "Apple",
    "devto_faang_interview_prep.txt": "General",
    "substack_behavioral_interview_myths.txt": "General",
}


def recursive_chunk(text, chunk_size=400, separators=("\n\n", "\n", ". ", " ")):
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []
    sep = next((s for s in separators if s in text), "")
    if not sep:
        return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size)]
    parts, chunks, cur = text.split(sep), [], ""
    for part in parts:
        if len(cur) + len(part) + len(sep) <= chunk_size:
            cur += part + sep
        else:
            if cur.strip():
                chunks.append(cur.strip())
            if len(part) > chunk_size:
                chunks.extend(recursive_chunk(part, chunk_size, separators[1:]))
                cur = ""
            else:
                cur = part + sep
    if cur.strip():
        chunks.append(cur.strip())
    return [c for c in chunks if c]


def merge_runts(chunks, min_len=80):
    out = []
    for c in chunks:
        if out and len(out[-1]) < min_len:
            out[-1] = out[-1] + " " + c
        else:
            out.append(c)
    if len(out) > 1 and len(out[-1]) < min_len:
        out[-2] = out[-2] + " " + out.pop()
    return out


def add_overlap(chunks, overlap=50):
    out = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            tail = chunks[i - 1][-overlap:]
            space = tail.find(" ")
            if space != -1:
                tail = tail[space + 1:]
            chunk = tail + " " + chunk
        out.append(chunk)
    return out


def build_chunks(chunk_size=400):
    docs, metas, ids = [], [], []
    for path in sorted(glob.glob(f"{DOCS_PATH}/*.txt")):
        fname = os.path.basename(path)
        company = COMPANY_BY_FILE.get(fname)
        if company is None:
            raise ValueError(
                f"No company mapping for '{fname}'. Add it to COMPANY_BY_FILE "
                f'(use "General" for non-company-specific sources) so it is not '
                f"silently mislabeled."
            )
        with open(path, encoding="utf-8") as f:
            text = f.read()
        file_chunks = add_overlap(merge_runts(recursive_chunk(text, chunk_size)))
        for i, ch in enumerate(file_chunks):
            docs.append(ch)
            metas.append({"source": fname, "company": company})
            ids.append(f"{fname}::{i}")
    return docs, metas, ids


def main():
    docs, metas, ids = build_chunks()
    n_files = len(set(m["source"] for m in metas))
    print(f"Chunked {len(docs)} chunks from {n_files} files")

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=f"sentence-transformers/{EMBEDDING_MODEL}"
    )
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(CHROMA_COLLECTION)
        print(f"Deleted existing collection '{CHROMA_COLLECTION}'")
    except Exception as e:
        # Expected on first run (no collection yet); surface the reason rather
        # than swallowing it silently so a real failure is still visible.
        print(f"No existing collection '{CHROMA_COLLECTION}' to delete (or delete failed): {e}")

    col = client.create_collection(
        CHROMA_COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    col.add(documents=docs, metadatas=metas, ids=ids)
    print(f"Stored {len(docs)} chunks in ChromaDB at '{CHROMA_PATH}'")


if __name__ == "__main__":
    main()
