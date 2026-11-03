# EU AI Act assessment

*Law as of 27 July 2026 (checked on 3 November 2026). Generated with claude_cli / claude-sonnet-5-5.*

> **Disclaimer.** This assessment is generated automatically from the text of Regulation (EU) 2024/1689 as consolidated on 27 July 2026 (including Regulation (EU) 2026/1744). It is an orientation tool, not legal advice, and it does not replace an assessment by a qualified lawyer. Verify every citation against the official text before relying on it.

## Described system

> We are a 200-person logistics company in Milan. We bought a SaaS tool that screens incoming CVs and ranks candidates for our HR team, which then invites the top 20 to interview. We use it as delivered by the vendor and do not modify it.

## Result

- **Classification:** High-risk AI system
- **Confidence:** High
- **Role:** Deployer

## Reasoning

Your system ranks job applicants, which is a listed high-risk use under [Annex III, point 4(a)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#anx_III). Because it profiles candidates, the exemption in [Art. 6(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_6) cannot be relied on.

**What this means for you as deployer**

- Use the system according to the provider's instructions ([Art. 26(1)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)).
- Inform workers' representatives and affected candidates before use ([Art. 26(7)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)).
- Assign human oversight to competent, trained staff ([Art. 26(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)).

The provider carries the main conformity duties; you must verify they are met.

## Findings

### Recruitment and selection is an Annex III use case (decisive)

The system ranks and filters candidates, which falls under [Annex III, point 4(a)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#anx_III) (recruitment or selection of natural persons, in particular to analyse and filter applications and evaluate candidates).

**Citations:** [Annex III, point 4(a)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#anx_III), [Art. 6(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_6)

### Art. 6(3) derogation does not apply

The tool profiles natural persons and materially influences who is interviewed, so the derogation of Art. 6(3) is not available; see [Art. 6(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_6).

**Citations:** [Art. 6(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_6)

### You act as deployer

The company uses the system under its own authority in a professional context, so the deployer duties of [Art. 26(1)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26) and [Art. 26(7)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26) apply.

**Citations:** [Art. 26(1)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26), [Art. 26(7)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

## Obligations

### Governance and risk management

- **Use the system per the provider's instructions** (Deployer; mandatory; applies from 2 December 2027). Take technical and organisational measures to use the system as instructed ([Art. 26(1)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)).
  - [Art. 26(1)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Documentation and records

- **Keep automatically generated logs** (Deployer; mandatory; applies from 2 December 2027). Keep the logs under your control for at least six months.
  - [Art. 26(6)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Transparency

- **Inform workers and candidates** (Deployer; mandatory; applies from 2 December 2027). Before putting the system into use at work, inform workers' representatives and the workers concerned.
  - [Art. 26(7)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Human oversight

- **Assign human oversight** (Deployer; mandatory; applies from 2 December 2027). Entrust oversight to people with the necessary competence, training and authority.
  - [Art. 26(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Monitoring

- **Monitor and report incidents** (Deployer; mandatory; applies from 2 December 2027). Monitor operation and inform the provider and authorities of serious incidents.
  - [Art. 26(5)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### AI literacy

- **Ensure AI literacy** (Provider and deployer; recommended; applies from 2 February 2025). Ensure a sufficient level of AI literacy of staff operating the system ([Art. 4](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_4)).
  - [Art. 4](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_4)

## Compliance checklist

- [ ] **Obtain the provider's instructions for use**. Request and file the instructions and the EU declaration of conformity.
  - [Art. 26(1)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)
  - *Template hint:* Vendor due-diligence questionnaire
- [ ] **Name the human overseers**. Appoint trained HR staff who can override or disregard the ranking.
  - [Art. 26(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)
- [ ] **Notify employee representatives**. Send the information notice before the tool goes live.
  - [Art. 26(7)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)
  - *Template hint:* Employee information notice
- [ ] **Add a candidate notice**. Tell applicants that an AI system is used in the selection.
  - [Art. 26(11)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)
- [ ] **Configure log retention**. Ensure logs are kept for at least six months.
  - [Art. 26(6)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)
- [ ] **Run an AI literacy session**. Train the HR team on the tool's capabilities and limits.
  - [Art. 4](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_4)
  - *Template hint:* Training attendance register

## Timeline

- **2 February 2025**: AI literacy duty already applies ([Art. 4](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_4))
- **2 December 2027**: Obligations for Annex III high-risk systems apply ([Art. 6(2)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_6))

## Assumptions and uncertainties

### Assumptions

- The vendor is the provider and has not substantially modified its purpose.

### Uncertainties

- It is unclear whether the vendor offers human-override features; confirm this with the vendor.

### Facts still unknown

- `human_oversight`

## Related provisions

- [Recital 57](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689#rct_57): Explains why employment systems are high-risk.
- [Art. 86](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_86): Right to an explanation of individual decision-making.

## Cited provisions

### Annex III, point 4(a)

> AI systems intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates;

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#anx_III)

### Art. 6(2)

> In addition to the high-risk AI systems referred to in paragraph 1, AI systems referred to in Annex III shall be considered to be high-risk.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_6)

### Art. 26(1)

> Deployers of high-risk AI systems shall take appropriate technical and organisational measures to ensure they use such systems in accordance with the instructions for use accompanying the systems, pursuant to paragraphs 3 and 6.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Art. 26(7)

> Before putting into service or using a high-risk AI system at the workplace, deployers who are employers shall inform workers’ representatives and the affected workers that they will be subject to the use of the high-risk AI system. This information shall be provided, where applicable, in accordance with the rules and procedures laid down in Union and national law and practice on information of workers and their representatives.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Art. 26(2)

> Deployers shall assign human oversight to natural persons who have the necessary competence, training and authority, as well as the necessary support.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Art. 26(6)

> Deployers of high-risk AI systems shall keep the logs automatically generated by that high-risk AI system to the extent such logs are under their control, for a period appropriate to the intended purpose of the high-risk AI system, of at least six months, unless provided otherwise in applicable Union or national law, in particular in Union law on the protection of personal data.
> Deployers that are financial institutions subject to requirements regarding their internal governance, arrangements or processes under Union financial services law shall maintain the logs as part of the documentation kept pursuant to the relevant Union financial service law.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Art. 26(5)

> Deployers shall monitor the operation of the high-risk AI system on the basis of the instructions for use and, where relevant, inform providers in accordance with Article 72. Where deployers have reason to consider that the use of the high-risk AI system in accordance with the instructions may result in that AI system presenting a risk within the meaning of Article 79(1), they shall, without undue delay, inform the provider or distributor and the relevant market surveillance authority, and shall suspend the use of that system. Where deployers have identified a serious incident, they shall also immediately inform first the provider, and then the importer or distributor and the relevant market surveillance authorities of that incident. If the deployer is not able to reach the provider, Article 73 shall apply mutatis mutandis. This obligation shall not cover sensitive operational data of deployers of AI systems which are law enforcement authorities.
> For deployers that are financial institutions subject to requirements regarding their internal governance, arrangements or processes under Union financial services law, the monitoring obligation set out in the first subparagraph shall be deemed to be fulfilled by complying with the rules on internal governance arrangements, processes and mechanisms pursuant to the relevant financial service law.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Art. 4

> AI literacy
> 1. Providers and deployers of AI systems shall take measures to support the development of AI literacy of their staff and other persons dealing with the operation and use of AI systems on their behalf, taking into account their technical knowledge, experience, education and training and the context the AI systems are to be used in, and considering the persons or groups of persons on whom the AI systems are to be used. This obligation does not require providers or deployers to guarantee any specific level of AI literacy of any individual.
> 2. The Commission and the Member States shall support and facilitate the efforts of providers and deployers of AI systems, in particular SMEs, in fulfilling their obligation under paragraph 1 of this Article. For that purpose, the Commission shall publish practical examples of how to comply with that obligation on the single information platform referred to in Article 62(3), point (b).
> 3. The Board shall adopt recommendations, taking into account European competence frameworks, to support the Commission and Member States in the promotion of AI literacy required under paragraph 1, including by setting out common objectives.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_4)

### Art. 26(11)

> Without prejudice to Article 50 of this Regulation, deployers of high-risk AI systems referred to in Annex III that make decisions or assist in making decisions related to natural persons shall inform the natural persons that they are subject to the use of the high-risk AI system. For high-risk AI systems used for law enforcement purposes Article 13 of Directive (EU) 2016/680 shall apply.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_26)

### Recital 57

> AI systems used in employment, workers management and access to self-employment, in particular for the recruitment and selection of persons, for making decisions affecting terms of the work-related relationship, promotion and termination of work-related contractual relationships, for allocating tasks on the basis of individual behaviour, personal traits or characteristics and for monitoring or evaluation of persons in work-related contractual relationships, should also be classified as high-risk, since those systems may have an appreciable impact on future career prospects, livelihoods of those persons and workers’ rights. Relevant work-related contractual relationships should, in a meaningful manner, involve employees and persons providing services through platforms as referred to in the Commission Work Programme 2021. Throughout the recruitment process and in the evaluation, promotion, or retention of persons in work-related contractual relationships, such systems may perpetuate historical patterns of discrimination, for example against women, certain age groups, persons with disabilities, or persons of certain racial or ethnic origins or sexual orientation. AI systems used to monitor the performance and behaviour of such persons may also undermine their fundamental rights to data protection and privacy.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689#rct_57)

### Art. 86

> Right to explanation of individual decision-making
> 1. Any affected person subject to a decision which is taken by the deployer on the basis of the output from a high-risk AI system listed in Annex III, with the exception of systems listed under point 2 thereof, and which produces legal effects or similarly significantly affects that person in a way that they consider to have an adverse impact on their health, safety or fundamental rights shall have the right to obtain from the deployer clear and meaningful explanations of the role of the AI system in the decision-making procedure and the main elements of the decision taken.
> 2. Paragraph 1 shall not apply to the use of AI systems for which exceptions from, or restrictions to, the obligation under that paragraph follow from Union or national law in compliance with Union law.
> 3. This Article shall apply only to the extent that the right referred to in paragraph 1 is not otherwise provided for under Union law.

[Read on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727#art_86)

---

*Not legal advice · generated 3 November 2026 · law as of 27 July 2026*
