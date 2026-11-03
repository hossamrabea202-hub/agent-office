# Faults from Alien's Play test (i9 chat 1205): i5's share F1, F3, F9, F11, F12

## F3 hero starts in the full Obsidian set / Vesna shows all 4 bundles FORGING: READY (data only, no paste)
- **Cause** (`f3_probe_ue.py`, read-only): the hero's own copy of BPC_ObsidianSet (BP_ThirdPersonCharacter > ObsidianSet) has
  **AvailMask = 0 and empty PieceId / PieceBone / PieceOffset / KnightCover** saved on it, which override the class data.
  - Nothing counts as available, so Vesna shows FORGING x4.
  - The piece table is empty, so the 15 Obsidian piece meshes on the hero (tags ObsK0..ObsK14, present) are never attached. Only the cuirass shows, through MPC Armor (gold/silver/black mix).
- **Fix** `f3_fix_ue.py`:
  - resets those 5 variables on the hero copy to the class values (AvailMask 991, 15 rows);
  - starts the set owned and worn (ObsOwned = ObsWorn = 991 = pieces 10-14 and 16-19);
  - the **Helm stays FORGING**, because it has no art yet (bit 5 is not in AvailMask).
- Steps (i9, Alien not in Play):
  1. `py handoffs/faults-1205/f3_fix_ue.py --dry-run`. Expect AvailMask 0 -> 991, PieceId 0 -> 15, ...
  2. `--apply` (backs up to `f3_backup.json`, compiles and saves the hero BP).
  3. Revert: `--revert`.
- Play test (**new game, delete the Obsidian save slot `CastleSaveObsidian` first**: an old save keeps its old state):
  - the hero wears shoulders, rerebraces, forearms, gauntlets, waist, thighs, greaves and boots plus the cuirass;
  - Vesna lists Torso, Gauntlets and Legs as owned and worn, and Helm as FORGING;
  - the set bonus shows 3/4.

## F1, F9, F11, F12: waiting for exports (request filed, chat 1222)
- F1 weaponsmith list over Vesna's shop: BPC_VesnaTrade, BP_ArmoryHUD, BPC_WeaponKit.
- F9 INFECTED notice: BP_NoticeHUD.
- F11 log errors: BPC_Muster (RQ empty, index 0..2) and BPC_ShieldKit (BlockChance index -1).
- F12 log error: BPC_WeaponKit (index 2 of a 2-long Data on Set Equipped / save load).

## F12 BPC_WeaponKit "index 2 of array Data length 2": READY (one pin, Master fixes on the spot)
- **Cause:** LoadSaved reads `Data[0]` (owned) and `Data[ wkAdd_IntInt56 ]` for **Equipped** (-> wkRound58 -> wkSetEquipped59).
  - `wkAdd_IntInt56` has A = 1 and **B = 1** (its C++ default: the intended 0 was lost on paste, the known Add_IntInt gotcha), so it reads `Data[2]`.
  - SaveNow writes only 2 values (MakeArray NumInputs = 2), so the read fails and Equipped is never restored. Every load fell back to weapon 0.
- **Fix:** BPC_WeaponKit > EventGraph, node `wkAdd_IntInt56` (the Add (int) just before the `Data` GET that feeds Set Equipped): set **B = 0**. Compile, save.
- Test: equip a non-default weapon, save, reload. The same weapon is equipped, and the log is free of "index 2 of array Data".
- Found with `t3d_arrays.js` (lists every array read in a whole-BP T3D, its array, its index source and its consumer).

## F11 log errors in BPC_Muster (RQ) and BPC_ShieldKit (BlockChance): READY (pre-checked merges)
- **Muster** "index 0..2 of array RQ length 0":
  - SetIState / SetINote / SetISub read RQ[0..2] behind `BooleanAND(RQ.Length > k, RQ[k] == 2)`. Blueprint's AND evaluates BOTH inputs, so the guard never protected the read.
  - Fix: copy RQ into a new RQ3, resize it to at least 3 (padding 0, never the 2 compared), and point the 3 reads at RQ3. Same result, no bad read.
- **ShieldKit** "index -1 of BlockChance": the hit roll read BlockChance[Worn] with Worn = -1 (no shield). Fix: `Branch(Worn >= 0)` in front of the roll. Its else does nothing, like the roll's own empty else.
- Files `f11/`: `gen_f11.py`, the small pastes, the manifests, and `*_merged.txt`. Merged with applyall on the live EventGraphs extracted from i9's export (`t3d_to_graph.js`): Validation OK, +7 / +3 links as expected; fix_impure: nothing to change.
- Steps (i9):
  1. `py handoffs/faults-1205/f11/add_rq3_ue.py` (adds the RQ3 int array to BPC_Muster).
  2. BPC_Muster EventGraph: Ctrl+A, BackSpace, Ctrl+V `f11/muster_merged.txt`, Refresh All Nodes, compile, save.
     Or, smaller: paste `f11/muster_rq3_paste.txt` and do the 5 rewires in `f11/muster_manifest.json`.
  3. BPC_ShieldKit EventGraph: Ctrl+A, BackSpace, Ctrl+V `f11/shield_merged.txt` (95 nodes), compile, save.
- Test: Play a wave with an empty recruit queue and with no shield. The log has no "array RQ" and no "BlockChance" errors. With a shield worn, blocks still happen.
