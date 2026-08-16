# Learning Standards Ontology (LSO)

An open OWL 2 ontology, SKOS identifier-scheme registry and SHACL governance layer for K-12 academic
standards, built and measured against the public standards corpus:

- **1,931,913 standard statements** across **23,700 standard sets** and **771 jurisdictions**, harvested
  from the Common Standards Project public API,
- **770,861 distinct Achievement Standards Network identifiers** carried by those statements,
- the **CEDS Ontology v14.0.0.0** from the US Department of Education, 243,601 triples, parsed and
  counted axiom by axiom,
- a live **CASE** package from the Georgia Department of Education,
- joined into a **21,404,069 triple** knowledge graph gated by SHACL.

The finding that motivated everything else is in the next section, and it is not a subtle one.

## Every ASN identifier is dead. All of them.

The Achievement Standards Network was the linked-data identifier layer for American academic
standards. Its identifiers are the ones LRMI's `educationalAlignment` pattern was designed around,
so they are embedded in learning-resource metadata across the open education web, in the Learning
Registry, in inBloom, in DCMI's own published examples, and in the standards aggregations that
schools and vendors query today.

Three censuses, no sampling except where stated:

| Population | Identifiers | Resolve |
|---|---:|---:|
| ASN identifiers still cited in public code (44,084 distinct, 57,769 citations; 462 of 494 matching files yielded URIs, across 52 repositories) | 44,084 dereferenced | **0** |
| ASN document identifiers carried by the live standards corpus | 3,057 dereferenced | **0** |
| ASN statement identifiers carried by the live standards corpus (random sample of 770,861, seed 20260816) | 20,000 dereferenced | **0** |

Every one returns HTTP 404. Not degraded, not slow, not partially migrated. Zero.

The part that makes this a governance finding rather than an obituary is what *does* still resolve.
`http://purl.org/ASN/schema/core/` returns 200 and serves real RDF/XML, from a static object store.
The vocabulary that describes the identifiers is alive. The identifiers it describes are gone. Every
downstream system that stored an ASN URI stored a promise that the PURL layer still faithfully
forwards to a 404.

The dependency reaches the standards bodies themselves. `1EdTech/qti-examples` — published by the
organisation behind CASE, the specification that succeeded ASN — ships a QTI v3 example package whose
curriculum-standard references are ASN URIs. All nine of them return 404, in both the canonical PURL
form and at the origin. DCMI's own LRMI example files do the same.

A worked instance, verifiable in one command: AP Microeconomics learning objective POL-5.B, "Explain
sources of income and wealth inequality," is current, published by the College Board, in force, and
carries ASN identifier `S21370147`. `curl -IL http://purl.org/ASN/resources/S21370147` returns 404,
having faithfully redirected first. See [examples/worked-example.ttl](examples/worked-example.ttl).

## What the incumbent standards can reject

An ontology earns its keep by ruling things out. So: given a specific wrong statement, does the
published artefact notice? Six mis-statements, each translated into the artefact's own vocabulary,
each counted as detected only when an axiom actually present in that artefact is violated.

| Artefact | Detected | Expressible but undetected | Inexpressible |
|---|---:|---:|---:|
| **LSO (this repository)** | **6 of 6** | 0 | 0 |
| CEDS Ontology v14 (US Dept of Education) | **0 of 6** | 1 | 5 |
| ASN schema | **1 of 6** | 3 | 2 |

*Inexpressible* means the artefact has no term for what the mutation says. That is reported separately
rather than scored as a failure, because an artefact cannot be blamed for failing to reject a sentence
it cannot form. It is not the lesser finding: it means the artefact has nothing to say about that part
of the domain at all.

Underneath that result is an axiom census:

| Artefact | Triples | Classes | Object properties | Entailing axioms | Refuting axioms |
|---|---:|---:|---:|---:|---:|
| CEDS Ontology v14 | 243,601 | 967 | **0** | 1,381 | **24** |
| ASN schema | 465 | 0 | 0 | 18 | **121** |
| LSO | 440 | 19 | 16 | 12 | **100** |

*Refuting axioms* are the families that let data contradict a model: domains, ranges, disjointness,
cardinality, functionality, irreflexivity, asymmetry. An artefact with none of them will accept any
assertion made in its terms.

Three things follow, and all three are counted rather than argued:

1. **The abandoned vocabulary constrains more than the maintained federal one.** The ASN schema is 465
   triples and has been unmaintained for years. It carries 121 refuting axioms. CEDS v14 is 524 times
   larger and carries 24, of which 6 are ranges on CEDS's own annotation properties (`textFormat`,
   `minCount`, `maxLength` and so on) and 18 are `owl:allValuesFrom` restrictions. Across all 2,336 of
   its domain properties, CEDS v14 declares **zero `rdfs:domain`**.

2. **CEDS v14 declares no object properties, and its own README says otherwise.** The repository
   README states that the ontology provides "definitions and meaning about those relationships through
   Object Properties." The shipped v14 file declares **0 `owl:ObjectProperty`** and 0
   `owl:DatatypeProperty`. Relationships are present, but as bare `rdf:Property` typed with
   schema.org's `domainIncludes` and `rangeIncludes`, which schema.org defines as indicative rather
   than constraining. The relationships are documentation. They carry no logical force.

3. **CEDS v14 types 965 terms as both an `owl:Class` and a `skos:ConceptScheme`.** A class is a set of
   individuals; a concept scheme is a container of concepts. Conflating them means `rdf:type` and
   `skos:inScheme` are used interchangeably and no reasoner can distinguish an instance from a member.
   Its 19,546 SKOS concepts carry **zero `skos:broader` or `skos:narrower`** relations, so genuinely
   hierarchical vocabularies inside it, such as the 1,753 SCED course codes and 7,916 ISO 639-3
   language codes, are published as flat lists with their structure discarded.

This is a measurement, not a verdict on the people who built these things. CEDS describes itself as a
draft, is actively maintained, is Apache-2.0 licensed, and has a live SHACL/JSON-LD workstream with
NCES precisely because the shipped artefact does not constrain. The measurement says how large that
gap currently is.

### A correction made during this build

The first version of the falsifiability checker read multiple `rdfs:range` declarations conjunctively,
which is what RDFS actually says. Under that reading the ASN schema appeared to detect three mutations.
It was not detecting them. `asn:isChildOf` declares two ranges, `StandardDocument` and `Statement`,
plainly meaning "either", and under the strict reading every ordinary ASN parent link violates its own
schema. The checker was changed to the charitable disjunctive reading and ASN's score fell from 3 to 1.
The strict-reading defect is now reported separately: **10 ASN properties declare more than one domain
or range**. The lower number is the honest one. See [docs/METHOD.md](docs/METHOD.md).

## The corpus has both identifier failures at once

| Finding | Number |
|---|---:|
| ASN identifiers attached to more than one distinct statement record | **79,882** of 770,861 (10.4%) |
| Of those, identifiers whose statements have **materially different text** — one name, two different standards | **433** |
| Identifiers spanning more than one document | 2,156 |
| Distinct ASN identifiers carrying the single most replicated statement text | **718** |
| Standard sets stating **no licence at all** | **1,498** of 23,700 (6.3%) |
| Standard sets carrying **no publication status**, so a consumer cannot tell if they are in force | **10,314** of 23,700 (43.5%) |
| Standard sets marked Deprecated | 4,760 (20.1%) |

Verified worked collision, checked against the live API while writing this: `S100EC5D` is attached to
five statement records inside one document, Arizona's Academic Content Standards - Science. Four of them
read "Design and conduct controlled investigations." The fifth reads "State that respiration involves
the action of enzymes in cells."

The mirror image is just as bad. "Demonstrate command of the conventions of standard English
capitalization, punctuation, and spelling" appears verbatim under **718 distinct ASN identifiers**.
Nothing in the published data says those are the same expectation. A system asked whether two states
teach the same thing has to decide by comparing strings.

And the alignment layer that was supposed to answer that question is mostly not alignment. In Georgia's
live CASE package for Computer Science, of 2,483 associations, **2,453 (98.8%) are `isChildOf`** — that
is document structure, not correspondence between frameworks. There are 30 `isRelatedTo` and **zero**
cross-framework associations of any kind. The package contains no reference to ASN, and none to CEDS.

## What LSO does about it

Three design commitments, each a direct response to a measured failure above.

1. **Identifiers are first-class nodes and resolvability is recorded data.** An `lso:IdentifierAssertion`
   carries its scheme, its source and its observed `lso:ResolutionObservation` with an HTTP status, a
   timestamp and the final URL after redirects. Link rot stops being an anecdote and becomes a query.
   No incumbent artefact here has anywhere to put that fact.

2. **Scope and custody are declared, so the wrong identifier at the wrong level is an error.** The SKOS
   registry records for each scheme whether it is document-, statement- or jurisdiction-scoped, whether
   it is globally unique, whether it *promises* dereferenceability, and whether anyone is currently
   honouring that promise. ASN is recorded as `dereferenceable true` and `custodyStatus "orphaned"`, and
   that gap is the whole subject of this repository.

3. **Alignments record what would refute them.** An `lso:AlignmentAssertion` carries a falsifiability
   grade and may carry explicit refutation criteria. One with neither is classified by the reasoner as
   `lso:UnfalsifiableAlignment`. `isRelatedTo`, the most common cross-framework predicate in practice,
   is graded unfalsifiable in the registry, because no observation counts against it, and a claim that
   cannot fail cannot inform a decision.

The test suite enforces on LSO the properties whose absence it measures in others: every property
declares exactly one domain and one range, the ontology declares disjointness, and no term is typed as
both an `owl:Class` and a `skos:ConceptScheme`. Breaking any of those fails CI, deliberately.

## Repository layout

```
ontology/lso-core.ttl              Core OWL 2: standards, identifiers, resolution, alignment
skos/identifier-schemes.ttl        7 identifier schemes with scope, custody, uniqueness, syntax
shapes/lso-shapes.ttl              SHACL layers 1-2: syntax, completeness, scope
shapes/lso-rules.ttl               SHACL layer 3: 8 cross-source governance rules (R1-R8)
pipeline/analyse_incumbents.py     Axiom census of CEDS, ASN, CASE and LSO
pipeline/falsifiability_test.py    The six-mutation experiment
pipeline/harvest_asn_citations.py  Builds the ASN citation population from public code
pipeline/asn_census.py             Dereferences every identifier in that population
pipeline/harvest_csp.py            Harvests the Common Standards Project corpus
pipeline/build_graph.py            Streams the 21.4M-triple graph
pipeline/governance_report.py      Computes every finding set-based
queries/                           6 SPARQL queries over the graph
examples/worked-example.ttl        One real standard, all the way down
docs/METHOD.md                     How each measurement was made, and its limits
reports/                           Generated: capability, falsifiability, governance
```

## Reproducing this

```bash
python -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
bash scripts/fetch_data.sh                     # CEDS (pinned), ASN schema, CSP, Georgia CASE
./.venv/bin/python pipeline/harvest_csp.py --out data
./.venv/bin/python pipeline/harvest_asn_citations.py --out data   # needs `gh auth status`
./.venv/bin/python pipeline/asn_census.py --out data
./.venv/bin/python pipeline/analyse_incumbents.py
./.venv/bin/python pipeline/falsifiability_test.py
./.venv/bin/python pipeline/governance_report.py --scratch data
./.venv/bin/python -m pytest tests/ -v
```

## Data currency

Only one source is pinned. The CEDS Ontology is fetched from the `V14.0.0.0` tag and the file analysed
here has SHA-256 beginning `26d782b6047236e8`; that measurement is reproducible byte for byte. The
Common Standards Project API, the Georgia CASE server and the ASN citation population are all served
current and will drift, so corpus counts and percentages are observations timestamped to the 16 August
2026 build, not constants. Harvested source data is not committed: several of the documents surveyed
state no licence at all, which is one of the findings, and redistributing them would be exactly the
mistake this repository documents.

The 21.4M-triple graph and the 2 GB Turtle file it produces are regenerable, not committed.

## Licence

Ontology, SKOS registry, SHACL shapes and documentation: CC BY 4.0. Pipeline code: MIT. See
[LICENSE](LICENSE).

## Who made this and why

Built by [The Tesseract Academy](https://gov.tesseract.academy) as open research into data foundations
for the education sector. If you are reconciling standards across jurisdictions, migrating off a dead
identifier scheme, or trying to work out whether your alignment data means anything, the queries in
`queries/` are a reasonable place to start, and we are interested in the answers you get:
**fabio@thetesseractacademy.com**.

Corrections are welcome and will be made. If a number here is wrong, open an issue with the command
that shows it.
