#!/usr/bin/env python3
"""Fetch public Michigan graph only after user has reviewed upstream license.

The downloaded byte sequence must match the pinned Git blob identifier.
The source is CC BY-NC 4.0 and subject to Redistricting Data Hub conditions;
this repository does not redistribute the graph.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/eveomett-states/Michigan/main/mi.json"
SOURCE_PAGE = "https://github.com/eveomett-states/Michigan"
EXPECTED_GIT_BLOB = "a4dfe70818f87b97924781216f3d86a672cfc66a"

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destination", type=Path,
                    default=Path("data/raw/mi/mi/mi.json"))
    ap.add_argument("--acknowledge-source-terms", action="store_true")
    args = ap.parse_args()
    if not args.acknowledge_source_terms:
        ap.error("Read upstream CC BY-NC 4.0 and RDH license/terms, then pass --acknowledge-source-terms")
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "research-reproducibility-checker"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    sha = git_blob_sha(data)
    if sha != EXPECTED_GIT_BLOB:
        raise ValueError(f"Source has changed: Git blob {sha}, expected {EXPECTED_GIT_BLOB}; refusing to write")
    dest = args.destination
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=dest.parent, delete=False) as temp:
        temp.write(data)
        temp_name = temp.name
    os.replace(temp_name, dest)
    manifest = {
        "source": SOURCE_PAGE, "download_url": SOURCE,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "git_blob_sha1": sha, "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "license": "CC BY-NC 4.0 plus RDH terms; verify upstream restrictions",
        "status": "bytes checked against pinned source blob; upstream preprocessing not independently re-run",
    }
    path = dest.with_suffix(dest.suffix + ".provenance.json")
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Verified and saved:", dest, "manifest:", path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
