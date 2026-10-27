# #2 Soldier level-up FX: less dramatic than the hero (build)

From checkking (Claude), VFX Artist. Built on the Master's exports in `handoffs/exports/checkking/levelup/` (BP_SoldierLevelUpFX graph + components, NS_LevelUp_None breakdown) and `BP_SoldierLevelWatch.t3d`. Kind: **manual**. Option **(a)**: tune `BP_SoldierLevelUpFX` itself. This replaces the Niagara plan in PLAN.md, because NS_LevelUp_None is empty.

## Why it reads hero-sized

`BP_SoldierLevelWatch` spawns `BP_SoldierLevelUpFX` at actor scale **0.33**, but:

- **Glow** (point light, radius **420**, intensity from `C_LvlUp_Light`) **ignores actor scale**. It lights a 4 m circle around the soldier exactly as brightly as the hero's. This is most of the "drama".
- **Two pillars** (inner and outer wall cylinders) and the full **2.6 s** timing are the same shape and length as the hero's.
- When a wave ends, several soldiers level in the same frame, so you get several hero-style columns and lights at once.
- The `NS_LevelUp_None` spawn draws nothing (an empty system), so removing it changes nothing visually.

## Changes

### A. BP_SoldierLevelUpFX (class defaults + EventGraph)

| # | Where | Change |
|---|---|---|
| A1 | Component **Glow** | AttenuationRadius **420 → 150** |
| A2 | EventGraph: `C_LvlUp_Light` → `SetIntensity` (CX_38 → CX_39) | multiply the curve value by a new float var `LightMul` (default **0.2**) before CX_39 |
| A3 | Component **Pillar2** (outer wall) | Visible **false**. One thin column instead of two |
| A4 | EventGraph: CX_14 `GetGameTimeSinceCreation` | multiply by a new float var `PlaySpeed` (default **1.6**) and feed that into all 9 targets (5× `T` params, 4× curve InTime). The whole effect plays 1.6× faster |
| A5 | BeginPlay CX_2 `SetLifeSpan` | **2.6 → 1.65** (= 2.6 / 1.6 plus a frame) |
| A6 | New bool var `bLite` (**Instance Editable + Expose on Spawn**, default false) | at the start of BeginPlay: if `bLite`, hide **Pillar** and **Glow** too, leaving just the ring and orb |

Note: BeginPlay CX_3..CX_12 snaps the actor to a cannon that's within 20 cm. That's left over from `BP_CannonLevelUpFX`. It never fires for soldiers, so leave it.

### B. BP_SoldierLevelWatch (the spawner)

| # | Where | Change |
|---|---|---|
| B1 | CX_21 `SpawnSystemAtLocation(NS_LevelUp_None)` | **delete** (draws nothing); wire CX_20.then → CX_22 |
| B2 | New float var `LastFXT` (default -10) | crowd throttle: before CX_19, `Lite = (GetTimeSeconds - LastFXT) < 0.15`. Feed `Lite` into CX_19's exposed `bLite` pin (Refresh Node after A6 to show it). After spawning, `LastFXT = GetTimeSeconds` **only when not Lite** |
| B3 | CX_22 `PlaySoundAtLocation` | VolumeMultiplier **0.5 → 0.3**, and skip the call when `Lite` (Branch). Ten soldiers leveling at once = one chime, not ten |

### C. Hero, a related leak (BP_ThirdPersonCharacter · CheckLevelUp)

`K2Node_CallFunction_7` spawns the same empty `NS_LevelUp_None` attached to the hero's Mesh with **bAutoDestroy = false**. It draws nothing, but every level-up leaves one more idle Niagara component on the hero. **Delete it** (wire XL15.then → CallFunction_229). The hero's real effect comes from `BP_HeroLevelUpWatcher` and is untouched.

## Result

| | Hero (unchanged) | Soldier before | Soldier after |
|---|---|---|---|
| Light | full curve, r 420 | full curve, r 420 | 20% of the curve, r 150 |
| Columns | 2 | 2 (scale 0.33) | 1 (scale 0.33) |
| Length | 2.6 s | 2.6 s | 1.6 s |
| 5 soldiers at once | n/a | 5 full effects + 5 chimes | 1 full + 4 ring/orb only + 1 chime |

## Checks (Play)

1. Level the hero: same effect as before.
2. Level one soldier: a short, thin blue column, a small glow on the ground only (no 4 m lit circle), gone in about 1.6 s, and it follows him if he's walking.
3. End a wave where several soldiers level at once: one full effect, the rest just a ring and orb, and one chime.
4. `stat Niagara` after 5 hero level-ups: no growing count of idle components (C).
