#!/bin/sh
# Regenerate the helm (#485): builds low + high, bakes every channel in its own Blender process, writes textures + FBX.
#   sh run_bake.sh [SIZE=2048] [SAMPLES=24]     log: $WORK/bake.log ("ALL DONE" or "FAILED <stage>")
# WORK = scratch folder for .blend + raw EXR (about 500 MB, outside the repo); RENDER_THREADS caps the CPU so the laptop stays usable.
B="${BLENDER:-/c/Program Files/Blender Foundation/Blender 4.5/blender.exe}"
SRC="$(cd "$(dirname "$0")" && pwd -W 2>/dev/null || pwd)"
export SRC OUT="${OUT:-$SRC/..}" WORK="${WORK:-C:/Users/hossam.rabea/ckw/helmet}"
export BAKE_SIZE="${1:-2048}" BAKE_SAMPLES="${2:-24}" RENDER_THREADS="${RENDER_THREADS:-8}"
mkdir -p "$WORK"; LOG="$WORK/bake.log"; echo "start $(date)" > "$LOG"
for r in 1 3; do
  if CHEST_RES=$r "$B" -b --factory-startup -P "$SRC/build_helm.py" 2>&1 | grep -E "BUILD OK" >> "$LOG"; then :; else echo "FAILED build r$r" >> "$LOG"; exit 1; fi
done
run() {  # stage blend
  t0=$(date +%s)
  STAGE=$1 "$B" -b "$WORK/$2" -P "$SRC/bake_staged.py" > "$WORK/stage_$1.log" 2>&1
  grep -E "^TRIS" "$WORK/stage_$1.log" >> "$LOG"
  if grep -q "STAGE $1 OK\|STAGE $1 " "$WORK/stage_$1.log" && grep -q "OK" "$WORK/stage_$1.log"; then echo "$1 ok $(( $(date +%s) - t0 )) s" >> "$LOG"
  else grep -E "Error|Traceback|line [0-9]+" "$WORK/stage_$1.log" | tail -8 >> "$LOG"; echo "FAILED $1" >> "$LOG"; exit 1; fi
}
run prep helm_build_r1.blend
[ -n "$PREP_ONLY" ] && { echo "PREP ONLY" >> "$LOG"; exit 0; }
for s in BC RG MT AO Normal; do run $s bake_ready.blend; done
run finish bake_ready.blend
echo "ALL DONE $(date)" >> "$LOG"
