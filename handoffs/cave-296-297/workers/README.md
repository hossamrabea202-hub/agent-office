# Fixes after the Master's pastes of #341 / #349 (adjustedfilm, 2026-10-31 night)

## #349 miners: gear on the right bones

UE 5.3 Python can't set a component's parent socket, so the pick, helmet and satchel sat at the body root.

**Fix:** open **BP_MineWorker** and paste `BP_MineWorker_Gear_graph.txt` into its EventGraph (17 nodes, Validation OK).
It's a BeginPlay that snaps:
- Pick → `hand_r`;
- Helmet → `head` (+9 cm);
- Satchel → `spine_03`;
- Candle → onto the helmet.

If BP_MineWorker already has a BeginPlay, wire this chain after it instead (a one-minute fix).

**Test:** Play, go down. The miners hold the pick, wear the helmet with its candle light, and carry the satchel at the hip.

## #341 dungeon: no wall of fog underground

1. `py "<repo>/handoffs/cave-296-297/workers/setup_ugfog_ue.py" --dry-run`, then without it. It makes
   BP_UndergroundFog and places one.
2. Paste the 3 lines of `BP_UndergroundFog_BPVar.txt`, Compile, then paste `BP_UndergroundFog_graph.txt`
   (25 nodes, Validation OK, fix_impure no changes). Compile and save.

**Test:**
1. Take the door down: no fog in the dungeon.
2. Climb back up: the fog is back as before.
3. `DepthZ` (−2500 cm) is the line between up and down.
