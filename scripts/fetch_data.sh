#!/usr/bin/env bash
# Fetch every public source this repository builds on.
#
# Nothing here needs an API key. Three of the four sources are served "current" rather than pinned
# to a snapshot, so a rerun will produce different totals from the ones published in README.md.
# That is stated rather than hidden: see the "Data currency" section of the README.
set -euo pipefail
OUT="${1:-data}"
mkdir -p "$OUT"
UA="Mozilla/5.0 (compatible; learning-standards-ontology build; https://github.com/fabio-rovai/learning-standards-ontology)"

echo "==> CEDS Ontology, release V14.0.0.0, pinned to the tag (Apache-2.0)"
curl -fsSL -A "$UA" -o "$OUT/CEDS-Ontology.rdf" \
  "https://raw.githubusercontent.com/CEDStandards/CEDS-Ontology/V14.0.0.0/src/CEDS-Ontology.rdf"

echo "==> ASN schema (still served, from a static object store)"
curl -fsSL -A "$UA" -H "Accept: application/rdf+xml" -o "$OUT/asn_schema.rdf" \
  "http://purl.org/ASN/schema/core/"

echo "==> Common Standards Project: jurisdictions"
curl -fsSL -A "$UA" -o "$OUT/csp_juris.json" \
  "https://api.commonstandardsproject.com/api/v1/jurisdictions"

echo "==> Georgia CASE server: document list"
curl -fsSL -A "$UA" -o "$OUT/ga_case_documents.json" \
  "https://case.georgiastandards.org/ims/case/v1p0/CFDocuments"

echo
echo "Jurisdiction detail, standard sets, standards and the ASN resolution census are fetched by"
echo "the pipeline itself, because each is thousands of requests:"
echo "  python pipeline/harvest_csp.py   --out data"
echo "  python pipeline/asn_census.py    --out data"
