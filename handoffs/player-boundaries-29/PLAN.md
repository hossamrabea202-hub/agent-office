# #29 Player boundaries: keep players on the playable ground, out of the fog pockets

Seat: `hossam gmail laptop2 (Claude)` · card #29 · 2026-10-29. The owner's screenshot (on the card) marks two
fog-filled forest pockets: one north-west of the hill shrine, and one big pocket between the hill and the tentacle.
The ground drops away there and the player falls into fog.

## Goal

The player should **never meet an invisible wall they can't explain**. Every edge reads as a place in the world,
from about 30 m away, before the player reaches it. Collision is the safety net, not the design.

## Three layers at every edge

| Layer | What | Why |
|---|---|---|
| 1. Read (30-60 m) | **A landmark silhouette** on the edge: a broken watchtower, a collapsed palisade gate, a dead giant tree. It's backlit by the fog, so it reads as "end of the road", not "go explore". | The eye is drawn **along** the edge, not over it. |
| 2. Block (0-5 m) | **A natural wall** that matches the ground it stands on: rock outcrops and cliff lips on the hill, a burnt palisade with sharpened stakes and overturned carts in the forest, fallen-trunk piles across gaps. Placed in 2-3 overlapping rows, never one straight line. | It tells the player "can't pass" at a glance, and it fits the siege story: the defenders walled off the fog. |
| 3. Safety (hidden) | **Collision that hugs the props**, made of simple shapes. It blocks the **Pawn** (the hero) and the camera, slightly higher than a jump. The NavMesh stops 1 m inside. Behind it, a soft kill or respawn volume returns anyone who still gets out, with a fade instead of a death. | No pixel gaps, no getting stuck on a single rock, and nobody falls through the world. |

## The fog edge (look)

- The fog stays: it's the mood. Now it **frames** the arena instead of hiding drops.
  - A height-fog band sits just behind the barrier line, so props fade into it and the drop is never visible.
  - Ground mist cards sit at the barrier's foot.
- **Soft warning at the edge:**
  - Within 4 m of the line, the screen edges cool and darken slightly.
  - Distant zombie moans play from the fog side, and the hero's footstep audio gets a little hollow.
  - No UI text. (AAA reference: the fog-edge treatment of Elden Ring and The Last of Us Part II, with a diegetic
    "this is the edge" instead of a message box.)

## Zombies keep their way in

- Waves come out of the fog, so the barrier stays **player-only**:
  - The collision channel blocks the Pawn but not the zombie's own capsule profile.
  - Or each wave spawn lane gets a **breach**: a smashed section of palisade that zombies climb through. These
    become intentional combat focal points.
- First step: I'll check the spawn points in the export before choosing between the two.

## Deliverables (after the export)

1. **Border line** traced from the real height and NavMesh grid: where the ground drops more than 1.5 m within
   2 m, plus where the NavMesh ends.
   - Top-down preview over the owner's screenshot area, with the barrier line, prop rows and breaches drawn on it.
2. **Placement script** (UE Python) that places the prop rows along that line from meshes **already in the
   project**:
   - rocks, palisade, logs and carts; random yaw, scale 0.85-1.25, sunk into the slope, no repeats side by side
   - plus one spline-hugging collision actor per edge, the edge kill or respawn volume, and the fog and mist cards
   - All of it goes in its own folder, `Boundaries_29`, so it can be removed in one step. It is placed in the open
     level only after the Master's OK.
3. **Edge warning** (vignette + audio), a small component on the hero driven by distance to the line.
4. **Checks:**
   - Walk and jump the whole perimeter: no gaps, no snags, the camera never clips through.
   - Zombies still spawn and reach the castle.
   - Frame rate in the forest pocket doesn't drop: props are instanced (HISM) with 3 LODs and culled at 150 m.

## Needs first (export request on the card)

Run `tools/laptop2/export_level_bounds.py` in the editor with the game level open. It changes nothing; it writes
`handoffs/exports/laptop2/bounds29/`:
- the height and NavMesh grid
- the landscape, NavMesh and fog bounds, kill-Z, the player start
- the big actors and their meshes
- the blocker-like meshes already in the project
