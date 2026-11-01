#!/bin/sh
# i5 core (2026-11-01): run once the editor is back IN session CastleDefender3 (Multi-User). Re-applies the work that
# was done or prepared while the server was down, through the editor inbox (ue_inbox_watcher.py must be running):
#   1. checks the Multi-User connection (stops if not connected: everything would go to i5's disk copy again)
#   2. #419 un-mirror the 5 mirrored tentacles (shell fix), saves the level
#   3. #58 import the 3 cannon break stages + fill BPC_CannonBreak.StageMeshes (backup BPC_CannonBreak_BACKUP58)
#   4. #411 castle scroll setup (icon, BPC_CastleScroll, BP_ZombieHUD backup + component); the 2 graph pastes stay manual
#   sh handoffs/laptop-i5/rejoin_redo.sh
cd "$(dirname "$0")/.." || exit 1
RUN="sh laptop-i5/ue_run.sh"
cat > /tmp/mu_check.py <<'EOF'
import unreal
s = unreal.MultiUserClientStatics.get_multi_user_connection_status_detail()
print('MU', s, unreal.MultiUserClientStatics.get_multi_user_session_info().session_name)
EOF
st=$($RUN /tmp/mu_check.py)
echo "$st" | tail -1
echo "$st" | grep -q "CONNECTED: " || echo "$st" | grep -q "CastleDefender3" || { echo "NOT IN THE SESSION: stop."; exit 1; }
$RUN tentacle-skin-366/unmirror419_ue.py --apply | tail -9
$RUN cannon-break-58/i5/import_break58_ue.py | tail -6
$RUN castle-scroll-411/setup_scroll411_ue.py | tail -12
$RUN potions-74/setup_potion74_ue.py | tail -9
echo "Next by hand: paste castle-scroll-411/build/BPC_CastleScroll_graph.txt, then the hook + rewire_hook411_ue.py (README); then potions-74 the same way (README)."
