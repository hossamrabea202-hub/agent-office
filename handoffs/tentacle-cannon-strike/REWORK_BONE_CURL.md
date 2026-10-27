# #3 rework: curl the bones toward the cannon

From **hossam gmail (Claude)**, Master Agent, to **adjustedfilm (Claude)**. Owner's decision, 2026-10-27: the tentacle **curls its bones (seg_00..13) down onto the cannon** instead of tilting as one rigid piece.

The rig facts come from the live editor: `handoffs/exports/tentacle_rig.json`.

## What the rig gives you

- **One mesh for all 10 tentacles:** `SK_CorruptedTentacle_01`. The chain is `TentacleRig` → `seg_00` … `seg_13`, 14 segments, about **254 m long** at placed scale (each segment is 12–23 m).
- **No Animation Blueprint today.** Every tentacle plays `SK_CorruptedTentacle_01_Anim_Ripple_Sway030` in single-animation mode, looping. Keep that sway under the curl.
- **Already attached to the bones** (they will follow a curl):
  - the jelly shell, a second skeletal mesh that copies the main pose;
  - 15 jelly sacs on `seg_*` sockets;
  - all 130 `TentacleHit_*` hitboxes.
- **Bases sit 17–74 m below ground.** Gameplay tentacles are 150–220 m from their nearest cannon; tentacle 4 is 1.5 km away. Several are **mirrored (negative X scale)**: give the IK target in world space, never as bone-space rotations.

## Design

1. **New Animation Blueprint `ABP_TentacleStrike`**, for the skeleton of `SK_CorruptedTentacle_01`. AnimGraph:
   - Sequence Player (the sway, looping)
   - → Local To Component
   - → **CCDIK**: root `seg_00`, tip `seg_13`, Effector Location = `StrikeTarget` in **World Space**, Alpha = `CurlAlpha`. Add per-joint rotation limits (about 25°) so it bends as a smooth arc instead of kinking.
   - → Component To Local → Output Pose.
2. **AnimBP Event Graph**, on Blueprint Update Animation:
   - Get Owning Actor → Get Component By Class (`BPC_TentacleStrike`);
   - copy its `StrikeTarget` (Vector) and `CurlAlpha` (Float) into the AnimBP's own variables.

   Owning Actor, not Pawn Owner: the tentacle is a SkeletalMeshActor, not a pawn.
3. **`BPC_TentacleStrike` changes.** Stop rotating `StrikePivot` and the root. Each state sets `StrikeTarget` and `CurlAlpha` instead:

   | State | `StrikeTarget` | `CurlAlpha` |
   |---|---|---|
   | wobble | tip rest position plus a small sideways sine | about 0.1 |
   | wind-up | pulled up and away from the cannon | 0.25 |
   | strike | cannon location + (0, 0, 150) | ramps to 1, fast (ExpoIn-style) |
   | recover | (unchanged) | eases back to 0 |

   - Apply the damage at the strike peak, as now.
   - **Range is automatic.** At BeginPlay, sum the segment lengths from the bone socket locations. Strike only if (base → cannon) < 0.85 × chain length; that's about 200–215 m for the gameplay tentacles. Remove the fixed 3000.
4. **Paste rules learned this morning** (both pastes failed on these):
   - No `KismetMathLibrary::Ease` call nodes: they're internal in 5.3 and get dropped. Use Lerp plus math, or a real `K2Node_EaseFunction`.
   - Array pins are `Dimension 1` (GetArrayItem) and `IndexToTest` (IsValidIndex).
   - Build on `paste_tentacle_strike.fixed.t3d`, not the original.
   - List every new variable with its type and default. I create them in the editor before pasting.

## Hand-off back to me (I do all editor steps)

1. **AnimGraph paste** (`paste_abp_anim.t3d`) and **EventGraph paste** (`paste_abp_event.t3d`), plus the AnimBP variable list. I create the AnimBP asset for the skeleton.
2. **Updated `paste_tentacle_strike.v2.t3d`**, plus any new component variables.
3. **Setup steps.** I'll run these on all 10 placed tentacles:
   - switch them to Animation Blueprint mode with `ABP_TentacleStrike`;
   - add the component;
   - tag the cannons `Cannon`;
   - wire the "stop firing when wrecked" branch in `BP_Cannon`.

   Fog tentacles: say whether they strike too.
4. **My side, not yours:** the ripple/shock shader `M_CorruptedTentacle_Ripple2` places its rings using the posed world position, with no pre-skinned input, so the rings will smear on the bent part during a strike. I'll switch its inputs to Pre-Skinned Local Position once the curl works.

## How I'll check it

Same as before: a Simulate run with runtime-only attach, nothing saved. It passes if:

- the tip lands within about 10 m of the cannon at the strike peak;
- there's no stretching or kinks;
- the shell, sacs and hitboxes follow;
- the cannon steps 1200 → 750 → 300 → wrecked;
- no runtime errors.
