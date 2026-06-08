"""
Unit tests for retrieve() and ask().

Run with: pytest test_retrieve_and_ask.py -v
"""

import pytest
from unittest.mock import MagicMock, patch

import retrieve as retrieve_module
import query as query_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chroma_result(docs, sources, companies, distances):
    return {
        "documents": [docs],
        "metadatas": [[{"source": s, "company": c} for s, c in zip(sources, companies)]],
        "distances": [distances],
    }


def _make_groq_response(content: str):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# retrieve()
# ---------------------------------------------------------------------------

class TestRetrieve:
    def setup_method(self):
        retrieve_module._collection = None  # reset lazy cache before every test

    @patch("retrieve.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("retrieve.chromadb.PersistentClient")
    def test_result_shape(self, mock_client_cls, _mock_ef):
        """Each returned dict has text, source, company, and distance with correct values."""
        col = MagicMock()
        col.query.return_value = _make_chroma_result(
            ["Netflix values freedom and responsibility."],
            ["interviewingio_netflix_guide.txt"],
            ["Netflix"],
            [0.25],
        )
        mock_client_cls.return_value.get_collection.return_value = col

        results = retrieve_module.retrieve("What does Netflix value?", k=1)

        assert len(results) == 1
        r = results[0]
        assert r["text"] == "Netflix values freedom and responsibility."
        assert r["source"] == "interviewingio_netflix_guide.txt"
        assert r["company"] == "Netflix"
        assert r["distance"] == 0.25

    @patch("retrieve.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("retrieve.chromadb.PersistentClient")
    def test_company_filter_builds_where_clause(self, mock_client_cls, _mock_ef):
        """Passing companies=["Netflix"] adds a $in where-clause to the ChromaDB query."""
        col = MagicMock()
        col.query.return_value = _make_chroma_result(
            ["Netflix tip"], ["netflix.txt"], ["Netflix"], [0.3]
        )
        mock_client_cls.return_value.get_collection.return_value = col

        retrieve_module.retrieve("interview tips", k=1, companies=["Netflix"])

        col.query.assert_called_once_with(
            query_texts=["interview tips"],
            n_results=1,
            where={"company": {"$in": ["Netflix"]}},
        )

    @patch("retrieve.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("retrieve.chromadb.PersistentClient")
    def test_no_company_filter_passes_none(self, mock_client_cls, _mock_ef):
        """Passing companies=None omits the where-clause so all documents are searched."""
        col = MagicMock()
        col.query.return_value = _make_chroma_result(
            ["Generic advice"], ["devto.txt"], ["General"], [0.4]
        )
        mock_client_cls.return_value.get_collection.return_value = col

        retrieve_module.retrieve("FAANG prep", k=1, companies=None)

        col.query.assert_called_once_with(
            query_texts=["FAANG prep"],
            n_results=1,
            where=None,
        )

    @patch("retrieve.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("retrieve.chromadb.PersistentClient")
    def test_multiple_results_preserve_order(self, mock_client_cls, _mock_ef):
        """Results come back in the same rank order ChromaDB returns them (closest first)."""
        col = MagicMock()
        col.query.return_value = _make_chroma_result(
            ["Chunk A", "Chunk B", "Chunk C"],
            ["a.txt", "b.txt", "c.txt"],
            ["Amazon", "Google", "Meta"],
            [0.1, 0.3, 0.5],
        )
        mock_client_cls.return_value.get_collection.return_value = col

        results = retrieve_module.retrieve("leadership principles", k=3)

        assert len(results) == 3
        assert results[0]["text"] == "Chunk A"
        assert results[1]["company"] == "Google"
        assert results[2]["distance"] == 0.5

    @patch("retrieve.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("retrieve.chromadb.PersistentClient")
    def test_collection_is_cached_across_calls(self, mock_client_cls, _mock_ef):
        """ChromaDB PersistentClient is built only once; subsequent calls reuse the cached collection."""
        col = MagicMock()
        col.query.return_value = _make_chroma_result(
            ["text"], ["s.txt"], ["X"], [0.2]
        )
        mock_client_cls.return_value.get_collection.return_value = col

        retrieve_module.retrieve("q1", k=1)
        retrieve_module.retrieve("q2", k=1)

        assert mock_client_cls.call_count == 1  # PersistentClient built only once

    @patch("retrieve.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("retrieve.chromadb.PersistentClient")
    def test_multi_company_filter(self, mock_client_cls, _mock_ef):
        """A list of multiple companies is passed as-is into the $in operator."""
        col = MagicMock()
        col.query.return_value = _make_chroma_result(
            ["Netflix chunk", "Amazon chunk"],
            ["netflix.txt", "amazon.txt"],
            ["Netflix", "Amazon"],
            [0.2, 0.4],
        )
        mock_client_cls.return_value.get_collection.return_value = col

        retrieve_module.retrieve("behavioral", k=2, companies=["Netflix", "Amazon"])

        col.query.assert_called_once_with(
            query_texts=["behavioral"],
            n_results=2,
            where={"company": {"$in": ["Netflix", "Amazon"]}},
        )


# ---------------------------------------------------------------------------
# ask()
# ---------------------------------------------------------------------------

class TestAsk:
    def setup_method(self):
        query_module._client = None  # reset lazy cache before every test

    def _chunks(self, n=2, distance=0.3):
        return [
            {
                "text": f"Chunk {i} about interview prep.",
                "source": f"doc_{i}.txt",
                "company": "Netflix" if i % 2 == 0 else "Amazon",
                "distance": distance,
            }
            for i in range(n)
        ]

    @patch("query.retrieve")
    @patch("query.Groq")
    @patch("query.GROQ_API_KEY", "test-key")
    def test_returns_expected_keys(self, mock_groq_cls, mock_retrieve):
        """Return dict always contains answer, sources, and chunks keys with correct values."""
        chunks = self._chunks(n=2)
        mock_retrieve.return_value = chunks
        mock_groq_cls.return_value.chat.completions.create.return_value = (
            _make_groq_response("Netflix values candor.")
        )

        result = query_module.ask("What does Netflix value?")

        assert set(result.keys()) == {"answer", "sources", "chunks"}
        assert result["answer"] == "Netflix values candor."
        assert result["chunks"] == chunks

    @patch("query.retrieve")
    @patch("query.Groq")
    @patch("query.GROQ_API_KEY", "test-key")
    def test_sources_deduplicated_and_ordered(self, mock_groq_cls, mock_retrieve):
        """Duplicate source filenames are removed while preserving first-seen order."""
        mock_retrieve.return_value = [
            {"text": "a", "source": "netflix.txt", "company": "Netflix", "distance": 0.2},
            {"text": "b", "source": "amazon.txt", "company": "Amazon", "distance": 0.3},
            {"text": "c", "source": "netflix.txt", "company": "Netflix", "distance": 0.4},
        ]
        mock_groq_cls.return_value.chat.completions.create.return_value = (
            _make_groq_response("Answer.")
        )

        result = query_module.ask("question")

        assert result["sources"] == ["netflix.txt", "amazon.txt"]

    @patch("query.retrieve")
    @patch("query.Groq")
    @patch("query.GROQ_API_KEY", "test-key")
    def test_low_confidence_injects_warning(self, mock_groq_cls, mock_retrieve):
        """When the closest chunk distance exceeds WEAK_DISTANCE_THRESHOLD (0.55), a low-confidence note is prepended to the Groq prompt."""
        mock_retrieve.return_value = self._chunks(n=1, distance=0.8)  # above 0.55 threshold
        create = mock_groq_cls.return_value.chat.completions.create
        create.return_value = _make_groq_response("I don't have enough information.")

        query_module.ask("obscure niche question")

        user_msg = create.call_args.kwargs["messages"][1]["content"]
        assert "retrieval confidence is low" in user_msg

    @patch("query.retrieve")
    @patch("query.Groq")
    @patch("query.GROQ_API_KEY", "test-key")
    def test_high_confidence_no_warning(self, mock_groq_cls, mock_retrieve):
        """When the closest chunk distance is below the threshold, no confidence warning appears in the prompt."""
        mock_retrieve.return_value = self._chunks(n=1, distance=0.2)  # below 0.55 threshold
        create = mock_groq_cls.return_value.chat.completions.create
        create.return_value = _make_groq_response("Here is the answer.")

        query_module.ask("netflix behavioral interview")

        user_msg = create.call_args.kwargs["messages"][1]["content"]
        assert "retrieval confidence is low" not in user_msg

    @patch("query.retrieve")
    @patch("query.Groq")
    @patch("query.GROQ_API_KEY", "test-key")
    def test_empty_retrieval_degrades_gracefully(self, mock_groq_cls, mock_retrieve):
        """When retrieve() finds nothing, ask() still returns a well-formed result:
        empty sources/chunks, the low-confidence note fires (min distance falls back
        to 1.0 > 0.55), and the LLM is still called so it can issue the Rule 2 refusal."""
        mock_retrieve.return_value = []  # filter matched nothing / empty corpus
        create = mock_groq_cls.return_value.chat.completions.create
        create.return_value = _make_groq_response(
            "I don't have enough information in my documents to answer that."
        )

        result = query_module.ask("a question with no matching documents")

        assert result["sources"] == []
        assert result["chunks"] == []
        user_msg = create.call_args.kwargs["messages"][1]["content"]
        assert "retrieval confidence is low" in user_msg  # default=1.0 trips the gate
        assert result["answer"].startswith("I don't have enough information")

    @patch("query.GROQ_API_KEY", None)
    def test_missing_api_key_raises(self):
        """RuntimeError is raised immediately when GROQ_API_KEY is not set."""
        query_module._client = None
        with pytest.raises(RuntimeError, match="GROQ_API_KEY is not set"):
            query_module.ask("any question")

    @patch("query.retrieve")
    @patch("query.Groq")
    @patch("query.GROQ_API_KEY", "test-key")
    def test_companies_forwarded_to_retrieve(self, mock_groq_cls, mock_retrieve):
        """The companies kwarg is passed through unchanged to the underlying retrieve() call."""
        mock_retrieve.return_value = self._chunks(n=1)
        mock_groq_cls.return_value.chat.completions.create.return_value = (
            _make_groq_response("Answer.")
        )

        query_module.ask("Netflix culture", k=3, companies=["Netflix"])

        mock_retrieve.assert_called_once_with("Netflix culture", k=3, companies=["Netflix"])

    @patch("query.retrieve")
    @patch("query.Groq")
    @patch("query.GROQ_API_KEY", "test-key")
    def test_context_blocks_contain_source_headers(self, mock_groq_cls, mock_retrieve):
        """The Groq prompt includes [Source: filename] headers and the chunk text for each retrieved document."""
        mock_retrieve.return_value = [
            {"text": "Be yourself.", "source": "netflix.txt", "company": "Netflix", "distance": 0.2}
        ]
        create = mock_groq_cls.return_value.chat.completions.create
        create.return_value = _make_groq_response("Answer.")

        query_module.ask("interview tips")

        user_msg = create.call_args.kwargs["messages"][1]["content"]
        assert "[Source: netflix.txt]" in user_msg
        assert "Be yourself." in user_msg
