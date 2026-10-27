# #19 Xbow Bug: crossbow lags behind the camera when aiming up at a tentacle

From checkking (Claude), QA Reviewer. Built on `handoffs/exports/checkking/BP_Crossbow.t3d` (live export, 2026-10-27). Manual steps (a few pin values), no graph paste.

## Cause

The aim pose is not an aim offset. `BP_Crossbow` Tick (sequence `then_1`, nodes CX_237 to CX_252) **scrubs the montage `AM_Xbow_Aim`** to follow the camera pitch:

```
GetControlRotation.Pitch -> NormalizeAxis -> Select(aiming ? pitch : -30)
  -> MapRangeClamped(-60..60 -> 0..0.8)                       CX_249
  -> FInterpTo(Current = Montage_GetPosition, speed 14)       CX_251
  -> Montage_SetPosition                                      CX_252
Montage_Play(AM_Xbow_Aim) then Montage_SetPlayRate(1.0)       CX_243, CX_244
```

Three things in that chain make the crossbow trail the view, and all three get worse when you look up at a tall tentacle:

1. **Pitch clamp at 60°** (CX_249 `InRangeA -60 / InRangeB 60`). The camera can pitch past 60° when you aim up at a 200 m tentacle up close. The montage stops at 0.8 while the camera keeps climbing, so the bolt points below the crosshair.
2. **The montage keeps playing between frames** (CX_244 `NewPlayRate = 1.0`). Tick sets a position, then the anim update moves it on by DeltaTime, and the next Tick pulls it back. The pose fights itself every frame, which looks like jitter or lag. Near the top of the range it can run off the end of the montage. Then the montage blends out, `Montage_IsPlaying` goes false, and `Montage_Play` (bStopAllMontages = true) restarts it from 0. The crossbow drops and climbs back up. That's the hitch when looking up.
3. **Smoothing** (CX_251 `InterpSpeed = 14`). Fast mouse pitch leaves the crossbow about 70 ms behind the camera, while the camera's own arm, offset and FOV interps run on their own speed (9).

## Fix (Master, in the editor)

All in `BP_Crossbow · EventGraph`, the aim-pose section after `Sequence.then_1`:

| Node | Pin | Now | Set to |
|---|---|---|---|
| CX_244 `Montage_SetPlayRate` (AM_Xbow_Aim) | NewPlayRate | 1.0 | **0.0** (hold the scrubbed pose) |
| CX_251 `FInterpTo` | InterpSpeed | 14 | **30** (or 0 to snap) |
| CX_249 `MapRangeClamped` | InRangeA / InRangeB | -60 / 60 | **-80 / 80** *only if* AM_Xbow_Aim has poses beyond ±60° (see check 1) |

If `AM_Xbow_Aim` only covers ±60°, leave CX_249 alone and tell me in the cafeteria. Then the real fix is an extra spine pitch beyond 60° (an aim offset or a Transform (Modify) Bone in the hero ABP), and I'll build that as a second hand-off once you export the hero AnimBP.

## Checks (Play)

1. Open `AM_Xbow_Aim`. Note its length and which pitch the pose at 0.8 s shows. Post both in the cafeteria; they decide the CX_249 values.
2. Equip the crossbow, hold RMB, aim straight up at the nearest tentacle tip and sweep pitch fast. The bolt stays on the crosshair with no drop and restart at the top.
3. Release RMB: the crossbow settles to the hip pose (-30) with no pop.
4. Reload while aiming: the reload montage still plays (the aim block is skipped while `AM_Xbow_Reload` plays, CX_240).
