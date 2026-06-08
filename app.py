"""
Gradio web UI for the FAANG interview RAG system.
Run: python app.py  → open http://localhost:7860
"""

import logging
import re
from html import escape

import gradio as gr

from query import ask

# ── Company metadata ──────────────────────────────────────────────────────────

COMPANY_META = {
    "Amazon":  {"icon": "🛒", "color": "#f59e0b"},
    "Google":  {"icon": "🔍", "color": "#34d399"},
    "Meta":    {"icon": "👥", "color": "#60a5fa"},
    "Apple":   {"icon": "🍎", "color": "#a78bfa"},
    "Netflix": {"icon": "🎬", "color": "#f87171"},
}


def build_source_html(sources: list) -> str:
    if not sources:
        return "<p class='no-sources'>No sources retrieved.</p>"

    chips = []
    for source in sources:
        icon = "📄"
        # Match on filename tokens (split on _ and .) so e.g. "meta" only
        # matches blind_meta_e4_onsite.txt, never an incidental substring.
        tokens = set(re.split(r"[_.]", source.lower()))
        for company, meta in COMPANY_META.items():
            if company.lower() in tokens:
                icon = meta["icon"]
                break
        chips.append(
            f'<span class="source-chip">'
            f'<span class="source-icon">{icon}</span>'
            f'<span class="source-name">{escape(source)}</span>'
            f'</span>'
        )

    return (
        '<div class="sources-header">RETRIEVED FROM</div>'
        f'<div class="sources-container">{"".join(chips)}</div>'
    )


def handle_query(question: str, company: str):
    if not question.strip():
        return "*Please enter a question.*", build_source_html([])

    companies = None if company == "All" else [company]
    try:
        result = ask(question, companies=companies)
    except Exception:
        logging.exception("ask() failed for question=%r company=%r", question, company)
        return (
            "An error occurred while processing your question. Please try again later.",
            build_source_html([]),
        )
    return result["answer"], build_source_html(result["sources"])


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
/* ── Root & layout ─────────────────────────────────────────────────────── */
.gradio-container {
    max-width: 800px !important;
    margin: 0 auto !important;
    padding: 0 1rem 3rem !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
footer { display: none !important; }

/* ── Hero ───────────────────────────────────────────────────────────────── */
.hero-wrap { text-align: center; padding: 2.5rem 0 1.5rem; }
.hero-wrap h1 {
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 0.5rem;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-wrap p {
    color: #94a3b8;
    font-size: 0.88rem;
    max-width: 540px;
    margin: 0 auto;
    line-height: 1.6;
}

/* ── Company filter chips ───────────────────────────────────────────────── */
#company-filter { margin: 0.25rem 0 1rem; }
#company-filter > .wrap > label {
    border-radius: 20px !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}
#company-filter .wrap {
    justify-content: center !important;
    gap: 8px !important;
    flex-wrap: wrap;
}
#company-filter input[type="radio"] { display: none !important; }
#company-filter label span {
    display: block;
    padding: 6px 18px !important;
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 20px !important;
    color: #94a3b8 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
}
#company-filter label span:hover {
    border-color: #3b82f6 !important;
    color: #e2e8f0 !important;
}
#company-filter label:has(input:checked) span {
    background: #1d4ed8 !important;
    border-color: #3b82f6 !important;
    color: #dbeafe !important;
    font-weight: 600 !important;
}

/* ── Question input ─────────────────────────────────────────────────────── */
#question-input { margin-bottom: 0.75rem !important; }
#question-input label span {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

/* broad selectors to survive Gradio 6 DOM nesting */
textarea,
input[type="text"],
.block textarea,
#question-input textarea {
    font-size: 1rem !important;
    line-height: 1.6 !important;
    border-radius: 12px !important;
    border: 1.5px solid #475569 !important;
    background: #1e293b !important;
    color: #f1f5f9 !important;
    padding: 14px 16px !important;
    resize: none !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
    min-height: 78px !important;
    box-sizing: border-box !important;
    width: 100% !important;
    opacity: 1 !important;
    display: block !important;
}
textarea::placeholder,
.block textarea::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}
textarea:focus,
.block textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    outline: none !important;
}

/* ── Ask button ─────────────────────────────────────────────────────────── */
#ask-btn {
    border-radius: 10px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.15s ease !important;
}
#ask-btn:hover { opacity: 0.88 !important; }

/* ── Divider ────────────────────────────────────────────────────────────── */
.divider {
    border: none !important;
    border-top: 1px solid #1e293b !important;
    margin: 1.25rem 0 !important;
}

/* ── Answer panel ───────────────────────────────────────────────────────── */
#answer-panel {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 14px !important;
    padding: 1.5rem 1.75rem !important;
    min-height: 100px !important;
    margin-bottom: 1rem !important;
}
#answer-panel .prose {
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    line-height: 1.75 !important;
}
#answer-panel p, #answer-panel li { color: #e2e8f0 !important; }
#answer-panel em { color: #64748b !important; font-style: italic; }
#answer-panel strong { color: #93c5fd !important; }
#answer-panel h1, #answer-panel h2, #answer-panel h3 {
    color: #f1f5f9 !important;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 0.35rem;
    margin-top: 1.25rem;
}
#answer-panel code {
    background: #1e293b !important;
    color: #a78bfa !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.88em;
}

/* ── Sources ────────────────────────────────────────────────────────────── */
.sources-header {
    font-size: 0.7rem;
    font-weight: 700;
    color: #475569;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.sources-container { display: flex; flex-wrap: wrap; gap: 8px; }
.source-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #0f172a;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 7px 13px;
    transition: border-color 0.15s ease;
    cursor: default;
}
.source-chip:hover { border-color: #3b82f6; }
.source-icon { font-size: 0.85rem; }
.source-name {
    font-size: 0.78rem;
    font-family: 'SF Mono', 'Fira Code', 'Menlo', monospace;
    color: #64748b;
}
.no-sources { color: #475569 !important; font-size: 0.82rem; margin: 0; }

/* ── Examples ───────────────────────────────────────────────────────────── */
#examples-section { margin-top: 0.5rem; }
#examples-section .label-wrap span {
    color: #475569 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* Gradio 6 renders single-column examples as .gallery > .gallery-item buttons */
#examples-section .gallery {
    display: flex !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    gap: 10px !important;
    background: transparent !important;
    border: none !important;
}
#examples-section .gallery-item {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 999px !important;
    padding: 9px 18px !important;
    max-width: 340px !important;
    color: #94a3b8 !important;
    font-size: 0.82rem !important;
    line-height: 1.3 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    cursor: pointer;
    transition: all 0.15s ease;
}
#examples-section .gallery-item:hover {
    background: #243049 !important;
    border-color: #3b82f6 !important;
    color: #e2e8f0 !important;
    transform: translateY(-1px);
}
"""

# ── Layout ────────────────────────────────────────────────────────────────────

with gr.Blocks(title="FAANG Interview Prep") as demo:

    gr.HTML("""
        <div class="hero-wrap">
            <h1>FAANG Interview Prep</h1>
            <p>Ask anything about Amazon, Google, Meta, Apple, or Netflix interview culture —
            answers grounded in real interview documents, zero hallucination.</p>
        </div>
    """)

    company_filter = gr.Radio(
        choices=["All", "Amazon", "Google", "Meta", "Apple", "Netflix"],
        value="All",
        label="Filter by company",
        elem_id="company-filter",
    )

    question_box = gr.Textbox(
        label="Your question",
        placeholder="e.g. What values does Netflix prioritize in behavioral interviews?",
        lines=3,
        max_lines=6,
        elem_id="question-input",
    )

    ask_btn = gr.Button("Ask", variant="primary", elem_id="ask-btn", size="lg")

    gr.HTML('<hr class="divider">')

    answer_box = gr.Markdown(
        value="*Your answer will appear here after you ask a question.*",
        elem_id="answer-panel",
    )

    sources_box = gr.HTML(value="")

    gr.HTML('<hr class="divider">')

    gr.Examples(
        examples=[
            ["What specific values and behaviors does Netflix prioritize in behavioral interviews?"],
            ["What behaviors are red flags that Apple interviews look for negatively?"],
            ["What are the key structural elements of a strong technical decision story?"],
            ["What behavioral patterns appear in documented rejection reasons?"],
            ["What does Amazon look for with its Leadership Principles during interviews?"],
        ],
        inputs=[question_box],
        elem_id="examples-section",
        label="Examples",
    )

    ask_btn.click(
        handle_query,
        inputs=[question_box, company_filter],
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        handle_query,
        inputs=[question_box, company_filter],
        outputs=[answer_box, sources_box],
    )

if __name__ == "__main__":
    demo.launch(css=CSS, theme=gr.themes.Base())
