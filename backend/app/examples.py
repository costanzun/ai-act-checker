"""One-click examples for the gallery (bilingual). Tiers are cross-checked by tests against the engine."""

from __future__ import annotations

EXAMPLES: list[dict] = [
    {
        "id": "cv-screening-deployer",
        "title": {"en": "CV screening for an HR department", "it": "Screening dei CV per un ufficio HR"},
        "description": {
            "en": "Our HR department in Milan uses a third-party tool that reads incoming CVs, scores candidates against the job description and ranks them. Recruiters review the top 20 and decide whom to interview.",
            "it": "Il nostro ufficio HR a Milano usa uno strumento di terzi che legge i CV ricevuti, assegna un punteggio ai candidati rispetto all'annuncio e li ordina. I recruiter esaminano i primi 20 e decidono chi convocare.",
        },
        "tags": ["employment", "Annex III"],
        "expected_tier": "high_risk",
    },
    {
        "id": "customer-service-chatbot",
        "title": {"en": "Customer-service chatbot", "it": "Chatbot per il servizio clienti"},
        "description": {
            "en": "We built a chatbot on top of a commercial large language model to answer customer questions about orders and returns on our e-commerce site. It introduces itself as a virtual assistant.",
            "it": "Abbiamo costruito un chatbot basato su un grande modello linguistico commerciale per rispondere alle domande dei clienti su ordini e resi nel nostro sito e-commerce. Si presenta come assistente virtuale.",
        },
        "tags": ["transparency", "Art. 50"],
        "expected_tier": "limited_risk",
        "expected_overlays": ['transparency_art50'],
    },
    {
        "id": "emotion-recognition-call-centre",
        "title": {"en": "Emotion recognition of call-centre staff", "it": "Riconoscimento delle emozioni degli operatori di call center"},
        "description": {
            "en": "A call-centre operator wants software that analyses agents' voices during calls to detect stress and frustration, so team leads can coach them and the scores feed into performance reviews.",
            "it": "Un operatore di call center vuole un software che analizzi la voce degli agenti durante le chiamate per rilevare stress e frustrazione, così i team leader possono fare coaching e i punteggi entrano nelle valutazioni delle prestazioni.",
        },
        "tags": ["biometrics", "workplace", "Art. 5"],
        "expected_tier": "prohibited",
    },
    {
        "id": "credit-scoring-bank",
        "title": {"en": "Consumer credit scoring at a bank", "it": "Credit scoring dei consumatori in banca"},
        "description": {
            "en": "We are a retail bank developing an in-house machine-learning model that estimates the creditworthiness of individuals applying for personal loans. The score determines approval and the interest rate automatically for small amounts.",
            "it": "Siamo una banca retail e stiamo sviluppando internamente un modello di machine learning che stima l'affidabilità creditizia delle persone che chiedono un prestito personale. Il punteggio determina automaticamente approvazione e tasso per i piccoli importi.",
        },
        "tags": ["essential services", "Annex III"],
        "expected_tier": "high_risk",
    },
    {
        "id": "spam-filter",
        "title": {"en": "Email spam filter", "it": "Filtro antispam per la posta"},
        "description": {
            "en": "Our IT team deploys a machine-learning spam filter on the company mail server. It moves suspected spam to a junk folder; employees can restore messages themselves.",
            "it": "Il nostro team IT installa un filtro antispam basato su machine learning sul server di posta aziendale. Sposta i messaggi sospetti nella cartella spam; i dipendenti possono recuperarli da soli.",
        },
        "tags": ["minimal risk"],
        "expected_tier": "minimal_risk",
    },
    {
        "id": "exam-proctoring",
        "title": {"en": "Online exam proctoring at a university", "it": "Proctoring degli esami online in università"},
        "description": {
            "en": "A university buys an online proctoring system that watches students through their webcam during remote exams and flags suspicious behaviour for the examiner to review.",
            "it": "Un'università acquista un sistema di proctoring che osserva gli studenti tramite webcam durante gli esami a distanza e segnala comportamenti sospetti all'esaminatore.",
        },
        "tags": ["education", "Annex III"],
        "expected_tier": "high_risk",
    },
    {
        "id": "deepfake-marketing",
        "title": {"en": "Synthetic video avatars for marketing", "it": "Avatar video sintetici per il marketing"},
        "description": {
            "en": "A marketing agency offers a service that generates realistic videos of a fictional presenter reading client scripts in several languages, to be published on social media.",
            "it": "Un'agenzia di marketing offre un servizio che genera video realistici di un presentatore fittizio che legge i testi dei clienti in più lingue, da pubblicare sui social.",
        },
        "tags": ["generative", "Art. 50"],
        "expected_tier": "limited_risk",
        "expected_overlays": ['transparency_art50'],
    },
    {
        "id": "medical-device-triage",
        "title": {"en": "AI inside a medical imaging device", "it": "IA integrata in un dispositivo di imaging medico"},
        "description": {
            "en": "We manufacture a CE-marked radiology device and are adding a deep-learning module that detects suspected tumours on scans as a safety-relevant function, subject to notified-body assessment under the Medical Devices Regulation.",
            "it": "Produciamo un dispositivo radiologico con marcatura CE e stiamo aggiungendo un modulo di deep learning che individua sospetti tumori nelle immagini come funzione rilevante per la sicurezza, soggetto a valutazione dell'organismo notificato ai sensi del Regolamento sui dispositivi medici.",
        },
        "tags": ["Annex I", "medical devices"],
        "expected_tier": "high_risk",
    },
    {
        "id": "gpai-model-provider",
        "title": {"en": "Releasing a general-purpose language model", "it": "Rilascio di un modello linguistico di uso generale"},
        "description": {
            "en": "Our AI lab trained a 70-billion-parameter language model on web data and will release it to EU customers through an API for any downstream use.",
            "it": "Il nostro laboratorio di IA ha addestrato un modello linguistico da 70 miliardi di parametri su dati web e lo renderà disponibile ai clienti UE tramite API per qualsiasi uso.",
        },
        "tags": ["GPAI", "Chapter V"],
        "expected_tier": "minimal_risk",
        "expected_overlays": ['gpai'],
    },
    {
        "id": "police-facial-recognition",
        "title": {"en": "Live facial recognition at a city square", "it": "Riconoscimento facciale in tempo reale in una piazza"},
        "description": {
            "en": "A municipal police force wants to connect existing CCTV cameras in the main square to live facial recognition that matches passers-by against a watch-list and alerts officers in real time.",
            "it": "Una polizia municipale vuole collegare le telecamere della piazza principale a un riconoscimento facciale in tempo reale che confronta i passanti con una lista di ricercati e avvisa gli agenti.",
        },
        "tags": ["law enforcement", "biometrics", "Art. 5"],
        "expected_tier": "prohibited",
    },
    {
        "id": "research-prototype",
        "title": {"en": "University research prototype", "it": "Prototipo di ricerca universitario"},
        "description": {
            "en": "A university lab is developing an experimental model to predict student drop-out for a scientific study. It is not offered to anyone and will not be used to take decisions about students.",
            "it": "Un laboratorio universitario sta sviluppando un modello sperimentale per prevedere l'abbandono degli studi nell'ambito di uno studio scientifico. Non è offerto a nessuno e non sarà usato per decisioni sugli studenti.",
        },
        "tags": ["scope", "Art. 2"],
        "expected_tier": "out_of_scope",
    },
    {
        "id": "payroll-rules",
        "title": {"en": "Rule-based payroll calculator", "it": "Calcolo delle buste paga basato su regole"},
        "description": {
            "en": "Our payroll software computes salaries and taxes using fixed formulas and tables written by accountants. There is no learning or statistical component.",
            "it": "Il nostro software per le buste paga calcola stipendi e imposte con formule e tabelle fisse scritte dai commercialisti. Non ha componenti di apprendimento o statistiche.",
        },
        "tags": ["not an AI system", "Art. 3"],
        "expected_tier": "out_of_scope",
    },
]


def examples_for(lang: str) -> list[dict]:
    lang = lang if lang in ("en", "it") else "en"
    return [
        {
            "id": e["id"],
            "title": e["title"][lang],
            "description": e["description"][lang],
            "text": e["description"][lang],
            "tags": e["tags"],
            "expected_tier": e["expected_tier"],
            "expected_overlays": e.get("expected_overlays", []),
        }
        for e in EXAMPLES
    ]
