# Interface contracts

Every module is built against these contracts so parallel work composes.
Changes must be additive; if you need a breaking change, stop and report it.

## 1. Provision IDs (shared by corpus, engine, retrieval, UI, eval)

Machine ID format (string, ASCII, no spaces):

| Kind | ID | Display label (EN / IT) |
|------|----|-------------------------|
| Article | `art:6` | Art. 6 / Art. 6 |
| Paragraph | `art:6.2` | Art. 6(2) / Art. 6, par. 2 |
| Point | `art:6.3.a` | Art. 6(3)(a) / Art. 6, par. 3, lett. a) |
| Sub-point | `art:5.1.h.i` | Art. 5(1)(h)(i) |
| Omnibus-inserted paragraph | `art:5.1a` | Art. 5(1a) |
| Omnibus-inserted point | `art:5.1.ba` | Art. 5(1)(ba) |
| Annex | `annex:III` | Annex III / Allegato III |
| Annex point | `annex:III.4` | Annex III, point 4 |
| Annex sub-point | `annex:III.4.a` | Annex III, point 4(a) |
| Annex section (Annex I) | `annex:I.A.11` | Annex I, Section A, point 11 |
| Recital | `rec:57` | Recital 57 / Considerando 57 |
| Guidance (non-binding) | `guid:prohibited-2025.3.2` | Commission Guidelines on prohibited practices (2025), §3.2 |

Rules: paragraph numbers as in the text (`1`, `2`, `1a`); points as lower-case
letters (`a`, `ba`); roman sub-points lower-case (`i`, `ii`). Annex numbers as
roman upper-case (`I`…`XIII`). Unnumbered single-paragraph articles use the
article ID itself (`art:4`).

## 2. Corpus JSON (`data/corpus/en.json`, `data/corpus/it.json`)

```jsonc
{
  "meta": {
    "celex": "02024R1689-20260727",
    "language": "en",                       // "en" | "it"
    "consolidated_as_of": "2026-07-27",
    "retrieved_at": "2026-11-03",
    "source_url": "http://publications.europa.eu/resource/celex/02024R1689-20260727",
    "eurlex_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27",
    "amending_acts": [
      {"celex": "32026R1744", "marker": "M1", "short_title": "Regulation (EU) 2026/1744 (Digital Omnibus on AI)", "oj_date": "2026-07-24", "in_force": "2026-07-27"}
    ],
    "counts": {"articles": 113, "annexes": 13, "recitals": 180, "provisions": 0}
  },
  "provisions": [
    {
      "id": "art:6.2",
      "type": "paragraph",                  // article | paragraph | point | annex | annex_point | recital
      "label": "Art. 6(2)",
      "parent_id": "art:6",
      "children": ["..."],                  // ordered child IDs, [] if leaf
      "article": 6, "paragraph": "2", "point": null, "annex": null, "recital": null,
      "chapter": "III", "chapter_title": "High-risk AI systems",
      "section": "1", "section_title": "Classification of AI systems as high-risk",
      "title": "Classification rules for high-risk AI systems",   // article title, repeated on descendants
      "text": "In addition to the high-risk AI systems referred to in paragraph 1, AI systems referred to in Annex III shall be considered to be high-risk.",
      "amendment": null,                    // or {"marker":"M1","kind":"replaced"|"inserted"|"deleted","by":"32026R1744"}
      "order": 412                          // global document order
    }
  ]
}
```

`text` is the node's own text (for an article node: its title; for a
paragraph with points: the introductory words; for a point: the point text).
`full_text(id)` in `app/corpus/store.py` assembles a node with its descendants
for display. Deleted provisions are kept with `amendment.kind == "deleted"` and
`text` = "" plus the original text in `original_text` when recoverable.

Guidance corpus (`data/guidance/*.json`): same shape, `type: "guidance"`,
IDs `guid:<slug>.<section>`, `meta.binding: false`, `meta.source_url`.

## 3. Corpus store API (`backend/app/corpus/store.py`)

```python
class CorpusStore:
    def __init__(self, data_dir: Path): ...
    def get(self, id: str, lang: str = "en") -> Provision | None
    def full_text(self, id: str, lang: str = "en") -> str
    def label(self, id: str, lang: str = "en") -> str
    def exists(self, id: str) -> bool
    def eurlex_url(self, id: str, lang: str = "en") -> str   # deep link to EUR-Lex/ELI
    def iter(self, lang: str = "en", types: set[str] | None = None) -> Iterator[Provision]
    def meta(self, lang: str = "en") -> CorpusMeta
```

## 4. FactSheet (`backend/app/engine/facts.py`) — see the file; it is the contract

`None` always means "unknown". Pydantic v2 models. Field paths used in
questions/answers are dotted (`biometric.emotion_recognition`).

## 5. Engine API (`backend/app/engine/__init__.py`)

```python
Tier = Literal["prohibited", "high_risk", "limited_risk", "minimal_risk", "out_of_scope"]
Confidence = Literal["high", "medium", "low"]

class Finding(BaseModel):
    rule_id: str                 # e.g. "art5.1.f-emotion-workplace"
    kind: Literal["prohibition", "high_risk_annex_iii", "high_risk_annex_i", "derogation_6_3", "transparency", "gpai", "scope", "not_ai_system", "note"]
    title: dict[str, str]        # {"en": ..., "it": ...}
    rationale: dict[str, str]    # short, factual, references the facts used
    citations: list[str]         # provision IDs; MUST resolve in corpus
    facts_used: list[str]        # fact paths
    decisive: bool               # True if this finding set the tier

class Classification(BaseModel):
    tier: Tier
    confidence: Confidence
    findings: list[Finding]
    overlays: dict[str, list[str]]   # {"transparency_art50": ["art:50.1"], "gpai": ["art:53"], ...}
    role: Literal["provider", "deployer", "both", "other", "unknown"]
    applies_from: list[Milestone]    # dates relevant to this result
    unresolved: list[str]            # fact paths still unknown that could matter
    assumptions: list[dict[str,str]] # {"en":..., "it":...} explicit assumptions made

class Question(BaseModel):
    id: str; fact_path: str
    text: dict[str, str]; why: dict[str, str]
    type: Literal["single", "boolean", "text"]
    options: list[dict]              # [{"value": ..., "label": {"en":..,"it":..}}]
    impact: float                    # 0..1 how much outcome uncertainty it removes

class Obligation(BaseModel):
    id: str; role: Literal["provider","deployer","both"]
    category: Literal["governance","documentation","data","transparency","oversight","registration","monitoring","literacy","other"]
    title: dict[str,str]; summary: dict[str,str]
    citations: list[str]; applies_from: str | None   # ISO date
    priority: Literal["must","should"]

class ChecklistItem(BaseModel):
    id: str; title: dict[str,str]; description: dict[str,str]
    citations: list[str]; obligation_ids: list[str]; template_hint: dict[str,str] | None

class Milestone(BaseModel):
    id: str; date: str; what: dict[str,str]; citations: list[str]; status: Literal["in_force","upcoming"]

def classify(facts: FactSheet) -> Classification
def next_questions(facts: FactSheet, max_questions: int = 3, asked: set[str] = frozenset()) -> list[Question]
def obligations_for(c: Classification, facts: FactSheet) -> list[Obligation]
def checklist_for(obligations: list[Obligation]) -> list[ChecklistItem]
def timeline(today: date | None = None) -> list[Milestone]
def all_citation_ids() -> set[str]    # for the test that every citation resolves
```

Tier precedence: `out_of_scope` (Art. 2 exclusions, or not an AI system) is
decided first; then `prohibited` > `high_risk` > `limited_risk` (Art. 50
obligations only) > `minimal_risk`. Overlays are additive (a high-risk emotion
recognition system also carries Art. 50(3)). GPAI-model obligations are an
overlay, not a tier.

## 6. LLM provider API (`backend/app/llm/`)

```python
class Message(TypedDict): role: Literal["system","user","assistant"]; content: str

@dataclass
class LLMResult:
    text: str; model: str; provider: str
    input_tokens: int | None; output_tokens: int | None
    cost_usd: float | None          # API-equivalent; None if unknown; 0.0 for local
    latency_ms: int; cached: bool

class LLMProvider(ABC):
    name: str; model: str
    async def complete(self, messages: list[Message], *, temperature: float = 0.0, max_tokens: int = 2048, json_mode: bool = False) -> LLMResult
    async def stream(self, messages: list[Message], *, temperature: float = 0.0, max_tokens: int = 2048) -> AsyncIterator[str | LLMResult]   # str deltas, then exactly one LLMResult

def get_provider(name: str | None = None, model: str | None = None) -> LLMProvider
# env: LLM_PROVIDER=claude_cli|nvidia|local_mlx|anthropic_api|openai_compat ; LLM_MODEL ; LLM_MAX_CONCURRENCY ; LLM_CACHE_PATH ; LLM_CACHE=1
# claude_cli: CLAUDE_CLI_PATH (default "claude"), model aliases sonnet|opus|haiku
# nvidia: NVIDIA_API_KEY, NVIDIA_BASE_URL (default https://integrate.api.nvidia.com/v1), LLM_MODEL (e.g. nvidia/llama-3.3-nemotron-super-49b-v1)
# local_mlx: MLX_MODEL (default mlx-community/Qwen2.5-14B-Instruct-4bit)
# anthropic_api: ANTHROPIC_API_KEY
# openai_compat: OPENAI_BASE_URL, OPENAI_API_KEY
```
Cache: SQLite at `LLM_CACHE_PATH` (default `data/cache/llm.sqlite`), key =
sha256(provider, model, json(messages), temperature, max_tokens, json_mode).
Streaming responses are cached after completion and replayed as a single delta.
Retries: 3 attempts, exponential backoff (1s, 3s, 9s) on transient errors;
`LLMError` otherwise. Concurrency: process-wide `asyncio.Semaphore(LLM_MAX_CONCURRENCY)`.
JSON helper: `parse_json_object(text) -> dict` strips code fences, finds the
outermost `{...}`, repairs trailing commas; raises `JSONParseError`.

## 7. HTTP API (`backend/app/api/`), base `http://localhost:8101`

- `GET /health` → `{"status":"ok","provider":"claude_cli","model":"sonnet","corpus_loaded":true}`
- `GET /api/meta` → `{law_as_of, checked_at, celex, amending_acts, provider, model, timeline: Milestone[], disclaimer: {en,it}, languages:["en","it"]}`
- `GET /api/examples?lang=en` → `{examples: [{id, title, description, tags, expected_tier}]}` (12 one-click examples)
- `GET /api/law/{id}?lang=en` → `{provision: Provision, full_text, breadcrumb: [{id,label}], children: Provision[], eurlex_url}`; 404 if unknown
- `GET /api/law/search?q=...&lang=en&k=8` → `{hits: [{id, label, snippet, score}]}`
- `POST /api/assess` body:
  ```jsonc
  {"description": "...", "language": "en", "session_id": "optional", "facts": null | FactSheet, "answers": [{"fact_path": "role", "value": "deployer"}], "round": 0, "provider": null, "model": null}
  ```
  Response `text/event-stream`, events (`event:` name, `data:` JSON):
  - `stage` `{"stage": "extracting"|"retrieving"|"classifying"|"drafting"|"finalising", "message": {"en":..,"it":..}}`
  - `facts` `{"facts": FactSheet}`
  - `questions` `{"questions": Question[], "facts": FactSheet, "round": 1, "session_id": "..."}` then `done {"status":"needs_clarification"}`
  - `token` `{"section": "reasoning", "text": "..."}`
  - `result` `{"assessment": Assessment}` then `done {"status":"complete"}`
  - `error` `{"message": {"en":..,"it":..}, "code": "llm_unavailable"|"invalid_input"|"internal"}`
- `POST /api/export/markdown` body `{assessment}` → `text/markdown` attachment
- `POST /api/export/pdf` body `{assessment}` → `application/pdf` attachment

Assessment:
```jsonc
{
  "id": "uuid", "created_at": "ISO", "language": "en",
  "law_as_of": "2026-07-27", "checked_at": "2026-11-03",
  "model": {"provider": "claude_cli", "model": "claude-sonnet-5-5"},
  "description": "...", "facts": FactSheet,
  "classification": Classification,
  "reasoning_md": "Markdown. Citations as [[art:6.2]] tokens; the UI renders them as chips.",
  "obligations": Obligation[], "checklist": ChecklistItem[],
  "related_provisions": [{"id":"rec:57","why":{"en":..,"it":..}}],   // from retrieval, for further reading
  "uncertainties": [{"en":..,"it":..}],
  "disclaimer": {"en":..,"it":..},
  "metrics": {"latency_ms": 0, "llm_calls": 2, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cached": false}
}
```
Citation token convention everywhere (reasoning, rationale, summaries):
`[[art:6.2]]`. The server validates tokens against the corpus and removes
invalid ones before sending; the UI never has to handle an unknown ID.

## 8. Frontend conventions (`frontend/`)
- `NEXT_PUBLIC_API_URL` (default `http://localhost:8101`).
- Routes: `/` landing (hero, how it works, examples gallery, describe form),
  `/assess` guided flow (steps: Describe → Clarify → Result), `/law/[id]`
  provision page (deep-linkable), `/about` (method, limits, law as of, disclaimer).
- i18n: dictionary `frontend/src/i18n/{en,it}.ts`; language in URL search
  param `?lang=it` and persisted in `localStorage`; `<html lang>` updated.
- Theme: `next-themes`, class strategy, light + dark, tokens in `globals.css`.
- Citations: `<Cite id="art:6.2" />` chip → opens `CitationPanel` (shadcn Sheet)
  that fetches `/api/law/{id}` and shows label, breadcrumb, text, EUR-Lex link,
  amendment badge if `amendment` is set. Hover shows a tooltip with the first
  200 chars.
- Tier palette (CSS variables): prohibited `--tier-prohibited`, high-risk
  `--tier-high`, limited `--tier-limited`, minimal `--tier-minimal`,
  out-of-scope `--tier-oos`.

## 9. Eval case schema (`eval/cases.yaml`)
```yaml
- id: annex3-4a-cv-screening
  title: CV screening tool for an HR department
  description: "Plain-language description as a user would type it"
  language: en
  source: annex_iii        # annex_iii | art5 | commission_guidelines | art50 | gpai | edge
  role: deployer
  expected_tier: high_risk
  expected_overlays: []    # e.g. [transparency_art50, gpai]
  expected_citations: [annex:III.4.a, art:6.2, art:26]
  should_ask: true         # description alone lacks a decisive fact
  facts:                   # ground truth; the runner answers questions from these paths
    role: deployer
    sector: employment
    decision_impact: materially_influences
  notes: "Why this label"
```
