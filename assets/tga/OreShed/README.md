# Ore stockpile shed (#202 item 2) — TGA (Claude), 2026-10-30

Original procedural asset for the #201 mine/metal system: the castle-yard end of the cart road, where the ore carts
unload. Sources: `tools/tga/oreshed/` (`build_shed.py` → `bake_shed.py` → `lookdev_shed.py`).
Run `import_oreshed_ue.py` in the UE 5.3 editor (`py "<path>"`).

- **SM_OreShed**: 6.0 × 2.6 m lean-to, 2.9 m at the open front, 2.2 m at the back; 11.1k tris, 121 individual timbers
  (posts, eave beams, rafters, knee braces, overlapping roof / back / side boards, bay dividers, low front boards, floor),
  each with a slight sag/tilt so it reads hand-built. Pivot at the floor centre; the open front faces Blender −Y (check the facing once after import and rotate the actor).
- **5 bays**, one per metal (left → right as seen from the road): Iron, Copper, Silver, Gold ore, Starmetal. Each has a
  hanging tally board on two iron chains for a metal icon/decal-free text plate later. Bay centres (cm, local):
  x = −232, −116, 0, 116, 232; y = 0; floor z = 3. Drop laptop2's MineKit ore loads (#202 item 1) in them, or scale
  an ore heap with the stock count.
- **Textures** 4096² (≈180 px/m): BaseColor (sRGB), ORM (R AO, G roughness, B metallic: bare iron only), Normal
  (DirectX). Wood grain follows each timber's long axis (baked per piece), sun-greyed tops, damp line at the base, moss
  in the roof hollows, ore-dust stains in the bays, rusty chains/nails. pbr_check OK.
- **Material** M_OreShed / MI_OreShed with Tint, TintAmount and Wetness (rain darkens + smooths the wood).
- **Collision**: convex hulls (bays stay walkable; falls back to one box if decomposition fails).

Screens: `screens/`.
