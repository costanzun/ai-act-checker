import type { ExampleItem, Lang, Tier } from "../types";

interface Ex { id: string; tier: Tier; tags: string[]; overlays?: string[]; en: [string, string, string]; it: [string, string, string] }

// [title, one-line description, full description sent to the assessment]
const EX: Ex[] = [
  { id: "cv-screening", tier: "high_risk", tags: ["employment", "annex_iii"],
    en: ["CV screening tool", "Ranks job applicants for an HR department.", "Our HR department uses software that scores and ranks CVs from job applicants and shortlists the best candidates for interviews."],
    it: ["Selezione dei CV", "Classifica i candidati per l'ufficio HR.", "Il nostro ufficio HR usa un software che assegna un punteggio ai CV dei candidati, li classifica e prepara la lista ristretta per i colloqui."] },
  { id: "customer-chatbot", tier: "limited_risk", tags: ["transparency", "art50"],
    en: ["Customer support chatbot", "Answers customer questions on a web shop.", "We run a chatbot on our web shop that answers customer questions about orders and returns in natural language."],
    it: ["Chatbot per l'assistenza clienti", "Risponde alle domande dei clienti di un negozio online.", "Gestiamo un chatbot nel nostro negozio online che risponde in linguaggio naturale alle domande dei clienti su ordini e resi."] },
  { id: "emotion-workplace", tier: "prohibited", tags: ["art5", "biometrics"],
    en: ["Emotion recognition at work", "Reads employees' mood from webcams.", "We want to install software that analyses employees' facial expressions on their webcams during the working day to detect stress and low motivation."],
    it: ["Riconoscimento delle emozioni al lavoro", "Rileva l'umore dei dipendenti dalle webcam.", "Vogliamo installare un software che analizza le espressioni facciali dei dipendenti tramite webcam durante l'orario di lavoro per rilevare stress e scarsa motivazione."] },
  { id: "spam-filter", tier: "minimal_risk", tags: ["minimal"],
    en: ["Email spam filter", "Sorts unwanted email for a company.", "Our IT team uses a machine-learning filter that moves unwanted promotional email into a spam folder."],
    it: ["Filtro antispam", "Smista la posta indesiderata di un'azienda.", "Il nostro team IT usa un filtro basato su machine learning che sposta la posta promozionale indesiderata nella cartella spam."] },
  { id: "credit-scoring", tier: "high_risk", tags: ["finance", "annex_iii"],
    en: ["Credit scoring", "Assesses consumers' creditworthiness.", "Our bank uses a model to assess the creditworthiness of private individuals applying for personal loans."],
    it: ["Scoring creditizio", "Valuta l'affidabilità creditizia dei consumatori.", "La nostra banca usa un modello per valutare l'affidabilità creditizia delle persone fisiche che richiedono prestiti personali."] },
  { id: "exam-proctoring", tier: "high_risk", tags: ["education", "annex_iii"],
    en: ["Exam proctoring", "Flags suspected cheating in online exams.", "A university uses software that monitors students during online exams and flags behaviour that looks like cheating."],
    it: ["Sorveglianza degli esami", "Segnala possibili casi di copiatura negli esami online.", "Un'università usa un software che monitora gli studenti durante gli esami online e segnala comportamenti che sembrano copiatura."] },
  { id: "deepfake-marketing", tier: "limited_risk", tags: ["transparency", "art50"],
    en: ["Synthetic video ads", "Generates AI avatars for marketing.", "Our marketing team generates videos with realistic AI avatars that speak to customers in product ads."],
    it: ["Video pubblicitari sintetici", "Genera avatar IA per il marketing.", "Il nostro team marketing genera video con avatar IA realistici che parlano ai clienti negli annunci di prodotto."] },
  { id: "predictive-maintenance", tier: "minimal_risk", tags: ["minimal", "industry"],
    en: ["Predictive maintenance", "Predicts machine failures in a factory.", "We use sensor data and machine learning to predict when factory machines need servicing."],
    it: ["Manutenzione predittiva", "Prevede i guasti dei macchinari in fabbrica.", "Usiamo dati dei sensori e machine learning per prevedere quando i macchinari di fabbrica richiedono manutenzione."] },
  { id: "medical-triage", tier: "high_risk", tags: ["health", "annex_i"],
    en: ["Medical imaging triage", "Prioritises radiology scans.", "We sell software that analyses X-ray images and ranks them by urgency for radiologists in hospitals."],
    it: ["Triage di diagnostica per immagini", "Dà priorità alle radiografie.", "Vendiamo un software che analizza le radiografie e le ordina per urgenza per i radiologi degli ospedali."] },
  { id: "social-scoring", tier: "prohibited", tags: ["art5"],
    en: ["Citizen social scoring", "Scores people on social behaviour.", "A city wants to score residents based on their social behaviour and give or deny access to public services accordingly."],
    it: ["Punteggio sociale dei cittadini", "Assegna punteggi in base al comportamento sociale.", "Un comune vuole assegnare ai residenti un punteggio in base al comportamento sociale e concedere o negare servizi pubblici di conseguenza."] },
  { id: "gpai-model", tier: "limited_risk", tags: ["gpai"], overlays: ["gpai"],
    en: ["General-purpose language model", "Trains and releases a foundation model.", "We train a large language model and make it available to developers through an API."],
    it: ["Modello linguistico generale", "Addestra e distribuisce un modello di base.", "Addestriamo un grande modello linguistico e lo mettiamo a disposizione degli sviluppatori tramite API."] },
  { id: "research-only", tier: "out_of_scope", tags: ["scope"],
    en: ["Pure research prototype", "Used only for scientific research.", "Our lab develops a model solely for scientific research and it is never placed on the market or put into service."],
    it: ["Prototipo di sola ricerca", "Usato esclusivamente per la ricerca scientifica.", "Il nostro laboratorio sviluppa un modello esclusivamente per la ricerca scientifica e non viene mai immesso sul mercato né messo in servizio."] },
];

export function mockExamples(lang: Lang): ExampleItem[] {
  return EX.map((e) => ({ id: e.id, title: e[lang][0], description: e[lang][1], tags: e.tags, expected_tier: e.tier, text: e[lang][2], ...(e.overlays ? { expected_overlays: e.overlays } : {}) }));
}

export function mockExampleText(id: string, lang: Lang): string | null {
  const e = EX.find((x) => x.id === id);
  return e ? e[lang][2] : null;
}

/** Full text lookup used by the assess page when navigated with ?example=<id> (mock only). */
export const MOCK_EXAMPLE_TIER = (id: string): Tier | null => EX.find((x) => x.id === id)?.tier ?? null;
