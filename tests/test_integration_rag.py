"""
Integration / evaluation tests for the REAL RAG pipeline.

Unlike test_retrieve_and_ask.py (fully mocked, fast, free), these tests hit the
real persistent ChromaDB index and — for the generation tests — the real Groq
LLM. This is the layer that verifies RAG *quality*: retrieval relevance and
answer grounding, not just that the wiring is connected.

These tests are OPT-IN. pytest.ini deselects the `integration` marker by default,
so a plain `pytest` run stays fast and offline. Run this layer explicitly:

    pytest -m integration -v

Prerequisites (tests skip cleanly when missing, they do not fail):
  * chroma_db/ must be built first:  python ingest.py
  * GROQ_API_KEY must be set (.env)  — only the generation tests need it.

Expected outcomes are anchored to the measured findings in planning.md
(e.g. Netflix questions retrieve strongly; the Apple system-design question is a
documented corpus gap, encoded here as an xfail so it stays visible).
"""

import os

import pytest

from config import CHROMA_PATH, GROQ_API_KEY, WEAK_DISTANCE_THRESHOLD
import query as query_module
from retrieve import retrieve

pytestmark = pytest.mark.integration

# --- Skip guards: degrade gracefully instead of failing on an unbuilt index ---
_DB_READY = os.path.isdir(CHROMA_PATH) and os.path.exists(
    os.path.join(CHROMA_PATH, "chroma.sqlite3")
)
requires_db = pytest.mark.skipif(
    not _DB_READY, reason="chroma_db not built — run `python ingest.py` first"
)
requires_key = pytest.mark.skipif(
    not GROQ_API_KEY, reason="GROQ_API_KEY not set — needed for live generation"
)


# ---------------------------------------------------------------------------
# Retrieval quality — runs against the real ChromaDB index (no LLM, no key).
# ---------------------------------------------------------------------------
@requires_db
class TestRetrievalQuality:
    def test_strong_topic_match_is_relevant_and_confident(self):
        """A Netflix question surfaces Netflix chunks at a strong (sub-threshold)
        distance — the recall+confidence baseline measured in planning.md (Q1)."""
        results = retrieve(
            "What values and behaviors does Netflix prioritize in behavioral interviews?",
            k=5,
        )
        assert results, "expected at least one chunk for a well-covered topic"
        companies = [r["company"] for r in results]
        assert "Netflix" in companies, f"no Netflix chunk in top-5: {companies}"
        # Strong match: the closest chunk should beat the low-confidence gate.
        assert min(r["distance"] for r in results) < WEAK_DISTANCE_THRESHOLD

    def test_results_are_ranked_closest_first(self):
        """ChromaDB returns chunks in ascending-distance order; retrieve() preserves it."""
        results = retrieve("how should I prepare for a behavioral interview?", k=5)
        distances = [r["distance"] for r in results]
        assert distances == sorted(distances), f"not closest-first: {distances}"

    @pytest.mark.parametrize("company", ["Netflix", "Amazon"])
    def test_company_filter_restricts_to_that_company(self, company):
        """The $in metadata filter is a hard guarantee: every returned chunk
        belongs to the requested company (precision of the filter itself)."""
        results = retrieve("interview tips", k=5, companies=[company])
        assert results, f"filter for {company} returned nothing"
        assert all(r["company"] == company for r in results), [
            r["company"] for r in results
        ]

    @pytest.mark.parametrize(
        "question, companies, expected_company",
        [
            ("What does Netflix value in interviews?", ["Netflix"], "Netflix"),
            ("What are Amazon's leadership principles?", ["Amazon"], "Amazon"),
        ],
    )
    def test_recall_golden_set(self, question, companies, expected_company):
        """Small golden set: each company-scoped question must recall a chunk from
        the company whose docs actually contain the answer."""
        results = retrieve(question, k=5, companies=companies)
        assert expected_company in [r["company"] for r in results]

    @pytest.mark.xfail(
        reason="Documented corpus gap (planning.md Q5): no Apple system-design "
        "content exists, so Netflix chunks fill every slot. Tracked, not silently "
        "ignored — will XPASS if Apple sources are added.",
        strict=False,
    )
    def test_apple_system_design_gap(self):
        results = retrieve(
            "How does Apple evaluate system design thinking?",
            k=5,
            companies=["Apple", "Netflix"],
        )
        assert "Apple" in [r["company"] for r in results]


# ---------------------------------------------------------------------------
# Generation quality — runs the full pipeline against the real Groq LLM.
# ---------------------------------------------------------------------------
@requires_db
@requires_key
class TestGenerationQuality:
    def test_grounded_answer_has_sources_and_stays_on_topic(self):
        """End-to-end ask() returns a non-empty, cited answer for an in-corpus
        question, and the answer actually mentions the subject it retrieved."""
        result = query_module.ask(
            "What does Netflix value in behavioral interviews?", k=5
        )
        assert result["answer"].strip(), "empty answer"
        assert result["sources"], "no sources cited"
        assert result["chunks"], "no chunks retrieved"
        assert "netflix" in result["answer"].lower()

    def test_refuses_when_answer_is_not_in_corpus(self):
        """Faithfulness/grounding check: an out-of-domain question must trigger the
        Rule 2 refusal rather than a hallucinated answer from model training data."""
        result = query_module.ask("What is the chemical formula for water?")
        assert "don't have enough information" in result["answer"].lower(), (
            f"expected refusal, got: {result['answer']!r}"
        )
