# #296 / #297 Cave: dungeon door (part 1 here) and texturing (waits on the cave dump)

By `adjustedfilm (Claude)`, 2026-10-31. Owner W: #297: *"cave needs an entrance inner door clicking E teleports us
underground dungens where we see the mine and the tunnels and workers"*.

**Split:**
- part 1 (this hand-off): the door + teleport system;
- part 2: the dungeon art is TGA's card #309 (tunnels, timber supports, mine chamber, a real mine door mesh);
- part 3 (adjustedfilm): a place script that puts the dungeon in an always-loaded sub-level far under the map, with
  the two doors placed, as soon as the cave dump (request) and #309 are in.

**Decision:** one door class placed twice, each pointing at the other. That way the same paste gives both "go down" and
"climb back up". Until part 3, the Master can test the system with any two spots in the map.

## Pre-checks (done)

| Check | Result |
|---|---|
| `fix_impure.py BP_CaveDoor_graph.txt` | no changes |
| `applyall.py check BP_CaveDoor_graph.txt` | 68 nodes, 75 links, **Validation OK** |
| existing Blueprints changed | **none** (uses the live `BP_NoticeHUD.PushNotice` only) |
| self-calls to own events | **none** (DoorPoll / DoTeleport run from timers by name, the #254 lesson) |

## What the player gets

- Walk up to the cave's inner door: the notice shows **[E] Go down into the mine** (once per visit).
- Press **E**:
  - the screen fades to black in 0.35 s, and the sound fades too;
  - the hero stands 1.5 m in front of the dungeon door, facing away from it, and the camera turns with him;
  - the screen fades back in over 0.5 s.
- The dungeon door says **[E] Climb back up to the cave** and works the same way back.
- Holding E can't bounce you back and forth: the press is edge-detected.

## Steps (Master)

1. `py "<repo>/handoffs/cave-296-297/setup_cavedoor297_ue.py" --dry-run`, then run it again without `--dry-run`. It
   makes `/Game/CastleDefender/Gameplay/Cave/BP_CaveDoor` with:
   - `Door`: a stand-in slab, blocks like a wall;
   - `Exit`: an arrow, editor only.
2. Open BP_CaveDoor. Paste the 8 lines of `VARIABLES_BPVar.txt` on the VARIABLES header, one at a time, then Compile.
3. Paste `BP_CaveDoor_graph.txt` into the EventGraph. Compile and save.
4. **Test placement** (part 3 will do this for real). Drag two BP_CaveDoor into ThirdPersonMap:
   - **A** in the cave, at the inner wall, with its arrow pointing into the cave;
   - **B** anywhere for now, with its arrow pointing where the hero should walk.

   In the Details panel:

   | Door | Target | Prompt |
   |---|---|---|
   | A | B | keep the default |
   | B | A | `[E] Climb back up to the cave` |

## Tests (Play)

1. Walk to A: the notice shows once. Walk away and back: it shows again.
2. Press E at A: fade out, then you're in front of B facing B's arrow, then fade in.
3. Press E at B: back at A.
4. Hold E down at A: one trip only, no bouncing.
5. Clear A's Target: E does nothing (no fade).

## Tuning (one minute, Class Defaults or per door)

| Variable | Default | What it does |
|---|---|---|
| `UseRange` | 220 cm | how near the hero must be |
| `ExitDist` | 150 cm | how far in front of the target door he lands |
| `Prompt` | `[E] Go down into the mine` | per door |

## Also here

`dump_cave_ue.py` is a read-only cave dump for #296 texturing and part 3 placement. It was filed as an export request.

---

## Part 3: the mine dungeon (`place_mine297_ue.py`, adjustedfilm 2026-10-31)

Uses TGA's #309 MineKit (`assets/tga/MineKit`) and its layout (`tools/tga/mine/lookdev_mine.py`).

**Decision:** both doors go in the persistent level. A hard `Target` reference can't cross from a sub-level into the
persistent level, so the dungeon **art** is in the always-loaded sub-level and the two doors are not.

### Steps (Master)

1. If the kit isn't in yet: `py "<repo>/assets/tga/MineKit/import_mine_ue.py"` (set `DRY_RUN = False` after the dry run).
2. `py "<repo>/handoffs/cave-296-297/place_mine297_ue.py" --dry-run`. Read the log:
   - `dungeon origin` is 50 m under Mine_01;
   - it stops if anything already sits in the dungeon box (then raise `DEPTH` at the top);
   - `tunnel trace` lines show which side of Mine_01's tunnel is rock.
3. `py ".../place_mine297_ue.py"`. It makes:
   - the sub-level `ThirdPersonMap_MineDungeon` (always loaded), with chamber, tunnels, timber, rails, cart, ore veins,
     spoil heap, door frame, 5 lanterns with warm 400 lm lights, and a NavMeshBoundsVolume;
   - BP_CaveDoor's door mesh swapped to `SM_Mine_Door`;
   - `MineDoor_Up` inside Mine_01's tunnel, facing the mouth, and `MineDoor_Down` at the dungeon's dead end, with Targets
     paired and the "climb back up" prompt.

   It saves the levels and writes `place_mine297.txt`.
4. Push `place_mine297.txt`, and post a screenshot of each door on #297.
   - Undo: `--remove` (everything carries the tag `Mine297`).
   - It's safe to re-run: the last run is removed first.
   - It only raises Kill Z if the hero would die down there, and logs it.

### Tests (Play)

1. Walk into Mine_01: the old oak door stands at the tunnel's inner end. [E] → fade → you're in the dungeon's dead end,
   facing up the tunnel.
2. Lanterns glow and pool warm light. The wet floor shines. Nothing is pitch black around the lanterns.
3. Walk the tunnels into the chamber: there are no seams and no snagging on timber.
4. [E] at the dungeon door takes you back up to Mine_01.
5. If MineDoor_Up ended up in the rock or outside the mouth, move it by hand (a one-minute fix) and note it on #297.

## Part 4: miners in the dungeon (`mine_workers297_ue.py`)

Owner: *"...where we see the mine and the tunnels and workers"*. They are stand-in miners until the MetaHuman pass,
built like the soldiers (from the Master's `soldier_components.txt`):
- a hidden Quinn body plays a looping swing;
- the knight body follows it, the same way soldiers work;
- TGA's #247 gear goes on the body: a pick in `hand_r`, the candle helmet on `head`, and the ore satchel on `spine_03`;
- a real 120 lm candle light sits on the helmet.

They have no AI and no fighting. There are three:
- two swing at the ore veins, each with its own rhythm;
- one rests by the cart.

### Steps (Master)

1. If the gear isn't in yet, run `py "<repo>/assets/tga/MinerGear/import_minergear_ue.py"`.
2. Run part 3 (`place_mine297_ue.py`) first.
3. `py "<repo>/handoffs/cave-296-297/mine_workers297_ue.py" --dry-run`, then run it without `--dry-run`. It makes
   `BP_MineWorker` and places `Mine297_Worker_0..2`.
4. Undo: `place_mine297_ue.py --remove` (they carry the tag `Mine297`).

### Tests

1. Go down: two miners swing at the ore and one rests by the cart. Each has a small warm candle light.
2. The gear sits in the hand, on the head and at the hip. If a piece sits at the feet, set its **Parent Socket** in
   BP_MineWorker (`hand_r` / `head` / `spine_03`). That's a one-minute fix.
3. The swing is the soldier's sword stroke used as a pick stroke (a stand-in). Better: give `AnimToPlay` on the Body a
   real mining anim later.
