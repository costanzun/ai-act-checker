"""Clarifying questions chosen by sensitivity analysis.

For every unknown fact path in ``REGISTRY`` whose gate is open, the engine
re-runs the rules for each possible value of that fact and measures how many
values change the outcome (tier, overlays, or the Art. 6(3) derogation). Only
facts that can change the outcome are asked, highest impact first, max 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .facts import FactSheet
from .models import Question

Bi = dict[str, str]


def B(en: str, it: str) -> Bi:
    return {"en": en, "it": it}


YES_NO = [
    {"value": True, "label": B("Yes", "Sì")},
    {"value": False, "label": B("No", "No")},
]


@dataclass
class Entry:
    path: str
    text: Bi
    why: Bi
    options: list[dict[str, Any]] = field(default_factory=lambda: list(YES_NO))
    after: list[str] = field(default_factory=list)  # all must be set and truthy
    after_any: list[str] = field(default_factory=list)  # at least one truthy
    when_values: dict[str, tuple[Any, ...]] = field(default_factory=dict)  # path -> allowed current values

    @property
    def qtype(self) -> str:
        vals = [o["value"] for o in self.options]
        return "boolean" if vals == [True, False] else "single"


def _opts(pairs: list[tuple[Any, str, str]]) -> list[dict[str, Any]]:
    return [{"value": v, "label": B(en, it)} for v, en, it in pairs]


ROLE_ENTRY = Entry(
    path="role",
    text=B(
        "Are you building this system and putting it on the market under your name, or using a system someone else supplies?",
        "State sviluppando questo sistema e immettendolo sul mercato con il vostro nome, oppure utilizzate un sistema fornito da altri?",
    ),
    why=B(
        "Providers and deployers have different obligations under the AI Act.",
        "Fornitori e deployer hanno obblighi diversi ai sensi del regolamento sull'IA.",
    ),
    options=_opts(
        [
            ("provider", "We develop it and supply it under our name (provider)", "Lo sviluppiamo e lo forniamo con il nostro nome (fornitore)"),
            ("deployer", "We use a system supplied by someone else (deployer)", "Usiamo un sistema fornito da terzi (deployer)"),
            ("both", "Both: we build it and use it ourselves", "Entrambi: lo sviluppiamo e lo usiamo noi stessi"),
            ("other", "We import or distribute it only", "Lo importiamo o distribuiamo soltanto"),
        ]
    ),
)

REGISTRY: list[Entry] = [
    Entry(
        "is_ai_system",
        B(
            "Does the system learn from data or infer its outputs (predictions, content, recommendations), or does it only apply fixed rules written by people?",
            "Il sistema apprende dai dati o deduce i propri output (previsioni, contenuti, raccomandazioni), oppure applica soltanto regole fisse scritte da persone?",
        ),
        B("Only systems that infer outputs are 'AI systems' under the Act.", "Solo i sistemi che deducono gli output sono «sistemi di IA» ai sensi del regolamento."),
        options=_opts(
            [
                (True, "It learns or infers its outputs", "Apprende o deduce i propri output"),
                (False, "It only follows fixed, hand-written rules", "Segue soltanto regole fisse scritte a mano"),
            ]
        ),
    ),
    Entry(
        "annex_iii_area",
        B(
            "Which of these uses best describes what the system's output is used for?",
            "Quale di questi utilizzi descrive meglio l'impiego dell'output del sistema?",
        ),
        B(
            "Uses listed in Annex III make a system high-risk.",
            "Gli utilizzi elencati nell'allegato III rendono un sistema ad alto rischio.",
        ),
        options=_opts(
            [
                ("1a_remote_biometric_identification", "Identifying people remotely from biometrics", "Identificare persone a distanza tramite dati biometrici"),
                ("1b_biometric_categorisation_sensitive", "Categorising people by sensitive traits from biometrics", "Classificare persone per caratteristiche sensibili tramite dati biometrici"),
                ("1c_emotion_recognition", "Recognising emotions", "Riconoscere le emozioni"),
                ("2_critical_infrastructure_safety", "Safety of critical infrastructure (energy, water, traffic, digital)", "Sicurezza di infrastrutture critiche (energia, acqua, traffico, digitale)"),
                ("3a_education_admission", "Admission to schools or training", "Ammissione a scuole o corsi di formazione"),
                ("3b_education_evaluation", "Grading or evaluating learners", "Valutare l'apprendimento degli studenti"),
                ("3c_education_level_assessment", "Deciding the level of education a person can access", "Stabilire il livello di istruzione accessibile a una persona"),
                ("3d_education_proctoring", "Detecting cheating during exams", "Rilevare comportamenti scorretti durante gli esami"),
                ("4a_recruitment_selection", "Recruiting: job ads, CV screening, candidate evaluation", "Selezione del personale: annunci, screening dei CV, valutazione dei candidati"),
                ("4b_work_decisions_monitoring", "Promotion, termination, task allocation or monitoring of workers", "Promozioni, licenziamenti, assegnazione di compiti o monitoraggio dei lavoratori"),
                ("5a_public_benefits_eligibility", "Eligibility for public benefits or services", "Ammissibilità a prestazioni o servizi pubblici"),
                ("5b_creditworthiness", "Credit scoring of individuals", "Valutazione del merito creditizio di persone fisiche"),
                ("5c_life_health_insurance_pricing", "Pricing or risk assessment for life/health insurance", "Prezzi o valutazione del rischio per assicurazioni vita/malattia"),
                ("5d_emergency_dispatch_triage", "Emergency calls, dispatch or patient triage", "Chiamate di emergenza, invio dei soccorsi o triage"),
                ("6a_le_victim_risk", "Police: risk of becoming a victim", "Polizia: rischio di diventare vittima"),
                ("6b_le_polygraph", "Police: polygraph-like tools", "Polizia: strumenti tipo poligrafo"),
                ("6c_le_evidence_reliability", "Police: reliability of evidence", "Polizia: affidabilità delle prove"),
                ("6d_le_offending_risk_profiling", "Police: risk of offending or re-offending", "Polizia: rischio di reato o recidiva"),
                ("6e_le_profiling_investigation", "Police: profiling in investigations", "Polizia: profilazione nelle indagini"),
                ("7a_migration_polygraph", "Border/migration: polygraph-like tools", "Frontiere/migrazione: strumenti tipo poligrafo"),
                ("7b_migration_risk_assessment", "Border/migration: risk assessment of travellers", "Frontiere/migrazione: valutazione del rischio dei viaggiatori"),
                ("7c_migration_application_examination", "Examining asylum, visa or residence applications", "Esame di domande di asilo, visto o soggiorno"),
                ("7d_migration_identification", "Border/migration: identifying people", "Frontiere/migrazione: identificazione di persone"),
                ("8a_justice_assist_judicial", "Assisting judges or dispute resolution", "Assistere giudici o la risoluzione delle controversie"),
                ("8b_elections_influence", "Influencing elections or voting behaviour", "Influenzare elezioni o comportamento di voto"),
                ("none", "None of these", "Nessuno di questi"),
            ]
        ),
    ),
    Entry(
        "annex_i_product",
        B(
            "Is the system part of (or itself) a regulated product, such as a medical device, machine, toy, vehicle or lift?",
            "Il sistema fa parte di un prodotto regolamentato (o lo è esso stesso), come un dispositivo medico, una macchina, un giocattolo, un veicolo o un ascensore?",
        ),
        B(
            "AI in products covered by Annex I legislation can be high-risk under Art. 6(1).",
            "L'IA nei prodotti disciplinati dalla normativa dell'allegato I può essere ad alto rischio ai sensi dell'art. 6, par. 1.",
        ),
        options=_opts(
            [
                ("none", "No regulated product", "Nessun prodotto regolamentato"),
                ("medical_devices", "Medical device", "Dispositivo medico"),
                ("in_vitro_diagnostics", "In vitro diagnostic device", "Dispositivo medico-diagnostico in vitro"),
                ("machinery", "Machinery", "Macchine"),
                ("toys", "Toy", "Giocattolo"),
                ("vehicles", "Motor vehicle", "Veicolo a motore"),
                ("agricultural_vehicles", "Agricultural or forestry vehicle", "Veicolo agricolo o forestale"),
                ("civil_aviation", "Civil aviation or drones", "Aviazione civile o droni"),
                ("rail", "Rail", "Ferroviario"),
                ("marine_equipment", "Marine equipment", "Equipaggiamento marittimo"),
                ("lifts", "Lift", "Ascensore"),
                ("radio_equipment", "Radio equipment", "Apparecchiature radio"),
                ("personal_protective_equipment", "Personal protective equipment", "Dispositivi di protezione individuale"),
                ("pressure_equipment", "Pressure equipment", "Attrezzature a pressione"),
                ("gas_appliances", "Gas appliance", "Apparecchio a gas"),
                ("equipment_explosive_atmospheres", "Equipment for explosive atmospheres", "Apparecchi per atmosfere esplosive"),
                ("cableways", "Cableway", "Impianto a fune"),
                ("recreational_craft", "Recreational craft", "Imbarcazione da diporto"),
                ("other_regulated_product", "Another product under EU harmonisation law", "Altro prodotto soggetto alla normativa di armonizzazione UE"),
            ]
        ),
    ),
    Entry(
        "safety_component",
        B(
            "Does the AI perform a safety function in that product, so that its failure could endanger people's health or safety?",
            "L'IA svolge una funzione di sicurezza nel prodotto, tale che un suo guasto potrebbe mettere in pericolo la salute o la sicurezza delle persone?",
        ),
        B(
            "Only safety components (or the product itself) are high-risk under Art. 6(1).",
            "Solo i componenti di sicurezza (o il prodotto stesso) sono ad alto rischio ai sensi dell'art. 6, par. 1.",
        ),
        after=["annex_i_product"],
    ),
    Entry(
        "annex_i_third_party_assessment",
        B(
            "Does the product need a notified body (third-party conformity assessment) under its own EU product rules for health and safety reasons?",
            "Il prodotto richiede l'intervento di un organismo notificato (valutazione della conformità da parte di terzi) ai sensi della propria normativa UE per motivi di salute e sicurezza?",
        ),
        B(
            "Art. 6(1)(b) makes it high-risk only if third-party assessment is required.",
            "L'art. 6, par. 1, lett. b), lo rende ad alto rischio solo se è richiesta una valutazione di terzi.",
        ),
        after=["annex_i_product", "safety_component"],
    ),
    Entry(
        "art63.profiling_of_natural_persons",
        B(
            "Does the system build profiles of individuals — evaluating personal aspects such as performance, reliability, behaviour or preferences?",
            "Il sistema crea profili di persone, valutando aspetti personali come rendimento, affidabilità, comportamento o preferenze?",
        ),
        B(
            "Profiling always keeps an Annex III system high-risk (Art. 6(3)).",
            "La profilazione mantiene sempre ad alto rischio un sistema dell'allegato III (art. 6, par. 3).",
        ),
        after=["annex_iii_area"],
    ),
    Entry(
        "decision_impact",
        B(
            "Who decides in the end — does the system's output decide, or does a person make the final decision, and how much do they rely on the output?",
            "Chi decide alla fine: decide l'output del sistema oppure una persona prende la decisione finale, e in che misura si basa sull'output?",
        ),
        B(
            "An Annex III system can escape high-risk only if it does not materially influence the decision (Art. 6(3)).",
            "Un sistema dell'allegato III può non essere ad alto rischio solo se non influenza materialmente la decisione (art. 6, par. 3).",
        ),
        options=_opts(
            [
                ("determines_outcome", "The output is the decision", "L'output è la decisione"),
                ("materially_influences", "A person decides but relies heavily on the output", "Decide una persona, ma si basa in larga misura sull'output"),
                ("supports_human_decision", "A person assesses the case independently; the output is just one input", "Una persona valuta il caso autonomamente; l'output è solo un elemento"),
                ("no_decision_about_persons", "No decisions about individuals are involved", "Non riguarda decisioni su persone"),
            ]
        ),
        after=["annex_iii_area"],
    ),
    Entry(
        "art63.narrow_procedural_task",
        B(
            "Is the system limited to a narrow procedural task, such as sorting documents, detecting duplicates or converting formats?",
            "Il sistema si limita a un compito procedurale ristretto, come ordinare documenti, rilevare duplicati o convertire formati?",
        ),
        B("A narrow procedural task can qualify for the Art. 6(3)(a) derogation.", "Un compito procedurale limitato può rientrare nella deroga dell'art. 6, par. 3, lett. a)."),
        after=["annex_iii_area"],
    ),
    Entry(
        "art63.improves_prior_human_activity",
        B(
            "Does it only improve the result of work a person has already completed (e.g. polishing the wording of a finished assessment)?",
            "Si limita a migliorare il risultato di un lavoro già completato da una persona (ad es. rifinire il testo di una valutazione già conclusa)?",
        ),
        B("This can qualify for the Art. 6(3)(b) derogation.", "Può rientrare nella deroga dell'art. 6, par. 3, lett. b)."),
        after=["annex_iii_area"],
    ),
    Entry(
        "art63.detects_patterns_without_replacing_assessment",
        B(
            "Does it only flag deviations from past decision patterns for a person to review, without replacing or influencing their assessment?",
            "Si limita a segnalare scostamenti dalle decisioni passate perché una persona li esamini, senza sostituirne o influenzarne la valutazione?",
        ),
        B("This can qualify for the Art. 6(3)(c) derogation.", "Può rientrare nella deroga dell'art. 6, par. 3, lett. c)."),
        after=["annex_iii_area"],
    ),
    Entry(
        "art63.preparatory_task_only",
        B(
            "Does it only prepare material for a later assessment (e.g. indexing, translation, summarising files) without assessing the person?",
            "Si limita a preparare materiale per una valutazione successiva (ad es. indicizzazione, traduzione, sintesi di fascicoli) senza valutare la persona?",
        ),
        B("A preparatory task can qualify for the Art. 6(3)(d) derogation.", "Un compito preparatorio può rientrare nella deroga dell'art. 6, par. 3, lett. d)."),
        after=["annex_iii_area"],
    ),
    Entry(
        "transparency.interacts_with_natural_persons",
        B(
            "Do people interact with the system directly, for example by chatting or talking to it?",
            "Le persone interagiscono direttamente con il sistema, ad esempio chattando o parlando con esso?",
        ),
        B("Direct interaction triggers the AI-disclosure duty of Art. 50(1).", "L'interazione diretta fa scattare l'obbligo di informazione dell'art. 50, par. 1."),
    ),
    Entry(
        "transparency.obvious_to_users_it_is_ai",
        B(
            "Would a reasonably attentive user already understand, from the context, that they are dealing with an AI and not a person?",
            "Un utente ragionevolmente attento capirebbe già dal contesto di avere a che fare con un'IA e non con una persona?",
        ),
        B("No disclosure is needed when it is obvious (Art. 50(1)).", "L'informativa non è necessaria quando ciò è evidente (art. 50, par. 1)."),
        after=["transparency.interacts_with_natural_persons"],
    ),
    Entry(
        "transparency.generates_synthetic_content",
        B(
            "Does the system generate text, images, audio or video as output?",
            "Il sistema genera testi, immagini, audio o video come output?",
        ),
        B("Generated content must be machine-readably marked (Art. 50(2)).", "I contenuti generati devono essere marcati in modo leggibile meccanicamente (art. 50, par. 2)."),
    ),
    Entry(
        "transparency.deepfake",
        B(
            "Can it produce realistic images, audio or video of real people, places or events that could pass as authentic?",
            "Può produrre immagini, audio o video realistici di persone, luoghi o eventi reali che potrebbero sembrare autentici?",
        ),
        B("Deep fakes must be disclosed by the deployer (Art. 50(4)).", "I deep fake devono essere dichiarati dal deployer (art. 50, par. 4)."),
        after=["transparency.generates_synthetic_content"],
    ),
    Entry(
        "transparency.public_interest_text",
        B(
            "Is generated text published to inform the public on matters of public interest (news, public affairs)?",
            "I testi generati sono pubblicati per informare il pubblico su questioni di interesse pubblico (notizie, affari pubblici)?",
        ),
        B("Such text must be disclosed as AI-generated (Art. 50(4)).", "Tali testi devono essere dichiarati come generati dall'IA (art. 50, par. 4)."),
        after=["transparency.generates_synthetic_content"],
    ),
    Entry(
        "transparency.human_editorial_control",
        B(
            "Is every text reviewed by an editor, with someone holding editorial responsibility for publication?",
            "Ogni testo è rivisto da un redattore e c'è qualcuno che detiene la responsabilità editoriale della pubblicazione?",
        ),
        B("Editorial control removes the Art. 50(4) disclosure duty for text.", "Il controllo editoriale esclude l'obbligo dell'art. 50, par. 4, per i testi."),
        after=["transparency.public_interest_text"],
    ),
    Entry(
        "biometric.emotion_recognition",
        B(
            "Does the system infer people's emotions or intentions from their face, voice, or other biometric signals?",
            "Il sistema deduce emozioni o intenzioni delle persone dal volto, dalla voce o da altri segnali biometrici?",
        ),
        B("Emotion recognition is high-risk and banned at work and in education.", "Il riconoscimento delle emozioni è ad alto rischio ed è vietato sul lavoro e nell'istruzione."),
    ),
    Entry(
        "context_workplace_or_education",
        B(
            "Is it used on employees at work, or on students in schools or training institutions?",
            "Viene usato su dipendenti sul luogo di lavoro o su studenti in scuole o istituti di formazione?",
        ),
        B("Emotion recognition in these settings is prohibited (Art. 5(1)(f)).", "Il riconoscimento delle emozioni in questi contesti è vietato (art. 5, par. 1, lett. f))."),
        after=["biometric.emotion_recognition"],
    ),
    Entry(
        "biometric.medical_or_safety_purpose",
        B(
            "Is the emotion detection there strictly for medical or safety reasons (e.g. detecting driver fatigue)?",
            "Il rilevamento delle emozioni serve esclusivamente per motivi medici o di sicurezza (ad es. rilevare la stanchezza del conducente)?",
        ),
        B("Medical or safety reasons are the only exception to Art. 5(1)(f).", "I motivi medici o di sicurezza sono l'unica eccezione all'art. 5, par. 1, lett. f)."),
        after=["biometric.emotion_recognition", "context_workplace_or_education"],
    ),
    Entry(
        "biometric.categorisation",
        B(
            "Does the system sort people into categories based on biometric data such as face, body or voice?",
            "Il sistema classifica le persone in categorie sulla base di dati biometrici come volto, corpo o voce?",
        ),
        B("Biometric categorisation is regulated by Art. 5, Art. 50 and Annex III.", "La categorizzazione biometrica è disciplinata dagli artt. 5 e 50 e dall'allegato III."),
    ),
    Entry(
        "biometric.infers_sensitive_attributes",
        B(
            "Do those categories infer race, political opinions, trade union membership, religion or beliefs, sex life or sexual orientation?",
            "Queste categorie deducono razza, opinioni politiche, appartenenza sindacale, religione o convinzioni, vita sessuale o orientamento sessuale?",
        ),
        B("Inferring these traits from biometrics is prohibited (Art. 5(1)(g)).", "Dedurre questi tratti dai dati biometrici è vietato (art. 5, par. 1, lett. g))."),
        after=["biometric.categorisation"],
    ),
    Entry(
        "biometric.dataset_labelling_or_law_enforcement",
        B(
            "Is it only used to label or filter lawfully acquired biometric datasets, or by law enforcement to categorise biometric data?",
            "Viene usato solo per etichettare o filtrare set di dati biometrici acquisiti lecitamente, o dalle autorità di contrasto per categorizzare dati biometrici?",
        ),
        B("These uses are outside the Art. 5(1)(g) ban.", "Questi usi non rientrano nel divieto dell'art. 5, par. 1, lett. g)."),
        after=["biometric.categorisation", "biometric.infers_sensitive_attributes"],
    ),
    Entry(
        "biometric.remote_identification",
        B(
            "Does the system identify people at a distance by matching their face or other biometrics against a database (not just verifying a claimed identity)?",
            "Il sistema identifica persone a distanza confrontando volto o altri dati biometrici con una banca dati (non solo verificando un'identità dichiarata)?",
        ),
        B("Remote biometric identification is high-risk and partly prohibited.", "L'identificazione biometrica remota è ad alto rischio e in parte vietata."),
    ),
    Entry(
        "law_enforcement.used_by_or_for_law_enforcement",
        B("Is it used by or on behalf of police or other law enforcement authorities?", "È usato dalle forze di polizia o da altre autorità di contrasto, o per loro conto?"),
        B("Real-time identification for law enforcement is prohibited save narrow exceptions.", "L'identificazione in tempo reale a fini di contrasto è vietata salvo eccezioni ristrette."),
        after=["biometric.remote_identification"],
    ),
    Entry(
        "biometric.real_time",
        B("Does the identification happen live, without significant delay?", "L'identificazione avviene in diretta, senza ritardi significativi?"),
        B("'Real-time' use is the trigger for Art. 5(1)(h).", "L'uso «in tempo reale» è il presupposto dell'art. 5, par. 1, lett. h)."),
        after=["biometric.remote_identification"],
    ),
    Entry(
        "biometric.publicly_accessible_space",
        B(
            "Is it used in places open to the public, such as streets, stations or shops?",
            "Viene usato in luoghi aperti al pubblico, come strade, stazioni o negozi?",
        ),
        B("Art. 5(1)(h) concerns publicly accessible spaces.", "L'art. 5, par. 1, lett. h), riguarda gli spazi accessibili al pubblico."),
        after=["biometric.remote_identification"],
    ),
    Entry(
        "law_enforcement.rbi_strictly_necessary_objective",
        B(
            "Is each use strictly necessary to search for specific victims or missing persons, prevent an imminent threat or terrorist attack, or locate a suspect of a serious Annex II crime?",
            "Ogni uso è strettamente necessario per cercare vittime specifiche o persone scomparse, prevenire una minaccia imminente o un attacco terroristico, o localizzare un sospettato di un reato grave dell'allegato II?",
        ),
        B("Only these objectives lift the Art. 5(1)(h) ban.", "Solo questi obiettivi escludono il divieto dell'art. 5, par. 1, lett. h)."),
        after=[
            "biometric.remote_identification",
            "biometric.real_time",
            "biometric.publicly_accessible_space",
            "law_enforcement.used_by_or_for_law_enforcement",
        ],
    ),
    Entry(
        "gpai.is_gpai_model",
        B(
            "Are you offering a general-purpose AI model itself (e.g. a foundation or large language model others can build on)?",
            "State offrendo un modello di IA per finalità generali (ad es. un modello di base o un grande modello linguistico su cui altri possono costruire)?",
        ),
        B("General-purpose model providers have their own duties (Art. 53).", "I fornitori di modelli per finalità generali hanno obblighi propri (art. 53)."),
    ),
    Entry(
        "gpai.provider_of_model",
        B(
            "Did your organisation develop that model and make it available on the market?",
            "La vostra organizzazione ha sviluppato il modello e lo ha messo a disposizione sul mercato?",
        ),
        B("Art. 53 obligations fall on the model's provider.", "Gli obblighi dell'art. 53 gravano sul fornitore del modello."),
        after=["gpai.is_gpai_model"],
    ),
    Entry(
        "gpai.systemic_risk",
        B(
            "Was the model trained with more than 10^25 floating-point operations, or has the Commission designated it as having systemic risk?",
            "Il modello è stato addestrato con più di 10^25 operazioni in virgola mobile, o la Commissione lo ha designato come modello con rischio sistemico?",
        ),
        B("Systemic-risk models carry extra duties (Art. 55).", "I modelli con rischio sistemico hanno obblighi aggiuntivi (art. 55)."),
        after=["gpai.is_gpai_model", "gpai.provider_of_model"],
    ),
    Entry(
        "gpai.integrates_third_party_gpai",
        B(
            "Is the system built on a general-purpose model supplied by someone else (e.g. via an API)?",
            "Il sistema è basato su un modello per finalità generali fornito da terzi (ad es. tramite API)?",
        ),
        B("Integrators are downstream providers, not model providers, unless they modify the model.", "Chi integra è un fornitore a valle, non fornitore del modello, salvo che lo modifichi."),
    ),
    Entry(
        "gpai.substantially_modifies_model",
        B(
            "Do you substantially modify that model itself, for example by fine-tuning or retraining it, rather than only prompting it?",
            "Modificate in modo sostanziale il modello stesso, ad esempio con fine-tuning o riaddestramento, anziché limitarvi a fornirgli istruzioni (prompt)?",
        ),
        B("A substantial modification can make you a model provider.", "Una modifica sostanziale può rendervi fornitori del modello."),
        after=["gpai.integrates_third_party_gpai"],
    ),
    Entry(
        "manipulation.subliminal_or_deceptive",
        B(
            "Does the system use techniques people cannot consciously perceive, or deliberately manipulative or deceptive techniques, to steer their choices?",
            "Il sistema usa tecniche non percepibili consapevolmente, o tecniche deliberatamente manipolative o ingannevoli, per orientare le scelte delle persone?",
        ),
        B("Harmful manipulation is prohibited (Art. 5(1)(a)).", "La manipolazione dannosa è vietata (art. 5, par. 1, lett. a))."),
    ),
    Entry(
        "manipulation.exploits_vulnerabilities",
        B(
            "Does it target or exploit vulnerabilities linked to age, disability or a difficult social or economic situation?",
            "Prende di mira o sfrutta vulnerabilità legate all'età, alla disabilità o a una situazione sociale o economica difficile?",
        ),
        B("Exploiting vulnerabilities is prohibited (Art. 5(1)(b)).", "Lo sfruttamento delle vulnerabilità è vietato (art. 5, par. 1, lett. b))."),
    ),
    Entry(
        "manipulation.distorts_behaviour_significant_harm",
        B(
            "Could this lead people to decisions they would not otherwise take, causing them or others significant harm?",
            "Ciò potrebbe indurre le persone a decisioni che altrimenti non prenderebbero, causando a loro o ad altri un danno significativo?",
        ),
        B("Significant harm is a condition of Art. 5(1)(a) and (b).", "Il danno significativo è una condizione dell'art. 5, par. 1, lett. a) e b)."),
        after_any=["manipulation.subliminal_or_deceptive", "manipulation.exploits_vulnerabilities"],
    ),
    Entry(
        "social_scoring",
        B(
            "Does it score people over time on their social behaviour or personal traits, leading to unfavourable treatment in unrelated contexts or out of proportion?",
            "Attribuisce nel tempo un punteggio alle persone in base al comportamento sociale o a tratti personali, con trattamenti sfavorevoli in contesti non collegati o sproporzionati?",
        ),
        B("Social scoring is prohibited (Art. 5(1)(c)).", "Il punteggio sociale è vietato (art. 5, par. 1, lett. c))."),
    ),
    Entry(
        "law_enforcement.predictive_policing_profiling_only",
        B(
            "Does it predict whether a person will commit a crime based only on profiling or personality traits, rather than on objective facts?",
            "Prevede se una persona commetterà un reato basandosi solo sulla profilazione o sui tratti della personalità, anziché su fatti oggettivi?",
        ),
        B("This is prohibited by Art. 5(1)(d).", "È vietato dall'art. 5, par. 1, lett. d)."),
    ),
    Entry(
        "law_enforcement.untargeted_facial_scraping",
        B(
            "Does it build or expand a face database by collecting facial images indiscriminately from the internet or CCTV?",
            "Crea o amplia una banca dati di volti raccogliendo indiscriminatamente immagini facciali da internet o da telecamere?",
        ),
        B("Untargeted scraping is prohibited (Art. 5(1)(e)).", "L'estrazione non mirata è vietata (art. 5, par. 1, lett. e))."),
    ),
    Entry(
        "nudify_or_sexual_abuse_material",
        B(
            "Is the system meant to (or used to) create sexual or intimate imagery of real, identifiable people without their consent, or child sexual abuse material?",
            "Il sistema è destinato (o usato) a creare immagini sessuali o intime di persone reali identificabili senza il loro consenso, o materiale pedopornografico?",
        ),
        B("Prohibited from 2 December 2026 (Art. 5(1)(ba), (bb)).", "Vietato dal 2 dicembre 2026 (art. 5, par. 1, lett. ba) e bb))."),
        after=["transparency.generates_synthetic_content"],
    ),
    Entry(
        "intimate_content_foreseeable_without_safeguards",
        B(
            "Could users foreseeably get it to produce such material, and does it lack robust safeguards (filters, refusal training) that reliably prevent it?",
            "Gli utenti potrebbero prevedibilmente indurlo a produrre tale materiale, e mancano salvaguardie solide (filtri, addestramento al rifiuto) che lo impediscano in modo affidabile?",
        ),
        B("Providers are prohibited from offering such systems without safeguards (Art. 5(1a)).", "Ai fornitori è vietato offrire tali sistemi senza salvaguardie (art. 5, par. 1 bis)."),
        after=["transparency.generates_synthetic_content"],
    ),
]

# The Art. 6(3) derogation can only help when the output does not materially influence decisions
# about people, so its four conditions (and the profiling question) are asked only after that is known.
_ART63_GATE: dict[str, tuple[Any, ...]] = {"decision_impact": ("supports_human_decision", "no_decision_about_persons")}
for _e in REGISTRY:
    if _e.path.startswith("art63."):
        _e.when_values = dict(_ART63_GATE)

_BY_PATH: dict[str, Entry] = {e.path: e for e in REGISTRY}
_BY_PATH["role"] = ROLE_ENTRY
_PRIORITY: dict[str, int] = {e.path: i for i, e in enumerate(REGISTRY)}


def _truthy(v: Any) -> bool:
    return v is not None and v is not False and v != "none"


def _gate_open(f: FactSheet, e: Entry) -> bool:
    if e.after and not all(_truthy(f.get_path(p)) for p in e.after):
        return False
    if e.after_any and not any(_truthy(f.get_path(p)) for p in e.after_any):
        return False
    for path, values in e.when_values.items():
        if f.get_path(path) not in values:
            return False
    return True


def probe_paths(f: FactSheet) -> list[str]:
    """Unknown registry paths (plus role) whose gate is open."""
    out = [e.path for e in REGISTRY if f.get_path(e.path) is None and _gate_open(f, e)]
    if f.role is None:
        out.append("role")
    return out


def _question(e: Entry, impact: float) -> Question:
    return Question(
        id=f"q-{e.path}",
        fact_path=e.path,
        text=dict(e.text),
        why=dict(e.why),
        type=e.qtype,  # type: ignore[arg-type]
        options=[dict(o, label=dict(o["label"])) for o in e.options],
        impact=round(impact, 4),
    )


def next_questions(facts: FactSheet, max_questions: int = 3, asked: set[str] = frozenset()) -> list[Question]:
    from .rules import evaluate, sensitivity

    limit = max(0, min(max_questions, 3))
    if limit == 0:
        return []
    asked_paths = {a[2:] if a.startswith("q-") else a for a in asked}
    base = evaluate(facts)

    scored: list[tuple[float, float, int, str]] = []
    for p in probe_paths(facts):
        if p in asked_paths:
            continue
        s = sensitivity(facts, base, p)
        impact = s.impact
        if p == "role" and base.tier not in ("out_of_scope", "minimal_risk"):
            impact = max(impact, 0.5)
        if impact > 0:
            scored.append((impact, s.tier_impact, _PRIORITY.get(p, -1), p))

    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    chosen = scored[:limit]
    role_needed = (
        facts.role is None and "role" not in asked_paths and base.tier not in ("out_of_scope", "minimal_risk")
    )
    if role_needed and all(p != "role" for *_, p in chosen):
        role_item = next(t for t in scored if t[3] == "role")
        chosen = chosen[: limit - 1] + [role_item]
    return [_question(_BY_PATH[p], imp) for imp, _, _, p in chosen]
