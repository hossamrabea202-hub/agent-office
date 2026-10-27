# Obsidian Sovereign: Shoulders L/R (AAA remodel by checkking)

Second piece of the set remodel, made to match the [chest pilot](../Chest/README.md). Same pipeline: built procedurally in Blender 4.5 (scripts in `source/`), baked from a dense high poly to a 13,016-triangle game mesh per side. The Codex shoulders stay untouched in `assets/Codex/Obsidian-Sovereign/Shoulders` for comparison.

## What's new vs the Codex version

| | Codex (Round 1) | This remodel |
|---|---|---|
| Construction | one closed shell with painted lame lines | **real pauldron**: domed main cap with a medial keel, a **turned stop rib** below the neck edge, and **4 articulated lames** tucked under each other |
| Edges | gold-painted rim | **rolled edges** on the cap (top, bottom, front and back ends) and on every lame |
| Articulation | none | **sliding rivets** at both lame ends plus a centre rivet on each lame, rivets at the cap ends |
| Fastening | none | **leather arming strap round the upper arm** with steel buckle and tongue, and a riveted leather hanger from the last lame to the strap |
| Ornament | flat drawn lines, sun disc | the chest's vocabulary: **gold inlay** (laurel sprays either side of the keel, lozenge), **double gold borders with etched dark bands** on the cap, a gold line on each lame |
| Surface | uniform black | same procedural layers as the chest: blackened steel with temper colour, hammer marks, worn edges, grime in cavities, scratches, leather grain |
| UVs | Smart UV | **true-length unrolled islands** per plate and rim, inner shell at 35% density, **0 overlapping pixels** (checked at 512), ~65% used |
| Triangles | 19,196 faces | 13,016 per side |

## Files

- `SM_ObsidianSovereign_Shoulders_L.fbx`, `SM_ObsidianSovereign_Shoulders_R.fbx`: game meshes, metres, Z up, facing -Y, **in the Codex set's frame** (they sit on the chest as exported). R is an exact mirror of L and shares its UVs and textures. Static, not skinned.
- `textures/`: 4K `T_ObsidianSovereign_Shoulders_BaseColor` (sRGB), `_ORM` (R = AO, G = roughness, B = metallic), `_Normal_DirectX` (16-bit, Unreal).
- `import_shoulders_ue.py`: UE 5.3 import. Both meshes and the textures with the right settings, one `MI_ObsidianSovereign_Shoulders` on the shared `M_ObsidianSovereign` master (made here too if the chest import hasn't run).
- `renders/`: beauty renders with the chest.
- `source/`: `shoulderlib.py` (pauldron surface round the upper-arm axis, reusing the chest's plate tools), `build_shoulders.py`, `bake_staged.py`, `run_bake.ps1`, `render_clay.py`. The shared `chestlib.py` / `materials.py` are in `../Chest/source/`.

## Still open

- **Fit and skinning** to `ShadowknightUE_SK` (issue #1). The arm axis (30° A-pose) and the shoulder joint position come from the Codex pieces, not the real hero.
- In game the lames should follow the upper-arm bone and the cap the clavicle/upper-arm blend; decide once the skeleton is here.
- LODs, and a look under the game's lighting.
- The leather (here and on the chest) reads a little light tan under bright studio light. If it looks the same in game, darken it set-wide in one pass rather than per piece.
- `renders/` show the chest with its committed textures next to the shoulders, both straight from the exported FBX files (no hand placement).
