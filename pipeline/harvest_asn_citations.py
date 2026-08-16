#!/usr/bin/env python3
"""Find ASN resource identifiers still cited in public code and data.

This establishes the population for the resolution census. It searches public code hosting for
files containing ASN resource URIs, fetches each matching file, and extracts every ASN URI it
contains. The point is to measure identifiers that real published artefacts still depend on, not
identifiers invented for the test.

Requires the GitHub CLI (`gh`) to be authenticated: `gh auth status`.

Usage:  python pipeline/harvest_asn_citations.py --out data
"""
from __future__ import annotations
import argparse, base64, collections, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

QUERIES = ['"asn.jesandco.org/resources"', '"purl.org/ASN/resources"',
           '"asn.desire2learn.com/resources"', '"http://purl.org/ASN/resources/S"',
           'educationalAlignment "asn.jesandco.org"', '"asn.jesandco.org/resources/S" language:JSON']
URI = re.compile(r"https?://(?:purl\.org/ASN|asn\.jesandco\.org|asn\.desire2learn\.com)"
                 r"/resources/[A-Za-z0-9_\-\.]+")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    files = {}
    for q in QUERIES:
        for page in (1, 2):
            r = subprocess.run(["gh", "api", "-X", "GET", "search/code", "-f", f"q={q}",
                                "-f", "per_page=100", "-f", f"page={page}", "--jq",
                                ".items[] | [.repository.full_name, .path, .sha] | @tsv"],
                               capture_output=True, text=True, timeout=120)
            n = 0
            for line in r.stdout.strip().split("\n"):
                if line:
                    repo, path, sha = line.split("\t")[:3]
                    files[(repo, path)] = sha
                    n += 1
            print(f"  {q[:45]:<45} page {page}: +{n} (files {len(files)})", flush=True)
            if n < 100:
                break
            time.sleep(7)

    def blob(rec):
        repo, path, sha = rec
        try:
            o = subprocess.run(["gh", "api", f"repos/{repo}/git/blobs/{sha}", "--jq", ".content"],
                               capture_output=True, text=True, timeout=120)
            if o.returncode:
                return repo, []
            return repo, URI.findall(base64.b64decode(o.stdout).decode("utf-8", "replace"))
        except Exception:
            return repo, []

    uris, by_repo, ok = collections.Counter(), collections.defaultdict(set), 0
    recs = [[r, p, s] for (r, p), s in files.items()]
    with ThreadPoolExecutor(max_workers=10) as ex:
        for repo, found in ex.map(blob, recs):
            if found:
                ok += 1
            for u in found:
                uris[u] += 1
                by_repo[repo].add(u)
    json.dump({"uris": dict(uris), "by_repo": {k: sorted(v) for k, v in by_repo.items()},
               "files_searched": len(files), "files_with_uris": ok},
              open(os.path.join(a.out, "asn_uris.json"), "w"))
    print(f"\nfiles searched {len(files):,}, yielding URIs {ok:,}, across {len(by_repo)} repositories")
    print(f"distinct ASN resource URIs {len(uris):,}, total citations {sum(uris.values()):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
