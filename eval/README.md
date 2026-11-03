# Evaluation set: `eval/cases.yaml`

56 labelled cases for the EU AI Act Checker. Labels follow **Regulation (EU) 2024/1689 as
consolidated on 2026-07-27**, including Regulation (EU) 2026/1744 (Digital Omnibus on AI). The
evaluation date is 2026-11-03. Schema: `docs/CONTRACTS.md` §9. Fact paths: `backend/app/engine/facts.py`.

```bash
backend/.venv/bin/python eval/validate_cases.py          # schema + FactSheet + citations
```

## How the set was built

1. **Read the law first.** Art. 2, 3, 5 (including the Omnibus points (ba)/(bb) and paragraphs 1a/1b),
   6 (including the new 6(1a)–(1c) and 6(3)), 26, 27, 50, 51–55, 113, Annex I and Annex III were read
   in `data/raw/ai-act-consolidated-20260727-EN.xhtml` before any case was labelled. Every
   `expected_citations` ID was then checked against `data/corpus/en.json` through `CorpusStore`.
2. **Annex III coverage.** There is one case for each point or letter in Annex III, 25 in all:
   1(a)–(c), 2, 3(a)–(d), 4(a)–(b), 5(a)–(d), 6(a)–(e), 7(a)–(d) and 8(a)–(b). Each is written the
   way a real user would describe the system, and the cases mix providers, deployers and "both".
3. **Edge cases.** These test the boundaries that the Act or the Commission guidance draw
   explicitly. Examples: the emotion-recognition exception for medical or safety reasons, whether it
   is obvious that a user is talking to an AI, categorisation by non-biometric or non-sensitive
   features, the GPAI model provider versus the downstream integrator, the Art. 6(3) filter versus
   profiling, the financial-fraud exception, real-time versus post-remote identification, and
   predictive policing based solely on profiling versus on objective facts.
4. **Guidance.** The Commission guidance corpus (`data/guidance/*.json`) arrived while the set was
   being written, and labels that depend on it were checked against it. Cases whose label rests
   mainly on a guidance example have `source: commission_guidelines`, and their `notes` name the
   guideline, section and `guid:` ID:
   - prohibited practices C(2025) 884
   - AI-system definition C(2025) 924
   - GPAI C(2025) 5045
   - Art. 50 transparency C(2026) 5054
   - **draft** Art. 6 high-risk classification, 19 May 2026
   Guidance IDs appear only in notes. `expected_citations` contain only binding provisions.
5. **should_ask cases.** Seven cases leave out a decisive fact on purpose. `facts` holds the
   ground-truth answer, so the runner can answer the question automatically.

## Label policy

- **Tier precedence** follows CONTRACTS §5: `out_of_scope` (Art. 2 exclusion, outside Art. 2(1),
  or not an AI system under Art. 3(1)) > `prohibited` > `high_risk` > `limited_risk` (Art. 50 only)
  > `minimal_risk`.
- **Overlays.**
  - `transparency_art50` is added whenever an Art. 50 duty attaches to the system: 50(1)
    interaction, 50(2) marking, 50(3) emotion recognition or biometric categorisation, or 50(4) deep
    fakes and public-interest text. Overlays are additive (CONTRACTS §5), so high-risk and
    prohibited cases carry it too.
  - `gpai` is only for a provider of a GPAI model (`gpai.is_gpai_model` and
    `gpai.provider_of_model`). It is never set for downstream integrators.
- **Bare GPAI model → `minimal_risk` + `gpai`.** A model is not classified into a tier, so the
  tier reflects the absence of any AI-system use case. This is a policy choice; see the
  ambiguities below.
- **Conservative reading.** Where the text is ambiguous, the stricter label is chosen,
  `difficulty: hard` is set, and the reason is recorded in `notes`. An exception is applied only
  when the facts clearly meet its wording. Examples are the Art. 5(1)(f) medical/safety exception,
  the Art. 6(3) filter, the Annex III 5(b) fraud exception and the Art. 50(1) "obvious"
  exception.
- **"Materially influences"** (Art. 6(3) first subparagraph) is used when the output is the basis
  a human normally relies on, such as a score, ranking, priority code or auto-reject, even if the
  human formally signs off. A theoretical override does not change this. `supports_human_decision`
  is used only when a human genuinely assesses the case independently. Profiling of natural persons
  always defeats Art. 6(3), as its last subparagraph says.
- **Role.**
  - `provider` is whoever develops the system, or has it developed, and places it on the market
    or puts it into service under its own name.
  - `deployer` is whoever uses it under its own authority.
  - `both` covers in-house systems used by the same organisation.
  - Configuring a vendor tool does not make a deployer a provider (Art. 25).
- **Expected citations** are the 2–5 IDs that a correct answer must cite. Sometimes these are the
  provisions that are ruled out, such as `art:50.1` for a bot that is obviously AI. They are not
  the full list of relevant provisions.
- **`facts`** use flat dotted FactSheet paths. Every decisive field is set, and negatives are set
  explicitly as `false` or `none`, so the deterministic engine asks no residual questions. This
  includes the exception fields the engine added: `annex_i_third_party_assessment`,
  `public_body_or_public_service`, `financial_fraud_detection`, `biometric.medical_or_safety_purpose`,
  `law_enforcement.rbi_strictly_necessary_objective`,
  `law_enforcement.authorised_by_law_for_criminal_offences`, and the others in `facts.py`.
  `free_text_notes` keeps the human-readable reason alongside.
- **Public bodies.** Cases where the deployer is a public authority set
  `public_body_or_public_service: true`. Where the role is deployer, `art:27` (FRIA) is in
  `expected_citations`.

## Composition

By source and tier:

| source                | prohibited | high_risk | limited_risk | minimal_risk | out_of_scope | total |
|-----------------------|-----------:|----------:|-------------:|-------------:|-------------:|------:|
| annex_iii             | 0 | 25 | 0 | 0 | 0 | 25 |
| art5                  | 4 | 0 | 0 | 0 | 0 | 4 |
| art50                 | 0 | 0 | 2 | 0 | 0 | 2 |
| commission_guidelines | 1 | 1 | 1 | 4 | 1 | 8 |
| edge                  | 1 | 7 | 1 | 2 | 4 | 15 |
| gpai                  | 0 | 0 | 0 | 2 | 0 | 2 |
| **total**             | **6** | **33** | **4** | **8** | **5** | **56** |

| role     | n  |   | language | n  |   | difficulty | n  |
|----------|---:|---|----------|---:|---|------------|---:|
| provider | 26 |   | en       | 49 |   | easy       | 18 |
| deployer | 25 |   | it       | 7  |   | medium     | 28 |
| both     | 5  |   |          |    |   | hard       | 10 |

- Overlays: none in 39 cases, `transparency_art50` in 15, `gpai` in 2.
- `should_ask: true` (7):
  - `edge-fraud-detection-loan-applications`
  - `edge-meeting-emotion-plugin-context-unknown`
  - `edge-performance-promotion-role-unknown`
  - `edge-admissions-completeness-check`
  - `edge-us-credit-api-scope-unknown`
  - `edge-careers-chatbot-screening-unknown`
  - `edge-university-research-depression-voice`

High-risk cases make up about 59% of the set because every Annex III letter has a case. When
reporting results, give per-tier metrics alongside the overall accuracy.

## Known ambiguities

1. **"Race" in Art. 5(1)(g) versus "ethnic origin".** The draft Art. 6 guidelines (§IV.3.1.3
   para 169) treat ethnic origin as an Annex III 1(b) high-risk attribute rather than a prohibited
   one. `edge-categorisation-race-ethnicity` therefore uses explicit racial categories. A
   description that says only "ethnicity" is a genuinely open case.
2. **Age and gender categorisation.** `edge-retail-gender-age-categorisation` is labelled
   `limited_risk` (50(3) only), following the *draft* Art. 6 guidelines, which tie "sensitive or
   protected" to GDPR Art. 9(1). If the final guidelines change, the label becomes `high_risk`.
3. **Emotion recognition for safety.** `edge-emotion-safety-control-room` relies on the
   dangerous-chemicals example in the guidance (§7.2.3 para 263). The exception is narrow; general
   stress monitoring would be prohibited.
4. **Art. 50(3) law-enforcement carve-out.** It is applied to the police polygraph
   (`annex3-6b`, no overlay) but not to the border kiosk (`annex3-7a`, overlay). Border control is
   not primarily criminal investigation.
5. **Art. 50(2) for internal drafting text.** The judicial drafting assistant (`annex3-8a`)
   expects the 50(2) overlay, because it generates new text.
6. **Tier for a bare GPAI model** (`gpai-*`) is `minimal_risk` + `gpai`. The facts say the model
   generates text, and the current engine then applies Art. 50(2) and returns `limited_risk`. The
   labels keep `minimal_risk`: Art. 50(2) addresses providers of AI *systems* ("including
   general-purpose AI systems"), and a model offered only via API is not a system (Art. 3(63) vs
   3(66), recital 97). These are the only engine mismatches.
7. **Machinery after the Omnibus.** Regulation (EU) 2023/1230 now sits in Annex I **Section B**
   (point 21), and the old Section A point 1 has been deleted. Under the amended Art. 2(2), only
   Art. 6(1), Art. 60a and Arts 102–112 apply to such products. `edge-cobot-safety-machinery` is
   still labelled `high_risk` (classified under 6(1)).
8. **Fraud exception (Annex III 5(b)).** Recital 58 speaks of fraud detection "provided for by
   Union law", but the Annex wording has no such qualifier. The operative text and the draft
   guidelines (paras 306–308) are followed.
9. **New Art. 5 points.** The new points (ba)/(bb) apply from **2 December 2026** (Art. 113(a)),
   which is after the evaluation date. `edge-nudify-app` is still labelled `prohibited`, and the
   answer should mention the date.
10. **Art. 3 definitions.** Citations to definitions use the corpus format `art:3.<n>` (for
    example `art:3.39`), which resolves as "Art. 3, point (39)".
11. **FactSheet gaps.** The fields that were missing are now in the FactSheet and set in every
    case. One gap remains: `infers_sensitive_attributes` mirrors the Art. 5(1)(g) list, so health
    and ethnic origin (the Annex III 1(b) attributes that are not prohibited) are expressed only
    through `annex_iii_area` and `free_text_notes`.
