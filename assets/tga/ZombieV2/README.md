# Zombie variations v2 (#199) — TGA (Claude), 2026-10-30

Six **original** zombie bodies × three skins, built procedurally (no licensed mesh used or shipped). Generator, baker,
anim and lookdev sources: `tools/tga/zombiev2/`. Run `import_zombiev2_ue.py` in the UE 5.3 editor (`py "<path>"`).

| Variant | Story | Geometry damage | Texture damage | Emissive |
|---|---|---|---|---|
| **Bloated** | drowned in the moat | swollen gut with a ragged vertical split | waterlogged blue-grey cast, slick (MI Wetness 0.6) | – |
| **Burnt** | fire deaths (#30) | cracked crust over the whole body | char crust, worst on the upper body | ember cracks (orange, GlowIntensity 6) |
| **Hollow** | torn apart | right arm gone at the shoulder, ribcage torn open with broken rib bars | flesh/bone in the chest hole and the arm stump | – |
| **Infected** | realm-touched (#155/#169) | pink growth clusters (shoulder, back, thigh, scalp) | pink growths + realm veins | eyes + growths (pink, GlowIntensity 5) |
| **Soldier** | risen castle soldier (#41) | tabard with folds and a torn hem, shoulder strap | faded tabard cloth (red / blue / violet by skin) | – |
| **Crawler** | legs gone at mid-thigh | ragged stumps | stump flesh + bone ends | – |

Skins: **Pale** (grey-green, dead a while), **Dark** (dark brown), **Realm** (violet-grey, pink veins and eyes glow).
Every body: wounds are geometry + texture only, no decals (owner rule). Milky sunken eyes, rotted nasal cavity,
teeth in a slack open jaw, dried blood running down from the mouth and wounds.

## Specs
- `SK_ZombieV2_<Variant>`: ~22k tris, one material slot, 2048² textures (BaseColor sRGB, ORM: R=AO G=roughness B=0,
  Normal DirectX, optional `_E` emissive mask). Non-metal, BaseColor 30–240 sRGB, 3-scale roughness (knowledge base).
- **Skeleton:** `SK_ZombieV2_Skeleton` uses **SK_Zombie's bone names** (#200: Hips root, Spine/Spine1/Spine2, Neck, Head,
  Left/Right Shoulder/Arm/ForeArm/Hand, UpLeg/Leg/Foot/ToeBase/Toe_End, HeadTop_End). The import adds it to
  SK_Zombie_Skeleton's **Compatible Skeletons** (both ways), so the existing zombie AnimBP/anims drive the walkers.
  Fingers and cloth bones are not in v2 (subset of the old skeleton; anims that key them are simply ignored).
  *Pending:* the Master's `zombie_refpose.txt` (dump script `tools/tga/zombiev2/dump_zombie_refpose_ue.py`) — with it
  the bind pose/rolls get matched exactly; until then check one walker in PIE for arm twist.
- **Crawler anims:** `A_ZombieV2_Crawl` (32 f loop, in place: alternating arm pulls, ~1 m/s at 1.0 play rate) and
  `A_ZombieV2_CrawlDeath` (40 f one-shot). Use a slow CharacterMovement speed (~90 cm/s) and capsule half-height ~35.
- Material `M_ZombieV2` uses the zombie skin master's parameter names (Tint, TintAmount, Wetness, HitT, GlowColor,
  GlowIntensity, BaseColorTex/ORMTex/NormalTex/GlowTex) so BP_ZombieVariety's tint/hit-flash code works unchanged.

## Spawn weights per wave (suggested; BP_ZombieWaveManager / BP_ZombieVariety pick a mesh + MI per spawn)
Weights are relative within a wave; the skin is rolled separately (Pale 50 / Dark 40 / Realm 10, Realm → 60 after the
realm breach SwarmUnlocked).

| Waves | Bloated | Burnt | Hollow | Infected | Soldier | Crawler | Notes |
|---|---|---|---|---|---|---|---|
| 1–3 | 20 | 0 | 35 | 0 | 0 | 45 | slow crowd: crawlers + hollows teach the player |
| 4–6 | 25 | 15 | 30 | 0 | 10 | 20 | Burnt after the first fire (#30); first risen soldiers |
| 7–9 | 20 | 20 | 20 | 15 | 15 | 10 | Infected from the realm breach (#190) |
| 10+ | 15 | 20 | 15 | 25 | 20 | 5 | Soldier weight +5 per fallen castle soldier (#41), cap 40 |

Crawlers are short targets: give them 60 % of a walker's HP and 2× XP for a headshot.
