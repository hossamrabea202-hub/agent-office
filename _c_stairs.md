From: hossam gmail (Claude), Master. **Owner order 2026-10-31 09:08: assigned to @TGA (Claude).**

## AAA staircases: one watertight hero mesh per flight, high poly baked to low poly
The castle stairs are 238 separate step/stair actors (boxes) with flat tiling stone. The owner wants each staircase to be **ONE watertight 3D mesh**, with a high poly baked down so it looks high-poly at low-poly cost.

**Per flight:**
- **Low poly:** one watertight element. Steps, side stringers / walls and the landing in one mesh. Quads/tris, no n-gons, ≤1k tris per flight (owner asset standard), clean UVs plus a lightmap UV.
- **High poly (≤50k):** rounded bevels on every edge, chipped corners and broken step noses, worn dished tread centres where people walk (deepest in the middle and on the bottom steps), a few cracked steps, mortar joints.
- **Bake** high → low: Normal (DirectX), AO, Curvature (and Height if useful).
- **Materials:** stone PBR driven by the bakes. Darker grime in cavities and joints, lighter worn edges, polished, smoother (lower roughness) tread centres, moss/damp near the ground. 2K BC/ORM/N, pbr_check pass, realism KB + INDUSTRY_SECRETS §1/§4.
- **Match** the castle stone look (MI_Castle_StoneWall_World / Castle_StepCap colours).
- **Reuse:** identical flights share one asset; make a kit (straight flight N steps, wall-hugging flight, gatehouse steps).

**Hand-off:** an import script (StaticMesh + MI) plus a placement script that replaces the old step actors at the same transforms (it hides the old ones in a folder first, so they can be undone). Request the stair export with `office.js request --kind export --target "ThirdPersonMap stairs"` (the Master will export the stair actors' transforms and bounds as JSON).

**Note:** the stair-wear decals the Master tried (V2_StairWear) are removed; they read as stripes. Wear belongs in the baked material.
