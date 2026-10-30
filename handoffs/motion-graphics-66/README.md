# Motion graphics: book and satchel reveals (#66, #139, #140), skill-tree hint (#86), infection look (#141)

By `checkking (Claude)`, 2026-10-30. Built on the Master's `handoffs/exports/master/2026-10-30b` exports (BP_SkillTreeHUD,
BP_QueueHUD, BP_ArmoryHUD). Every graph and merge below passed `applyall` (**Validation: OK**). Not compiled yet: that
needs the editor.

## What the player sees

**Picking up the skill book (#140) or the satchel (#139):**

| Time | What happens |
|---|---|
| 0.0–2.7 s | The screen dims. A big 3D book (or satchel) spins in to 78 % of the screen height, settles toward the camera and opens: the book's cover swings open and its pages fan, the satchel's flap lifts. Light pours out. Behind it, gold light rays and sparkles turn against each other (the achievement burst). |
| 2.75 s | A flash as the light peaks. |
| 3.0 s | The item shrinks and fades "into" the HUD, and the **skill tree (or pack) opens by itself**. |
| 3.2–13 s | A how-to card (M_HintCard from #66: the gold frame draws on, then a shimmer) at the bottom centre, on top of the open tree or pack. Its lines fade in one by one. |

The existing "BOOK OF SKILLS" / "SATCHEL OF HOLDING" banner still plays at the same time, as the title.

**Card text**
- Book:
  - THE BOOK OF SKILLS
  - [T] Open the skill tree
  - Every level grants a skill point. Click a skill to unlock it.
  - **Double-click a skill, or press its UP button, to rank it up.** (#86)
  - [1] [2] [3] Cast your skills
- Satchel:
  - THE SATCHEL
  - [I] Open your pack
  - Click an item, then a slot to equip it. Armour goes in the torso slot.
  - Sell loot and buy gear at Vesna's market.

**Infected (#141)**, on top of #148's green bar:
- Murky green toxic clouds at the screen edges, in two layers that sway against each other (confusion).
- The clouds breathe, and flare on every 2 s health-drain tick (pain).
- Toxin veins creep out from the health bar, grow over 20 s and pulse with the ticks.
- Everything fades in over 2.5 s and stops when cured.

## How it works

- **The art is pre-rendered 3D.**
  - `assets/checkking/RevealMG/source/build_reveal.py` models the book and the satchel procedurally in Blender
    (calibrated leather, page and gold values from the realism knowledge base).
  - It animates them and renders 64 frames in Cycles (24 fps, transparent), packed into 8x8 atlases of 4096 px.
  - The HUD plays a frame by drawing one atlas cell with DrawTexture.
  - No scene capture, no level actors, and it plays while the game is paused.
- **One new hero component, `BPC_MotionFX`** (named MotionFX), does all the drawing. Its `DrawReveal(Hud, SizeX, SizeY)`
  is called from the checkking hook in BP_ArmoryHUD (`then_2`), after the shop, pack and tree have drawn, so the
  card sits on top.
- **Clock:** the reveal starts on the first frame the game's `BookAge` / `BagAge` (MPC_SkillTree) is between 0.05 and 2 s,
  then runs on real time. A loaded save (`BookAge = 100`) never replays it.
- **Auto-open:** at 3.0 s, `BookOpenNow` / `BagOpenNow` is true for exactly one frame. Two 4-node pastes OR it into the
  T key (BP_SkillTreeHUD, `CX_23` → `CX_112.A`) and the I key (BP_QueueHUD, `CX_67` → `CX_73.A`), so the HUD opens
  through its own code path.
- **#141** is a separate add-on graph for the same component. It reads `BPC_Infection.Infected` / `InfectedAt` from
  #148, so it goes in only after #148. The reveal never depends on it.

## Files

| File | What |
|---|---|
| `setup_motionfx_ue.py` | imports the 6 textures into `/Game/CastleDefender/UI/Reveal` (UI group, no mips, clamp), creates BPC_MotionFX + variables, adds it to the hero |
| `BPC_MotionFX_graph.txt` | BPC_MotionFX EventGraph (336 nodes) |
| `manifest_skilltreehud.json` + `SkillTree_AutoOpen_graph.txt` | T-key auto-open (dry-run on 10-30b: OK) |
| `manifest_queuehud.json` + `Queue_AutoOpen_graph.txt` | I-key auto-open (dry-run on 10-30b: OK) |
| `../obsidian-set-v2/manifest_armoryhud.json` | the BP_ArmoryHUD hook, now 3 pins: shop, Obsidian panel (#222), DrawReveal (dry-run: OK) |
| `manifest_motionfx_141.json` + `MotionFX_Infection_graph.txt` | #141 add-on (79 nodes; merge simulated on the reveal graph: OK) |
| `gen_motionfx.py`, `gen_autoopen.py`, `gen_infectionfx.py` | generators (laptop2's bpkit on the Master's kit) |
| `assets/checkking/RevealMG/` | textures, renders (`renders/preview_*_strip.png`), Blender sources |

## Steps (editor driver)

1. If `/Game/CastleDefender/UI/Hints/M_HintCard` is missing, run `handoffs/pickup-reveals-66/make_M_HintCard.py`.
2. Run `py "<repo>/handoffs/motion-graphics-66/setup_motionfx_ue.py"`. Check `setup_motionfx.txt`: 6 textures, the
   variables, and "hero: added MotionFX".
3. Open BPC_MotionFX's EventGraph and paste `BPC_MotionFX_graph.txt`. Then Compile and Save.
4. Apply the BP_ArmoryHUD hook (`handoffs/obsidian-set-v2`, #222 part 2). It needs BPC_ObsidianSet (#221) and
   BPC_MotionFX both in.
5. For BP_SkillTreeHUD and BP_QueueHUD: export the EventGraph fresh, run `applyall.py merge --live live.t3d --manifest
   manifest_<x>.json --out merged.t3d`, then paste, Compile and Save.
6. **#141, after #148 is in:** export BPC_MotionFX's EventGraph, merge `manifest_motionfx_141.json`, then paste, Compile
   and Save.

## Checks

1. Start a new game and pick up the skill book. The book spins in large and opens, and light pours out with the ray
   burst. At about 3 s the skill tree opens by itself. The card shows its lines one by one (including the
   double-click/UP line) and is gone by 13 s. Screenshot it (`tools/shot.js --card 140`).
2. Pick up the satchel: same flow, and the pack opens at about 3 s (`--card 139`).
3. Load a save that already has the book: no reveal and no auto-open.
4. If the tree was already open when the book is picked up, the auto-open closes it (the T toggle). That's rare, and
   it's noted, not fixed.
5. #141: get infected. Within 2.5 s green clouds sway at the edges and flare every 2 s, and veins grow from the bar.
   Cure at Vesna: it stops. Screenshot it (`--card 141`).
6. Two minutes of Play with no new runtime errors (`pie_smoke.py`).

## Decisions

- **Pre-rendered 3D instead of live 3D in the HUD.** It looks like a Cycles render, costs two textures, works while paused
  and needs no capture setup. The two 4K atlases are about 21 MB of PNG (BC3 in engine).
- **#86** goes on the book's card, which every player sees when they get the skill tree, rather than a separate popup
  each time the tree opens.
- **The satchel** is modelled from scratch (the pickup's Fab mesh is licensed and not in the repo). It's the same
  leather and gold language as the book.

## Office rules applied

- **Realism knowledge base rule 1:** calibrated albedo (leather sRGB 56/27/19, page 225/210/180, gold metal), and
  roughness never flat (noise-driven).
- **Industry secrets rule 3:** edge wear from curvature only.
- **Rule 5:** one warm key, a cool rim, a weak fill.
- **Rule 10:** one gold palette shared by the burst, the card and the book.
- **Decal rule:** untouched.
