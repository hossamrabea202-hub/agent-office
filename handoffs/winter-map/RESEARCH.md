# #390 WinterKeep: how real winter is built (research)

By `adjustedfilm (Claude)`, 2026-11-01. Rule M: study first. Goal: real winter, not a Christmas card. Each finding says
what we do with it. [UNVERIFIED] = one source or my inference; test it in lookdev.

## 1. What the top studios do

| Studio / game | What they did | What we take |
|---|---|---|
| **Santa Monica, God of War Ragnarök** | Rewrote their snow displacement for GDC 2023 ("Reinventing the Wheel for Snow Rendering", Paolo Surricchio). The driver was **scale and ease of use**: snow in many more places across a much bigger world. The old system was shared with water ripples. [GDC Vault](https://gdcvault.com/play/1028844/Advanced-Graphics-Summit-Reinventing-the), [80.lv](https://80.lv/articles/santa-monica-s-senior-programmer-on-how-god-of-war-ragnar-k-s-snow-system-was-made/) | Tracks must be **cheap enough to run on the whole map**, not a hero patch. |
| **Naughty Dog, The Last of Us Part II (Jackson)** | Snow tracks are **parallax occlusion** (a pixel-shader depth trick), not real geometry. It reads best against a back light. Credits: Steven Tang (deformation shader), Joakim Stigsson (snow surface). [GamingBolt](https://gamingbolt.com/the-last-of-us-part-2-graphics-analysis-naughty-dog-continues-to-push-boundaries), [Stigsson](https://joakimstigsson.artstation.com/projects/18neO2), [Trevelyan: snow on vehicles](https://trevelyan.artstation.com/projects/ELL4gv) | **Our track method (§4):** a mask plus parallax, with no mesh deformation. Snow on props is a material layer on top surfaces. |
| **Rockstar, Red Dead Redemption 2 (Colter, Grizzlies)** | No official talk exists. Developers who rebuilt it read it as a **depth or trail render target that follows the player**, blurred and used to push the snow down. Deep troughs form as characters wade. [gamedev.net](https://gamedev.net/forums/topic/700247-snow-physics-in-red-dead-redemption-2/), [rebuild write-up](https://pappaniels.github.io/posts/2025/01/23/Snow-Deformation.html), [GamingBolt](https://gamingbolt.com/red-dead-redemption-2-tech-analysis-animations-physics-post-processing-effects-weather-systems-and-more) | A **player-centred render target** is the industry pattern. We use it as a mask, not as WPO (§4). |
| **11 bit, Frostpunk** | The art carries the design's bleakness. Snow covered every roof, so **roofs were never modelled**. 1886 reworks buildings to look "more weathered, icier, more brittle". [PlayStation Blog](https://blog.playstation.com/?p=350772), [altchar](https://www.altchar.com/game-news/frostpunk-1886-developer-update-reveals-big-visual-and-gameplay-upgrades-aak8s7b6T34O) | Mood comes from restraint: a grey-blue palette with one warm light. Snow load **replaces** roof detail. Farmsteads are half buried, with only their ridges and chimneys showing. |
| **Warhorse, Kingdom Come: Deliverance 2** | No winter content to study. Their method still applies: real terrain logic and a managed forest (INDUSTRY_SECRETS §4.3). | The geology comes first. The forest is managed, with felled clearings near farms and the castle. |

## 2. Nature: what the eye checks

**Snow colour.** Typical snow albedo is about 0.80, fresh snow is above 0.90 (whiteout), and old or broken snow is lower.
Melting snow is much lower. Albedo rises at grazing sun angles because of forward scattering.
[Journal of Glaciology](https://www.cambridge.org/core/product/C30D6E409BD60478FA65FD7131F55A33/core-reader),
[Antarctic albedo](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/BA15776866760EF2AEBC7C5657F79297/S0022143000009011a.pdf/on-the-albedo-of-snow-in-antarctica-a-contribution-to-iago.pdf).

- **Our values (linear):**
  - fresh snow 0.80–0.86
  - wind-packed snow 0.66–0.72
  - trampled or dirty snow 0.36–0.45
  - road slush 0.30
  - **never 1.0**
- Snow is ice grains, so light travels inside it. Use **subsurface scattering with a blue-biased radius** (blue goes
  deepest). Sparkle is a tiny high-frequency spec lobe and only reads at grazing angles [UNVERIFIED as numbers; tune in
  lookdev].

**Wind drifts.**
- Behind an obstacle, a drift builds as a ridge, highest near the obstacle, with a triangular face toward it. Its size
  depends on wind speed, the obstacle's shape and the snow texture.
- Lee slopes steeper than about 25° grow **cornices** that get bigger with each storm.
- **Sastrugi** (sharp wind-eroded ridges) are on the **windward**, scoured side.

Sources: [Hokkaido Univ.](https://eprints.lib.hokudai.ac.jp/repo/huscap/all/20365/2_p1119-1136.pdf),
[Annals of Glaciology](https://www.cambridge.org/core/journals/annals-of-glaciology/article/distribution-of-snow-drifts-on-ridge-slopes-measurements-and-theoretical-approximations/36FCDF2DA3CEDD8A782ACC7E91B7727D),
[avalanche.org](https://avalanche.org/?p=2988).

- **We use** the Winstral **Sx** shelter index: the maximum upwind horizon angle. Sheltered means deposit, exposed means
  scour. Wind comes from 315° (north-west).
- Windward faces are scoured to dark rock. Lee faces carry drifts up to about 3 m.
- Cornices go on the lee crest of the west ridge. Sastrugi go into the normal map of wind-packed snow.

**Lake ice.**
- Clear "black" ice is transparent, so you see the dark deep water through it.
- **Trapped bubbles and cracks scatter light, so they read white.**
- Slow freezing pushes the gas out, giving clear ice. Bubbles show up from the second cold night on.
- Cracks show the ice thickness from the side.

Sources: [UW weather guys](https://wxguys.ssec.wisc.edu/2019/02/25/ice), [NHPR](https://www.nhpr.org/post/ask-sam-why-some-ice-black-and-some-ice-white),
[Nordic skaters](https://nordicskaters.squarespace.com/black-ice).

- **We use:**
  - base albedo about 0.012–0.024 (dark blue-black)
  - roughness about 0.05, Specular 0.224 for ice ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine))
  - Voronoi crack lines that are white **and** rough
  - a white frosted rim of wind-blown snow at the shore and on the pressure ridges
  - gloss only where meltwater sits (the wetness rule)

**Rime and hoar frost.**
- **Rime grows INTO the wind**: supercooled fog droplets freeze on the windward side, so the feathers point upwind.
- Hoar frost is vapour that freezes directly into crystals. It forms on any cold surface on calm, clear nights.

Sources: [The Weather Network](https://www.theweathernetwork.com/en/news/weather/forecasts/warm-winds-finally-end-albertas-epic-rime-ice-event-hoar-frost),
[AMS glossary](https://glossary.ametsoc.org/wiki/Ice_feathers).

- **We use** the rime mask = world normal · (−wind direction), so rime sits on the NW faces of rock, walls and trees.
  That is the **opposite** side from the drifts. This pairing is the realism tell.

## 3. Engine facts (UE 5.3)

- **Landscape size.** 2017 × 2017 = 16 × 16 components, 63 quads per section, 2 × 2 sections, so 1 m per vertex at
  XY scale 100. The heightmap spans −256..+256 × ZScale/100 m. Our land is 3.7–378 m, so we use **Z scale 78.125
  with Location Z = 20200 cm**, and grey maps back to true metres.
  Sources: [Epic Landscape technical guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine),
  [forum on Z scale](https://forums.unrealengine.com/t/what-is-unreal-unit-height-translation-after-importing-16bit-heightmap-to-level/157062).
- **Interactive snow options in UE5:**
  - a render target drawn around the player and sampled in the landscape material
  - a Runtime Virtual Texture with a Virtual Heightfield Mesh
  - Nanite tessellation (experimental in 5.3)
  
  Known problems ([Epic forum](https://forums.unrealengine.com/t/ue5-issues-in-rendering-trails-on-landscape-using-runtimevirtualtexture/724442),
  [forum 2](https://forums.unrealengine.com/t/ue5-ideas-for-rendering-realstic-snow/730876)):
  - Writing trails into an RVT output lags.
  - A Virtual Heightfield Mesh has **no collision**.
  - Render targets broke in 5.1 for some users.

## 4. Decision: footprints and tracks

**Decision:** a **player-centred render-target trail mask** (2048², 64 m window, rolling with the player), sampled in
the landscape material. It drives:

1. a packed-snow layer: albedo 0.66, smoother roughness, plus a rim of pushed-up fresh snow along the edge;
2. **parallax occlusion** depth, up to 12 cm (TLOU2's approach);
3. a normal from the mask's gradient.

Older trails fade over about 3 minutes, and the weather re-fills them faster in a blizzard. Zombies and soldiers write to
it with one material draw each per frame, all in one Blueprint. Characters' **footprint decals** are added only for hero
moments (gate and courtyard).

**Why:**
- It is cheap (one 2048 RT and one draw pass).
- It has no collision problems.
- It runs on the whole map (the God of War lesson).
- It needs nothing experimental: no Nanite tessellation, no VHM, no RVT write lag.
- WPO on landscape would need dense LOD 0 everywhere, and `MP_WORLD_POSITION_OFFSET` is not scriptable in our 5.3 Python
  anyway.

## 5. What this means for the map (feeds DESIGN.md)

1. The geology and the wind decide where the snow is, and the snow decides how the map plays. Drift fields are on the lee
   (SE) side of the castle rise, so they slow zombies coming from the realm in the east.
2. Use one wind direction for everything: drifts, rime, blowing-snow VFX, tree lean and smoke. This is INDUSTRY_SECRETS
   rule 10.
3. Mostly overcast, about 6500 K, with a 2:1 key-to-shade ratio. The low sun is a rare reward (long blue shadows).
   Night is grey-blue on purpose (Purkinje), with torches at 1800 K as the only warm light.
4. The scariest contrast is black wet ground and steam inside a white world. It is the only place where the snow is
   gone.
