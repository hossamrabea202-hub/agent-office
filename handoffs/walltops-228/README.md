# #228 Wall-walk tops: stretched, smeary texture → world-aligned at a real scale

By `adjustedfilm (Claude)`, 2026-10-31. Playtest (10-30): the wall-walk tops show a stretched wood-brown smear, no stone
detail. The card asks to *"list which meshes/MIs cover those wall tops and their tiling, then propose the fix"*.

**One script, three modes:** `walltops228_ue.py`.

## Step 1: report (changes nothing)

```
py "<repo>/handoffs/walltops-228/walltops228_ue.py"
```

- Writes `walltops228_report.txt`: every mesh on the castle actors with its materials, the tiling-like parameters and the
  textures of each MI.
- **Flags likely culprits:** wood-named materials on wall actors, and tiling below 1.
- **Commit it, or paste it on card #228.** The agent (me or the next one) picks the MIs to fix. No debugging for the
  Master.

## Step 2: fix (after the MIs are named on the card)

```
py "<repo>/handoffs/walltops-228/walltops228_ue.py" --fix MI_Name1 MI_Name2 --dry-run
py "<repo>/handoffs/walltops-228/walltops228_ue.py" --fix MI_Name1 MI_Name2
```

1. Makes `M_WallWorldAligned` once, using Unreal's WorldAlignedTexture / WorldAlignedNormal: textures are projected in
   world space, so there is no stretching on any face, at **300 cm per tile** (`--size 200` for smaller stones).
2. Creates `MI_<name>_WA` for each named MI, carrying **that MI's own textures** (BaseColor, Normal, ORM), so the look
   stays and only the scale is fixed.
3. Swaps them in on every component that uses those MIs, logs each swap to `walltops228_swaps.txt`, and saves the level.
- **The courtyard floor is untouched** unless its MI is named.
- **Undo:** `--revert` puts every logged material back.

## Checks

- **Top-down view:** the four circled areas (NW tower top, inner wall-walk, east and south wall-walks) show stone or wood
  at a normal scale, like the cobbles.
- **Close up on the walk:** no smear, no visible repeat.
- **Wall sides:** the same scale and no seams. If the sides looked better before, report it and only the top meshes get
  the swap.

## Office rules applied

- **Realism KB:** real-world texel scale (a 300 cm tile matches the stone courses), the original textures kept, no new
  colour.
- **Keep-the-look:** new assets only; the swap is logged and reversible.
- **The Master only pastes:** a report run, then a fix run with the names the agent picks.
