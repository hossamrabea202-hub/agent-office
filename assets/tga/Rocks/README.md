# Rock cluster set (#202 item 4) — TGA (Claude), 2026-10-30

Original procedural boulders for the road, courtyard and mine approach. Sources: `tools/tga/rocks/` (`build_rocks.py`
→ `bake_rocks.py` → `lookdev_rocks.py`). Run `import_rocks_ue.py` in the UE 5.3 editor (`py "<path>"`).

| Mesh | Size | Tris |
|---|---|---|
| SM_Rock_S | ~0.5 m | 2.1k |
| SM_Rock_M | ~1.2 m | 4.4k |
| SM_Rock_L | ~2.4 m | 8.4k |

- Noisy ellipsoids cut by random fracture planes (flat broken faces with chipped, soft edges), shallow bedding strata,
  sunk 15 % so they sit in the ground; the buried underside is cut away. Pivot at ground level under the centre.
- One shared 2048² atlas (≈350 px/m), two skins: **Dry** (weathered granite-grey, mica speckle, pale lichen rosettes,
  dust on top) and **Mossy** (patchy moss cushions on the tops and in hollows). Shared Normal (DirectX), ORM (R AO,
  G roughness, B 0). Both pbr_check OK.
- M_Rock / MI_Rock_Dry / MI_Rock_Mossy (Tint, TintAmount, Wetness — rain darkens and smooths). Meshes default to Dry.
- 26-DOP simple collision. Scatter tip: clusters of 1 L + 1-2 M + 2-4 S, random Z rotation, sink 5-10 cm, Mossy in shade.

Screens: `screens/`.
