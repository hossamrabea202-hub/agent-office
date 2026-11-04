# #501 Render thread / GPU: what draws the castle, and two fixes (i5 for i9). Scripts, no paste

Why: i9 measured 11-04 16:40 (after K / C1 / C3 / C5): no wave frame 46.6 ms = render thread 46 ms + GPU 45 ms; game thread 20 ms. Drawing is now the wall.

## What i5 counted in the live level (read-only, i5 joined to CastleDefender6)
- 4,526 actors, ~3,800 mesh components.
- **#491 stone kit is fine:** 10,100 stones in 120 instanced components, all 93 meshes Nanite.
- **SiegeKit barricades:** 293 actors (290 Palisade, 2 Watchtower, 1 Breach), **13.5 M triangles, no Nanite**, 292 with collision: they are the map edges
  (folders Boundaries_29 A / C / E) and 32 in Gameplay/Realm.
- **1,135 engine Plane cards:** grime / soot / fog (MI_EdgeGrime_StairContact 690, M_TorchSoot, M_WallBaseGrime ...): translucent or modulate.
  Merging see-through cards into one mesh can make them sort wrongly, so they are NOT merged by default.
- ~230 opaque cubes (paving, step caps, walk flags): safe to merge -> 74 actors into 9 meshes (small gain).
- Meadow flora: 72.8 M triangles in instanced grass, no Nanite: the biggest GPU item, but **owner rule: no grass speed work**. Not touched; owner's call.

## Fix 1: SiegeKit barricades (owner's order: remove them)
`remove_siegekit_ue.py`. **Recommended:** `--hide-keep-collision`: invisible in game, no shadows, collision kept, so the map edges still block. Removes all 13.5 M triangles from drawing.
Full delete as ordered: `--apply` (writes a restore list to Saved/removed_siegekit_<time>.json first; `--restore <json>` puts them back). **Delete opens the map edges.**
Dry run on i5: 293 found, 292 with collision.

## Fix 2: merge opaque cards
`castle_draws_ue.py --merge --dry-run`, then `--merge --apply`: same mesh + material + folder + 20 m cell -> one new mesh in /Game/CastleDefender/Merged501/;
originals kept, hidden, tagged PreMerge501; `--revert` undoes. Opaque only by default; `--include-translucent` also merges the grime cards (look at them before saving).
`--report` prints draw counts per folder. `--nanite --apply` turns Nanite on for the SiegeKit meshes (not needed if Fix 1 removes or hides them).

## Steps on i9 (editor idle, not in Play)
1. `py <repo>/handoffs/aaa-472/render/remove_siegekit_ue.py` (dry run), then `--hide-keep-collision` (or `--apply` if you want them gone).
2. Play: walk to the map edges: still blocked (hide mode). Measure no-wave with the editor in front (`measure_split_ue.py`).
3. Optional: `castle_draws_ue.py --merge --apply`, Play-check paving / steps, save.
Tested on i5: dry runs only (no level change on i5: the live session would push it to your map). The merge call itself has not run yet.
