# #293 Blob mines, blobs and the realm bubble: research before the redesign

By `adjustedfilm (Claude)`, 2026-10-31. Owner (W:): *"the blobs that act as mines are very bright and cartoonish. Study
Netflix and sci-fi studio research before redesigning both blob mines, blobs, and realm bubble."*

## 1. What the studios did (sources at the end)

**Netflix, *Stranger Things 3* (Rodeo FX): the Mind Flayer's flesh, which starts as blobs of goop**
- **Practical first.** They filmed goopy materials and real meat, then matched the CG to them. No invented colour.
- **"A mix of wet and dry skin to have a nice breakup over the surface."** Even gloss reads as plastic. Wet patches
  against tacky, drier patches read as flesh.
- **Lineage: Carpenter's *The Thing*.** Dark, desaturated reds and bruise browns, translucent membranes, mucus strings.
  Never saturated candy colours.
- **ILM (season 5):** organic walls got a real **subsurface** component, so a flashlight shows light spreading inside.
  Subsurface, not emissive glow, is what makes flesh feel alive.

**Sci-fi film, *Annihilation* (DNEG, with DP Rob Hardy): the Shimmer, the closest film reference for our realm bubble**
- **Mostly photographed.** Lens and on-set lighting tests came first, and the CG matched an analogue source.
- **The look is a "petrol slick":** an oily or soapy **thin-film iridescence** (interference colours that change with the
  viewing angle). It is mostly clear, and colour only shows at grazing angles and in drifting bands. It is **not** a
  coloured glowing dome.
- **Inner structure comes from fractals** (DNEG's Mandelbulb studies): slow, self-similar patterns instead of cartoon
  shapes.

## 2. What that means for our assets

| Asset | Why it looks cartoonish now | What to change |
|---|---|---|
| **Blob mines** (BP_BlobMine, #191) | bright, saturated, evenly glossy, self-lit | **Dark, desaturated flesh-slime:** base albedo 0.04–0.12 (bruise red-brown, bile olive). **Subsurface** (Subsurface Profile or Two-Sided Foliage) with a deep-red scatter colour. **Roughness breakup:** wet 0.05–0.15 in patches, tacky 0.35–0.5 elsewhere (noise mask). **No emissive**; the "armed" tell becomes a slow pulse of the subsurface, or a faint heartbeat in the vertex offset. |
| **Blobs** (#137 / #164) | same family | same material family as the mines, so they read as one species. Add **mucus strings / drips** (masked cards, or the #82 slime trail material), and a slight **vertex wobble** at about 0.5–1 Hz, not a bouncy cartoon squash. |
| **Realm bubble** (M_RealmBubble2, #169) | a purple haze with glow 1.5 reads as a game shield | **A "petrol slick" thin-film:** mostly clear (opacity 0.02–0.06 head-on), with interference colours only in a **fresnel** band (thickness from slow noise, hue from a thin-film approximation). Faint refraction. **Glow 0** by day and very low at night. The tentacle silhouettes stay, darker and less saturated. Optional: slow fractal-like domain-warped bands drifting across it. |

**Realism rules to apply:**
- calibrated albedo: dark organics 0.03–0.15 linear;
- no emissive on biology unless it is bioluminescent by design;
- **one** cue for danger (the pulse), not colour;
- lookdev under locked exposure, by day and at night;
- before/after shots for the owner's OK (live materials are not swapped without approval).

## 3. Build plan (next agent or me: new assets only, nothing live overwritten)

1. **Request (filed):** the material slots and current materials on BP_BlobMine's `Blob` mesh and the blob actor, plus a
   screenshot of each, and the parameter values of the MI on SM_RealmDome.
2. **`M_FleshSlime` + `MI_BlobMine_Flesh`, `MI_Blob_Flesh`:**
   - lit, Subsurface Profile `SSP_FleshSlime` (scatter radius about 1.2 cm, deep red);
   - Custom HLSL for the wet/tacky roughness breakup, veins (domain-warped noise, slightly darker and more translucent);
   - a `Pulse` parameter that only raises the subsurface. No textures, so no licence issues.
3. **`M_RealmBubble3` + `MI_RealmBubble3`:**
   - translucent, surface lighting;
   - thin-film hue from `cos(2π·(thickness·k + {0, 0.33, 0.67}))` × fresnel;
   - opacity 0.03 head-on, rising to about 0.35 at the rim; refraction 0.02;
   - keep #169's tentacle silhouettes, darkened.
4. **Lookdev:** a setup script applies the new MIs to **copies** placed beside the originals, with before/after
   screenshots by day and at night. **Swap only after the owner says yes.**

## Sources
- [Stranger Things 3: Rodeo FX breakdowns (Digital Production)](https://digitalproduction.com/2019/10/17/stranger-things-3-rodeo-fx-breakdowns/)
- [How the VFX team channeled *The Thing* for the Mind Flayer (Yahoo / IndieWire)](https://www.yahoo.com/entertainment/stranger-things-vfx-team-channeled-214547044.html)
- [ILM: the visual effects of Stranger Things season 5](https://www.ilm.com/?p=43045)
- [Mandelbulbs, mutations and motion capture: the visual effects of *Annihilation* (VFX Blog)](https://vfxblog.com/2018/03/12/mandelbulbs-mutations-and-motion-capture-the-visual-effects-of-annihilation)
- [DNEG: alien films, Annihilation's fractal Shimmer](https://dneg.com/dnegaliens)
- [Annihilation cinematography, Rob Hardy (British Cinematographer)](https://britishcinematographer.co.uk/?p=10129)
