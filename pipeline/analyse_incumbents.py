#!/usr/bin/env python3
"""Measure the logical capability of the incumbent standards in K-12 education data.

The question this answers is deliberately narrow and mechanical: given the published artefact,
how many statements about the world can it entail, and how many can it reject? Both questions
are answered by counting axioms of the kinds that produce entailment and contradiction. No
judgement is involved and every number is reproducible from the fetched file.

Artefacts examined:
  CEDS Ontology v14      https://w3id.org/CEDStandards/terms/   (US Department of Education)
  ASN schema             http://purl.org/ASN/schema/core/       (Achievement Standards Network)
  CASE package           any live CASE v1p0/v1p1 CFPackage endpoint
  LSO                    this repository

Usage:  python pipeline/analyse_incumbents.py --data-dir data --out reports/INCUMBENT_CAPABILITY.md
"""
from __future__ import annotations
import argparse, json, os, sys, collections, datetime
from rdflib import Graph, RDF, RDFS, OWL, SKOS, URIRef

# Axiom families. The first group creates entailments; the second creates the possibility of
# contradiction. An artefact scoring zero in the second group cannot be wrong about anything.
ENTAILING = [
    ("rdfs:subClassOf", RDFS.subClassOf), ("rdfs:subPropertyOf", RDFS.subPropertyOf),
    ("owl:equivalentClass", OWL.equivalentClass), ("owl:inverseOf", OWL.inverseOf),
    ("owl:TransitiveProperty", None), ("owl:SymmetricProperty", None),
    ("skos:broader", SKOS.broader), ("skos:narrower", SKOS.narrower),
]
REFUTING = [
    ("rdfs:domain", RDFS.domain), ("rdfs:range", RDFS.range),
    ("owl:disjointWith", OWL.disjointWith), ("owl:AllDisjointClasses", None),
    ("owl:FunctionalProperty", None), ("owl:InverseFunctionalProperty", None),
    ("owl:IrreflexiveProperty", None), ("owl:AsymmetricProperty", None),
    ("owl:someValuesFrom", OWL.someValuesFrom), ("owl:allValuesFrom", OWL.allValuesFrom),
    ("owl:cardinality", OWL.cardinality), ("owl:minCardinality", OWL.minCardinality),
    ("owl:maxCardinality", OWL.maxCardinality), ("owl:complementOf", OWL.complementOf),
    ("owl:propertyDisjointWith", OWL.propertyDisjointWith),
]
TYPED = {"owl:TransitiveProperty": OWL.TransitiveProperty, "owl:SymmetricProperty": OWL.SymmetricProperty,
         "owl:FunctionalProperty": OWL.FunctionalProperty,
         "owl:InverseFunctionalProperty": OWL.InverseFunctionalProperty,
         "owl:IrreflexiveProperty": OWL.IrreflexiveProperty,
         "owl:AsymmetricProperty": OWL.AsymmetricProperty,
         "owl:AllDisjointClasses": OWL.AllDisjointClasses}


def count_axioms(g: Graph) -> dict:
    out = {}
    for name, pred in ENTAILING + REFUTING:
        if name in TYPED:
            out[name] = len(set(g.subjects(RDF.type, TYPED[name])))
        else:
            out[name] = len(list(g.triples((None, pred, None))))
    return out


def profile(g: Graph, label: str) -> dict:
    ax = count_axioms(g)
    ext = collections.Counter()
    for s, p, o in g:
        for n in (s, o):
            if isinstance(n, URIRef):
                u = str(n)
                base = u.split("#")[0] + "#" if "#" in u else u.rsplit("/", 1)[0] + "/"
                ext[base] += 1
    return {
        "label": label,
        "triples": len(g),
        "classes": len(set(g.subjects(RDF.type, OWL.Class))),
        "objectProperties": len(set(g.subjects(RDF.type, OWL.ObjectProperty))),
        "datatypeProperties": len(set(g.subjects(RDF.type, OWL.DatatypeProperty))),
        "rdfProperties": len(set(g.subjects(RDF.type, RDF.Property))),
        "concepts": len(set(g.subjects(RDF.type, SKOS.Concept))),
        "conceptSchemes": len(set(g.subjects(RDF.type, SKOS.ConceptScheme))),
        "classesThatAreAlsoSchemes": len(set(g.subjects(RDF.type, OWL.Class)) & set(g.subjects(RDF.type, SKOS.ConceptScheme))),
        "externalAlignments": sum(len(list(g.triples((None, p, None))))
                                  for p in (SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch,
                                            SKOS.narrowMatch, SKOS.relatedMatch, OWL.sameAs)),
        "axioms": ax,
        "entailingTotal": sum(ax[n] for n, _ in ENTAILING),
        "refutingTotal": sum(ax[n] for n, _ in REFUTING),
        "namespaces": ext.most_common(8),
    }


def case_profile(pkg: dict, label: str) -> dict:
    """CASE is JSON, not RDF, so its capability is counted from its own association vocabulary."""
    items = pkg.get("CFItems", [])
    assoc = pkg.get("CFAssociations", [])
    types = collections.Counter(a.get("associationType") for a in assoc)
    structural = types.get("isChildOf", 0)
    return {
        "label": label,
        "cfItems": len(items),
        "cfAssociations": len(assoc),
        "associationTypes": types.most_common(),
        "structuralShare": (structural / len(assoc)) if assoc else None,
        "semanticAssociations": len(assoc) - structural,
        "crossFrameworkAssociations": sum(v for k, v in types.items()
                                          if k in ("exactMatchOf", "isPeerOf", "precedes", "exemplar")),
        "itemsWithHumanCodingScheme": sum(1 for i in items if i.get("humanCodingScheme")),
        "itemsWithoutHumanCodingScheme": sum(1 for i in items if not i.get("humanCodingScheme")),
        # CASE has no formal semantics: no axiom in the package can be contradicted by data.
        "entailingTotal": 0,
        "refutingTotal": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="reports/INCUMBENT_CAPABILITY.md")
    ap.add_argument("--repo-root", default=".")
    a = ap.parse_args()

    results, missing = [], []

    ceds = os.path.join(a.data_dir, "CEDS-Ontology.rdf")
    if os.path.exists(ceds):
        g = Graph(); g.parse(ceds, format="xml")
        results.append(profile(g, "CEDS Ontology v14 (US Department of Education)"))
    else:
        missing.append(ceds)

    asn = os.path.join(a.data_dir, "asn_schema.rdf")
    if os.path.exists(asn):
        g = Graph(); g.parse(asn, format="xml")
        results.append(profile(g, "ASN schema (Achievement Standards Network)"))
    else:
        missing.append(asn)

    for f in ("ontology/lso-core.ttl", "skos/identifier-schemes.ttl"):
        pass
    g = Graph()
    for f in ("ontology/lso-core.ttl", "skos/identifier-schemes.ttl"):
        p = os.path.join(a.repo_root, f)
        if os.path.exists(p): g.parse(p, format="turtle")
    if len(g): results.append(profile(g, "LSO (this repository)"))

    case_res = None
    cp = os.path.join(a.data_dir, "ga_case_package.json")
    if os.path.exists(cp):
        case_res = case_profile(json.load(open(cp)), "CASE package, Georgia Computer Science GSE (live)")
    else:
        missing.append(cp)

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    L = [f"# What the incumbent standards can entail, and what they can reject\n",
         f"Generated {stamp} by `pipeline/analyse_incumbents.py`. Every number below is counted "
         f"directly from the published artefact named in the row.\n",
         "## Axiom census\n",
         "| Artefact | Triples | Classes | Object props | Datatype props | Entailing axioms | Refuting axioms | External alignments |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        L.append(f"| {r['label']} | {r['triples']:,} | {r['classes']:,} | {r['objectProperties']:,} | "
                 f"{r['datatypeProperties']:,} | {r['entailingTotal']:,} | **{r['refutingTotal']:,}** | {r['externalAlignments']:,} |")
    L.append("\n*Refuting axioms* counts domains, ranges, disjointness, cardinality, functionality, "
             "irreflexivity, asymmetry and property disjointness: the axiom families that let data "
             "contradict the model. An artefact with none of them cannot be wrong about anything.\n")

    for r in results:
        L.append(f"\n### {r['label']}\n")
        L.append(f"- {r['triples']:,} triples, {r['classes']:,} `owl:Class`, "
                 f"{r['objectProperties']:,} `owl:ObjectProperty`, {r['datatypeProperties']:,} `owl:DatatypeProperty`, "
                 f"{r['rdfProperties']:,} bare `rdf:Property`.")
        if r["conceptSchemes"]:
            L.append(f"- {r['concepts']:,} `skos:Concept` across {r['conceptSchemes']:,} `skos:ConceptScheme`; "
                     f"{r['classesThatAreAlsoSchemes']:,} terms are typed as BOTH `owl:Class` and `skos:ConceptScheme`.")
        L.append(f"- External alignments to any other vocabulary: **{r['externalAlignments']:,}**.")
        nz = {k: v for k, v in r["axioms"].items() if v}
        zero = [k for k, v in r["axioms"].items() if not v]
        L.append(f"- Axioms present: {', '.join(f'`{k}` {v:,}' for k, v in sorted(nz.items())) or 'none'}.")
        L.append(f"- Axioms absent entirely: {', '.join(f'`{k}`' for k in sorted(zero)) or 'none'}.")

    if case_res:
        c = case_res
        L.append(f"\n### {c['label']}\n")
        L.append(f"- {c['cfItems']:,} CFItems, {c['cfAssociations']:,} CFAssociations.")
        L.append(f"- Association types: {', '.join(f'`{k}` {v:,}' for k, v in c['associationTypes'])}.")
        if c["structuralShare"] is not None:
            L.append(f"- **{c['structuralShare']*100:.1f}%** of associations are `isChildOf`, which is document "
                     f"structure rather than a correspondence between frameworks. Cross-framework associations "
                     f"(`exactMatchOf`, `isPeerOf`, `precedes`, `exemplar`): **{c['crossFrameworkAssociations']:,}**.")
        L.append(f"- Items carrying a human coding scheme: {c['itemsWithHumanCodingScheme']:,}; without: "
                 f"{c['itemsWithoutHumanCodingScheme']:,}.")
        L.append("- CASE defines no logical axioms, so no assertion expressed in a CASE package can "
                 "contradict the CASE specification. Its JSON schema constrains shape, not meaning.")

    if missing:
        L.append("\n## Inputs not present in this run\n")
        for m in missing:
            L.append(f"- `{m}` — not found; the corresponding row is omitted rather than estimated.")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write("\n".join(L) + "\n")
    json.dump({"generated": stamp, "rdf": results, "case": case_res},
              open(a.out.replace(".md", ".json"), "w"), indent=1)
    print(f"wrote {a.out}")
    for r in results:
        print(f"  {r['label']}: entailing={r['entailingTotal']} refuting={r['refutingTotal']}")
    if case_res:
        print(f"  {case_res['label']}: structural share={case_res['structuralShare']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
