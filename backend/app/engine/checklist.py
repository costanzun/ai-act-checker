"""Concrete documents and artefacts that evidence compliance with obligations."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ChecklistItem, Obligation

Bi = dict[str, str]


def B(en: str, it: str) -> Bi:
    return {"en": en, "it": it}


@dataclass
class Item:
    id: str
    title: Bi
    description: Bi
    citations: list[str]
    obligation_ids: list[str]
    template_hint: Bi | None = None


CATALOG: list[Item] = [
    Item("doc-prohibition-stop", B("Decision record: withdraw or redesign", "Verbale di decisione: ritiro o riprogettazione"),
         B("Record the decision to stop, withdraw or redesign the prohibited functionality, with the date and the technical change made.",
           "Registrare la decisione di interrompere, ritirare o riprogettare la funzione vietata, con data e modifica tecnica apportata."),
         ["art:5"], ["pro-art5"],
         B("Board/management minute + change ticket reference + legal sign-off.", "Verbale della direzione + riferimento al ticket di modifica + approvazione legale.")),
    Item("doc-risk-management-file", B("Risk management file", "Fascicolo di gestione dei rischi"),
         B("Risk register covering identified and foreseeable risks to health, safety and fundamental rights, misuse scenarios, mitigation measures, residual-risk acceptance and test results.",
           "Registro dei rischi con rischi noti e prevedibili per salute, sicurezza e diritti fondamentali, scenari di uso improprio, misure di attenuazione, accettazione del rischio residuo e risultati delle prove."),
         ["art:9"], ["hr-p-art9"],
         B("ISO/IEC 23894 or ISO 14971-style risk table: hazard, affected group, likelihood, severity, control, residual risk, owner.",
           "Tabella dei rischi secondo ISO/IEC 23894 o ISO 14971: pericolo, gruppo interessato, probabilità, gravità, misura, rischio residuo, responsabile.")),
    Item("doc-data-governance", B("Data governance record", "Registro di governance dei dati"),
         B("Datasheets for training, validation and testing data: origin, collection purpose, preparation steps, assumptions, representativeness, bias examination and mitigation, known gaps.",
           "Schede dei dati di addestramento, convalida e prova: origine, finalità della raccolta, preparazione, ipotesi, rappresentatività, esame e attenuazione delle distorsioni, lacune note."),
         ["art:10"], ["hr-p-art10"],
         B("'Datasheets for Datasets' template, one per dataset, plus a bias-testing report.", "Modello «Datasheets for Datasets», uno per set di dati, più un rapporto sui test di distorsione.")),
    Item("doc-technical-documentation", B("Technical documentation (Annex IV)", "Documentazione tecnica (allegato IV)"),
         B("Technical file with every Annex IV element: general description, development process, monitoring and control, performance metrics, risk management, changes, standards applied, declaration of conformity, post-market monitoring plan.",
           "Fascicolo tecnico con tutti gli elementi dell'allegato IV: descrizione generale, processo di sviluppo, monitoraggio e controllo, metriche di prestazione, gestione dei rischi, modifiche, norme applicate, dichiarazione di conformità, piano di monitoraggio successivo."),
         ["art:11", "annex:IV"], ["hr-p-art11"],
         B("One section per Annex IV point (1–9); SMEs/SMCs may use the Commission's simplified form.", "Una sezione per ciascun punto dell'allegato IV (1-9); PMI e SMC possono usare il modulo semplificato della Commissione.")),
    Item("doc-logging-policy", B("Logging and record-keeping policy", "Politica di registrazione e conservazione dei log"),
         B("Specification of events logged, log format, access controls, and a retention schedule of at least six months for provider- and deployer-controlled logs.",
           "Specifica degli eventi registrati, formato dei log, controlli di accesso e calendario di conservazione di almeno sei mesi per i log controllati da fornitore e deployer."),
         ["art:12", "art:19", "art:26.6"], ["hr-p-art12", "hr-p-art19", "hr-d-art26.6"],
         B("Table: event type, fields captured, storage location, retention period, legal basis.", "Tabella: tipo di evento, campi registrati, luogo di conservazione, periodo di conservazione, base giuridica.")),
    Item("doc-instructions-for-use", B("Instructions for use", "Istruzioni per l'uso"),
         B("Deployer-facing instructions with the Art. 13(3) content: provider identity, intended purpose, accuracy and limitations, human oversight measures, input data specifications, maintenance and log handling.",
           "Istruzioni per i deployer con i contenuti dell'art. 13, par. 3: identità del fornitore, finalità prevista, accuratezza e limiti, misure di sorveglianza umana, specifiche dei dati di input, manutenzione e gestione dei log."),
         ["art:13", "art:14", "art:15.3"], ["hr-p-art13", "hr-p-art14", "hr-p-art15"],
         B("Structure the document along Art. 13(3)(a)–(f); declare accuracy metrics as required by Art. 15(3).", "Strutturare il documento secondo l'art. 13, par. 3, lett. a)-f); dichiarare le metriche di accuratezza come richiesto dall'art. 15, par. 3.")),
    Item("doc-qms", B("Quality management system documentation", "Documentazione del sistema di gestione della qualità"),
         B("Written policies, procedures and instructions covering the 13 aspects of Art. 17(1), from regulatory strategy to accountability framework.",
           "Politiche, procedure e istruzioni scritte che coprono i 13 aspetti dell'art. 17, par. 1, dalla strategia di conformità al quadro di responsabilità."),
         ["art:17"], ["hr-p-art17", "hr-p-art18"],
         B("Map each Art. 17(1)(a)–(m) item to an existing ISO 9001 / ISO/IEC 42001 procedure.", "Associare ciascuna voce dell'art. 17, par. 1, lett. a)-m), a una procedura ISO 9001 / ISO/IEC 42001 esistente.")),
    Item("doc-conformity-assessment", B("Conformity assessment record", "Documentazione della valutazione della conformità"),
         B("Evidence of the conformity assessment procedure followed (internal control under Annex VI, notified-body procedure under Annex VII, or the sectoral Annex I procedure) and any certificates.",
           "Prova della procedura di valutazione della conformità seguita (controllo interno dell'allegato VI, procedura con organismo notificato dell'allegato VII o procedura settoriale dell'allegato I) e degli eventuali certificati."),
         ["art:43"], ["hr-p-art43"],
         B("Checklist of Section 2 requirements with evidence references; notified-body certificate if applicable.", "Elenco di controllo dei requisiti della sezione 2 con i riferimenti alle prove; certificato dell'organismo notificato se applicabile.")),
    Item("doc-eu-declaration", B("EU declaration of conformity", "Dichiarazione di conformità UE"),
         B("Signed declaration containing the Annex V information, kept for 10 years, plus the CE marking artwork (digital CE marking for online systems).",
           "Dichiarazione firmata con le informazioni dell'allegato V, conservata per 10 anni, e marcatura CE (digitale per i sistemi online)."),
         ["art:47", "annex:V", "art:48"], ["hr-p-art47", "hr-p-art48"],
         B("Annex V has 8 points: system name, provider, sole-responsibility statement, conformity statement, data-protection statement, standards, notified body, place/date/signature.",
           "L'allegato V prevede 8 punti: nome del sistema, fornitore, dichiarazione di responsabilità esclusiva, dichiarazione di conformità, protezione dei dati, norme, organismo notificato, luogo/data/firma.")),
    Item("doc-registration", B("EU database registration entry", "Registrazione nella banca dati dell'UE"),
         B("Prepared registration data for the EU database (Annex VIII, Section A for providers, Section B for Art. 6(3) systems, Section C for public-sector deployers).",
           "Dati di registrazione predisposti per la banca dati dell'UE (allegato VIII, sezione A per i fornitori, sezione B per i sistemi dell'art. 6, par. 3, sezione C per i deployer pubblici)."),
         ["art:49", "art:71", "annex:VIII"], ["hr-p-art49", "hr-d-art49.3", "der-p-art49.2"],
         B("Fill a spreadsheet with the Annex VIII fields before opening the EU database account.", "Compilare un foglio di calcolo con i campi dell'allegato VIII prima di aprire l'account nella banca dati dell'UE.")),
    Item("doc-post-market-plan", B("Post-market monitoring plan", "Piano di monitoraggio successivo all'immissione sul mercato"),
         B("Plan for actively collecting and analysing performance data from deployers and other sources over the lifetime; part of the technical documentation.",
           "Piano per raccogliere e analizzare attivamente i dati sulle prestazioni provenienti dai deployer e da altre fonti per tutta la durata; parte della documentazione tecnica."),
         ["art:72"], ["hr-p-art72", "hr-p-art20"],
         B("Metrics, data sources, review frequency, triggers for corrective action (Art. 20); Commission template due by 2 September 2027.",
           "Metriche, fonti dei dati, frequenza del riesame, soglie per le misure correttive (art. 20); modello della Commissione atteso entro il 2 settembre 2027.")),
    Item("doc-serious-incident-procedure", B("Serious incident procedure", "Procedura per gli incidenti gravi"),
         B("Procedure to detect, escalate and report serious incidents within 15 / 10 / 2 days, including the deployer-to-provider notification path.",
           "Procedura per rilevare, segnalare internamente e comunicare gli incidenti gravi entro 15 / 10 / 2 giorni, compreso il canale di notifica dal deployer al fornitore."),
         ["art:73", "art:26.5", "art:3.49"], ["hr-p-art73", "hr-d-art26.5"],
         B("Runbook with severity matrix, contacts of the market surveillance authority and report template.", "Procedura operativa con matrice di gravità, contatti dell'autorità di vigilanza del mercato e modello di segnalazione.")),
    Item("doc-deployer-operating-procedure", B("Deployer operating procedure and oversight roster", "Procedura operativa del deployer e registro della sorveglianza"),
         B("Internal procedure for using the system per the instructions, named human overseers with their training and authority, input-data checks and the suspension procedure.",
           "Procedura interna per usare il sistema secondo le istruzioni, nomina dei responsabili della sorveglianza umana con formazione e poteri, controlli sui dati di input e procedura di sospensione."),
         ["art:26.1", "art:26.2", "art:26.4", "art:26.5"], ["hr-d-art26.1", "hr-d-art26.2", "hr-d-art26.4", "hr-d-art26.5"],
         B("RACI table + training log + 'stop and escalate' criteria.", "Tabella RACI + registro della formazione + criteri di «arresto ed escalation».")),
    Item("doc-fria", B("Fundamental rights impact assessment", "Valutazione d'impatto sui diritti fondamentali"),
         B("Assessment with the six elements of Art. 27(1)(a)–(f), notified to the market surveillance authority; may cross-reference the DPIA.",
           "Valutazione con i sei elementi dell'art. 27, par. 1, lett. a)-f), notificata all'autorità di vigilanza del mercato; può rinviare alla DPIA."),
         ["art:27", "art:26.9"], ["hr-d-art27", "hr-d-art26.9"],
         B("Use the AI Office questionnaire template (Art. 27(5)); reuse the GDPR DPIA sections (Art. 27(4)).", "Usare il questionario dell'Ufficio per l'IA (art. 27, par. 5); riutilizzare le sezioni della DPIA (art. 27, par. 4).")),
    Item("doc-worker-notice", B("Worker information notice", "Informativa ai lavoratori"),
         B("Notice to workers' representatives and affected workers before the system is used at the workplace.",
           "Informativa ai rappresentanti dei lavoratori e ai lavoratori interessati prima che il sistema sia usato sul luogo di lavoro."),
         ["art:26.7"], ["hr-d-art26.7"],
         B("What the system does, which decisions it supports, data used, human oversight, contact point; align with national information/consultation rules.",
           "Cosa fa il sistema, quali decisioni supporta, dati usati, sorveglianza umana, punto di contatto; coordinare con le norme nazionali su informazione e consultazione.")),
    Item("doc-affected-person-notice", B("Affected-person notice and explanation procedure", "Informativa alle persone interessate e procedura di spiegazione"),
         B("Notice informing individuals that a high-risk system is used in decisions about them, and a procedure to provide explanations on request.",
           "Informativa alle persone sul fatto che un sistema ad alto rischio è usato nelle decisioni che le riguardano, e procedura per fornire spiegazioni su richiesta."),
         ["art:26.11", "art:86"], ["hr-d-art26.11", "hr-d-art86"],
         B("Short notice at the point of decision + explanation template: AI's role, main elements of the decision, how to contest.",
           "Breve informativa al momento della decisione + modello di spiegazione: ruolo dell'IA, elementi principali della decisione, modalità di contestazione.")),
    Item("doc-not-high-risk-assessment", B("Art. 6(3) 'not high-risk' assessment", "Valutazione di «non alto rischio» ai sensi dell'art. 6, par. 3"),
         B("Documented reasoning showing which Art. 6(3) condition applies, that there is no profiling, and that the output does not materially influence decisions.",
           "Motivazione documentata che indica quale condizione dell'art. 6, par. 3, si applica, l'assenza di profilazione e che l'output non influenza materialmente le decisioni."),
         ["art:6.3", "art:6.4"], ["der-p-art6.4"],
         B("One page: Annex III point, condition (a)–(d) relied on, evidence, profiling check, reviewer sign-off.", "Una pagina: punto dell'allegato III, condizione a)-d) invocata, prove, verifica sulla profilazione, approvazione del revisore.")),
    Item("doc-transparency-disclosures", B("AI transparency disclosures", "Informative di trasparenza sull'IA"),
         B("User-facing disclosure texts shown at the first interaction or exposure: AI interaction notice, emotion-recognition / biometric-categorisation notice, deep-fake and AI-text labels.",
           "Testi di informativa mostrati alla prima interazione o esposizione: avviso di interazione con un'IA, avviso di riconoscimento delle emozioni o categorizzazione biometrica, etichette per deep fake e testi generati."),
         ["art:50.1", "art:50.3", "art:50.4", "art:50.5"], ["tr-p-art50.1", "tr-d-art50.3", "tr-d-art50.4"],
         B("Clear, distinguishable, accessible wording; screenshot of where it appears; date first shown.", "Formulazione chiara, distinguibile e accessibile; schermata del punto in cui appare; data della prima visualizzazione.")),
    Item("doc-content-marking-spec", B("Synthetic content marking specification", "Specifica della marcatura dei contenuti sintetici"),
         B("Technical specification of the machine-readable marking (e.g. watermark, metadata, C2PA content credentials) and the detection method, with robustness tests.",
           "Specifica tecnica della marcatura leggibile meccanicamente (ad es. filigrana, metadati, credenziali C2PA) e del metodo di rilevamento, con prove di robustezza."),
         ["art:50.2"], ["tr-p-art50.2"],
         B("Per output type (text, image, audio, video): marking technique, detector, failure rate, interoperability standard.", "Per tipo di output (testo, immagine, audio, video): tecnica di marcatura, rilevatore, tasso di errore, norma di interoperabilità.")),
    Item("doc-ai-literacy-programme", B("AI literacy programme", "Programma di alfabetizzazione in materia di IA"),
         B("Training and awareness measures for staff and others operating or using AI systems on your behalf, tailored to their role and the context of use.",
           "Misure di formazione e sensibilizzazione per il personale e per chi gestisce o usa sistemi di IA per vostro conto, adattate al ruolo e al contesto d'uso."),
         ["art:4.1"], ["lit-art4"],
         B("Role-based curriculum + attendance log; see the Commission's practical examples on the AI single information platform.", "Percorso formativo per ruolo + registro delle presenze; vedere gli esempi pratici della Commissione sulla piattaforma unica di informazione sull'IA.")),
    Item("doc-gpai-technical-documentation", B("GPAI model documentation (Annexes XI and XII)", "Documentazione del modello GPAI (allegati XI e XII)"),
         B("Model documentation for authorities (Annex XI) and for downstream providers (Annex XII): architecture, training process, data, compute, evaluations, capabilities and limitations.",
           "Documentazione del modello per le autorità (allegato XI) e per i fornitori a valle (allegato XII): architettura, processo di addestramento, dati, calcolo, valutazioni, capacità e limiti."),
         ["art:53.1.a", "art:53.1.b", "annex:XI", "annex:XII"], ["gpai-art53.1.a", "gpai-art53.1.b"],
         B("The GPAI Code of Practice 'Model Documentation Form' covers both annexes.", "Il «Model Documentation Form» del codice di buone pratiche GPAI copre entrambi gli allegati.")),
    Item("doc-gpai-copyright-policy", B("Copyright policy", "Politica sul diritto d'autore"),
         B("Policy to comply with EU copyright law, including how text-and-data-mining reservations (e.g. robots.txt) are identified and respected.",
           "Politica di rispetto del diritto d'autore dell'UE, compreso il modo in cui le riserve sull'estrazione di testo e dati (ad es. robots.txt) sono individuate e rispettate."),
         ["art:53.1.c"], ["gpai-art53.1.c"],
         B("Follow the copyright chapter of the GPAI Code of Practice.", "Seguire il capitolo sul diritto d'autore del codice di buone pratiche GPAI.")),
    Item("doc-gpai-training-summary", B("Public training-content summary", "Sintesi pubblica dei contenuti di addestramento"),
         B("Publicly available, sufficiently detailed summary of the content used to train the model.",
           "Sintesi pubblica e sufficientemente dettagliata dei contenuti usati per addestrare il modello."),
         ["art:53.1.d"], ["gpai-art53.1.d"],
         B("Use the AI Office template for the training-data summary.", "Usare il modello dell'Ufficio per l'IA per la sintesi dei dati di addestramento.")),
    Item("doc-gpai-systemic-risk", B("Systemic-risk evaluation and mitigation file", "Fascicolo di valutazione e attenuazione dei rischi sistemici"),
         B("Model evaluation and adversarial-testing reports, systemic-risk assessment, incident log and cybersecurity measures; notification to the Commission.",
           "Rapporti di valutazione del modello e dei test contraddittori, valutazione dei rischi sistemici, registro degli incidenti e misure di cibersicurezza; notifica alla Commissione."),
         ["art:55", "art:52.1"], ["gpai-art55.1.a", "gpai-art55.1.b", "gpai-art55.1.c", "gpai-art55.1.d", "gpai-art52.1"],
         B("Safety and Security chapter of the GPAI Code of Practice (safety framework + model report).", "Capitolo «Safety and Security» del codice di buone pratiche GPAI (quadro di sicurezza + relazione sul modello).")),
    Item("doc-sectoral-compliance", B("Sectoral product compliance file", "Fascicolo di conformità settoriale"),
         B("Map how the AI requirements are covered within the sectoral type-approval or product legislation file for the product.",
           "Indicare come i requisiti per l'IA sono coperti nel fascicolo di omologazione o di conformità settoriale del prodotto."),
         ["art:2.2", "art:6.1"], ["hr-annex-i-b-sectoral"],
         B("Cross-reference table: AI Act Arts 9–15 topics → sectoral requirement → evidence.", "Tabella di corrispondenza: temi degli artt. 9-15 → requisito settoriale → prova.")),
]


def checklist_for(obligations: list[Obligation]) -> list[ChecklistItem]:
    present = {o.id for o in obligations}
    out: list[ChecklistItem] = []
    for it in CATALOG:
        ids = [i for i in it.obligation_ids if i in present]
        if not ids:
            continue
        out.append(
            ChecklistItem(
                id=it.id,
                title=dict(it.title),
                description=dict(it.description),
                citations=list(it.citations),
                obligation_ids=ids,
                template_hint=dict(it.template_hint) if it.template_hint else None,
            )
        )
    return out


def checklist_citation_ids() -> set[str]:
    return {c for it in CATALOG for c in it.citations}
