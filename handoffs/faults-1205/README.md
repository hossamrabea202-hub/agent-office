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
