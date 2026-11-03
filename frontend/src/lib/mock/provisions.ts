import type { Amendment, Lang, LawResponse, Provision } from "../types";

interface Raw {
  id: string;
  type: string;
  parent?: string;
  label: { en: string; it: string };
  title?: { en: string; it: string };
  text: { en: string; it: string };
  amendment?: Amendment;
}

const M1 = (kind: Amendment["kind"]): Amendment => ({ marker: "M1", kind, by: "32026R1744" });

// Abridged texts for demo purposes only; the real backend serves the consolidated corpus.
const RAW: Raw[] = [
  { id: "art:4", type: "article", label: { en: "Art. 4", it: "Art. 4" }, title: { en: "AI literacy", it: "Alfabetizzazione in materia di IA" },
    text: { en: "Providers and deployers of AI systems shall take measures to ensure, to their best extent, a sufficient level of AI literacy of their staff and other persons dealing with the operation and use of AI systems on their behalf.", it: "I fornitori e i deployer dei sistemi di IA adottano misure per garantire, nella misura del possibile, un livello sufficiente di alfabetizzazione in materia di IA del loro personale e delle altre persone che si occupano del funzionamento e dell'utilizzo dei sistemi di IA per loro conto." },
    amendment: M1("replaced") },
  { id: "art:5", type: "article", label: { en: "Art. 5", it: "Art. 5" }, title: { en: "Prohibited AI practices", it: "Pratiche di IA vietate" },
    text: { en: "Prohibited AI practices", it: "Pratiche di IA vietate" } },
  { id: "art:5.1", type: "paragraph", parent: "art:5", label: { en: "Art. 5(1)", it: "Art. 5, par. 1" }, title: { en: "Prohibited AI practices", it: "Pratiche di IA vietate" },
    text: { en: "The following AI practices shall be prohibited:", it: "Sono vietate le seguenti pratiche di IA:" } },
  { id: "art:5.1.f", type: "point", parent: "art:5.1", label: { en: "Art. 5(1)(f)", it: "Art. 5, par. 1, lett. f)" }, title: { en: "Prohibited AI practices", it: "Pratiche di IA vietate" },
    text: { en: "the placing on the market, the putting into service for this specific purpose, or the use of AI systems to infer emotions of a natural person in the areas of workplace and education institutions, except where the use of the AI system is intended to be put in place or into the market for medical or safety reasons;", it: "l'immissione sul mercato, la messa in servizio per tale finalità specifica o l'uso di sistemi di IA per inferire le emozioni di una persona fisica nell'ambito del luogo di lavoro e degli istituti di istruzione, tranne laddove l'uso del sistema di IA sia destinato a essere messo in funzione o immesso sul mercato per motivi medici o di sicurezza;" } },
  { id: "art:6", type: "article", label: { en: "Art. 6", it: "Art. 6" }, title: { en: "Classification rules for high-risk AI systems", it: "Regole di classificazione per i sistemi di IA ad alto rischio" },
    text: { en: "Classification rules for high-risk AI systems", it: "Regole di classificazione per i sistemi di IA ad alto rischio" } },
  { id: "art:6.2", type: "paragraph", parent: "art:6", label: { en: "Art. 6(2)", it: "Art. 6, par. 2" }, title: { en: "Classification rules for high-risk AI systems", it: "Regole di classificazione per i sistemi di IA ad alto rischio" },
    text: { en: "In addition to the high-risk AI systems referred to in paragraph 1, AI systems referred to in Annex III shall be considered to be high-risk.", it: "Oltre ai sistemi di IA ad alto rischio di cui al paragrafo 1, sono considerati ad alto rischio i sistemi di IA di cui all'allegato III." } },
  { id: "art:6.3", type: "paragraph", parent: "art:6", label: { en: "Art. 6(3)", it: "Art. 6, par. 3" }, title: { en: "Classification rules for high-risk AI systems", it: "Regole di classificazione per i sistemi di IA ad alto rischio" },
    text: { en: "By derogation from paragraph 2, an AI system referred to in Annex III shall not be considered to be high-risk where it does not pose a significant risk of harm to the health, safety or fundamental rights of natural persons, including by not materially influencing the outcome of decision making. An AI system referred to in Annex III shall always be considered to be high-risk where it performs profiling of natural persons.", it: "In deroga al paragrafo 2, un sistema di IA di cui all'allegato III non è considerato ad alto rischio se non presenta un rischio significativo di danno per la salute, la sicurezza o i diritti fondamentali delle persone fisiche, anche non influenzando materialmente il risultato del processo decisionale. Un sistema di IA di cui all'allegato III è sempre considerato ad alto rischio qualora effettui profilazione di persone fisiche." } },
  { id: "art:9", type: "article", label: { en: "Art. 9", it: "Art. 9" }, title: { en: "Risk management system", it: "Sistema di gestione dei rischi" },
    text: { en: "A risk management system shall be established, implemented, documented and maintained in relation to high-risk AI systems. It shall be a continuous iterative process planned and run throughout the entire lifecycle of a high-risk AI system.", it: "Un sistema di gestione dei rischi è istituito, attuato, documentato e mantenuto in relazione ai sistemi di IA ad alto rischio. Esso è inteso come un processo iterativo continuo pianificato ed eseguito nel corso dell'intero ciclo di vita del sistema di IA ad alto rischio." } },
  { id: "art:10", type: "article", label: { en: "Art. 10", it: "Art. 10" }, title: { en: "Data and data governance", it: "Dati e governance dei dati" },
    text: { en: "High-risk AI systems which make use of techniques involving the training of AI models with data shall be developed on the basis of training, validation and testing data sets that meet the quality criteria referred to in paragraphs 2 to 5.", it: "I sistemi di IA ad alto rischio che utilizzano tecniche che prevedono l'addestramento di modelli di IA con dati sono sviluppati sulla base di set di dati di addestramento, convalida e prova che soddisfano i criteri di qualità di cui ai paragrafi da 2 a 5." } },
  { id: "art:11", type: "article", label: { en: "Art. 11", it: "Art. 11" }, title: { en: "Technical documentation", it: "Documentazione tecnica" },
    text: { en: "The technical documentation of a high-risk AI system shall be drawn up before that system is placed on the market or put into service and shall be kept up-to date.", it: "La documentazione tecnica di un sistema di IA ad alto rischio è redatta prima dell'immissione sul mercato o della messa in servizio del sistema ed è tenuta aggiornata." } },
  { id: "art:14", type: "article", label: { en: "Art. 14", it: "Art. 14" }, title: { en: "Human oversight", it: "Sorveglianza umana" },
    text: { en: "High-risk AI systems shall be designed and developed in such a way, including with appropriate human-machine interface tools, that they can be effectively overseen by natural persons during the period in which they are in use.", it: "I sistemi di IA ad alto rischio sono progettati e sviluppati, anche con strumenti di interfaccia uomo-macchina adeguati, in modo tale da poter essere supervisionati efficacemente da persone fisiche durante il periodo in cui sono in uso." } },
  { id: "art:26", type: "article", label: { en: "Art. 26", it: "Art. 26" }, title: { en: "Obligations of deployers of high-risk AI systems", it: "Obblighi dei deployer di sistemi di IA ad alto rischio" },
    text: { en: "Deployers of high-risk AI systems shall take appropriate technical and organisational measures to ensure they use such systems in accordance with the instructions for use accompanying the systems. Deployers shall assign human oversight to natural persons who have the necessary competence, training and authority, and shall keep the logs automatically generated by the system for at least six months.", it: "I deployer di sistemi di IA ad alto rischio adottano misure tecniche e organizzative adeguate per garantire di utilizzare tali sistemi conformemente alle istruzioni per l'uso. I deployer affidano la sorveglianza umana a persone fisiche che dispongono della competenza, della formazione e dell'autorità necessarie e conservano i log generati automaticamente dal sistema per almeno sei mesi." } },
  { id: "art:27", type: "article", label: { en: "Art. 27", it: "Art. 27" }, title: { en: "Fundamental rights impact assessment", it: "Valutazione d'impatto sui diritti fondamentali" },
    text: { en: "Prior to deploying a high-risk AI system referred to in Article 6(2), certain deployers shall perform an assessment of the impact on fundamental rights that the use of such system may produce.", it: "Prima di utilizzare un sistema di IA ad alto rischio di cui all'articolo 6, paragrafo 2, determinati deployer effettuano una valutazione dell'impatto sui diritti fondamentali che l'uso di tale sistema può produrre." } },
  { id: "art:50", type: "article", label: { en: "Art. 50", it: "Art. 50" }, title: { en: "Transparency obligations for providers and deployers of certain AI systems", it: "Obblighi di trasparenza per i fornitori e i deployer di determinati sistemi di IA" },
    text: { en: "Transparency obligations for providers and deployers of certain AI systems", it: "Obblighi di trasparenza per i fornitori e i deployer di determinati sistemi di IA" } },
  { id: "art:50.1", type: "paragraph", parent: "art:50", label: { en: "Art. 50(1)", it: "Art. 50, par. 1" }, title: { en: "Transparency obligations for providers and deployers of certain AI systems", it: "Obblighi di trasparenza per i fornitori e i deployer di determinati sistemi di IA" },
    text: { en: "Providers shall ensure that AI systems intended to interact directly with natural persons are designed and developed in such a way that the natural persons concerned are informed that they are interacting with an AI system, unless this is obvious from the point of view of a natural person who is reasonably well-informed, observant and circumspect.", it: "I fornitori garantiscono che i sistemi di IA destinati a interagire direttamente con persone fisiche siano progettati e sviluppati in modo tale che le persone fisiche interessate siano informate di stare interagendo con un sistema di IA, a meno che ciò non risulti evidente dal punto di vista di una persona fisica ragionevolmente informata, attenta e avveduta." } },
  { id: "art:50.3", type: "paragraph", parent: "art:50", label: { en: "Art. 50(3)", it: "Art. 50, par. 3" }, title: { en: "Transparency obligations for providers and deployers of certain AI systems", it: "Obblighi di trasparenza per i fornitori e i deployer di determinati sistemi di IA" },
    text: { en: "Deployers of an emotion recognition system or a biometric categorisation system shall inform the natural persons exposed thereto of the operation of the system.", it: "I deployer di un sistema di riconoscimento delle emozioni o di un sistema di categorizzazione biometrica informano le persone fisiche che vi sono esposte del funzionamento del sistema." } },
  { id: "art:86", type: "article", label: { en: "Art. 86", it: "Art. 86" }, title: { en: "Right to explanation of individual decision-making", it: "Diritto alla spiegazione dei singoli processi decisionali" },
    text: { en: "Any affected person subject to a decision which is taken by the deployer on the basis of the output from a high-risk AI system listed in Annex III shall have the right to obtain from the deployer clear and meaningful explanations of the role of the AI system in the decision-making procedure.", it: "Qualsiasi persona interessata oggetto di una decisione adottata dal deployer sulla base dell'output di un sistema di IA ad alto rischio elencato nell'allegato III ha il diritto di ottenere dal deployer spiegazioni chiare e significative sul ruolo del sistema di IA nella procedura decisionale." } },
  { id: "art:113", type: "article", label: { en: "Art. 113", it: "Art. 113" }, title: { en: "Entry into force and application", it: "Entrata in vigore e applicazione" },
    text: { en: "This Regulation shall apply from 2 August 2026. However, Chapters I and II shall apply from 2 February 2025; the obligations for high-risk AI systems referred to in Annex III shall apply from 2 December 2027, and those referred to in Annex I from 2 August 2028.", it: "Il presente regolamento si applica a decorrere dal 2 agosto 2026. Tuttavia, i capi I e II si applicano a decorrere dal 2 febbraio 2025; gli obblighi per i sistemi di IA ad alto rischio di cui all'allegato III si applicano dal 2 dicembre 2027 e quelli di cui all'allegato I dal 2 agosto 2028." },
    amendment: M1("replaced") },
  { id: "annex:III", type: "annex", label: { en: "Annex III", it: "Allegato III" }, title: { en: "High-risk AI systems referred to in Article 6(2)", it: "Sistemi di IA ad alto rischio di cui all'articolo 6, paragrafo 2" },
    text: { en: "High-risk AI systems pursuant to Article 6(2) are the AI systems listed in any of the following areas:", it: "I sistemi di IA ad alto rischio a norma dell'articolo 6, paragrafo 2, sono i sistemi di IA elencati in uno dei seguenti settori:" } },
  { id: "annex:III.4", type: "annex_point", parent: "annex:III", label: { en: "Annex III, point 4", it: "Allegato III, punto 4" }, title: { en: "Employment, workers' management and access to self-employment", it: "Occupazione, gestione dei lavoratori e accesso al lavoro autonomo" },
    text: { en: "Employment, workers' management and access to self-employment:", it: "Occupazione, gestione dei lavoratori e accesso al lavoro autonomo:" } },
  { id: "annex:III.4.a", type: "annex_point", parent: "annex:III.4", label: { en: "Annex III, point 4(a)", it: "Allegato III, punto 4, lett. a)" }, title: { en: "Employment, workers' management and access to self-employment", it: "Occupazione, gestione dei lavoratori e accesso al lavoro autonomo" },
    text: { en: "AI systems intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates;", it: "sistemi di IA destinati a essere utilizzati per l'assunzione o la selezione di persone fisiche, in particolare per pubblicare annunci di lavoro mirati, analizzare e filtrare le candidature e valutare i candidati;" } },
  { id: "rec:44", type: "recital", label: { en: "Recital 44", it: "Considerando 44" },
    text: { en: "There are serious concerns about the scientific basis of AI systems aiming to identify or infer emotions, particularly as expression of emotions vary considerably across cultures and situations. The placing on the market, putting into service or use of AI systems intended to detect the emotional state of individuals in situations related to the workplace and education should be prohibited.", it: "Vi sono serie preoccupazioni in merito alla base scientifica dei sistemi di IA che mirano a rilevare o dedurre le emozioni, in particolare perché l'espressione delle emozioni varia notevolmente tra culture e situazioni. Dovrebbero essere vietati l'immissione sul mercato, la messa in servizio o l'uso di sistemi di IA destinati a rilevare lo stato emotivo delle persone in situazioni relative al luogo di lavoro e all'istruzione." } },
  { id: "rec:57", type: "recital", label: { en: "Recital 57", it: "Considerando 57" },
    text: { en: "AI systems used in employment, workers management and access to self-employment, in particular for the recruitment and selection of persons, for making decisions affecting terms of the work-related relationship, promotion and termination, should be classified as high-risk, since those systems may have an appreciable impact on future career prospects and livelihoods.", it: "I sistemi di IA utilizzati nei settori dell'occupazione, della gestione dei lavoratori e dell'accesso al lavoro autonomo, in particolare per l'assunzione e la selezione delle persone, dovrebbero essere classificati come ad alto rischio, dal momento che possono avere un impatto significativo sul futuro e sulle prospettive di carriera e sui mezzi di sussistenza." } },
  { id: "rec:132", type: "recital", label: { en: "Recital 132", it: "Considerando 132" },
    text: { en: "Certain AI systems intended to interact with natural persons or to generate content may pose specific risks of impersonation or deception irrespective of whether they qualify as high-risk. Natural persons should be notified when they are interacting with an AI system.", it: "Determinati sistemi di IA destinati a interagire con persone fisiche o a generare contenuti possono comportare rischi specifici di impersonificazione o inganno, indipendentemente dal fatto che siano considerati ad alto rischio. Le persone fisiche dovrebbero essere informate quando interagiscono con un sistema di IA." } },
  { id: "guid:prohibited-2025.7", type: "guidance", label: { en: "Commission Guidelines on prohibited practices (2025), §7", it: "Orientamenti della Commissione sulle pratiche vietate (2025), §7" },
    text: { en: "The prohibition on emotion recognition in the workplace covers systems that infer emotions of employees, including during recruitment and probation. Non-binding guidance.", it: "Il divieto di riconoscimento delle emozioni sul luogo di lavoro riguarda i sistemi che inferiscono le emozioni dei dipendenti, anche durante l'assunzione e il periodo di prova. Orientamenti non vincolanti." } },
];

const BY_ID = new Map(RAW.map((r) => [r.id, r]));

const CHAPTERS: Record<string, { id: string; label: string }> = {
  art: { id: "reg", label: "Regulation (EU) 2024/1689" },
};

function toProvision(r: Raw, lang: Lang): Provision {
  return {
    id: r.id, type: r.type, label: r.label[lang], parent_id: r.parent ?? null,
    children: RAW.filter((c) => c.parent === r.id).map((c) => c.id),
    title: r.title ? r.title[lang] : null, text: r.text[lang], amendment: r.amendment ?? null,
  };
}

export function mockLaw(id: string, lang: Lang): LawResponse | null {
  const r = BY_ID.get(id);
  if (!r) return null;
  const chain: { id: string; label: string }[] = [];
  let cur: Raw | undefined = r.parent ? BY_ID.get(r.parent) : undefined;
  while (cur) { chain.unshift({ id: cur.id, label: cur.label[lang] }); cur = cur.parent ? BY_ID.get(cur.parent) : undefined; }
  const root = r.type === "recital" ? { id: "rec", label: lang === "it" ? "Considerando" : "Recitals" }
    : r.type === "guidance" ? { id: "guid", label: lang === "it" ? "Orientamenti" : "Guidance" }
    : r.id.startsWith("annex") ? { id: "annexes", label: lang === "it" ? "Allegati" : "Annexes" } : CHAPTERS.art;
  const children = RAW.filter((c) => c.parent === id).map((c) => toProvision(c, lang));
  const full = [r.text[lang], ...children.map((c) => `${c.label.replace(/^.*?(\(|,)/, "$1").trim()} ${c.text}`)].join("\n\n");
  const num = id.startsWith("art:") ? id.slice(4).split(".")[0] : "";
  return {
    provision: toProvision(r, lang),
    full_text: full,
    breadcrumb: [root, ...chain],
    children,
    eurlex_url: `https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27${num ? `#art_${num}` : ""}`,
  };
}
