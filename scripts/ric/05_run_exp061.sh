#!/usr/bin/env bash
# EXP-061 step 6: timed runs. For each configuration a fresh nearRT-RIC and
# emulated gNB are started, the timing xApp subscribes, records, unsubscribes,
# and everything is stopped. Run ALONE: concurrent jobs contaminate the tail.
#   10 ms reporting period: all six radio models, 5,000 indications each
#    1 ms reporting period: LR and RF, 20,000 indications each (queueing stress)
set -uo pipefail
RIC=${RIC:-$HOME/ric}
REPO=${REPO:?set REPO to the repository path}
B="$RIC/flexric/build"
SM="$RIC/smlib/"
CONF="$RIC/flexric.conf"
M="$REPO/results/EXP-061/models"
OUT="$REPO/results/EXP-061/raw"
LOGS="$REPO/results/EXP-061/logs"
mkdir -p "$OUT" "$LOGS" "$SM"
find "$B/src/sm" -name '*.so' -exec ln -sf {} "$SM" \;
printf '[NEAR-RIC]\nNEAR_RIC_IP = 127.0.0.1\n\n[XAPP]\nDB_DIR = /tmp/\n' > "$CONF"
export LD_LIBRARY_PATH="$RIC/local/usr/lib/x86_64-linux-gnu"
LOCAL=$(mktemp -d)
cp "$M/windows.f32" "$M"/*.onnx "$M"/ref_*.f32 "$LOCAL/"

{
  echo "date: $(date -Is)"
  echo "kernel: $(uname -r)"
  echo "cpus: $(nproc)"
  grep -m1 'model name' /proc/cpuinfo
  echo "flexric: $(git -C "$RIC/flexric" describe --tags) $(git -C "$RIC/flexric" rev-parse --short HEAD)"
  echo "onnxruntime: 1.30.0 (C API)"
  echo "load before runs: $(cat /proc/loadavg)"
} > "$LOGS/host.txt"

run() {  # model period n warmup
  local key=$1 period=$2 n=$3 warm=$4 tag="$1_p$2"
  pkill -f nearRT-RIC; pkill -f emu_agent_gnb; sleep 1
  "$B/examples/ric/nearRT-RIC" -c "$CONF" -p "$SM" > /tmp/ric_$tag.log 2>&1 &
  sleep 2
  "$B/examples/emulator/agent/emu_agent_gnb" -c "$CONF" -p "$SM" > /tmp/gnb_$tag.log 2>&1 &
  sleep 3
  IDS_MODEL="$LOCAL/$key.onnx" IDS_WINDOWS="$LOCAL/windows.f32" IDS_REF="$LOCAL/ref_$key.f32" \
  IDS_PERIOD_MS=$period IDS_N=$n IDS_WARMUP=$warm IDS_OUT="$OUT/ric_$tag.csv" \
    "$B/examples/xApp/c/ids_timing/xapp_ids_timing" -c "$CONF" -p "$SM" > /tmp/xapp_$tag.log 2>&1
  local rc=$?
  pkill -f emu_agent_gnb; pkill -f nearRT-RIC; sleep 1
  { echo "== $tag rc=$rc"; grep '^\[IDS\]' /tmp/xapp_$tag.log; grep -c 'CONTROL-ACK' /tmp/xapp_$tag.log; } | tee -a "$LOGS/runs.txt"
  grep -i 'error\|assert\|abort' /tmp/xapp_$tag.log /tmp/ric_$tag.log /tmp/gnb_$tag.log | head -5 >> "$LOGS/runs.txt"
}

: > "$LOGS/runs.txt"
for key in tree logreg xgboost mlp hgb rf; do run $key 10 5000 200; done
for key in logreg rf; do run $key 1 20000 1000; done
echo "load after runs: $(cat /proc/loadavg)" >> "$LOGS/host.txt"
rm -rf "$LOCAL"
