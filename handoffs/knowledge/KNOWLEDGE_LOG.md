# Knowledge log: realism findings from every agent

Add new entries at the top. Format: **date · seat · topic**, then the finding, the source, and whether it was tested in our pipeline.

---

**2026-10-30 · hossam gmail (Claude), cloud · round 2: industry secrets (researched, not yet tested)**
I ran about an hour of research in four tracks: materials, lighting and camera, characters and motion, and VFX and
environment. Everything is in [INDUSTRY_SECRETS.md](INDUSTRY_SECRETS.md), with sources. The owner made it an office rule.
Proposed gate changes for `pbr_check`:
- Warn when natural materials (wood, stone, soil) sit below 50–60 sRGB. Dyed blacks measure down to 35, so 30 stays the
  hard floor.
- Warn when mean HSV saturation is above about 60 %. Measured natural materials sit at 30–55 %; rust is about 70 %.

Highest-value items to try first:
- whitewash and false ashlar on the castle
- Composite Texture (normal → roughness) on every ORM
- torches at 1700–1900 K with a drift plus 8–10 Hz flicker and a Source Radius
- zombie play-rate and start-position variation
- sphere-mask wounds

**2026-10-29 · TGA (Claude) · passing pbr_check is not enough: judge under a locked grey ball (tested)**
The v2 siege kit passed `pbr_check` (bark median ~60 sRGB, above the 30 floor). Under a calibrated lookdev, with the
exposure locked so the 0.18 grey ball reads 118 sRGB, the bark rendered darker than the ball and looked like stained
timber. The flat grey-sky renders had hidden it. The fix: scale BaseColor ×2.1 in linear light with a soft shoulder,
giving a median ~89 sRGB, which is in the weathered-wood band. This is exact for albedo, needs no rebake, and leaves
the normal and ORM alone. Script: `assets/laptop2/SiegeBarricadeKit/source/albedo_lift.py`.
- Meter in the **Standard** view transform, which is linear, then render with AgX at that exposure. Metering through
  AgX converges very slowly because of its highlight shoulder.
- Calibrated lookdev mode: `LOOKDEV=1` in `preview135.py` (Nishita sky, sun 35°, grey and chrome balls, auto-meter).
- Still open: the bark plates repeat a regular leaf-shaped pattern, which shows in calibrated light. The fix needs
  more irregular plate cells in `build_kit.py`, not texture work.

**2026-10-29 · TGA (Claude) · the validator averages sRGB channels: deep reds need a neutral lift (tested)**
`pbr_check` measures the mean of the sRGB channels, not luminance. A deep red such as old blood (R high, G and B near 0)
fails even when its luminance is fine, and scaling it up keeps G and B at 0. What passed was a soft toe in sRGB on the
channel mean: an even add of up to ~36, applied only to tones below ~70. It keeps the hue and removes the impossible
near-zero G and B, which real dried blood and skin don't have. Used on the Flesh Brute skins (all 10 maps pass).

**2026-10-29 · hossam gmail laptop2 (Claude) · metal albedo (tested)**
Our shield iron was baked at about 71 sRGB with metallic 1, which renders as black plastic in UE. Bare iron is about 0.56 linear (Epic), so
180–200 sRGB. Old dark iron = bright metal under a dark oxide or mill-scale layer whose metallic drops. Fixed in
`shieldmat.iron`; the validator caught it. Source: Epic material docs, Adobe Substance PBR guide.

**2026-10-29 · hossam gmail laptop2 (Claude) · lookdev exposure (tested)**
A physical sky at the default exposure rendered the 0.18 grey ball far too bright, and every asset looked washed out. Always set
exposure so the grey ball reads mid-grey (about 118 sRGB) before judging. Source: Cave Academy grey-ball method, Epic EV100 docs.

**2026-10-29 · hossam gmail laptop2 (Claude) · baking bugs to check for (tested)**
Three silent bake killers we hit:
1. End caps sharing the side strip's UV island paint across it.
2. Superellipsoid or planar UVs whose front and back overlap (the back gem showed on the front).
3. Tube sweeps with inward-facing normals, which render black through the normal map.

Check the BaseColor sheet itself, not just renders.
