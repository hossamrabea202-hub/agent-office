# Hand-off: Obsidian chest v2 textures (#64)

From: checkking (Claude), 2026-10-28. For: the Master (or the Vice) at the editor. Asset re-import only, no Blueprint paste.

## Why it looked like matte black plastic

The shipped steel BaseColor sat at ~0.02 linear almost everywhere (texture p10-p90: sRGB 0.145-0.176) at metallic 1. For a metal, BaseColor *is* the reflection colour, so the chest reflected very little and had almost no variation: one even dark sheet, which the dark level flattened further. v2 (measured): steel ~0.037 linear with a ~3x wider spread (sRGB 0.19-0.28), metallic 0.85 on the oxide and 1.0 on worn edges, blue-violet temper, hammer marks, polish and scratch roughness break-up, wider edge wear to bright steel, grime in cavities, and antique gold (dark, rough recess walls, polished high points).

Renders: `assets/checkking/Obsidian-Sovereign/Chest/renders/chest4k_v2_*.png` (baked game mesh, Cycles).

**Known issue (old, not new in v2):** the two over-the-shoulder leather straps bake as grey/white instead of leather (visible in the old renders too). They sit under the pauldrons when worn. checkking takes this as the next fix on #64.

## Part 1: textures (this hand-off)

1. `git pull` the office repo.
2. Output Log → Python: `py "<repo>/assets/checkking/Obsidian-Sovereign/Chest/reimport_textures_ue.py"`
   - Re-imports only `T_ObsidianSovereign_Chest_BaseColor`, `_ORM` and `_Normal_DirectX` in `/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Chest`.
   - Does **not** touch `SK_ObsidianSovereign_Chest` / `SM_…` or any material. **Don't** run `import_chest_ue.py`: it re-imports the mesh.
   - The UV layout is identical to the shipped bake (checked: max UV difference 0.0), so `MI_ObsidianSovereign_Chest` works as is.
3. Check in Play, with the Obsidian chest worn, close camera, in the courtyard and under a torch: steel sheen and blue-violet tint in the highlights, bright worn edges, gold that looks set into the metal. If it's still too dark in the level, raise `RoughnessScale` on the MI to 0.85 before you touch the textures (that's a Decision for the Master, live in the editor).

## Parts 2 and 3: old armour poking through, fit (needs the licensed knight FBX)

These need `ShadowknightUE_SK` + `SK_Knight_ChestRemnant`, which aren't on checkking's PC (#1). Whoever fitted the chest (the Vice, on the owner's PC) should:

1. **Find what pokes through.** In Play, wear Obsidian and look at the neck and shoulders from the front and both sides. The owner's screenshot shows gold + purple trim at the collar and the old pauldron inner edges.
2. **Collar/neck trim on KnightMesh:** add that section's material to the `ArmorMode` gate (same as `M_HeroArmor_AAA`: 1 = hide when worn), or, if it shares a material with parts that must stay, mask it with a vertex-colour/UV-region opacity mask.
3. **Pauldron edges in ChestRemnant:** in Blender, delete the collar faces inside the chest volume and push the pauldron inner rims 3-5 mm out from the chest surface (shrinkwrap with offset, chest as target). Keep the weights, re-export over `SK_Knight_ChestRemnant`.
4. **Bottom edge over the belt/tabard:** tuck the fauld lames behind the belt by moving the lowest ring ~1 cm in and up (lattice on the lower 8 cm of the chest), or hide the belt section under it with the same gate.
5. **Checks:** idle, walk, run, sword attack and crossbow aim. No old silver or gold/purple pieces through the chest, no chest through the pauldrons, the chest bottom behind the belt.

Built on: shipped chest `bake_ready.blend` (same LP + UVs), no Blueprint export needed.
