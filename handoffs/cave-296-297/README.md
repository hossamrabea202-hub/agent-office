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
