#!/usr/bin/env python3
"""Can these standards reject a wrong statement?

An ontology earns its keep by ruling things out. This script takes real harvested standards data,
injects mis-statements of six kinds, and asks each published artefact whether it can tell that
anything is wrong. Nothing here is a matter of opinion: a mutation is detected if and only if some
axiom actually present in the artefact is violated by it.

The checker is deliberately small and vocabulary-neutral, so the same code judges every artefact
by the same rule. It enforces exactly the axiom families that make contradiction possible:

    rdfs:domain, rdfs:range        a property used on the wrong kind of subject or object
    owl:disjointWith, AllDisjointClasses   an individual in two classes that cannot overlap
    owl:FunctionalProperty        two distinct values where at most one is allowed
    owl:IrreflexiveProperty       a property asserted of something and itself
    owl:AsymmetricProperty        a property asserted in both directions
    owl:maxCardinality            more values than the restriction permits

For LSO, pyshacl is additionally run over the repository's own SHACL layers, because SHACL is
where LSO puts constraints that OWL cannot express. Artefacts without shapes are not penalised
for that: they are simply reported as having none.

Usage:  python pipeline/falsifiability_test.py --out reports/FALSIFIABILITY.md
"""
from __future__ import annotations
import argparse, json, os, sys, collections, datetime, itertools
from rdflib import Graph, Namespace, URIRef, Literal, BNode, RDF, RDFS, OWL, XSD

LSO = Namespace("https://learning.tesseract.academy/lso#")
LSOS = Namespace("https://learning.tesseract.academy/lso/scheme/")
EX = Namespace("https://learning.tesseract.academy/lso/test/")
CEDS = Namespace("https://w3id.org/CEDStandards/terms/")
ASN = Namespace("http://purl.org/ASN/schema/core/")


# --------------------------------------------------------------------------
# The checker
# --------------------------------------------------------------------------
def violations(vocab: Graph, data: Graph) -> list[str]:
    """Return the axiom violations of `data` against the axioms declared in `vocab`."""
    out = []
    types = collections.defaultdict(set)
    for s, o in data.subject_objects(RDF.type):
        types[s].add(o)

    def supers(c, seen=None):
        seen = seen or set()
        if c in seen:
            return seen
        seen.add(c)
        for p in vocab.objects(c, RDFS.subClassOf):
            if isinstance(p, URIRef):
                supers(p, seen)
        return seen

    closed = {s: set(itertools.chain.from_iterable(supers(c) for c in cs)) for s, cs in types.items()}

    # Domain and range, read DISJUNCTIVELY when a property declares more than one.
    #
    # Strict RDFS says multiple rdfs:range declarations are conjunctive: the object must belong to
    # every declared range at once. Several real vocabularies plainly do not mean that. ASN declares
    # asn:isChildOf with range both StandardDocument and Statement, intending "either", and under the
    # strict reading every legitimate ASN parent link violates its own schema. Judging an artefact by
    # a reading its authors did not intend would manufacture findings, so the charitable disjunctive
    # reading is used here and the strict-reading defect is reported separately by
    # report_multi_domain_range().
    dom = collections.defaultdict(set)
    rng = collections.defaultdict(set)
    for p, d in vocab.subject_objects(RDFS.domain):
        if isinstance(d, URIRef):
            dom[p].add(d)
    for p, r in vocab.subject_objects(RDFS.range):
        if isinstance(r, URIRef):
            rng[p].add(r)
    for p, ds in dom.items():
        for s, o in data.subject_objects(p):
            if s in closed and not (ds & closed[s]):
                out.append(f"domain: <{p}> requires subject of type {sorted(str(x) for x in ds)}, "
                           f"got {sorted(str(x) for x in types[s])}")
    for p, rs in rng.items():
        if rs <= {RDFS.Literal, RDFS.Resource}:
            continue
        for s, o in data.subject_objects(p):
            if isinstance(o, URIRef) and o in closed and not (rs & closed[o]):
                out.append(f"range: <{p}> requires object of type {sorted(str(x) for x in rs)}, "
                           f"got {sorted(str(x) for x in types[o])}")

    # disjointness, pairwise and n-ary
    disjoint = set()
    for a, b in vocab.subject_objects(OWL.disjointWith):
        disjoint.add(frozenset((a, b)))
    for node in vocab.subjects(RDF.type, OWL.AllDisjointClasses):
        for lst in vocab.objects(node, OWL.members):
            members = list(vocab.items(lst))
            for a, b in itertools.combinations(members, 2):
                disjoint.add(frozenset((a, b)))
    for s, cs in closed.items():
        for pair in disjoint:
            if pair <= cs:
                out.append(f"disjoint: {s} is typed as both {sorted(str(x) for x in pair)}")

    # functional, irreflexive, asymmetric
    for p in vocab.subjects(RDF.type, OWL.FunctionalProperty):
        for s in set(data.subjects(p)):
            if len(set(data.objects(s, p))) > 1:
                out.append(f"functional: <{p}> has multiple values on {s}")
    for p in vocab.subjects(RDF.type, OWL.IrreflexiveProperty):
        for s, o in data.subject_objects(p):
            if s == o:
                out.append(f"irreflexive: <{p}> asserted of {s} and itself")
    for p in vocab.subjects(RDF.type, OWL.AsymmetricProperty):
        for s, o in data.subject_objects(p):
            if (o, p, s) in data:
                out.append(f"asymmetric: <{p}> asserted in both directions between {s} and {o}")

    # maxCardinality restrictions reachable from a declared subClassOf
    for r in vocab.subjects(RDF.type, OWL.Restriction):
        prop = vocab.value(r, OWL.onProperty)
        mx = vocab.value(r, OWL.maxCardinality) or vocab.value(r, OWL.cardinality)
        if prop is None or mx is None:
            continue
        for cls in vocab.subjects(RDFS.subClassOf, r):
            for s, cs in closed.items():
                if cls in cs and len(set(data.objects(s, prop))) > int(mx):
                    out.append(f"maxCardinality: {s} exceeds {int(mx)} values of <{prop}>")
    return out


# --------------------------------------------------------------------------
# The mutations
# --------------------------------------------------------------------------
def mutations() -> dict[str, Graph]:
    """Six wrong statements, each expressed against LSO's vocabulary."""
    M = {}

    g = Graph()
    g.add((EX.s1, RDF.type, LSO.StandardStatement))
    g.add((EX.s1, RDF.type, LSO.StandardsDocument))
    M["M1 a statement that is also a document"] = g

    g = Graph()
    g.add((EX.s1, RDF.type, LSO.StandardStatement))
    g.add((EX.s2, RDF.type, LSO.StandardStatement))
    g.add((EX.s1, LSO.hasParentStatement, EX.s2))
    g.add((EX.s2, LSO.hasParentStatement, EX.s1))
    M["M2 two statements each the parent of the other"] = g

    g = Graph()
    g.add((EX.s1, RDF.type, LSO.StandardStatement))
    g.add((EX.s1, LSO.hasParentStatement, EX.s1))
    M["M3 a statement that is its own parent"] = g

    g = Graph()
    g.add((EX.a1, RDF.type, LSO.AlignmentAssertion))
    g.add((EX.s1, RDF.type, LSO.StandardStatement))
    g.add((EX.s2, RDF.type, LSO.StandardStatement))
    g.add((EX.a1, LSO.alignmentSource, EX.s1))
    g.add((EX.a1, LSO.alignmentSource, EX.s2))
    g.add((EX.a1, LSO.alignmentTarget, EX.s2))
    g.add((EX.a1, LSO.alignmentPredicate, LSOS.exactMatch))
    M["M4 an alignment with two different source statements"] = g

    g = Graph()
    g.add((EX.d1, RDF.type, LSO.StandardsDocument))
    g.add((EX.j1, RDF.type, LSO.Jurisdiction))
    g.add((EX.d1, LSO.inDocument, EX.j1))
    M["M5 a document contained in a jurisdiction"] = g

    g = Graph()
    g.add((EX.ia, RDF.type, LSO.IdentifierAssertion))
    g.add((EX.ia, LSO.identifierScheme, LSOS.ASN))
    g.add((EX.ia, LSO.identifierScheme, LSOS.CASEGUID))
    g.add((EX.ia, LSO.identifierValue, Literal("S1143FA1")))
    M["M6 one identifier assertion belonging to two schemes"] = g

    return M


# Each artefact is judged in its OWN vocabulary. A mutation is translated term by term; if the
# artefact has no counterpart for a property the mutation needs, the mutation is INEXPRESSIBLE
# there and is reported as such. Counting an inexpressible sentence as "undetected" would be a
# rigged comparison: an artefact cannot be blamed for failing to reject a sentence it cannot form.
A = "http://purl.org/ASN/schema/core/"

VOCAB_MAP = {
    "ASN": {
        "classes": {LSO.StandardStatement: URIRef(A + "Statement"),
                    LSO.StandardsDocument: URIRef(A + "StandardDocument"),
                    LSO.Jurisdiction: URIRef(A + "JurisdictionScheme"),
                    LSO.AlignmentAssertion: None,
                    LSO.IdentifierAssertion: None},
        "props": {LSO.hasParentStatement: URIRef(A + "isChildOf"),
                  LSO.inDocument: URIRef(A + "isChildOf"),
                  LSO.alignmentSource: None, LSO.alignmentTarget: None,
                  LSO.alignmentPredicate: None,
                  LSO.identifierScheme: None, LSO.identifierValue: URIRef(A + "identifier")},
    },
    # CEDS names real domain entities (Course C200072, Organization C200239) but declares no
    # property that relates them and no rdfs:domain anywhere, so structural mutations have no
    # CEDS counterpart property at all.
    "CEDS": {
        "classes": {LSO.StandardStatement: CEDS["C200072"],      # Course
                    LSO.StandardsDocument: CEDS["C200072"],      # Course
                    LSO.Jurisdiction: CEDS["C200239"],           # Organization
                    LSO.AlignmentAssertion: None,
                    LSO.IdentifierAssertion: None},
        "props": {LSO.hasParentStatement: None, LSO.inDocument: None,
                  LSO.alignmentSource: None, LSO.alignmentTarget: None,
                  LSO.alignmentPredicate: None,
                  LSO.identifierScheme: None, LSO.identifierValue: None},
    },
}


def translate(g: Graph, target: str):
    """Return (graph, inexpressible_reason). Reason is None when fully translatable."""
    if target == "LSO":
        return g, None
    m = VOCAB_MAP[target]
    out = Graph()
    for s, p, o in g:
        if p == RDF.type:
            c = m["classes"].get(o, o)
            if c is None:
                return None, f"no counterpart class for {o.split('#')[-1]}"
            out.add((s, p, c))
        else:
            q = m["props"].get(p, p)
            if q is None:
                return None, f"no counterpart property for {p.split('#')[-1]}"
            out.add((s, q, o))
    return out, None


def report_multi_domain_range(vocab: Graph) -> list[str]:
    """Properties declaring more than one domain or range.

    Under strict RDFS these are conjunctions, so the property can only ever be used on something
    belonging to all of the declared classes at once. Where those classes are siblings with no
    common instances, the declaration is unsatisfiable and every ordinary use of the property
    violates it. This is reported rather than silently repaired.
    """
    out = []
    for pred, kind in ((RDFS.domain, "domain"), (RDFS.range, "range")):
        by = collections.defaultdict(set)
        for p, v in vocab.subject_objects(pred):
            if isinstance(v, URIRef):
                by[p].add(v)
        for p, vs in sorted(by.items()):
            if len(vs) > 1:
                out.append(f"<{p}> declares {len(vs)} {kind}s: {sorted(str(x).split('/')[-1] for x in vs)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="reports/FALSIFIABILITY.md")
    a = ap.parse_args()

    vocabs = {}
    lso = Graph()
    for f in ("ontology/lso-core.ttl", "skos/identifier-schemes.ttl"):
        lso.parse(f, format="turtle")
    vocabs["LSO (this repository)"] = lso

    p = os.path.join(a.data_dir, "CEDS-Ontology.rdf")
    if os.path.exists(p):
        g = Graph(); g.parse(p, format="xml"); vocabs["CEDS Ontology v14"] = g
    p = os.path.join(a.data_dir, "asn_schema.rdf")
    if os.path.exists(p):
        g = Graph(); g.parse(p, format="xml"); vocabs["ASN schema"] = g

    shapes = Graph()
    for f in ("shapes/lso-shapes.ttl", "shapes/lso-rules.ttl"):
        shapes.parse(f, format="turtle")

    M = mutations()
    rows, detail = [], []
    for vname, vg in vocabs.items():
        target = "CEDS" if "CEDS" in vname else ("ASN" if "ASN" in vname else "LSO")
        det = inx = 0
        per = {}
        for mname, mg in M.items():
            data, reason = translate(mg, target)
            if data is None:
                per[mname] = ("inexpressible", [reason])
                inx += 1
                continue
            v = violations(vg, data)
            hit = bool(v)
            if target == "LSO":
                from pyshacl import validate as shvalidate
                conforms, _, _ = shvalidate(data, shacl_graph=shapes, advanced=True,
                                            inference="none", abort_on_first=False)
                if not conforms:
                    hit = True
                    v = v + ["rejected by this repository's SHACL shapes"]
            per[mname] = ("detected" if hit else "not detected", v[:3])
            det += hit
        rows.append((vname, det, inx, len(M)))
        detail.append((vname, per))

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    L = ["# Can these standards reject a wrong statement?\n",
         f"Generated {stamp} by `pipeline/falsifiability_test.py`. Six mis-statements are put to each "
         "artefact, each translated into that artefact's own vocabulary. A mutation counts as detected "
         "only when an axiom actually present in that artefact is violated by it. Where the artefact "
         "has no term for what the mutation says, the result is *inexpressible*, not *not detected*: "
         "an artefact cannot be blamed for failing to reject a sentence it cannot form. Inexpressible "
         "is not a lesser failure than undetected, though. It means the artefact has nothing to say "
         "about that part of the domain at all.\n",
         "| Artefact | Detected | Expressible but undetected | Inexpressible |", "|---|---:|---:|---:|"]
    for v, d, i, n in rows:
        L.append(f"| {v} | **{d} of {n}** | {n - d - i} | {i} |")
    L.append("\n## Which mutation, which artefact\n")
    L.append("| Mutation | " + " | ".join(v for v, _, _, _ in rows) + " |")
    L.append("|---|" + "---|" * len(rows))
    for mname in M:
        L.append(f"| {mname} | " + " | ".join(per[mname][0] for _, per in detail) + " |")
    L.append("\n## Why each verdict\n")
    for vname, per in detail:
        L.append(f"\n### {vname}\n")
        for mname, (verdict, v) in per.items():
            if verdict == "detected":
                L.append(f"- **{mname}** — detected: {v[0] if v else ''}")
            elif verdict == "inexpressible":
                L.append(f"- {mname} — inexpressible: {v[0]}.")
            else:
                L.append(f"- {mname} — expressible, but undetected: the artefact declares no axiom this violates.")
    L.append("\n## Unsatisfiable domain and range declarations\n")
    L.append("Properties declaring more than one domain or range. RDFS reads these as conjunctions, "
             "so the property may only be used on something belonging to every declared class at "
             "once. Where the classes are siblings, ordinary correct usage violates the schema.\n")
    any_multi = False
    for vname, vg in vocabs.items():
        multi = report_multi_domain_range(vg)
        if multi:
            any_multi = True
            L.append(f"\n**{vname}** — {len(multi)}:\n")
            for m in multi:
                L.append(f"- `{m}`")
    if not any_multi:
        L.append("None found in any artefact examined.")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write("\n".join(L) + "\n")
    json.dump({"generated": stamp,
               "rows": [{"artefact": v, "detected": d, "inexpressible": i, "total": n} for v, d, i, n in rows]},
              open(a.out.replace(".md", ".json"), "w"), indent=1)
    print(f"wrote {a.out}")
    for v, d, i, n in rows:
        print(f"  {v}: detected {d}/{n}, inexpressible {i}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
