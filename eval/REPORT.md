# Evaluation report

Generated 2026-11-04 07:59 UTC by `eval/run_eval.py`. Test set: `eval/cases.yaml` (56 labelled cases; see `eval/README.md`).

Law baseline: Regulation (EU) 2024/1689 consolidated 2026-07-27 (incl. Regulation (EU) 2026/1744).

## Headline table

| Configuration | Tier accuracy | Under-classified | Overlays | Asked when needed | Citation validity | Citation recall | p50 latency (uncached) | Mean cost / assessment | Errors |
|---|---|---|---|---|---|---|---|---|---|
| **hybrid** · claude_cli · `sonnet` | 54/56 (96%) | 0% | 100% | 57% | 100% | 84% | 9.8 s | $0.0298 | 0 |
| **hybrid** · local_mlx · `Qwen2.5-3B-Instruct-4bit` | 42/56 (75%) | 14% | 81% | 29% | 100% | 52% | 16.8 s | $0.0000 | 2 |
| **baseline** · claude_cli · `sonnet` | 53/56 (95%) | 2% | 93% | 0% | 100% | 49% | 7.7 s | $0.0106 | 0 |

Definitions: *Tier accuracy* = exact match of the risk tier. *Under-classified* = predicted a less severe tier than the label (the dangerous error). *Overlays* = Art. 50 / GPAI overlays exactly right (among completed runs). *Asked when needed* = share of `should_ask` cases where at least one clarifying question was asked. *Citation validity* = share of cited IDs that resolve to a real provision. *Citation recall* = share of the labelled key provisions that were cited. Cost = API-equivalent USD reported by the Claude CLI (billed as subscription) or $0 for local models (Apple M4 Max). Latency is the median over assessments whose LLM calls were not served from the cache; it includes all LLM calls and question rounds.

## hybrid · claude_cli · sonnet

Run 2026-11-04T07:58:43+00:00 on Claude Code CLI (subscription); wall time 281.2 s; uncached p50 9.8 s; p95 13.1 s; mean tokens in/out 8068/1146; hard-case accuracy 90%; stripped (disallowed) citations 0; file `20261104-085402-hybrid__claude_cli__sonnet.json`.

| Case | Expected | Got | Asked | Note |
|---|---|---|---|---|
| `edge-university-research-depression-voice` | out_of_scope | minimal_risk | yes | missing: art:2.6, art:2.8 |
| `edge-us-credit-api-scope-unknown` | out_of_scope | high_risk | no | missing: art:2.1 |

## hybrid · local_mlx · mlx-community/Qwen2.5-3B-Instruct-4bit

Run 2026-11-04T07:47:32+00:00 on Apple M4 Max, 48 GB; wall time 1416.6 s; uncached p50 16.8 s; p95 56.9 s; mean tokens in/out 4757/726; hard-case accuracy 70%; stripped (disallowed) citations 50; file `20261103-183311-hybrid__local_mlx__mlx-community_Qwen2.5-3B-Instruct-4bit.json`.

| Case | Expected | Got | Asked | Note |
|---|---|---|---|---|
| `annex3-4b-rider-shift-allocation` | high_risk | out_of_scope | no | missing: annex:III.4.b, art:6.2, art:26 |
| `annex3-5d-emergency-call-triage` | high_risk | None | no | could not extract facts: no valid JSON object found (Expecting property name enc |
| `annex3-6e-profiling-fraud-network` | high_risk | minimal_risk | no | missing: annex:III.6.e, art:6.2, art:6.3 |
| `edge-admissions-completeness-check` | minimal_risk | high_risk | yes | missing: art:6.3, art:6.3.a |
| `edge-categorisation-clothing-colour` | minimal_risk | out_of_scope | no | missing: art:5.1.g, annex:III.1.b |
| `edge-categorisation-race-ethnicity` | prohibited | high_risk | yes | missing: art:5.1.g, art:3.40 |
| `edge-cv-dedupe-formatting` | minimal_risk | out_of_scope | no | missing: art:6.3, art:6.3.a, art:6.4 |
| `edge-gpai-integrator-support-bot` | limited_risk | out_of_scope | no | missing: art:50.1, art:50.2, art:3.68 |
| `edge-military-targeting` | out_of_scope | high_risk | no | missing: art:2.3 |
| `edge-nudify-app` | prohibited | None | no | could not extract facts: no valid JSON object found (Expecting ',' delimiter: li |
| `edge-police-realtime-frs-square` | prohibited | high_risk | no | missing: art:5.1.h, art:5.2, annex:II |
| `edge-pre-market-prototype` | out_of_scope | high_risk | yes | missing: art:2.8 |
| `edge-retail-gender-age-categorisation` | limited_risk | minimal_risk | yes | missing: art:50.3, annex:III.1.b, art:5.1.g |
| `edge-university-research-depression-voice` | out_of_scope | high_risk | no | missing: art:2.6, art:2.8 |

## baseline · claude_cli · sonnet

Run 2026-11-04T07:53:53+00:00 on Claude Code CLI (subscription); wall time 460.0 s; uncached p50 7.7 s; p95 12.9 s; mean tokens in/out 1657/400; hard-case accuracy 80%; stripped (disallowed) citations 0; file `20261104-084613-baseline__claude_cli__sonnet.json`.

| Case | Expected | Got | Asked | Note |
|---|---|---|---|---|
| `edge-admissions-completeness-check` | minimal_risk | high_risk | no | missing: art:6.3, art:6.3.a |
| `edge-careers-chatbot-screening-unknown` | high_risk | limited_risk | no | missing: annex:III.4.a, art:6.3, art:26 |
| `edge-us-credit-api-scope-unknown` | out_of_scope | high_risk | no |  |

## Accuracy by case source (hybrid configurations)

| Source | n | `sonnet` | `Qwen2.5-3B-Instruct-4bit` |
|---|---|---|---|
| annex_iii | 25 | 25/25 | 22/25 |
| art5 | 4 | 4/4 | 1/4 |
| art50 | 2 | 2/2 | 2/2 |
| commission_guidelines | 8 | 8/8 | 5/8 |
| edge | 15 | 13/15 | 10/15 |
| gpai | 2 | 2/2 | 2/2 |
