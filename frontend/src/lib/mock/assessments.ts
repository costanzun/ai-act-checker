import type {
  Assessment, ChecklistItem, Classification, FactSheet, FactValue, Lang, LText, Milestone, Obligation, Question, Tier,
} from "../types";

const t = (en: string, it: string): LText => ({ en, it });

export const DISCLAIMER: LText = t(
  "This is an automated assessment under Regulation (EU) 2024/1689 and does not constitute legal advice. Have a qualified lawyer review the result before relying on it.",
  "Questa è una valutazione automatizzata ai sensi del Regolamento (UE) 2024/1689 e non costituisce consulenza legale. Fai verificare il risultato da un professionista qualificato prima di farvi affidamento.",
);

export const TIMELINE: Milestone[] = [
  { id: "m-2024-08-01", date: "2024-08-01", what: t("The AI Act enters into force.", "Il regolamento sull'IA entra in vigore."), citations: ["art:113"], status: "in_force" },
  { id: "m-2025-02-02", date: "2025-02-02", what: t("Definitions and prohibited practices (Chapters I and II) apply.", "Si applicano definizioni e pratiche vietate (capi I e II)."), citations: ["art:5", "art:113"], status: "in_force" },
  { id: "m-2025-08-02", date: "2025-08-02", what: t("Rules on general-purpose AI models and governance apply.", "Si applicano le norme sui modelli di IA per finalità generali e sulla governance."), citations: ["art:113"], status: "in_force" },
  { id: "m-2026-07-27", date: "2026-07-27", what: t("Digital Omnibus on AI (Reg. (EU) 2026/1744) enters into force.", "Entra in vigore il Digital Omnibus sull'IA (Reg. (UE) 2026/1744)."), citations: ["art:113"], status: "in_force" },
  { id: "m-2026-08-02", date: "2026-08-02", what: t("General date of application, including transparency obligations (Art. 50).", "Data generale di applicazione, compresi gli obblighi di trasparenza (art. 50)."), citations: ["art:50", "art:113"], status: "in_force" },
  { id: "m-2026-12-02", date: "2026-12-02", what: t("New prohibitions added by the Digital Omnibus apply.", "Si applicano i nuovi divieti introdotti dal Digital Omnibus."), citations: ["art:5", "art:113"], status: "upcoming" },
  { id: "m-2027-08-02", date: "2027-08-02", what: t("General-purpose models placed on the market before 2 August 2025 must comply.", "I modelli per finalità generali immessi sul mercato prima del 2 agosto 2025 devono conformarsi."), citations: ["art:113"], status: "upcoming" },
  { id: "m-2027-12-02", date: "2027-12-02", what: t("High-risk obligations for Annex III systems apply.", "Si applicano gli obblighi per i sistemi ad alto rischio dell'Allegato III."), citations: ["annex:III", "art:113"], status: "upcoming" },
  { id: "m-2028-08-02", date: "2028-08-02", what: t("High-risk obligations for Annex I product systems apply.", "Si applicano gli obblighi per i sistemi ad alto rischio dell'Allegato I (prodotti)."), citations: ["art:113"], status: "upcoming" },
  { id: "m-2029-08-02", date: "2029-08-02", what: t("Commission evaluation and review of the Regulation.", "Valutazione e riesame del regolamento da parte della Commissione."), citations: ["art:113"], status: "upcoming" },
  { id: "m-2030-12-31", date: "2030-12-31", what: t("AI components of certain large-scale EU IT systems must comply.", "I componenti di IA di alcuni sistemi informatici UE su larga scala devono conformarsi."), citations: ["art:113"], status: "upcoming" },
];

const ms = (...ids: string[]) => TIMELINE.filter((m) => ids.includes(m.id));

// ---------- CV screening: high risk, asks 2 questions first ----------
export const CV_QUESTIONS: Question[] = [
  {
    id: "q-role", fact_path: "role",
    text: t("Does your organisation build this system, or only use a system bought from someone else?", "La tua organizzazione sviluppa questo sistema o si limita a usare un sistema acquistato da terzi?"),
    why: t("Providers and deployers have different obligations under Articles 16 and 26.", "Fornitori e deployer hanno obblighi diversi ai sensi degli articoli 16 e 26."),
    type: "single",
    options: [
      { value: "provider", label: t("We build it", "Lo sviluppiamo noi") },
      { value: "deployer", label: t("We use a system from a vendor", "Usiamo il sistema di un fornitore") },
      { value: "both", label: t("Both: we build it and use it", "Entrambi: lo sviluppiamo e lo usiamo") },
    ],
    impact: 0.82,
  },
  {
    id: "q-decision", fact_path: "decision_impact",
    text: t("Does the score decide, or materially influence, which candidates move forward?", "Il punteggio decide, o influenza in modo sostanziale, quali candidati proseguono?"),
    why: t("If the tool only does a narrow preparatory task, the Article 6(3) derogation may remove the high-risk status.", "Se lo strumento svolge solo un compito preparatorio limitato, la deroga dell'articolo 6, par. 3, può escludere l'alto rischio."),
    type: "boolean", options: [], impact: 0.64,
  },
];

function cvAssessment(lang: Lang, description: string, answers: Record<string, unknown>): Assessment {
  const unknown = Object.values(answers).some((v) => v === null || v === "unknown");
  const role = (typeof answers.role === "string" && ["provider", "deployer", "both"].includes(answers.role) ? answers.role : "deployer") as Classification["role"];
  const classification: Classification = {
    tier: "high_risk",
    confidence: unknown ? "medium" : "high",
    role,
    findings: [
      {
        rule_id: "annex3-4a-recruitment", kind: "high_risk_annex_iii", decisive: true,
        title: t("Recruitment and selection is an Annex III use case", "Selezione e assunzione sono un caso d'uso dell'Allegato III"),
        rationale: t("The system analyses and ranks job applications, which is listed in [[annex:III.4.a]]. Systems listed in Annex III are high-risk under [[art:6.2]].", "Il sistema analizza e classifica le candidature, attività elencata nell'[[annex:III.4.a]]. I sistemi dell'Allegato III sono ad alto rischio ai sensi dell'[[art:6.2]]."),
        citations: ["annex:III.4.a", "art:6.2"], facts_used: ["sector", "purpose"],
      },
      {
        rule_id: "art6.3-derogation-not-met", kind: "derogation_6_3", decisive: false,
        title: t("The Article 6(3) derogation does not apply", "La deroga dell'articolo 6, par. 3, non si applica"),
        rationale: t("The tool profiles candidates and its ranking materially influences who is interviewed, so the exemption in [[art:6.3]] cannot be relied on.", "Lo strumento profila i candidati e la classifica influenza in modo sostanziale chi viene convocato, quindi non si può invocare l'esenzione dell'[[art:6.3]]."),
        citations: ["art:6.3"], facts_used: ["decision_impact", "profiling"],
      },
    ],
    overlays: {},
    applies_from: ms("m-2027-12-02"),
    unresolved: unknown ? ["decision_impact"] : [],
    assumptions: unknown ? [t("We assumed the ranking materially influences hiring decisions.", "Abbiamo ipotizzato che la classifica influenzi in modo sostanziale le decisioni di assunzione.")] : [],
  };
  const reasoning = lang === "it"
    ? `## Perché questo livello di rischio\n\nIl tuo sistema **seleziona e classifica candidati**, un'attività che l'[[annex:III.4.a]] elenca tra i casi d'uso ad alto rischio. Per l'[[art:6.2]] i sistemi dell'Allegato III sono considerati ad alto rischio.\n\nLa deroga dell'[[art:6.3]] non sembra applicabile: il sistema effettua profilazione e il suo punteggio incide sulla decisione di convocare un candidato. Il [[rec:57]] spiega che questi sistemi possono avere un impatto rilevante sulle prospettive di carriera.\n\n## Cosa significa per te\n\n- Come **${role === "provider" ? "fornitore" : "deployer"}**, devi rispettare i requisiti del Capo III, in particolare la sorveglianza umana ([[art:14]]) e, per chi lo usa, gli obblighi dell'[[art:26]].\n- Gli obblighi per i sistemi dell'Allegato III si applicano dal **2 dicembre 2027** (Digital Omnibus, [[art:113]]).\n- Le persone interessate hanno diritto a una spiegazione ([[art:86]]).`
    : `## Why this risk tier\n\nYour system **screens and ranks job candidates**, which [[annex:III.4.a]] lists as a high-risk use case. Under [[art:6.2]], systems listed in Annex III are considered high-risk.\n\nThe derogation in [[art:6.3]] does not appear to apply: the system profiles candidates and its score influences who is invited to interview. [[rec:57]] explains that such systems can have a significant impact on career prospects and livelihoods.\n\n## What this means for you\n\n- As a **${role === "provider" ? "provider" : "deployer"}** you must meet the Chapter III requirements, notably human oversight ([[art:14]]) and, for those who use the system, the duties in [[art:26]].\n- Obligations for Annex III systems apply from **2 December 2027** (Digital Omnibus, [[art:113]]).\n- People affected have a right to an explanation ([[art:86]]).`;

  const obligations: Obligation[] = [
    { id: "ob-rms", role: "provider", category: "governance", priority: "must", applies_from: "2027-12-02", citations: ["art:9"],
      title: t("Risk management system", "Sistema di gestione dei rischi"), summary: t("Establish and maintain a continuous risk management process across the whole lifecycle ([[art:9]]).", "Istituire e mantenere un processo continuo di gestione dei rischi lungo l'intero ciclo di vita ([[art:9]]).") },
    { id: "ob-data", role: "provider", category: "data", priority: "must", applies_from: "2027-12-02", citations: ["art:10"],
      title: t("Data governance", "Governance dei dati"), summary: t("Training, validation and test data must be relevant, representative and examined for bias ([[art:10]]).", "I dati di addestramento, convalida e prova devono essere pertinenti, rappresentativi e verificati rispetto a possibili distorsioni ([[art:10]]).") },
    { id: "ob-doc", role: "provider", category: "documentation", priority: "must", applies_from: "2027-12-02", citations: ["art:11"],
      title: t("Technical documentation", "Documentazione tecnica"), summary: t("Draw up and keep up to date the technical documentation before the system is placed on the market ([[art:11]]).", "Redigere e tenere aggiornata la documentazione tecnica prima dell'immissione sul mercato ([[art:11]]).") },
    { id: "ob-oversight", role: "deployer", category: "oversight", priority: "must", applies_from: "2027-12-02", citations: ["art:26", "art:14"],
      title: t("Assign human oversight", "Affidare la sorveglianza umana"), summary: t("Give oversight to people with the necessary competence, training and authority ([[art:26]], [[art:14]]).", "Affidare la sorveglianza a persone con competenza, formazione e autorità necessarie ([[art:26]], [[art:14]]).") },
    { id: "ob-logs", role: "deployer", category: "monitoring", priority: "must", applies_from: "2027-12-02", citations: ["art:26"],
      title: t("Keep system logs", "Conservare i log del sistema"), summary: t("Keep automatically generated logs for at least six months ([[art:26]]).", "Conservare i log generati automaticamente per almeno sei mesi ([[art:26]]).") },
    { id: "ob-fria", role: "deployer", category: "governance", priority: "should", applies_from: "2027-12-02", citations: ["art:27"],
      title: t("Fundamental rights impact assessment", "Valutazione d'impatto sui diritti fondamentali"), summary: t("Only if you are a public body or provide public services: certain deployers must assess the impact on fundamental rights before first use ([[art:27]]).", "Solo se siete un ente pubblico o fornite servizi pubblici: alcuni deployer devono valutare l'impatto sui diritti fondamentali prima del primo utilizzo ([[art:27]]).") },
    { id: "ob-literacy", role: "both", category: "literacy", priority: "must", applies_from: "2025-02-02", citations: ["art:4"],
      title: t("AI literacy of staff", "Alfabetizzazione del personale in materia di IA"), summary: t("Ensure a sufficient level of AI literacy among people operating the system ([[art:4]]).", "Garantire un livello sufficiente di alfabetizzazione in materia di IA tra chi gestisce il sistema ([[art:4]]).") },
    { id: "ob-inform", role: "deployer", category: "transparency", priority: "must", applies_from: "2027-12-02", citations: ["art:86"],
      title: t("Explain decisions to candidates", "Spiegare le decisioni ai candidati"), summary: t("Give affected people clear explanations of the system's role in decisions ([[art:86]]).", "Fornire alle persone interessate spiegazioni chiare sul ruolo del sistema nelle decisioni ([[art:86]]).") },
  ];
  const checklist: ChecklistItem[] = [
    { id: "ck-inventory", title: t("Inventory the system and its purpose", "Censire il sistema e la sua finalità"), description: t("Write down what the tool does, who uses it and on whom.", "Descrivere cosa fa lo strumento, chi lo usa e su chi."), citations: ["annex:III.4.a"], obligation_ids: ["ob-rms"], template_hint: t("One-page system card: purpose, users, affected people, vendor.", "Scheda di sistema di una pagina: finalità, utenti, persone interessate, fornitore.") },
    { id: "ck-oversight", title: t("Name the people who oversee the tool", "Individuare le persone che supervisionano lo strumento"), description: t("Assign trained reviewers who can override or ignore the ranking.", "Assegnare revisori formati che possano ignorare o modificare la classifica."), citations: ["art:26", "art:14"], obligation_ids: ["ob-oversight"], template_hint: null },
    { id: "ck-logs", title: t("Set up six-month log retention", "Impostare la conservazione dei log per sei mesi"), description: t("Confirm with the vendor that logs are available and stored.", "Verificare con il fornitore che i log siano disponibili e conservati."), citations: ["art:26"], obligation_ids: ["ob-logs"], template_hint: null },
    { id: "ck-instructions", title: t("Obtain and follow the instructions for use", "Ottenere e seguire le istruzioni per l'uso"), description: t("Request the provider's instructions for use and technical documentation summary.", "Richiedere al fornitore le istruzioni per l'uso e una sintesi della documentazione tecnica."), citations: ["art:26", "art:11"], obligation_ids: ["ob-doc"], template_hint: t("Vendor questionnaire covering Annex IV headings.", "Questionario al fornitore sulle voci dell'Allegato IV.") },
    { id: "ck-fria", title: t("Run a fundamental rights impact assessment", "Svolgere una valutazione d'impatto sui diritti fondamentali"), description: t("Document risks to candidates and mitigation measures before go-live.", "Documentare i rischi per i candidati e le misure di mitigazione prima dell'avvio."), citations: ["art:27"], obligation_ids: ["ob-fria"], template_hint: null },
    { id: "ck-notice", title: t("Tell candidates an AI tool is used", "Informare i candidati dell'uso di uno strumento di IA"), description: t("Add a clear notice and a contact for explanation requests.", "Aggiungere un'informativa chiara e un contatto per le richieste di spiegazione."), citations: ["art:86"], obligation_ids: ["ob-inform"], template_hint: t("Short notice for the careers page and application form.", "Breve informativa per la pagina carriere e il modulo di candidatura.") },
    { id: "ck-training", title: t("Train staff on AI literacy", "Formare il personale sull'alfabetizzazione in materia di IA"), description: t("Short training for recruiters on limits and bias of the tool.", "Breve formazione per i selezionatori su limiti e distorsioni dello strumento."), citations: ["art:4"], obligation_ids: ["ob-literacy"], template_hint: null },
  ];
  return build("cv-screening", lang, description, classification, reasoning, obligations, checklist,
    [{ id: "rec:57", why: t("Explains why employment systems are high-risk.", "Spiega perché i sistemi per l'occupazione sono ad alto rischio.") }, { id: "art:6.3", why: t("The derogation you may want to test.", "La deroga che potresti voler verificare.") }],
    unknown ? [t("Not stated: whether the ranking decides who is interviewed.", "Non indicato: se la classifica decide chi viene convocato.")] : [],
    { role, sector: "employment", decision_impact: (answers.decision_impact ?? null) as FactValue });
}

// ---------- Chatbot: limited risk ----------
function chatbotAssessment(lang: Lang, description: string): Assessment {
  const classification: Classification = {
    tier: "limited_risk", confidence: "high", role: "provider",
    findings: [{
      rule_id: "art50.1-interaction", kind: "transparency", decisive: true,
      title: t("The system interacts directly with people", "Il sistema interagisce direttamente con le persone"),
      rationale: t("A chatbot intended to interact with natural persons must tell them they are talking to an AI system ([[art:50.1]]).", "Un chatbot destinato a interagire con persone fisiche deve informarle che stanno interagendo con un sistema di IA ([[art:50.1]]).") ,
      citations: ["art:50.1"], facts_used: ["interacts_with_people"],
    }],
    overlays: { transparency_art50: ["art:50.1"], ...(/language model|modello linguistico|llm/i.test(description) ? { gpai: ["art:53"] } : {}) }, applies_from: ms("m-2026-08-02"), unresolved: [], assumptions: [],
  };
  const reasoning = lang === "it"
    ? `## Perché questo livello di rischio\n\nIl chatbot **dialoga direttamente con i clienti**. Non rientra in nessun caso d'uso ad alto rischio, ma l'[[art:50.1]] impone di informare le persone che stanno interagendo con un sistema di IA, salvo che sia ovvio.\n\nIl [[rec:132]] chiarisce che l'obbligo serve a prevenire inganno e impersonificazione.\n\n## Cosa fare\n\nMostra un avviso chiaro all'inizio della conversazione. Gli obblighi di trasparenza si applicano dal **2 agosto 2026**, quindi sono già in vigore.`
    : `## Why this risk tier\n\nYour chatbot **talks directly to customers**. It does not fall under a high-risk use case, but [[art:50.1]] requires people to be told they are interacting with an AI system, unless that is obvious.\n\n[[rec:132]] explains that the duty exists to prevent deception and impersonation.\n\n## What to do\n\nShow a clear notice at the start of the conversation. Transparency duties apply from **2 August 2026**, so they are already in force.`;
  const obligations: Obligation[] = [
    { id: "ob-disclose", role: "provider", category: "transparency", priority: "must", applies_from: "2026-08-02", citations: ["art:50.1"],
      title: t("Tell users they are talking to an AI", "Informare gli utenti che parlano con un'IA"), summary: t("Design the chatbot so users are informed at the start ([[art:50.1]]).", "Progettare il chatbot in modo che gli utenti siano informati all'inizio ([[art:50.1]]).") },
    { id: "ob-literacy2", role: "both", category: "literacy", priority: "should", applies_from: "2025-02-02", citations: ["art:4"],
      title: t("AI literacy of staff", "Alfabetizzazione del personale in materia di IA"), summary: t("Make sure staff running the bot understand its limits ([[art:4]]).", "Assicurarsi che chi gestisce il bot ne comprenda i limiti ([[art:4]]).") },
  ];
  const checklist: ChecklistItem[] = [
    { id: "ck-notice", title: t("Add an AI disclosure to the chat window", "Aggiungere un'informativa sull'IA nella finestra di chat"), description: t("A visible line such as \"You are chatting with an AI assistant\".", "Una riga ben visibile come \"Stai parlando con un assistente IA\"."), citations: ["art:50.1"], obligation_ids: ["ob-disclose"], template_hint: t("\"You are chatting with an AI assistant. A human can take over on request.\"", "\"Stai parlando con un assistente IA. Un operatore può subentrare su richiesta.\"") },
    { id: "ck-handoff", title: t("Offer a way to reach a human", "Offrire un modo per contattare una persona"), description: t("Good practice, not required by Article 50.", "Buona prassi, non richiesta dall'articolo 50."), citations: [], obligation_ids: [], template_hint: null },
  ];
  return build("customer-chatbot", lang, description, classification, reasoning, obligations, checklist,
    [{ id: "rec:132", why: t("Background on the transparency duty.", "Contesto dell'obbligo di trasparenza.") }], [], { role: "provider", interacts_with_people: true });
}

// ---------- Emotion recognition at work: prohibited ----------
function emotionAssessment(lang: Lang, description: string): Assessment {
  const classification: Classification = {
    tier: "prohibited", confidence: "high", role: "deployer",
    findings: [{
      rule_id: "art5.1.f-emotion-workplace", kind: "prohibition", decisive: true,
      title: t("Emotion recognition in the workplace", "Riconoscimento delle emozioni sul luogo di lavoro"),
      rationale: t("Inferring employees' emotions from facial expressions at work is banned by [[art:5.1.f]], and there is no medical or safety reason in the description.", "Inferire le emozioni dei dipendenti dalle espressioni facciali sul lavoro è vietato dall'[[art:5.1.f]] e la descrizione non indica motivi medici o di sicurezza."),
      citations: ["art:5.1.f", "rec:44"], facts_used: ["biometric.emotion_recognition", "context.workplace"],
    }],
    overlays: {}, applies_from: ms("m-2025-02-02"), unresolved: [], assumptions: [t("We assumed no medical or safety purpose.", "Abbiamo ipotizzato l'assenza di finalità mediche o di sicurezza.")],
  };
  const reasoning = lang === "it"
    ? `## Perché questo livello di rischio\n\nIl software **deduce lo stato emotivo dei dipendenti** dalle loro espressioni facciali durante il lavoro. L'[[art:5.1.f]] vieta questa pratica, salvo motivi medici o di sicurezza. Il [[rec:44]] ne spiega le ragioni scientifiche ed etiche, e gli orientamenti della Commissione ([[guid:prohibited-2025.7]]) confermano che il divieto copre anche l'assunzione.\n\n## Cosa significa\n\nIl sistema **non può essere immesso sul mercato né usato** nell'UE. Il divieto si applica dal **2 febbraio 2025**. Valuta alternative che non inferiscano emozioni, ad esempio sondaggi volontari e anonimi sul benessere.`
    : `## Why this risk tier\n\nThe software **infers employees' emotional states** from their facial expressions at work. [[art:5.1.f]] bans this practice unless it serves a medical or safety purpose. [[rec:44]] sets out the scientific and ethical reasons, and the Commission guidelines ([[guid:prohibited-2025.7]]) confirm the ban also covers recruitment.\n\n## What this means\n\nThe system **cannot be placed on the market or used** in the EU. The ban has applied since **2 February 2025**. Consider alternatives that do not infer emotions, such as voluntary, anonymous wellbeing surveys.`;
  const obligations: Obligation[] = [
    { id: "ob-stop", role: "deployer", category: "governance", priority: "must", applies_from: "2025-02-02", citations: ["art:5.1.f"],
      title: t("Do not deploy the system", "Non utilizzare il sistema"), summary: t("The practice is prohibited; fines for breaches of Article 5 are the highest in the Act ([[art:5.1.f]]).", "La pratica è vietata; le sanzioni per le violazioni dell'articolo 5 sono le più alte del regolamento ([[art:5.1.f]]).") },
  ];
  const checklist: ChecklistItem[] = [
    { id: "ck-stop", title: t("Stop the project or remove emotion inference", "Interrompere il progetto o eliminare l'inferenza di emozioni"), description: t("Confirm with your legal team before any pilot starts.", "Confermare con l'ufficio legale prima di avviare qualsiasi pilota."), citations: ["art:5.1.f"], obligation_ids: ["ob-stop"], template_hint: null },
    { id: "ck-alt", title: t("Review lawful alternatives", "Valutare alternative lecite"), description: t("For example opt-in, anonymous surveys that do not analyse faces.", "Ad esempio sondaggi anonimi e volontari che non analizzano i volti."), citations: [], obligation_ids: [], template_hint: null },
  ];
  return build("emotion-workplace", lang, description, classification, reasoning, obligations, checklist,
    [{ id: "guid:prohibited-2025.7", why: t("Commission guidance on this prohibition.", "Orientamenti della Commissione su questo divieto.") }], [], { role: "deployer", biometric: { emotion_recognition: true } });
}

// ---------- Minimal risk: fallback ----------
function minimalAssessment(lang: Lang, description: string): Assessment {
  const classification: Classification = {
    tier: "minimal_risk", confidence: "medium", role: "deployer",
    findings: [{
      rule_id: "no-match", kind: "note", decisive: true,
      title: t("No prohibition, Annex III use case or transparency trigger found", "Nessun divieto, caso d'uso dell'Allegato III o obbligo di trasparenza rilevato"),
      rationale: t("Nothing in the description matches [[art:5]], [[annex:III]] or [[art:50]].", "Nulla nella descrizione corrisponde all'[[art:5]], all'[[annex:III]] o all'[[art:50]]."),
      citations: ["art:5", "annex:III", "art:50"], facts_used: [],
    }],
    overlays: {}, applies_from: ms("m-2025-02-02"), unresolved: [], assumptions: [t("Nothing in the description suggests that the system affects people's rights or safety, so we assumed it does not.", "Nulla nella descrizione suggerisce che il sistema incida su diritti o sicurezza delle persone, quindi abbiamo ipotizzato di no.")],
  };
  const reasoning = lang === "it"
    ? `## Perché questo livello di rischio\n\nIl sistema descritto non rientra tra le pratiche vietate ([[art:5]]), non è elencato nell'[[annex:III]] e non attiva obblighi di trasparenza ([[art:50]]). Resta l'obbligo generale di alfabetizzazione ([[art:4]]).`
    : `## Why this risk tier\n\nThe system you describe is not a prohibited practice ([[art:5]]), is not listed in [[annex:III]] and does not trigger transparency duties ([[art:50]]). The general AI literacy duty in [[art:4]] still applies.`;
  const obligations: Obligation[] = [
    { id: "ob-literacy3", role: "both", category: "literacy", priority: "must", applies_from: "2025-02-02", citations: ["art:4"],
      title: t("AI literacy of staff", "Alfabetizzazione del personale in materia di IA"), summary: t("Ensure sufficient AI literacy of staff ([[art:4]]).", "Garantire un livello sufficiente di alfabetizzazione del personale ([[art:4]]).") },
  ];
  const checklist: ChecklistItem[] = [
    { id: "ck-literacy", title: t("Give staff a short AI literacy briefing", "Offrire al personale una breve formazione sull'IA"), description: t("A one-hour session is a reasonable starting point.", "Una sessione di un'ora è un buon punto di partenza."), citations: ["art:4"], obligation_ids: ["ob-literacy3"], template_hint: null },
  ];
  return build("minimal", lang, description, classification, reasoning, obligations, checklist, [], [], { role: "deployer" });
}

function build(
  key: string, lang: Lang, description: string, classification: Classification, reasoning_md: string,
  obligations: Obligation[], checklist: ChecklistItem[], related: Assessment["related_provisions"],
  uncertainties: LText[], facts: FactSheet,
): Assessment {
  return {
    id: `mock-${key}-${lang}`, created_at: new Date().toISOString(), language: lang,
    law_as_of: "2026-07-27", checked_at: "2026-11-03",
    model: { provider: "mock", model: "fixture-v1" },
    description, facts, classification, reasoning_md, obligations, checklist,
    related_provisions: related, uncertainties, disclaimer: DISCLAIMER,
    metrics: { latency_ms: 4200, llm_calls: 2, input_tokens: 2100, output_tokens: 640, cost_usd: key === "cv-screening" ? 0.054 : 0, cached: false },
  };
}

export type Scenario = "cv" | "chatbot" | "emotion" | "minimal";

export function pickScenario(description: string): Scenario {
  const d = description.toLowerCase();
  if (/emotion|emozion|mood|umore|stress|social scor|punteggio sociale/.test(d)) return "emotion";
  if (/\bcv\b|resume|candidat|hiring|recruit|credit|loan|prestit|exam|esam|medical|radiolog|x-ray|radiograf/.test(d)) return "cv";
  if (/chatbot|avatar|deepfake|synthetic|language model|modello linguistico|llm/.test(d)) return "chatbot";
  return "minimal";
}

export function buildMockAssessment(scenario: Scenario, lang: Lang, description: string, answers: Record<string, unknown>): Assessment {
  switch (scenario) {
    case "cv": return cvAssessment(lang, description, answers);
    case "chatbot": return chatbotAssessment(lang, description);
    case "emotion": return emotionAssessment(lang, description);
    default: return minimalAssessment(lang, description);
  }
}

export const TIER_OF: Record<Scenario, Tier> = { cv: "high_risk", chatbot: "limited_risk", emotion: "prohibited", minimal: "minimal_risk" };
