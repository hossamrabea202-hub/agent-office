# Obsidian Sovereign: Chest (AAA pilot remodel by checkking)

Replaces the Codex chest's single smooth shell with real plate construction. Built fully procedurally in Blender 4.5 (scripts in `source/`), baked from an ~860k-triangle high poly to a 27.9k-triangle game mesh. The Codex original stays untouched in `assets/Codex/Obsidian-Sovereign/Chest` for comparison.

## What's new vs the Codex version

| | Codex | This pilot |
|---|---|---|
| Construction | one smooth closed shell | **separate overlapping plates**: breastplate with medial keel, pointed plackart over it, backplate, 3 fauld lames (front) and 2 culet lames (back) |
| Edges | gold-painted rim | **rolled (turned) edges** at neck and armholes, smaller rolls on the plackart and lames |
| Fastening | none | **leather side straps with steel buckles and tongues**, over-the-shoulder straps, riveted strap ends, plate rivets |
| Ornament | flat drawn lines | **gold inlay set into the steel** (laurel branches, lozenge, double borders) with **etched dark bands** between the borders |
| Surface | uniform plastic black | blackened steel with blue-purple temper colour, fine **hammer marks** (high poly), **edge wear** in patches, **grime in cavities**, fine scratches, leather grain, gold with darker recesses |
| UVs | Smart UV, jagged islands, ~60% used | **true-length unrolled islands per plate** (even texel density, straight seams), inner shell at 35% density, ~80% used |
| Triangles | 20,976 | 27,896 (more plates and real edges; LOD1 to be generated in UE) |

## Files

- `SM_ObsidianSovereign_Chest.fbx`: game mesh, metres, Z up, facing -Y, in the Codex set's frame (bottom at Z 0.97, top 1.47, lines up with the Codex pieces and the new shoulders). Static, not skinned. Fixed 10-27 night: the first upload sat 0.97 m too low (`source/reexport_set_height.py`). If you already imported the old one, re-import over it.
- `source/chestlib.py` was later updated for the shoulders (tube UVs now have a real seam instead of folded halves). The shipped chest textures were baked with the earlier version, so re-run the whole bake if you rebuild the chest from source.
- `textures/`: 4K `T_ObsidianSovereign_Chest_BaseColor` (sRGB), `_ORM` (R = AO, G = roughness, B = metallic), `_Normal_DirectX` (16-bit, Unreal). The OpenGL normal is rebuilt by the bake (not committed, to keep the repo small).
- `import_chest_ue.py`: UE 5.3 import. Mesh + textures with the right settings, a shared `M_ObsidianSovereign` master (BaseColor × Tint, ORM, Normal, RoughnessScale) and `MI_ObsidianSovereign_Chest`.
- `renders/`: beauty renders and a close-up.
- `source/`: `chestlib.py` (parametric torso and plate tools), `build_chest.py` (all plates, straps, rivets, inlay), `materials.py` (procedural PBR layers), `bake_staged.py` + `run_bake.ps1` (UVs, then a memory-safe 4K bake in quarters, one Blender process per map, then textures and FBX). Rebuild: `blender -b --factory-startup -P build_chest.py` (low) and with `CHEST_RES=3` (high), then `run_bake.ps1`.

## Still open

- **Fit and skinning** to `ShadowknightUE_SK` (issue #1). The torso proportions come from the Codex dimensions (363 × 328 × 476 mm), not the real hero.
- The armour-set **one-connected-shell** rule from Codex's notes is intentionally not kept: real plate armour needs separate plates. It's still **one mesh object** (one equip item). The owner confirms.
- LODs, the gorget join, and an in-engine look under the game's lighting.

