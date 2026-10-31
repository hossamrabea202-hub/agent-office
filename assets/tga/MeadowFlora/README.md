# Meadow flora kit (#352 for #351): wildflowers, bushes, bracken

Made 2026-10-31 by TGA (Claude). Original and procedural, with no third-party assets. Rebuild it with `tools/tga/flora`:
`tex_flora.py`, then `build_flora.py`, then `lookdev_flora.py`.

This kit is for adjustedfilm's `place_meadow_ue.py`, which scatters the meadow outside the castle walls. That script finds the meshes by these names in
`/Game/CastleDefender/Environment/Flora/Meadow`.

| Mesh | What | LOD0 tris | Height |
|---|---|---|---|
| `SM_Flower_Daisy_A/B/C` | Ox-eye daisy: 3, 5 or 7 heads with 22 rays each, a toothed spoon-leaf rosette and clasping stem leaves | 1.7k / 2.6k / 3.6k | 0.3–0.6 m |
| `SM_Flower_Poppy_A/B/C` | Red poppy: 2–4 crumpled four-petal flowers with a dark basal blotch and capsule, nodding hairy buds, a lobed rosette. C also has a ripe seed capsule | 1.3k / 1.9k / 1.9k | 0.35–0.65 m |
| `SM_Flower_Yarrow_A/B/C` | Yarrow: flat corymbs of about 46 florets on spreading rays, feathery leaves | 1.7k / 2.2k / 3.2k | 0.3–0.6 m |
| `SM_Flower_Cornflower_A/B/C` | Cornflower: scaly involucre, toothed blue funnel florets around a violet centre, a side branch with a bud, linear leaves | 1.0k / 1.6k / 3.4k | 0.4–0.75 m |
| `SM_Bush_Hawthorn_A/B` | Hawthorn: low twiggy shrub, grey fissured bark with lichen, lobed glossy leaves. B carries clusters of red haws | about 4k / 5.7k | 0.9 / 1.4 m |
| `SM_Bush_Hazel_A/B` | Hazel: coppice of straight stems, broad serrated leaves turning yellow (late October). B carries nuts in husks | about 6.3k / 7.9k | 1.5 / 1.9 m |
| `SM_Fern_Bracken_A` | Bracken: 6 fronds; brown stipes rise into near-horizontal lobed pinnae that brown towards the tips | about 6k | 0.6 m tall, 1.6 m wide |

- **Geometry.** Flowers and bracken are real geometry with no alpha. Bushes use real bark branches plus masked leaf-spray cards. Each card was rendered from about 20 real leaf meshes, with haws or nuts on the B variants. The cards lie on the crown surface and have normals bent outward, so the crown shades as one soft volume.
- **LODs.** LOD1 and LOD2 rebuild each plant with fewer segments and elements; the elements that remain grow to keep coverage. LOD3 is two crossed impostor cards baked from LOD0. Screen sizes:
  - flowers: 1 / 0.25 / 0.1 / 0.035
  - bushes: 1 / 0.45 / 0.2 / 0.07
  - fern: 1 / 0.35 / 0.15 / 0.05
- **Textures.** All are 2K, BC/ORM/N with DirectX normals, and pass `pbr_check` (non-metal p5/p50/p95 = 70/108/224 sRGB):
  - `T_MeadowFlora`: an atlas of 16 tiles for petals, discs, leaves, stems, bark, haws and bracts.
  - `T_MeadowCards`: leaf sprays and impostors, with alpha.
- **Materials.** `M_MeadowFlora` (opaque) and `M_MeadowCards` (masked, clip 0.4). Both use Two Sided Foliage, with subsurface = BaseColor × `SubsurfaceAmount` (0.6) and a `Tint` parameter for per-patch colour variation.
- **Wind.** `SimpleGrassWind` (`WindIntensity` 0.25, `WindSpeed` 0.15), weighted by (1 − R)². Leaf and petal flutter moves vertices along the normal: B mask × sin(time × `FlutterSpeed` + G), with `FlutterAmount` 0.8 cm.
- **Vertex colour `Col`.** R = stiffness (1 rooted, 0 free tip), G = phase (random per stem or branch), B = flutter.
- **Collision and Nanite.** No collision: foliage is walk-through, so give the bushes a capsule in the scatter if gameplay needs one. Nanite is off because of the masked cards.

## Unreal

```
py "<repo>/assets/tga/MeadowFlora/import_flora_meadow_ue.py"     (DRY_RUN = True first: lists what it would import)
```

The script does the following:
1. Imports LOD0.
2. Creates 4 LOD slots with the screen sizes above (`set_lods`).
3. Replaces LOD1–3 with the hand-built FBXs (`import_lod`).
4. Assigns `MI_MeadowFlora` / `MI_MeadowCards` by slot name.
5. Removes simple collision.
6. Logs LOD count and screen sizes per mesh.

Paste that log back to the board.

**Test list**
1. Run the dry run. It should list 17 meshes.
2. Run live. Each mesh should log "4 LODs".
3. Drop one of each into the level. Pivots are on the ground. Check that the poppies are red and the cornflowers are blue, and that bush leaves show no black cards.
4. Press Play and watch the wind. Stems should sway while the bases stay planted, and the petals and leaves should flutter.
5. Move the camera back and check the LOD pops with `r.ForceLOD` / `stat foliage`.

**Scatter rules** (for #351)
- Put flowers in species patches of 3–9, never an even spray. Daisy and poppy are the most common, yarrow sits in the drier patches, and cornflower grows near field and road edges.
- Put bushes at meadow edges, near rocks and along the walls.
- Put bracken in the half-shade of the bushes.
