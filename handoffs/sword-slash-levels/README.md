# #7 Sword VFX: the slash gets better as the hero levels up

From checkking (Claude), VFX Artist. Built on `handoffs/exports/checkking/BP_ThirdPersonCharacter.t3d` (live export, 2026-10-27). Kind: **manual** (written steps). Part A needs nothing new; part B waits on the material info below.

## What runs today

`BP_ThirdPersonCharacter · EventGraph`, on each montage hit notify:

| Swing | Damage | Slash spawn chain |
|---|---|---|
| AM_Slash1 | `ApplyRadialDamage` ZX8 (origin = actor + forward × 120, r 150) | SM2..SM16: StaticMeshActor at actor + (0,0,**20**), Roll **35**, scale 1, `SM_SwordSlash`, MID `Start` = GetTimeSeconds, LifeSpan **0.35** |
| AM_Slash2 | `ApplyRadialDamage` ZX9 | SL2..SL16: same, + (0,0,**25**), Roll **-15** |

Nothing in either chain reads `Level`, so a level-1 and a level-20 slash look the same.

## Part A: level tiers (paste-free, no new assets)

1. **One function for both chains.** Select SM2..SM16 and *Collapse to Function* → `SpawnSlashFX`. Inputs: `Roll` (float), `ZUp` (float), `TimeOffset` (float), `ScaleMul` (float). Wire Roll into the MakeRotator Roll pin, ZUp into the Add_VectorVector Z, and in `SetScalarParameterValue(Start)` use `GetTimeSeconds + TimeOffset`. Delete SL2..SL16 and call `SpawnSlashFX(-15, 25, 0, 1)` after ZX9; the SM call is `SpawnSlashFX(35, 20, 0, 1)` after ZX8.
2. **Level drives size and life**, inside `SpawnSlashFX`:
   - `L = Clamp(Level, 0, 10)` as float.
   - MakeTransform **Scale** = `(1 + 0.05 × L) × ScaleMul`, uniform (1.0 → 1.5 at level 10).
   - SetLifeSpan **InLifespan** = `0.35 + 0.015 × L` (0.35 → 0.50 s).
3. **Echo slash from level 4.** After each `SpawnSlashFX` call: `Branch(Level >= 4)` → `SpawnSlashFX(Roll + 8, ZUp + 6, 0.06, 0.9)`. Same mesh, a little rotated and later (the material's sweep starts from `Start`, so the +0.06 s offset makes it trail the first arc without a Delay node).
4. **Third arc from level 8:** `Branch(Level >= 8)` → `SpawnSlashFX(Roll - 8, ZUp - 6, 0.12, 0.8)`.

Result: lv 1-3 one arc; 4-7 two arcs and bigger; 8+ three arcs, about 1.4-1.5× size, longer trail.

## Part B: colour and glow by tier (needs the material)

Planned: steel white (lv 1-3) → gold (4-7) → ember orange with a glow boost (8+), via vector and scalar parameters on the same MID in `SpawnSlashFX`, plus a small spark burst along the arc at 8+. To wire it I need the material's parameter names.

## The offset bug (still open)

The arc spawns at the hero's centre, but the damage lands 120 cm in front. Whether that's the "offset" depends on where `SM_SwordSlash`'s pivot is. If the pivot is the arc's centre and the radius is about 120, it's already right. If the pivot is on the arc itself, the spawn needs `+ forward × 120` (wire `ZX5` instead of `GetActorLocation`). The bounds below will settle it.

## Needed from the Master (into `handoffs/exports/checkking/slash/`)

- `slash_mesh.txt`: `SM_SwordSlash` bounds (box extent and origin) and its material path.
- `slash_material.txt`: that material's parameter names with defaults (scalar, vector, texture) and what `Start` drives.
- A screenshot of a slash at level 1, from behind the hero, so I can see the current offset.

## Checks after Part A (Play)

1. Level 1: one arc, same as today.
2. Use the debug XP or level up to 4: two arcs, the second trailing slightly.
3. Level 8+: three arcs, visibly bigger, still gone within about 0.5 s.
4. Combo Slash1 → Slash2 still alternates the 35° and -15° roll, and damage is unchanged (the ZX8/ZX9 values aren't touched).
