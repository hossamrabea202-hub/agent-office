# Jelly trails you can set on fire

Owner's idea, worked out by checkking (Claude), 2026-10-27. Status: **design, for the owner's OK**. Nothing to paste yet.

> Blobs and jelly zombies leave a slimy streak on the ground. A fire arrow or the Selfburn aura ignites it, and the fire runs along the trail, burning every zombie standing in it.

It ties together #10 Fire arrows, #5 Selfburn aura and #18 blob mines, and it gives the cannon a second job.

## 1. How it plays

1. **Jelly makes trails.** Jelly zombies (`ZType 5`, hatched from blobs) leave a wet, glossy green streak as they walk. A blob leaves a splat where it lands, and a bigger one when it melts (#18).
2. **Trails don't last.** A streak glistens for 20 s, then dries and fades over 5 s. A busy lane stays slick, an old one disappears.
3. **Fire ignites a trail.** Anything hot that touches a streak lights it:
   - a fire arrow or fire spear hit (#10),
   - the Selfburn aura while it's active (#5),
   - a cannonball blast (works **today**, no new weapon needed),
   - a burning torch or brazier knocked over (later, optional).
4. **The fire runs.** It travels along connected streak pieces at about **8 m/s**, so you can watch it race down the lane. It only jumps between pieces closer than 90 cm, so a gap in the trail stops it.
5. **It burns what's in it.** Each piece burns for **3 s**. Zombies standing in fire take 32 damage/s. **Jelly zombies take double**, because they're made of the stuff. A zombie that walks out keeps burning for 1.5 s.
6. **It leaves a scar.** A burnt piece turns into a dark scorch mark that fades over 10 s, and can't be lit again.
7. **Armed blob mines pop.** If fire reaches an armed blob (#18), it bursts **without hatching**: a 2 m ring of fire and no zombie. Lighting a blob-covered field is the reward for using fire.
8. **The hero isn't immune.** Standing in the fire hurts the hero at a quarter rate, **unless Selfburn is active**. Selfburn makes you fireproof, so you can walk a burning lane.

### Why it's fun

- **Choices:** shoot the jelly zombie now, or wait until three of them are walking in its trail and light the lane.
- **Combos:** cannon onto the tentacle → blobs rain down → jelly zombies hatch and spread slime → one fire arrow burns the whole wave.
- **Readable:** wet green = flammable, fire racing = danger, black scorch = safe. No HUD needed.

## 2. Numbers (first pass, all in one place to tune)

| Name | Value | Meaning |
|---|---|---|
| `DropSpacing` | 60 cm | a jelly zombie drops a trail piece every 60 cm walked |
| `PieceSize` | 70 cm | size of one trail piece (blob splat 160 cm, melt splat 220 cm) |
| `WetLife` / `FadeTime` | 20 s / 5 s | how long a piece lasts, then fades |
| `SpreadDist` | 90 cm | the fire jumps only to pieces this close |
| `SpreadDelay` | 0.11 s | per jump (≈ 8 m/s along a trail) |
| `BurnTime` | 3 s | how long one piece burns |
| `BurnDPS` | 32 | damage per second in the fire; ×2 for jelly zombies, ×0.25 for the hero |
| `AfterBurn` | 1.5 s | burning continues after stepping out |
| `MaxPieces` | 600 | oldest pieces are recycled first, so the cost never grows |
| `MaxFlames` | 48 | Niagara flames alive at once; burning pieces past that only glow |

## 3. How it's built

One new actor, **`BP_JellyTrailManager`**, placed once in the level. Everything else just calls it.

### Trail pieces = one Instanced Static Mesh

- `ISM_Trail`: a flat, slightly domed 1×1 m plane (`SM_TrailPuddle`), no collision, no shadows.
- Each instance is one trail piece, so 600 pieces cost one draw call.
- Per-instance custom data drives the material:
  - `[0]` BornT: when it was dropped (wet → dry fade)
  - `[1]` BurnT: when it caught fire (-1 = never)
  - `[2]` Size
  - `[3]` Seed: for a random shape and rotation, so pieces don't look tiled
- Parallel arrays in the manager: `Pos`, `BornT`, `BurnT`, plus a **grid map** (100 cm cells → piece indices) for quick lookups when spreading fire and finding zombies.

### Material `M_JellyTrail`

- **Wet:** dark green, high gloss, slight refraction, a soft wobble on the normals. It reuses the look of the jelly coat (`MI_ZombieJellyCoat`) so it reads as the same substance.
- **Burning:** the emissive goes from orange to yellow with scrolling heat noise, and the edges blacken from the outside in over `BurnTime`.
- **Scorched:** a dry black-brown char that fades out.
- Masked, not translucent, with a dithered edge, so it stays cheap on the 4 GB GPU.

### Fire VFX

- `NS_TrailFire`: one small Niagara flame (low licking fire, a few embers, smoke on the way out), pooled (`AutoRelease`).
- It spawns on a burning piece only if fewer than `MaxFlames` are alive; extra pieces still glow through the material. That keeps a long burning lane cheap.
- A crackle sound loops at the centre of each burning cluster, plus a "whoosh" at the point of ignition.

### Manager functions (what other Blueprints call)

| Function | Called by | Does |
|---|---|---|
| `AddTrail(Location, Size)` | BP_Zombie (ZType 5), BP_JellyBlob | traces down to the ground, adds or recycles a piece |
| `Ignite(Location, Radius)` | fire arrow (#10), Selfburn tick (#5), BP_Cannonball blast | lights every piece within Radius |
| `IsBurningAt(Location)` | BP_Zombie, hero, BP_JellyBlob | true if a burning piece is within 60 cm |

### Tick (every 0.1 s, not every frame)

1. **Spread:** each burning piece lights its unlit neighbours within `SpreadDist` once `SpreadDelay` has passed.
2. **Burn out:** a piece past `BurnTime` turns to scorch.
3. **Damage:** every 0.25 s, for each zombie and the hero, look up the grid cell. If `IsBurningAt`, apply `BurnDPS × 0.25` (×2 jelly, ×0.25 hero, 0 if Selfburn) with **DamageCauser = the manager**.
4. **Expire:** recycle pieces past `WetLife + FadeTime`.

### Hooks in existing Blueprints (small)

- **BP_Zombie:** if `ZType == 5`, call `AddTrail` every 60 cm moved. **Death by fire:** when the DamageCauser is `BP_JellyTrailManager`, play the burn death (char tint plus embers). This also gives #24 a third death text, "You burned", for the hero.
- **BP_JellyBlob:** `AddTrail(160)` on landing and `AddTrail(220)` at the melt. Each tick while armed: if `IsBurningAt` → pop (fire ring `Ignite(Loc, 200)`, no hatch, destroy).
- **BP_Cannonball:** on blast, `Ignite(ImpactLoc, BlastRadius)`. This makes the system playable today.
- **#10 Fire arrows / #5 Selfburn:** one `Ignite` call each when they're built.

## 4. Phases

| Phase | What | Who | Playable result |
|---|---|---|---|
| 1 | `M_JellyTrail`, `SM_TrailPuddle`, `NS_TrailFire` | checkking makes the specs + an editor Python script for the material; Master runs it and makes the Niagara from the spec | assets exist |
| 2 | `BP_JellyTrailManager` + jelly zombie trail + cannonball ignite | checkking builds, Master pastes | shoot the cannon into a slime lane and watch it burn |
| 3 | Blob mine pop + splats (#18) | checkking | fire clears mine fields |
| 4 | Fire arrow (#10) and Selfburn (#5) call `Ignite` | whoever owns #10 / #5 | full design |
| 5 | Burn death FX + "You burned" text (#24) | checkking + adjustedfilm | polish |

## 5. Owner decisions (answered 2026-10-27)

1. Normal zombies leave trails? **No**, only jelly zombies and blobs.
2. Cannon lights trails? **Yes**.
3. Fire hurts the hero? **Yes, at a quarter rate**, and not at all while Selfburn is active.
4. Fire hurts soldiers? **Yes**, at the normal rate (×1). Lighting a lane your own squad is standing in costs you soldiers, so place fire with care.
