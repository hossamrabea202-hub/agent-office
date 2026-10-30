# Knowledge base: realism (top priority for every agent)

**Owner's rule, 2026-10-29:** every agent reads these before making or changing anything visual, applies them, and
adds what they learn. The goal is the most realistic result we can reach: "real life, not a game".

## Read first, in this order

1. [Photoreal game asset playbook](Photoreal%20game%20asset%20playbook.md). The research report: how Naughty Dog, Rockstar,
   Sucker Punch, Guerrilla, Epic/Quixel and film/streaming VFX houses (Blur, Digic, Weta, ILM) get photorealism. It has a
   **ranked playbook** and a **pre-hand-off checklist with numbers**.
2. [Realism standard](../laptop2-realism/STANDARD.md). The short rules version: calibrated albedo, roughness, wear in
   physical order, lookdev.
3. **[Industry secrets](INDUSTRY_SECRETS.md) (2026-10-30, office rule).** Round 2: measured per-material values, the
   Composite Texture trick, lighting and camera numbers, torch Kelvin and flicker, skin, eyes and zombie motion, gore
   without C++, fire flipbooks, and what real medieval castles looked like. Start with its **10 rules**.
4. `research_notes/`. The raw findings behind the report, with sources: materials and PBR, geometry and baking,
   environment and vegetation, lighting and lookdev.

## The rules that matter most (from the playbook)

1. **Calibrated values.** Non-metal BaseColor is 30–240 sRGB (50 if strict). Bare metal is ≥ 180 sRGB. Metallic is 0 or 1
   (in-between only at rust and dirt edges). UE Specular stays 0.5 (4 %). No lighting or AO is baked into BaseColor.
2. **Judge only in a calibrated lookdev scene,** never in the game level. It has a grey ball (albedo 0.18), a chrome ball,
   a colour chart and **locked exposure** (Min EV100 = Max EV100).
3. **Every wear layer has a physical cause, in this order:** base → grain → sun → edges (curvature) → cavities (AO) →
   gravity streaks → up-facing dust or moss → wetness (Lagarde: wood darkens ~0.82/0.58/0.38 per channel, gloss
   gain ×0.5, metals don't darken) → one shared dirt pass. Add a transition band where two materials meet. Restraint
   over grunge.
4. **Bevels are sized from texel density:** at least 2–3 texels (≥ 2–3 mm at 1024 px/m). 16-bit normal bakes, MikkTSpace,
   import normals in UE.
5. **Ground every prop.** Sink it 10–30 %, add a debris skirt, blend it into the terrain (RVT) and darken the contact line.
6. **Lumen-safe building.** Walls ≥ 10 cm thick and closed. A real light behind every small emissive (torches).
7. **Vegetation by rules, not uniform scatter.** Use clumping noise, layered wind, several densities and culls.

## Tools

- `tools/laptop2/pbr_check.py`: `blender -b --factory-startup -P pbr_check.py -- <BaseColor.png> <ORM.png>`. It flags
  albedo out of range, dark metal, in-between metallic and flat roughness. Run it before every texture hand-off.

## Contribute

Found something that makes things look more real (a talk, a number, a trick that worked or failed)? Add it to
[KNOWLEDGE_LOG.md](KNOWLEDGE_LOG.md):
- one entry per finding
- give the source and the date
- note whether you tested it

Post one line in the cafeteria when you add something important. The playbook gets updated from the log.

## Owner rule 2026-10-30: do not break the decal system
Retexturing or material edits on existing assets have broken the decal system more than once. From now on:
1. Never change DBuffer / decal settings, decal materials or the materials that decals sit on without the owner's OK.
2. Prefer new mesh variants or new material *instances* over editing a live material.
3. Test one piece side by side with an original that carries decals, screenshot it, then roll out.
