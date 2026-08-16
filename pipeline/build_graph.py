#!/usr/bin/env python3
"""Build the LSO instance graph from the harvested public sources.

Sources, all public and all fetched by scripts/fetch_data.sh:
  Common Standards Project API   jurisdictions, standard sets, standards, ASN identifiers, licences
  ASN resolution census          the observed HTTP status of every ASN identifier found in the wild
  CASE package (live server)     associations, for the alignment side of the graph

Output is streamed Turtle rather than assembled in an rdflib Graph, because the ASN-scoped corpus
alone runs to millions of triples and an in-memory build is not reproducible on a laptop. The
result is parsed back in chunks by pipeline/validate.py to prove it is well-formed.

Usage:
  python pipeline/build_graph.py --scratch <dir> --out data/lso-graph.ttl --scope asn
"""
from __future__ import annotations
import argparse, gzip, json, os, re, sys, datetime, collections

LSO = "https://learning.tesseract.academy/lso#"
LSOS = "https://learning.tesseract.academy/lso/scheme/"
LSOD = "https://learning.tesseract.academy/lso/id/"

PREAMBLE = f"""@prefix lso:  <{LSO}> .
@prefix lsos: <{LSOS}> .
@prefix lsod: <{LSOD}> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

lsod:source-csp a prov:Agent ; rdfs:label "Common Standards Project public API" .
lsod:source-asn-census a prov:Agent ; rdfs:label "LSO ASN resolution census" .
lsod:source-case-ga a prov:Agent ; rdfs:label "Georgia Department of Education CASE server" .
"""

ESC = {'\\': r'\\', '"': r'\"', '\n': r'\n', '\r': r'\r', '\t': r'\t'}
_esc_re = re.compile(r'[\\"\n\r\t]')
SAFE = re.compile(r'[^A-Za-z0-9._~-]')


def lit(s) -> str:
    return '"' + _esc_re.sub(lambda m: ESC[m.group()], str(s)) + '"'


def slug(s) -> str:
    return SAFE.sub("_", str(s))[:120]


ADOPTION_STATUS = {"Published": "Published", "Deprecated": "Deprecated", "Draft": "Draft"}


class Writer:
    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")
        self.f.write(PREAMBLE)
        self.n = 0
        self.seen = set()

    def t(self, s, p, o):
        self.f.write(f"{s} {p} {o} .\n")
        self.n += 1

    def once(self, key) -> bool:
        if key in self.seen:
            return False
        self.seen.add(key)
        return True

    def close(self):
        self.f.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True, help="directory holding the harvested JSON")
    ap.add_argument("--out", default="data/lso-graph.ttl")
    ap.add_argument("--scope", choices=["asn", "all"], default="asn",
                    help="asn = statements carrying an ASN identifier plus their ancestors; all = every harvested statement")
    a = ap.parse_args()

    stamp = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    S = a.scratch

    juris = {j["id"]: j for j in json.load(open(os.path.join(S, "csp_juris.json")))["data"]}
    census = {}
    cpath = os.path.join(S, "asn_full.json")
    if os.path.exists(cpath):
        c = json.load(open(cpath))
        for row in c["rows"]:
            census[row[0]] = {"status": row[1], "citations": row[3]}
    print(f"jurisdictions={len(juris):,} asn_census={len(census):,}", flush=True)

    with gzip.open(os.path.join(S, "csp_standards.json.gz"), "rt") as f:
        sets = json.load(f)
    print(f"standard sets={len(sets):,}", flush=True)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    w = Writer(a.out)
    stats = collections.Counter()

    # ---- jurisdictions -------------------------------------------------
    for jid, j in juris.items():
        u = f"lsod:jurisdiction_{slug(jid)}"
        w.t(u, "a", "lso:Jurisdiction")
        w.t(u, "rdfs:label", lit((j.get("title") or "").strip()))
        w.t(u, "lso:jurisdictionType", lit(j.get("type")))
        ia = f"lsod:idassert_j_{slug(jid)}_csp"
        w.t(u, "lso:identifiedBy", ia)
        w.t(ia, "a", "lso:IdentifierAssertion")
        w.t(ia, "lso:identifierScheme", "lsos:CSP")
        w.t(ia, "lso:identifierValue", lit(jid))
        w.t(ia, "lso:assertedBy", "lsod:source-csp")
        stats["jurisdictions"] += 1

    # ---- documents, adoptions, statements ------------------------------
    stmt_rows = {}          # csp statement id -> record
    stmt_doc = {}           # csp statement id -> document id
    doc_meta = {}

    for st in sets:
        # 13,706 of the harvested standard sets carry no document record at all. Every statement
        # must sit in exactly one document for the hierarchy to be versionable, so the set itself is
        # used as a surrogate container. That is a modelling decision by this pipeline, not a fact
        # in the source, so surrogates are flagged in the graph and counted separately. Reporting
        # them as published documents would inflate the document count roughly fivefold.
        real = bool(st.get("docid"))
        docid = st.get("docid") or st.get("sid")
        if not docid:
            stats["sets_without_any_identifier"] += 1
            continue
        if not real:
            stats["surrogate_documents"] += 1
        m = doc_meta.setdefault(docid, {"surrogate": not real,
                                        "title": st.get("doctitle") or st.get("title"),
                                        "subject": st.get("subject"), "asn": st.get("docasn"),
                                        "source": st.get("docsource"), "licences": set(),
                                        "adoptions": set(), "valid": st.get("docvalid")})
        if st.get("license"):
            m["licences"].add(st["license"])
        m["adoptions"].add((st["jid"], st.get("docstatus")))
        for s in st["std"]:
            sid = s.get("id")
            if not sid:
                continue
            if sid not in stmt_rows:
                stmt_rows[sid] = s
                stmt_doc[sid] = docid
                stats["statements_distinct"] += 1
            stats["statement_rows"] += 1

    print(f"distinct documents={len(doc_meta):,} distinct statements={len(stmt_rows):,} "
          f"rows={stats['statement_rows']:,}", flush=True)

    # scope selection: ASN-identified statements plus every ancestor needed to keep trees whole
    if a.scope == "asn":
        keep = {sid for sid, s in stmt_rows.items() if s.get("asn")}
        frontier = set(keep)
        while frontier:
            nxt = set()
            for sid in frontier:
                p = stmt_rows[sid].get("parent")
                if p and p in stmt_rows and p not in keep:
                    keep.add(p); nxt.add(p)
            frontier = nxt
        stats["statements_in_scope"] = len(keep)
    else:
        keep = set(stmt_rows)
        stats["statements_in_scope"] = len(keep)
    keep_docs = {stmt_doc[s] for s in keep} | set(doc_meta)
    print(f"statements in scope={len(keep):,}", flush=True)

    for docid, m in doc_meta.items():
        if docid not in keep_docs:
            continue
        u = f"lsod:document_{slug(docid)}"
        w.t(u, "a", "lso:StandardsDocument")
        if m["surrogate"]:
            w.t(u, "lso:surrogateContainer", "true")
            stats["documents_surrogate"] += 1
        else:
            stats["documents_source_declared"] += 1
        if m["title"]:
            w.t(u, "lso:documentTitle", lit(m["title"]))
            w.t(u, "rdfs:label", lit(m["title"]))
        if m["subject"]:
            w.t(u, "lso:subjectArea", lit(m["subject"]))
        if m["source"]:
            w.t(u, "lso:sourceURL", f'{lit(m["source"])}^^xsd:anyURI')
        for lic in m["licences"]:
            w.t(u, "lso:licenceLabel", lit(lic))
            stats["documents_with_licence_row"] += 1
        if not m["licences"]:
            stats["documents_without_licence"] += 1
        ia = f"lsod:idassert_d_{slug(docid)}_csp"
        w.t(u, "lso:identifiedBy", ia)
        w.t(ia, "a", "lso:IdentifierAssertion")
        w.t(ia, "lso:identifierScheme", "lsos:CSP")
        w.t(ia, "lso:identifierValue", lit(docid))
        w.t(ia, "lso:assertedBy", "lsod:source-csp")
        if m["asn"]:
            emit_asn(w, u, f"d_{slug(docid)}", m["asn"], census, stamp, stats)
        for jid, status in m["adoptions"]:
            if jid not in juris:
                continue
            au = f"lsod:adoption_{slug(docid)}_{slug(jid)}"
            w.t(au, "a", "lso:Adoption")
            w.t(au, "lso:adoptionOf", u)
            w.t(au, "lso:adoptedBy", f"lsod:jurisdiction_{slug(jid)}")
            w.t(au, "lso:adoptionStatus", lit(ADOPTION_STATUS.get(status, "Unstated")))
            if m["valid"] and re.fullmatch(r"\d{4}", str(m["valid"])):
                w.t(au, "lso:validFrom", f'{lit(m["valid"])}^^xsd:gYear')
            stats["adoptions"] += 1
            stats[f"adoption_{ADOPTION_STATUS.get(status, 'Unstated')}"] += 1
            w.t(u, "lso:publishedBy", f"lsod:jurisdiction_{slug(jid)}")
        stats["documents"] += 1

    for sid in keep:
        s = stmt_rows[sid]
        u = f"lsod:statement_{slug(sid)}"
        w.t(u, "a", "lso:StandardStatement")
        w.t(u, "lso:inDocument", f"lsod:document_{slug(stmt_doc[sid])}")
        if s.get("desc"):
            w.t(u, "lso:statementText", lit(s["desc"]))
        if s.get("notation"):
            w.t(u, "lso:humanCodingScheme", lit(s["notation"]))
            ia = f"lsod:idassert_s_{slug(sid)}_hcs"
            w.t(u, "lso:identifiedBy", ia)
            w.t(ia, "a", "lso:IdentifierAssertion")
            w.t(ia, "lso:identifierScheme", "lsos:HumanCodingScheme")
            w.t(ia, "lso:identifierValue", lit(s["notation"]))
            w.t(ia, "lso:assertedBy", "lsod:source-csp")
            stats["hcs_assertions"] += 1
        if s.get("depth") is not None:
            w.t(u, "lso:statementDepth", f'"{int(s["depth"])}"^^xsd:nonNegativeInteger')
        p = s.get("parent")
        if p and p in keep:
            w.t(u, "lso:hasParentStatement", f"lsod:statement_{slug(p)}")
        for anc in (s.get("anc") or []):
            if anc in keep:
                w.t(u, "lso:hasAncestorStatement", f"lsod:statement_{slug(anc)}")
        ia = f"lsod:idassert_s_{slug(sid)}_csp"
        w.t(u, "lso:identifiedBy", ia)
        w.t(ia, "a", "lso:IdentifierAssertion")
        w.t(ia, "lso:identifierScheme", "lsos:CSP")
        w.t(ia, "lso:identifierValue", lit(sid))
        w.t(ia, "lso:assertedBy", "lsod:source-csp")
        if s.get("asn"):
            emit_asn(w, u, f"s_{slug(sid)}", s["asn"], census, stamp, stats)
        stats["statements"] += 1

    # ---- CASE alignments ------------------------------------------------
    gp = os.path.join(S, "ga_pkg.json")
    if os.path.exists(gp):
        pkg = json.load(open(gp))
        for assoc in pkg.get("CFAssociations", []):
            src = (assoc.get("originNodeURI") or {}).get("identifier")
            tgt = (assoc.get("destinationNodeURI") or {}).get("identifier")
            typ = assoc.get("associationType")
            if not (src and tgt and typ):
                continue
            pred = {"isChildOf": "lsos:isChildOf", "isRelatedTo": "lsos:isRelatedTo",
                    "exactMatchOf": "lsos:exactMatch", "isPeerOf": "lsos:isRelatedTo"}.get(typ)
            if not pred:
                stats[f"case_assoc_unmapped_{typ}"] += 1
                continue
            au = f"lsod:alignment_ga_{slug(assoc.get('identifier'))}"
            w.t(au, "a", "lso:AlignmentAssertion")
            w.t(au, "lso:alignmentSource", f"lsod:case_{slug(src)}")
            w.t(au, "lso:alignmentTarget", f"lsod:case_{slug(tgt)}")
            w.t(au, "lso:alignmentPredicate", pred)
            w.t(au, "lso:assertedBy", "lsod:source-case-ga")
            stats["case_alignments"] += 1
            stats[f"case_assoc_{typ}"] += 1
        for it in pkg.get("CFItems", []):
            iid = it.get("identifier")
            if not iid:
                continue
            u = f"lsod:case_{slug(iid)}"
            w.t(u, "a", "lso:StandardStatement")
            if it.get("fullStatement"):
                w.t(u, "lso:statementText", lit(it["fullStatement"][:1200]))
            if it.get("humanCodingScheme"):
                w.t(u, "lso:humanCodingScheme", lit(it["humanCodingScheme"]))
            ia = f"lsod:idassert_case_{slug(iid)}"
            w.t(u, "lso:identifiedBy", ia)
            w.t(ia, "a", "lso:IdentifierAssertion")
            w.t(ia, "lso:identifierScheme", "lsos:CASEGUID")
            w.t(ia, "lso:identifierValue", lit(iid))
            w.t(ia, "lso:assertedBy", "lsod:source-case-ga")
            stats["case_items"] += 1

    w.close()
    stats["triples"] = w.n
    print(json.dumps(dict(sorted(stats.items())), indent=1))
    json.dump({"generated": stamp, "scope": a.scope, "stats": dict(stats)},
              open("reports/BUILD_STATS.json", "w"), indent=1)
    print(f"\nwrote {a.out}: {w.n:,} triples")
    return 0


def emit_asn(w, artefact, key, value, census, stamp, stats):
    ia = f"lsod:idassert_{key}_asn"
    w.t(artefact, "lso:identifiedBy", ia)
    w.t(ia, "a", "lso:IdentifierAssertion")
    w.t(ia, "lso:identifierScheme", "lsos:ASN")
    w.t(ia, "lso:identifierValue", lit(value))
    w.t(ia, "lso:assertedBy", "lsod:source-csp")
    stats["asn_assertions"] += 1
    obs = census.get(value)
    if obs is None:
        stats["asn_not_in_census"] += 1
        return
    ou = f"lsod:obs_asn_{slug(value)}"
    w.t(ia, "lso:resolution", ou)
    w.t(ia, "lso:citationCount", f'"{int(obs["citations"])}"^^xsd:nonNegativeInteger')
    if w.once(("obs", value)):
        status = str(obs["status"])
        resolves = status.startswith("2")
        w.t(ou, "a", "lso:ResolutionObservation")
        w.t(ou, "lso:resolutionStatus", lit(status))
        w.t(ou, "lso:resolves", "true" if resolves else "false")
        w.t(ou, "lso:observedAt", f'{lit(stamp)}^^xsd:dateTime')
        w.t(ou, "lso:finalURL", f'{lit("https://asn.jesandco.org/resources/" + value)}^^xsd:anyURI')
        w.t(ou, "prov:wasAttributedTo", "lsod:source-asn-census")
    stats["asn_resolved" if str(obs["status"]).startswith("2") else "asn_dead"] += 1


if __name__ == "__main__":
    sys.exit(main())
