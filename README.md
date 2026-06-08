# The Unofficial Guide — Project 1

**[▶ Watch the demo video (3.5 min)](demo_video/demo-web.mp4)** — three queries answered with source citations, one strong-retrieval case, one where the system struggles, one out-of-scope refusal, and a walkthrough of the evaluation report.

---

## Domain

Tech interview preparation advice for FAANG companies (Amazon, Google, Meta, Apple, Netflix). This knowledge is valuable but hard to find through official channels because companies don't publicly document their interview culture, what evaluators look for, or the behaviors that lead to rejection. Candidates share real experiences on Reddit, Blind, Glassdoor, and Substack that official HR materials never provide — specific values tested in behavioral rounds, red flags interviewers watch for, and what distinguishes a strong answer from one that looks fine on the surface but leads to a no-hire decision.

The system lets a candidate ask natural questions ("What does Netflix actually care about in behavioral interviews?") and get answers grounded in real candidate experiences and official company principles — not generic advice.

---

## Document Sources

| # | Source | Type | URL | Local file |
|---|--------|------|-----|-----------|
| 1 | Glassdoor | Amazon SDE interview experiences | https://www.glassdoor.com/Interview/Amazon-Software-Development-Engineer-Interview-Questions-EI_IE6036.0,6_KO7,36.htm | documents/glassdoor_amazon_sde_interview.txt |
| 2 | Glassdoor | Amazon SDE II interview experiences | https://www.glassdoor.com/Interview/Amazon-Software-Development-Engineer-II-Interview-Questions-EI_IE6036.0,6_KO7,39.htm | documents/glassdoor_amazon_sde2_interview.txt |
| 3 | Amazon (official) | Amazon Leadership Principles | https://www.amazon.jobs/content/en/our-workplace/leadership-principles | documents/amazon_leadership_principles_official.txt |
| 4 | Glassdoor | Google SWE interview experiences | https://www.glassdoor.com/Interview/Google-Software-Engineer-Interview-Questions-EI_IE9079.0,6_KO7,24.htm | documents/glassdoor_google_swe_interview.txt |
| 5 | Blind | Meta E4 onsite writeup | https://www.teamblind.com/post/Meta-E4-onsite-interview-Q27rUDTa | documents/blind_meta_e4_onsite.txt |
| 6 | Reddit (r/leetcode) | Netflix interview — recent experiences | https://www.reddit.com/r/leetcode/comments/1lh77b3/anyone_interview_at_netflix_recently/ | documents/netflix_interview_recently.txt |
| 7 | interviewing.io | Netflix full interview guide | https://interviewing.io/guides/hiring-process/netflix | documents/interviewingio_netflix_guide.txt |
| 8 | Blind | Apple interview discussions | https://www.teamblind.com/company/Apple/posts/apple-interview | documents/blind_apple_interview.txt |
| 9 | DEV Community | FAANG interview prep retrospective | https://dev.to/somadevtoo/i-failed-4-faang-interviews-before-learning-this-the-complete-coding-interview-preparation-guide-gjh | documents/devto_faang_interview_prep.txt |
| 10 | The Behavioral (Substack) | Why candidates fail behavioral interviews — 7 myths + Decode-Select-Deliver framework | https://thebehavioral.substack.com/p/why-you-fail-at-behavioral-interviews | documents/substack_behavioral_interview_myths.txt |

---

## Document Cleaning

Each document was cleaned manually before chunking to remove platform scaffolding that would pollute embeddings and dilute retrieval quality. The rule was: **remove anything that isn't the substantive interview content**; keep everything that helps a candidate prepare.

**What was stripped (by source type):**

- **Glassdoor** — date headers, "Anonymous Interview Candidate" labels, outcome/experience/difficulty badges, "Application" section headers, `Interview questions [1]` labels, `Answer question`, `Helpful`, `Share` buttons.
- **Blind** — usernames, current-company tags, standalone dates, vote triples (three bare numbers stacked vertically), `Reply`, `Like`, `Read more` truncation markers, `Poll` + participant counts, `Interview Experiences` / `Tech Industry` section labels.
- **Reddit** — `Upvote` / `Downvote` / `Reply` / `Award` / `Share` labels, vote counts, `OP` / `•` / relative timestamps (`1y ago`, `Edited`), `u/username avatar` lines.
- **dev.to** — hashtag header block (`#softwareengineering` etc.), affiliate disclosure, image caption lines (e.g. `coding interview prep cheat sheet`), discount codes and promotional sentences, `Additional Resources:` link list, sign-off.
- **interviewing.io** — `Learning Center` / `Guides` nav breadcrumb, duplicate title line, `Want to know if you're ready...` CTA, `See available times` button, trailing "Netflix interview replays" section.
- **Amazon official** — 16× `Download video transcript` lines interspersed between principles.
- **All files** — curly quotes and apostrophes → straight, em/en dashes → `-`, 3+ consecutive blank lines collapsed to one, trailing whitespace removed.

**What was kept:**

Interview narratives, actual questions asked, round-by-round structure, prep advice, outcome signals (no offer / difficult), anecdotes, and any company/role context needed to interpret the content.

**Source replacement:**

`quora_rejection_reasons.txt` originally contained an off-topic HR rant with no structured rejection analysis. It was replaced and renamed to `substack_behavioral_interview_myths.txt` — a cleaned version of [Why You Fail at Behavioral Interviews](https://thebehavioral.substack.com/p/why-you-fail-at-behavioral-interviews) (The Behavioral, Substack), which directly maps to the rejection-reason evaluation question: 7 concrete myths about behavioral interviews and a Decode-Select-Deliver prep framework.

**Verification step:**

After cleaning, each file was read in full to confirm: no nav text, no leftover UI scaffolding, no `Read more` / `Download video transcript` / vote counts remaining, and that the paragraph structure (blank-line-delimited blocks) was intact for the chunker.

---

## Chunking Strategy

**Chunk size:** 400 characters (a cap, not a fixed window). A 400-char cap splits only 9% of paragraphs in this corpus vs. 22% at 300 chars and 5% at 500. That's the right tradeoff for documents structured as principle + example pairs: a 300-char cap routinely cuts the example away from its principle (the key failure to avoid), while a 500-char cap merges unrelated sections into one chunk and dilutes its embedding.

**Overlap:** 50 characters prepended from the tail of the previous chunk. Because we chunk on natural paragraph boundaries, there's little mid-point context to bridge — a small overlap (~1 sentence) is enough to catch a point that spills across paragraphs without bloating the index. The tail is snapped to the next word boundary before prepending so no chunk starts mid-word.

**Additional pass — runt merging:** After splitting, any chunk shorter than 80 characters is folded into its neighbor. Without this pass, short header lines (e.g., "Netflix Interview Guide") win top-k slots on loosely related queries by keyword overlap alone, even though they carry almost no semantic signal. Runt-merging forces headers to ride with their content.

**Why these choices fit your documents:** The 10 source files share a consistent structure: a short header line, then blank-line-delimited sections where each paragraph contains one complete idea — a value, an anecdote, or a piece of advice. The natural retrieval unit is the section, not an arbitrary character window. Chunking on `\n\n` preserves that semantic unit in almost every case; the recursive fallback to `\n`, `. `, and ` ` only fires for the 9% of paragraphs that exceed the cap.

**Final chunk count:** 134 chunks across 10 documents (145 before runt-merge). Average size: ~333 characters; range: 107–500 characters (max exceeds 400 because the 50-char overlap is prepended after splitting).

---

## Sample Chunks

Six representative chunks pulled directly from the live ChromaDB collection, each labeled with its source document. (Chunks may begin with a short overlap fragment carried over from the previous chunk — e.g. `growing headcount, budget size...` — which is the 50-char overlap pass in action.)

**Chunk 1 — `amazon_leadership_principles_official.txt`** (company: Amazon)
> growing headcount, budget size, or fixed expense. Earn Trust
> Leaders listen attentively, speak candidly, and treat others respectfully. They are vocally self-critical, even when doing so is awkward or embarrassing. Leaders do not believe their or their team's body odor smells of perfume. They benchmark themselves and their teams against the best.

**Chunk 2 — `interviewingio_netflix_guide.txt`** (company: Netflix)
> effectively giving you multiple shots on goal. There's also no specific company-wide scale for performance at Netflix. This is different from, say, Google, where all candidates are graded on the same "Strong Hire, Hire, Neutral, No Hire, Strong No-Hire" scale. Different teams have different processes, but most decisions are made based on live post-onsite discussions.

**Chunk 3 — `substack_behavioral_interview_myths.txt`** (company: General)
> Myth 1: No Prep Required, Just Be Yourself Behavioral interviews demand preparation despite their personal nature. While authenticity matters, candidates must understand what interviewers seek and craft stories that effectively communicate relevant competencies. Even impressive work can fail without proper articulation.

**Chunk 4 — `blind_meta_e4_onsite.txt`** (company: Meta)
> today and feel like I bombed the last round. Round 1: Coding - answered both questions optimally and answered follow-ups which were tricky.
> Round 2: Behavioral - had a good rapport with the interviewer and felt like it went well.
> Round 3: Product architecture - got through all the requirements, designed the system with diagrams, went deep into API design, answered follow-ups.

**Chunk 5 — `glassdoor_google_swe_interview.txt`** (company: Google)
> with at least three questions to show interest. Question: Given a list of ranges like [0,1], [2,5], ... create a class with methods to find if an element is in any range and to insert a new range.
>
> Candidate 2 - No offer, Positive experience, Difficult interview
> Interviewed at Google, New York, NY.

**Chunk 6 — `devto_faang_interview_prep.txt`** (company: General)
> teamwork, and real-world problem-solving. Structure with the STAR Method - STAR (Situation, Task, Action, Result) isn't optional. It helps you present experiences clearly and logically. Interviewers don't want rambling stories - they want to see how you handled challenges, made decisions, and measured success.

---

## Embedding Model

**Model used:** `sentence-transformers/all-MiniLM-L6-v2` via the `sentence-transformers` library. It runs locally with no API key, no rate limits, and no cost — the right default for a project where inference needs to happen freely during development. It's 80MB, embeds at hundreds of sentences per second on CPU, and produces 384-dimensional vectors. Its English-language semantic search quality is well-validated on benchmarks, and it handles the informal interview-discussion language in this corpus (casual Blind posts, Reddit threads, structured guides) without the vocabulary gap problems a model trained only on formal text would have.

**Production tradeoff reflection:** If cost weren't a constraint, I'd weigh several tradeoffs. `all-mpnet-base-v2` is the next step up on the MTEB leaderboard — same architecture family, higher accuracy on semantic similarity, ~4× larger. More meaningful would be a hybrid retrieval approach: BM25 keyword search combined with dense vector search (reciprocal rank fusion). Keyword search catches exact phrase matches that are important in this domain — a candidate searching for "Customer Obsession" wants chunks that contain that exact phrase, not semantically adjacent chunks about "customer service." For multilingual support, a model like `paraphrase-multilingual-mpnet-base-v2` would handle Spanish or Mandarin community posts; this corpus is English-only so that wasn't a factor. API-hosted embeddings (e.g., OpenAI `text-embedding-3-small`) would reduce local compute overhead for a deployed product but would add per-query cost and an external dependency.

---

## Retrieval Test Results

Three queries run through the retrieval layer only (no generation), showing the top returned chunks with their cosine distances (lower = closer). Reproduce with `python _test_retrieval.py`. ChromaDB returns distance, not similarity; a distance ≥ 0.50 is flagged as a weak match.

### Query 1 — "What specific values and behaviors does Netflix prioritize in behavioral interviews?" (company filter: Netflix)

| Rank | Distance | Source | Chunk (top 3 shown) |
|------|----------|--------|---------------------|
| 1 | 0.253 | interviewingio_netflix_guide.txt | "...individuals capable of driving products forward. A unique part of Netflix's behavioral interview is the 'Dream Team' interview... The 'volume' is turned up on all of the things you might see in a typical behavioral round at Netflix (scale, accountability, open communication about concerns, high risk and high reward.)" |
| 2 | 0.280 | interviewingio_netflix_guide.txt | "...Anecdote from a Netflix Interviewer: 'Netflix doesn't hire as much as other FAANGs, so they want to make sure you're a star...' One key thing you need to do before your Netflix behavioral interview is read their culture memo. If you don't do this, you will fail the behavioral round." |
| 3 | 0.291 | interviewingio_netflix_guide.txt | "...Behavioral Answers to behavioral questions are almost as important as system design at Netflix. You'll get rejected if you fail the behavioral screen. These interviews have a heavy emphasis on the candidate being a cultural fit, being able to work in a team, having curiosity, and being product minded, highly motivated individuals capable of driving products forward." |

**Why these chunks are relevant:** All three are on-topic matches (distances 0.25–0.29, the lowest in the eval set). They name the behaviors the query asks about (cultural fit, teamwork, curiosity, product-mindedness, accountability) and come from the dedicated Netflix guide, surfacing the "culture memo" and "Dream Team" specifics of Netflix's behavioral round.

### Query 2 — "What are the key structural elements present in strong technical decision stories?" (no filter)

| Rank | Distance | Source | Chunk (top 3 shown) |
|------|----------|--------|---------------------|
| 1 | 0.356 | substack_behavioral_interview_myths.txt | "...strong stories adaptable to different questions. One well-chosen narrative about a complex project can demonstrate evidence across multiple competencies including ownership, technical depth, collaboration, and handling ambiguity." |
| 2 | 0.487 | substack_behavioral_interview_myths.txt | "...Select: Choose 4-5 well-developed stories... Deliver: Craft compelling narratives that establish context efficiently, explain actions clearly, quantify meaningful results, and demonstrate genuine learning." |
| 3 | 0.495 | substack_behavioral_interview_myths.txt | "...from mistakes, and collaboration capability. Interview stories may involve smaller experiences - class projects, internships, hackathons - but required evidence signals remain identical, demanding intentional story selection." |

**Why these chunks are relevant:** The top chunk (0.356) is a genuine match — it enumerates the competencies a strong story should demonstrate (ownership, technical depth, collaboration, ambiguity), and chunks 2–3 supply the Decode-Select-Deliver framing (establish context, explain actions, quantify results, demonstrate learning). These map to "structural elements." Note the distance climb after rank 1 (0.356 → 0.487 → 0.495): the corpus has general story-structure advice but no document specifically about technical-decision story structure, so retrieval returns the closest general-storytelling content rather than company-specific material. The generated answer (Q3 in Example Responses) reflects this, stating the structural elements aren't explicitly enumerated.

### Query 3 — "What specific behavioral patterns and attitudes appear in documented rejection reasons?" (no filter)

| Rank | Distance | Source | Chunk (top 3 shown) |
|------|----------|--------|---------------------|
| 1 | 0.586 | substack_behavioral_interview_myths.txt | "Why You Fail at Behavioral Interviews (The Behavioral, Substack) Myth 1: No Prep Required, Just Be Yourself" |
| 2 | 0.599 | blind_meta_e4_onsite.txt | "...the follow-ups too - they generally ask for them. Response on interview difficulty: If you didn't get to code a question at all, then it is highly likely a reject, especially in the current market." |
| 3 | 0.607 | blind_apple_interview.txt | "...everything clearly but still got rejected. Apple onsite rejection - what could have gone wrong?... I genuinely felt like I nailed the onsite. Coding and system design felt straightforward, interviewers seemed engaged. Got rejected." |

**Why these chunks are (weakly) relevant:** Every chunk is flagged weak (all distances ≥ 0.586). The corpus contains no document that enumerates rejection reasons as a unified topic, so retrieval scatters across loosely related fragments: a Substack header, a Meta difficulty note, an Apple "what went wrong" anecdote. The distances signal low confidence even though the surface keyword ("rejection") matches. See the Failure Case Analysis for the root-cause breakdown.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt given to Groq's `llama-3.3-70b-versatile` enforces grounding through four explicit, numbered rules:

```text
You are an interview preparation assistant. Answer questions using ONLY the
information in the retrieved document excerpts provided by the user.

Rules you must follow without exception:
1. Answer exclusively from the retrieved documents. Do not draw on your training knowledge.
2. If the documents do not contain enough information to answer the question, respond with
   exactly: "I don't have enough information in my documents to answer that."
3. Always cite the source document(s) your answer draws from, using the filename shown in
   each excerpt header (e.g., "According to interviewingio_netflix_guide.txt, ...").
4. Be specific — quote or closely paraphrase the documents rather than paraphrasing vaguely.
```

The phrase "without exception" and the exact refusal wording in Rule 2 are deliberate: vague instructions like "try to use the documents" leave room for the model to blend training knowledge when retrieval is weak. Numbered rules reduce that ambiguity.

**How source attribution is surfaced in the response:** Each retrieved chunk is injected into the user message with a `[Source: filename]` header above the chunk text. Rule 3 instructs the model to cite filenames by name — meaning attribution is structurally enforced by the context format, not left for the model to generate on its own. The Gradio UI then displays the deduplicated list of source filenames in a separate "Retrieved from" panel next to the answer.

---

## Example Responses

Real, unedited outputs from the full pipeline (`python query.py "<question>"`). Source attribution is visible inline in the answer text (Rule 3) and again in the **Sources** line.

### Example 1 — in-scope, strong retrieval

**Query:** "What specific values and behaviors does Netflix prioritize in behavioral interviews?"

**Response:**
> According to interviewingio_netflix_guide.txt, Netflix prioritizes the following values and behaviors in behavioral interviews: being a cultural fit, ability to work in a team, curiosity, being product-minded, and being highly motivated individuals capable of driving products forward. Additionally, they emphasize the importance of open communication about concerns, accountability, and high risk and high reward, as well as having metrics and impact statements.
>
> These values are highlighted in multiple excerpts from interviewingio_netflix_guide.txt, which also mentions that the company looks for individuals who can drive products forward and are a "star", as stated by a Netflix Interviewer.

**Sources:** interviewingio_netflix_guide.txt

### Example 2 — in-scope, honest partial answer

**Query:** "What are the key structural elements present in strong technical decision stories according to the documents?"

**Response:**
> According to substack_behavioral_interview_myths.txt, strong stories, such as those about complex projects, can demonstrate evidence across multiple competencies. However, the documents do not explicitly outline the key structural elements for strong technical decision stories.
>
> For crafting compelling narratives in general, substack_behavioral_interview_myths.txt suggests that they should "establish context efficiently, explain actions clearly, quantify meaningful results, and demonstrate genuine learning."
>
> There is no specific information about the structural elements of technical decision stories in the provided documents, including amazon_leadership_principles_official.txt, which focuses on leadership principles rather than story structure.

**Sources:** substack_behavioral_interview_myths.txt, amazon_leadership_principles_official.txt

Here the model answers from what is present, cites both filenames inline, and flags that the specific information requested is not in the corpus rather than inventing it.

### Example 3 — out-of-scope query (refusal)

**Query:** "What specific behaviors or qualities are red flags that Apple interviews look for negatively?"

**Response:**
> I don't have enough information in my documents to answer that.

**Sources:** blind_apple_interview.txt

The Apple source is a community discussion thread of anecdotes, not a red-flag taxonomy. The closest chunk sits at distance 0.483 with the rest ≥ 0.546, so the model correctly returns the exact refusal string from Rule 2 instead of fabricating a list. (See Failure Case Analysis → Secondary failure for the full breakdown.)

---

## Evaluation Report

All 5 questions were run through the full pipeline: retrieval from persistent ChromaDB (top-k=5, all-MiniLM-L6-v2, cosine distance), then generation via Groq llama-3.3-70b-versatile with the grounding system prompt. Company metadata filters were applied for company-specific questions.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What specific values and behaviors does Netflix prioritize in behavioral interviews? | Autonomy, high accountability, impact over effort, decision-making without waiting for approval, metrics-driven | Cultural fit, teamwork, curiosity, product-mindedness, highly motivated, metrics and impact statements — cited interviewingio_netflix_guide.txt | Relevant (all 5 chunks Netflix, dist 0.25–0.35) | Accurate |
| 2 | What specific behaviors or qualities are red flags that Apple interviews look for negatively? | Lack of attention to detail, UX blindness, craftsmanship deficit, insufficient privacy/security consideration | "I don't have enough information in my documents to answer that." | Partially relevant (best dist 0.48, generic Apple recruiting anecdotes, no red-flag taxonomy) | Accurate (correct refusal; expected content absent from corpus) |
| 3 | What are the key structural elements present in strong technical decision stories according to the documents? | Ownership from conception to ship, cross-functional collaboration, explicit trade-off discussion, impact/outcome focus | Establishing context efficiently, explaining actions clearly, quantifying results, demonstrating genuine learning — cited substack_behavioral_interview_myths.txt | Partially relevant (top chunk dist 0.38; others 0.51–0.56) | Partially accurate |
| 4 | What specific behavioral patterns and attitudes appear in documented rejection reasons? | Blaming circumstances, defensiveness, lack of initiative, poor clarification, not demonstrating company values | Lists expected positive behaviors (cultural fit, teamwork, curiosity) and infers rejection by inversion — does not refuse despite all distances ≥ 0.59 | Off-target (all 5 chunks dist 0.59–0.63, no rejection-reason document exists) | Inaccurate |
| 5 | What are the documented differences in how Apple and Netflix each evaluate system design thinking? | Apple: scalability, UX, privacy, craftsmanship; Netflix: speed, iteration cycles, measurable business impact | "I don't have enough information in my documents to answer that." | Off-target (all 5 chunks Netflix, zero Apple system-design content) | Accurate (correct refusal; Apple system-design content absent from corpus) |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

### Primary failure — Q4: Documented rejection reasons

**Question that failed:** "What specific behavioral patterns and attitudes appear in documented rejection reasons?"

**What the system returned:** Instead of refusing, the model listed expected *positive* behaviors (cultural fit, teamwork, curiosity) retrieved from the Netflix interview guide and inferred what would cause rejection if those behaviors were absent. The answer is not grounded in documented rejection reasons — it's an inversion of interview success criteria. The system should have returned the "I don't have enough information" refusal.

**Root cause (tied to a specific pipeline stage):** Two pipeline stages failed together.

*Stage 3 — Retrieval:* All five retrieved chunks had cosine distances between 0.59 and 0.63 — well above the 0.50 threshold that the eval harness flagged as weak matches. No document in the corpus contains a dedicated rejection-reason analysis. The chunker correctly ingested the Substack source (which discusses why candidates fail behavioral interviews in general terms), but that document describes common misconceptions, not documented company-specific rejection patterns. There was no chunk with strong semantic overlap with the query.

*Stage 5 — Generation:* The grounding prompt instructs the model to refuse if the documents don't contain enough information, but it doesn't specify a distance threshold or a "minimum signal" criterion. When the model received five loosely related chunks — about Netflix culture, Meta follow-up questions, Apple rejection anecdotes, and general behavioral advice — it found enough surface-level relevance to construct an answer by reasoning across the chunks rather than citing them directly. The prompt's Rule 2 ("if the documents do not contain enough information") is ambiguous when the documents contain *related but not sufficient* information; the model treated "related" as "enough."

**What was changed to fix it:** A retrieval-confidence gate is now implemented in `query.py`: when the minimum distance across the top-k chunks exceeds `WEAK_DISTANCE_THRESHOLD` (defined in `config.py`, currently 0.55), `ask()` prepends a note to the user prompt before the chunks — "Note: retrieval confidence is low for this query — the documents may not contain the specific information requested." — which gives the model an explicit signal to prefer the Rule 2 refusal. A complementary fix still open is to add documents that actually contain rejection analysis — post-interview feedback threads or structured rejection debriefs from Blind or Glassdoor.

---

### Secondary failure — Q2: Apple red flags

**Question that failed:** "What specific behaviors or qualities are red flags that Apple interviews look for negatively?"

**What the system returned:** The system correctly returned the "I don't have enough information" refusal. This is the right system behavior — but the failure is at the document collection stage, not the generation stage.

**Root cause (tied to a specific pipeline stage):** *Stage 1 — Document ingestion.* The Apple source (`blind_apple_interview.txt`) is a community discussion thread — candidates asking each other about their experiences, not structured red-flag analysis. The posts are anecdotal ("I explained everything clearly but still got rejected") rather than taxonomic. When the retrieval embeds the query "red flags Apple looks for negatively," the closest Apple chunks (dist 0.48) are generic rejection anecdotes and recruiting observations, not a taxonomy of failure modes. The corpus gap means retrieval can't return on-topic chunks regardless of how chunking or embedding is tuned — it's a source-quality problem, not a parameter problem. This was anticipated in planning.md's "Anticipated Challenge #4" and confirmed in the eval harness findings.

**What you would change to fix it:** Replace the Blind Apple thread with a source that contains structured Apple interview analysis — a detailed blog post, interviewing.io's Apple guide (if available), or a curated collection of Apple-specific Glassdoor interview reviews that describe rejection feedback explicitly.

---

## Spec Reflection

**One way the spec helped during implementation:**

The Chunking Strategy section of planning.md was unusually specific — it pre-measured the corpus to determine that a 300-char cap splits 22% of paragraphs vs. 9% at 400, showed why 400 fits the principle+example structure of these documents, and described the runt-merge pass with a concrete minimum-length threshold (80 chars). Having those measurements in writing before writing any code meant the chunking implementation could be generated and verified in one pass: the implementation was correct the first time because the spec described not just *what* to do but *why* each parameter was chosen. Without that pre-validation, the typical workflow would be: implement, run, see short header chunks winning top-k slots, diagnose, add runt merge, re-run — which the spec short-circuited entirely.

**One way the implementation diverged from the spec, and why:**

The spec's initial `config.py` set `N_RESULTS = 3`, while planning.md's Retrieval Approach section argued for top-k=5 as the right balance between context richness and signal dilution. The divergence was a copy-paste error in the config file that contradicted the planning document. More interestingly, the spec anticipated that the company metadata filter would be a key retrieval improvement ("metadata filtering by company" listed as a mitigation for company bleed) — but the eval harness measured that the filter changed exactly 1 chunk across all 5 evaluation questions. For queries that already name the company, the embedding model ranks the right company's chunks at the top without any filter. The filter was kept as a guard for future ambiguous queries, but the spec's framing of it as a primary mitigation turned out to be overstated. The real retrieval improvement came from runt-merge, not metadata filtering.

---

## AI Usage

**Instance 1 — Chunking implementation and overlap fix**

- *What I gave the AI:* The full Chunking Strategy section from planning.md, including the pseudocode for `recursive_chunk()` and `add_overlap()`, and the measured corpus stats (134 chunks, 9% paragraph split rate at 400 chars).
- *What it produced:* A working `recursive_chunk()` implementation that matched the pseudocode exactly, plus an `add_overlap()` function that prepended the last 50 characters of the previous chunk without any word-boundary handling.
- *What I changed or overrode:* The overlap implementation produced chunks that started mid-word — e.g., the tail `"il she asked"` from `"until she asked"`. I directed the AI to add a word-boundary snap: find the first space in the tail and drop everything before it, so the prepended context always starts on a complete word. This produced the `tail.find(" ")` guard in `add_overlap()`. I also added the `merge_runts()` pass after observing in the eval harness that bare header lines were winning top-k slots on loosely related queries.

**Instance 2 — Persistent retrieval and grounding system prompt**

- *What I gave the AI:* The architecture diagram and Retrieval Approach section from planning.md, the eval harness output showing which queries returned weak matches (Q4 all ≥0.59), and the requirement that the system must refuse out-of-scope questions rather than hallucinate.
- *What it produced:* Working `ingest.py`, `retrieve.py`, and `query.py` files with a ChromaDB PersistentClient setup, module-level collection caching, and an initial system prompt that said "try to use only the provided documents."
- *What I changed or overrode:* I replaced "try to use only" with four numbered rules including an explicit refusal template ("I don't have enough information in my documents to answer that.") and the phrase "without exception" — because the weaker wording left the model room to blend training knowledge when retrieval was thin, as Q4's tangential answer later confirmed. I also changed `N_RESULTS` from the config's default of 3 to 5 to match the planning.md specification.

---

## Query Interface

The interface is a Gradio web app ([app.py](app.py)) served at `http://localhost:7860`.

**Input fields:**

| Field | Type | Purpose |
|-------|------|---------|
| **Filter by company** | Radio buttons — `All`, `Amazon`, `Google`, `Meta`, `Apple`, `Netflix` | Optional metadata filter. `All` (default) searches every document; selecting a company restricts retrieval to that company's chunks via ChromaDB's `$in` `where` clause. |
| **Your question** | Multi-line textbox (3–6 lines) | The natural-language question. Submitted by clicking **Ask** or pressing Enter. Empty input returns a "Please enter a question." prompt without calling the model. |
| **Examples** | Clickable preset chips | Five one-click sample questions that populate the textbox. |

**Output fields:**

| Field | Type | Content |
|-------|------|---------|
| **Answer panel** | Rendered Markdown | The grounded LLM response, with source filenames cited inline (e.g. "According to interviewingio_netflix_guide.txt, ..."). |
| **Retrieved from** | Source chips | The deduplicated list of source documents the answer drew from, each with a company icon (🎬 Netflix, 🍎 Apple, 🛒 Amazon, 🔍 Google, 👥 Meta). |

**Sample interaction transcript:**

```text
[Filter by company]  ( ) All  ( ) Amazon  ( ) Google  ( ) Meta  ( ) Apple  (•) Netflix

[Your question]
> What specific values and behaviors does Netflix prioritize in behavioral interviews?

[ Ask ]
─────────────────────────────────────────────────────────────────────────────

Answer:
According to interviewingio_netflix_guide.txt, Netflix prioritizes the following
values and behaviors in behavioral interviews: being a cultural fit, ability to
work in a team, curiosity, being product-minded, and being highly motivated
individuals capable of driving products forward. Additionally, they emphasize the
importance of open communication about concerns, accountability, and high risk and
high reward, as well as having metrics and impact statements.

These values are highlighted in multiple excerpts from interviewingio_netflix_guide.txt,
which also mentions that the company looks for individuals who can drive products
forward and are a "star", as stated by a Netflix Interviewer.

RETRIEVED FROM
🎬 interviewingio_netflix_guide.txt
```

---

## Demo

Run the app with:

```bash
python app.py
```

Open [http://localhost:7860](http://localhost:7860) in your browser. Type any question about FAANG interview culture, behavioral expectations, or company-specific values. The answer panel shows the grounded response with source citations; the "Retrieved from" panel lists the documents the answer drew from.

To rebuild the vector store (e.g., after adding new documents):

```bash
python ingest.py
```

To inspect retrieval quality (which chunks each query returns, with distances):

```bash
python _test_retrieval.py
```
