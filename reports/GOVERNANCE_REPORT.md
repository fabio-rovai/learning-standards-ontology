# Governance report

Generated 2026-08-16 by `pipeline/governance_report.py` from the harvested public sources. Every figure is computed, not asserted. Figures drawn from a sample rather than a census are labelled as such and carry a 95% Wilson interval.

## The corpus

- Jurisdictions: **771** ([('school', 368), ('organization', 334), ('state', 65), ('country', 2), ('corporation', 1), ('nation', 1)]).
- Standard sets harvested: **23,700**; distinct documents: **3,057**.
- Standard statements: **1,931,913** rows, **1,931,373** distinct Common Standards Project identifiers.
- Statements carrying an ASN identifier: **992,992** rows, **770,861** distinct ASN identifiers (51.4% of rows).

## R6 — Licence coverage

| Licence | Standard sets | Share |
|---|---:|---:|
| CC BY 4.0 US | 13,707 | 57.8% |
| CC BY 3.0 US | 8,495 | 35.8% |
| NO LICENCE STATED | 1,498 | 6.3% |

**1,498 standard sets (6.3%) state no licence at all.** These are public curriculum policy documents that cannot be lawfully redistributed by anyone relying on the published metadata, because the metadata does not say they can be. The absence is not an edge case in the data; it is a standing block on every downstream open use.

## Adoption status

| Status | Standard sets | Share |
|---|---:|---:|
| Unstated | 10,314 | 43.5% |
| Published | 8,626 | 36.4% |
| Deprecated | 4,760 | 20.1% |

**10,314 sets (43.5%) carry no publication status.** A consumer cannot tell from the record whether these standards are in force, superseded, or draft. `Deprecated` accounts for a further 4,760 (20.1%).

## R4 — Identifier collision

- ASN identifiers attached to more than one distinct statement record: **79,882** of 770,861 (10.4%).
- Of those, identifiers whose attached statements have **materially different text**: **433**. These are hard collisions: one globally unique identifier naming two different standards.
- Identifiers spanning more than one document: **2,156**.

Worked collisions, each verifiable against the live public API:

- `S100EC5D` — 5 statement records across 1 document(s):
  - "Design and conduct controlled investigations."
  - "State that respiration involves the action of enzymes in cells"
- `S101BE2B` — 10 statement records across 1 document(s):
  - "Observations, Questions, and Hypotheses"
  - "Respiration"
- `S101E29E` — 5 statement records across 1 document(s):
  - "Formulate predictions, questions, or hypotheses based on observations. Locate appropriate resources."
  - "State the uses of evergy in the body of humans: muscle contraction, protein synthesis, cell division, active transport, growth, the passage of nerve i"

## The inverse failure — one statement, many identifiers

Identifier collision has a mirror image, and this corpus has both at once. The most widely replicated statement text appears under this many *distinct* ASN identifiers:

| Distinct ASN identifiers | Statement text |
|---:|---|
| 718 | Demonstrate command of the conventions of standard English capitalization, punctuation, and spelling when writ |
| 667 | Demonstrate command of the conventions of standard English grammar and usage when writing or speaking. |
| 587 | Produce clear and coherent writing in which the development, organization, and style are appropriate to task,  |
| 531 | Demonstrate understanding of figurative language, word relationships, and nuances in word meanings. |
| 500 | Draw evidence from literary or informational texts to support analysis, reflection, and research. |

Nothing in the published data says these are the same expectation. A system asked whether two states teach the same thing has to decide by comparing strings.

## R1 — Identifier resolution

**Census A — every ASN identifier still cited in public code.** Population 44,084 identifiers across 57,769 citations; all 44,084 dereferenced.

| HTTP status | Identifiers |
|---|---:|
| 404 | 44,084 |

**0 of 44,084 resolve (0.0%).** This is a census, not a sample: every identifier in the population was dereferenced.

**Census B — every ASN document identifier in the live standards corpus.** n = 3,057.

| HTTP status | Identifiers |
|---|---:|
| 404 | 3,057 |

Resolving: **0 of 3,057 (0.0%)**.

**Census C — a random sample of ASN statement identifiers in the live standards corpus.** n = 20,000 drawn at random from 770,861.

| HTTP status | Identifiers |
|---|---:|
| 404 | 20,000 |

Resolving: **0 of 20,000 (0.0%)**, 95% Wilson interval [0.00%, 0.02%].


## What these rules are

Each heading above corresponds to a rule in `shapes/lso-rules.ttl`, written as SHACL-SPARQL so it is portable to any conforming engine. The figures here are computed set-based because the full graph exceeds what rdflib can self-join in reasonable time. The SHACL and the set-based computation are checked against each other on the worked example and on samples small enough to run both ways.

