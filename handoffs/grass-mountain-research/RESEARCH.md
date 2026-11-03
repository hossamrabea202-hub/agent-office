# #440 Mountain grass fields: how AAA environment artists set them up (i5 / adjustedfilm, 2026-11-03)

Owner (Alien, 2026-11-02): "ask TGA to perform a deep research on how AAA environment artists set up grass fields in
mountain areas" (TGA never got to it; i5 took it on 11-03). Owner: "we are going to polish our scene using the info".
Research only: nothing in the game changes until the owner OKs the plan at the end.

## 1. What a real mountain grassland looks like (the target)
- **Bands by altitude, not one carpet.** Forest gives way to tawny grassland, then to rock, and the change can be
  abrupt (a sharp treeline) or gradual, with tongues of grassland running down into scrub and spurs of scrub running
  up. [Te Ara, alpine plants](https://teara.govt.nz/en/alpine-plants/page-1)
- **Tall tussock low, dwarf tussock high.** In the Humboldt Mountains snow tussock grassland runs continuously from about
  1,100 to 1,530 m, then gives way in snow pockets to a high-alpine grassland of dwarf tussocks.
  [NZ Journal of Ecology, Humboldt Mountains](https://newzealandecology.org/nzje/2539)
- **Above the tussock line the tussock form is replaced by dwarf cushion plants** (Körner's zonation: treeline,
  shrub line, tussock line). [Otago altitudinal study](https://ourarchive.otago.ac.nz/esploro/outputs/journalArticle/Altitudinal-patterns-of-vegetation-flora-life/9926517804901891)
- **A hard treeline at the subalpine edge** (Victorian Alps: woodland ends abruptly, no trees above ~1800 m, too exposed).
  [Victorian alpine resorts, vegetation](https://www.alpineresorts.vic.gov.au/the-resorts/environment/education-resources/vegetation-communities-and-native-flora)
- What this means on screen:
  1. grass gets **shorter, sparser and clumpier** with altitude and wind exposure; ridges are bare, hollows are lush;
  2. **slope kills grass**: on steep faces it hangs on only in ledges and cracks; scree fans at the foot of cliffs are
     bare stone with a few tufts at their edges;
  3. **colour is never one green**: tawny / straw tussock, olive-grey sedge, greener only in wet hollows and along water
     and paths; dead blades at the base of every tuft;
  4. **clumps, not lawn**: tussock grasses grow in discrete clumps with soil and stones showing between them.

## 2. How AAA games build it
- **Ghost of Tsushima** (Sucker Punch, GDC 2021): fully procedural grass fields generated on the GPU, a global wind field
  that both grass and particles read, gusts and vortices modelled cheaply ("vorticles") rather than accurately.
  [GDC: Procedural Grass in Ghost of Tsushima](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass),
  [GDC: Blowing from the West](https://gdcvault.com/play/1027124/Blowing-from-the-West-Simulating),
  [Game Developer on the wind talk](https://gamedeveloper.com/design/using-vorticles-to-simulate-wind-in-i-ghost-of-tsushima-i-)
  Lessons: grass density and height are driven by **data maps** (not painted by hand); one shared wind drives everything
  so the field moves as one; at distance the field is carried by the **terrain material colour**, not by blades.
- **Common UE5 split** (alpine environment packs and tutorials): **Landscape Grass Types** for small dense stuff (grass,
  pebbles, small stones), **PCG** for trees, rocks and larger clumps, filtered by slope and height.
  [PCG basics, UE 5.4+](https://medium.com/@sarah.hyperdense/pcg-basics-your-first-procedural-scatter-system-in-ue5-fab626e1d6f0),
  [Alpine Lakeside Village, World Partition + PCG](https://giftkerdlapee.artstation.com/projects/vb6zvD)
- **Landscape grass types fill a layer uniformly**: altitude and slope limits have to come from the material's grass
  output weights (height / slope masks), not from the grass type itself. [UE forum](https://forums.unrealengine.com/t/applying-landscape-grass-outputs-to-specific-altitudes-world-height-and-slope-angles/133473)
- **Clumping** is not built in: make it with a noise-driven density mask (PCG density noise, or a low-frequency noise
  multiplied into the grass output weight). Nanite grass "mats" (50 x 50 cm patches of varied height and density) are
  another way to get variety without millions of single blades. [AstraVorex grass pack](https://forums.unrealengine.com/t/astravorex-realistic-grass-pack/2747344)

## 3. Recipe for our valley (UE 5.8, i9 = RTX laptop T1000, i5 = 2 GB MX570)
1. **Inventory first** (read-only): which grass the castle valley uses today (landscape grass types on
   `MI_MountainBackdrop_Near` or PCG / BP scatter: the 11-03 audit found no InstancedFoliageActor), densities, cull
   distances, shadow settings, and the frame cost on the Master.
2. **Three grass bands from data**, in the landscape material's grass outputs:
   - *valley floor + castle surroundings*: mixed meadow grass 25-45 cm, densest, greener in hollows and along paths;
   - *mid slopes*: tussock clumps 20-35 cm, straw / olive colours, soil and stones between clumps;
   - *high slopes / ridges*: dwarf tufts 5-12 cm, sparse, mostly rock and cushions; no grass above the band.
   Weights = height band x (1 - slope mask, grass gone above ~35 deg) x low-frequency noise (clumping, 8-20 m cells)
   x wetness (more and greener in hollows, using the existing #410 wet MPC when it rains).
3. **Transitions**: scree / rock fans at cliff feet (PCG rocks + pebble grass type, no tall grass), a 1-3 m soft edge
   where grass meets rock, tufts along cracks on steep faces.
4. **Colour**: per-instance random hue/value (+-8 %), straw tips and dead blades at the base (no single olive green: the
   owner flagged olive in the 11-02 audit); albedo in the calibrated range of the realism KB.
5. **Wind**: one global wind direction (WindDirectionalSource, 5 exist in the level) driving grass WPO and particles, a
   slow gust wave across the field; amplitude grows with blade height.
6. **Performance**: shadows on near grass only, cull 40-80 m by band, distance carried by the terrain material colour;
   Nanite grass mats only if the T1000 profile allows; measure before/after on the Master (i9's perf pass baseline).
7. **Lookdev at locked exposure**, before/after from the gameplay camera and from the wall walk, then the owner's OK.

## 4. Who does what (proposal)
- i5: step 1 inventory (read-only) + the grass-output mask graph design as a new material instance / material function.
- i9: frame-cost check on the Master and the swap after the owner's OK.
