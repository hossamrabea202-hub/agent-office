# #451: castle seams, hard edges and cube faces (i5 / adjustedfilm, 2026-11-03)

Owner (Alien, 00:30 + 00:50): polish the game by the ChatGPT review rules (#347 master prompt), then for 5 hours "go around
the castle and keep an eye for any surfaces or hard edges or cube faces of objects like stone walls (need to meet
correctly), study real world references for each problem, don't mess up our decals, enhance the scene like AAA technical
realistic artists". Research: [RESEARCH_seams.md](RESEARCH_seams.md).

All batches below were applied **from i5 in the live session CastleDefender6, NOT saved** (no editor driver was online on
the Master). Every script has `--dry-run`, a JSON backup and `--revert`. Decals and decal cards were never touched.

| Batch | What was wrong | Real-world / AAA rule | Fix | Proof |
|---|---|---|---|---|
| 1 | 58 exact duplicate actors (30 wall-walk floor plates `Cube_77..93`, 28 `SM_WalkSlab_75..102`) | one piece per surface | extra copy hidden (`dup_fix_ue.py`) | A/B identical on screen (cleanup: each surface was drawn twice). My first "triangle sawtooth" shot was the map still streaming in, not the duplicates. |
| 2 | 36 castle blocks were plain `SM_Cube_Nanite` stand-ins (folders `Restored/SM_Bevel_NNN`) with razor CG edges | dressed stone never has a CG-sharp arris | original meshes put back: 12 `SM_Bevel_023` merlons; 12 `SM_Bevel_024` and 12 `SM_Bevel_007` (meshes gone) via `SM_Bevel_023` / `SM_Bevel_013` turned 90 deg, same size, same material (`bevel_restore_ue.py`) | `shots/pair_bevel_restore.png` (lit): the stone now wraps over the corner. Note: the SM_Bevel meshes are 8-vertex boxes, not real chamfers. |
| 3 | 120 separate 3 m paving plates stacked on top of the continuous courtyard floor cut a 3 m tile grid with 2 cm gaps through the cobbles | a cobbled courtyard is laid continuously | plates hidden, the continuous `Castle_CourtyardFloor_Single` (same material, receives decals) shows (`hide_set_ue.py paving_plates`) | `shots/pair_courtyard_cobbles.png` (lit) |

## For i9 / the Master
Save these actors on the Master when you are back (they live in the session transaction log only), or re-run on the
Master after a `git pull` (each is idempotent and keeps its backup next to it):
```
py ".../gpt-review-polish/dup_fix_ue.py" --apply
py ".../gpt-review-polish/bevel_restore_ue.py" --only SM_Bevel_023,SM_Bevel_024,SM_Bevel_007 --apply
py ".../gpt-review-polish/hide_set_ue.py" paving_plates --mesh Cube --mat MI_Castle_Paving_POM --size 298x288 --top 3.2 --apply
```
Checks: east wall walk walkable; merlons on the keep top (x 2400-2660, z 1300) and the 24 turned blocks sit where they
were (no gap, no overlap shift); courtyard floor collision fine, mud decals still on the floor.

## Looked at, left alone (with reason)
- Curtain walls already run 400-500 cm into both round corner towers (drum radius ~580 cm): no wall-end gap there.
- Tower base "bright lines" = the drum's own limewash mortar joints catching a grazing test light, not gaps.
- Wall-foot black band inside the south curtain = contact grime cards `Blend_Contact_*` (decals: not touched). Reads as a
  hard black strip under a test light; owner/i9 to judge.
- Mirrored "Prev" text near the keep = back of the trade showcase arrows (gameplay UI), not a scene bug.
- Seam-scan GAP/FLOAT candidates that are design (stacked string-course layers, parapet reveal, stairs, gate) were not moved.

## Tools (all read-only unless `--apply`)
`seam_scan_ue.py` (gaps / coplanar faces with visibility probes / floating / primitives), `shots_ue.py` (light i5 renders:
below clouds, flags off, `@bc` base colour, `@n` normals), `lit_ab_ue.py` (temporary test light + A/B toggle),
`probe_actors_ue.py`, `junction_fix_ue.py` (wall-into-tower extension; found nothing to do).
- Arrow slits (42 `M_Shadow` plates): tried an unlit near-black "void" material (`M_ArrowLoopVoid451`, `slit_void_ue.py`).
  Lit A/B (`shots/slitab_A` vs `_B`) was WORSE: unlit emissive scales with exposure, so at night it turned into a flat
  brown panel, while the original navy plate already reads as a dark opening under light. Reverted at once; the new
  material is unused (safe to delete). A real fix needs actual openings in the wall meshes.

## Batch 4: forge hearth (applied in the session, not saved)
`Forge_01` (BP_Forge) rendered as white plastic blocks: `SM_Camp_Forge` only has a lightmap-style UV set, so the forge
texture doesn't land (`shots/pair_forge.png` left). Per-instance override on this placed actor only: the hearth gets the
castle's world-aligned stone `MI_Castle_Trim_World` (right). Trade-off: the mesh is one material slot, so the coals and
the poker become stone too. The proper fix is a re-UV / re-bake of SM_Camp_Forge (card for TGA). Revert:
`forge_stone_ue.py --revert`; re-apply on the Master: `forge_stone_ue.py --apply`.
