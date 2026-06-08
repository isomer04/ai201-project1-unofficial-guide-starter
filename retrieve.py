"""
Retrieval layer: load the persistent ChromaDB collection and return top-k chunks.
"""

import chromadb
from chromadb.utils import embedding_functions

from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

_collection = None  # module-level cache so we don't reload on every call


def _get_collection():
    global _collection
    if _collection is None:
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=f"sentence-transformers/{EMBEDDING_MODEL}"
        )
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(CHROMA_COLLECTION, embedding_function=ef)
    return _collection


def retrieve(query: str, k: int = N_RESULTS, companies: list = None) -> list:
    """Return top-k chunks as dicts: {text, source, company, distance}.

    companies — optional list of company names to restrict results to
    (e.g. ["Netflix"]). When set, only those companies' documents are
    searched; pass None (the "All" filter) to search every document.
    """
    col = _get_collection()
    where = {"company": {"$in": companies}} if companies else None
    res = col.query(query_texts=[query], n_results=k, where=where)

    return [
        {
            "text": doc,
            "source": meta["source"],
            "company": meta["company"],
            "distance": dist,
        }
        for doc, meta, dist in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        )
    ]
