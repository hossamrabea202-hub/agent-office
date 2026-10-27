# #18 Blobs: jelly blobs become mines

From checkking (Claude), VFX Artist. Built on `handoffs/exports/checkking/BP_JellyBlob.t3d` (live export, 2026-10-27). Kind: **manual** (written steps). Only `BP_JellyBlob` changes. The hatch chain (CX_38..CX_69: the jelly zombie, coat MID, shield, `ResumeMove`) stays exactly as it is.

Owner's ask: *"they act as mines, once you step on them they melt down and deform then form up slummy meshy then morph into a zombie"*.

## What runs today

- **BeginPlay:** lobbed by `Move` (ProjectileMovement) at 650-1250 cm/s, LifeSpan 25.
- **Tick**, state kept in the `Blob` MID:
  - `LandT < 0` (flying): when speed < 5 and age > 0.3 → `LandT = now`.
  - Landed (CX_27): when `HatchT < 0` and `now - LandT > 1.55` → `HatchT = now` → spawn the jelly zombie → blob LifeSpan 1.3.

So every blob hatches 1.55 s after it lands, whether or not anyone is near.

## New behaviour

| Phase | When | What you see |
|---|---|---|
| Armed | landed, nobody close | sits on the ground with a slow jelly breathing pulse |
| Triggered | the hero comes within **110 cm** of `Body` | `TrigT = now` |
| Melt | 0 → 0.5 s after the trigger | squashes flat and spreads: scale XY 1 → 1.8, Z 1 → 0.25 |
| Re-form | 0.5 → 1.5 s | pulls up into a wobbling slimy column: XY 1.8 → 0.6, Z 0.25 → 2.2, jiggle fading out |
| Hatch | 1.5 s | the existing hatch chain fires (zombie + coat + shield, blob LifeSpan 1.3) |
| No timeout | armed, nobody steps on it | **waits forever** (owner's call, 2026-10-27). `ArmedMax` stays in as a switch: set it above 0 to hatch untouched blobs after that many seconds |

All of the deforming is `SetRelativeScale3D` on the `Blob` mesh, so there's no material change and no new asset.

## Steps (BP_JellyBlob)

**Variables** (new): `TrigT` float, default **-1**. `ArmedMax` float, default **0** (0 = never hatch on its own). `TriggerRadius` float, default **110**.

**BeginPlay:** SetLifeSpan 25 → **0** (the hatch chain's own SetLifeSpan 1.3 still cleans up; an armed blob must not vanish at 25 s).

**Tick, landed branch:** put a new block between `CX_16.else` and `CX_27`. CX_27 is today's HatchT check; we replace its condition.

1. `Sequence` → `then_0`: **trigger check**
   - `Branch(TrigT < 0)` →
   - `Dist = VSize(GetPlayerCharacter(0).GetActorLocation - Body.GetComponentLocation)`
   - `Branch(Dist < TriggerRadius)` → `Set TrigT = GetTimeSeconds`
2. `then_1`: **shape**, `Branch(TrigT < 0)`:
   - **true (armed):** `p = 1 + 0.06 × sin(now × 3)` → `Blob.SetRelativeScale3D(p, p, 2 - p)`
   - **false (triggered):** `t = now - TrigT`
     - `a = Clamp(t / 0.5, 0, 1)` and `b = Clamp((t - 0.5) / 1.0, 0, 1)`
     - `XY = Lerp(1 + 0.8a, 0.6, b)` and `Z = Lerp(1 - 0.75a, 2.2, b)` (Lerp A = melt value, B = column value, Alpha = b)
     - `jig = 0.08 × sin(now × 25) × (1 - b) × a`
     - `Blob.SetRelativeScale3D(XY + jig, XY - jig, Z)`
3. `then_2`: the existing `CX_27` (HatchT getter) chain. Replace **CX_31's input** (`now - LandT > 1.55`) with:
   - `Triggered = (TrigT >= 0) AND (now - TrigT > 1.5)`
   - `TimedOut = (ArmedMax > 0) AND (TrigT < 0) AND (now - LandT > ArmedMax)`
   - `CX_32.B = Triggered OR TimedOut` (CX_32.A, the `HatchT < 0` check, stays)

5.3 paste rules from the README still apply: no `Ease`, use `Lerp` and `Clamp`.

## Checks (Play)

1. Fire the cannon at the tentacle so blobs fall. They land and **stay**, breathing gently. No zombie at 1.55 s.
2. Walk the hero onto one: it flattens and spreads (about 0.5 s), rises into a wobbling column (about 1 s), and the jelly zombie hatches from it with its coat and shield, same as today.
3. Leave one alone for a minute: it is still armed and never hatches on its own.
4. Soldiers walking over a blob do **not** trigger it (hero only). Say in the cafeteria if the owner wants soldiers to trigger it too: swap `GetPlayerCharacter` for a sphere overlap.
5. Many blobs at once: no frame-time spike (Tick work per blob is one distance check and one scale set).
