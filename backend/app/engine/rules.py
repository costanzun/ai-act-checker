"""Deterministic classification rules for Regulation (EU) 2024/1689 as amended by
Regulation (EU) 2026/1744 (consolidated text of 27 July 2026).

Every rule is hand-authored from the text and carries its provision IDs.
See docs/legal-logic.md for the decision tree in prose.

Evaluation semantics
--------------------
* A rule has positive conditions (``when``) and exceptions.
* A positive condition whose fact is ``None`` (unknown) never satisfies the rule:
  the rule is *pending* and its missing paths are reported.
* An exception whose fact is unknown is handled in one of two ways:
  ``ask=True``  -> the rule fires conservatively, an explicit assumption is
                   recorded and the path is reported as unresolved;
  ``ask=False`` -> rare statutory exceptions (e.g. use authorised by law to
                   prosecute crime): treated as not applying; the rationale says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Literal

from . import timeline as tl
from .facts import FactSheet
from .knowledge.annexes import ANNEX_I, ANNEX_III
from .models import Classification, Finding, Milestone

Bi = dict[str, str]


def B(en: str, it: str) -> Bi:
    return {"en": en, "it": it}


# ---------------------------------------------------------------------------
# Condition tree
# ---------------------------------------------------------------------------
class Node:
    def status(self, f: FactSheet) -> str:  # "sat" | "fail" | "unk"
        raise NotImplementedError

    def missing(self, f: FactSheet) -> list[str]:
        raise NotImplementedError

    def complete(self, f: FactSheet, out: dict[str, Any]) -> None:
        """Add assignments for unknown leaves that would make this node satisfied."""
        raise NotImplementedError

    def assumptions(self, f: FactSheet) -> list[tuple[str, Bi]]:
        return []

    def paths(self) -> set[str]:
        raise NotImplementedError

    def leaves(self) -> list["C"]:
        raise NotImplementedError


@dataclass(eq=False)
class C(Node):
    path: str
    values: tuple
    none_ok: bool = False  # unknown counts as satisfied (silently)
    none_assumption: Bi | None = None  # unknown counts as satisfied, with an explicit assumption

    def _val(self, f: FactSheet) -> Any:
        return f.get_path(self.path)

    def status(self, f: FactSheet) -> str:
        v = self._val(f)
        if v is None:
            return "sat" if (self.none_ok or self.none_assumption) else "unk"
        return "sat" if v in self.values else "fail"

    def missing(self, f: FactSheet) -> list[str]:
        return [self.path] if self.status(f) == "unk" else []

    def complete(self, f: FactSheet, out: dict[str, Any]) -> None:
        if self.status(f) == "unk" and self.path not in out:
            out[self.path] = self.values[0]

    def assumptions(self, f: FactSheet) -> list[tuple[str, Bi]]:
        if self.none_assumption and self._val(f) is None:
            return [(self.path, self.none_assumption)]
        return []

    def paths(self) -> set[str]:
        return {self.path}

    def leaves(self) -> list["C"]:
        return [self]


@dataclass(eq=False)
class All(Node):
    children: list[Node]

    def status(self, f: FactSheet) -> str:
        st = [c.status(f) for c in self.children]
        if "fail" in st:
            return "fail"
        return "sat" if all(s == "sat" for s in st) else "unk"

    def missing(self, f: FactSheet) -> list[str]:
        if self.status(f) == "fail":
            return []
        return [p for c in self.children for p in c.missing(f)]

    def complete(self, f: FactSheet, out: dict[str, Any]) -> None:
        for c in self.children:
            if c.status(f) != "fail":
                c.complete(f, out)

    def assumptions(self, f: FactSheet) -> list[tuple[str, Bi]]:
        return [a for c in self.children for a in c.assumptions(f)]

    def paths(self) -> set[str]:
        return set().union(*(c.paths() for c in self.children))

    def leaves(self) -> list[C]:
        return [lf for c in self.children for lf in c.leaves()]


@dataclass(eq=False)
class Any_(Node):
    children: list[Node]

    def status(self, f: FactSheet) -> str:
        st = [c.status(f) for c in self.children]
        if "sat" in st:
            return "sat"
        return "fail" if all(s == "fail" for s in st) else "unk"

    def missing(self, f: FactSheet) -> list[str]:
        if self.status(f) != "unk":
            return []
        return [p for c in self.children for p in c.missing(f)]

    def complete(self, f: FactSheet, out: dict[str, Any]) -> None:
        if self.status(f) == "sat":
            return
        for c in self.children:
            if c.status(f) == "unk":
                c.complete(f, out)
                return

    def assumptions(self, f: FactSheet) -> list[tuple[str, Bi]]:
        for c in self.children:
            if c.status(f) == "sat":
                return c.assumptions(f)
        return []

    def paths(self) -> set[str]:
        return set().union(*(c.paths() for c in self.children))

    def leaves(self) -> list[C]:
        return [lf for c in self.children for lf in c.leaves()]


def T(path: str) -> C:
    return C(path, (True,))


def F(path: str) -> C:
    return C(path, (False,))


@dataclass(eq=False)
class Exc:
    """Exception that blocks a rule when its fact is True."""

    path: str
    ask: bool
    assumption: Bi | None = None


Effect = Literal["out_of_scope", "prohibited", "high_risk_i", "high_risk_iii", "derogation", "overlay", "note"]


@dataclass(eq=False)
class Rule:
    id: str
    kind: str
    effect: Effect
    when: Node
    title: Bi
    rationale: Bi
    citations: list[str]
    exceptions: list[Exc] = field(default_factory=list)
    overlay: tuple[str, list[str]] | None = None
    cite_fn: Callable[[FactSheet], list[str]] | None = None
    rationale_fn: Callable[[FactSheet], Bi] | None = None
    extra_citations: list[str] = field(default_factory=list)  # every ID cite_fn may emit

    def paths(self) -> set[str]:
        return self.when.paths() | {e.path for e in self.exceptions}

    def cites(self, f: FactSheet) -> list[str]:
        out = list(self.citations)
        if self.cite_fn:
            out += [c for c in self.cite_fn(f) if c not in out]
        return out

    def all_citations(self) -> set[str]:
        return set(self.citations) | set(self.extra_citations)


@dataclass
class RuleEval:
    rule: Rule
    status: str  # "fire" | "fail" | "pending"
    missing: list[str]
    assumptions: list[tuple[str, Bi]]
    open_exceptions: list[str]


def eval_rule(r: Rule, f: FactSheet) -> RuleEval:
    st = r.when.status(f)
    if st == "fail":
        return RuleEval(r, "fail", [], [], [])
    for e in r.exceptions:
        if f.get_path(e.path) is True:
            return RuleEval(r, "fail", [], [], [])
    if st == "unk":
        return RuleEval(r, "pending", r.when.missing(f), [], [])
    assumptions = list(r.when.assumptions(f))
    open_exc: list[str] = []
    for e in r.exceptions:
        if e.ask and f.get_path(e.path) is None:
            open_exc.append(e.path)
            if e.assumption:
                assumptions.append((e.path, e.assumption))
    return RuleEval(r, "fire", [], assumptions, open_exc)


# ---------------------------------------------------------------------------
# Rule catalogue
# ---------------------------------------------------------------------------
LE_EXC = Exc("law_enforcement.authorised_by_law_for_criminal_offences", ask=False)

# (a) not an AI system; (b) Art. 2 scope ----------------------------------------
SCOPE_RULES: list[Rule] = [
    Rule(
        id="art3.1-not-ai-system",
        kind="not_ai_system",
        effect="out_of_scope",
        when=All(
            [
                F("is_ai_system"),
                Any_([C("gpai.is_gpai_model", (False,), none_ok=True), C("gpai.provider_of_model", (False,), none_ok=True)]),
            ]
        ),
        title=B("Not an AI system", "Non è un sistema di IA"),
        rationale=B(
            "The system does not infer from its inputs how to generate outputs with some autonomy; it does not meet the definition of 'AI system', so the AI Act does not apply.",
            "Il sistema non deduce dagli input come generare output con un certo grado di autonomia; non rientra nella definizione di «sistema di IA» e il regolamento non si applica.",
        ),
        citations=["art:3.1", "rec:12"],
    ),
    Rule(
        id="art2.1-no-eu-nexus",
        kind="scope",
        effect="out_of_scope",
        when=F("in_eu_scope"),
        title=B("No link with the EU market", "Nessun collegamento con il mercato dell'UE"),
        rationale=B(
            "The system is not placed on the EU market, not used in the EU and its output is not used in the EU.",
            "Il sistema non è immesso sul mercato dell'UE, non è usato nell'UE e il suo output non è utilizzato nell'UE.",
        ),
        citations=["art:2.1"],
    ),
    Rule(
        id="art2.3-military",
        kind="scope",
        effect="out_of_scope",
        when=C("scope_exclusion", ("military_defence_national_security",)),
        title=B("Excluded: military, defence or national security", "Escluso: finalità militari, di difesa o di sicurezza nazionale"),
        rationale=B(
            "AI systems used exclusively for military, defence or national security purposes are outside the scope of the Act. Dual use (e.g. also civilian) is not covered by the exclusion.",
            "I sistemi di IA usati esclusivamente per finalità militari, di difesa o di sicurezza nazionale sono esclusi. L'uso duale (anche civile) non rientra nell'esclusione.",
        ),
        citations=["art:2.3", "rec:24"],
    ),
    Rule(
        id="art2.4-third-country-cooperation",
        kind="scope",
        effect="out_of_scope",
        when=C("scope_exclusion", ("third_country_public_authority_cooperation",)),
        title=B("Excluded: third-country authority cooperation", "Escluso: cooperazione con autorità di paesi terzi"),
        rationale=B(
            "Public authorities of third countries and international organisations using AI in law-enforcement or judicial cooperation with the EU, with adequate safeguards, are excluded.",
            "Sono escluse le autorità pubbliche di paesi terzi e le organizzazioni internazionali che usano l'IA nella cooperazione di polizia o giudiziaria con l'UE, con garanzie adeguate.",
        ),
        citations=["art:2.4"],
    ),
    Rule(
        id="art2.6-scientific-research",
        kind="scope",
        effect="out_of_scope",
        when=C("scope_exclusion", ("scientific_research_only",)),
        title=B("Excluded: scientific research and development", "Escluso: ricerca e sviluppo scientifici"),
        rationale=B(
            "AI systems or models, including their output, specifically developed and put into service for the sole purpose of scientific research and development are excluded.",
            "Sono esclusi i sistemi o modelli di IA, e il loro output, sviluppati e messi in servizio specificamente al solo scopo di ricerca e sviluppo scientifici.",
        ),
        citations=["art:2.6", "rec:25"],
    ),
    Rule(
        id="art2.8-pre-market-rnd",
        kind="scope",
        effect="out_of_scope",
        when=C("scope_exclusion", ("pre_market_research_testing",)),
        title=B("Excluded: research and testing before market", "Escluso: ricerca e prove prima dell'immissione sul mercato"),
        rationale=B(
            "Research, testing and development before placing on the market or putting into service is excluded; testing in real-world conditions is not.",
            "Ricerca, prove e sviluppo prima dell'immissione sul mercato o della messa in servizio sono esclusi; le prove in condizioni reali non lo sono.",
        ),
        citations=["art:2.8", "rec:25"],
    ),
    Rule(
        id="art2.10-personal-use",
        kind="scope",
        effect="out_of_scope",
        when=All(
            [
                C("scope_exclusion", ("personal_non_professional",)),
                C("role", ("deployer",)),
            ]
        ),
        title=B("Excluded: purely personal, non-professional use", "Escluso: uso personale non professionale"),
        rationale=B(
            "Obligations of deployers who are natural persons using AI in a purely personal, non-professional activity do not apply (providers remain covered).",
            "Non si applicano gli obblighi dei deployer persone fisiche che usano l'IA nell'ambito di un'attività personale non professionale (i fornitori restano soggetti).",
        ),
        citations=["art:2.10", "art:3.4"],
    ),
]

# (c) Art. 5 prohibitions ---------------------------------------------------------
NEW_PROHIBITION_NOTE = B(
    " This prohibition, inserted by Regulation (EU) 2026/1744, applies from 2 December 2026.",
    " Questo divieto, introdotto dal regolamento (UE) 2026/1744, si applica dal 2 dicembre 2026.",
)

PROHIBITION_RULES: list[Rule] = [
    Rule(
        id="art5.1.a-manipulation",
        kind="prohibition",
        effect="prohibited",
        when=All([T("manipulation.subliminal_or_deceptive"), T("manipulation.distorts_behaviour_significant_harm")]),
        title=B("Prohibited: subliminal, manipulative or deceptive techniques", "Vietato: tecniche subliminali, manipolative o ingannevoli"),
        rationale=B(
            "Subliminal, purposefully manipulative or deceptive techniques that materially distort behaviour by impairing informed decisions, causing or likely to cause significant harm.",
            "Tecniche subliminali, deliberatamente manipolative o ingannevoli che distorcono materialmente il comportamento pregiudicando decisioni informate e causano, o possono causare, un danno significativo.",
        ),
        citations=["art:5.1.a", "rec:29"],
    ),
    Rule(
        id="art5.1.b-exploiting-vulnerabilities",
        kind="prohibition",
        effect="prohibited",
        when=All([T("manipulation.exploits_vulnerabilities"), T("manipulation.distorts_behaviour_significant_harm")]),
        title=B("Prohibited: exploitation of vulnerabilities", "Vietato: sfruttamento delle vulnerabilità"),
        rationale=B(
            "Exploits vulnerabilities due to age, disability or a specific social or economic situation, materially distorting behaviour and causing or likely to cause significant harm.",
            "Sfrutta vulnerabilità dovute all'età, alla disabilità o a una specifica situazione sociale o economica, distorcendo materialmente il comportamento e causando, o potendo causare, un danno significativo.",
        ),
        citations=["art:5.1.b", "rec:29"],
    ),
    Rule(
        id="art5.1.ba-bb-intimate-csam",
        kind="prohibition",
        effect="prohibited",
        when=T("nudify_or_sexual_abuse_material"),
        title=B(
            "Prohibited: non-consensual intimate material or child sexual abuse material",
            "Vietato: materiale intimo non consensuale o materiale pedopornografico",
        ),
        rationale=B(
            "The intended purpose (or the deployer's use) is generating or manipulating realistic intimate or sexually explicit material of identifiable persons without explicit consent, or child sexual abuse material."
            + NEW_PROHIBITION_NOTE["en"],
            "La finalità prevista (o l'uso da parte del deployer) è generare o manipolare materiale realistico intimo o sessualmente esplicito di persone identificabili senza consenso esplicito, o materiale pedopornografico."
            + NEW_PROHIBITION_NOTE["it"],
        ),
        citations=["art:5.1.ba", "art:5.1.bb", "art:5.1a", "art:5.1b"],
    ),
    Rule(
        id="art5.1a.a.ii-foreseeable-without-safeguards",
        kind="prohibition",
        effect="prohibited",
        when=All(
            [
                T("intimate_content_foreseeable_without_safeguards"),
                C(
                    "role",
                    ("provider", "both"),
                    none_assumption=B(
                        "Role not stated: assumed you place the system on the market (provider), which is the role this prohibition targets.",
                        "Ruolo non indicato: si presume che tu immetta il sistema sul mercato (fornitore), il ruolo cui si rivolge questo divieto.",
                    ),
                ),
            ]
        ),
        title=B(
            "Prohibited for providers: intimate/CSAM generation foreseeable without safeguards",
            "Vietato per i fornitori: generazione prevedibile di materiale intimo o pedopornografico senza misure di salvaguardia",
        ),
        rationale=B(
            "Placing on the market is prohibited where such generation is a reasonably foreseeable and reproducible outcome and the system lacks reasonable and adequate safeguards to reliably prevent it. Deployers are only caught when they use the system for that purpose."
            + NEW_PROHIBITION_NOTE["en"],
            "L'immissione sul mercato è vietata quando tale generazione è un esito ragionevolmente prevedibile e riproducibile e il sistema non dispone di misure di salvaguardia ragionevoli e adeguate per impedirla in modo affidabile. I deployer rientrano nel divieto solo se usano il sistema a tale scopo."
            + NEW_PROHIBITION_NOTE["it"],
        ),
        citations=["art:5.1a", "art:5.1a.a", "art:5.1a.b", "art:5.1.ba", "art:5.1.bb"],
    ),
    Rule(
        id="art5.1.c-social-scoring",
        kind="prohibition",
        effect="prohibited",
        when=T("social_scoring"),
        title=B("Prohibited: social scoring", "Vietato: punteggio sociale"),
        rationale=B(
            "Evaluates or classifies persons over time based on social behaviour or personal characteristics, with the score leading to detrimental treatment in unrelated contexts or disproportionate to the behaviour.",
            "Valuta o classifica persone nel tempo in base al comportamento sociale o a caratteristiche personali, con un punteggio che porta a trattamenti pregiudizievoli in contesti non collegati o sproporzionati.",
        ),
        citations=["art:5.1.c", "rec:31"],
    ),
    Rule(
        id="art5.1.d-predictive-policing",
        kind="prohibition",
        effect="prohibited",
        when=T("law_enforcement.predictive_policing_profiling_only"),
        title=B("Prohibited: crime prediction based solely on profiling", "Vietato: previsione di reati basata unicamente sulla profilazione"),
        rationale=B(
            "Assesses or predicts the risk that a person commits a criminal offence based solely on profiling or personality traits. Not prohibited: support to a human assessment already based on objective, verifiable facts linked to a criminal activity.",
            "Valuta o prevede il rischio che una persona commetta un reato unicamente sulla base della profilazione o dei tratti della personalità. Non è vietato il supporto a una valutazione umana già basata su fatti oggettivi e verificabili connessi a un'attività criminosa.",
        ),
        citations=["art:5.1.d", "rec:42"],
    ),
    Rule(
        id="art5.1.e-facial-scraping",
        kind="prohibition",
        effect="prohibited",
        when=T("law_enforcement.untargeted_facial_scraping"),
        title=B("Prohibited: untargeted scraping of facial images", "Vietato: estrazione non mirata di immagini facciali"),
        rationale=B(
            "Creates or expands facial recognition databases through untargeted scraping of facial images from the internet or CCTV footage.",
            "Crea o amplia banche dati di riconoscimento facciale mediante estrazione non mirata di immagini facciali da internet o da filmati di telecamere a circuito chiuso.",
        ),
        citations=["art:5.1.e", "rec:43"],
    ),
    Rule(
        id="art5.1.f-emotion-workplace-education",
        kind="prohibition",
        effect="prohibited",
        when=All([T("biometric.emotion_recognition"), T("context_workplace_or_education")]),
        exceptions=[
            Exc(
                "biometric.medical_or_safety_purpose",
                ask=True,
                assumption=B(
                    "Assumed the emotion inference is not put in place for medical or safety reasons (the only exception in Art. 5(1)(f)).",
                    "Si presume che il riconoscimento delle emozioni non sia attuato per motivi medici o di sicurezza (unica eccezione dell'art. 5, par. 1, lett. f)).",
                ),
            )
        ],
        title=B("Prohibited: emotion recognition at work or in education", "Vietato: riconoscimento delle emozioni sul luogo di lavoro o nell'istruzione"),
        rationale=B(
            "Infers emotions of natural persons in the workplace or in education institutions; only medical or safety reasons are excepted.",
            "Deduce le emozioni di persone fisiche sul luogo di lavoro o negli istituti di istruzione; sono fatti salvi solo i motivi medici o di sicurezza.",
        ),
        citations=["art:5.1.f", "art:3.39", "rec:44", "rec:18"],
    ),
    Rule(
        id="art5.1.g-biometric-categorisation-sensitive",
        kind="prohibition",
        effect="prohibited",
        when=All([T("biometric.categorisation"), T("biometric.infers_sensitive_attributes")]),
        exceptions=[
            Exc(
                "biometric.dataset_labelling_or_law_enforcement",
                ask=True,
                assumption=B(
                    "Assumed the system does not merely label or filter lawfully acquired biometric datasets, and is not categorisation of biometric data in the area of law enforcement.",
                    "Si presume che il sistema non si limiti a etichettare o filtrare set di dati biometrici acquisiti lecitamente e che non si tratti di categorizzazione di dati biometrici nell'ambito delle attività di contrasto.",
                ),
            )
        ],
        title=B(
            "Prohibited: biometric categorisation inferring sensitive characteristics",
            "Vietato: categorizzazione biometrica che deduce caratteristiche sensibili",
        ),
        rationale=B(
            "Categorises individuals on their biometric data to deduce or infer race, political opinions, trade union membership, religious or philosophical beliefs, sex life or sexual orientation.",
            "Classifica individualmente le persone sulla base dei dati biometrici per dedurne razza, opinioni politiche, appartenenza sindacale, convinzioni religiose o filosofiche, vita sessuale o orientamento sessuale.",
        ),
        citations=["art:5.1.g", "art:3.40", "rec:30"],
    ),
    Rule(
        id="art5.1.h-realtime-rbi-law-enforcement",
        kind="prohibition",
        effect="prohibited",
        when=All(
            [
                T("biometric.remote_identification"),
                T("biometric.real_time"),
                T("biometric.publicly_accessible_space"),
                T("law_enforcement.used_by_or_for_law_enforcement"),
            ]
        ),
        exceptions=[
            Exc(
                "law_enforcement.rbi_strictly_necessary_objective",
                ask=True,
                assumption=B(
                    "Assumed the use is not strictly necessary for one of the three objectives listed in Art. 5(1)(h)(i)-(iii).",
                    "Si presume che l'uso non sia strettamente necessario per uno dei tre obiettivi elencati all'art. 5, par. 1, lett. h), punti i)-iii).",
                ),
            )
        ],
        title=B(
            "Prohibited: real-time remote biometric identification in public spaces for law enforcement",
            "Vietato: identificazione biometrica remota «in tempo reale» in spazi accessibili al pubblico a fini di attività di contrasto",
        ),
        rationale=B(
            "Real-time remote biometric identification in publicly accessible spaces for law enforcement, outside the narrowly listed objectives (victims and missing persons, imminent threats or terrorism, suspects of Annex II offences).",
            "Identificazione biometrica remota in tempo reale in spazi accessibili al pubblico a fini di contrasto, al di fuori degli obiettivi tassativamente elencati (vittime e persone scomparse, minacce imminenti o terrorismo, sospettati di reati dell'allegato II).",
        ),
        citations=["art:5.1.h", "art:3.42", "art:3.44", "rec:32", "rec:33"],
    ),
]

# (d) Art. 6(1) Annex I ---------------------------------------------------------
_ANNEX_I_PRODUCTS = tuple(k for k in ANNEX_I)


def _annex_i_cites(f: FactSheet) -> list[str]:
    prod = f.annex_i_product
    if not prod or prod not in ANNEX_I:
        return []
    section, pts, _, _, arts = ANNEX_I[prod]
    out = list(pts)
    if section == "B":
        out += ["art:2.2"] + arts
    return out


def _annex_i_rationale(f: FactSheet) -> Bi:
    prod = f.annex_i_product
    sec, _, en, it, _ = ANNEX_I.get(prod, ("A", [], "Annex I product", "prodotto dell'allegato I", []))
    base = B(
        f"Safety component of (or itself) a product covered by Annex I — {en} — that requires third-party conformity assessment for health and safety reasons.",
        f"Componente di sicurezza di un prodotto (o prodotto esso stesso) disciplinato dall'allegato I — {it} — soggetto a valutazione della conformità da parte di terzi per motivi di salute e sicurezza.",
    )
    if sec == "B":
        base["en"] += (
            " Section B legislation: under Art. 2(2) only Art. 6(1), Art. 60a and Arts 102–112 of the AI Act apply; the AI requirements reach you through the sectoral legislation."
        )
        base["it"] += (
            " Normativa della sezione B: ai sensi dell'art. 2, par. 2, si applicano solo l'art. 6, par. 1, l'art. 60 bis e gli articoli da 102 a 112; i requisiti per l'IA si applicano tramite la normativa settoriale."
        )
    return base


ANNEX_I_RULE = Rule(
    id="art6.1-annex-i-safety-component",
    kind="high_risk_annex_i",
    effect="high_risk_i",
    when=All(
        [
            C("annex_i_product", _ANNEX_I_PRODUCTS),
            T("safety_component"),
            T("annex_i_third_party_assessment"),
        ]
    ),
    title=B("High-risk: safety component of an Annex I product", "Alto rischio: componente di sicurezza di un prodotto dell'allegato I"),
    rationale=B("", ""),
    rationale_fn=_annex_i_rationale,
    citations=["art:6.1", "art:6.1.a", "art:6.1.b", "art:3.14", "art:6.1a", "rec:47"],
    cite_fn=_annex_i_cites,
    extra_citations=sorted({c for k in ANNEX_I for c in (ANNEX_I[k][1] + ANNEX_I[k][4])} | {"art:2.2"}),
)

ANNEX_I_NOTES: list[Rule] = [
    Rule(
        id="art6.1c-no-third-party-assessment",
        kind="note",
        effect="note",
        when=All([C("annex_i_product", _ANNEX_I_PRODUCTS), T("safety_component"), F("annex_i_third_party_assessment")]),
        title=B("Annex I product without third-party assessment", "Prodotto dell'allegato I senza valutazione di terzi"),
        rationale=B(
            "Not high-risk under Art. 6(1): the product is not required to undergo third-party conformity assessment for health and safety reasons.",
            "Non è ad alto rischio ai sensi dell'art. 6, par. 1: il prodotto non è soggetto a valutazione della conformità da parte di terzi per motivi di salute e sicurezza.",
        ),
        citations=["art:6.1.b", "art:6.1c"],
    ),
    Rule(
        id="art6.1a-not-safety-component",
        kind="note",
        effect="note",
        when=All([C("annex_i_product", _ANNEX_I_PRODUCTS), F("safety_component")]),
        title=B("AI is not a safety component", "L'IA non è un componente di sicurezza"),
        rationale=B(
            "AI used solely for non-safety aspects (user assistance, performance optimisation, efficiency, automation, convenience, quality control) is not a safety component — unless its failure would endanger health and safety.",
            "L'IA usata solo per aspetti non legati alla sicurezza (assistenza all'utente, ottimizzazione, efficienza, automazione, comodità, controllo qualità) non è un componente di sicurezza, salvo che il suo guasto metta in pericolo salute e sicurezza.",
        ),
        citations=["art:3.14", "art:6.1a", "art:6.1b"],
    ),
]


# (e) Art. 6(2) Annex III --------------------------------------------------------
def _annex_iii_rule(area: str) -> Rule:
    pid, en, it, recs = ANNEX_III[area]
    base: Node = C("annex_iii_area", (area,))
    exceptions: list[Exc] = []
    if area == "1a_remote_biometric_identification":
        base = Any_([base, T("biometric.remote_identification")])
        exceptions = [Exc("biometric.verification_only", ask=False)]
    elif area == "1b_biometric_categorisation_sensitive":
        base = Any_([base, All([T("biometric.categorisation"), T("biometric.infers_sensitive_attributes")])])
    elif area == "1c_emotion_recognition":
        base = Any_([base, T("biometric.emotion_recognition")])
    elif area == "5b_creditworthiness":
        exceptions = [Exc("financial_fraud_detection", ask=False)]
    return Rule(
        id=f"annex-iii-{area.split('_')[0]}",
        kind="high_risk_annex_iii",
        effect="high_risk_iii",
        when=base,
        exceptions=exceptions,
        title=B(f"High-risk: Annex III — {en}", f"Alto rischio: allegato III — {it}"),
        rationale=B(
            f"The intended purpose falls under Annex III ({en}); Annex III systems are high-risk under Art. 6(2) unless the Art. 6(3) derogation applies.",
            f"La finalità prevista rientra nell'allegato III ({it}); i sistemi dell'allegato III sono ad alto rischio ai sensi dell'art. 6, par. 2, salvo applicazione della deroga dell'art. 6, par. 3.",
        ),
        citations=["art:6.2", pid, "annex:III", *recs],
    )


ANNEX_III_RULES: list[Rule] = [_annex_iii_rule(a) for a in ANNEX_III]

_ART63_ANY = Any_(
    [
        T("art63.narrow_procedural_task"),
        T("art63.improves_prior_human_activity"),
        T("art63.detects_patterns_without_replacing_assessment"),
        T("art63.preparatory_task_only"),
    ]
)


def _derog_cites(f: FactSheet) -> list[str]:
    m = {
        "art63.narrow_procedural_task": "art:6.3.a",
        "art63.improves_prior_human_activity": "art:6.3.b",
        "art63.detects_patterns_without_replacing_assessment": "art:6.3.c",
        "art63.preparatory_task_only": "art:6.3.d",
    }
    return [c for p, c in m.items() if f.get_path(p) is True]


DEROGATION_RULE = Rule(
    id="art6.3-derogation",
    kind="derogation_6_3",
    effect="derogation",
    when=All(
        [
            _ART63_ANY,
            F("art63.profiling_of_natural_persons"),
            C("decision_impact", ("supports_human_decision", "no_decision_about_persons")),
        ]
    ),
    title=B("Art. 6(3) derogation: not high-risk", "Deroga dell'art. 6, par. 3: non ad alto rischio"),
    rationale=B(
        "The Annex III system meets a condition of Art. 6(3) (narrow procedural task, improving a completed human activity, detecting patterns without replacing human assessment, or preparatory task), does not profile natural persons and does not materially influence the decision. The provider must document this assessment and register the system.",
        "Il sistema dell'allegato III soddisfa una condizione dell'art. 6, par. 3 (compito procedurale limitato, miglioramento di un'attività umana completata, rilevamento di schemi senza sostituire la valutazione umana o compito preparatorio), non effettua profilazione e non influenza materialmente la decisione. Il fornitore deve documentare la valutazione e registrare il sistema.",
    ),
    citations=["art:6.3", "art:6.4", "art:49.2", "rec:53"],
    cite_fn=_derog_cites,
    extra_citations=["art:6.3.a", "art:6.3.b", "art:6.3.c", "art:6.3.d"],
)

DEROGATION_NOTES: list[Rule] = [
    Rule(
        id="art6.3-profiling-always-high-risk",
        kind="derogation_6_3",
        effect="note",
        when=T("art63.profiling_of_natural_persons"),
        title=B("Profiling: always high-risk", "Profilazione: sempre ad alto rischio"),
        rationale=B(
            "The system performs profiling of natural persons, so it is always high-risk and the Art. 6(3) derogation cannot apply.",
            "Il sistema effettua la profilazione di persone fisiche: è sempre ad alto rischio e la deroga dell'art. 6, par. 3, non può applicarsi.",
        ),
        citations=["art:6.3", "art:3.52"],
    ),
    Rule(
        id="art6.3-material-influence",
        kind="derogation_6_3",
        effect="note",
        when=All([_ART63_ANY, C("decision_impact", ("determines_outcome", "materially_influences"))]),
        title=B("Derogation not applied: output shapes the decision", "Deroga non applicata: l'output incide sulla decisione"),
        rationale=B(
            "A condition of Art. 6(3) is described, but the output determines or materially influences the decision. Art. 6(3) requires no significant risk, 'including by not materially influencing the outcome of decision making'; the engine applies the conservative reading and keeps the system high-risk.",
            "È descritta una condizione dell'art. 6, par. 3, ma l'output determina o influenza materialmente la decisione. L'art. 6, par. 3, richiede l'assenza di un rischio significativo, «anche nel senso di non influenzare materialmente il risultato del processo decisionale»; il motore adotta la lettura prudenziale e mantiene l'alto rischio.",
        ),
        citations=["art:6.3", "rec:53"],
    ),
]

RBI_EXCEPTION_NOTE = Rule(
    id="art5.2-rbi-authorised-objective",
    kind="note",
    effect="note",
    when=All(
        [
            T("biometric.remote_identification"),
            T("biometric.real_time"),
            T("biometric.publicly_accessible_space"),
            T("law_enforcement.used_by_or_for_law_enforcement"),
            T("law_enforcement.rbi_strictly_necessary_objective"),
        ]
    ),
    title=B("Real-time RBI only under strict conditions", "RBI in tempo reale solo a condizioni rigorose"),
    rationale=B(
        "Use for a listed objective is not prohibited but requires national law, prior judicial or independent authorisation, a fundamental rights impact assessment and registration; the system is high-risk (Annex III, point 1(a)).",
        "L'uso per un obiettivo elencato non è vietato ma richiede una base nel diritto nazionale, un'autorizzazione preventiva giudiziaria o indipendente, una valutazione d'impatto sui diritti fondamentali e la registrazione; il sistema è ad alto rischio (allegato III, punto 1, lett. a)).",
    ),
    citations=["art:5.2", "art:5.3", "art:5.5", "art:27", "art:49"],
)

# (f) Art. 50 transparency overlays ---------------------------------------------
TRANSPARENCY_RULES: list[Rule] = [
    Rule(
        id="art50.1-interaction-disclosure",
        kind="transparency",
        effect="overlay",
        overlay=("transparency_art50", ["art:50.1"]),
        when=T("transparency.interacts_with_natural_persons"),
        exceptions=[
            Exc(
                "transparency.obvious_to_users_it_is_ai",
                ask=True,
                assumption=B(
                    "Assumed it is not obvious to a reasonably well-informed person that they are interacting with an AI system.",
                    "Si presume che non sia evidente, per una persona ragionevolmente informata, di interagire con un sistema di IA.",
                ),
            ),
            LE_EXC,
        ],
        title=B("Transparency: tell people they are interacting with AI", "Trasparenza: informare le persone che interagiscono con un'IA"),
        rationale=B(
            "The system interacts directly with natural persons; they must be informed they are interacting with AI unless this is obvious from the context (exception for systems authorised by law to fight crime).",
            "Il sistema interagisce direttamente con persone fisiche, che devono essere informate di interagire con un'IA salvo che ciò sia evidente dal contesto (eccezione per i sistemi autorizzati dalla legge a contrastare reati).",
        ),
        citations=["art:50.1", "art:50.5", "rec:132"],
    ),
    Rule(
        id="art50.2-synthetic-content-marking",
        kind="transparency",
        effect="overlay",
        overlay=("transparency_art50", ["art:50.2"]),
        when=T("transparency.generates_synthetic_content"),
        exceptions=[Exc("transparency.assistive_editing_only", ask=False), LE_EXC],
        title=B("Transparency: mark synthetic content as AI-generated", "Trasparenza: marcare i contenuti sintetici come generati dall'IA"),
        rationale=B(
            "The system generates synthetic audio, image, video or text; outputs must be marked in a machine-readable, detectable format (not required for assistive standard editing that does not substantially alter the input).",
            "Il sistema genera audio, immagini, video o testi sintetici; gli output devono essere marcati in un formato leggibile meccanicamente e rilevabile (non richiesto per funzioni di editing standard che non alterano in modo sostanziale l'input).",
        ),
        citations=["art:50.2", "rec:133", "art:111.4"],
    ),
    Rule(
        id="art50.3-emotion-biometric-disclosure",
        kind="transparency",
        effect="overlay",
        overlay=("transparency_art50", ["art:50.3"]),
        when=Any_([T("biometric.emotion_recognition"), T("biometric.categorisation")]),
        exceptions=[LE_EXC],
        title=B(
            "Transparency: inform people exposed to emotion recognition or biometric categorisation",
            "Trasparenza: informare le persone esposte a riconoscimento delle emozioni o categorizzazione biometrica",
        ),
        rationale=B(
            "Deployers of an emotion recognition or biometric categorisation system must inform exposed persons and process personal data lawfully.",
            "I deployer di un sistema di riconoscimento delle emozioni o di categorizzazione biometrica devono informare le persone esposte e trattare i dati personali in modo lecito.",
        ),
        citations=["art:50.3", "art:3.39", "art:3.40"],
    ),
    Rule(
        id="art50.4-deep-fake-disclosure",
        kind="transparency",
        effect="overlay",
        overlay=("transparency_art50", ["art:50.4"]),
        when=T("transparency.deepfake"),
        exceptions=[LE_EXC],
        title=B("Transparency: disclose deep fakes", "Trasparenza: dichiarare i deep fake"),
        rationale=B(
            "Deployers generating or manipulating image, audio or video deep fakes must disclose that the content is artificially generated or manipulated (for evidently artistic, satirical or fictional works, an appropriate disclosure that does not hamper the work).",
            "I deployer che generano o manipolano deep fake di immagini, audio o video devono dichiarare che il contenuto è generato o manipolato artificialmente (per opere palesemente artistiche, satiriche o di finzione, con modalità che non ostacolino la fruizione dell'opera).",
        ),
        citations=["art:50.4", "art:3.60", "rec:134"],
    ),
    Rule(
        id="art50.4-public-interest-text",
        kind="transparency",
        effect="overlay",
        overlay=("transparency_art50", ["art:50.4"]),
        when=T("transparency.public_interest_text"),
        exceptions=[
            Exc(
                "transparency.human_editorial_control",
                ask=True,
                assumption=B(
                    "Assumed the AI-generated text is not subject to human review or editorial control with a person holding editorial responsibility.",
                    "Si presume che il testo generato dall'IA non sia sottoposto a revisione umana o a controllo editoriale con una persona che ne detiene la responsabilità editoriale.",
                ),
            ),
            LE_EXC,
        ],
        title=B("Transparency: disclose AI-generated public-interest text", "Trasparenza: dichiarare i testi di interesse pubblico generati dall'IA"),
        rationale=B(
            "AI-generated text published to inform the public on matters of public interest must be disclosed as such, unless it underwent human review or editorial control under someone's editorial responsibility.",
            "I testi generati dall'IA pubblicati per informare il pubblico su questioni di interesse pubblico devono essere dichiarati, salvo revisione umana o controllo editoriale sotto la responsabilità editoriale di una persona.",
        ),
        citations=["art:50.4", "rec:134"],
    ),
]

# (g) GPAI overlay ----------------------------------------------------------------
GPAI_RULES: list[Rule] = [
    Rule(
        id="art53-gpai-provider",
        kind="gpai",
        effect="overlay",
        overlay=("gpai", ["art:53", "art:54"]),
        when=All([T("gpai.is_gpai_model"), T("gpai.provider_of_model")]),
        title=B("Provider of a general-purpose AI model", "Fornitore di un modello di IA per finalità generali"),
        rationale=B(
            "You develop and place a general-purpose AI model on the market: technical documentation, information for downstream providers, copyright policy and training-content summary apply (open-source models with public weights are exempt from documentation duties unless they carry systemic risk).",
            "Sviluppi e immetti sul mercato un modello di IA per finalità generali: si applicano documentazione tecnica, informazioni per i fornitori a valle, politica sul diritto d'autore e sintesi dei contenuti di addestramento (i modelli open source con pesi pubblici sono esentati dagli obblighi documentali salvo rischio sistemico).",
        ),
        citations=["art:53", "art:3.63", "art:3.3", "rec:97", "rec:101"],
    ),
    Rule(
        id="art55-gpai-systemic-risk",
        kind="gpai",
        effect="overlay",
        overlay=("gpai", ["art:55"]),
        when=All([T("gpai.is_gpai_model"), T("gpai.provider_of_model"), T("gpai.systemic_risk")]),
        title=B("General-purpose AI model with systemic risk", "Modello di IA per finalità generali con rischio sistemico"),
        rationale=B(
            "The model has high-impact capabilities (presumed above 10^25 training FLOPs) or is designated by the Commission: model evaluation, adversarial testing, systemic-risk mitigation, incident reporting and cybersecurity apply.",
            "Il modello ha capacità di impatto elevato (presunte oltre 10^25 FLOP di addestramento) o è designato dalla Commissione: si applicano valutazione del modello, test contraddittori, attenuazione dei rischi sistemici, segnalazione degli incidenti e cibersicurezza.",
        ),
        citations=["art:55", "art:51", "art:52", "rec:110", "rec:111"],
    ),
    Rule(
        id="gpai-integrator-substantial-modification",
        kind="gpai",
        effect="overlay",
        overlay=("gpai", ["art:53"]),
        when=All([T("gpai.integrates_third_party_gpai"), T("gpai.substantially_modifies_model")]),
        title=B("Modifying a third-party GPAI model", "Modifica di un modello di IA per finalità generali di terzi"),
        rationale=B(
            "You substantially modify (e.g. fine-tune) a third-party general-purpose model; the engine conservatively treats you as provider of the modified model for the modification. The Act does not define the threshold; check the Commission guidance on GPAI obligations.",
            "Modifichi in modo sostanziale (ad es. con fine-tuning) un modello per finalità generali di terzi; il motore ti considera prudenzialmente fornitore del modello modificato per la parte modificata. Il regolamento non fissa la soglia; verifica gli orientamenti della Commissione sui modelli GPAI.",
        ),
        citations=["art:53", "art:3.3", "art:3.63", "rec:109"],
    ),
]

NOTE_RULES: list[Rule] = [
    Rule(
        id="gpai-integrator-not-provider",
        kind="note",
        effect="note",
        when=All([T("gpai.integrates_third_party_gpai"), F("gpai.substantially_modifies_model")]),
        title=B("Integrating a third-party GPAI model", "Integrazione di un modello GPAI di terzi"),
        rationale=B(
            "Building a system on someone else's general-purpose model does not make you a GPAI model provider; you are a downstream provider entitled to the model provider's documentation. Your system is classified on its own intended purpose (and Art. 25 applies if it becomes high-risk).",
            "Costruire un sistema sul modello per finalità generali di un terzo non ti rende fornitore del modello; sei un fornitore a valle con diritto alla documentazione del fornitore del modello. Il tuo sistema è classificato in base alla propria finalità prevista (e si applica l'art. 25 se diventa ad alto rischio).",
        ),
        citations=["art:3.68", "art:53.1.b", "art:25.1", "rec:85"],
    ),
    Rule(
        id="art50.4-artistic-limited-disclosure",
        kind="note",
        effect="note",
        when=All([T("transparency.deepfake"), T("transparency.artistic_creative_satirical")]),
        title=B("Artistic or satirical deep fake", "Deep fake artistico o satirico"),
        rationale=B(
            "For evidently artistic, creative, satirical or fictional works, the duty is limited to disclosing the existence of generated content in a way that does not hamper the work.",
            "Per opere palesemente artistiche, creative, satiriche o di finzione l'obbligo si limita a rivelare l'esistenza di contenuti generati con modalità che non ostacolino la fruizione dell'opera.",
        ),
        citations=["art:50.4"],
    ),
    RBI_EXCEPTION_NOTE,
]

ALL_RULES: list[Rule] = (
    SCOPE_RULES
    + PROHIBITION_RULES
    + [ANNEX_I_RULE]
    + ANNEX_I_NOTES
    + ANNEX_III_RULES
    + [DEROGATION_RULE]
    + DEROGATION_NOTES
    + TRANSPARENCY_RULES
    + GPAI_RULES
    + NOTE_RULES
)

MINIMAL_CITES = ["art:95", "art:4.1", "rec:165"]
OPEN_SOURCE_CITES = ["art:2.12"]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
@dataclass
class Eval:
    tier: str
    overlays: dict[str, list[str]]
    derogation: str  # "applies" | "denied" | "n/a"
    findings: list[Finding]
    assumptions: list[tuple[str, Bi]]
    open_paths: list[str]  # exception paths assumed conservatively
    evals: dict[str, RuleEval]
    annex_i_section: str | None = None
    hr_basis: str | None = None  # "annex_i" | "annex_iii"

    def outcome(self) -> tuple:
        ov = tuple(sorted((k, tuple(sorted(v))) for k, v in self.overlays.items()))
        return (self.tier, ov, self.derogation)


def _finding(re: RuleEval, f: FactSheet, decisive: bool = False) -> Finding:
    r = re.rule
    rat = r.rationale_fn(f) if r.rationale_fn else dict(r.rationale)
    return Finding(
        rule_id=r.id,
        kind=r.kind,  # type: ignore[arg-type]
        title=dict(r.title),
        rationale=rat,
        citations=r.cites(f),
        facts_used=sorted(r.paths()),
        decisive=decisive,
    )


def _add_assumptions(target: list[tuple[str, Bi]], items: list[tuple[str, Bi]]) -> None:
    for p, a in items:
        if all(a != b for _, b in target):
            target.append((p, a))


def evaluate(f: FactSheet) -> Eval:
    """Pure evaluation of the rule set (no sensitivity analysis)."""
    evals = {r.id: eval_rule(r, f) for r in ALL_RULES}
    findings: list[Finding] = []
    assumptions: list[tuple[str, Bi]] = []
    open_paths: list[str] = []

    def fired(rules: list[Rule]) -> list[RuleEval]:
        return [evals[r.id] for r in rules if evals[r.id].status == "fire"]

    def absorb(res: list[RuleEval]) -> None:
        for e in res:
            _add_assumptions(assumptions, e.assumptions)
            for p in e.open_exceptions:
                if p not in open_paths:
                    open_paths.append(p)

    # (a)/(b) scope -------------------------------------------------------------
    scope = fired(SCOPE_RULES)
    if scope:
        first = scope[0]
        absorb([first])
        findings.append(_finding(first, f, decisive=True))
        return Eval("out_of_scope", {}, "n/a", findings, assumptions, open_paths, evals)

    overlays: dict[str, list[str]] = {}

    # (c) prohibitions ------------------------------------------------------------
    prohib = fired(PROHIBITION_RULES)
    absorb(prohib)
    for e in prohib:
        findings.append(_finding(e, f, decisive=True))

    # (d) Annex I -----------------------------------------------------------------
    annex_i = evals[ANNEX_I_RULE.id]
    section = None
    if annex_i.status == "fire":
        section = ANNEX_I.get(f.annex_i_product or "", ("A",))[0]
        findings.append(_finding(annex_i, f, decisive=not prohib))
    for e in fired(ANNEX_I_NOTES):
        findings.append(_finding(e, f))

    # (e) Annex III + Art. 6(3) ----------------------------------------------------
    a3 = fired(ANNEX_III_RULES)
    absorb(a3)
    derogation = "n/a"
    if a3:
        d = evals[DEROGATION_RULE.id]
        derogation = "applies" if d.status == "fire" else "denied"
        hr3_decisive = not prohib and annex_i.status != "fire" and derogation == "denied"
        for e in a3:
            findings.append(_finding(e, f, decisive=hr3_decisive))
        if derogation == "applies":
            findings.append(_finding(d, f, decisive=not prohib and annex_i.status != "fire"))
        for e in fired(DEROGATION_NOTES):
            findings.append(_finding(e, f))
        if derogation == "denied" and d.status == "pending":
            _add_assumptions(
                assumptions,
                [
                    (
                        "art63",
                        B(
                            "The Art. 6(3) derogation is not applied because the facts needed to establish it are unknown; the system is treated as high-risk.",
                            "La deroga dell'art. 6, par. 3, non è applicata perché mancano i fatti necessari per accertarla; il sistema è trattato come ad alto rischio.",
                        ),
                    )
                ],
            )

    hr_basis = None
    if annex_i.status == "fire":
        hr_basis = "annex_i"
    elif a3 and derogation == "denied":
        hr_basis = "annex_iii"

    # (f) transparency ------------------------------------------------------------
    # Art. 50 is addressed to providers/deployers of AI *systems* (Art. 3(1)); a bare general-purpose
    # AI model offered on its own is not a system (Art. 3(63), recital 97), so no Art. 50 overlay.
    bare_model = f.is_ai_system is False and f.gpai.is_gpai_model is True
    tr = [] if bare_model else fired(TRANSPARENCY_RULES)
    if hr_basis == "annex_i" and section == "B" and not a3:
        if tr:
            _add_assumptions(
                assumptions,
                [
                    (
                        "annex_i_product",
                        B(
                            "Art. 2(2) limits the AI Act provisions applicable to Annex I Section B high-risk systems; Art. 50 duties are therefore not listed. Check the sectoral legislation.",
                            "L'art. 2, par. 2, limita le disposizioni applicabili ai sistemi ad alto rischio della sezione B dell'allegato I; gli obblighi dell'art. 50 non sono quindi elencati. Verifica la normativa settoriale.",
                        ),
                    )
                ],
            )
        tr = []
    absorb(tr)
    for e in tr:
        key, provs = e.rule.overlay  # type: ignore[misc]
        lst = overlays.setdefault(key, [])
        for p in provs:
            if p not in lst:
                lst.append(p)
        findings.append(_finding(e, f))

    # (g) GPAI -------------------------------------------------------------------
    gp = fired(GPAI_RULES)
    for e in gp:
        key, provs = e.rule.overlay  # type: ignore[misc]
        lst = overlays.setdefault(key, [])
        for p in provs:
            if p not in lst:
                lst.append(p)
        findings.append(_finding(e, f))

    for e in fired(NOTE_RULES):
        findings.append(_finding(e, f))

    # tier --------------------------------------------------------------------------
    if prohib:
        tier = "prohibited"
    elif hr_basis:
        tier = "high_risk"
    elif overlays.get("transparency_art50"):
        tier = "limited_risk"
        for fd in findings:
            if fd.kind == "transparency":
                fd.decisive = True
    else:
        tier = "minimal_risk"

    if tier == "minimal_risk" and f.free_open_source_licence is True and f.is_ai_system is not False:
        findings.append(
            Finding(
                rule_id="art2.12-open-source",
                kind="scope",
                title=B("Excluded: free and open-source AI system", "Escluso: sistema di IA con licenza libera e open source"),
                rationale=B(
                    "Released under a free and open-source licence and neither prohibited, high-risk nor subject to Art. 50: the Act does not apply to the system (GPAI model duties, if any, are unaffected).",
                    "Rilasciato con licenza libera e open source e non vietato, non ad alto rischio né soggetto all'art. 50: il regolamento non si applica al sistema (restano gli eventuali obblighi per i modelli GPAI).",
                ),
                citations=list(OPEN_SOURCE_CITES),
                facts_used=["free_open_source_licence"],
                decisive=True,
            )
        )
        tier = "out_of_scope"
    elif tier == "minimal_risk":
        findings.append(
            Finding(
                rule_id="minimal-risk",
                kind="note",
                title=B("Minimal risk", "Rischio minimo"),
                rationale=B(
                    "No prohibition, high-risk category or transparency duty applies. AI literacy measures (Art. 4) remain required; voluntary codes of conduct are encouraged.",
                    "Non si applicano divieti, categorie ad alto rischio né obblighi di trasparenza. Restano obbligatorie le misure di alfabetizzazione in materia di IA (art. 4); sono incoraggiati codici di condotta volontari.",
                ),
                citations=list(MINIMAL_CITES),
                facts_used=[],
                decisive=True,
            )
        )

    return Eval(tier, overlays, derogation, findings, assumptions, open_paths, evals, section, hr_basis)


# ---------------------------------------------------------------------------
# Sensitivity helpers (shared with questions.py)
# ---------------------------------------------------------------------------
def rules_reading(path: str) -> list[Rule]:
    return [r for r in ALL_RULES if path in r.paths()]


def probe(f: FactSheet, path: str, value: Any) -> Eval:
    """Evaluate with ``path=value``; rules that ``path`` keeps alive are optimistically
    completed (their other unknown positive conditions set to satisfying values) so
    that answers whose effect depends on a further unknown are still detected."""
    g = f.with_answer(path, value)
    assign: dict[str, Any] = {}
    for r in rules_reading(path):
        e = eval_rule(r, g)
        if e.status == "pending":
            # only complete when the probed leaf itself is satisfied
            # guard leaves (unknown-tolerant, e.g. role) never trigger completion
            leaf_ok = any(
                lf.path == path and lf.status(g) == "sat" and not (lf.none_ok or lf.none_assumption)
                for lf in r.when.leaves()
            )
            if leaf_ok:
                r.when.complete(g, assign)
    for p, v in assign.items():
        if p != path and g.get_path(p) is None:
            g = g.with_answer(p, v)
    return evaluate(g)


def domain(path: str) -> list[Any]:
    """Possible values of a fact path (bool -> [True, False]; Literal -> all values)."""
    import typing

    model: Any = FactSheet
    parts = path.split(".")
    for part in parts[:-1]:
        model = model.model_fields[part].annotation
    ann = model.model_fields[parts[-1]].annotation
    args = [a for a in typing.get_args(ann) if a is not type(None)]
    if not args:
        args = [ann]
    out: list[Any] = []
    for a in args:
        if a is bool:
            out += [True, False]
        elif typing.get_origin(a) is Literal:
            out += list(typing.get_args(a))
    return out


@dataclass
class Sensitivity:
    path: str
    impact: float
    tier_impact: float
    changes: int
    total: int


def sensitivity(f: FactSheet, base: Eval, path: str) -> Sensitivity:
    vals = domain(path)
    b = base.outcome()
    changed = tier_changed = 0
    for v in vals:
        o = probe(f, path, v).outcome()
        if o != b:
            changed += 1
            if o[0] != b[0]:
                tier_changed += 1
    n = max(len(vals), 1)
    return Sensitivity(path, changed / n, tier_changed / n, changed, len(vals))


# ---------------------------------------------------------------------------
# classify
# ---------------------------------------------------------------------------
_ROLE_ASSUMPTION = B(
    "Your role (provider or deployer) is not stated; obligations are listed for both until it is confirmed.",
    "Il tuo ruolo (fornitore o deployer) non è indicato; gli obblighi sono elencati per entrambi finché non viene confermato.",
)
_EU_ASSUMPTION = B(
    "Assumed the system is placed on the EU market, used in the EU or its output is used in the EU (Art. 2(1)).",
    "Si presume che il sistema sia immesso sul mercato dell'UE, usato nell'UE o che il suo output sia utilizzato nell'UE (art. 2, par. 1).",
)
_EXCL_ASSUMPTION = B(
    "Assumed none of the Art. 2 exclusions (military, research-only, personal use, pre-market testing) applies.",
    "Si presume che non si applichi nessuna delle esclusioni dell'art. 2 (finalità militari, sola ricerca, uso personale, prove prima dell'immissione sul mercato).",
)


def _applies_from(e: Eval, today: date | None) -> list[Milestone]:
    ids: list[str] = []
    if e.tier == "out_of_scope":
        return []
    ids.append("chapters-i-ii")
    if e.tier == "prohibited":
        new = any(
            fd.rule_id in ("art5.1.ba-bb-intimate-csam", "art5.1a.a.ii-foreseeable-without-safeguards") for fd in e.findings
        )
        if new:
            ids.append("new-prohibitions-and-marking-legacy")
    if e.hr_basis == "annex_iii":
        ids.append("high-risk-annex-iii")
    if e.hr_basis == "annex_i":
        ids.append("high-risk-annex-i")
    if e.overlays.get("transparency_art50"):
        ids.append("general-application")
        if "art:50.2" in e.overlays["transparency_art50"] and "new-prohibitions-and-marking-legacy" not in ids:
            ids.append("new-prohibitions-and-marking-legacy")
    if e.overlays.get("gpai"):
        ids += ["gpai-governance-penalties", "gpai-legacy"]
    if e.tier == "minimal_risk":
        ids.append("general-application")
    seen: list[str] = []
    for i in ids:
        if i not in seen:
            seen.append(i)
    ms = tl.milestones_by_id(seen, today)
    return sorted(ms, key=lambda m: m.date)


def classify(facts: FactSheet, today: date | None = None) -> Classification:
    from .questions import probe_paths  # lazy: questions imports this module

    e = evaluate(facts)
    base_outcome = e.outcome()

    unresolved: list[tuple[float, float, str]] = []
    for p in probe_paths(facts):
        s = sensitivity(facts, e, p)
        if s.changes:
            unresolved.append((s.tier_impact, s.impact, p))
    unresolved.sort(key=lambda t: (-t[0], -t[1]))
    tier_dependent = any(t[0] > 0 for t in unresolved)

    paths = [p for _, _, p in unresolved]
    if facts.role is None and e.tier not in ("out_of_scope", "minimal_risk") and "role" not in paths:
        paths.append("role")

    if tier_dependent:
        confidence = "low"
    elif unresolved or e.open_paths:
        confidence = "medium"
    else:
        confidence = "high"
    _ = base_outcome

    assumptions = [a for _, a in e.assumptions]
    if e.tier != "out_of_scope":
        if facts.in_eu_scope is None:
            assumptions.append(_EU_ASSUMPTION)
        if facts.scope_exclusion is None:
            assumptions.append(_EXCL_ASSUMPTION)
        if facts.role is None and e.tier != "minimal_risk":
            assumptions.append(_ROLE_ASSUMPTION)

    return Classification(
        tier=e.tier,  # type: ignore[arg-type]
        confidence=confidence,  # type: ignore[arg-type]
        findings=e.findings,
        overlays=e.overlays,
        role=facts.role or "unknown",
        applies_from=_applies_from(e, today),
        unresolved=paths,
        assumptions=assumptions,
    )


def rule_citation_ids() -> set[str]:
    out: set[str] = set()
    for r in ALL_RULES:
        out |= r.all_citations()
    out |= set(MINIMAL_CITES) | set(OPEN_SOURCE_CITES)
    return out
