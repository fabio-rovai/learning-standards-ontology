# Build report

What was fetched, what was computed, what could not be obtained, and what is uncertain. Build date
**16 August 2026**. Every figure in the README traces to something here.

## Sources fetched

| Source | Endpoint | Result | Pinned? |
|---|---|---|---|
| CEDS Ontology v14.0.0.0 | `raw.githubusercontent.com/CEDStandards/CEDS-Ontology/V14.0.0.0/src/CEDS-Ontology.rdf` | 20,247,983 bytes, 243,601 triples | **Yes**, tag-pinned; SHA-256 begins `26d782b6047236e8` |
| ASN schema | `http://purl.org/ASN/schema/core/` | HTTP 200, 46,197 bytes, `application/rdf+xml`, 465 triples | No |
| Common Standards Project | `api.commonstandardsproject.com/api/v1` | 771 jurisdictions, 23,713 standard sets listed, 23,700 fetched, 1,931,913 statement rows | No |
| Georgia CASE server | `case.georgiastandards.org/ims/case/v1p0` | 60 CFDocuments; one package fetched in full: 2,453 CFItems, 2,483 CFAssociations | No |
| ASN resource identifiers | `asn.jesandco.org/resources/{id}` | 44,084 + 3,057 + 20,000 dereferenced | n/a |

The CEDS ontology fetched from the pinned tag is **byte-identical** to the file analysed, confirmed by
checksum comparison. That measurement is reproducible exactly. Nothing else here is.

## Verified facts about the ASN indirection layer

Checked directly rather than assumed, because the whole link-rot finding depends on it:

- `http://purl.org/ASN/resources/S1143FA1` → 404, having redirected to `https://asn.jesandco.org/resources/S1143FA1`.
- `http://purl.org/ASN/schema/core/` → **200**, redirecting to `s3.amazonaws.com/jestaticd2l/purl/schema/standard`, `application/rdf+xml`.
- `http://purl.org/ASN/scheme/ASNEducationLevel/` → **200**, via `elastic1.asn.desire2learn.com`.
- `https://asn.desire2learn.com/` → 200. The site is up. `/resources/{id}` under it returns 404.
- The S3 bucket `jestaticd2l` returns `AccessDenied` to a listing request, so its full contents could not be enumerated.

So: the schema and the education-level scheme survive; the resource identifiers do not. That asymmetry
is the finding, and it is stronger than "the service is down" because the service is not down.

## Which host was censused, and why

The canonical identifier form is `http://purl.org/ASN/resources/{id}`. That layer rate-limits hard: an
early probe of 60 identifiers at 8 concurrent returned **50 HTTP 429s and 10 404s**. Censusing 44,084
identifiers through it would have been hostile and would have measured the rate limiter, not the data.

The redirect target was therefore verified once, confirmed stable across a sample checked in both forms,
and the censuses were run against the origin host `asn.jesandco.org` at 10 concurrent with backoff. The
PURL layer's own behaviour is reported separately above rather than folded into the census numbers.

## Census results

| Census | Population | n | Method | 404 | 2xx |
|---|---:|---:|---|---:|---:|
| A: cited in public code | 44,084 | 44,084 | Census | 44,084 | 0 |
| B: document identifiers in live corpus | 3,057 | 3,057 | Census | 3,057 | 0 |
| C: statement identifiers in live corpus | 770,861 | 20,000 | Random sample, seed 20260816 | 20,000 | 0 |

Census C is a sample because a full census of 770,861 identifiers at a polite request rate would have
taken roughly eleven hours. At n = 20,000 with zero successes the 95% Wilson upper bound on the
resolving proportion is under 0.02%.

The population for census A was built by searching public code hosting for ASN resource URIs: 494 files
matched, 462 yielded at least one URI, across 52 repositories, giving 46,007 distinct URIs of which
44,084 are in canonical ASN identifier form. Repositories include `dcmi/lrmi` and `dcmi/ldci` (DCMI's own
published examples), `LearningRegistry/LearningRegistry`, `inbloom/APP-tagger`, `NCAR/dls-repository-stack`,
and `t3-innovation-network/desm`, `cassproject/cass-editor`, and `1EdTech/qti-examples`.

The 1EdTech case was checked individually because it is the sharpest: the organisation that publishes
CASE, the specification which succeeded ASN, ships `qtiv3-examples/packaging/ccPackage/imsmanifest.xml`
containing nine `purl.org/ASN/resources/` references. All nine return 404 in both the PURL form and at
the origin; `S113AA2C` and `S113AA2D` were verified by hand.

## Could not be obtained

- **A full enumeration of the ASN S3 bucket.** Listing is denied. Whether an archived data dump exists
  there is unknown, so no claim is made about it either way.
- **A full census of all 770,861 corpus statement identifiers.** Sampled instead, stated as such.
- **CASE coverage beyond one live package.** The Georgia server exposes 60 documents; one was fetched in
  full. The 98.8% structural-association figure is therefore a single-package measurement and is labelled
  that way everywhere it appears. It should not be generalised to CASE as a whole without more packages.
- **`ceds.ed.gov/ontology/`** returns HTTP 403 to an automated request. The GitHub repository was used
  instead, which is the source the CEDS README itself points to.
- **Demand-side research.** A planned survey of ontology and knowledge-graph hiring across education
  publishers was not completed; the agents running it terminated early. The HMH Ontology Engineer posting
  was verified directly (live, posted 30 July 2026, remote, $100,000-$115,000, requiring BFO, DOLCE,
  Common Core Ontologies or OBO Foundry experience). No broader market claim is made.

## Uncertainties and judgement calls

- **Surrogate documents.** 13,710 of 23,700 harvested standard sets carry no document record. Every
  statement needs exactly one container for the hierarchy to be versionable, so the set itself is used as
  a surrogate. These are flagged `lso:surrogateContainer true` in the graph and counted separately:
  **3,057 source-declared documents, 13,710 surrogates**. Reporting 16,767 documents without that split
  would overstate the corpus roughly fivefold.
- **Disjunctive reading of multiple domains and ranges.** Described in the README and `docs/METHOD.md`.
  It lowered ASN's falsifiability score from 3 to 1. The stricter reading would have flattered this
  repository's comparison and was rejected for that reason.
- **The Common Standards Project is an aggregator, not an authority.** Where it disagrees with a state
  education agency, the state is right. Its coverage is uneven, and counts describe that corpus rather
  than the universe of American academic standards.
- **`asn_not_in_census`: 972,789 identifier assertions in the graph carry no resolution observation**,
  because only censuses A, B and C were run. Absence of an observation is modelled as absence, never as
  a successful resolution.
- **Statement text comparison for collisions is exact-match after whitespace stripping.** Two records
  differing only by punctuation count as divergent. The 433 figure is therefore an upper bound on hard
  collisions; the worked example was inspected by hand and verified against the live API.

## Graph build

| Quantity | Value |
|---|---:|
| Triples | 21,404,069 |
| Turtle file size | 2.0 GB |
| Statements in scope (carrying an ASN identifier, plus ancestors) | 993,098 |
| Identifier assertions: ASN | 996,049 |
| Identifier assertions: human coding scheme | 674,233 |
| Jurisdictions | 771 |
| Documents (source-declared / surrogate) | 3,057 / 13,710 |
| Adoptions (Published / Deprecated / Unstated) | 4,911 / 1,543 / 10,314 |
| CASE items and associations imported | 2,453 / 2,483 |

The graph is streamed as Turtle rather than assembled in memory, because a 21-million-triple rdflib
build is not reproducible on a laptop. Well-formedness was verified by parsing the first 400,002 lines
into rdflib, yielding 399,996 triples with no syntax errors.

The layer-3 rules are published as SHACL-SPARQL for portability but are executed set-based by
`pipeline/governance_report.py`, because multi-way self-joins at this scale exceed what rdflib can do in
reasonable time. The same limit was documented for the investment fund ontology at 1.29M triples, and
this graph is sixteen times larger. The SHACL is validated against the worked example, where it produces
exactly the expected findings: R1 (orphaned statement) and R6 (no licence stated).

## Corrections made during the build

1. The falsifiability checker's conjunctive range reading, described above. ASN 3 → 1.
2. The `fetch_data.sh` CEDS URL was initially wrong (a guessed path that returned 404). Replaced with
   the verified tag-pinned path and confirmed byte-identical to the analysed file.
3. A worked collision was first attributed to Ohio. The jurisdiction identifier resolves to **Arizona**.
   Corrected before publication.
4. The repository count for census A was first written as 55, which is the number of repositories
   containing matching files. 52 repositories actually yielded URIs. The lower, correct figure is used.
