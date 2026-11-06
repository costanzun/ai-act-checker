// Mirrors docs/CONTRACTS.md §2, §5, §7.

export type Lang = "en" | "it";
export type LText = Record<string, string>; // {"en": ..., "it": ...}

export type Tier = "prohibited" | "high_risk" | "limited_risk" | "minimal_risk" | "out_of_scope";
export type Confidence = "high" | "medium" | "low";
export type Role = "provider" | "deployer" | "both" | "other" | "unknown";

/** FactSheet is owned by the backend; `null` always means "unknown". */
export type FactValue = string | number | boolean | null | FactValue[] | { [k: string]: FactValue };
export type FactSheet = { [k: string]: FactValue };

export interface Milestone {
  id: string;
  date: string;
  what: LText;
  citations: string[];
  status: "in_force" | "upcoming";
}

export type FindingKind =
  | "prohibition" | "high_risk_annex_iii" | "high_risk_annex_i" | "derogation_6_3"
  | "transparency" | "gpai" | "scope" | "not_ai_system" | "note";

export interface Finding {
  rule_id: string;
  kind: FindingKind;
  title: LText;
  rationale: LText;
  citations: string[];
  facts_used: string[];
  decisive: boolean;
}

export interface Classification {
  tier: Tier;
  confidence: Confidence;
  findings: Finding[];
  overlays: Record<string, string[]>;
  role: Role;
  applies_from: Milestone[];
  unresolved: string[];
  assumptions: LText[];
}

export interface QuestionOption {
  value: string | number | boolean;
  label: LText;
}

export interface Question {
  id: string;
  fact_path: string;
  text: LText;
  why: LText;
  type: "single" | "boolean" | "text";
  options: QuestionOption[];
  impact: number;
}

export type ObligationCategory =
  | "governance" | "documentation" | "data" | "transparency" | "oversight"
  | "registration" | "monitoring" | "literacy" | "other";

export interface Obligation {
  id: string;
  role: "provider" | "deployer" | "both";
  category: ObligationCategory;
  title: LText;
  summary: LText;
  citations: string[];
  applies_from: string | null;
  priority: "must" | "should";
}

export interface ChecklistItem {
  id: string;
  title: LText;
  description: LText;
  citations: string[];
  obligation_ids: string[];
  template_hint: LText | null;
}

export interface RelatedProvision { id: string; why: LText }

export interface Metrics {
  latency_ms: number; llm_calls: number; input_tokens: number; output_tokens: number;
  cost_usd: number; cached: boolean;
}

/** Engine counterfactual: an answer that could move the tier (backend `engine/whatif.py`). */
export interface WhatIf {
  fact_path: string;
  question: LText;
  why: LText;
  current: LText;
  current_value: FactValue;
  answer: LText;
  value: string | number | boolean | null;
  tier: Tier;
  unresolved: boolean;
  actionable: boolean;
}

export interface Assessment {
  id: string;
  created_at: string;
  language: Lang;
  law_as_of: string;
  checked_at: string;
  model: { provider: string; model: string };
  description: string;
  facts: FactSheet;
  classification: Classification;
  /** Additive (proposed): one-sentence plain-language summary shown in the tier hero. */
  summary?: LText;
  reasoning_md: string;
  obligations: Obligation[];
  checklist: ChecklistItem[];
  related_provisions: RelatedProvision[];
  uncertainties: LText[];
  /** Answers that could change the tier; may be absent on assessments saved before it existed. */
  what_if?: WhatIf[];
  disclaimer: LText;
  metrics: Metrics;
}

export interface Meta {
  law_as_of: string;
  checked_at: string;
  celex: string;
  amending_acts: { celex: string; marker?: string; short_title: string; oj_date?: string; in_force?: string }[];
  provider: string;
  model: string;
  timeline: Milestone[];
  disclaimer: LText;
  languages: Lang[];
}

export interface ExampleItem {
  id: string;
  title: string;
  description: string;
  tags: string[];
  expected_tier: Tier;
  /** Additive (proposed): full plain-language prompt to run. Falls back to `description`. */
  text?: string;
  /** Optional: additive overlays such as "gpai". */
  expected_overlays?: string[];
}

export interface Amendment { marker: string; kind: "replaced" | "inserted" | "deleted"; by: string }

export interface Provision {
  id: string;
  type: string;
  label: string;
  parent_id: string | null;
  children: string[];
  title: string | null;
  text: string;
  amendment: Amendment | null;
  chapter?: string | null;
  chapter_title?: string | null;
  order?: number;
}

export interface LawResponse {
  provision: Provision;
  full_text: string;
  breadcrumb: { id: string; label: string }[];
  children: Provision[];
  eurlex_url: string;
}

export interface Answer { fact_path: string; value: string | number | boolean | null }

export interface AssessRequest {
  description: string;
  language: Lang;
  session_id?: string | null;
  facts?: FactSheet | null;
  answers?: Answer[];
  round: number;
  /** Echo of the `asked` list from the last `questions` event. */
  asked?: string[];
  provider?: string | null;
  model?: string | null;
}

export type Stage = "extracting" | "retrieving" | "classifying" | "drafting" | "finalising";

export type SseEvent =
  | { type: "stage"; stage: Stage; message: LText }
  | { type: "facts"; facts: FactSheet }
  | { type: "questions"; questions: Question[]; facts: FactSheet; round: number; session_id: string; asked?: string[] }
  | { type: "token"; section: string; text: string }
  | { type: "verdict"; assessment: Assessment }
  | { type: "result"; assessment: Assessment }
  | { type: "done"; status: "complete" | "needs_clarification" }
  | { type: "error"; message: LText; code: "llm_unavailable" | "invalid_input" | "internal" };
