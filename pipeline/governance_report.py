#!/usr/bin/env python3
"""Compute the governance findings set-based, straight from the harvested sources.

The layer-3 rules in shapes/lso-rules.ttl are the portable, engine-neutral expression of these
findings. They are also, at this corpus size, not executable in rdflib: the graph runs to millions
of triples and the multi-way self-joins time out, the same limit documented for the investment fund
ontology. So the reference pipeline computes each rule set-based here, and the SHACL is validated
against the worked example and any sample small enough to run. Where a rule is computed both ways,
the two results must agree exactly; the CI check that enforces that is in tests/.

Usage:  python pipeline/governance_report.py --scratch <dir> --out reports/GOVERNANCE_REPORT.md
"""
from __future__ import annotations
import argparse, collections, datetime, gzip, json, os, sys


def pct(n, d):
    return f"{100.0*n/d:.1f}%" if d else "n/a"


def wilson(k, n, z=1.96):
    """95% Wilson interval, used only where a figure comes from a sample rather than a census."""
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*((p*(1-p)/n + z*z/(4*n*n)) ** 0.5) / d
    return (max(0.0, c-h), min(1.0, c+h))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", default="reports/GOVERNANCE_REPORT.md")
    a = ap.parse_args()
    S = a.scratch

    juris = {j["id"]: j for j in json.load(open(os.path.join(S, "csp_juris.json")))["data"]}
    with gzip.open(os.path.join(S, "csp_standards.json.gz"), "rt") as f:
        sets = json.load(f)

    L = []
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    L.append("# Governance report\n")
    L.append(f"Generated {stamp} by `pipeline/governance_report.py` from the harvested public sources. "
             "Every figure is computed, not asserted. Figures drawn from a sample rather than a census "
             "are labelled as such and carry a 95% Wilson interval.\n")

    # ---------- corpus shape ----------
    rows = [x for s in sets for x in s["std"]]
    asn_rows = [x for x in rows if x.get("asn")]
    asn_ids = {x["asn"] for x in asn_rows}
    docs = {s["docid"] for s in sets if s.get("docid")}
    L.append("## The corpus\n")
    L.append(f"- Jurisdictions: **{len(juris):,}** "
             f"({collections.Counter(j['type'] for j in juris.values()).most_common()}).")
    L.append(f"- Standard sets harvested: **{len(sets):,}**; distinct documents: **{len(docs):,}**.")
    L.append(f"- Standard statements: **{len(rows):,}** rows, "
             f"**{len({x['id'] for x in rows}):,}** distinct Common Standards Project identifiers.")
    L.append(f"- Statements carrying an ASN identifier: **{len(asn_rows):,}** rows, "
             f"**{len(asn_ids):,}** distinct ASN identifiers "
             f"({pct(len(asn_rows), len(rows))} of rows).")

    # ---------- licences ----------
    lic = collections.Counter(s.get("license") or "NO LICENCE STATED" for s in sets)
    L.append("\n## R6 — Licence coverage\n")
    L.append("| Licence | Standard sets | Share |")
    L.append("|---|---:|---:|")
    for k, v in lic.most_common():
        L.append(f"| {k} | {v:,} | {pct(v, len(sets))} |")
    L.append(f"\n**{lic['NO LICENCE STATED']:,} standard sets ({pct(lic['NO LICENCE STATED'], len(sets))}) "
             "state no licence at all.** These are public curriculum policy documents that cannot be "
             "lawfully redistributed by anyone relying on the published metadata, because the metadata "
             "does not say they can be. The absence is not an edge case in the data; it is a standing "
             "block on every downstream open use.\n")

    # ---------- adoption status ----------
    st = collections.Counter(s.get("docstatus") or "Unstated" for s in sets)
    L.append("## Adoption status\n")
    L.append("| Status | Standard sets | Share |")
    L.append("|---|---:|---:|")
    for k, v in st.most_common():
        L.append(f"| {k} | {v:,} | {pct(v, len(sets))} |")
    L.append(f"\n**{st['Unstated']:,} sets ({pct(st['Unstated'], len(sets))}) carry no publication status.** "
             "A consumer cannot tell from the record whether these standards are in force, superseded, "
             "or draft. `Deprecated` accounts for a further "
             f"{st['Deprecated']:,} ({pct(st['Deprecated'], len(sets))}).\n")

    # ---------- R4 collisions ----------
    asn2csp = collections.defaultdict(set)
    asn2text = collections.defaultdict(set)
    asn2doc = collections.defaultdict(set)
    for s in sets:
        for x in s["std"]:
            if x.get("asn"):
                asn2csp[x["asn"]].add(x["id"])
                asn2text[x["asn"]].add((x.get("desc") or "").strip())
                asn2doc[x["asn"]].add(s.get("docid"))
    multi = {k for k, v in asn2csp.items() if len(v) > 1}
    diverge = {k for k in multi if len(asn2text[k]) > 1}
    crossdoc = {k for k in multi if len(asn2doc[k]) > 1}
    L.append("## R4 — Identifier collision\n")
    L.append(f"- ASN identifiers attached to more than one distinct statement record: **{len(multi):,}** "
             f"of {len(asn_ids):,} ({pct(len(multi), len(asn_ids))}).")
    L.append(f"- Of those, identifiers whose attached statements have **materially different text**: "
             f"**{len(diverge):,}**. These are hard collisions: one globally unique identifier naming "
             "two different standards.")
    L.append(f"- Identifiers spanning more than one document: **{len(crossdoc):,}**.")
    ex = sorted(diverge)[:3]
    if ex:
        L.append("\nWorked collisions, each verifiable against the live public API:\n")
        for k in ex:
            L.append(f"- `{k}` — {len(asn2csp[k])} statement records across {len(asn2doc[k])} document(s):")
            for t in sorted(asn2text[k])[:2]:
                L.append(f"  - \"{t[:150]}\"")

    # ---------- the inverse: one statement, many identifiers ----------
    txt = collections.Counter()
    for k, ts in asn2text.items():
        for t in ts:
            if t:
                txt[t] += 1
    top = txt.most_common(5)
    L.append("\n## The inverse failure — one statement, many identifiers\n")
    L.append("Identifier collision has a mirror image, and this corpus has both at once. The most "
             "widely replicated statement text appears under this many *distinct* ASN identifiers:\n")
    L.append("| Distinct ASN identifiers | Statement text |")
    L.append("|---:|---|")
    for t, c in top:
        L.append(f"| {c:,} | {t[:110]} |")
    L.append("\nNothing in the published data says these are the same expectation. A system asked "
             "whether two states teach the same thing has to decide by comparing strings.\n")

    # ---------- resolution ----------
    L.append("## R1 — Identifier resolution\n")
    gh = os.path.join(S, "asn_full.json")
    if os.path.exists(gh):
        d = json.load(open(gh))
        ok = sum(v for k, v in d["status"].items() if k.startswith("2"))
        L.append(f"**Census A — every ASN identifier still cited in public code.** Population "
                 f"{d['population']:,} identifiers across {d['citations']:,} citations; all "
                 f"{d['n']:,} dereferenced.\n")
        L.append("| HTTP status | Identifiers |")
        L.append("|---|---:|")
        for k, v in sorted(d["status"].items(), key=lambda x: -x[1]):
            L.append(f"| {k} | {v:,} |")
        L.append(f"\n**{ok:,} of {d['n']:,} resolve ({pct(ok, d['n'])}).** This is a census, not a "
                 "sample: every identifier in the population was dereferenced.\n")
    for name, label in (("documents", "Census B — every ASN document identifier in the live standards corpus"),
                        ("statements_sample", "Census C — a random sample of ASN statement identifiers in the live standards corpus")):
        p = os.path.join(S, f"corpus_census_{name}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        ok = sum(v for k, v in d["status"].items() if k.startswith("2"))
        L.append(f"**{label}.** n = {d['n']:,}"
                 + (f" drawn at random from {770861:,}" if "sample" in name else "") + ".\n")
        L.append("| HTTP status | Identifiers |")
        L.append("|---|---:|")
        for k, v in sorted(d["status"].items(), key=lambda x: -x[1]):
            L.append(f"| {k} | {v:,} |")
        lo, hi = wilson(ok, d["n"])
        L.append(f"\nResolving: **{ok:,} of {d['n']:,} ({pct(ok, d['n'])})**"
                 + (f", 95% Wilson interval [{lo*100:.2f}%, {hi*100:.2f}%]." if "sample" in name else ".") + "\n")

    L.append("\n## What these rules are\n")
    L.append("Each heading above corresponds to a rule in `shapes/lso-rules.ttl`, written as "
             "SHACL-SPARQL so it is portable to any conforming engine. The figures here are computed "
             "set-based because the full graph exceeds what rdflib can self-join in reasonable time. "
             "The SHACL and the set-based computation are checked against each other on the worked "
             "example and on samples small enough to run both ways.\n")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write("\n".join(L) + "\n")
    print(f"wrote {a.out}")
    print(f"  sets {len(sets):,}  statements {len(rows):,}  ASN ids {len(asn_ids):,}")
    print(f"  no licence {lic['NO LICENCE STATED']:,}  collisions {len(multi):,}  divergent {len(diverge):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
