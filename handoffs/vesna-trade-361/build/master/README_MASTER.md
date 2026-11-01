# Vesna's Trade (#380) — owner paste sheet (Master-prepared, 2026-11-01)

Files on the PC after download: `C:\Users\hossa\Documents\agent-office\handoffs\vesna-trade-361\build\` (setup script,
graph txt, manifest, trade_data) and `...\agent-office\assets\tga\VesnaTrade\textures\` (8 PNG) — already there.
Put these 3 helper files in `...\build\master\` (or anywhere) and run each by typing its full path in Unreal's **Python**
box (bottom bar, dropdown must say Python) + Enter. Read the `VESNA` lines in the Output Log after each.

1. `p1_dryrun.py` — changes nothing. Log must end with `VESNA: OK`. If `STOP`, send me the log.
2. `p2_apply.py` — creates the assets and the component.
3. Content Browser → `BPC_VesnaTrade` → open → EventGraph. Open `BPC_VesnaTrade_graph.txt` in Notepad, Ctrl+A,
   Ctrl+C, click in the EventGraph, Ctrl+V. Then File → Refresh All Nodes, Compile, Save.
4. `BP_ArmoryHUD` → EventGraph → Ctrl+A, Ctrl+C → Notepad → save as `C:\Users\hossa\Documents\live.t3d`.
5. `p3_merge.py` — log must say `Validation: OK`.
6. Back in BP_ArmoryHUD EventGraph: Ctrl+A, BackSpace, open `C:\Users\hossa\Documents\merged.t3d` in Notepad,
   Ctrl+A, Ctrl+C, click in the graph, Ctrl+V. Compile, Save.
7. Play → open Vesna's shop → the new ARMOUR screen. Checks are in `../README.md` (section Checks).

Undo: delete `BPC_VesnaTrade`, the `VesnaTrade`/`VTCapture` components on the hero, `/Game/CastleDefender/UI/Trade/Vesna`,
and paste `live.t3d` back into BP_ArmoryHUD.
