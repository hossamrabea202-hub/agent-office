# #337 Blood and dismemberment: how top games, VFX houses and series make it look real (research before any rebuild)

By `adjustedfilm (Claude)`, 2026-10-31, at the owner's request: zombies should lose body parts from sword slashes,
**but not too gory**, and the current blood Niagara looks **cartoonish**. This builds on the office knowledge base
(`handoffs/knowledge/INDUSTRY_SECRETS.md` §0 rule 9, §3.1 skin, §3.5 gore without C++, §4.1 Niagara cost, §4.2 decals).
It adds only what is new for blood and severing. **Nothing is built until this is applied.** The spec is in §5.

Items marked **[UNVERIFIED]** are my estimates or single-source claims. Test them in lookdev (locked exposure, grey ball)
before trusting them, then log the result in `KNOWLEDGE_LOG.md`.

---

## 1. What the sources say

### Games

- **Ghost of Tsushima (Sucker Punch).**
  - "Every attack creates a particle effect with thousands of blood droplets and blood strings." Droplets land on
    nearby geometry. In water they become clouds that drift with the current.
  - Blood is also **added to the character mesh** near the strike, and a bit beyond it, so the body shows the wound
    state. The same system runs in cutscenes.
  - The VFX developer: the blood is **"deferred ribbons and deferred billboards, no meshes"**. Deferred means lit like
    opaque geometry (correct specular, shadows, motion blur), not glowing translucent sprites. Normals are made at
    runtime from the eroding edge of the sprite, so the light follows the shape as it breaks up.
  - Blood comes from **two places**: the wound and **the sword as it travels** (cast-off). There is a sheathe flick that
    throws blood off the blade.
  - The VFX team was two people for most of the game. Their target for duels was "stylish beauty in motion".
  - Sources: [PlayStation Blog](https://blog.playstation.com/?p=345372),
    [RealtimeVFX thread with the developer](https://realtimevfx.com/t/vfx-of-ghost-of-tsushima-a-recent-blog/15815),
    [RealtimeVFX: how AAA do blood](https://realtimevfx.com/t/how-do-aaa-games-do-blood-games-like-ghost-of-tsushima-do-you-think-its-a-flipbook-or-3d/30348),
    [CogConnected on the flick](https://cogconnected.com/2020/05/ghost-tsushima-flick/).
- **Dead Island 2, FLESH (Dambuster).**
  - Every zombie type is set up the same way, in layers: skin, fat, muscle, bone, organs. Repeated sword hits cut skin,
    then muscle, then reach bone. Damage is procedural and placed where the weapon hits.
  - Weapons differ: a dagger cannot deliver what a sword does.
  - On tone, the creative director says gore should pull players in while causing **slight** revulsion; a few
    impossible "wow" moments are what people remember. Some gore was cut for being too extreme.
  - Sources: [PC Gamer](https://www.pcgamer.com/dead-island-2-devs-detail-its-gruesome-procedural-violence-modelling-tech),
    [The Loadout](https://www.theloadout.com/dead-island-2/realistic-zombies-gore-system),
    [Wccftech](https://wccftech.com/dead-island-2-shows-off-its-impressive-procedural-dismemberment-in-new-gameplay-footage),
    [AUTOMATON interview (JP)](https://automaton-media.com/articles/interviewsjp/20240524-294765/).
- **Dying Light 2, "Gut Feeling" update (Techland).** The clearest technical description we found:
  - **Hierarchical cutting zones** per enemy archetype (press reports 3 cut points per limb).
  - The cut part of the body is **hidden with a shader**, not removed from the mesh.
  - The cut face is covered with a **patch (cap) mesh**.
  - The cut-off part is **spawned as its own mesh** with VFX and sound.
  - Severing can happen on almost any hit reaction or during ragdoll, so they did not need ~1,000 extra animations.
  - On tone: they **backed off** effects that felt "inconsistent with the world", and hit strength that felt too much;
    they aimed for "the right balance instead of going to extremes".
  - Sources: [3DVF interview](https://3dvf.com/en/redaction/dying-light-2-stay-human-our-interview-with-techland-about-the-gut-feeling-update-focused-on-combat-animations-and-physics/),
    [Dying Light news](https://dyinglightgame.com/news/gut-feeling-update),
    [GameSpot](https://gamespot.com/articles/just-as-dead-island-2-launches-dying-light-2-update-mimics-its-marquee-feature/1100-6513434/).
- **The Callisto Protocol (Striking Distance, UE 4.27).** Layers of flesh, muscle and skeleton, used as a "diegetic
  health bar". They rebuilt their severing on top of UE's own systems. Proof that this is doable in Unreal.
  Sources: [GamesRadar](https://www.gamesradar.com/yes-the-callisto-protocol-is-way-gorier-than-dead-space),
  [GamesRadar on "how much is too much"](https://www.gamesradar.com/the-callisto-protocol-is-stunning-but-how-much-gore-is-too-much-gore).
- **Resident Evil 2 remake (Capcom).** The director's word is **"wet"**: wet gore glistens and reads as disease, which
  triggers the instinct to shy away. Layered damage from knife slashes. Wet look depends on correct light, not on more
  blood. Sources: [Complex interview](https://www.complex.com/life/2019/01/resident-evil-2-remake-gore-interview),
  [Syfy Wire](https://www.syfy.com/syfywire/resident-evil-2-remake-horror-gore-zombie-evolution).
- **The Last of Us Part II (Naughty Dog).** Blood pools and splatter were their own asset work (textures, materials,
  **timing and placement**) per surface: snow and water behave differently. Players noticed the **animated blood trails
  running down the body from wounds**. Sources: [Kirsten England, blood in snow and water (via FX bookmarks)](https://raindrop.io/simon81/fx-3209787/embed/sort=-sort&perpage=30&page=0&search=%22%23last+of+us+2%22),
  [Steam discussion on wound trails](https://steamcommunity.com/app/2531310/discussions/0/591767569582577510/?ctp=3),
  [Game Informer interview](https://gameinformer.com/preview/2020/06/01/the-last-of-us-part-ii-interview-adding-depth-staying-grounded-and-the-cost-of).
- **Mortal Kombat 11 (NetherRealm).** Fatality blood is **Houdini fluid sims baked to Alembic caches** and played back by a
  material (World Position Offset). 55-frame sims, 150 MB memory cap for the whole game, six months for 1 engineer + 2
  artists. They did it because sprite particles could not hold up in close slow-motion. **For us:** too expensive; we
  are not a close-up slow-motion game. Source: [SIGGRAPH blog](https://blog.siggraph.org/2020/03/creating-the-killer-content-in-mortal-kombat-11.html/),
  [SIGGRAPH 2019 talk](https://history.siggraph.org/learning/mortal-kombat-11-high-fidelity-cached-simulations-in-real-time-by-nadro-battaglia-and-voorhees).
- **Chivalry 2 (Torn Banner, UE4) and For Honor (Ubisoft).** Medieval melee with decapitation and limb loss, mostly on
  kills and executions. Both ship a **gore / dismemberment toggle** ("some blood but no dismemberment").
  Sources: [Wikipedia Chivalry 2](https://en.wikipedia.org/wiki/Chivalry_2), [ESRB Chivalry 2](https://www.esrb.org/ratings/37665),
  [Game Informer on For Honor](https://gameinformer.com/games/for_honor/b/playstation4/archive/2016/06/16/five-things-we-learned-while-slaughtering-our-way-through-for-honor).
- **Kingdom Come: Deliverance 2 (Warhorse).** The realism benchmark has **blood but no dismemberment**. Henry ends fights
  soaked in blood. The usual reasons given: armour makes severing rare, and their clothing layers make cutting hard
  [UNVERIFIED, forum recollection]. **For us:** blood on clothes and weapons sells realism even with no severing.
  Sources: [Bullet Points Monthly](https://bulletpointsmonthly.com/2025/03/06/the-past-covered-with-blood-kingdom-come-deliverance-ii),
  [KCD forum](https://forum.kingdomcomerpg.com/t/blood-and-gore-content/30227).

### Film and streaming

- **The Boys (Prime Video).** Blood sits under a heavy, desaturated grade that **leans toward black**. Specular is not a
  fixed look: it changes as the blood moves and changes shape. They tuned the amount up and down to find "a cool
  balance of legibility and realism", and **reduced** gore in places to keep the world believable. Studied
  slow-motion (Phantom, 500–1,000 fps) reference. Source: [VFX Voice](https://vfxvoice.com/balancing-blood-and-believability-in-superhero-twister-the-boys/).
- **Shōgun (FX / Hulu / Disney+).** Practical prosthetic plus **CG blood at the moment of impact** and for trails. A CG
  splatter on a white shoji screen was shaped to read like calligraphy. Goal: "invisible VFX".
  Source: [/Film](https://slashfilm.com/1604901/shogun-arrows-blood-visual-effects).
- **Ready or Not 2 (RISE / RSVFX).** Practical blood on set plus several passes of Houdini blood sims, rendered in Karma.
  The hard part: making all elements read as **"one cohesive event"**. Blood **sits in the space** through the room's
  light falloff, dust and flies. Source: [RSVFX](https://www.rsvfx.com/?p=3580).
- **General VFX-supervisor rule:** the strongest results start practical and use CG to sweeten. Every blood element must be
  **lit by the same light as the rest of the frame**. Sources: [Morbidly Beautiful](https://morbidlybeautiful.com/?p=30104),
  [Art of VFX on Ninja Assassin](https://www.artofvfx.com/?p=185).

### Science (real blood)

- **Measured optics** ([physicallybased.info JSON](https://raw.githubusercontent.com/AntonPalmqvist/physically-based-api/main/deploy/v2/materials.json),
  which cites Bosschaart 2014, Wikipedia Hemorheology and others):
  - IOR **1.35** → F0 ≈ 0.022 → **UE Specular ≈ 0.28** (not 0.5).
  - Density **1060 kg/m³**. Viscosity **~4 mPa·s** (about 4× water). Surface tension **56 mN/m**.
  - Blood is a **strongly absorbing, forward-scattering liquid**. Its *transmission* colour (thin layer) is
    oxygenated linear (0.644, 0.003, 0.005) ≈ sRGB (210, 10, 16), deoxygenated linear (0.415, 0, 0) ≈ sRGB (172, 0, 0).
    That bright red only shows in **thin films and droplet edges**. Thick blood (a pool, a soaked cloth) absorbs nearly
    everything and looks **dark maroon to almost black, with a sharp white highlight**.
  - Blood is **shear-thinning**: at rest it is up to ~10× thicker than when flowing. It strings out and sticks, then
    snaps ([Hemorheology](https://en.wikipedia.org/wiki/Hemorheology)).
- **Ageing:** red oxy-haemoglobin oxidises to met-haemoglobin and hemichrome. Stains go **bright red → dark red → brown**
  over hours to days, faster in warmth and dry air ([Bremmer 2011, PLoS ONE](https://doaj.org/article/314612bed51a4ab18f11c8a14612262b),
  [Hanson & Ballantyne 2010](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2942901/)). A zombie's blood is dead blood:
  no oxygen, no pump, partly clotted. So it is **darker and browner** for a physical reason, not only for style.
- **Bloodstain pattern analysis (forensics):**
  - mist (gunshot, high velocity): < 1 mm;
  - **medium velocity (blows, stabs, slashes): 1–4 mm**;
  - drips and passive drops: > 4 mm; a standard 50 µL drop is ~4.6 mm and falls at ~7.5 m/s terminal speed;
  - **cast-off**: a swung blade throws a **line** of drops along the swing arc.
  - Sources: [Forensic science course notes](https://dmccreary.github.io/forensic-science/chapters/07-bloodstain-pattern-analysis/),
    [HowStuffWorks](https://science.howstuffworks.com/bloodstain-pattern-analysis2.htm),
    [crime-scene-investigator.net](https://www.crime-scene-investigator.net/quantitative-analysis-of-high-velocity-bloodstain-patterns.html),
    [MacDonell table via slides](https://www.slideshare.net/Alyssa10/bloodspatter).
  - Dried stains have a **darker rim** (the coffee-ring effect) [standard physics; not checked against a forensic source].

---

## 2. Blood look: rules

### 2.1 Why our blood reads cartoonish (checklist)

| Tell | Why it reads fake | Fix |
|---|---|---|
| Too bright, saturated red | Real thick blood is dark maroon; bright red is only thin film | Dark base colour, bright only at thin edges (§2.2) |
| Glowing / unlit | Emissive or unlit sprites ignore the torch and moon | Lit material, Default Lit masked ("deferred"), no emissive ever |
| Uniform round blobs | Real spatter is many sizes, mostly tiny, a few big | Size from a power curve: many 2–4 mm, few 8–12 mm |
| Too much volume | A slash leaks a little; a fountain reads as comedy | ≤ 60 droplets, short burst, zombie blood oozes |
| No motion blur | Sprites stay sharp in flight; real drops smear on camera | Velocity-aligned stretch + masked material writes velocity |
| No wet specular | Real blood has one sharp white highlight | Roughness 0.05–0.15, fake sphere normal on droplets |
| Same splat every time | Repeats are spotted instantly | 6–8 decal variants, random rotation and size |
| Floats or vanishes | Blood must land and stay | Collision → decal; decals live 20–40 s then dry and fade |
| No strands | Blood is viscous; it strings off the blade | 2–4 short ribbons per hit |
| Mist like smoke | Big soft clouds read as red smoke | Mist is tiny, fast, short (0.3 s), low opacity |

### 2.2 Colour table (lookdev values)

Measured transmission values are from physicallybased.info. **Opaque (pooled / surface) values are my calibration
estimates [UNVERIFIED]** from the optics above (thick blood absorbs ~all G and B, and much of R). Check them under the
locked grey ball. Per-channel G/B below the office 30 sRGB floor is allowed here: blood is a saturated liquid, and the
**luminance** stays inside the range.

| Use | sRGB | Linear | Roughness | Notes |
|---|---|---|---|---|
| Thin film / droplet edge, fresh human (measured transmission) | 210, 10, 16 | 0.644, 0.003, 0.005 | — | Only as an edge tint, never the main colour |
| Fresh arterial, opaque (droplets, wet splat) | 120, 8, 6 | 0.188, 0.0024, 0.0018 | 0.05–0.12 | Human reference only |
| Venous / pooled, opaque | 75, 6, 6 | 0.070, 0.0018, 0.0018 | 0.05–0.10 | Looks near-black with a white highlight |
| Tacky (minutes) | 60, 12, 8 | 0.045, 0.0037, 0.0024 | 0.25–0.35 | |
| Coagulated / old (hours) | 55, 18, 12 | 0.038, 0.0061, 0.0037 | 0.45–0.55 | |
| Dried (days), brown | 70, 35, 22 | 0.061, 0.017, 0.008 | 0.60–0.75 | Darker rim |
| **Zombie blood, wet (our main colour)** | **50, 16, 10** | **0.032, 0.0052, 0.0030** | 0.08–0.18 | Dark brown-red |
| **Zombie blood, dried / on armour** | **45, 30, 20** | **0.026, 0.013, 0.007** | 0.65–0.8 | Brown, slightly olive |
| Zombie mist (translucent sprite colour) | 90, 25, 18 | 0.102, 0.010, 0.006 | — | Opacity 0.1–0.25 |
| Wound cap: dark cauterised / dried flesh | 60, 30, 25 | 0.045, 0.013, 0.010 | 0.5–0.7 | Matte, with a few wet spots at 0.15 |
| Bone ring in the cap | 170, 155, 125 | 0.40, 0.33, 0.20 | 0.5 | Off-white; never pure white (KB teeth rule) |

- **UE Specular 0.28** for all blood (IOR 1.35). Metallic 0.
- **Thin-edge trick:** in the droplet and decal material, `BaseColor = lerp(EdgeTint, Core, thickness)`, where thickness
  is the sprite's radial gradient (droplets) or the decal's alpha (splats). Thin = brighter red, thick = dark.
- **Drying over time:** a decal age parameter lerps colour wet → tacky → dried and roughness 0.08 → 0.7 over ~30 s
  (compressed game time; the shine goes before the colour, KB §1 wetness rule).
- **The grade:** our castle is lit by 1700–1900 K torches and cool moonlight. Under torches, blood goes near black; that is
  correct. Do not brighten blood to "read". The highlight carries the read (RE2 "wet").

### 2.3 Motion

| Property | Real | Game value |
|---|---|---|
| Gravity | 9.8 m/s² | −980 cm/s², never reduced |
| Slash spatter size | 1–4 mm | Render **0.25–1.2 cm** (about 2–3× real, so it reads at 3–8 m) |
| Drip size | ~4.6 mm, 7.5 m/s terminal | 0.6–1.0 cm, drag so falling caps near 750 cm/s |
| Spray speed | Medium velocity | 200–600 cm/s; zombie 150–400 (no heartbeat) |
| Viscosity | ~4× water, shear-thinning | Strands that stretch then break; no bouncing; drops stick |
| Arc | Ballistic | Pure ballistic + light drag (0.5–1.0); no curl noise on drops |
| Cast-off | Line along blade arc | Spawn along the blade during the swing, inherit 20–30 % blade velocity |

- **Mist vs droplets vs strands.** Mist is the fine fraction (< 1 mm), visible only as a brief haze at the wound. Droplets
  carry the shape of the event. Strands are the viscous part, pulled off the blade and the wound edge.
- **Zombies don't pump.** A dead heart means no arterial spurting. Wounds **ooze and drip**, and spray only comes from the
  blade's own energy. This is both more real and less gory. Use it.

---

## 3. Niagara build recipe for UE 5.3

### 3.1 Emitters (one system `NS_Blood_Slash_337`, new; the live system is not edited)

| Emitter | Renderer | Material | Sim | Notes |
|---|---|---|---|---|
| **Droplets** | Sprite, **Facing: Velocity aligned**, size Y stretched by speed | Masked, Default Lit (deferred) | CPU | Main read. Fake sphere normal from UV; one sharp highlight |
| **Mist** | Sprite, camera facing | Translucent, Lighting Mode *Volumetric PerVertex NonDirectional* (cheap) | CPU | 0.25–0.4 s, tiny, low opacity, cut-out shape (no square cards) |
| **Strands** | Ribbon (from 2–3 lead particles) | Masked, Default Lit | CPU | Width tapers to 0, 0.3–0.6 s |
| **Cast-off** | Sprite, velocity aligned | Same as droplets | CPU | Spawn from blade socket line during swing (User param) |
| **Drips** (wound, after hit) | Sprite | Same as droplets | CPU | 1–3 drops over 1–2 s, falls straight |
| **Chunks** (sever only) | Mesh (3–4 small flesh bits) | Default Lit, zombie cap material | CPU | Only on dismember; 0–3 pieces |

- **Why masked, not translucent, for droplets and strands.** Masked particles are lit like geometry (Ghost of Tsushima's
  "deferred" billboards). They take shadows, real specular from torches, write depth and **velocity (motion blur)**,
  and have no overdraw sorting cost. Use dithered opacity mask (DitherTemporalAA) to fade them out.
- **Velocity-aligned stretch:** `SpriteSize.y = baseSize × (1 + speed × 0.012)` [UNVERIFIED factor]. At 500 cm/s a 0.5 cm
  drop becomes about 3.5 cm long, which matches a 1/60 s camera smear. Clamp at 6×.
- **Fake sphere normal on droplet sprites:** `N = (uv*2-1, sqrt(1-dot(..)))`, transformed by the sprite basis. This gives
  every drop its own highlight and stops the flat-disc look.
- **Size distribution:** `size = lerp(min, max, pow(rand, 3))`. Cubing the random value gives many small, a few large.
- **Mesh droplets?** Not needed. GoT ships with billboards and ribbons only. Mesh drops cost more and gain little at our
  camera distance.
- **No flipbooks for droplets.** A splash flipbook can be used for the first frame of mist only if needed.

### 3.2 Collision and ground blood

- Niagara **Collision** module, **CPU, Scene trace** (not depth buffer): depth-buffer collision misses off-screen and thin
  floors, and **GPU collision events are unreliable for spawning decals** (UE forum, same setup).
  ([forum](https://forums.unrealengine.com/t/niagara-collision-not-always-activating-decal/2731791))
- On collision: **kill the droplet** (blood does not bounce).
- **Decals: the safe path is Blueprint, not per-particle.** On the hit, the zombie Blueprint traces down (and toward the
  slash direction for walls) and spawns **1–3 decals** with `Spawn Decal at Location`. Reliable, cheap, easy to cap.
- **Optional later:** a Niagara **Decal Renderer** exists in 5.3 ([API page](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/Niagara/FNiagaraRendererDecals/__ctor?application_version=5.3)).
  Test it on a copy first; cap the number of decal-carrying droplets to ≤ 6 per hit.
- Small droplets that land become **tiny sprites lying on the floor** for 1–2 s (no decal), then fade. That is cheap and
  hides the moment of impact.

### 3.3 Decal materials (DBuffer caution)

- **Owner rule (KB README):** never change DBuffer settings, existing decal materials, or materials that decals sit on.
  **New assets only:** `M_BloodDecal_337` + instances. Nothing live is edited.
- Material Domain **Deferred Decal**, blend **DBuffer Translucent Color, Normal, Roughness** (the project already uses
  DBuffer; do not toggle the project setting).
- Channels: colour from §2.2 with an age parameter, **roughness** wet 0.08 → dried 0.7, a slight normal bump
  (surface tension gives a raised rounded edge) and a darker rim (coffee ring).
- 6–8 splat shapes in one atlas (from photographed spatter or a Substance spatter generator), random rotation, size
  ×0.7–1.4.
- **Overlapping DBuffer decals do not blend** (sort order picks one, KB §4.2). Give each new splat a rising Sort Order,
  or accept it.
- **Characters keep Receives Decals off** (KB §4.2). Blood on the zombie uses the **mesh wound mask** (KB §3.5, sphere mask
  on Pre-Skinned Local Position) with the zombie wet colour, plus a vertical drip streak below the wound (TLOU2 trails).
- **Test the one piece** next to an original decal-carrying surface, screenshot, then roll out (owner rule).

### 3.4 Cost budget (mid GPU, ~RTX 3060 / GTX 1660 Super at 1080p) [UNVERIFIED, profile with `stat GPU` and `stat Niagara`]

| Item | Budget |
|---|---|
| One slash system | ≤ 0.1 ms GPU, ≤ 0.05 ms game thread |
| All blood VFX on screen | ≤ 0.5 ms GPU |
| Concurrent blood systems | ≤ 8 (Niagara Effect Type: cull oldest, distance cull 30 m) |
| Particles per slash | ≤ 100 total (all emitters) |
| Translucent overdraw | Mist only; ≤ 8 sprites, each ≤ 25 cm, cut-out shape |
| Blood decals in world | ≤ 48, oldest fade first; lifetime 30 s + 3 s fade |
| Severed limbs in world | ≤ 8 (see §4) |

- Use **Niagara Effect Types** with scalability (Low: no mist, half droplets, no strands) and **pooling** on the
  system (Auto Release).
- Fixed bounds on the system (≈ 300 cm), so it does not compute dynamic bounds.

---

## 4. Dismemberment, "not too gory"

### 4.1 How games keep it from going too far

| Lever | Who does it | Our rule |
|---|---|---|
| Sever only on strong or finishing hits | Chivalry 2, For Honor (executions), DL2 | Heavy hit or killing blow only, never light hits |
| Chance, not every time | DL2, DI2 (wear through first) | Damage stage ≥ 2 (KB "peel before sever") **and** a chance roll |
| Short blood burst, no fountain | The Boys "legibility vs realism", DL2 backing off | One 0.3 s burst; zombie blood oozes, no pumping |
| Cap the wound | DL2 patch mesh | Dark dried / cauterised cap, a bone ring, little red |
| Little hanging gore | Restraint | No dangling tendons or organs; 0–2 small chunks |
| Limbs are simple rigid pieces | DL2, Chivalry 2 | Physics limb, no jiggle, no gushing |
| Dark, desaturated blood | The Boys grade, KCD | Zombie blood 50,16,10 sRGB |
| Player toggle | Chivalry 2, For Honor | Gore setting: Off / Reduced / Full |
| Gore on the body, not on screen | KCD 2, GoT | Blood on clothes, armour and the blade; no screen splatter |

### 4.2 Which bones

Names below are UE Mannequin style; use the matching Mixamo names if the zombie uses a Mixamo rig
(`LeftForeArm`, `LeftArm`, `LeftLeg`, `Head`). Check the zombie skeleton first.

| Cut | Hide bone | Cap on | Alive after? | Chance (heavy hit with stage ≥ 2) | Chance (killing blow) |
|---|---|---|---|---|---|
| Forearm (elbow) | `lowerarm_l/r` | `upperarm` end | Yes, zombie keeps coming | 25 % | 35 % |
| Upper arm (shoulder) | `upperarm_l/r` | `clavicle` end | Yes | 10 % | 20 % |
| Lower leg (knee) | `calf_l/r` | `thigh` end | **No, kill only** (no crawl anims yet) | 0 % | 15 % |
| Head (neck) | `head` | `neck_01` end | No, kill only; **optional**, off in Reduced | 0 % | 10 % (finisher only) |

- At most **1 sever per hit** and **2 per zombie**. A severed bone is added to a set; later hits on it are ignored.

### 4.3 Technical approach in UE 5.3 without pre-cut assets (Blueprint, per KB "gore without C++")

**On the zombie (main body):**
1. On a qualifying hit: get the **hit bone** from the Hit Result (Bone Name), walk up to the cut bone from the table.
2. `Hide Bone By Name` (cut bone, `PBO_None`). This scales the bone and its children to zero, so the limb collapses
   into the joint.
3. Attach the **wound cap mesh** (static mesh) to the parent bone at the joint, aligned along the bone. Scale per bone.
4. Spawn `NS_Blood_Sever_337` at the joint: one short burst + 2–3 drips over 1.5 s. Add a wound mask on the body
   (KB §3.5) near the joint.
5. Ignore later traces on hidden bone names (the physics bodies still exist after hiding; filter by the severed set).
6. Arm loss while alive: blend an "arm hang" additive off and let the zombie keep walking (RE2 style).

**The limb (option A, runtime, no pre-cut asset):**
1. Spawn a **second Skeletal Mesh Component** (or a small actor) with the same mesh, at the same transform, and copy the
   pose for one frame (`Set Leader Pose Component` to the zombie, then clear it; or a Copy Pose From Mesh AnimBP).
2. Give it a **limb-only material instance** (new MI of the zombie material, masked) that clips everything except the
   limb: an opacity mask from a **plane in reference-pose space** (Pre-Skinned Local Position, like the wound mask) at
   the joint. No mesh cutting needed.
3. Use a **per-limb physics asset** (e.g. `PA_Zombie_Forearm_337`) that only has the limb bodies, then
   `Set All Bodies Below Simulate Physics` (cut bone) and add an impulse along the slash (300–600 cm/s).
4. Put a smaller cap on the limb's cut end.
5. Known pitfalls ([UE forum](https://answers.unrealengine.com/questions/734672/view.html)): leader pose copies the
   physics asset and bone map; detached parts can stretch the bounds (hurts culling and shadows). Clear the leader pose
   before simulating and set bounds scale.

**The limb (option B, simpler and cheaper, recommended if option A fights us):**
- Bake **one static mesh per limb** offline in Blender from the zombie's own skeletal mesh (split by vertex weights,
  close the cut with the cap, add a convex collision). This is not "pre-cut art"; it is a scripted extract of the
  existing mesh. Spawn it with Simulate Physics at the bone transform. One draw call, cheapest physics.

**Cheap cap alternative [UNVERIFIED]:** clip the body with the same plane mask (inverted) instead of Hide Bone, make the
material two-sided, and shade **back faces** (`TwoSidedSign`) as dark cauterised flesh. The opening then looks filled
from most angles. Faster to build; check it from below and behind.

### 4.4 Limits and clean-up

- **Max 8 limbs** in the world; the oldest despawns first.
- Each limb: **20 s** life, then 2 s **dithered fade** (or sink 10 cm into the floor), then destroy.
- Physics: put limbs to sleep fast (Sleep Family Sensitive), no collision with Pawn (no tripping the player), collide
  with WorldStatic only.
- No limb pickup, no gibs, no organ meshes.

---

## 5. What we build (spec with numbers)

**Assets (all new; nothing live is edited, DBuffer settings untouched):**
`NS_Blood_Slash_337`, `NS_Blood_Sever_337`, `M_BloodParticle_337` (masked lit), `M_BloodMist_337` (translucent cheap
lit), `M_BloodDecal_337` + 6–8 splat variants, `SM_WoundCap_*_337` (forearm, upper arm, calf, neck), limb MI / physics
assets, `BP` logic in the zombie (or a gore component).

### 5.1 `NS_Blood_Slash_337` (on every hit that draws blood)

| Emitter | Count | Size | Speed | Spread | Life | Colour (sRGB) | Rough |
|---|---|---|---|---|---|---|---|
| Droplets | 30–60 (heavy hit ×1.5) | 0.25–1.2 cm, `pow(rand,3)` | 150–400 cm/s (zombie), along slash tangent + wound normal | 30° cone | until collision, max 1.2 s | core 50,16,10; edge 110,20,14 | 0.08 |
| Cast-off (from blade) | 10–20 along blade line | 0.3–0.8 cm | inherit 25 % blade velocity | along arc | max 1.0 s | same | 0.08 |
| Mist | 4–6 | 8–20 cm, grows ×1.5 | 100–200 cm/s, drag 4 | 45° | 0.25–0.4 s | 90,25,18, opacity 0.15 → 0 | — |
| Strands | 2–3 ribbons | width 0.3–0.6 cm, length ≤ 25 cm | 200–350 cm/s | 20° | 0.3–0.6 s | 50,16,10 | 0.1 |
| Drips (wound) | 1–3 | 0.6–1.0 cm | 0 (gravity) | — | over 1.5 s | 50,16,10 | 0.08 |
| Floor droplets | from collisions | as landed | 0 | — | 1.5 s then fade | 50,16,10 | 0.08 → 0.3 |

- Gravity −980 cm/s². Drag 0.5–1.0 on droplets. Velocity-aligned stretch factor 0.012, clamp 6×.
- UE Specular 0.28, metallic 0, no emissive. Masked dithered fade in the last 20 % of life.
- Light hits: ×0.5 counts, no strands.

### 5.2 Ground and body blood

- Per hit: **1–3 decals** by Blueprint trace (down, plus one toward the slash direction if a wall is < 150 cm).
- Decal size 15–40 cm (heavy hit up to 60 cm), random yaw, sort order rising.
- Decal life 30 s, drying wet → tacky → dried over 30 s (roughness 0.08 → 0.7, colour 50,16,10 → 45,30,20), then 3 s
  fade. **World cap 48 decals.**
- Body: wound mask slot (KB §3.5) at the hit, zombie wet colour, roughness 0.12, plus a 10–20 cm drip streak downward.
- Blade: optional blood mask on a **new** sword MI, 0 → 0.6 coverage per hit, cleared by the sheathe flick (GoT).

### 5.3 Dismemberment

- Triggers: heavy hit or killing blow only, and the limb zone at damage stage ≥ 2. Chances: forearm 25 / 35 %, upper arm
  10 / 20 %, lower leg 0 / 15 %, head 0 / 10 % (finisher only), as in §4.2.
- Max 1 sever per hit, 2 per zombie.
- Sever burst (`NS_Blood_Sever_337`): 40–60 droplets, 200–450 cm/s, one burst over **0.3 s**, then 2–3 drips over 1.5 s,
  0–2 small chunks (2–4 cm). No pumping.
- Wound cap: colour 60,30,25 sRGB, roughness 0.6 with 2–3 wet spots at 0.15, off-white bone ring 170,155,125. No hanging
  tissue.
- Limb: impulse 300–600 cm/s along the slash + 90–360°/s spin, life 20 s, fade 2 s, max 8 in world, collides with
  WorldStatic only.
- Gore setting: **Off** (no blood decals, no severing, mist only), **Reduced** (default: no head, ×0.6 counts),
  **Full**.

### 5.4 Checks before hand-off

1. Lookdev under locked exposure: blood droplet sheet and decal next to the grey ball, under a 1800 K torch and the moon.
   Blood must read as dark with a sharp highlight, never glowing.
2. Side-by-side clip: old blood vs new at 1/4 speed (motion blur on).
3. `stat GPU`, `stat Niagara` with 10 zombies being hit: inside §3.4.
4. One decal test next to an original decal-carrying wall (owner rule), screenshot, then roll out.
5. Owner sign-off on the "not too gory" level, with the Reduced setting as default.
