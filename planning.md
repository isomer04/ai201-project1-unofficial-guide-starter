## Domain

Tech interview preparation advice for FAANG companies (Apple, Netflix, Google, Meta, Amazon). This knowledge is valuable but hard to find through official channels because companies don't publicly explain their interview culture, what they value, or red flags they watch for. Candidates share real experiences and insights on Reddit, LinkedIn, Medium, and blogs that official HR materials don't provide. Sources include behavioral interview expectations, culture fit signals, technical focus areas, and company-specific values.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG Pipeline                                 │
└─────────────────────────────────────────────────────────────────────┘

[1]                [2]                [3]              [4]          [5]
Documents      Chunking         Embeddings      Vector Store      Query
(raw text)     + Overlap        + Search        (similarity)    Generation
   ▼                ▼                ▼                ▼              ▼
┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ 10 files │──│Custom        │──│all-      │──│ChromaDB  │──│Groq      │
│(txt)     │  │recursive     │  │MiniLM-   │  │          │  │llama-    │
│ ~20 KB   │  │splitter      │  │L6-v2     │  │top-k=5   │  │3.3-70b   │
└──────────┘  │400 char cap  │  │(sbert)   │  │chunks    │  │(grounded)│
              │50 char       │  │          │  │          │  │answer    │
              │overlap       │  │          │  │          │  │          │
              └──────────────┘  └──────────┘  └──────────┘  └──────────┘
                     ▲                              ▲              ▲
                     │                              │              │
              134 chunks                    Semantic search     Interview Q
              (after runt-merge)           + ranking
```

**Stage 1 — Document Ingestion:** Read 10 text files (~38.5 KB total after cleaning) into memory.

**Stage 2 — Chunking:** Recursive character splitter (custom implementation) with 400-char cap and 50-char overlap, plus a runt-merge pass that folds short title fragments into their neighbor. Produces 134 chunks (avg 333 chars, range 107–500; max exceeds the 400 cap because 50-char overlap is prepended after splitting).

**Stage 3 — Embedding + Vector Store:** Encode each chunk with `sentence-transformers/all-MiniLM-L6-v2` (lightweight, no API key). Store embeddings in **ChromaDB** for fast similarity search.

**Stage 4 — Retrieval:** Given a user question, embed it and fetch the top 5 most similar chunks from ChromaDB (providing ~1.5–2.5 KB of context).

**Stage 5 — Generation:** Pass retrieved chunks + user question to Groq's llama-3.3-70b-versatile with a system prompt that enforces "answer using only these documents." Return grounded answer with citations.

## Documents

| # | Source | Type | URL | File |
|---|--------|------|-----|------|
| 1 | Glassdoor | Amazon SDE interview experiences | https://www.glassdoor.com/Interview/Amazon-Software-Development-Engineer-Interview-Questions-EI_IE6036.0,6_KO7,36.htm | documents/glassdoor_amazon_sde_interview.txt |
| 2 | Glassdoor | Amazon SDE II interview experiences | https://www.glassdoor.com/Interview/Amazon-Software-Development-Engineer-II-Interview-Questions-EI_IE6036.0,6_KO7,39.htm | documents/glassdoor_amazon_sde2_interview.txt |
| 3 | Glassdoor | Google SWE interview experiences | https://www.glassdoor.com/Interview/Google-Software-Engineer-Interview-Questions-EI_IE9079.0,6_KO7,24.htm | documents/glassdoor_google_swe_interview.txt |
| 4 | Blind | Meta E4 onsite writeup | https://www.teamblind.com/post/Meta-E4-onsite-interview-Q27rUDTa | documents/blind_meta_e4_onsite.txt |
| 5 | Amazon (official) | Leadership Principles | https://www.amazon.jobs/content/en/our-workplace/leadership-principles | documents/amazon_leadership_principles_official.txt |
| 6 | DEV Community | FAANG interview prep retrospective | https://dev.to/somadevtoo/i-failed-4-faang-interviews-before-learning-this-the-complete-coding-interview-preparation-guide-gjh | documents/devto_faang_interview_prep.txt |
| 7 | The Behavioral (Substack) | Why candidates fail behavioral interviews - 7 myths + Decode-Select-Deliver framework | https://thebehavioral.substack.com/p/why-you-fail-at-behavioral-interviews | documents/substack_behavioral_interview_myths.txt |
| 8 | Reddit | Netflix interview |https://www.reddit.com/r/leetcode/comments/1lh77b3/anyone_interview_at_netflix_recently/ | documents/netflix_interview_recently.txt |
| 9 | interviewing.io | Netflix interview guide | https://interviewing.io/guides/hiring-process/netflix | documents/interviewingio_netflix_guide.txt |
| 10 | Blind | Apple interview discussions | https://www.teamblind.com/company/Apple/posts/apple-interview | documents/blind_apple_interview.txt |

## Chunking Strategy

**Chunk size:** 400 characters (cap, not fixed — small sections stay small)

**Overlap:** 50 characters (about 1 sentence)

**Chunking method:** Paragraph-based recursive character splitting. Split first on paragraph breaks (`\n\n`), and only fall back to finer separators (`\n`, `. `, ` `) for the rare paragraph that exceeds the cap.

**Document profile:**
Documents follow a similar shape: a header line, then sections separated by blank lines, each containing a principle or insight paired with an example or quote.

- Total corpus: ~38.5 KB across 10 files (after cleaning), 168 paragraphs (avg 227 chars, max 809)
- Measured on this corpus: 400-char cap splits 9% of paragraphs (vs. 22% at 300, 5% at 500); after runt-merge the splitter yields 134 chunks. See Evaluation Findings.

**Why these choices fit your documents:**
The natural retrieval unit here is the *section*, because each blank-line-delimited paragraph is already one coherent principle+example (e.g., "Ownership:" + the supporting story). The strategy is therefore to chunk on paragraph boundaries, not arbitrary windows.

- **Why 400 and not 300:** a 300-char cap splits 27 of 159 paragraphs (16%) — routinely cutting a principle away from its example, which is exactly the failure we most want to avoid (see Anticipated Challenges). A 400-char cap leaves 99% of paragraphs intact while staying well under the embedding model's ~256-token (~1,000-char) limit, so no chunk gets silently truncated. We chose 400 over a larger cap (650+) to keep each chunk focused on a single topic: the chunker greedily merges adjacent paragraphs up to the cap, and a larger cap would merge *unrelated* sections into one chunk, blurring its embedding and diluting retrieval.
- **Why the 400 cap also helps small sections:** greedy packing merges runt fragments (e.g., a 29-char header line) into a neighbor, so we don't index near-meaningless tiny chunks.
- **Why 50-char overlap:** because we cut at natural paragraph boundaries there is little context to bridge, so a small overlap (~1 sentence) is enough to catch a point that spills across two paragraphs without bloating the index.

**Implementation approach:**
```python
def recursive_chunk(text, chunk_size=400, separators=["\n\n", "\n", ". ", " "]):
    """Paragraph-first splitter. Packs sections up to chunk_size; only the
    rare oversized paragraph recurses to a finer separator so the cap is
    always honored (unlike a single-pass split that leaves blocks over-cap)."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []
    sep = next((s for s in separators if s in text), "")
    if not sep:  # no separator left: hard cut as a last resort
        return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size)]

    parts, chunks, cur = text.split(sep), [], ""
    for part in parts:
        if len(cur) + len(part) + len(sep) <= chunk_size:
            cur += part + sep
        else:
            if cur.strip():
                chunks.append(cur.strip())
            if len(part) > chunk_size:           # oversized paragraph -> recurse
                chunks.extend(recursive_chunk(part, chunk_size, separators[1:]))
                cur = ""
            else:
                cur = part + sep
    if cur.strip():
        chunks.append(cur.strip())
    return [c for c in chunks if c]


def add_overlap(chunks, overlap=50):
    """Prepend the tail of the previous chunk so a point spanning a
    paragraph boundary isn't orphaned."""
    out = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            tail = chunks[i - 1][-overlap:]
            space = tail.find(" ")          # trim to a word boundary so the
            if space != -1:                 # overlap doesn't start mid-word
                tail = tail[space + 1:]
            chunk = tail + " " + chunk
        out.append(chunk)
    return out
```

*Note: the function above documents the exact behavior we want. Implementation can be vanilla Python or use a library if it matches this logic.*

**Limitations of this method (honest):**
- Relies on clean `\n\n` formatting. A future scraped/PDF source that is one wall of text would produce one oversized chunk before the finer separators kick in.
- Paragraph lengths are uneven, so chunk sizes vary (avg 333, range 107–500 chars; the max exceeds the 400 cap because 50-char overlap is prepended after splitting).
- Bullet lists (e.g., the 4-round onsite block) are one "paragraph" but really several items; splitting them at the cap is acceptable here but not semantically ideal.

**Final chunk count:** 134 chunks across 10 documents (measured on the current corpus, after the runt-merge pass; 145 before merge). Well above the 50-chunk minimum and well below 2,000 — in the healthy signal range for semantic retrieval.

## Retrieval Approach

**Embedding model:** all-MiniLM-L6-v2 (via sentence-transformers)

**Top-k:** 5 chunks per query

**Why this model:**
all-MiniLM-L6-v2 is lightweight, fast, and effective for semantic search on domain-specific text. It doesn't require GPU or API keys, which fits the free/lightweight requirement. It handles English well and works reasonably on behavioral/interview-focused language.

**Production tradeoff reflection:**
If cost weren't a constraint, I'd consider larger models like all-mpnet-base-v2 or e5-large for higher accuracy on domain-specific behavioral language. They better capture nuanced differences between similar interview concepts (e.g., "ownership" vs. "autonomy"). I'd also weigh embedding-based retrieval vs. a hybrid approach (keyword + semantic) to catch exact phrase matches that interviews candidates look for (like specific company values by name). Local deployment of a larger model would eliminate API costs while improving accuracy on company-specific terminology.

**Top-k justification:** 5 chunks provides 1.5–2.5 KB of context, enough for the LLM to see multiple examples and perspectives without overwhelming it. Too few (k=2–3) misses nuance; too many (k>10) dilutes signal with less relevant advice.

## Evaluation Plan

1. **Question:** "What specific values and behaviors does Netflix prioritize in behavioral interviews?"
   - **Expected answer:** Netflix emphasizes autonomy, high accountability, impact over effort, and decision-making without waiting for explicit approval. Documents should contain examples like "taking ownership from decision to results" and "measuring impact of actions."

2. **Question:** "What specific behaviors or qualities are red flags that Apple interviews look for negatively?"
   - **Expected answer:** Lack of attention to detail, not thinking about user experience, lack of craftsmanship/quality mindset, and insufficient consideration of privacy/security. Documents should clearly identify these as things to avoid or demonstrate negatively.

3. **Question:** "What are the key structural elements present in strong technical decision stories according to the documents?"
   - **Expected answer:** Documents should identify: ownership from conception to shipping, cross-functional collaboration mentioned, explicit discussion of trade-offs or constraints, focus on impact/outcomes, not just effort spent.

4. **Question:** "What specific behavioral patterns and attitudes appear in documented rejection reasons?"
   - **Expected answer:** Documents identify: blaming external circumstances, being defensive, lack of initiative/proactivity, poor clarification seeking, defensive communication, not demonstrating company values, and acknowledged technical gaps.

5. **Question:** "What are the documented differences in how Apple and Netflix each evaluate system design thinking?"
   - **Expected answer:** Apple's emphasis (documents state): long-term scalability, user experience, privacy, craftsmanship, quality over speed. Netflix's emphasis (documents state): speed/iteration cycles, performance under load, measurable business impact, rapid learning.

## Anticipated Challenges

1. **Inconsistent terminology across sources:** Reddit discussions use casual language ("ownership," "vibes") while blog posts use formal language ("strategic responsibility," "autonomy"). The embedding model might miss semantic equivalence when queries use different phrasing than documents. *Mitigation:* Larger overlap or post-retrieval synonym expansion.

2. **Company-specific advice bleeding across companies:** Documents mention all 5 companies, but advice for Amazon (leadership principles, operational excellence) differs from Netflix (speed, autonomy) or Apple (design, taste). Without explicit source filtering, a query about Netflix culture might retrieve Amazon advice. *Mitigation:* Include company name in chunks or add metadata filtering by company.

3. **Chunks splitting key examples:** Behavioral advice often pairs a principle with a specific example ("Move fast" → "shipped in 2 weeks, measured impact"). A too-small chunk might contain the principle but cut the example — this is why we chunk on paragraph boundaries with a 400-char cap (measured on the current 10-doc corpus: a 300-char cap splits 22% of paragraphs vs. 9% at 400, and 5% at 500). *Mitigation:* 50-char overlap bridges points that spill across a boundary; verify during evaluation and raise the cap toward 500 if examples still get cut.

4. **Cross-company comparison queries may surface retrieval gaps:** Q5 (Apple vs. Netflix system design thinking) depends on both documents containing explicit system design content. The Blind Apple thread may be too community-discussion-style to contain structured system design criteria. If retrieval can't find specific Apple system design content, this becomes a documented failure case — which is expected and acceptable per the evaluation requirements.

## Evaluation Findings (measured)

Ran each of the 5 evaluation questions through the retrieval pipeline (cap=400, k=5, MiniLM embeddings, ChromaDB) via `python _test_retrieval.py` and inspected the actual chunks returned. Corpus: 10 files, ~38.5 KB → **134 chunks** after chunking and runt-merge. Findings reported by inspecting retrieved chunks, not by assuming.

**Per-question results:**

| Q | Result | What retrieval returned |
|---|--------|--------------------------|
| Q1 Netflix values | **Pass** | 5/5 Netflix chunks, sim 0.63–0.73. Strong, on-topic coverage. |
| Q2 Apple red flags | **Partial / fail** | 2 Apple + 3 General chunks, but the Apple chunks are generic rejection/recruiting anecdotes ("are they really hiring?"), not a red-flag taxonomy. The expected answer (attention to detail, UX, craftsmanship, privacy) is **not present in the corpus**. Weak sims (≤0.51). |
| Q3 technical-story structure | **Pass-ish** | General storytelling chunks (Decode-Select-Deliver, STAR-is-table-stakes). Adequate but not company-specific. |
| Q4 rejection patterns | **Weak** | Mixed Meta/Apple/Netflix/General, all low sim (0.37–0.41). Coverage is thin; no single document enumerates rejection patterns. |
| Q5 Apple vs. Netflix system design | **Fail (accepted)** | 5/5 Netflix chunks, **zero Apple** even with the Apple filter enabled. Apple system-design content does not exist in the corpus. Confirms Anticipated Challenge #4 — documented, expected failure case. |

**Diagnosis (what the eval proved, vs. what we assumed):**
- The wrong/weak answers are driven by **corpus gaps** (Q2, Q5 — Apple lacks structured red-flag and system-design content), **not** by chunk size. Re-running at cap=300/400/500 does not create content that isn't there.
- **Company bleed is minimal on these questions.** Because each query names its company, the embeddings already rank the right company's chunks at the top. Measured: the company metadata filter changed exactly **1 chunk across all 5 questions** (and that chunk was irrelevant either way). The filter is kept as a cheap guard for future ambiguous queries that *don't* name a company — it is not the lever that improves these scores.

**Fixes applied as a result:**
- **Runt-merge** (`merge_runts`): greedy packing was flushing short source-title lines as standalone chunks (e.g., the Substack header was winning a top-k slot on Q4 purely by keyword overlap). Short fragments now merge into their neighbor so headers ride with content. Effect: 145 → 134 chunks, and Q4's top hit is now substantive instead of a bare title.
- **Company metadata** (`source`, `company` per chunk) added to enable `$in` filtering by company at query time.

**Honest limitations carried forward:**
- Q2 and Q5 remain weak/failed and are accepted as documented gaps; closing them requires *adding sources* with real Apple red-flag and system-design content, not tuning parameters.
- Low absolute similarities on Q4 (~0.4) indicate the corpus does not strongly cover "rejection patterns" as a unified topic.

## AI Tool Plan

1. **Chunking implementation:** I'll give Claude my chunking strategy section and ask it to write a paragraph-first recursive splitter with a 400-char cap and 50-char overlap. I expect a function that splits on `\n\n` and recurses to finer separators only for oversized paragraphs. I'll verify it on sample documents (confirming all chunks land under the cap and examples aren't cut) and adjust boundaries if needed.

2. **System prompt for grounding:** I'll ask Claude to draft a system prompt that instructs the LLM to only answer using retrieved documents and cite sources. Input: my evaluation plan and expected answers. Claude will produce a prompt that emphasizes "use only the provided interview documents" and "if the documents don't cover this, say so." I'll test it and tighten language if the model still hallucinates.

3. **Embedding and retrieval pipeline:** I'll describe my documents, chunking approach, and top-k=5 choice, then ask Claude to help implement ChromaDB integration with sentence-transformers. I expect working code for ingesting chunks, computing embeddings, and running similarity search. I'll override the retrieval query handling if it needs company filtering.