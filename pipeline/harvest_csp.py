#!/usr/bin/env python3
"""Harvest the Common Standards Project: jurisdictions, standard sets, and every standard.

The API is public and needs no key. It is the best surviving bridge between the ASN identifier
generation and the present, because it carries each standard's ASN identifier alongside its own.

Usage:  python pipeline/harvest_csp.py --out data
"""
from __future__ import annotations
import argparse, collections, gzip, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://api.commonstandardsproject.com/api/v1"
UA = {"User-Agent": "Mozilla/5.0 (compatible; learning-standards-ontology build)"}


def get(url, tries=3):
    for t in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90))
        except Exception as e:
            if t == tries - 1:
                return {"error": str(e)}
            time.sleep(2 + 3 * t)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    jpath = os.path.join(a.out, "csp_juris.json")
    if not os.path.exists(jpath):
        json.dump(get(f"{BASE}/jurisdictions"), open(jpath, "w"))
    J = json.load(open(jpath))["data"]
    print(f"jurisdictions: {len(J):,}", flush=True)

    sets, errs = [], 0
    def fetch_j(j):
        return j["id"], get(f"{BASE}/jurisdictions/{j['id']}")
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, (jid, d) in enumerate(ex.map(fetch_j, J), 1):
            if "error" in d:
                errs += 1
                continue
            for s in d.get("data", {}).get("standardSets", []):
                doc = s.get("document") or {}
                sets.append({"jid": jid, "sid": s["id"], "title": s.get("title"),
                             "subject": s.get("subject"), "levels": s.get("educationLevels"),
                             "asn": doc.get("asnIdentifier"), "docid": doc.get("id"),
                             "doctitle": doc.get("title"), "status": doc.get("publicationStatus"),
                             "valid": doc.get("valid"), "sourceURL": doc.get("sourceURL")})
            if n % 150 == 0:
                print(f"  jurisdictions {n}/{len(J)} sets={len(sets):,} errors={errs}", flush=True)
    json.dump(sets, open(os.path.join(a.out, "csp_sets.json"), "w"))
    print(f"standard sets: {len(sets):,} (jurisdiction errors: {errs})", flush=True)

    def fetch_set(s):
        d = get(f"{BASE}/standard_sets/{s['sid']}")
        if "error" in d:
            return None
        dd = d.get("data", {})
        doc = dd.get("document") or {}
        lic = dd.get("license")
        return {"sid": dd.get("id"), "jid": s["jid"], "title": dd.get("title"),
                "subject": dd.get("subject"), "normSubject": dd.get("normalizedSubject"),
                "levels": dd.get("educationLevels"), "cspStatus": dd.get("cspStatus"),
                "license": lic.get("title") if isinstance(lic, dict) else lic,
                "licenseURL": lic.get("URL") if isinstance(lic, dict) else None,
                "docid": doc.get("id"), "docasn": doc.get("asnIdentifier"),
                "docstatus": doc.get("publicationStatus"), "docvalid": doc.get("valid"),
                "docsource": doc.get("sourceURL"), "doctitle": doc.get("title"),
                "std": [{"id": v.get("id"), "asn": v.get("asnIdentifier"),
                         "notation": v.get("statementNotation"), "label": v.get("statementLabel"),
                         "depth": v.get("depth"), "parent": v.get("parentId"),
                         "anc": v.get("ancestorIds"), "desc": (v.get("description") or "")[:1200],
                         "comment": (v.get("comment") or "")[:400] or None}
                        for v in (dd.get("standards") or {}).values()]}

    res, bad, t0 = [], 0, time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, r in enumerate(ex.map(fetch_set, sets), 1):
            if r is None:
                bad += 1
            else:
                res.append(r)
            if n % 1000 == 0:
                print(f"  sets {n}/{len(sets)} ok={len(res):,} bad={bad} "
                      f"standards={sum(len(x['std']) for x in res):,} {int(time.time()-t0)}s", flush=True)
    with gzip.open(os.path.join(a.out, "csp_standards.json.gz"), "wt") as f:
        json.dump(res, f)
    allstd = [s for r in res for s in r["std"]]
    print(f"\nsets ok {len(res):,}, failed {bad}")
    print(f"standard rows {len(allstd):,}, distinct {len({s['id'] for s in allstd}):,}")
    print(f"distinct ASN statement identifiers {len({s['asn'] for s in allstd if s['asn']}):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
