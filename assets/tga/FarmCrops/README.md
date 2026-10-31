# Farm crops for #223 — TGA (Claude), 2026-10-31

Crop art for the farming system (the farmer character and the farming BP are not part of this). Original procedural work.
Sources: `tools/tga/farm/` (`build_farm.py` → `paint_farm.py` → `lookdev_farm.py`). Run `import_farm_ue.py` in the
UE 5.3 editor (`py "<path>"`); it lands in `/Game/CastleDefender/Props/Farm`.

| Mesh | Tris | What |
|---|---|---|
| SM_Field_Plot | 12.8k | 4 × 4 m tilled plot, 8 furrow ridges along X (every 50 cm), edges ease down to the ground |
| SM_Crop_Wheat_Sown | 5.3k | 1 × 1 m patch: fresh shoots, 4–8 cm |
| SM_Crop_Wheat_Growing | 10.1k | green stalks with leaves, 32–50 cm |
| SM_Crop_Wheat_Ripe | 13.0k | golden stalks 85–108 cm with ears and awns, leaning a little downwind (+X) |
| SM_Crop_Wheat_Harvested | 5.9k | stubble, loose straw and one bound sheaf |
| SM_Crop_Cabbage_Young | 1.7k | 4 young cabbages, open leaves |
| SM_Crop_Cabbage_Ripe | 2.1k | 4 ripe heads, about 21 cm, with wrapper leaves |

- **Placement:** each crop patch is 1 × 1 m with two rows at y = ±25 cm.
  - Put patches on the plot at x/y ∈ {-150, -50, 50, 150} cm (16 per plot); the rows then sit on the ridges.
  - All pivots sit on the ground at the centre. Rotating a patch by 180° about Z keeps the rows on the ridges, which helps hide repeats.
- **Growth:** swap the stage mesh at the same transform (Sown → Growing → Ripe → Harvested). Cabbage goes Young → Ripe, then remove the patch on harvest.
- **Materials:**
  - **M_FieldSoil:** seamless 2 m tile (≈1000 px/m) with clods, pebbles, straw and damp patches.
  - **M_Crops:** a single 2048² trim sheet covering stalks, ears, leaves and cabbage. It is two-sided and has no alpha cards.
  - Both have Tint, TintAmount and Wetness; rain → Wetness for #226. pbr_check OK on both.
- **Wind:** vertex colour R is a wind weight (0 at the root, 1 at 1 m). M_Crops wires it into the engine's SimpleGrassWind (WindIntensity 0.3, WindSpeed 0.6). If that function is missing, the import logs a warning and the crops stay still.
- **Performance and collision:** the import turns Nanite on for every crop and gives crops no collision (feet pass through). The plot gets a thin box collision.
  - A full ripe plot is ≈210k tris, so keep Nanite on.
  - Without Nanite, use the Growing/Ripe meshes at a distance only via HISM with a cull distance.
- **Honest notes:**
  - The wheat ears use the trim sheet, so the awns are thin geometry and shimmer a little at long range without TSR.
  - There is no subsurface translucency on the leaves, so there's no back-lit glow.

Screens: `screens/`.
