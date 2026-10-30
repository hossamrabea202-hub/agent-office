# Obsidian set v2: a set system that works with the pieces we have, and grows by one table row per piece

By `checkking (Claude)`, 2026-10-30, card #96. Owner asked for "a better system" for the in-game Obsidian set.
Built on the Master's 2026-10-30 export (`handoffs/exports/master/2026-10-30/BPC_ObsidianSet.t3d` and
`BP_ThirdPersonCharacter.t3d`). Graph check: **321 nodes, 390 links, Validation: OK**. Not compiled yet: that needs the
editor.

## What was wrong with v1 (found in today's exports)

1. **Nothing calls the set.** BPC_ObsidianSet is on the hero and the hero damage reads `ObsSet`, but no HUD calls
   `BuyPiece` or `SetPieceWorn`. Vesna still sells only the cuirass, through the old `ObsV` / `Armor.R` path. So in game
   the set can't be bought, worn or completed.
2. **All or nothing.** The bonus needs 11/11 pieces. 6 of the 11 have no game art yet, so the bonus can't be reached at all.
3. **Every piece costs a big HUD paste.** Each new piece meant a new HUD vector on BP_ZombieHUD, an equip remap in
   BP_QueueHUD, a carousel branch in BP_SkillTreeHUD (22 MB graph), a hero component and a material gate. 10 more pieces
   that way are 10 risky pastes.
4. **The pieces don't show.** Shoulders, gauntlets, boots and shins are static meshes with nothing that puts them on the
   hero.
5. Smaller bugs: `BuyPiece` on an owned piece raised the price count again, and `SetPieceWorn` could wear a piece you
   don't own.

## The new system

**One table, one component.** `pieces.csv` lists every piece: id, slot, side, the knight bone it rides on, and which knight
material slot it covers. `setup_set_v2_ue.py` reads it, finds the imported meshes and writes everything into
BPC_ObsidianSet. **Adding a piece later = import its mesh, re-run the setup script.** No graph, HUD or hero edit.

**Tiered bonus.** The set gets stronger as you wear more of it, so it works today and grows as the art lands:

| Pieces worn | Tier | Bonus | Look |
|---|---|---|---|
| 2 | 1 | damage taken -3 % | |
| 4 | 2 | damage taken -6 % | |
| 6 | 3 | damage taken -9 %, **ember shockwave** on hit (40 dmg, 4 m, 12 s) | embers + gold rim pulse |
| 8 | 4 | damage taken -12 %, shockwave recharges in 9 s | |
| 11 | 5 | damage taken -15 %, "Sovereign's Ember" | 0.8 s completion flash |

- Today's art (cuirass, pauldrons, gauntlets, sabatons, greaves) = 5 pieces = **tier 2** now, tier 3 with the next piece.
- The tier values live in `TierAt` / `TierDR` on the component: tune them there.
- **No hero paste needed:** the hero already multiplies by `1 - ObsSet.R x 0.15`. v2 writes `ObsSet.R = TierDR / 0.15`.
- **No material change needed:** `M_ObsidianSetAura` lights up at `R >= 0.5`, which is tier 3.

**Pieces on the hero.** The setup script adds one hidden StaticMeshComponent per piece mesh under KnightMesh. It reads the
knight's ref pose to get each piece's offset from its bone. At BeginPlay the component re-attaches each piece to its bone
(foot_l, calf_r, hand_l, upperarm_r, …) with that offset. When a piece is worn it shows, and `M_ObsidianSetAura` is its
overlay.

**Knight armour hidden underneath, without holes.** A knight material slot is swapped for `M_ObsHidden` only when
**every** piece that covers it is worn: arms = pauldrons + gauntlets + rerebraces + vambraces; legs = sabatons + greaves +
fauld + cuisses; helmet; cape. While the set is partial, the Obsidian plates sit over the knight armour. The chest keeps
its own `ArmorMode` gate (#52).

**The cuirass counts automatically.** Refresh reads `Armor.R` (the existing chest switch), so the cuirass you already buy
at Vesna counts as set piece 10 without any HUD change.

**Refresh** runs on every event and every 0.5 s. Visuals only change when the worn set changes.

**Same events as v1, so nothing breaks:** `BuyPiece(Id)`, `SetPieceWorn(Id, Worn)`, `BuyShield()`,
`LoadState(Owned, Worn, Bought, ShieldLvl)`, `PushZombies`. New events:
- `ToggleWear(Id)`, for a set panel.
- `DebugGiveAll()`, for tests.
- `BuyPiece` now refuses a piece with no art or one that's already owned, and puts a bought piece straight on.

## Steps (editor driver)

1. Import the pieces that aren't in yet. Run whichever of these haven't run:
   - `assets/checkking/Obsidian-Sovereign/Shoulders/import_shoulders_ue.py`
   - `assets/checkking/Obsidian-Sovereign/Gauntlets/import_gauntlets_ue.py`

   Boots and shins went in on 10-28.
2. If `M_ObsidianSetAura` isn't in the project yet, run `handoffs/obsidian-set-bonus-96/make_M_ObsidianSetAura.py`.
   Then run `py "<repo>/handoffs/obsidian-set-v2/setup_set_v2_ue.py"`.
   - It writes `setup_set_v2.txt`, with one line per piece row and the AvailMask.
   - It lists the knight's bones if a bone name in `pieces.csv` is wrong: fix the CSV and re-run.
3. Back up `BPC_ObsidianSet.uasset`. Open its EventGraph: click empty graph, Ctrl+A, BackSpace, then Ctrl+V
   `BPC_ObsidianSet_v2_graph.txt`. Confirm the Fix Self Context dialog if it appears, File > Refresh All Nodes, then
   Compile and Save.
4. Re-export and diff (`defdiff.py`): every pasted node is in `Nodes()`, and there are no orphan pins.
5. Play, then run `test_set_v2.py` with STEP set to `give`, `off13`, `none` and `buy`.

## Checks

1. `give`: the boots, greaves, gauntlets and pauldrons appear on the hero and follow the run and attack animations.
   Tier is 2 (4 pieces, or 5 with the cuirass worn) and damage is x0.94.
2. Screenshot the hero front and back (`tools/shot.js --card 96`). Check the plates sit on the body, not floating or
   sunk. If one is off, its bone in `pieces.csv` is the first suspect. The pieces aren't skinned (see below).
3. `off13`: the boots go away and come back, and the WornCount drops and returns.
4. `none`: everything hides, knight armour is complete again, ObsSet.R is 0.
5. `buy`: ids 15–20 are refused (no art), 11–14 are bought, and the price climbs 450, 650, 950, 1350.
6. Real Play for 2 minutes: no new runtime errors from BPC_ObsidianSet (`pie_smoke.py`).

## Known limits (decisions)

- **Decision: rigid attach, not skinning.** Each piece follows one bone. That's right for helmet, gauntlet plates,
  sabatons and greaves. Pauldrons and cuisses may show a seam at extreme poses. Skinned versions need the licensed
  knight FBX (issue #1). When those exist, a skinned piece just replaces its row's mesh.
- The gauntlet fingers are modelled in a relaxed curl and don't bend with the hand.
- Knockback immunity at tier 5 still needs a check wherever the hero gets launched (not in these exports).
- Per-piece DEF numbers from SPEC 1 aren't applied. **Decision:** the tier bonus is the set's stat, so damage stays in
  one place.

## Part 2 (next hand-off, on today's HUD exports): let the player use it

- **Vesna:** one carousel entry, "Obsidian Armoury". Prev/next pages through the pieces in AvailMask, showing each
  piece's name, state (owned or worn) and `NextPrice`. BUY = pay `NextPrice`, then `ObsidianSet.BuyPiece(Id)`.
  It's one branch in BP_SkillTreeHUD for all pieces, not one per piece.
- **Inventory:** an `OBSIDIAN SET 5/11 · TIER 2` line under the torso slot. Clicking it opens a small paper-doll panel
  with one toggle per owned piece, which calls `ToggleWear`.
- **Save:** BP_CastleSave stores ObsOwned / ObsWorn / ObsBought / ShieldLevel, and calls `LoadState` on load.

## Office rules applied

- **Industry secrets rule 10 (coherence):** every piece shares one overlay, one ember clock (game time) and one tier
  value, so the whole set always agrees.
- **Rule 1:** the piece look is unchanged here. The textures already passed the calibrated v2 lookdev.
- **Decal rule:** no decal or DBuffer setting is touched. Only new assets and new material slots on the hero are used.
