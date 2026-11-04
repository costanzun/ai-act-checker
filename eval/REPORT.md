# Evaluation report

Generated 2026-11-03 20:18 UTC by `eval/run_eval.py`. Test set: `eval/cases.yaml` (56 labelled cases; see `eval/README.md`).

Law baseline: Regulation (EU) 2024/1689 consolidated 2026-07-27 (incl. Regulation (EU) 2026/1744).

## Headline table

| Configuration | Tier accuracy | Under-classified | Overlays | Asked when needed | Citation validity | Citation recall | p50 latency | Mean cost / assessment | Errors |
|---|---|---|---|---|---|---|---|---|---|
| **hybrid** · claude_cli · `sonnet` | 14/56 (25%) | 0% | 100% | 0% | 100% | 95% | 2.2 s | $0.0230 | 42 |

Definitions: *Tier accuracy* = exact match of the risk tier. *Under-classified* = predicted a less severe tier than the label (the dangerous error). *Overlays* = Art. 50 / GPAI overlays exactly right (among completed runs). *Asked when needed* = share of `should_ask` cases where at least one clarifying question was asked. *Citation validity* = share of cited IDs that resolve to a real provision. *Citation recall* = share of the labelled key provisions that were cited. Cost = API-equivalent USD reported by the Claude CLI (billed as subscription) or $0 for local models (Apple M4 Max). Latency includes all LLM calls and question rounds; cached calls are included where marked.

## hybrid · claude_cli · sonnet

Run 2026-11-03T20:18:41+00:00 on Claude Code CLI (subscription); wall time 220.7 s; uncached p50 2.2 s; p95 31.0 s; mean tokens in/out 5883/809; hard-case accuracy 20%; stripped (disallowed) citations 0; file `20261103-174310-hybrid__claude_cli__sonnet.json`.

| Case | Expected | Got | Asked | Note |
|---|---|---|---|---|
| `annex3-5c-life-insurance-pricing` | high_risk | None | no | claude CLI exited 1: Warning: no stdin data received in 3s, proceeding without i |
| `annex3-5d-emergency-call-triage` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-6a-dv-victim-risk` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-6b-police-deception-detection` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-6c-evidence-reliability` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-6d-reoffending-objective-facts` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-6e-profiling-fraud-network` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-7a-border-deception-kiosk` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-7b-traveller-risk-scoring` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-7c-asylum-credibility` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-7d-border-face-identification` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-8a-judicial-drafting-assistant` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `annex3-8b-voter-microtargeting` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-admissions-completeness-check` | minimal_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-careers-chatbot-screening-unknown` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-categorisation-clothing-colour` | minimal_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-categorisation-race-ethnicity` | prohibited | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-cobot-safety-machinery` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-cv-dedupe-formatting` | minimal_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-cv-ranking-personality-profiling` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-cv-screener-hr-deployer` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-deepfake-marketing-video` | limited_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-emotion-employees-wellbeing` | prohibited | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-emotion-safety-control-room` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-fraud-detection-loan-applications` | minimal_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-gpai-integrator-support-bot` | limited_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-internal-helpdesk-bot-obviously-ai` | minimal_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-medical-device-skin-cancer` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-meeting-emotion-plugin-context-unknown` | prohibited | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-military-targeting` | out_of_scope | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-nudify-app` | prohibited | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-performance-promotion-role-unknown` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-police-post-rbi` | high_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-police-realtime-frs-square` | prohibited | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-pre-market-prototype` | out_of_scope | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-predictive-policing-profiling-only` | prohibited | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-retail-gender-age-categorisation` | limited_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-spam-filter` | minimal_risk | None | no | claude CLI exited 1: Warning: no stdin data received in 3s, proceeding without i |
| `edge-university-research-depression-voice` | out_of_scope | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `edge-us-credit-api-scope-unknown` | out_of_scope | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `gpai-model-provider` | minimal_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |
| `gpai-systemic-risk-frontier` | minimal_risk | None | no | claude CLI error: You've hit your 5-hour limit · resets 10:40pm (Europe/Rome) |

## Accuracy by case source (hybrid configurations)

| Source | n | `sonnet` |
|---|---|---|
| annex_iii | 25 | 12/25 |
| art5 | 4 | 0/4 |
| art50 | 2 | 1/2 |
| commission_guidelines | 8 | 1/8 |
| edge | 15 | 0/15 |
| gpai | 2 | 0/2 |
