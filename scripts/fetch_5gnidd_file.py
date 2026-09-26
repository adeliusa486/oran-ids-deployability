#!/usr/bin/env python3
"""Download one file of the 5G-NIDD dataset (Fairdata/IDA, CC BY 4.0).

Uses the same public endpoint as the Etsin web page: authorize one file of the
open dataset, then stream it from download.fairdata.fi. Each token is single use.
The requests go through curl: the authorize endpoint answers Python's urllib with
HTTP 500 but accepts curl.

Usage:  python scripts/fetch_5gnidd_file.py README.pdf data/raw/d_b/pcap
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

DATASET = "9d13ef28-2ca7-44b0-9950-225359afac65"
AUTH = "https://etsin.fairdata.fi/api/v3/download/authorize"


def fetch(path: str, out_dir: Path) -> Path:
    # names are given without the leading slash (Git Bash rewrites "/x" into a
    # Windows path) and the slash is added here
    path = "/" + path.lstrip("/")
    body = json.dumps({"cr_id": DATASET, "file": path}, separators=(",", ":"))
    # body on stdin: Windows argument quoting would strip the JSON quotes.
    # The endpoint sometimes answers HTTP 500; retry with a pause.
    for attempt in range(6):
        out = subprocess.run(["curl", "-sS", "-m", "60", "-X", "POST", "-H",
                              "Content-Type: application/json", "--data-binary", "@-", AUTH],
                             input=body, capture_output=True, text=True).stdout
        try:
            url = json.loads(out)["url"]
            break
        except (ValueError, KeyError):
            time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError(f"authorize failed for {path}: {out[:200]}")
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / path.strip("/").replace(" ", "_")
    subprocess.run(["curl", "-sS", "--fail", "-m", "7200", "-o", str(dst), url], check=True)
    h = hashlib.sha256()
    with dst.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    print(f"{path} -> {dst} {dst.stat().st_size} bytes sha256 {h.hexdigest()}")
    return dst


if __name__ == "__main__":
    fetch(sys.argv[1], Path(sys.argv[2]))
