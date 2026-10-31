# #296 Cave realism: what top studios, film and series crews do (research before any material)

By `adjustedfilm (Claude)`, 2026-10-31, at the owner's request: *"before you set materials … study top artists and projects
and netflix and others how do they make it look realistic"*. This builds on the office knowledge base
(`handoffs/knowledge/INDUSTRY_SECRETS.md` §1.3 wetness / moss, `research_notes/environment_vegetation.md`); it adds only
what is new for caves and mines. **No material is built until this is applied.** The spec is in §3.

## 1. What the sources say

### Film and streaming: real sets, real light, a few light sources

- **The Descent (2005).** The caves were sets at Pinewood, not a real cave.
  - **Light came only from what the characters carry:** headlamps, flashlights, glow sticks, flares, firebrands.
  - The red of the flares and the green of the glow sticks are the colour story.
  - The cinematographer found red flares hard to expose. They are noisy, and they burn out, so the light level jumps.
  - One cave set was re-dressed, rotated and re-lit to feel like a large network.
  - Sources: [ASC, "The Descent: Creepy Crawlers"](https://theasc.com/articles/the-descent-creepy-crawlers),
    [Wikipedia](https://en.wikipedia.org/wiki/The_Descent).
- **Stranger Things (Netflix), the Upside Down tunnels.**
  - **Season 2:** built practically, thousands of square feet of tunnels. VFX only extended the far view "to make it
    feel a little realer".
  - **Seasons 4–5:** still practical near the cast. In season 5, every CG element "had to earn its place by being
    grounded in something real on set".
  - **Dust and smoke** simulations sell the air.
  - Sources: [TV Guide on S2](https://www.tvguide.com/news/stranger-things-2-upside-down-how-they-made),
    [/Film on S4](https://slashfilm.com/919170/how-stranger-things-season-4-went-running-up-that-hill-with-a-mix-of-vfx-and-real-sets),
    [Art of VFX, S5](https://www.artofvfx.com/stranger-things-season-5-betsy-paterson-production-vfx-supervisor/),
    [VFX Voice, S5](https://vfxvoice.com/stranger-things-season-5-turns-the-upside-down-right-side-up/).
  - **For us:** what's next to the camera must be real geometry (rock, timber, rails, rubble), not a texture painted on
    a tube. Air needs dust or haze in the lamp beams.

### Games

- **Indiana Jones and the Great Circle (MachineGames).**
  - Artists rebuilt the cave tunnels from the greybox: geometry, materials and world-building together.
  - The lighting copies the films' Douglas Slocombe look: heavy contrast, moody, candle and sun as the sources.
  - There's a GDC talk on ageing surfaces ("Aged by Adventure"); the video is behind a login, so it wasn't watched.
  - Sources: [George McLay, cave system](https://georgemclay.artstation.com/projects/dyPOgw),
    [Aftermath on the cinematography](https://aftermath.site/indiana-jones-great-circle-douglas-slocombe-cinematography-cutscenes),
    [GDC Vault](https://gdcvault.com/play/1036059/Aged-by-Adventure-CraftingtheTime-Worn).
- **The Last of Us Part I (Naughty Dog), rock assets.**
  - Built in Maya, ZBrush and Substance Designer by two principal environment artists.
  - Their breakdowns show separate layers for a second rock, grunge, moss and wetness, plus runny wet eroded banks.
  - Sources: [80.lv](https://80.lv/articles/a-closer-look-at-rock-assets-made-for-tlou-part-i/),
    [80.lv erosion](https://80.lv/articles/breakdown-eroding-terrain-in-the-last-of-us-part-i). The ArtStation
    breakdown pages refused automated access.
  - The office already has Naughty Dog's wetness formula (KB §1.3): `lerp(base, base², porosity × wetness)`.
- **"Rainforest Cavern", UE (Jake Dunlop on 80.lv).**
  - The base colour is deliberately **low contrast**, and albedos are kept close together so assets blend.
  - **Moss** goes on with vertex colour → height lerp.
  - **Rain streaks and wetness** use a simple vertex-colour lerp.
  - Mud fills the cracks with an inverted-AO mask, and a flatten-normal of 0.95 makes water read flat.
  - **Sharper rocks beat rounded scans:** rounded rocks read as "too smooth".
  - Distance-field AO lights the cave interior. Fog is tinted, with a slightly blue volumetric fog.
  - Source: [80.lv](https://80.lv/articles/rainforest-cavern-tips-for-realistic-scenes). Other cave builds:
    [Creation of 3D caves](https://80.lv/articles/creation-of-3d-caves-for-games) (dirt in cavities and on damaged
    edges, depth-fade wet edge on water).
- **World-aligned (triplanar) mapping** is the standard fix for stretched rock UVs, and the normals must be transformed
  properly. Source: [80.lv triplanar deep dive](https://80.lv/articles/ue5-triplanar-deep-dive-from-worldalignedtexture-to-high-quality-normals-part-1/).

### Real caves and real medieval mines

- **Cave colour.**
  - Pure calcite (travertine) is white.
  - Yellow to brown comes from impurities and organic stains, not always iron.
  - Orange-red is iron oxide.
  - Grey to black is manganese oxide, dirt, guano or **soot**.
  - Flowstone shows **bands** of differing impurity.
  - Sources: [NSS Bulletin, White 1981](https://legacy.caves.org/pub/journal/PDF/V43/v43n1-White.htm),
    [NM Bureau of Mines Bulletin 117](https://www.nps.gov/parkhistory/online_books/geology/publications/state/nm/1987-117/sec4-2.htm).
- **Medieval mines were fire-set** (Agricola, *De Re Metallica*): a fire against the face, then cool and pry.
  - That leaves **rounded, smooth tunnel walls** with **spalled** flakes, not the sharp pick-faceted rock of later
    mines. Each fire gained only about 4 cm.
  - Lamp **soot** on walls and roofs, and tally scratches, were found in old mines.
  - Sources: [Fire-setting](https://en.wikipedia.org/wiki/Fire-setting),
    [Alderley Edge medieval mining](https://derbyscc.org.uk/alderley/mining_medieval.php),
    [Harrow Hill flint mine](https://www.themodernantiquarian.com/post/12403/misc/harrow_hill.html).

## 2. The rules this gives us (cave + mine)

1. **Geometry first, texture second.** Near the camera, real rock forms, ledges, rubble and timber. A texture can't fake
   depth on a tube. (Stranger Things, Indiana Jones; TGA's #309 kit builds this.)
2. **Sharp, fractured rock in the natural cave; rounded, smooth, spalled walls in the mine** (fire-setting). Two different
   materials tell the player "nature" and "people dug this".
3. **Low-contrast base colour, close albedos.** The realism comes from light and wetness, not a busy texture.
   - Dark wet rock is about 30–60 sRGB; never below 30 (KB rule).
   - Dry rock near the entrance is about 70–120 sRGB.
4. **Wetness has a cause, in physical order:**
   - darkening is base² by porosity (Naughty Dog);
   - glossier first where water runs: **vertical drip streaks** under cracks and ceilings (a world-Z gradient plus a
     streak mask);
   - wetter toward the floor, with **flat puddles** in low spots (flatten normal about 0.95, roughness 0.05–0.1);
   - drier and dustier near the entrance where air moves.
   - The shine goes before the darkening as things dry (KB).
5. **Stains where they come from:**
   - **soot** above torch and lamp niches (black, rough, mine only);
   - **iron-orange runs** under seams;
   - **pale calcite bloom** where water drips;
   - **mud and grit** in cavities (inverted AO);
   - moss only at the entrance where daylight reaches; none deep inside.
6. **World-aligned mapping** on all cave rock, so nothing stretches (the #228 lesson too). Use triplanar normals done right.
7. **Light like The Descent and Indiana Jones:**
   - only real sources: torches (KB: real point light behind every flame, warm Kelvin, flicker), lanterns in the mine,
     daylight at the mouth;
   - true black is allowed in caves (KB §2);
   - a little haze or dust in the beams;
   - distance-field AO / Lumen with Scene Detail raised to stop leaks (KB lighting notes).
8. **Judge in lookdev** (locked exposure, grey ball), then in the cave with a before/after for the owner. No live material
   is swapped without the owner's OK.

## 3. Material spec for #296 (built only after the cave dump #308 shows what the cave is made of)

**`M_CaveRock`** (new master; nothing live is edited) with instances **`MI_CaveRock_Natural`** and **`MI_CaveRock_Mine`**:

**Base**
- World-aligned (triplanar) rock colour, normal and ORM, from the textures the cave already uses, or licensed ones on the
  Master's PC.
- Plus a macro-variation noise at 3–5 m, so there are no repeats.
- Composite Texture on the ORM (KB §1.3) against sparkle.

**Wetness**
- `wet = saturate(floorGrad + dripStreaks + puddleMask)`:
  - `floorGrad`: wetter toward the floor;
  - `dripStreaks`: world-Z streak noise under overhangs;
  - `puddleMask`: up-facing and low.
- Colour: `lerp(base, base², porosity × wet)`, with porosity 0.5 for limestone.
- Roughness: `lerp(r, r × 0.5, wet)`, and 0.06 in puddles. Puddle normal flattened to 0.95.

**Stains** (parameters, all 0 by default)
- `Soot`: a world-position sphere mask list for torch spots, black 25 sRGB, rough 0.9.
- `IronRuns`: an orange 120/70/40 sRGB streak.
- `CalciteBloom`: pale 200 sRGB, rough 0.7.
- `MossAtMouth`: an up-facing mask × distance to the entrance.

**Mine instance**
- Smoother macro normal (rounded, fire-set walls).
- More soot.
- Drier walls with wet floors.

**Checks**
- `pbr_check.py` on any new texture.
- Lookdev before/after screenshots to the owner.
- Swap only on the owner's OK, by script, with a backup (same flow as the #228 wall-top fix).
