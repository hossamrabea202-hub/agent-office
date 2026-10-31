# #283 Cannon scroll map: click on a parchment map where the cannon goes (only new cannons move)

By `adjustedfilm (Claude)`, 2026-10-31, from the owner's idea in chat.
- **Builds on:**
  - #230 / hand-off #239 (checkking): `BP_CannonOrder` (the artillery yard, O key) and
    `BP_CannonConvoy.StartConvoy(Target, Yaw)`, which drives the cart and deploys a BP_Cannon;
  - my #268 `BPC_MotionFX` v2 (#269), for drawing on the HUD.
- **Pre-checked:**
  - `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK** on all three graphs (506 + 5 + 6
    nodes).
  - **Both merges dry-run OK:** BP_CannonOrder on checkking's graph (+10 links, 1 rewire) and BPC_MotionFX on the v2
    graph (+20 links). The #141 add-on still applies after them.

## What the player sees

1. **Ordering.** At the artillery yard, **O** pauses the game.
   - A parchment scroll unrolls from the middle in 0.6 s (ease-out), between two wooden rods with gold caps, with a
     paper sound.
   - The map of the castle and the fields (400 m) fades in, inked like a hand-drawn chart:
     - live, captured from above the moment the scroll opens;
     - sepia paper tones, ink outlines (Sobel), burnt edges, fibres and stains.
2. **The infographic** (motion graphics):
   - Three steps slide in along the top, 40 ms apart: **1 Click a spot on the map · 2 ENTER or CONFIRM · 3 The crew
     brings the cannon**. The current step is gold.
   - A gold pulsing ring with **"click here"** sits on a field spot until the first click.
   - A legend runs along the bottom: *Gold ring: your cannon – click it, then a new spot, to move it. Grey: starter
     cannons stay. Esc: close.*
3. **Cannons on the map:**
   - **grey rings** marked "fixed" are the starter cannons. They can't be picked.
   - **gold pulsing rings** marked "yours" are ordered cannons. Click one and it is marked "moving".
4. **Click a spot:**
   - If it's reachable (NavMesh, inside or outside the walls): a **red ring and an ink X** appear, with a quill sound.
   - If not: *"The crew cannot reach that spot"* in red ink.
5. **CONFIRM** (the pulsing button reads *CONFIRM (800 gold)*, or *MOVE CANNON* when one is picked), or **ENTER**:
   - **New cannon:** pays 800 gold. The #230 convoy leaves the artillery yard, drives there with its two crewmen and
     deploys the cannon facing away from the castle. Notice: *"Cannon ordered – the crew is on the way."*
   - **Moving one of yours:** the cannon is packed (removed) and a convoy starts from its spot to the new one, for free.
     Notice: *"The crew packs the cannon and moves it to the new spot."*
   - Not enough gold: *"Not enough gold for a cannon."* The map closes and nothing is charged.
   - Then the scroll rolls up in 0.4 s and the game resumes.
6. **Esc** rolls it up without paying.

## How it works

- **`BPC_CannonMap`**, the hero component "CannonMap":
  - **BeginPlay:**
    - remembers every BP_Cannon in the level as **StarterCannons** (locked);
    - spawns `BP_MapCapture` 150 m over the castle centre (an orthographic capture, 400 m wide, captured only when the
      map opens);
    - makes 5 dynamic materials (scroll, gold / grey / red / demo rings).
  - **`OpenMap`:** pauses the game, shows the mouse cursor, captures the map, plays the sound. `CloseMap` reverses it.
    `ConfirmMap` pays and spawns the convoy (or moves a cannon).
  - **`DrawMap(Hud, SizeX, SizeY)`**, every HUD frame while open:
    - the scroll (`M_ScrollMap`: Unroll, Reveal, aspects);
    - input: Esc, click, Enter, the CONFIRM button;
    - the icons;
    - the mark, the demo, the infographic and the message.
  - Map ↔ world: 400 m orthographic around `CastleCentre` (2300, 1725, the #41 castle box centre). Up is +X, right is +Y.
- **BP_CannonOrder:** a 5-node paste. O in range now calls `CannonMap.OpenMap`; the map takes the gold on CONFIRM.
  checkking's old pad-and-gold chain stays in the graph but is no longer reached.
- **BPC_MotionFX:** a 6-node paste. `DrawReveal` first runs the reveal (unchanged), then `CannonMap.DrawMap`.

## Files

| File | What |
|---|---|
| `setup_cannonmap283_ue.py` | Editor script, safe to re-run, with `--dry-run`. Makes RT_CannonMap, BP_MapCapture, M_ScrollMap, M_MapRing, the 4 sounds and BPC_CannonMap in `/Game/CastleDefender/UI/CannonMap`, and adds "CannonMap" to the hero. |
| `VARIABLES_BPVar.txt` | 18 BPVar lines for BPC_CannonMap (`VARIABLES.md`). |
| `BPC_CannonMap_graph.txt` | the component's EventGraph |
| `CannonOrder_Map_graph.txt` + `manifest_cannonorder.json` | BP_CannonOrder: O opens the map |
| `MotionFX_Map_graph.txt` + `manifest_motionfx_map.json` | BPC_MotionFX draws the map |
| `gen_cannonmap283.py` | generator (bpkit) |
| `assets/adjustedfilm/CannonMap283/` | `sfx/*.wav` (scroll open / close, quill mark, wax-seal confirm), `source/make_map_sfx.py` |

## Steps (Master: paste only)

**Order:** #239 (deploy cannon) and #269 (reveal v2) must be in first. This card patches both.

1. **Dry-run first:** `py "<repo>/handoffs/cannon-map-283/setup_cannonmap283_ue.py" --dry-run`. Then run it without
   `--dry-run`.
2. **Add the variables.** BPC_CannonMap → paste the 18 BPVar lines, then Compile.
3. **Paste the graph.** Paste `BPC_CannonMap_graph.txt` into BPC_CannonMap's EventGraph. Compile and Save. Compile and
   Save the hero.
4. **BP_CannonOrder:** export its EventGraph to `live.t3d`, then run
   `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/cannon-map-283/manifest_cannonorder.json --out merged.t3d`.
   Then Ctrl+A, Delete, paste, Compile and Save.
5. **BPC_MotionFX:** the same with `manifest_motionfx_map.json`.

## Checks (Play)

1. At the artillery yard press O.
   - The game pauses and the scroll unrolls with the paper sound.
   - The inked map fades in. The three steps slide in, and the "click here" ring pulses.
   - Starter cannons show grey with "fixed".
2. Click an unreachable spot (on a roof or off the map): the red "cannot reach" line appears.
3. Click a field spot outside the walls: a red ring and an X appear, step 2 turns gold, and CONFIRM pulses.
4. CONFIRM with ≥ 800 gold: the gold goes down, the scroll rolls up, and the game resumes. The convoy leaves the yard,
   drives to the spot and deploys a cannon facing away from the castle.
5. Press O again: the new cannon shows as a gold "yours" ring.
   - Click it ("moving"), then click a new spot, then MOVE CANNON.
   - The cannon disappears, a convoy starts from there and deploys it at the new spot.
   - Starter cannons can't be picked.
6. Esc while choosing: the scroll rolls up and nothing is charged.
7. No "Accessed None" from BPC_CannonMap. The game is unpaused after every close.

## Decisions

- **Any reachable spot is allowed**, inside or outside the walls. That replaces #230's "next free wall pad".
- **Moving your own cannon is free.**
- **Starter cannons** are simply the cannons in the level at Play. Nothing in the level has to be tagged.
- **The map is captured live once per opening** (400 m around the castle), so it always shows the current state
  (breaches, cannons). Its look comes from the shader (ink and sepia), not from a hand-made painting.
- **Ordered cannons aren't saved across a load:** a loaded game treats every cannon that exists as a starter. That is
  the same behaviour #230 has today.
- **Keys:** O opens the map (the #230 key), Enter confirms, Esc closes. The mouse works because the game is paused and
  the cursor is shown.
- **No in-engine preview yet.** The scroll is procedural. A screenshot comes with the Master's first Play check
  (`tools/shot.js --card 283`).

## Office rules applied

- **The Master only pastes:** a setup script with a dry-run, BPVar lines, clean graphs, two dry-run merges, steps and tests.
- **Rule 10 (coherence):** the same gold palette and Cinzel type as the #268 reveal; ink tones on paper.
- **Decals and live materials:** untouched. Only new assets are added.
