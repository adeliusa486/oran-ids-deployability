#!/usr/bin/env bash
# EXP-061 step 3: smoke test. nearRT-RIC + emulated gNB (E2 agent) + stock KPM
# monitor xApp, all on 127.0.0.1 over SCTP. Confirms the E2 loop works before
# the timing xApp is added.
set -uo pipefail
RIC=${RIC:-$HOME/ric}
B="$RIC/flexric/build"
SM="$RIC/smlib/"
LOG="$RIC/logs/smoke"
mkdir -p "$SM" "$LOG"
find "$B/src/sm" -name '*.so' -exec ln -sf {} "$SM" \;
CONF="$RIC/flexric.conf"
printf '[NEAR-RIC]\nNEAR_RIC_IP = 127.0.0.1\n\n[XAPP]\nDB_DIR = %s/\n' "$LOG" > "$CONF"
export LD_LIBRARY_PATH="$RIC/local/usr/lib/x86_64-linux-gnu"

pkill -f nearRT-RIC; pkill -f emu_agent_gnb; sleep 1
"$B/examples/ric/nearRT-RIC" -c "$CONF" -p "$SM" > "$LOG/ric.log" 2>&1 &
sleep 2
"$B/examples/emulator/agent/emu_agent_gnb" -c "$CONF" -p "$SM" > "$LOG/gnb.log" 2>&1 &
sleep 3
timeout 20 "$B/examples/xApp/c/monitor/xapp_kpm_moni" -c "$CONF" -p "$SM" > "$LOG/xapp.log" 2>&1
echo "xapp exit: $?"
pkill -f emu_agent_gnb; pkill -f nearRT-RIC
echo "--- ric";  tail -8 "$LOG/ric.log"
echo "--- gnb";  tail -5 "$LOG/gnb.log"
echo "--- xapp"; grep -c 'ran_ue_id\|UE ID\|meas' "$LOG/xapp.log"; tail -15 "$LOG/xapp.log"
