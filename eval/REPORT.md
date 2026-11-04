# Evaluation report

Generated 2026-11-04 07:46 UTC by `eval/run_eval.py`. Test set: `eval/cases.yaml` (56 labelled cases; see `eval/README.md`).

Law baseline: Regulation (EU) 2024/1689 consolidated 2026-07-27 (incl. Regulation (EU) 2026/1744).

## Headline table

| Configuration | Tier accuracy | Under-classified | Overlays | Asked when needed | Citation validity | Citation recall | p50 latency | Mean cost / assessment | Errors |
|---|---|---|---|---|---|---|---|---|---|
| **hybrid** · claude_cli · `sonnet` | 53/56 (95%) | 2% | 100% | 57% | 100% | 83% | 16.1 s | $0.0297 | 0 |

Definitions: *Tier accuracy* = exact match of the risk tier. *Under-classified* = predicted a less severe tier than the label (the dangerous error). *Overlays* = Art. 50 / GPAI overlays exactly right (among completed runs). *Asked when needed* = share of `should_ask` cases where at least one clarifying question was asked. *Citation validity* = share of cited IDs that resolve to a real provision. *Citation recall* = share of the labelled key provisions that were cited. Cost = API-equivalent USD reported by the Claude CLI (billed as subscription) or $0 for local models (Apple M4 Max). Latency includes all LLM calls and question rounds; cached calls are included where marked.

## hybrid · claude_cli · sonnet

Run 2026-11-04T07:46:09+00:00 on Claude Code CLI (subscription); wall time 843.6 s; uncached p50 16.8 s; p95 22.8 s; mean tokens in/out 8058/1141; hard-case accuracy 90%; stripped (disallowed) citations 0; file `20261104-083206-hybrid__claude_cli__sonnet.json`.

| Case | Expected | Got | Asked | Note |
|---|---|---|---|---|
| `edge-meeting-emotion-plugin-context-unknown` | prohibited | high_risk | yes | missing: art:5.1.f |
| `edge-university-research-depression-voice` | out_of_scope | minimal_risk | yes | missing: art:2.6, art:2.8 |
| `edge-us-credit-api-scope-unknown` | out_of_scope | high_risk | no | missing: art:2.1 |

## Accuracy by case source (hybrid configurations)

| Source | n | `sonnet` |
|---|---|---|
| annex_iii | 25 | 25/25 |
| art5 | 4 | 4/4 |
| art50 | 2 | 2/2 |
| commission_guidelines | 8 | 8/8 |
| edge | 15 | 12/15 |
| gpai | 2 | 2/2 |
