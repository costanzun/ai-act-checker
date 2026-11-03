"""FactSheet: the structured facts about an AI system that drive classification.

This module is a shared CONTRACT (see docs/CONTRACTS.md §4). Other modules
(LLM extraction prompts, rule engine, question selector, eval runner, UI)
depend on these field names. Changes must be additive.

Convention: ``None`` always means "unknown / not stated". The rule engine
treats unknown facts conservatively and the question selector decides whether
an unknown fact is worth asking about.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["provider", "deployer", "both", "other"]
# "other" = importer / distributor / product manufacturer / affected person only.

ScopeExclusion = Literal[
    "none",
    "military_defence_national_security",  # Art. 2(3)
    "scientific_research_only",  # Art. 2(6)
    "pre_market_research_testing",  # Art. 2(8) (not real-world testing)
    "personal_non_professional",  # Art. 2(10)
    "third_country_public_authority_cooperation",  # Art. 2(4)
]

Sector = Literal[
    "biometrics",
    "critical_infrastructure",
    "education_vocational_training",
    "employment_workers_management",
    "essential_private_services",  # credit, insurance
    "essential_public_services",  # benefits, healthcare access, emergency services
    "law_enforcement",
    "migration_asylum_border",
    "justice_democratic_processes",
    "healthcare",
    "finance_other",
    "retail_marketing",
    "media_entertainment",
    "manufacturing_industrial",
    "transport_mobility",
    "software_it",
    "public_administration_other",
    "other",
]

DecisionImpact = Literal[
    "determines_outcome",  # the system's output is the decision
    "materially_influences",  # a human decides but relies substantially on the output
    "supports_human_decision",  # informative input; human genuinely assesses
    "no_decision_about_persons",  # does not concern decisions about natural persons
]

HumanOversight = Literal["fully_automated", "human_in_the_loop", "human_reviews_all"]

AnnexIIIArea = Literal[
    "1a_remote_biometric_identification",
    "1b_biometric_categorisation_sensitive",
    "1c_emotion_recognition",
    "2_critical_infrastructure_safety",
    "3a_education_admission",
    "3b_education_evaluation",
    "3c_education_level_assessment",
    "3d_education_proctoring",
    "4a_recruitment_selection",
    "4b_work_decisions_monitoring",
    "5a_public_benefits_eligibility",
    "5b_creditworthiness",
    "5c_life_health_insurance_pricing",
    "5d_emergency_dispatch_triage",
    "6a_le_victim_risk",
    "6b_le_polygraph",
    "6c_le_evidence_reliability",
    "6d_le_offending_risk_profiling",
    "6e_le_profiling_investigation",
    "7a_migration_polygraph",
    "7b_migration_risk_assessment",
    "7c_migration_application_examination",
    "7d_migration_identification",
    "8a_justice_assist_judicial",
    "8b_elections_influence",
    "none",
]

AnnexIProduct = Literal[
    "none",
    "machinery",
    "toys",
    "recreational_craft",
    "lifts",
    "equipment_explosive_atmospheres",
    "radio_equipment",
    "pressure_equipment",
    "cableways",
    "personal_protective_equipment",
    "gas_appliances",
    "medical_devices",
    "in_vitro_diagnostics",
    "civil_aviation",
    "vehicles",
    "agricultural_vehicles",
    "marine_equipment",
    "rail",
    "other_regulated_product",
]


class BiometricFacts(BaseModel):
    uses_biometric_data: bool | None = None
    remote_identification: bool | None = Field(
        None, description="Identifies persons at a distance by comparing biometrics to a database"
    )
    real_time: bool | None = None
    publicly_accessible_space: bool | None = None
    categorisation: bool | None = Field(None, description="Assigns persons to categories based on biometric data")
    infers_sensitive_attributes: bool | None = Field(
        None, description="Infers race, political opinions, trade union membership, religion, sex life or sexual orientation"
    )
    emotion_recognition: bool | None = Field(None, description="Infers emotions or intentions from biometric data")
    verification_only: bool | None = Field(None, description="One-to-one verification of a claimed identity only")


class ManipulationFacts(BaseModel):
    subliminal_or_deceptive: bool | None = None
    exploits_vulnerabilities: bool | None = Field(None, description="Age, disability or socio-economic situation")
    distorts_behaviour_significant_harm: bool | None = None


class Art63Facts(BaseModel):
    """Art. 6(3) derogation conditions (only relevant for Annex III areas)."""

    narrow_procedural_task: bool | None = None
    improves_prior_human_activity: bool | None = None
    detects_patterns_without_replacing_assessment: bool | None = None
    preparatory_task_only: bool | None = None
    profiling_of_natural_persons: bool | None = Field(None, description="If True the derogation never applies")


class GPAIFacts(BaseModel):
    is_gpai_model: bool | None = Field(None, description="The thing described is itself a general-purpose AI model")
    provider_of_model: bool | None = Field(None, description="The user develops/places the model on the market")
    systemic_risk: bool | None = Field(None, description="Training compute > 10^25 FLOPs or designated by the Commission")
    integrates_third_party_gpai: bool | None = Field(None, description="The system builds on someone else's GPAI model")
    substantially_modifies_model: bool | None = None


class TransparencyFacts(BaseModel):
    interacts_with_natural_persons: bool | None = Field(None, description="Chatbot, voice assistant, avatar")
    obvious_to_users_it_is_ai: bool | None = None
    generates_synthetic_content: bool | None = Field(None, description="Audio, image, video or text output")
    deepfake: bool | None = Field(None, description="Resembles real persons, places, events and may appear authentic")
    public_interest_text: bool | None = Field(None, description="Text published to inform the public on matters of public interest")


class LawEnforcementFacts(BaseModel):
    used_by_or_for_law_enforcement: bool | None = None
    predictive_policing_profiling_only: bool | None = Field(
        None, description="Predicts criminal offences based solely on profiling/personality traits"
    )
    untargeted_facial_scraping: bool | None = None


class FactSheet(BaseModel):
    """All facts extracted from the user's description and answers."""

    system_summary: str = Field("", description="One neutral sentence restating what the system does")
    is_ai_system: bool | None = Field(
        None, description="Art. 3(1): machine-based, infers from inputs how to generate outputs, some autonomy. False for plain rule-based software."
    )
    role: Role | None = None
    in_eu_scope: bool | None = Field(None, description="Placed on the EU market, used in the EU, or output used in the EU (Art. 2(1))")
    scope_exclusion: ScopeExclusion | None = None
    sector: Sector | None = None
    purpose: str = Field("", description="Intended purpose in the provider's words")
    affected_persons: list[str] = Field(default_factory=list)
    decision_impact: DecisionImpact | None = None
    human_oversight: HumanOversight | None = None
    annex_iii_area: AnnexIIIArea | None = None
    annex_i_product: AnnexIProduct | None = None
    safety_component: bool | None = Field(None, description="Is a safety component of, or is itself, an Annex I product")
    context_workplace_or_education: bool | None = None
    social_scoring: bool | None = Field(None, description="Evaluates/classifies persons over time on social behaviour or personal traits leading to detrimental treatment")
    nudify_or_sexual_abuse_material: bool | None = Field(
        None, description="Generates non-consensual intimate imagery or child sexual abuse material (Art. 5(1)(ba)/(bb) as amended)"
    )
    biometric: BiometricFacts = Field(default_factory=BiometricFacts)
    manipulation: ManipulationFacts = Field(default_factory=ManipulationFacts)
    art63: Art63Facts = Field(default_factory=Art63Facts)
    gpai: GPAIFacts = Field(default_factory=GPAIFacts)
    transparency: TransparencyFacts = Field(default_factory=TransparencyFacts)
    law_enforcement: LawEnforcementFacts = Field(default_factory=LawEnforcementFacts)
    free_text_notes: list[str] = Field(default_factory=list, description="Anything relevant the schema cannot capture")

    # ---- helpers -----------------------------------------------------------------
    def get_path(self, path: str) -> Any:
        node: Any = self
        for part in path.split("."):
            node = getattr(node, part) if isinstance(node, BaseModel) else node.get(part)
            if node is None:
                return None
        return node

    def with_answer(self, path: str, value: Any) -> "FactSheet":
        data = self.model_dump()
        node = data
        parts = path.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
        return FactSheet.model_validate(data)

    def unknown_paths(self) -> list[str]:
        """Dotted paths of every scalar field that is None."""
        out: list[str] = []

        def walk(model: BaseModel, prefix: str) -> None:
            for name, value in model:
                path = f"{prefix}{name}"
                if isinstance(value, BaseModel):
                    walk(value, path + ".")
                elif value is None:
                    out.append(path)

        walk(self, "")
        return out


def fact_schema_for_prompt() -> dict[str, Any]:
    """JSON schema of FactSheet, used by LLM extraction prompts."""
    return FactSheet.model_json_schema()
