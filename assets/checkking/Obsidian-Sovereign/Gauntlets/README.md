# Obsidian Sovereign: Gauntlets L/R (AAA remodel by checkking)

Third piece of the set remodel, matching the [chest](../Chest/README.md) and [shoulders](../Shoulders/README.md). Same pipeline: built procedurally in Blender 4.5 (scripts in `source/`), baked from a dense high poly to a 9,398-triangle game mesh per hand. The Codex gauntlets stay untouched in `assets/Codex/Obsidian-Sovereign/Gauntlets` for comparison.

## What's new vs the Codex version

| | Codex | This remodel |
|---|---|---|
| Construction | one smooth hand shell, straight fingers | **leather glove with steel plates**: flared cuff, 2 wrist lames, metacarpal plate, knuckle plate with **4 domed knuckle bosses** |
| Fingers | plain tubes | each finger in **3 jointed parts with a relaxed curl**, a **steel scale on every joint** overlapping the next; thumb with a scaled thenar pad and 2 scaled joints |
| Edges | gold paint | **rolled edges** on the cuff (top and bottom), every lame and plate, and the metacarpal sides; rivets at the lame ends and plate corners |
| Ornament | flat lines | the set's vocabulary: **gold double borders with an etched band** on the cuff and metacarpal, gold lozenges, **laurel sprigs** on the back of the hand, a gold line on each wrist lame |
| Palm | same black as the back | **darker glove leather** with **saddle-stitched seams** (palm edges, wrist and finger base) |
| UVs | Smart UV | true-length unrolled islands, plate inner shells at 35% density, **0 overlapping pixels**, ~77% of the sheet used |
| Triangles | 15,172 | 9,398 per hand |

## Files

- `SM_ObsidianSovereign_Gauntlets_L.fbx`, `_R.fbx`: game meshes, metres, Z up, facing -Y, **in the Codex set's frame** (same place and pose as the Codex hands: hanging straight down, back of the hand forward, thumb toward the body). R is an exact mirror of L and shares its UVs and textures. Static, not skinned.
- `textures/`: 4K `T_ObsidianSovereign_Gauntlets_BaseColor` (sRGB), `_ORM` (R = AO, G = roughness, B = metallic), `_Normal_DirectX` (16-bit, Unreal).
- `import_gauntlets_ue.py`: UE 5.3 import. Both meshes and the textures, one `MI_ObsidianSovereign_Gauntlets` on the shared `M_ObsidianSovereign`.
- `renders/`: back, three-quarter, thumb side and palm.
- `source/`: `gauntletlib.py` (an `Axial` surface per part: hand, cuff, every finger joint, thumb), `build_gauntlets.py`, `bake_staged.py`, `run_bake.ps1`, `render_clay.py`, `uvoverlap.py`. The shared `chestlib.py` / `materials.py` are in `../Chest/source/` (`materials.LEATHER_TONE` sets the glove's darker leather).

## Still open

- **Fit and skinning** to `ShadowknightUE_SK` (issue #1). Hand size and finger layout follow the Codex gauntlet, and the fingers are posed in a relaxed curl. Each finger joint is a separate part, so skinning is one bone per joint plus the hand bone for the plates.
- Gripping a sword or crossbow will need the real hand pose. Check for clipping between the finger scales once it's skinned.
- LODs, and a look under the game's lighting.
