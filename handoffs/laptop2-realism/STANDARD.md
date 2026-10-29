# Realism standard for Castle Defender assets (all seats)

Written 2026-10-29 by `hossam gmail laptop2 (Claude)` after a research pass the owner asked for: how top studios
make things look real (AAA texturing breakdowns, PBR calibration charts, Megascans/VFX lookdev practice). Sources are
at the bottom. Every new asset should pass this before it's handed off.

## 1. Calibrated albedo (BaseColor)

| Surface | Albedo (sRGB) | Notes |
|---|---|---|
| Any non-metal | **30–240** (aim for ≥ 50) | Nothing is black. Charcoal is about 30–40 and fresh snow about 240 |
| Weathered wood | about 90–115 (0.12–0.16 linear) | Fresh-cut wood is lighter (0.35–0.42 linear) |
| Bare metal | **180–250** | Darkness on old metal is oxide, rust or grime: non-metal layers with metallic 0 where they sit |
| Rust | 50–110, metallic 0 | Rough (0.85–0.95) |

Saturation: real materials are far less saturated than you think. Keep paint, wax and leather believable.

## 2. Roughness does the realism

- Never flat. Every surface has 5–10 % micro-variation, plus mid and macro (large patch) variation.
- Physics drives it:
  - wet areas and algae are glossier
  - dust is drier and rougher
  - polished contact edges (grips, worn edges) are smoother
  - rust is the roughest

## 3. Wear follows physics, layered in this order

1. Clean base (calibrated, with macro tone variation between parts: no two boards or planks the same).
2. Grain or structure (wood grain along the UV, hammer marks on iron, leather grain).
3. Exposure: sun-greying on outward and upper faces.
4. **Edge wear (curvature):** exposed edges wear first. Lighter or bare, and rougher on wood, brighter on metal.
5. **Cavity grime (AO):** dirt collects in hollows, the inverse of edge wear.
6. **Height and water:** a wet band near the ground, tide lines, algae and moss low down and in cavities, rot at the
   bottom.
7. **Gravity streaks:** rain streaks down from top edges, rust runs below every nail and strap, drips under wax.
8. One shared final dust or dirt pass over all of the prop's materials, so they belong together.
9. **Storytelling damage:** gashes, dents, a scorch, nicks, placed for a reason and not spread everywhere.

**Restraint:** the classic CG mistake is too many grunge layers. Subtle, then stop.

## 4. Geometry

- No razor edges: everything gets a small bevel or chamfer, so it catches a highlight.
- Real scale in metres. Texel density stays even across a prop (average the islands before packing).
- Imperfection: warp, sag, lean and irregular ends. Nothing is perfectly straight or symmetric.
- Low poly plus a high-poly bake. Check for overlapping UVs, cap islands, and inward-facing normals (which render black).

## 5. Lookdev and checks before hand-off

- Render a lookdev turntable or 3–4 views under a real sky (Nishita sky, sun about 35°), not flat grey. Metal needs
  something to reflect.
- Run the validator: `blender -b --factory-startup -P pbr_check.py -- <BaseColor.png> <ORM.png>` (in `tools/laptop2/`).
  It flags:
  - non-metal albedo outside 30–240 sRGB
  - dark metal (below 150 sRGB)
  - flat roughness
- Look at the BaseColor sheet itself: smears, black islands or a part's colour showing on another all mean a UV or
  normals bug.

## Sources

- [80.lv: photorealistic wooden box with natural wear](https://80.lv/articles/how-to-model-texture-a-photorealistic-wooden-box-with-natural-wear-and-tear/)
- [StraySpark: procedural damage workflow](https://www.strayspark.studio/blog/procedural-damage-game-assets-complete-workflow)
- [Leartes: textures and materials](https://cosmos.leartesstudios.com/blog/how-to-bring-your-3d-game-environment-to-life-with-textures-and-materials)
- [Shinsoj: PBR colour space and albedo chart](https://shinsoj.artstation.com/blog/Q9j6/pbr-color-space-conversion-and-albedo-chart)
- [Studio Matrx: Megascans variation](https://www.studiomatrx.org/students/real-time-vr-for-architecture/megascans-and-quixel-assets)
- [Relebook: realistic Unreal textures](https://www.relebook.com/articles/creating-unreal-engine-textures-realistic-environments)
- [Megascans: quarry lookdev](https://blog.megascans.se/?p=481)
