# Legal logic of the rule engine

Audit guide for `backend/app/engine/`. Law: Regulation (EU) 2024/1689 as consolidated on 27 July 2026
(incl. Regulation (EU) 2026/1744, see `docs/omnibus-2026-1744.md`). Every rule cites provision IDs
(docs/CONTRACTS.md §1); `all_citation_ids()` lists them all and `tests/test_engine_citations.py`
checks they resolve in the corpus.

## 1. Decision tree

```mermaid
flowchart TD
  A[FactSheet] --> B{is_ai_system = false?<br/>art:3.1}
  B -- yes, and not a GPAI model provider --> OOS[out_of_scope]
  B -- no / unknown --> C{Art. 2 exclusion?<br/>art:2.1 no EU nexus · 2.3 military · 2.4 third-country cooperation<br/>2.6 research only · 2.8 pre-market R&D · 2.10 personal use by deployer}
  C -- yes --> OOS
  C -- no --> D{Any Art. 5 rule fires?<br/>5.1.a · b · ba · bb · 5.1a · c · d · e · f · g · h}
  D -- yes --> P[prohibited]
  D -- no --> E{Annex I product AND safety component<br/>AND third-party assessment?<br/>art:6.1, 6.1a-c}
  E -- yes --> HR[high_risk]
  E -- no --> F{Annex III point?<br/>art:6.2}
  F -- yes --> G{Art. 6(3) derogation?<br/>a condition (a)-(d) AND no profiling<br/>AND output does not materially influence}
  G -- no --> HR
  G -- yes --> H
  F -- no --> H{Art. 50 duty?<br/>50.1 · 50.2 · 50.3 · 50.4}
  H -- yes --> L[limited_risk]
  H -- no --> I{FOSS licence?<br/>art:2.12}
  I -- yes --> OOS
  I -- no --> M[minimal_risk<br/>art:4.1 · art:95]
  P -.overlays.-> O[(Overlays: transparency_art50, gpai)]
  HR -.overlays.-> O
  L -.-> O
  M -.-> O
```

Precedence (CONTRACTS §5): out_of_scope → prohibited → high_risk → limited_risk → minimal_risk.
Art. 50 and GPAI duties are **overlays**, added whatever the tier (a high-risk emotion recognition
system also carries Art. 50(3)). The tier is "limited_risk" only when Art. 50 is the strongest regime.

## 2. Rules in prose

**(a) AI system** — `art:3.1`, `rec:12`. If the system only follows fixed human-written rules
(`is_ai_system = false`) it is out of scope. Exception: a provider of a general-purpose AI model is
not excluded on this ground (a model is not an AI system, but Art. 53 applies to it); the tier is then
minimal_risk with a GPAI overlay.

**(b) Scope** — `art:2.1` (EU nexus), `art:2.3` (exclusively military/defence/national security),
`art:2.4`, `art:2.6` (sole purpose of scientific R&D), `art:2.8` (R&D/testing before placing on the
market; real-world testing is *not* excluded), `art:2.10` (natural persons in purely personal,
non-professional use — only deployer obligations; a provider is not excluded). `art:2.12`
(free and open-source) is applied last, because it does not cover systems that are prohibited,
high-risk or subject to Art. 50.

**(c) Prohibitions** — one rule per point, conditions copied from the text:

| Rule | Fires when | Exception handled |
|---|---|---|
| `art:5.1.a` | subliminal/manipulative/deceptive techniques **and** material distortion causing significant harm | — |
| `art:5.1.b` | exploitation of age/disability/socio-economic vulnerability **and** significant harm | — |
| `art:5.1.ba`, `art:5.1.bb` | intended purpose / deployer use is non-consensual intimate material or CSAM (from 2 Dec 2026) | `art:5.1b` noted |
| `art:5.1a` (a)(ii) | foreseeable, reproducible generation without adequate safeguards — **providers only** (`art:5.1a.b`: deployers only if they use it for that purpose) | role unknown → assumed provider, recorded |
| `art:5.1.c` | social scoring with detrimental treatment | — |
| `art:5.1.d` | crime-risk prediction based **solely** on profiling/personality | support to human assessment based on objective facts is outside the fact definition |
| `art:5.1.e` | untargeted scraping of facial images | — |
| `art:5.1.f` | emotion inference **and** workplace/education | medical or safety reasons |
| `art:5.1.g` | biometric categorisation **and** inference of race, political opinions, union membership, religion/beliefs, sex life/orientation | labelling/filtering lawfully acquired datasets; categorisation in law enforcement |
| `art:5.1.h` | real-time **and** remote biometric identification **and** publicly accessible space **and** law enforcement | strictly necessary for objectives (i)–(iii); then high-risk Annex III 1(a) + note on `art:5.2`, `art:5.3` |

**(d) Annex I** — `art:6.1`: `annex_i_product` set **and** `safety_component` **and**
`annex_i_third_party_assessment`. The safety-component notion follows the Omnibus (`art:3.14`,
`art:6.1a`, `art:6.1b`); third-party assessment required only for non-health/safety risks does not
count (`art:6.1c`). The Annex I point is cited (e.g. `annex:I.A.11` medical devices). Section B
products (vehicles, aviation, rail, marine, agricultural vehicles, and — since the Omnibus — machinery
`annex:I.B.21`) are high-risk, but under `art:2.2` only Art. 6(1), 60a and 102–112 apply, so the engine
lists a single "comply via sectoral legislation" obligation and suppresses Art. 50 overlays (recorded
as an assumption).

**(e) Annex III and Art. 6(3)** — `art:6.2` + the Annex III point (one rule per point,
`annex:III.1.a` … `annex:III.8.b`). Biometric points are also derived from biometric facts (remote
identification → 1(a); categorisation by sensitive attributes → 1(b); emotion recognition → 1(c)).
Annex III 5(b) excludes financial-fraud detection. The derogation `art:6.3` applies only if **all**:

1. at least one of (a) narrow procedural task, (b) improves a previously completed human activity,
   (c) detects decision patterns without replacing/influencing human assessment, (d) preparatory task;
2. no profiling of natural persons (`art:6.3` third subparagraph — profiling is always high-risk);
3. `decision_impact` is "supports_human_decision" or "no_decision_about_persons".

Condition 3 is the engine's **conservative reading** of the first subparagraph ("does not pose a
significant risk … including by not materially influencing the outcome of decision making"): if the
output determines or materially influences the decision, the derogation is not applied and a note
explains why. If any of the three is unknown the system stays high-risk and the facts are reported as
unresolved. When the derogation applies the provider must document the assessment (`art:6.4`) and
register (`art:49.2`). The Omnibus did not amend Art. 6(2)–(8).

**(f) Transparency (Art. 50)** — `art:50.1` (interaction, unless obvious to a reasonably
well-informed person), `art:50.2` (machine-readable marking of synthetic content, unless assistive
standard editing), `art:50.3` (emotion recognition / biometric categorisation), `art:50.4` (deep fakes;
public-interest text unless human editorial control). The "authorised by law to fight crime"
exceptions are applied only when stated.

**(g) GPAI** — `art:53` (+ `art:54`) when the user provides a general-purpose AI model (`art:3.63`);
`art:55` (+ `art:51`, `art:52`) with systemic risk. Integrating someone else's model does **not** make
the integrator a GPAI provider (`art:3.68` downstream provider; `art:25.1` if the system becomes
high-risk). A substantial modification (e.g. fine-tuning) is conservatively treated as making the
integrator provider of the modified model (`rec:109`); the threshold is not in the Act.

**(h) Minimal** — Art. 4 AI literacy (as replaced by the Omnibus: "take measures to support", no
guaranteed level) and voluntary codes of conduct `art:95`.

## 3. Unknown facts, confidence and questions

* A positive condition whose fact is `None` never fires a rule.
* An **exception** whose fact is `None` (e.g. medical/safety reasons in 5(1)(f), "obvious" in 50(1),
  RBI objectives in 5(1)(h)) lets the rule fire conservatively; an explicit assumption is recorded.
  Rare statutory exceptions (crime-fighting authorisation, assistive editing, verification-only,
  fraud detection) are applied only when the fact is stated.
* Sensitivity analysis (`rules.sensitivity`, used by `classify` and `next_questions`): for each unknown
  fact in the registry (`questions.REGISTRY`, gated so follow-up facts are only probed once their
  parent fact is true), every possible value is tried; rules that the probed value keeps alive have
  their other unknown conditions optimistically completed, so chained conditions (e.g. Annex I
  product → safety component → third-party assessment) are detected. Impact = share of values that
  change (tier, overlays, derogation).
* Confidence: **low** if some unknown fact can change the tier; **medium** if it can only change an
  overlay or the derogation; **high** otherwise. `unresolved` lists those facts (plus `role` when the
  tier is prohibited/high/limited, since obligations depend on it).
* Assumptions are always recorded for: unknown EU nexus, unknown Art. 2 exclusion, unknown role.

## 4. Obligations and dates

Dates come from `art:113` as consolidated: Art. 4 and Art. 5 → 2025-02-02 (new 5(1)(ba)/(bb)/(1a)/(1b)
→ 2026-12-02); penalties (`art:99.3`) and GPAI → 2025-08-02; Art. 50 and Art. 95 → 2026-08-02;
high-risk duties → 2027-12-02 (Annex III) or 2028-08-02 (Annex I). Interpretation: Arts 43, 47–49,
72, 73 and 86 are outside Chapter III Sections 1–3 but presuppose a system classified as high-risk
under Art. 6, which only applies from those dates, so they carry the same date. Transitional rules:
`art:111.2` (legacy high-risk; public authorities by 2030-08-02), `art:111.3` (GPAI legacy by
2027-08-02), `art:111.4` (Art. 50(2) legacy by 2026-12-02).

Role filter: provider → provider duties; deployer → deployer duties; both/unknown → both sets; other
(importer/distributor) → Arts 23/24. FRIA (`art:27`) only for deployers of Annex III systems (not
point 2) that are public bodies or private entities providing public services, or for Annex III
5(b)/5(c); if public status is unknown it is listed as "should". `art:26.7` only for workplace use;
`art:26.11` and `art:86` only for Annex III systems deciding on natural persons; registration
`art:49.3` only for public-authority deployers.

## 5. Known limits

* Art. 25(1) re-qualification of deployers as providers is shown as an advisory obligation, not
  classified (no fact captures re-branding).
* Art. 2(13) limitations for Annex I Section A await delegated acts and are not modelled.
* Annex III "in so far as their use is permitted under Union or national law" and point 8(b)'s
  carve-out for tools whose output people are not directly exposed to are left to the narrative.
