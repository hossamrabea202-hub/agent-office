# Trim-sheet guide for #261 (TGA, 2026-10-31)

The Master builds two shared 2K trim sheets from the licensed textures on the owner's PC. Nothing licensed goes into the repo.

This guide fixes the layout, so that every agent can UV new props against it today and the Master's textures drop in later.

## Rules

- **Size:** each sheet is 2048 × 2048 with three maps:
  - `T_Trim_<Sheet>_BC` (sRGB)
  - `T_Trim_<Sheet>_ORM` (R AO, G roughness, B metallic)
  - `T_Trim_<Sheet>_N` (DirectX normal)

  Calibrate them to the realism knowledge base: non-metal albedo 30–240 sRGB, bare metal ≥ 180 sRGB, metallic 0 or 1.
- **Texel density:** 512 px/m, the props target, so a strip's pixel height maps straight to its real size (256 px = 50 cm).
  - Weapons and NPC gear that need more detail use their own 1K atlas, not the trims.
- **Strips tile along U, horizontally.** A plank or strap of any length takes one strip; U runs along the length at 512 px/m (4 m of length = U 0 → 1).
  - Paint every strip seamlessly in U. In V the strip stops at its rows.
  - `Spare` rows are for unique, non-tiling details.
- **Gutters:** leave 8 px between strips, filled by extending the strip's edge pixels (dilation).
  - That stays clean down to mip 3 (256 px), which is the farthest mip that props reach in a third-person view.
  - Keep UV islands 2 px inside the strip rows.
- **Matching:** colour and wear must match the existing kits (CampKit wood, TGA ore-shed and siege wood, the weapon-kit iron).
  - Check against them in the calibrated lookdev scene: grey ball at 118 sRGB, locked exposure.
- **Existing assets stay on their own textures.** One moves to the trims only after the owner approves a before/after screenshot of that asset (owner condition, #261).

## How to UV a new prop on a trim (Blender)

1. Model it with real-size boards, beams and straps. Apply scale.
2. Unwrap each board as a straight strip, then scale its UVs to the world density:
   - U length = board length / 4 m.
   - V height = board width / 4 m.
3. Snap V into the matching strip's **UV V range** (table below), then offset U freely to break up repeats.
4. End-grain faces go on `Beam_EndGrain`, one 128 px square per beam end. Metal bands go on `IronStrap*`. Unique bits go on `Spare`.
5. Assign `MI_Trim_WoodIron` or `MI_Trim_StonePlaster` in Unreal, or a second material slot when a prop mixes the trim with its own atlas.

`trim_layout.json` holds the same numbers for scripts: pixel rows, heights in cm, and V ranges.

## Master steps

1. Build the six maps on your PC from the licensed packs, to this layout. Import them anywhere under `/Game` (not the repo).
2. Open `create_trim_material_ue.py` and fill the `TEX` paths at the top. Then run `py "<repo>/handoffs/texture-plan/create_trim_material_ue.py"`.
3. The script does the following:
   - creates `M_Trim` (plus `UScale` to stretch along a strip, and the office's Tint / TintAmount / Wetness)
   - creates `MI_Trim_WoodIron` and `MI_Trim_StonePlaster`
   - sets the textures' compression, sRGB, wrap and 2K maximum

## Layouts
### T_Trim_WoodIron (2048 x 2048, 2040 px used)

| Strip | Rows (px, top = 0) | Height | Real size | UV V range | Content |
|---|---|---|---|---|---|
| OakPlank_Clean | 0-256 | 256 px | 50.0 cm | 0.8750-1.0000 | oak board face, 50 cm wide |
| OakPlank_Worn | 264-520 | 256 px | 50.0 cm | 0.7461-0.8711 | same board, edge wear + dirt in grain |
| PinePlank | 528-784 | 256 px | 50.0 cm | 0.6172-0.7422 | pine board, lighter, resin knots |
| Plank_Charred | 792-984 | 192 px | 37.5 cm | 0.5195-0.6133 | fire-blackened board, 37.5 cm |
| Beam_Side | 992-1248 | 256 px | 50.0 cm | 0.3906-0.5156 | squared beam face, 50 cm |
| Beam_EndGrain | 1256-1384 | 128 px | 25.0 cm | 0.3242-0.3867 | end-grain squares, 128 px each (25 cm) |
| IronStrap | 1392-1456 | 64 px | 12.5 cm | 0.2891-0.3203 | flat iron band, 12.5 cm |
| IronStrap_Rivets | 1464-1528 | 64 px | 12.5 cm | 0.2539-0.2852 | band with rivet row |
| NailRow | 1536-1568 | 32 px | 6.2 cm | 0.2344-0.2500 | nail heads on a 6 cm strip |
| Hinge | 1576-1672 | 96 px | 18.8 cm | 0.1836-0.2305 | strap hinge with knuckle, 19 cm |
| Rope | 1680-1744 | 64 px | 12.5 cm | 0.1484-0.1797 | twisted rope, 12.5 cm (cylinder UV around) |
| LeatherStrap | 1752-1816 | 64 px | 12.5 cm | 0.1133-0.1445 | stitched leather strap, 12.5 cm |
| Spare | 1824-2040 | 216 px | 42.2 cm | 0.0039-0.1094 | unique details: brackets, bolts, lock plates (no tiling) |

### T_Trim_StonePlaster (2048 x 2048, 2024 px used)

| Strip | Rows (px, top = 0) | Height | Real size | UV V range | Content |
|---|---|---|---|---|---|
| Ashlar_Block | 0-256 | 256 px | 50.0 cm | 0.8750-1.0000 | cut stone course, 50 cm |
| Ashlar_Worn | 264-520 | 256 px | 50.0 cm | 0.7461-0.8711 | same course, chipped arrises + moss line |
| Moulding_Ogee | 528-656 | 128 px | 25.0 cm | 0.6797-0.7422 | carved ogee moulding profile, 25 cm |
| Sill | 664-792 | 128 px | 25.0 cm | 0.6133-0.6758 | window sill / coping top, 25 cm |
| Arch_Voussoir | 800-992 | 192 px | 37.5 cm | 0.5156-0.6094 | wedge stones for arches, 37.5 cm |
| Plaster_Limewash | 1000-1256 | 256 px | 50.0 cm | 0.3867-0.5117 | limewashed plaster, flat |
| Plaster_Edge | 1264-1392 | 128 px | 25.0 cm | 0.3203-0.3828 | plaster broken edge showing stone, 25 cm |
| Brick_Course | 1400-1528 | 128 px | 25.0 cm | 0.2539-0.3164 | two brick courses, 25 cm |
| Mortar_Line | 1536-1568 | 32 px | 6.2 cm | 0.2344-0.2500 | recessed mortar joint, 6 cm |
| Cobble_Edge | 1576-1704 | 128 px | 25.0 cm | 0.1680-0.2305 | kerb / step edge, 25 cm |
| Spare | 1712-2024 | 312 px | 60.9 cm | 0.0117-0.1641 | unique details: keystones, carvings (no tiling) |

