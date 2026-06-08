"""
End-to-end ask(): retrieve relevant chunks, then generate a grounded answer via Groq.
"""

import logging
from typing import Optional

from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL, N_RESULTS, WEAK_DISTANCE_THRESHOLD
from retrieve import retrieve

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an interview preparation assistant. Your job is to answer questions using ONLY the information in the retrieved document excerpts provided by the user.

Rules you must follow without exception:
1. Answer exclusively from the retrieved documents. Do not draw on your training knowledge.
2. If the documents do not contain enough information to answer the question, respond with exactly: "I don't have enough information in my documents to answer that."
3. Always cite the source document(s) your answer draws from, using the filename shown in each excerpt header (e.g., "According to interviewingio_netflix_guide.txt, ...").
4. Be specific — quote or closely paraphrase the documents rather than paraphrasing vaguely."""

_client = None  # module-level cache so we don't rebuild the client on every call


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key "
                "(get one free at https://console.groq.com)."
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def ask(question: str, k: int = N_RESULTS, companies: Optional[list] = None) -> dict:
    """Run the full RAG pipeline for a question.

    Returns:
        {
            "answer":  str,          # grounded LLM response
            "sources": list[str],    # deduplicated source filenames
            "chunks":  list[dict],   # raw retrieved chunks (for debugging)
        }
    """
    chunks = retrieve(question, k=k, companies=companies)

    context_blocks = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )

    # Retrieval-confidence gate: when even the closest chunk is a weak match,
    # warn the model so it prefers the Rule 2 refusal over stitching an answer
    # out of loosely related context.
    min_distance = min((c["distance"] for c in chunks), default=1.0)
    confidence_note = ""
    if min_distance > WEAK_DISTANCE_THRESHOLD:
        confidence_note = (
            "Note: retrieval confidence is low for this query — the documents may not "
            "contain the specific information requested. If they do not, refuse per Rule 2.\n\n"
        )

    user_message = (
        f"{confidence_note}"
        f"Retrieved documents:\n{context_blocks}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the retrieved documents above. Cite your sources by filename."
    )

    sources = list(dict.fromkeys(c["source"] for c in chunks))  # ordered, deduplicated
    error_response = {
        "answer": "An error occurred while generating the answer. Please try again later.",
        "sources": [],
        "chunks": chunks,
    }

    client = _get_client()  # raises on missing API key (a config error, not an API failure)
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
    except Exception:
        logger.exception("Groq API call failed")
        return error_response

    # Guard against an unexpected/empty response shape before indexing into it.
    if not (response and response.choices and response.choices[0].message
            and response.choices[0].message.content):
        logger.error("Unexpected Groq response structure: %r", response)
        return error_response

    answer = response.choices[0].message.content
    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    # Quick smoke-test from the command line
    import sys
    q = " ".join(sys.argv[1:]) or "What values does Netflix prioritize in behavioral interviews?"
    result = ask(q)
    print("\n--- Answer ---")
    print(result["answer"])
    print("\n--- Sources ---")
    for s in result["sources"]:
        print(f"  • {s}")
