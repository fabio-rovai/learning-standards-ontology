# Can these standards reject a wrong statement?

Generated 2026-08-16 by `pipeline/falsifiability_test.py`. Six mis-statements are put to each artefact, each translated into that artefact's own vocabulary. A mutation counts as detected only when an axiom actually present in that artefact is violated by it. Where the artefact has no term for what the mutation says, the result is *inexpressible*, not *not detected*: an artefact cannot be blamed for failing to reject a sentence it cannot form. Inexpressible is not a lesser failure than undetected, though. It means the artefact has nothing to say about that part of the domain at all.

| Artefact | Detected | Expressible but undetected | Inexpressible |
|---|---:|---:|---:|
| LSO (this repository) | **6 of 6** | 0 | 0 |
| CEDS Ontology v14 | **0 of 6** | 1 | 5 |
| ASN schema | **1 of 6** | 3 | 2 |

## Which mutation, which artefact

| Mutation | LSO (this repository) | CEDS Ontology v14 | ASN schema |
|---|---|---|---|
| M1 a statement that is also a document | detected | not detected | not detected |
| M2 two statements each the parent of the other | detected | inexpressible | not detected |
| M3 a statement that is its own parent | detected | inexpressible | not detected |
| M4 an alignment with two different source statements | detected | inexpressible | inexpressible |
| M5 a document contained in a jurisdiction | detected | inexpressible | detected |
| M6 one identifier assertion belonging to two schemes | detected | inexpressible | inexpressible |

## Why each verdict


### LSO (this repository)

- **M1 a statement that is also a document** — detected: disjoint: https://learning.tesseract.academy/lso/test/s1 is typed as both ['https://learning.tesseract.academy/lso#StandardStatement', 'https://learning.tesseract.academy/lso#StandardsDocument']
- **M2 two statements each the parent of the other** — detected: asymmetric: <https://learning.tesseract.academy/lso#hasParentStatement> asserted in both directions between https://learning.tesseract.academy/lso/test/s1 and https://learning.tesseract.academy/lso/test/s2
- **M3 a statement that is its own parent** — detected: irreflexive: <https://learning.tesseract.academy/lso#hasParentStatement> asserted of https://learning.tesseract.academy/lso/test/s1 and itself
- **M4 an alignment with two different source statements** — detected: functional: <https://learning.tesseract.academy/lso#alignmentSource> has multiple values on https://learning.tesseract.academy/lso/test/a1
- **M5 a document contained in a jurisdiction** — detected: domain: <https://learning.tesseract.academy/lso#inDocument> requires subject of type ['https://learning.tesseract.academy/lso#StandardStatement'], got ['https://learning.tesseract.academy/lso#StandardsDocument']
- **M6 one identifier assertion belonging to two schemes** — detected: functional: <https://learning.tesseract.academy/lso#identifierScheme> has multiple values on https://learning.tesseract.academy/lso/test/ia

### CEDS Ontology v14

- M1 a statement that is also a document — expressible, but undetected: the artefact declares no axiom this violates.
- M2 two statements each the parent of the other — inexpressible: no counterpart property for hasParentStatement.
- M3 a statement that is its own parent — inexpressible: no counterpart property for hasParentStatement.
- M4 an alignment with two different source statements — inexpressible: no counterpart property for alignmentTarget.
- M5 a document contained in a jurisdiction — inexpressible: no counterpart property for inDocument.
- M6 one identifier assertion belonging to two schemes — inexpressible: no counterpart class for IdentifierAssertion.

### ASN schema

- M1 a statement that is also a document — expressible, but undetected: the artefact declares no axiom this violates.
- M2 two statements each the parent of the other — expressible, but undetected: the artefact declares no axiom this violates.
- M3 a statement that is its own parent — expressible, but undetected: the artefact declares no axiom this violates.
- M4 an alignment with two different source statements — inexpressible: no counterpart property for alignmentTarget.
- **M5 a document contained in a jurisdiction** — detected: domain: <http://purl.org/ASN/schema/core/isChildOf> requires subject of type ['http://purl.org/ASN/schema/core/Statement'], got ['http://purl.org/ASN/schema/core/StandardDocument']
- M6 one identifier assertion belonging to two schemes — inexpressible: no counterpart class for IdentifierAssertion.

## Unsatisfiable domain and range declarations

Properties declaring more than one domain or range. RDFS reads these as conjunctions, so the property may only be used on something belonging to every declared class at once. Where the classes are siblings, ordinary correct usage violates the schema.


**ASN schema** — 10:

- `<http://purl.org/ASN/schema/core/alignFrom> declares 2 domains: ['StandardDocument', 'Statement']`
- `<http://purl.org/ASN/schema/core/alignTo> declares 2 domains: ['StandardDocument', 'Statement']`
- `<http://purl.org/ASN/schema/core/altIdentifier> declares 2 domains: ['StandardDocument', 'Statement']`
- `<http://purl.org/ASN/schema/core/hasChild> declares 2 domains: ['StandardDocument', 'Statement']`
- `<http://purl.org/ASN/schema/core/hasProgressionModel> declares 2 domains: ['Rubric', 'rdf-schema#Resource']`
- `<http://purl.org/ASN/schema/core/sequence> declares 2 domains: ['CriterionLevel', 'RubricCriterion']`
- `<http://purl.org/ASN/schema/core/source> declares 2 domains: ['Rubric', 'StandardDocument']`
- `<http://purl.org/ASN/schema/core/alignFrom> declares 2 ranges: ['StandardDocument', 'Statement']`
- `<http://purl.org/ASN/schema/core/alignTo> declares 2 ranges: ['StandardDocument', 'Statement']`
- `<http://purl.org/ASN/schema/core/isChildOf> declares 2 ranges: ['StandardDocument', 'Statement']`
