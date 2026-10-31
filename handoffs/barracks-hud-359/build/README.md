# The Muster: the barracks screen (#359), paste hand-off

By TGA (Claude), 2026-11-01. Night plan: the barracks HUD, in the same kit as the owner's Vesna's Trade look (#361 / #380).
- **Check image:** `../renders/muster_vs_trade.jpg` (Vesna's Trade on the left, the Muster on the right).
- **Checks:**

  | What | Result |
  |---|---|
  | Component graph | 1,559 nodes, `applyall check` **Validation: OK** |
  | ArmoryHUD hook merge, dry-run on top of the #380 merge (run twice) | **OK** |
  | The 4 add-on merges, dry-run on their generated graphs | **OK** |

  The BarracksHUD gate couldn't be dry-run: the 10-30b BarracksHUD export already has duplicate PinIds, so applyall refuses it as a base. It's a 4-node paste with 3 hand wires instead (step 5).
- **Not compiled yet:** that needs the editor.

## What the player gets
**At the barracks NPC, E opens the Muster.** The game pauses and the cursor shows. Esc (or B on a pad) closes it.

The old recruit-card screen is skipped while you stand at the barracks. The once-per-visit "[J] walls / [F] flares / [M] medic" notices are gone, but the keys still work.

| Tab | Rows | What happens on E / click |
|---|---|---|
| **RECRUIT** | Swordsman, Crossbowman, Commander, Medic, Mechanic | Recruits: pays the **same price as the old screen** (40 / 60 gold × 1.25^army, commander 300), then `BP_BarracksHUD.Enqueue(Kind)`, so they train in the #188 queue with its bar over the NPC. Medic: BPC_Medics' own buy (150, max 4). Mechanic: **locked**, because the workshop isn't built (#50 is spec only). |
| **ARTILLERY** | Cannon | BP_CannonOrder's own order: 800 gold, takes the next free wall pad, the convoy comes (#230). |
| **FORTIFY** | Walls, Towers, Gate | BPC_CastleUpgrades' own buy, level 1 then 2 (gold plus iron / copper / silver / gold ore, #224). Gate: info only, because the smith forges it (#208). |
| **SUPPLIES** | Crossbow flares | BPC_Flares' own buy (400, one-time, #277). |

- **Every row** shows its icon, name, a live sub-line (ARMY 7 / 10, MEDICS 1 / 4, LEVEL 1 / 2, FREE PADS 2…) and its state:
  - the price (red when you can't pay it);
  - OWNED;
  - AT BEST;
  - LOCKED;
  - FULL, with the reason in the centre: army full, queue full (3), you already have a Commander, no free pad…
- **Centre:**
  - name, tag and a big icon (with level pips for walls and towers);
  - **Cost** (gold plus the ores) next to the **Treasury** (what you have of each);
  - **What it does**, in two lines, plus the state note;
  - the gold button: RECRUIT FOR / ORDER FOR / BUILD FOR / BUY FOR.
- **Right, GARRISON:** swordsmen, crossbowmen, commander, medics and army limit, then **IN TRAINING**: the 3 queue slots, with the head's progress bar.
- **Right, CASTLE:** walls and towers level, flares, free cannon pads, gate.
- **Treasury box:** iron, copper, silver and gold ore.
- **Purchase feedback:** a gold flash and the buy sound, and each system's own notice ("Walls built: …", "Cannon ordered – the crew is on the way"). Can't pay: "Not enough, captain." with the fail sound.
- **Keys:** A / D (W / S, arrows, D-pad, the < > arrows) select; LB / RB / Tab or a click switch tabs; Q switches GARRISON / CASTLE; E buys.

## How it works
- **New hero component `BPC_Muster`.** `DrawMuster(Hud, SizeX, SizeY)` is called every frame from BP_ArmoryHUD, in a new `MusterSeq` placed before the #66 reveal.
  - It works out `Near` (within 4.5 m of BP_NPC_Barracks, Vesna's shop closed), opens and closes the screen, and refreshes each item's price, ores and state from the real systems.
  - Then it draws, using the same frame-texture + atlas + Font_Cinzel method as #380.
- **Nothing is copied.** Each system gets a 1-node `HudBuy…` custom event wired into its own branch right after its key check, so the system pays, saves and notifies exactly as with its key.
  - Recruits use BP_BarracksHUD's existing `Enqueue` (#188), with the old screen's payment.
  - The army counts come from MPC_Barracks `Cnt` (R swordsmen, G crossbowmen, B commander, A limit), the same values the old screen prices from.

## Steps (editor driver)
**#380 (Vesna's Trade) goes first:** its ArmoryHUD merge puts in the hook this one extends.
1. `py "<repo>/handoffs/barracks-hud-359/build/setup_muster_ue.py"` with **DRY_RUN = True**.
   - Read `setup_muster.txt`.
   - **Decision:** every line must say `ok`. A MISSING BPC_Medics / BPC_Flares / BPC_CastleUpgrades / BP_CannonOrder means that card isn't in yet. Say which and I'll make that row show "not installed" without the call.
2. **The 4 add-ons.** For each of BPC_CastleUpgrades, BPC_Flares, BPC_Medics and BP_CannonOrder:
   1. Export the EventGraph fresh.
   2. Run `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/barracks-hud-359/build/manifest_<BP>.json --out merged.t3d`.
   3. Go on only with **Validation: OK**.
   4. Paste (Ctrl+A, BackSpace, Ctrl+V), then Compile and Save.

   If one says "PARTLY in the live graph", that graph was changed after it was generated. Post its export and I'll redo that manifest.
3. Set **DRY_RUN = False** and run the setup again. It imports the 2 textures, makes the optional barracks-NPC portrait, creates BPC_Muster with its variables and defaults, and adds the hero's `Muster`.
4. Open BPC_Muster's EventGraph, paste `BPC_Muster_graph.txt`, then File > Refresh All Nodes, Compile and Save.
5. **BP_BarracksHUD (by hand, 3 wires):**
   1. Paste `BarracksHUD_MusterGate_graph.txt` (4 nodes) into its EventGraph.
   2. Find the **Parent: DrawHUD** call (it follows the #188 QTick block). Drag its **then** to `MusterGateIfV`. This replaces its old link.
   3. Wire **MusterGateIfV False** and **MusterGateIfN False** to the node it used to go to (the first node of the old barracks draw, a Get Vector Parameter Value of MPC_Barracks).
   4. Compile and Save.
6. **BP_ArmoryHUD:**
   1. Export the EventGraph fresh.
   2. Run `applyall.py merge --live live.t3d --manifest handoffs/barracks-hud-359/build/manifest_armoryhud_muster.json --out merged.t3d`.
   3. Go on only with **Validation: OK**.
   4. Paste, then Compile and Save.

## Checks
1. **Walk to the barracks NPC and press E.** The Muster opens on RECRUIT, looks like the check image, and the old card screen doesn't show. Screenshot it with `tools/shot.js --card 359`.
2. **RECRUIT a swordsman.** Gold drops by the shown price, he appears in IN TRAINING with a filling bar (and the #188 bar over the NPC), and he walks out when it's done. The next price is ×1.25.
3. **FORTIFY → Walls:**
   - **BUILD** takes gold + 6 iron, says "Walls built: Reinforced masonry.", and the row shows LEVEL 1 / 2 with one pip.
   - Without the iron, the button is dim and you get "Not enough, captain.". Nothing is taken.
4. **ARTILLERY → Cannon ORDER.** 800 gold, "Cannon ordered", the convoy leaves the yard, and FREE PADS drops by 1. With no pads tagged `CannonPad` the row shows FULL, "No free cannon pad on the walls".
5. **SUPPLIES → Flares BUY.** The row turns OWNED, and CASTLE shows Flares OWNED.
6. **Medic:** count 1 / 4, and the medic walks out with his satchel. At 4 / 4 the row shows AT BEST.
7. **Esc** closes the Muster and unpauses. Walking away and back: no "[J] Castle works…" notice. **J still buys walls** at the barracks.
8. **2 minutes of Play** with no new runtime errors from BPC_Muster (`pie_smoke.py`).

## Decisions
- **E opens it, Esc closes it, and E is also the buy key inside**, as in Vesna's Trade (the target's key bar). A 0.25 s guard stops the opening E from buying.
- **Recruits pay here, then call `Enqueue`.** This is the same two steps the old screen does (CX_214 pays, then Enqueue), with the same price formula. A Muster recruit also checks the queue has room before paying. The old screen didn't, and lost the gold.
- **No "hold to buy" here:** one press, matching #380's button. The research's hold-to-buy stays in the kit for a later pass if the owner wants it.
- **The mechanic stays LOCKED** until #50 is built. **The gate** is information only, because the smith sells it.
- **The cannon is ordered from the barracks**, without walking to the yard. The convoy still starts at the yard.
- **Decal and material rule:** nothing existing is touched. Everything is new assets, one hero component and small add-on pastes.

## Files
| File | What |
|---|---|
| `setup_muster_ue.py` | DRY_RUN setup: textures, portrait, BPC_Muster + defaults, hero component |
| `BPC_Muster_graph.txt` | the component EventGraph (`tools/tga/vesna/gen_muster.py`, which reuses gen_trade.py's helpers: one kit) |
| `addon_<BP>_graph.txt` + `manifest_<BP>.json` | the HudBuy entry events for BPC_CastleUpgrades, BPC_Flares, BPC_Medics and BP_CannonOrder (`gen_muster_hooks.py`) |
| `ArmoryHUD_MusterHook_graph.txt` + `manifest_armoryhud_muster.json` | DrawMuster in BP_ArmoryHUD |
| `BarracksHUD_MusterGate_graph.txt` | the old-screen gate (4 nodes, 3 hand wires) |
| `muster_data.json` | variable defaults and atlas UVs |
| `assets/tga/Muster/textures/` | T_MU_Frame (1920×1080), T_MU_Atlas (2048²) |
| `tools/tga/vesna/` | `layout_mu.py`, `make_muster_html.py` (frame from chrome.html), `atlas.html?L=mu`, `live_mu.js`, `render.ps1 -Only muster` |
