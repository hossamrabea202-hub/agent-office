#!/bin/bash
# usage: run_headless.sh <script.py> [log]  (zlab, headless)
S="$1"; L="${2:-/c/Users/hossam.rabea/ckw/ztools/last_log.txt}"
MSYS_NO_PATHCONV=1 "/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "C:/Users/hossam.rabea/ckw/zlab/zlab.uproject" -run=pythonscript -script="$S" -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput > "$L" 2>&1
grep -a "LogPython\|PROBE\|EXPORT\|IMPORT\|POP\|Error:" "$L" | grep -av "Display: " | tail -40
