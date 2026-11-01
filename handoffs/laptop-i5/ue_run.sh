#!/bin/sh
# i5 core: run a .py in the editor through the inbox watcher and print its log entry.
#   sh ue_run.sh <script.py> [arg ...]      (waits up to 120 s)
INBOX=/c/Users/hossam.rabea/agent-office/handoffs/laptop-i5/ue_inbox
src="$1"; shift
name="$(basename "$src" .py)_$$"
before=$(wc -c < "$INBOX/_log.txt" 2>/dev/null || echo 0)
: > "$INBOX/$name.args"; for a in "$@"; do printf '%s\n' "$a" >> "$INBOX/$name.args"; done
cp "$src" "$INBOX/$name.py.tmp" && mv "$INBOX/$name.py.tmp" "$INBOX/$name.py"
i=0; while [ -f "$INBOX/$name.py" ] && [ $i -lt ${UE_WAIT:-240} ]; do sleep 0.5; i=$((i+1)); done
if [ -f "$INBOX/$name.py" ]; then echo "TIMEOUT: the editor did not pick up $name.py (busy or watcher not running)"; exit 1; fi
tail -c +$((before+1)) "$INBOX/_log.txt"
