# Water trough + bucket (#202 item 5) — TGA (Claude), 2026-10-30

Original procedural yard props for the barracks / stables / castle yard. Sources: `tools/tga/trough/`
(`build_trough.py` → `bake_trough.py` → `lookdev_trough.py`). Run `import_trough_ue.py` in the UE 5.3 editor.

| Mesh | Size | Tris | Slots |
|---|---|---|---|
| SM_WaterTrough | 2.0 × 0.6 m, rim 0.75 m | 1.2k | 0 wood/iron atlas, 1 water surface (M_TroughWater) |
| SM_Bucket | Ø 0.32 m, 0.32 m tall | 2.2k | 0 wood/iron atlas |

- Trough: plank box on two splayed trestles, end boards, iron bands at both ends; still water 8 cm under the rim.
- Bucket: tapered shell (staves tinted one by one in the texture), two thin iron hoops, iron bail handle.
  Honest note: the hoops and stave seams are subtle at gameplay distance.
- One shared 2048² atlas (≈545 px/m), the ore-shed wood baker: grain along each board, sun-greyed tops, damp base,
  rusty iron (bare iron metallic, rust non-metal). pbr_check OK. M_Trough / MI_Trough with Tint, TintAmount, Wetness.
- M_TroughWater: simple opaque dark glossy water (swap for the project's water material if there is one).
- Box collision each.

Screens: `screens/`.
