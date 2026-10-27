# #3 v2: the tentacle curls and strikes with its tip

From **adjustedfilm (Claude)** to the **Master Agent**. The owner picked **curl the bones**. This replaces the rigid lean in `BPC_TentacleStrike`. `BPC_CannonBreak` (your fixed file) stays as it is.

**How it works:** a post-process Anim Blueprint runs FABRIK from `seg_00` to `seg_13` on top of whatever the tentacle already plays, so the existing wobble and jelly animation stay. `BPC_TentacleStrike` drives it every tick with two values: `StrikeAlpha` (how much IK) and `StrikeTarget` (where the tip goes). The tip rises and sways (wobble), rears back and up (wind-up), then whips down onto the cannon (strike), and the hit lands at the end of the whip.

UE 5.3 fixes are built in: no `Ease` nodes (Lerp + math), `Dimension 1`, `IndexToTest`.

| File | Paste into |
|---|---|
| `paste_abp_tentacle_strike_pp_animgraph.t3d` | `ABP_TentacleStrikePP` → **AnimGraph** |
| `paste_tentacle_strike_curl.t3d` | `BPC_TentacleStrike` → **EventGraph** (replaces the old graph) |

## 1. ABP_TentacleStrikePP (new)

1. In `/Game/CastleDefender/Gameplay/Tentacle/` create an **Animation Blueprint** for the tentacle's skeleton, named exactly `ABP_TentacleStrikePP`. `BPC_TentacleStrike` casts to that path.
2. Variables: `StrikeAlpha` (Float, 0) and `StrikeTarget` (Vector, 0).
3. Paste the AnimGraph file into the **AnimGraph**. You get Input Pose → Local To Component → FABRIK → Component To Local. Drag the last node's pose into **Output Pose** (the paste can't carry the Output Pose node). Compile and save.
4. Open the tentacle **Skeletal Mesh asset**. In Asset Details, set **Post Process Anim Blueprint** to `ABP_TentacleStrikePP` and save.

## 2. BPC_TentacleStrike v2

1. Delete everything in its EventGraph.
2. Add these variables (keep the ones that already exist):

| Variable | Type | Default |
|---|---|---|
| StrikeRange | Float | **19000** (190 m, inside a ~206 m tentacle's reach) |
| StrikeDamage | Float | 450 |
| StrikeEvery | Float | 12 |
| MaxStrikers | Integer | 2 |
| WobbleTime | Float | 1.4 |
| WindupTime | Float | **0.6** |
| StrikeTime | Float | **0.35** |
| RecoverTime | Float | **1.6** |
| WobbleCm | Float | 600 (sideways sway of the tip) |
| RootBone | Name | seg_00 |
| TipBone | Name | seg_13 |
| HitFX | Niagara System ref | |
| HitSound | Sound Base ref | |
| Mesh | Skeletal Mesh Component ref | internal |
| State | Integer | internal |
| StateTime, Reach, Alpha | Float | internal |
| TargetCannon | Actor ref | internal |
| Base, Dir, Side, Hover, Windup, Aim | Vector | internal |

   You can delete the old StrikePivot, BaseRot, LeanAxis, Angle, LeanSign, WobbleDeg, WindupDeg and StrikeDeg.
3. Paste `paste_tentacle_strike_curl.t3d`, then compile and save.
4. Add `BPC_TentacleStrike` to `BP_TentacleVitals`. It finds the parent tentacle's Skeletal Mesh by itself (attach parent first, then its own actor), so no pivot is needed.

## 3. Check in Simulate

- Cannon tagged `Cannon` with `BPC_CannonBreak`, and a tentacle base within 190 m of it. Use `StrikeEvery = 3` for a quick look.
- Expect: the tentacle bends, the tip rises and sways for 1.4 s, rears back, whips down and touches the cannon. Then come the hit FX, the damage step and the slow recovery.
- Tentacles farther than about 190 m never strike, because their chain can't reach. If no gameplay tentacle is that close, tell me and I'll add a "lunge" (the root slides toward the cannon during the wind-up).

## If something is off

- **Cast pin shows red:** right-click the Cast node → Refresh Node, then reconnect its blue "As ABP Tentacle Strike PP" pin to both Set nodes.
- **Tentacle bends the wrong way or twists:** in the FABRIK node, check that Root Bone is `seg_00` and Tip Bone is the last segment (`seg_13`). Effector space must be **World Space**.
- **Nothing bends:** the Skeletal Mesh asset's Post Process Anim Blueprint isn't set, or the mesh found is a different Skeletal Mesh (the jelly shell?). Then set `Mesh` in `BP_TentacleVitals` BeginPlay.
