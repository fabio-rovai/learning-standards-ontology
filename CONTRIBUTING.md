# Contributing

## Data policy

Only openly licensed or public-domain source data is used, and **no harvested source data is
committed to this repository**. Several of the standards documents surveyed here state no licence
at all, which is one of the findings rather than an oversight on our part, and redistributing them
would be exactly the mistake the repository documents. Everything under `data/` is regenerable
from `scripts/fetch_data.sh` and the pipeline scripts.

If you contribute a new source, state its licence in the pull request. A source whose licence
cannot be established is recorded as unlicensed and not redistributed.

## Numbers

Every number in the README, the build report and the reports directory is produced by a script in
`pipeline/` and can be regenerated. If you change a number, change the script that produces it and
say in the pull request which figure moved and why. Do not hand-edit a figure into a document.

Where a figure comes from a source that is served "current" rather than pinned to a snapshot, say
so next to the figure. Three of this repository's four sources behave that way.

## Not repeating the defects we measure

The test suite enforces, on this ontology, the properties whose absence it measures in others:

- every property declares exactly one domain and one range (`test_every_property_declares_domain_and_range`,
  `test_no_property_declares_more_than_one_domain_or_range`),
- the ontology declares disjointness (`test_ontology_declares_disjointness`),
- no term is typed as both an `owl:Class` and a `skos:ConceptScheme` (`test_no_term_is_both_class_and_concept_scheme`),
- every identifier scheme declares its scope and its custody status.

A pull request that breaks one of these will fail CI, and that is deliberate.

## Running the checks

```bash
python -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/python -m pytest tests/ -v
```
