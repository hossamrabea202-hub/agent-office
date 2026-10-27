# #32 Jelly trail fire, phase 2: the fire manager + hooks

From checkking (Claude). Design and the owner's answers: `DESIGN.md` (section 5: only jelly leaves slime, cannon ignites, hero burns at 1/4 and not with Selfburn, **soldiers burn at the normal rate**). Needs phase 1 (`M_JellyTrail`, hand-off #35) first. Kind: **manual spec**. Build it as you did #27/#30 (events instead of functions where a paste needs them).

Playable result: jelly zombies leave slime → shoot the cannon into it → the fire runs down the lane and burns zombies (and careless soldiers).

---

## 1. New struct `S_IntList`

`/Game/CastleDefender/Gameplay/JellyTrail/S_IntList` with one member `Items: Array<int>`. It's needed because a Map value can't be an array directly.

## 2. New actor `BP_JellyTrailManager`

`/Game/CastleDefender/Gameplay/JellyTrail/BP_JellyTrailManager`. **Place one in the level** at the origin.

### Components

- `ISM_Trail` (InstancedStaticMesh): mesh `/Engine/BasicShapes/Plane`, material `M_JellyTrail`, **NumCustomDataFloats 4**, Collision NoCollision, Cast Shadow off.

### Variables (tunables first)

| Var | Type | Default |
|---|---|---|
| `MaxPieces` | int | 600 |
| `WetLife` | float | 25 (20 wet + 5 fade, matches the material) |
| `SpreadDist` | float | 90 |
| `SpreadDelay` | float | 0.11 |
| `BurnTime` | float | 3.0 (matches the material) |
| `BurnDPS` | float | 32 |
| `MaxFlames` | int | 48 |
| `FireFX` | NiagaraSystem | **the torch/campfire fire you use today** (asked in #35; if it's Cascade, use a ParticleSystem var and `SpawnEmitterAtLocation`) |
| `FireScale` | float | 0.5 |
| `Pos` | Array<Vector> | |
| `BornT`, `BurnT`, `Size` | Array<float> | |
| `Spread` | Array<bool> | |
| `Cells` | Map<int, S_IntList> | grid: 100 cm cells → piece indices |
| `PieceCell` | Array<int> | which cell each piece is in |
| `Active` | Array<int> | pieces burning right now |
| `Flames` | Map<int, NiagaraComponent> | piece → its flame |
| `Head` | int | 0 (ring-buffer write position) |
| `DmgAcc` | float | 0 |

### Helper: `CellKey(Loc) → int` (pure)

`(Floor(Loc.X / 100) + 5000) * 10000 + (Floor(Loc.Y / 100) + 5000)`

### Helper: `PiecesNear(Loc, R) → Array<int>` (pure-ish)

For `cx` from `Floor((Loc.X - R) / 100)` to `Floor((Loc.X + R) / 100)`, and `cy` likewise on Y: `Find(Cells, (cx + 5000) * 10000 + (cy + 5000))` → append its `Items`. Return the list. The caller does the exact distance check.

### `BeginPlay`

`SetActorTickInterval(0.1)`.

### Event `AddTrail(Loc: Vector, PieceSize: float)` (called by others)

1. Ground: `LineTraceForObjects` from `Loc + (0,0,60)` to `Loc - (0,0,250)`, ObjectTypes `[WorldStatic]`. No hit → return.
2. `i = Head`, then `Head = (Head + 1) % MaxPieces`.
3. `Xf = MakeTransform(HitLoc + HitNormal × 1.5, MakeRotFromZX(HitNormal, RandomUnitVector), (PieceSize/100, PieceSize/100, 1))`.
4. If `i >= Pos.Length`: **new**. `ISM_Trail.AddInstance(Xf, WorldSpace = true)` and `Add` to every array (Pos, BornT, BurnT -1, Size, Spread false, PieceCell 0).
   Else: **recycle**. Remove `i` from `Cells[PieceCell[i]].Items` (Find, RemoveItem, Add back). If `Flames` contains `i`, Deactivate it and Remove. `Active.RemoveItem(i)`. `ISM_Trail.UpdateInstanceTransform(i, Xf, World = true, MarkDirty = true)`.
5. Set `Pos[i] = HitLoc`, `BornT[i] = Now`, `BurnT[i] = -1`, `Size[i] = PieceSize`, `Spread[i] = false`.
6. Custom data (last call MarkRenderStateDirty = true): `[0] Now`, `[1] -1`, `[2] PieceSize`, `[3] RandomFloat`.
7. Grid: `k = CellKey(HitLoc)`, `PieceCell[i] = k`, add `i` to `Cells[k].Items` (Find or new S_IntList, Add, Map.Add).
8. **Dropped into fire catches fire:** if `IsBurningAt(HitLoc)` → `LightPiece(i)`.

### `LightPiece(i)`

Return unless: `i` is valid, `BurnT[i] < 0`, and `Now - BornT[i] < WetLife`. Then:
- `BurnT[i] = Now`, `Spread[i] = false`, `ISM_Trail.SetCustomDataValue(i, 1, Now, true)`, `Active.Add(i)`
- if `Flames.Length < MaxFlames` and FireFX is valid: `SpawnSystemAtLocation(FireFX, Pos[i], scale FireScale × Size[i]/70, AutoDestroy false)` → `Flames.Add(i, comp)`

### Event `Ignite(Loc: Vector, Radius: float)` (called by others)

For each `p` in `PiecesNear(Loc, Radius)`: if `Dist(Pos[p], Loc) < Radius` → `LightPiece(p)`. Then play the whoosh SFX at Loc if anything lit (any existing fire SFX).

### `IsBurningAt(Loc) → bool` (pure)

For `p` in `PiecesNear(Loc, 100)`: true if `BurnT[p] >= 0`, `Now - BurnT[p] < BurnTime`, `Dist2D(Pos[p], Loc) < Size[p] × 0.5 + 30` and `Abs(Pos[p].Z - Loc.Z) < 120`.

### `Tick` (every 0.1 s)

1. **Spread and burn out.** For each `i` in a **copy** of `Active`:
   - `t = Now - BurnT[i]`
   - if `!Spread[i]` and `t >= SpreadDelay`: `Spread[i] = true`; for `p` in `PiecesNear(Pos[i], SpreadDist)`: if `Dist(Pos[p], Pos[i]) < SpreadDist` → `LightPiece(p)`. Trails are dropped every 60 cm, so this runs the fire down a trail at about 8 m/s, and gaps over 90 cm stop it.
   - if `t >= BurnTime`: `Active.RemoveItem(i)`; if `Flames` has `i`: Deactivate, Remove.
2. **Damage**, every 0.25 s: `DmgAcc += DeltaSeconds`. If `DmgAcc >= 0.25` and `Active.Length > 0`: `DmgAcc = 0`, then for each actor in `GetAllActorsOfClass(Character)`:
   - `Feet = ActorLoc - (0, 0, CapsuleHalfHeight)`
   - if `IsBurningAt(Feet)`: `Rate` =
     - **BP_Zombie** → `ZType == 5 ? 2 : 1`
     - **BP_ThirdPersonCharacter** (hero) → `0.25`, or `0` if the hero has a `SelfburnActive` bool and it's true (#5 adds that; until then 0.25)
     - **anything else** (soldiers, Commander) → `1`
   - `ApplyDamage(Actor, BurnDPS × 0.25 × Rate, DamageCauser = self)` (skip when Rate = 0).

---

## 3. Hooks in existing Blueprints

### BP_Zombie: jelly zombies leave slime

New vars `TrailMgr` (BP_JellyTrailManager ref) and `LastTrailPos` (Vector, default 0,0,-99999). In ReceiveTick (any branch that runs while alive), add:

`ZType == 5` (it's set by BP_JellyBlob right after spawn, so check every tick, not in BeginPlay) **and** `Dist2D(ActorLoc, LastTrailPos) > 60` →
- if `TrailMgr` isn't valid: `TrailMgr = GetActorOfClass(BP_JellyTrailManager)`
- `LastTrailPos = ActorLoc`
- `TrailMgr.AddTrail(ActorLoc - (0, 0, CapsuleHalfHeight), 70)`

The death branch needs no change: kills by fire credit XP like any other kill. (Burn death FX and "You burned" are phase 5.)

### BP_JellyBlob: splats

- Where `LandT` is set (CX_26): `GetActorOfClass(BP_JellyTrailManager).AddTrail(Body.WorldLoc, 160)`.
- With #30 in: where `TrigT` is set: `AddTrail(Body.WorldLoc, 220)`.

(Armed blobs popping in fire is phase 3.)

### BP_Cannonball: blast lights slime

In the cannonball's explode or impact event (where it already does its radial damage or blast FX): `GetActorOfClass(BP_JellyTrailManager)` → if valid, `Ignite(ImpactLocation, <the blast radius it already uses>)`. I don't have a BP_Cannonball export, so use the radius that's already in that graph.

### Soldiers

Nothing to change, as long as soldiers already take damage through `ReceiveAnyDamage` (they do in the commander exports). They burn at the same rate as normal zombies.

---

## 4. Checks (Play)

1. Fire the cannon at a tentacle; let blobs hatch jelly zombies. Behind each jelly zombie, a line of glossy green puddles every ~60 cm. Normal zombies leave none.
2. Each blob leaves a bigger splat where it lands.
3. Shoot the cannon onto a slime lane: it lights at the impact and the fire runs along the trail (~8 m/s), each puddle burning orange for 3 s then turning black.
4. A zombie in the fire loses ~32 HP/s (jelly zombies ~64). A soldier standing in it gets hurt at 32/s. The hero at ~8/s.
5. A jelly zombie walking into a burning lane drops slime that catches immediately.
6. Gaps over ~90 cm stop the fire.
7. Heavy wave (50+ zombies, 600 puddles): `stat unit` game thread stays where it was ±1 ms; `stat Niagara` shows at most 48 trail flames.
8. After ~25 s the old slime is gone. Old scorch marks fade 10 s after burning.
