"""Obligation catalogue keyed by (tier/overlay, role), with application dates
derived from Art. 113 as consolidated (and Art. 111 transitional rules)."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import timeline as tl
from .facts import FactSheet
from .knowledge.annexes import ANNEX_I
from .models import Classification, Obligation

Bi = dict[str, str]


def B(en: str, it: str) -> Bi:
    return {"en": en, "it": it}


@dataclass
class Spec:
    id: str
    role: str  # provider | deployer | both
    category: str
    title: Bi
    summary: Bi
    citations: list[str]
    applies_from: str | None = None  # "HR" = high-risk date of the system
    priority: str = "must"
    extra: list[str] = field(default_factory=list)

    def build(self, applies_from: str | None, citations: list[str] | None = None, priority: str | None = None,
              summary: Bi | None = None) -> Obligation:
        return Obligation(
            id=self.id,
            role=self.role,  # type: ignore[arg-type]
            category=self.category,  # type: ignore[arg-type]
            title=dict(self.title),
            summary=dict(summary or self.summary),
            citations=list(citations or self.citations),
            applies_from=applies_from,
            priority=(priority or self.priority),  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------
LITERACY = Spec(
    "lit-art4",
    "both",
    "literacy",
    B("AI literacy measures", "Misure di alfabetizzazione in materia di IA"),
    B(
        "Take measures to support the AI literacy of staff and others operating or using the system on your behalf, considering their knowledge and the context of use. As amended by the Omnibus, no specific literacy level must be guaranteed.",
        "Adottare misure per sostenere l'alfabetizzazione in materia di IA del personale e di chi gestisce o usa il sistema per vostro conto, tenendo conto delle loro conoscenze e del contesto d'uso. Dopo l'Omnibus non è richiesto di garantire un livello specifico.",
    ),
    ["art:4.1", "art:3.56", "rec:20"],
    tl.PROHIBITIONS,
)

VOLUNTARY_CODES = Spec(
    "min-art95",
    "both",
    "governance",
    B("Voluntary codes of conduct", "Codici di condotta volontari"),
    B(
        "Consider voluntarily applying some high-risk requirements (e.g. documentation, human oversight) through a code of conduct.",
        "Valutare l'applicazione volontaria di alcuni requisiti per l'alto rischio (ad es. documentazione, sorveglianza umana) mediante un codice di condotta.",
    ),
    ["art:95", "rec:165"],
    tl.GENERAL,
    priority="should",
)

PROHIBITED = [
    Spec(
        "pro-art5",
        "both",
        "governance",
        B("Do not place on the market, put into service or use", "Non immettere sul mercato, mettere in servizio o usare"),
        B(
            "The practice is prohibited. Stop or redesign the system so that the prohibited function is removed before it is offered or used in the EU.",
            "La pratica è vietata. Interrompere o riprogettare il sistema eliminando la funzione vietata prima che sia offerto o usato nell'UE.",
        ),
        ["art:5"],
        tl.PROHIBITIONS,
    ),
    Spec(
        "pro-art99",
        "both",
        "other",
        B("Exposure to the highest fines", "Esposizione alle sanzioni più elevate"),
        B(
            "Non-compliance with Art. 5 is subject to fines of up to EUR 35 million or 7% of worldwide annual turnover, whichever is higher (for SMEs, whichever is lower).",
            "La violazione dell'art. 5 è punita con sanzioni fino a 35 milioni di EUR o al 7% del fatturato mondiale annuo, se superiore (per le PMI, se inferiore).",
        ),
        ["art:99.3", "art:99.6"],
        tl.GPAI_AND_GOVERNANCE,
    ),
]

HR_PROVIDER = [
    Spec("hr-p-art9", "provider", "governance", B("Risk management system", "Sistema di gestione dei rischi"),
         B("Establish, document and maintain a continuous risk management process over the whole lifecycle, including testing against predefined metrics and attention to minors and vulnerable groups.",
           "Istituire, documentare e mantenere un processo continuo di gestione dei rischi per l'intero ciclo di vita, comprese prove rispetto a metriche predefinite e attenzione ai minori e ai gruppi vulnerabili."),
         ["art:9"], "HR"),
    Spec("hr-p-art10", "provider", "data", B("Data and data governance", "Dati e governance dei dati"),
         B("Training, validation and testing data must follow governance practices (origin, preparation, bias examination and mitigation) and be relevant, representative and as error-free as possible.",
           "I dati di addestramento, convalida e prova devono seguire pratiche di governance (origine, preparazione, esame e attenuazione delle distorsioni) ed essere pertinenti, rappresentativi e il più possibile privi di errori."),
         ["art:10", "art:4a"], "HR"),
    Spec("hr-p-art11", "provider", "documentation", B("Technical documentation", "Documentazione tecnica"),
         B("Draw up technical documentation with at least the Annex IV elements before placing on the market and keep it up to date; SMEs and SMCs may use the simplified form.",
           "Redigere la documentazione tecnica con almeno gli elementi dell'allegato IV prima dell'immissione sul mercato e tenerla aggiornata; PMI e piccole imprese a media capitalizzazione possono usare il modulo semplificato."),
         ["art:11", "annex:IV"], "HR"),
    Spec("hr-p-art12", "provider", "documentation", B("Record-keeping (automatic logs)", "Conservazione delle registrazioni (log automatici)"),
         B("Design the system to automatically record events (logs) over its lifetime, enabling traceability, post-market monitoring and deployer monitoring.",
           "Progettare il sistema in modo che registri automaticamente gli eventi (log) per tutta la sua durata, a fini di tracciabilità, monitoraggio successivo e sorveglianza da parte del deployer."),
         ["art:12"], "HR"),
    Spec("hr-p-art13", "provider", "transparency", B("Transparency and instructions for use", "Trasparenza e istruzioni per l'uso"),
         B("Make the system's operation interpretable for deployers and supply instructions for use with the content listed in Art. 13(3).",
           "Rendere il funzionamento del sistema interpretabile per i deployer e fornire istruzioni per l'uso con i contenuti elencati all'art. 13, par. 3."),
         ["art:13"], "HR"),
    Spec("hr-p-art14", "provider", "oversight", B("Human oversight by design", "Sorveglianza umana fin dalla progettazione"),
         B("Design the system so that natural persons can effectively oversee it, understand its limits, avoid automation bias, override its output and stop it.",
           "Progettare il sistema affinché persone fisiche possano sorvegliarlo efficacemente, comprenderne i limiti, evitare la distorsione da automazione, ignorarne l'output e arrestarlo."),
         ["art:14"], "HR"),
    Spec("hr-p-art15", "provider", "governance", B("Accuracy, robustness and cybersecurity", "Accuratezza, robustezza e cibersicurezza"),
         B("Achieve and declare appropriate levels of accuracy, robustness and cybersecurity, including resilience to data poisoning, adversarial examples and feedback loops.",
           "Raggiungere e dichiarare livelli adeguati di accuratezza, robustezza e cibersicurezza, compresa la resilienza ad avvelenamento dei dati, esempi antagonistici e circuiti di retroazione."),
         ["art:15"], "HR"),
    Spec("hr-p-art16", "provider", "other", B("General provider obligations", "Obblighi generali del fornitore"),
         B("Ensure compliance with Section 2, indicate your name and contact address, meet accessibility requirements and demonstrate conformity on request.",
           "Garantire la conformità alla sezione 2, indicare nome e recapito, rispettare i requisiti di accessibilità e dimostrare la conformità su richiesta."),
         ["art:16"], "HR"),
    Spec("hr-p-art17", "provider", "governance", B("Quality management system", "Sistema di gestione della qualità"),
         B("Put in place a documented quality management system covering the aspects in Art. 17(1), proportionate to the size of the organisation (simplified for SMEs).",
           "Istituire un sistema di gestione della qualità documentato che copra gli aspetti dell'art. 17, par. 1, proporzionato alle dimensioni dell'organizzazione (semplificato per le PMI)."),
         ["art:17", "art:63"], "HR"),
    Spec("hr-p-art18", "provider", "documentation", B("Documentation keeping (10 years)", "Conservazione dei documenti (10 anni)"),
         B("Keep the technical documentation, QMS documentation, notified-body decisions and EU declaration of conformity available to authorities for 10 years.",
           "Tenere a disposizione delle autorità per 10 anni la documentazione tecnica, quella del sistema di gestione della qualità, le decisioni degli organismi notificati e la dichiarazione di conformità UE."),
         ["art:18"], "HR"),
    Spec("hr-p-art19", "provider", "documentation", B("Keep automatically generated logs", "Conservare i log generati automaticamente"),
         B("Keep the logs under your control for a period appropriate to the intended purpose, at least six months.",
           "Conservare i log sotto il proprio controllo per un periodo adeguato alla finalità prevista, di almeno sei mesi."),
         ["art:19"], "HR"),
    Spec("hr-p-art20", "provider", "monitoring", B("Corrective actions and duty of information", "Misure correttive e dovere di informazione"),
         B("If the system is not in conformity, immediately correct, withdraw, disable or recall it and inform distributors, deployers and, where it presents a risk, the authorities.",
           "Se il sistema non è conforme, correggerlo, ritirarlo, disattivarlo o richiamarlo immediatamente e informare distributori, deployer e, se presenta un rischio, le autorità."),
         ["art:20"], "HR"),
    Spec("hr-p-art21", "provider", "other", B("Cooperation with competent authorities", "Cooperazione con le autorità competenti"),
         B("On reasoned request, provide authorities with all information and documentation and access to logs needed to demonstrate conformity.",
           "Su richiesta motivata, fornire alle autorità tutte le informazioni, la documentazione e l'accesso ai log necessari a dimostrare la conformità."),
         ["art:21"], "HR"),
    Spec("hr-p-art22", "provider", "other", B("Authorised representative (non-EU providers)", "Rappresentante autorizzato (fornitori extra UE)"),
         B("If you are established outside the EU, appoint an EU authorised representative by written mandate before making the system available.",
           "Se siete stabiliti fuori dall'UE, nominare per iscritto un rappresentante autorizzato nell'UE prima di mettere a disposizione il sistema."),
         ["art:22"], "HR", priority="should"),
    Spec("hr-p-art43", "provider", "governance", B("Conformity assessment", "Valutazione della conformità"),
         B("Carry out the applicable conformity assessment before placing on the market, and again after any substantial modification.",
           "Effettuare la valutazione della conformità applicabile prima dell'immissione sul mercato e nuovamente dopo ogni modifica sostanziale."),
         ["art:43"], "HR", extra=["art:43.1", "art:43.2", "art:43.3", "annex:VI", "annex:VII"]),
    Spec("hr-p-art47", "provider", "documentation", B("EU declaration of conformity", "Dichiarazione di conformità UE"),
         B("Draw up a written, machine-readable or electronically signed EU declaration of conformity with the Annex V content and keep it for 10 years.",
           "Redigere una dichiarazione di conformità UE scritta, leggibile meccanicamente o firmata elettronicamente, con i contenuti dell'allegato V, e conservarla per 10 anni."),
         ["art:47", "annex:V"], "HR"),
    Spec("hr-p-art48", "provider", "other", B("CE marking", "Marcatura CE"),
         B("Affix the CE marking (digital CE marking for systems provided digitally), with the notified body number where applicable.",
           "Apporre la marcatura CE (digitale per i sistemi forniti in forma digitale), con il numero dell'organismo notificato ove applicabile."),
         ["art:48"], "HR"),
    Spec("hr-p-art49", "provider", "registration", B("Registration in the EU database", "Registrazione nella banca dati dell'UE"),
         B("Before placing on the market, register yourself and the system in the EU database with the Annex VIII, Section A information.",
           "Prima dell'immissione sul mercato, registrare se stessi e il sistema nella banca dati dell'UE con le informazioni dell'allegato VIII, sezione A."),
         ["art:49.1", "art:71", "annex:VIII"], "HR", extra=["art:49.5", "art:49.4"]),
    Spec("hr-p-art72", "provider", "monitoring", B("Post-market monitoring", "Monitoraggio successivo all'immissione sul mercato"),
         B("Establish a post-market monitoring system based on a plan that forms part of the technical documentation, collecting performance data throughout the lifetime.",
           "Istituire un sistema di monitoraggio successivo all'immissione sul mercato basato su un piano che fa parte della documentazione tecnica, raccogliendo dati sulle prestazioni per tutta la durata del sistema."),
         ["art:72"], "HR"),
    Spec("hr-p-art73", "provider", "monitoring", B("Serious incident reporting", "Comunicazione di incidenti gravi"),
         B("Report serious incidents to the market surveillance authority immediately and at the latest within 15 days (10 days for a death, 2 days for widespread infringements or critical-infrastructure disruption).",
           "Comunicare gli incidenti gravi all'autorità di vigilanza del mercato immediatamente e al più tardi entro 15 giorni (10 giorni in caso di decesso, 2 giorni per infrazioni diffuse o perturbazioni di infrastrutture critiche)."),
         ["art:73", "art:3.49"], "HR"),
]

HR_DEPLOYER = [
    Spec("hr-d-art26.1", "deployer", "governance", B("Use according to the instructions for use", "Uso conforme alle istruzioni per l'uso"),
         B("Take technical and organisational measures to use the system in accordance with the provider's instructions for use.",
           "Adottare misure tecniche e organizzative per usare il sistema conformemente alle istruzioni per l'uso del fornitore."),
         ["art:26.1"], "HR"),
    Spec("hr-d-art26.2", "deployer", "oversight", B("Assign human oversight", "Affidare la sorveglianza umana"),
         B("Assign human oversight to people with the necessary competence, training, authority and support.",
           "Affidare la sorveglianza umana a persone con competenza, formazione, autorità e sostegno necessari."),
         ["art:26.2"], "HR"),
    Spec("hr-d-art26.4", "deployer", "data", B("Relevant and representative input data", "Dati di input pertinenti e rappresentativi"),
         B("To the extent you control the input data, ensure it is relevant and sufficiently representative for the intended purpose.",
           "Nella misura in cui controllate i dati di input, garantire che siano pertinenti e sufficientemente rappresentativi rispetto alla finalità prevista."),
         ["art:26.4"], "HR"),
    Spec("hr-d-art26.5", "deployer", "monitoring", B("Monitor operation, suspend and report", "Monitorare il funzionamento, sospendere e segnalare"),
         B("Monitor the system per the instructions; if it may present a risk, inform the provider and the authority and suspend use; report serious incidents to the provider first.",
           "Monitorare il sistema secondo le istruzioni; se può presentare un rischio, informare il fornitore e l'autorità e sospenderne l'uso; segnalare gli incidenti gravi anzitutto al fornitore."),
         ["art:26.5", "art:73"], "HR"),
    Spec("hr-d-art26.6", "deployer", "documentation", B("Keep the logs", "Conservare i log"),
         B("Keep the automatically generated logs under your control for at least six months, unless other law provides otherwise.",
           "Conservare i log generati automaticamente sotto il proprio controllo per almeno sei mesi, salvo diversa disposizione di legge."),
         ["art:26.6"], "HR"),
    Spec("hr-d-art26.7", "deployer", "transparency", B("Inform workers and their representatives", "Informare i lavoratori e i loro rappresentanti"),
         B("Before using the system at the workplace, employers must inform workers' representatives and the affected workers.",
           "Prima di usare il sistema sul luogo di lavoro, i datori di lavoro devono informare i rappresentanti dei lavoratori e i lavoratori interessati."),
         ["art:26.7"], "HR"),
    Spec("hr-d-art49.3", "deployer", "registration", B("Register the use (public authorities)", "Registrare l'uso (autorità pubbliche)"),
         B("Public authorities and EU bodies (or those acting on their behalf) must register, select the system and register its use in the EU database before use; do not use an unregistered system.",
           "Le autorità pubbliche e gli organismi dell'UE (o chi agisce per loro conto) devono registrarsi, selezionare il sistema e registrarne l'uso nella banca dati dell'UE prima dell'uso; non usare sistemi non registrati."),
         ["art:26.8", "art:49.3", "annex:VIII"], "HR"),
    Spec("hr-d-art26.9", "deployer", "data", B("Data protection impact assessment", "Valutazione d'impatto sulla protezione dei dati"),
         B("Where applicable, use the provider's Art. 13 information to carry out the DPIA required under the GDPR or the Law Enforcement Directive.",
           "Ove applicabile, usare le informazioni dell'art. 13 fornite dal fornitore per effettuare la valutazione d'impatto prevista dal GDPR o dalla direttiva (UE) 2016/680."),
         ["art:26.9"], "HR", priority="should"),
    Spec("hr-d-art26.10", "deployer", "other", B("Authorisation for post-remote biometric identification", "Autorizzazione per l'identificazione biometrica remota a posteriori"),
         B("In criminal investigations, request judicial or administrative authorisation ex ante or within 48 hours, document each use and report annually.",
           "Nelle indagini penali, chiedere un'autorizzazione giudiziaria o amministrativa preventiva o entro 48 ore, documentare ogni uso e riferire annualmente."),
         ["art:26.10"], "HR"),
    Spec("hr-d-art26.11", "deployer", "transparency", B("Inform affected persons", "Informare le persone interessate"),
         B("Inform natural persons that they are subject to the use of the high-risk system when it makes or assists decisions about them.",
           "Informare le persone fisiche che sono soggette all'uso del sistema ad alto rischio quando esso adotta o contribuisce ad adottare decisioni che le riguardano."),
         ["art:26.11"], "HR"),
    Spec("hr-d-art27", "deployer", "governance", B("Fundamental rights impact assessment", "Valutazione d'impatto sui diritti fondamentali"),
         B("Before first use, assess the impact on fundamental rights (processes, period and frequency of use, affected groups, risks, oversight, mitigation and complaints) and notify the market surveillance authority of the results.",
           "Prima del primo uso, valutare l'impatto sui diritti fondamentali (processi, periodo e frequenza d'uso, categorie interessate, rischi, sorveglianza, misure e reclami) e notificarne i risultati all'autorità di vigilanza del mercato."),
         ["art:27", "rec:96"], "HR"),
    Spec("hr-d-art86", "deployer", "transparency", B("Explain individual decisions on request", "Spiegare le singole decisioni su richiesta"),
         B("Affected persons subject to a decision based on the system's output that significantly affects them can obtain clear and meaningful explanations of the AI's role and the main elements of the decision.",
           "Le persone interessate da una decisione basata sull'output del sistema che le riguarda in modo significativo possono ottenere spiegazioni chiare e significative sul ruolo dell'IA e sui principali elementi della decisione."),
         ["art:86", "rec:171"], "HR"),
    Spec("hr-d-art25", "deployer", "other", B("Avoid becoming the provider", "Evitare di diventare fornitore"),
         B("If you put your name or trademark on the system, substantially modify it, or change its intended purpose so it becomes high-risk, you take on all provider obligations.",
           "Se apponete il vostro nome o marchio sul sistema, lo modificate in modo sostanziale o ne cambiate la finalità prevista rendendolo ad alto rischio, assumete tutti gli obblighi del fornitore."),
         ["art:25.1", "rec:84"], "HR", priority="should"),
]

HR_OTHER = [
    Spec("hr-o-art23", "both", "other", B("Importer checks", "Verifiche dell'importatore"),
         B("Before placing the system on the market, verify conformity assessment, technical documentation, CE marking, declaration of conformity and authorised representative; keep copies for 10 years.",
           "Prima dell'immissione sul mercato, verificare valutazione della conformità, documentazione tecnica, marcatura CE, dichiarazione di conformità e rappresentante autorizzato; conservarne copia per 10 anni."),
         ["art:23"], "HR"),
    Spec("hr-o-art24", "both", "other", B("Distributor checks", "Verifiche del distributore"),
         B("Before making the system available, verify the CE marking, declaration of conformity and instructions for use; do not distribute non-conforming systems.",
           "Prima di mettere a disposizione il sistema, verificare marcatura CE, dichiarazione di conformità e istruzioni per l'uso; non distribuire sistemi non conformi."),
         ["art:24"], "HR"),
]

SECTION_B = Spec(
    "hr-annex-i-b-sectoral",
    "both",
    "governance",
    B("Comply via the sectoral product legislation", "Conformarsi tramite la normativa settoriale di prodotto"),
    B(
        "For Annex I Section B products only Art. 6(1), Art. 60a and Arts 102–112 of the AI Act apply; the AI requirements are applied through the type-approval or sectoral legislation (as amended by Arts 102–109 and by the Omnibus for machinery) and its implementing acts.",
        "Per i prodotti della sezione B dell'allegato I si applicano solo l'art. 6, par. 1, l'art. 60 bis e gli articoli da 102 a 112; i requisiti per l'IA si applicano tramite la normativa settoriale o di omologazione (modificata dagli articoli da 102 a 109 e, per le macchine, dall'Omnibus) e i relativi atti di esecuzione.",
    ),
    ["art:2.2", "art:6.1"],
    None,
)

DEROGATION = [
    Spec("der-p-art6.4", "provider", "documentation", B("Document the 'not high-risk' assessment", "Documentare la valutazione di «non alto rischio»"),
         B("Document why the Annex III system is not high-risk under Art. 6(3) before placing it on the market, and provide it to authorities on request.",
           "Documentare perché il sistema dell'allegato III non è ad alto rischio ai sensi dell'art. 6, par. 3, prima dell'immissione sul mercato, e fornire la documentazione alle autorità su richiesta."),
         ["art:6.4", "art:6.3"], tl.HIGH_RISK_ANNEX_III),
    Spec("der-p-art49.2", "provider", "registration", B("Register the system as not high-risk", "Registrare il sistema come non ad alto rischio"),
         B("Register yourself and the system in the EU database (Annex VIII, Section B, simplified by the Omnibus), stating the Art. 6(3) condition relied on.",
           "Registrare se stessi e il sistema nella banca dati dell'UE (allegato VIII, sezione B, semplificato dall'Omnibus), indicando la condizione dell'art. 6, par. 3, invocata."),
         ["art:49.2", "annex:VIII"], tl.HIGH_RISK_ANNEX_III),
]

TRANSPARENCY = {
    "art:50.1": Spec("tr-p-art50.1", "provider", "transparency", B("Disclose AI interaction", "Informare dell'interazione con un'IA"),
                     B("Design the system so people are informed they are interacting with AI, clearly and at the latest at first interaction, unless obvious from the context.",
                       "Progettare il sistema in modo che le persone siano informate, in modo chiaro e al più tardi alla prima interazione, di interagire con un'IA, salvo che ciò sia evidente dal contesto."),
                     ["art:50.1", "art:50.5"], tl.GENERAL),
    "art:50.2": Spec("tr-p-art50.2", "provider", "transparency", B("Machine-readable marking of synthetic content", "Marcatura leggibile meccanicamente dei contenuti sintetici"),
                     B("Ensure generated audio, image, video or text is marked in a machine-readable format and detectable as AI-generated, with effective, interoperable, robust and reliable solutions. Systems already on the market before 2 August 2026 must comply by 2 December 2026.",
                       "Garantire che audio, immagini, video o testi generati siano marcati in formato leggibile meccanicamente e rilevabili come generati dall'IA, con soluzioni efficaci, interoperabili, robuste e affidabili. I sistemi già sul mercato prima del 2 agosto 2026 devono conformarsi entro il 2 dicembre 2026."),
                     ["art:50.2", "art:111.4"], tl.GENERAL),
    "art:50.3": Spec("tr-d-art50.3", "deployer", "transparency", B("Inform people exposed to emotion recognition or biometric categorisation", "Informare le persone esposte a riconoscimento delle emozioni o categorizzazione biometrica"),
                     B("Inform the natural persons exposed of the operation of the system and process personal data in line with the GDPR.",
                       "Informare le persone fisiche esposte del funzionamento del sistema e trattare i dati personali in conformità al GDPR."),
                     ["art:50.3", "art:50.5"], tl.GENERAL),
    "art:50.4": Spec("tr-d-art50.4", "deployer", "transparency", B("Disclose deep fakes and AI-generated public-interest text", "Dichiarare deep fake e testi di interesse pubblico generati dall'IA"),
                     B("Disclose that deep-fake content, or text published to inform the public on matters of public interest, is AI-generated or manipulated (limited disclosure for artistic or satirical works; no duty for text under human editorial control).",
                       "Dichiarare che i contenuti deep fake, o i testi pubblicati per informare il pubblico su questioni di interesse pubblico, sono generati o manipolati dall'IA (informativa limitata per opere artistiche o satiriche; nessun obbligo per testi sotto controllo editoriale umano)."),
                     ["art:50.4", "art:50.5"], tl.GENERAL),
}

GPAI_BASE = [
    Spec("gpai-art53.1.a", "provider", "documentation", B("Model technical documentation (Annex XI)", "Documentazione tecnica del modello (allegato XI)"),
         B("Draw up and keep up to date the model's technical documentation, including training, testing and evaluation results, for the AI Office and national authorities.",
           "Redigere e aggiornare la documentazione tecnica del modello, compresi addestramento, prove e risultati della valutazione, per l'Ufficio per l'IA e le autorità nazionali."),
         ["art:53.1.a", "annex:XI"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art53.1.b", "provider", "documentation", B("Information for downstream providers (Annex XII)", "Informazioni per i fornitori a valle (allegato XII)"),
         B("Provide downstream AI system providers with information and documentation on the model's capabilities and limitations, with at least the Annex XII elements.",
           "Fornire ai fornitori di sistemi a valle informazioni e documentazione su capacità e limiti del modello, con almeno gli elementi dell'allegato XII."),
         ["art:53.1.b", "annex:XII"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art53.1.c", "provider", "governance", B("Copyright compliance policy", "Politica di rispetto del diritto d'autore"),
         B("Put in place a policy to comply with EU copyright law, including identifying and respecting text-and-data-mining opt-outs.",
           "Adottare una politica per rispettare il diritto d'autore dell'UE, compresa l'individuazione e il rispetto delle riserve sull'estrazione di testo e dati."),
         ["art:53.1.c"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art53.1.d", "provider", "transparency", B("Public summary of training content", "Sintesi pubblica dei contenuti di addestramento"),
         B("Publish a sufficiently detailed summary of the content used for training, using the AI Office template.",
           "Pubblicare una sintesi sufficientemente dettagliata dei contenuti usati per l'addestramento, secondo il modello dell'Ufficio per l'IA."),
         ["art:53.1.d"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art54", "provider", "other", B("Authorised representative (non-EU model providers)", "Rappresentante autorizzato (fornitori di modelli extra UE)"),
         B("If established outside the EU, appoint an authorised representative in the EU before placing the model on the market.",
           "Se stabiliti fuori dall'UE, nominare un rappresentante autorizzato nell'UE prima di immettere il modello sul mercato."),
         ["art:54"], tl.GPAI_AND_GOVERNANCE, priority="should"),
]

GPAI_SYSTEMIC = [
    Spec("gpai-art52.1", "provider", "registration", B("Notify the Commission", "Notificare la Commissione"),
         B("Notify the Commission within two weeks once the model meets (or will meet) the high-impact capability threshold.",
           "Notificare la Commissione entro due settimane da quando il modello raggiunge (o raggiungerà) la soglia delle capacità di impatto elevato."),
         ["art:52.1", "art:51.2"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art55.1.a", "provider", "governance", B("Model evaluation and adversarial testing", "Valutazione del modello e test contraddittori"),
         B("Evaluate the model with state-of-the-art protocols, including documented adversarial testing to identify and mitigate systemic risks.",
           "Valutare il modello con protocolli allo stato dell'arte, compresi test contraddittori documentati per individuare e attenuare i rischi sistemici."),
         ["art:55.1.a"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art55.1.b", "provider", "governance", B("Assess and mitigate systemic risks", "Valutare e attenuare i rischi sistemici"),
         B("Assess and mitigate possible systemic risks at Union level, including their sources.",
           "Valutare e attenuare i possibili rischi sistemici a livello dell'Unione, comprese le loro fonti."),
         ["art:55.1.b"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art55.1.c", "provider", "monitoring", B("Track and report serious incidents", "Tracciare e segnalare gli incidenti gravi"),
         B("Keep track of, document and report serious incidents and corrective measures to the AI Office without undue delay.",
           "Tracciare, documentare e segnalare senza indebito ritardo all'Ufficio per l'IA gli incidenti gravi e le misure correttive."),
         ["art:55.1.c"], tl.GPAI_AND_GOVERNANCE),
    Spec("gpai-art55.1.d", "provider", "governance", B("Cybersecurity of the model", "Cibersicurezza del modello"),
         B("Ensure adequate cybersecurity protection for the model and its physical infrastructure.",
           "Garantire un livello adeguato di protezione della cibersicurezza del modello e della sua infrastruttura fisica."),
         ["art:55.1.d"], tl.GPAI_AND_GOVERNANCE),
]

ALL_SPECS: list[Spec] = (
    [LITERACY, VOLUNTARY_CODES, SECTION_B]
    + PROHIBITED
    + HR_PROVIDER
    + HR_DEPLOYER
    + HR_OTHER
    + DEROGATION
    + list(TRANSPARENCY.values())
    + GPAI_BASE
    + GPAI_SYSTEMIC
)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------
def _roles(c: Classification) -> set[str]:
    r = c.role
    if r == "provider":
        return {"provider"}
    if r == "deployer":
        return {"deployer"}
    if r == "other":
        return {"other"}
    return {"provider", "deployer"}  # both / unknown


def _fired(c: Classification, prefix: str) -> list[str]:
    return [f.rule_id for f in c.findings if f.rule_id.startswith(prefix)]


def _annex_iii_point(c: Classification) -> str | None:
    for f in c.findings:
        if f.kind == "high_risk_annex_iii":
            for cid in f.citations:
                if cid.startswith("annex:III.") and cid != "annex:III":
                    return cid
    return None


_SECTORAL_ARTS = {"art:102", "art:103", "art:104", "art:105", "art:106", "art:107", "art:108", "art:109"}


def obligations_for(c: Classification, facts: FactSheet) -> list[Obligation]:
    if c.tier == "out_of_scope" and not c.overlays.get("gpai"):
        return []
    roles = _roles(c)
    out: list[Obligation] = []

    def add(spec: Spec, applies: str | None = None, **kw: object) -> None:
        if spec.role in roles or spec.role == "both":
            if any(o.id == spec.id for o in out):
                return
            out.append(spec.build(applies if applies is not None else spec.applies_from, **kw))  # type: ignore[arg-type]

    # Prohibited ---------------------------------------------------------------
    if c.tier == "prohibited":
        cites = ["art:5"]
        new_only = True
        for f in c.findings:
            if f.kind == "prohibition":
                cites += [x for x in f.citations if x.startswith("art:5") and x not in cites]
                if not f.rule_id.startswith(("art5.1.ba", "art5.1a")):
                    new_only = False
        add(PROHIBITED[0], tl.NEW_PROHIBITIONS if new_only else tl.PROHIBITIONS, citations=cites)
        add(PROHIBITED[1])
        return out

    is_hr = c.tier == "high_risk"
    hr_iii = any(f.kind == "high_risk_annex_iii" for f in c.findings) and not any(
        f.rule_id == "art6.3-derogation" for f in c.findings
    )
    hr_i = any(f.kind == "high_risk_annex_i" for f in c.findings)
    section_b = hr_i and not hr_iii and ANNEX_I.get(facts.annex_i_product or "", ("A",))[0] == "B"
    hr_date = tl.HIGH_RISK_ANNEX_III if hr_iii else tl.HIGH_RISK_ANNEX_I
    point = _annex_iii_point(c)
    point2 = point == "annex:III.2"

    if is_hr and section_b:
        add(SECTION_B, None, citations=SECTION_B.citations + [x for f in c.findings if f.kind == "high_risk_annex_i"
                                                           for x in f.citations if x.startswith("annex:I.") or x in _SECTORAL_ARTS])
        return out

    if is_hr:
        if roles & {"provider"}:
            for s in HR_PROVIDER:
                if s.id == "hr-p-art43":
                    if hr_i:
                        cites = ["art:43", "art:43.3"]
                    elif point and point.startswith("annex:III.1"):
                        cites = ["art:43", "art:43.1", "annex:VI", "annex:VII"]
                    else:
                        cites = ["art:43", "art:43.2", "annex:VI"]
                    add(s, hr_date, citations=cites)
                elif s.id == "hr-p-art49":
                    if not hr_iii:
                        continue  # Art. 49(1) registration concerns Annex III systems
                    if point2:
                        add(s, hr_date, citations=["art:49.5"], summary=B(
                            "Critical-infrastructure systems (Annex III, point 2) are registered at national level.",
                            "I sistemi per infrastrutture critiche (allegato III, punto 2) sono registrati a livello nazionale."))
                    else:
                        add(s, hr_date)
                else:
                    add(s, hr_date)
        if roles & {"deployer"}:
            for s in HR_DEPLOYER:
                sid = s.id
                if sid == "hr-d-art26.7":
                    # Art. 26(7) binds employers; students in an education setting are not workers
                    area = facts.annex_iii_area or ""
                    at_work = facts.sector == "employment_workers_management"
                    if area.startswith("4") or (at_work and facts.context_workplace_or_education is True):
                        add(s, hr_date)
                    elif at_work and facts.context_workplace_or_education is None:
                        add(s, hr_date, priority="should")
                elif sid == "hr-d-art49.3":
                    # Art. 49(3) binds public authorities, agencies and bodies (and those acting for them),
                    # not private entities providing public services; the fact sheet does not separate the two,
                    # so this stays a conditional ("should") item with the condition in the summary.
                    if hr_iii and not point2 and facts.public_body_or_public_service is not False:
                        add(s, hr_date, priority="should", summary=B(
                            "Only if you are a public authority, agency or body (or act on its behalf): register yourself, select the system and register its use in the EU database before use; do not use an unregistered system.",
                            "Solo se siete un'autorità, agenzia o organismo pubblico (o agite per suo conto): registratevi, selezionate il sistema e registratene l'uso nella banca dati dell'UE prima dell'uso; non usate sistemi non registrati."))
                elif sid == "hr-d-art26.10":
                    # post-remote identification only (real-time use is governed by Art. 5(1)(h) and 5(2)-(7))
                    if point == "annex:III.1.a" and facts.law_enforcement.used_by_or_for_law_enforcement is True and facts.biometric.real_time is not True:
                        add(s, hr_date)
                elif sid in ("hr-d-art26.11", "hr-d-art86"):
                    if hr_iii and not (sid == "hr-d-art86" and point2) and facts.decision_impact != "no_decision_about_persons":
                        add(s, hr_date)
                elif sid == "hr-d-art27":
                    if hr_iii and not point2:
                        credit_ins = point in ("annex:III.5.b", "annex:III.5.c")
                        if credit_ins or facts.public_body_or_public_service is True:
                            add(s, hr_date)
                        elif facts.public_body_or_public_service is None:
                            add(s, hr_date, priority="should", summary=B(
                                "Required if you are a body governed by public law or a private entity providing public services (and always for credit scoring and life/health insurance pricing): assess the impact on fundamental rights before first use and notify the results.",
                                "Obbligatoria se siete un organismo di diritto pubblico o un ente privato che fornisce servizi pubblici (e sempre per merito creditizio e prezzi delle assicurazioni vita/malattia): valutare l'impatto sui diritti fondamentali prima del primo uso e notificarne i risultati."))
                else:
                    add(s, hr_date)
        if "other" in roles:
            for s in HR_OTHER:
                out.append(s.build(hr_date))

    # Art. 6(3) derogation ---------------------------------------------------------
    if any(f.rule_id == "art6.3-derogation" for f in c.findings) and not is_hr:
        for s in DEROGATION:
            add(s)

    # Transparency -----------------------------------------------------------------
    for prov in c.overlays.get("transparency_art50", []):
        spec = TRANSPARENCY.get(prov)
        if spec:
            add(spec)
    if "deployer" in roles and "provider" not in roles and "art:50.1" in c.overlays.get("transparency_art50", []):
        out.append(Spec(
            "tr-d-art50.1-check", "deployer", "transparency",
            B("Check the provider's AI-interaction disclosure", "Verificare l'informativa del fornitore sull'interazione con l'IA"),
            B("The duty to tell people they are interacting with an AI system sits with the provider (Art. 50(1)); as deployer, confirm the disclosure is implemented and not removed in your deployment.",
              "L'obbligo di informare le persone che interagiscono con un sistema di IA grava sul fornitore (art. 50, par. 1); come deployer, verificate che l'informativa sia implementata e non rimossa nella vostra configurazione."),
            ["art:50.1"], priority="should",
        ).build(tl.GENERAL))

    # GPAI -------------------------------------------------------------------------
    gp = c.overlays.get("gpai", [])
    if gp:
        roles_backup = set(roles)
        roles.add("provider")  # GPAI duties fall on the model provider by definition of the overlay
        open_src = facts.free_open_source_licence is True and "art:55" not in gp
        for s in GPAI_BASE:
            if open_src and s.id in ("gpai-art53.1.a", "gpai-art53.1.b", "gpai-art54"):
                continue
            add(s)
        if "art:55" in gp:
            for s in GPAI_SYSTEMIC:
                add(s)
        roles.clear()
        roles.update(roles_backup)

    if c.tier == "out_of_scope":  # Art. 2(12) open-source system: only the GPAI model duties remain
        return out

    # Everyone in scope (providers and deployers) ---------------------------------------
    if "other" not in roles or c.role in ("unknown", "both"):
        add(LITERACY)
    if c.tier in ("minimal_risk", "limited_risk"):
        add(VOLUNTARY_CODES)
    return out


def obligation_citation_ids() -> set[str]:
    out: set[str] = set()
    for s in ALL_SPECS:
        out |= set(s.citations) | set(s.extra)
    return out


def obligation_ids() -> set[str]:
    return {s.id for s in ALL_SPECS}
