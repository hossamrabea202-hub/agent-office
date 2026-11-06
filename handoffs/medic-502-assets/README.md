# #502 Medic: final assets + badge (TGA PC (Claude), 2026-11-06)

The medic's art is done: cape linen + emblem, staff, a new satchel and the UI badge. `import_medic502_assets_ue.py` brings it
all into UE 5.8 as **new assets only**. Putting it on BP_Medic (and the C++ side) is for the next seat.

## What's in here
| Asset | What it is | Notes |
|---|---|---|
| `T_MedicCape_*` + `T_MedicEmblem_*` | bleached linen (12 cm tile) + the herb-sprig emblem, embroidered | checkking medic's textures (#502), pbr_check OK |
| `SM_MedicStaff` + `T_MedicStaff_*` | hazel staff 1.68 m, leather grip, iron ferrule, 3.1k tris | pivot = grip centre, axis +Z -> `hand_r` |
| `SM_MedicSatchel502` + `T_MedicSatchel502_*` | **new**: physician's leather satchel 28x19x9 cm, flap with 2 buckle straps, emblem patch, D-rings, flat 3.5 cm strap, dried-herb bundle. **4.8k tris** (baked from a 29.7k high), 2K atlas | replaces the blocky #248 satchel. Same attach as #248: pivot = strap top -> `spine_03`, front = -Y |
| `T_UI_MedicBadge_512 / _128 / _64` | medic badge: herb sprig on a linen disc in a gold ring (Muster / Vesna colours) | recruit card (512/128), MEDICS HUD line + desk chip (64) |

## Run it (Master)
1. `py import_medic502_assets_ue.py`: **dry run**. Expect `DRY RUN OK`, no `MISMATCH`. It also prints the soldier cape MI's
   parameters and which ones it will set.
2. `py import_medic502_assets_ue.py --apply`: imports into `/Game/CastleDefender/Characters/NPC/Medic502` and saves those new assets only.
3. Undo: `--revert` deletes only that folder.

## Cape note (read before wiring)
- `MI_MedicCape` is a child of the soldiers' `MI_Hero_Cloth_Crimson`, so Cloth shading, Masked and HideBackFlap stay identical.
- It sets the linen textures and a linen tint **only if** the parent has matching parameters. The apply log says exactly what was set.
  If the parent has no texture params, it's a plain child, and the linen needs the `M_MedicCape` duplicate from `../medic-look-502/PICKUP_502.md`.
- **Emblem on the cape:** the cape's UVs are licensed and not in the repo, so the emblem needs the Pre-Skinned Local projection from
  PICKUP_502.md (30 cm wide, centre 1.22 m on the back). That's a material-graph job for the wiring seat. The textures are imported ready for it.

## Checks done here (this PC has no editor)
- pbr_check: satchel OK (non-metal p50 62 sRGB, roughness 0.50-0.85), staff OK, cape OK.
- Lookdev with locked exposure (grey ball metered 116 sRGB, exposure -5.90, AgX): `shots/medic502_lookdev_lineup / _close / _satchel.png`.
  Badge on a dark panel and on bright ground: `shots/medic502_badge_sheet.png`.
- The import script is syntax-checked only. **Never run in UE**, so the dry run is its first test.
- The satchel iron came out as dark oxide everywhere, with no bare-metal highlights: the bake cleanup removed the few rubbed edges. It reads as old blackened iron.

## Rules applied
- KB 1-3: calibrated albedo (linen 0.56, never white; leather ~sRGB 62), roughness never flat, wear by cause (hand oil on the strap and flap, dust in the seams, oxide on the iron).
- INDUSTRY_SECRETS 0.1 (locked exposure), 0.3 (dirt has a cause), 0.10 (one leather family with #248's gear). Licence-safe emblem: no red cross.
- New assets only, `--dry-run` first, `--revert`.

Sources to rebuild: `source/build_satchel502.py` (Blender 5.0), `source/lookdev_medic502.py`, `source/make_badge502.ps1`.
