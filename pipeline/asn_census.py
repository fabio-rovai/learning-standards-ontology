#!/usr/bin/env python3
"""Census: does each ASN identifier found in the public corpus still resolve?

Population is built by pipeline/harvest_asn_citations.py, which searches public code hosting for
files still citing ASN resource URIs. Every identifier in that population is dereferenced once and
its HTTP status recorded. This is a census, not a sample: no extrapolation is involved.

Requests go to the origin host. The purl.org indirection layer in front of it rate-limits
aggressively, and its redirect target is verified separately rather than by hammering it.

Usage:  python pipeline/asn_census.py --out data
"""
from __future__ import annotations
import argparse, collections, json, os, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

ORIGIN = "https://asn.jesandco.org/resources/{}"
UA = {"User-Agent": "Mozilla/5.0 (compatible; academic identifier-resolution census; "
                    "https://github.com/fabio-rovai/learning-standards-ontology)",
      "Accept": "application/rdf+xml, application/ld+json, text/html;q=0.8"}
CANON = re.compile(r"^[SD][0-9A-F]{6,8}$")
URI = re.compile(r"^https?://(?:purl\.org/ASN|asn\.jesandco\.org|asn\.desire2learn\.com)"
                 r"/resources/([A-Za-z0-9_\-]+)$")


def probe(i):
    for t in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(ORIGIN.format(i), headers=UA), timeout=25)
            return i, r.status, len(r.read(400))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (t + 1))
                continue
            return i, e.code, 0
        except Exception as e:
            if t == 2:
                return i, "ERR:" + type(e).__name__, 0
            time.sleep(3)
    return i, 429, 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--citations", default="data/asn_uris.json")
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()

    ids = collections.Counter()
    for u, c in json.load(open(a.citations))["uris"].items():
        m = URI.match(u.rstrip("."))
        if m and CANON.match(m.group(1)):
            ids[m.group(1)] += c
    pop = sorted(ids)
    print(f"population {len(pop):,} identifiers, {sum(ids.values()):,} citations", flush=True)

    res, rows, t0 = collections.Counter(), [], time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, (i, st, ln) in enumerate(ex.map(probe, pop), 1):
            res[st] += 1
            rows.append([i, st, ln, ids[i]])
            if n % 2500 == 0:
                print(f"  {n:,}/{len(pop):,} {dict(res)} {int(time.time()-t0)}s", flush=True)
    out = {"population": len(pop), "citations": sum(ids.values()), "n": len(rows),
           "status": {str(k): v for k, v in res.items()}, "rows": rows}
    json.dump(out, open(os.path.join(a.out, "asn_full.json"), "w"))
    print("FINAL", dict(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
