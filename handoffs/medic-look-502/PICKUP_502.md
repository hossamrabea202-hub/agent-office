# #502 medic look: pickup note (checkking medic (Claude), 2026-11-04, stopped for credits)

Seat `checkking (Claude)` was held by the other checkking session, so this card was worked as `checkking medic (Claude)`.

## Done (in the repo)
- `tools/checkking/medic502/build_medic502.py`: Blender 4.5 script, `blender -b --factory-startup -P build_medic502.py -- <repo>`.
- `assets/checkking/MedicCape/textures/`:
  - T_MedicCape_BC / _ORM / _N (DX) / _N_GL / _Wear: 1024² tileable bleached linen, 12 cm tile, plain weave with
    64 threads per tile. Albedo lin 0.56/0.54/0.47 (p50 191 sRGB). Roughness 0.78–0.97.
  - Wear: R = breakup, G = mud speckle.
  - T_MedicEmblem_BCA / _ORM: TGA's herb-sprig idea redrawn as an embroidered emblem: green wool satin stitch in a
    stitched ring. Alpha = thread, with an 8 px clear border for Clamp. **Not a red cross.**
- `assets/checkking/MedicStaff/`:
  - SM_MedicStaff.fbx (3.1k tris) + medic502_staff.blend: hazel staff 1.68 m with a root-burl knob, a leather grip wrap
    (0.93–1.11 m) and an iron ferrule.
  - Pivot = grip centre (1.02 m above the tip), staff axis +Z.
  - Bevels: 3 mm on the ferrule, 2 mm on the wrap (texel density ~1067 px/m, so ≥ 3 texels).
  - textures/T_MedicStaff_BC / _ORM / _N / _N_GL: 512x2048 atlas. Wear by cause:
    - hand oil at the grip: darker, R 0.42;
    - soil splash on the bottom 30 cm;
    - sun-bleached knob top;
    - iron: dark oxide film; bare metal only where it is scraped (tip rim, raised hammer marks); rust at the lip; mud on
      the tip.
- `pbr_check.txt`: all 3 pairs OK.

## Key findings (use these)
- **The soldier look is built from 2 meshes.** Soldiers = hidden `Mesh` (SKM_Quinn_Simple + ABP_Quinn, always tick) +
  `KnightMesh` (ShadowknightUE_SK + ABP_KnightFollow).
  - The cape is KnightMesh **material slot 2** (MI_Hero_Cloth_Crimson, parent M_HeroCloth_AAA: Cloth shading, Masked,
    HideBackFlap).
  - The sword is a separate `Sword` StaticMeshComponent (SM_Longsword_LP), attached to hand_r in the graph.
  - Sources: laptop2/gameplay MANIFEST, black-faces-435 scan_report, weather-226 setup_torchbearer355_ue.py.
- **#185's BP_Medic copied only the Quinn `Mesh`** (setup_medics185_ue.py), so the medic probably shows as a visible
  mannequin. It has no sword component.
- Cape UVs are licensed and not in the repo. Plan: **project the emblem in Pre-Skinned Local Position.**
  - U = 0.5 − x/30 cm, V = 0.5 − (z − 122 cm)/30 cm.
  - Mask: Pre-Skinned Normal.y < −0.25 (the back faces −Y in mesh space). Add an `EmblemSide` ±1 param in case the
    back turns out to be +Y.
  - Hem mud: pre-skinned z < 45 cm × Wear.R/G.

## Not done (next agent)
1. `apply_medic502_ue.py` (UE 5.8) with `--dry-run`, `--preview` and a backup (`BP_Medic_BACKUP502`):
   - **Import the textures:**
     - BC: sRGB, mip Sharpen4;
     - ORM: Masks, Composite Texture = N, mode Normal-roughness-to-green;
     - N: Normalmap;
     - emblem: Clamp.
   - **Import the staff mesh** with normals and tangents.
   - **Staff material:** MI_MedicStaff = child of TGA's M_MedicGear.
   - **Cape material:** M_MedicCape = **duplicate** of M_HeroCloth_AAA (never edit the original). Re-wire BaseColor and
     Roughness: linen × LinenTiling (8), hem mud, emblem lerp. Keep the Opacity, Normal and AO of the original graph.
     If it uses Material Attributes, fall back to a white Tint MI and log it.
   - MI_MedicCape: copy the params from MI_Hero_Cloth_Crimson. FuzzColor ≈ linen luminance.
   - **BP_Medic only:**
     - hide Mesh and copy the soldier Mesh's visibility and tick options;
     - add a `Knight` SkeletalMeshComponent under Mesh, with properties copied from BP_SoldierSword's KnightMesh
       template and slot 2 = MI_MedicCape;
     - hide any Sword/Shield component (don't delete it);
     - add a `Staff` StaticMeshComponent on hand_r. Set the socket with `attach_socket_name`, and if that fails use the
       SCS node `attach_to_name` (the torchbearer355 trick).
     - Satchel: SCS socket spine_03. The #185 graph re-attaches it anyway.
   - `--preview` = do all of this on a duplicate `BP_Medic_Preview502`, for the owner's before/after shots.
2. Lookdev: Blender shots with locked exposure (TGA's lookdev_medic.py metering pattern). Then the i9 before/after of
   BP_Medic vs the preview.
3. Hand off to i9 with `office.js handoff`. **The swap waits for the owner's OK.**

## Rules applied
- KB rules 1–3 (calibrated values, roughness never flat, wear by cause).
- Bevels from texel density, 16-bit normals, Composite Texture planned.
- §1.3.5 cloth values, §1.3.6 Sharpen4.
- New assets only. Licence-safe emblem.
