#!/usr/bin/env bash
# EXP-063 step 2: re-extract 5G-NIDD flows with Zeek, the exporter behind D_A.
# Input: the dataset's GTP-removed pcapng archives (one capture per attack session
# and base station). Output: one conn.log per capture, copied to
# data/interim/d_b_zeek/<station>/<capture>.conn.log. Default Zeek settings;
# -C ignores checksums (the captures were taken after GTP decapsulation).
set -euo pipefail
Z=${Z:-$HOME/zeek}
REPO=${REPO:?set REPO to the repository path}
SRC="$REPO/data/raw/d_b/pcap"
WORK="$Z/nidd"
OUT="$REPO/data/interim/d_b_zeek"
mkdir -p "$WORK" "$OUT"
for zipf in "BS1_GTP_removed.zip" "BS2_GTP_removed.zip"; do
  st=${zipf%%_*}
  mkdir -p "$WORK/$st"
  if [ -z "$(ls "$WORK/$st"/*.pcapng 2>/dev/null)" ]; then
    python3 - "$SRC/$zipf" "$WORK/$st" <<'PY'
import sys, zipfile, os, shutil
z = zipfile.ZipFile(sys.argv[1])
for i in z.infolist():
    if i.filename.endswith(".pcapng"):
        with z.open(i) as s, open(os.path.join(sys.argv[2], os.path.basename(i.filename)), "wb") as d:
            shutil.copyfileobj(s, d, 1 << 22)
PY
  fi
done
"$Z/zeek" --version > "$OUT/zeek_version.txt"
run_one() {
  f=$1; st=$(basename "$(dirname "$f")"); cap=$(basename "$f" .pcapng)
  d="$Z/nidd/logs/$st/$cap"; mkdir -p "$d"; cd "$d"
  "$Z/zeek" -C -r "$f" LogAscii::use_json=F > zeek.stdout 2> zeek.stderr
  mkdir -p "$OUT/$st"; cp conn.log "$OUT/$st/$cap.conn.log"
  echo "$st/$cap $(grep -vc '^#' conn.log) flows"
}
export -f run_one; export Z OUT
ls "$WORK"/BS*/*.pcapng | xargs -P 10 -I{} bash -c 'run_one "$@"' _ {}
