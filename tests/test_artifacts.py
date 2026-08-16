"""Offline tests. Every one runs against files committed to this repository, with no network."""
import os, re, pytest
from rdflib import Graph, RDF, RDFS, OWL, SKOS, URIRef

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LSO = "https://learning.tesseract.academy/lso#"
TTL = ["ontology/lso-core.ttl", "skos/identifier-schemes.ttl",
       "shapes/lso-shapes.ttl", "shapes/lso-rules.ttl", "examples/worked-example.ttl"]


@pytest.mark.parametrize("f", TTL)
def test_turtle_parses(f):
    p = os.path.join(ROOT, f)
    if not os.path.exists(p):
        pytest.skip(f"{f} not present")
    g = Graph()
    g.parse(p, format="turtle")
    assert len(g) > 0


def load_vocab():
    g = Graph()
    for f in ("ontology/lso-core.ttl", "skos/identifier-schemes.ttl"):
        g.parse(os.path.join(ROOT, f), format="turtle")
    return g


def test_every_class_has_a_label_and_definition():
    g = load_vocab()
    for c in g.subjects(RDF.type, OWL.Class):
        if isinstance(c, URIRef) and str(c).startswith(LSO):
            assert g.value(c, RDFS.label), f"{c} has no rdfs:label"


def test_every_property_declares_domain_and_range():
    """The defect measured in CEDS v14 must not reappear here."""
    g = load_vocab()
    missing = []
    for t in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for p in g.subjects(RDF.type, t):
            if not str(p).startswith(LSO):
                continue
            if not g.value(p, RDFS.domain) or not g.value(p, RDFS.range):
                missing.append(str(p))
    assert not missing, f"properties without both domain and range: {missing}"


def test_no_property_declares_more_than_one_domain_or_range():
    """The defect measured in the ASN schema must not reappear here: multiple domains are
    conjunctive under RDFS, and sibling classes make them unsatisfiable."""
    g = load_vocab()
    bad = []
    for pred in (RDFS.domain, RDFS.range):
        for p in set(g.subjects(pred, None)):
            vals = [v for v in g.objects(p, pred) if isinstance(v, URIRef)]
            if len(vals) > 1:
                bad.append((str(p), str(pred), len(vals)))
    assert not bad, f"multiple domain/range declarations: {bad}"


def test_ontology_declares_disjointness():
    g = load_vocab()
    n = len(set(g.subjects(RDF.type, OWL.AllDisjointClasses))) + len(list(g.triples((None, OWL.disjointWith, None))))
    assert n > 0, "an ontology with no disjointness cannot reject anything"


def test_no_term_is_both_class_and_concept_scheme():
    """CEDS v14 types 965 terms as both. It is a category error and it is not repeated here."""
    g = load_vocab()
    both = set(g.subjects(RDF.type, OWL.Class)) & set(g.subjects(RDF.type, SKOS.ConceptScheme))
    assert not both, f"terms typed as both owl:Class and skos:ConceptScheme: {both}"


def test_every_identifier_scheme_declares_scope_and_custody():
    g = load_vocab()
    for s in g.subjects(RDF.type, URIRef(LSO + "IdentifierScheme")):
        assert g.value(s, URIRef(LSO + "schemeScope")), f"{s} declares no scope"
        assert g.value(s, URIRef(LSO + "custodyStatus")), f"{s} declares no custody status"


def test_syntax_patterns_are_valid_regexes_and_match_their_examples():
    g = load_vocab()
    for s, pat in g.subject_objects(URIRef(LSO + "syntaxPattern")):
        re.compile(str(pat))
    asn = re.compile(str(g.value(URIRef("https://learning.tesseract.academy/lso/scheme/ASN"),
                                 URIRef(LSO + "syntaxPattern"))))
    assert asn.match("S1143FA1") and asn.match("D1000255")
    assert not asn.match("not-an-asn-id")
