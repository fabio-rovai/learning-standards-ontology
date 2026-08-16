# Method

Four measurements are made here. Each is described so it can be repeated and, if it is wrong,
shown to be wrong.

## 1. Axiom census of the incumbent artefacts

**Question.** How many statements can each published artefact entail, and how many can it reject?

**Method.** `pipeline/analyse_incumbents.py` parses each artefact and counts axioms in two families.
*Entailing* axioms are the ones that let a reasoner derive something new: `rdfs:subClassOf`,
`rdfs:subPropertyOf`, `owl:equivalentClass`, `owl:inverseOf`, transitivity, symmetry, and SKOS
`broader`/`narrower`. *Refuting* axioms are the ones that let data contradict the model: domains,
ranges, disjointness, cardinality, functionality, irreflexivity, asymmetry, property disjointness,
and existential or universal restrictions.

**Why this split.** An artefact with many entailing axioms and no refuting ones is a vocabulary
that describes but cannot object. It will accept any assertion made in its terms. That is a
legitimate design for a glossary and a serious problem for a standard that data pipelines are
supposed to be validated against.

**Limits.** Counting axioms is not the same as measuring semantic quality, and an artefact could in
principle have few axioms that are individually very powerful. The count is a floor, not a verdict.
It is reported alongside the specific list of which axiom families are absent entirely, so the
reader can judge for themselves rather than trusting a single score.

## 2. Falsifiability experiment

**Question.** Given a specific wrong statement, does the artefact notice?

**Method.** `pipeline/falsifiability_test.py` constructs six mis-statements, translates each into
the artefact's own vocabulary, and checks whether any axiom actually present in that artefact is
violated.

**The fairness rule that matters.** Where an artefact has no term for what a mutation says, the
result is recorded as *inexpressible*, not as *not detected*. Judging CEDS by whether it rejects a
sentence written in LSO's vocabulary would manufacture a result. Inexpressible is reported as its
own column, and it is not a lesser finding: it means the artefact has nothing to say about that
part of the domain at all.

**A correction made during the build.** The first version of the checker read multiple `rdfs:range`
declarations conjunctively, which is what RDFS actually says. Under that reading the ASN schema
appeared to detect two mutations. It was not detecting them: `asn:isChildOf` declares two ranges,
`StandardDocument` and `Statement`, plainly meaning "either", and the strict reading makes every
ordinary ASN parent link violate its own schema. The checker was changed to the charitable
disjunctive reading, ASN's score fell from three to one, and the strict-reading defect is now
reported separately as a finding in its own right. The lower number is the honest one.

## 3. ASN identifier resolution census

**Question.** Of the ASN identifiers that public artefacts still cite, how many still resolve?

**Population.** `pipeline/harvest_asn_citations.py` searches public code hosting for files
containing ASN resource URIs, fetches each matching file, and extracts every ASN URI in it. Only
identifiers matching the canonical ASN form are kept. The population is therefore identifiers that
real published artefacts depend on, not identifiers invented for the test.

**Measurement.** `pipeline/asn_census.py` dereferences every identifier in the population once and
records the HTTP status. This is a census, not a sample, so no confidence interval is involved.

**Which host, and why.** Requests go to the origin host, `asn.jesandco.org`. The canonical form is
`http://purl.org/ASN/resources/{id}`, but that indirection layer rate-limits aggressively: an early
sample of 60 identifiers returned 50 HTTP 429s. Hammering it to produce a number would have been
both hostile and unnecessary, because the redirect is verifiable once and then holds for every
identifier. The redirect target was confirmed directly, and a sample of identifiers was checked in
both forms and returned the same status. The census result is therefore a statement about the data,
and the PURL layer's behaviour is reported separately.

**Limits.** Public code hosting is one corpus among several. Identifiers cited only in closed
systems, in PDFs, or in learning-object metadata never published to a code host are not counted.
The population is a lower bound on how widely these identifiers are still relied upon.

## 4. Standards corpus harvest

**Question.** What is actually in the public K-12 standards corpus, and how is it identified and
licensed?

**Method.** `pipeline/harvest_csp.py` walks the Common Standards Project public API: every
jurisdiction, every standard set, every standard. The API is used because it is the only public
source that carries each standard's ASN identifier alongside its own, which is what makes the
identifier-continuity question answerable at all.

**Limits.** The Common Standards Project is a third-party aggregation, not an authoritative
publisher. Where it disagrees with a state education agency, the state is right and this graph is
wrong. Its coverage is uneven: some jurisdictions have every framework, others have one. Counts
here describe that corpus, not the universe of American academic standards.

## Data currency

Three of the four sources are served "current" rather than pinned, so a rerun will not reproduce
the published totals exactly:

- **Pinned and reproducible byte for byte:** the CEDS Ontology, fetched from the `V14.0.0.0` tag.
  The file analysed here has SHA-256 beginning `26d782b6047236e8`.
- **Not pinned:** the Common Standards Project API, the Georgia CASE server, and the ASN citation
  population, which changes as public repositories change.

Every figure published in this repository is therefore timestamped to its build date. The method is
reproducible; the specific totals are observations, not constants.
