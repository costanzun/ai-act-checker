"""Annex I and Annex III data, transcribed from the consolidated text (27.7.2026)."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Annex III — one entry per point. Key = FactSheet.annex_iii_area value.
# (provision id, short EN title, short IT title, recital ids)
# ---------------------------------------------------------------------------
ANNEX_III: dict[str, tuple[str, str, str, list[str]]] = {
    "1a_remote_biometric_identification": (
        "annex:III.1.a",
        "Remote biometric identification",
        "Identificazione biometrica remota",
        ["rec:54"],
    ),
    "1b_biometric_categorisation_sensitive": (
        "annex:III.1.b",
        "Biometric categorisation by sensitive or protected attributes",
        "Categorizzazione biometrica in base ad attributi sensibili o protetti",
        ["rec:54"],
    ),
    "1c_emotion_recognition": ("annex:III.1.c", "Emotion recognition", "Riconoscimento delle emozioni", ["rec:54"]),
    "2_critical_infrastructure_safety": (
        "annex:III.2",
        "Safety component in critical infrastructure",
        "Componente di sicurezza di infrastrutture critiche",
        ["rec:55"],
    ),
    "3a_education_admission": (
        "annex:III.3.a",
        "Access or admission to education and training",
        "Accesso o ammissione a istituti di istruzione e formazione",
        ["rec:56"],
    ),
    "3b_education_evaluation": (
        "annex:III.3.b",
        "Evaluation of learning outcomes",
        "Valutazione dei risultati dell'apprendimento",
        ["rec:56"],
    ),
    "3c_education_level_assessment": (
        "annex:III.3.c",
        "Assessing the appropriate level of education",
        "Valutazione del livello di istruzione adeguato",
        ["rec:56"],
    ),
    "3d_education_proctoring": (
        "annex:III.3.d",
        "Monitoring prohibited behaviour of students during tests",
        "Monitoraggio dei comportamenti vietati degli studenti durante le prove",
        ["rec:56"],
    ),
    "4a_recruitment_selection": (
        "annex:III.4.a",
        "Recruitment and selection of candidates",
        "Assunzione e selezione del personale",
        ["rec:57"],
    ),
    "4b_work_decisions_monitoring": (
        "annex:III.4.b",
        "Decisions on work relationships, task allocation, performance monitoring",
        "Decisioni sui rapporti di lavoro, assegnazione dei compiti, monitoraggio delle prestazioni",
        ["rec:57"],
    ),
    "5a_public_benefits_eligibility": (
        "annex:III.5.a",
        "Eligibility for essential public assistance benefits and services",
        "Ammissibilità a prestazioni e servizi di assistenza pubblica essenziali",
        ["rec:58"],
    ),
    "5b_creditworthiness": (
        "annex:III.5.b",
        "Creditworthiness assessment and credit scoring",
        "Valutazione dell'affidabilità creditizia e del merito di credito",
        ["rec:58"],
    ),
    "5c_life_health_insurance_pricing": (
        "annex:III.5.c",
        "Risk assessment and pricing in life and health insurance",
        "Valutazione dei rischi e determinazione dei prezzi nelle assicurazioni vita e malattia",
        ["rec:58"],
    ),
    "5d_emergency_dispatch_triage": (
        "annex:III.5.d",
        "Emergency call evaluation, dispatch and patient triage",
        "Classificazione delle chiamate di emergenza, invio dei soccorsi e triage",
        ["rec:58"],
    ),
    "6a_le_victim_risk": (
        "annex:III.6.a",
        "Law enforcement: risk of becoming a victim",
        "Attività di contrasto: rischio di diventare vittima di reati",
        ["rec:59"],
    ),
    "6b_le_polygraph": (
        "annex:III.6.b",
        "Law enforcement: polygraphs and similar tools",
        "Attività di contrasto: poligrafi e strumenti analoghi",
        ["rec:59"],
    ),
    "6c_le_evidence_reliability": (
        "annex:III.6.c",
        "Law enforcement: reliability of evidence",
        "Attività di contrasto: affidabilità degli elementi probatori",
        ["rec:59"],
    ),
    "6d_le_offending_risk_profiling": (
        "annex:III.6.d",
        "Law enforcement: risk of offending or re-offending",
        "Attività di contrasto: rischio di commissione di reati o di recidiva",
        ["rec:59"],
    ),
    "6e_le_profiling_investigation": (
        "annex:III.6.e",
        "Law enforcement: profiling in criminal investigations",
        "Attività di contrasto: profilazione nel corso di indagini",
        ["rec:59"],
    ),
    "7a_migration_polygraph": (
        "annex:III.7.a",
        "Migration and border control: polygraphs and similar tools",
        "Migrazione e frontiere: poligrafi e strumenti analoghi",
        ["rec:60"],
    ),
    "7b_migration_risk_assessment": (
        "annex:III.7.b",
        "Migration and border control: risk assessment of persons",
        "Migrazione e frontiere: valutazione dei rischi posti da persone",
        ["rec:60"],
    ),
    "7c_migration_application_examination": (
        "annex:III.7.c",
        "Examination of asylum, visa and residence applications",
        "Esame delle domande di asilo, visto e permesso di soggiorno",
        ["rec:60"],
    ),
    "7d_migration_identification": (
        "annex:III.7.d",
        "Migration and border control: detecting or identifying persons",
        "Migrazione e frontiere: individuazione o identificazione di persone",
        ["rec:60"],
    ),
    "8a_justice_assist_judicial": (
        "annex:III.8.a",
        "Assisting judicial authorities or alternative dispute resolution",
        "Assistenza alle autorità giudiziarie o alla risoluzione alternativa delle controversie",
        ["rec:61"],
    ),
    "8b_elections_influence": (
        "annex:III.8.b",
        "Influencing elections, referenda or voting behaviour",
        "Influenza sull'esito di elezioni o referendum o sul comportamento di voto",
        ["rec:62"],
    ),
}

# ---------------------------------------------------------------------------
# Annex I — product legislation. Key = FactSheet.annex_i_product value.
# (section, list of Annex I point ids, EN label, IT label, sectoral amending article ids)
# Note: Section A point 1 (Machinery Directive 2006/42/EC) was DELETED by
# Regulation (EU) 2026/1744 and the Machinery Regulation (EU) 2023/1230 was
# INSERTED as Section B point 21.
# ---------------------------------------------------------------------------
ANNEX_I: dict[str, tuple[str, list[str], str, str, list[str]]] = {
    "toys": ("A", ["annex:I.A.2"], "Toys (Directive 2009/48/EC)", "Giocattoli (direttiva 2009/48/CE)", []),
    "recreational_craft": (
        "A",
        ["annex:I.A.3"],
        "Recreational craft and personal watercraft (Directive 2013/53/EU)",
        "Imbarcazioni da diporto e moto d'acqua (direttiva 2013/53/UE)",
        [],
    ),
    "lifts": ("A", ["annex:I.A.4"], "Lifts (Directive 2014/33/EU)", "Ascensori (direttiva 2014/33/UE)", []),
    "equipment_explosive_atmospheres": (
        "A",
        ["annex:I.A.5"],
        "Equipment for potentially explosive atmospheres (Directive 2014/34/EU)",
        "Apparecchi per atmosfere potenzialmente esplosive (direttiva 2014/34/UE)",
        [],
    ),
    "radio_equipment": (
        "A",
        ["annex:I.A.6"],
        "Radio equipment (Directive 2014/53/EU)",
        "Apparecchiature radio (direttiva 2014/53/UE)",
        [],
    ),
    "pressure_equipment": (
        "A",
        ["annex:I.A.7"],
        "Pressure equipment (Directive 2014/68/EU)",
        "Attrezzature a pressione (direttiva 2014/68/UE)",
        [],
    ),
    "cableways": (
        "A",
        ["annex:I.A.8"],
        "Cableway installations (Regulation (EU) 2016/424)",
        "Impianti a fune (regolamento (UE) 2016/424)",
        [],
    ),
    "personal_protective_equipment": (
        "A",
        ["annex:I.A.9"],
        "Personal protective equipment (Regulation (EU) 2016/425)",
        "Dispositivi di protezione individuale (regolamento (UE) 2016/425)",
        [],
    ),
    "gas_appliances": (
        "A",
        ["annex:I.A.10"],
        "Appliances burning gaseous fuels (Regulation (EU) 2016/426)",
        "Apparecchi che bruciano carburanti gassosi (regolamento (UE) 2016/426)",
        [],
    ),
    "medical_devices": (
        "A",
        ["annex:I.A.11"],
        "Medical devices (Regulation (EU) 2017/745)",
        "Dispositivi medici (regolamento (UE) 2017/745)",
        [],
    ),
    "in_vitro_diagnostics": (
        "A",
        ["annex:I.A.12"],
        "In vitro diagnostic medical devices (Regulation (EU) 2017/746)",
        "Dispositivi medico-diagnostici in vitro (regolamento (UE) 2017/746)",
        [],
    ),
    "machinery": (
        "B",
        ["annex:I.B.21"],
        "Machinery (Regulation (EU) 2023/1230) — moved to Section B by the Omnibus",
        "Macchine (regolamento (UE) 2023/1230) — spostato nella sezione B dall'Omnibus",
        [],
    ),
    "civil_aviation": (
        "B",
        ["annex:I.B.13", "annex:I.B.20"],
        "Civil aviation security and civil aviation / unmanned aircraft (Regulations (EC) 300/2008, (EU) 2018/1139)",
        "Sicurezza dell'aviazione civile e aviazione civile / aeromobili senza equipaggio (regolamenti (CE) 300/2008, (UE) 2018/1139)",
        ["art:102", "art:108"],
    ),
    "vehicles": (
        "B",
        ["annex:I.B.14", "annex:I.B.18", "annex:I.B.19"],
        "Motor vehicles, two- or three-wheel vehicles and quadricycles (Regulations (EU) 168/2013, 2018/858, 2019/2144)",
        "Veicoli a motore, veicoli a due o tre ruote e quadricicli (regolamenti (UE) 168/2013, 2018/858, 2019/2144)",
        ["art:104", "art:107", "art:109"],
    ),
    "agricultural_vehicles": (
        "B",
        ["annex:I.B.15"],
        "Agricultural and forestry vehicles (Regulation (EU) 167/2013)",
        "Veicoli agricoli e forestali (regolamento (UE) 167/2013)",
        ["art:103"],
    ),
    "marine_equipment": (
        "B",
        ["annex:I.B.16"],
        "Marine equipment (Directive 2014/90/EU)",
        "Equipaggiamento marittimo (direttiva 2014/90/UE)",
        ["art:105"],
    ),
    "rail": (
        "B",
        ["annex:I.B.17"],
        "Rail system interoperability (Directive (EU) 2016/797)",
        "Interoperabilità del sistema ferroviario (direttiva (UE) 2016/797)",
        ["art:106"],
    ),
    "other_regulated_product": (
        "A",
        ["annex:I"],
        "Other product covered by Annex I legislation",
        "Altro prodotto disciplinato dalla normativa dell'allegato I",
        [],
    ),
}


def annex_i_citations() -> set[str]:
    out: set[str] = set()
    for _, pts, _, _, arts in ANNEX_I.values():
        out.update(pts)
        out.update(arts)
    return out


def annex_iii_citations() -> set[str]:
    out: set[str] = set()
    for pid, _, _, recs in ANNEX_III.values():
        out.add(pid)
        out.update(recs)
    return out
