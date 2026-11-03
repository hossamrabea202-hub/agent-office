# #472 i5 as AAA technical artist: battle, crowd, crisp image, logic (roadmap, 2026-11-03)

Owner (Alien): "bring our quality up to better than best Call of Duty realism ... enhance the battle system and crowd
handling and crisp look and all logic needs polishing". Method: **measure, then change**, one pre-checked fix at a time,
with before/after.

## What the audit found (read-only, `bp_smells.js` on i9's 11-03 exports)
| Blueprint | Finding | Why it matters |
|---|---|---|
| BP_Zombie (827 nodes) | **Think every 0.25 s per zombie**: 2x GetAllActorsOfClass + 4x GetActorOfClass (gate, castle pieces, farmers); all timers start in the same frame (variance 0) | O(N) world scans per zombie = O(N^2) per wave; spikes because every zombie thinks in the same frame |
| BP_Zombie | **40 x PlayAnimation**, no Animation Blueprint | no blending (pops), no additive hit reacts, the 678 "AnimBP mode" warnings, every zombie animates at full rate |
| BP_Zombie | 11 x Delay in logic | fragile: a Delay keeps running after the zombie died / was pooled |
| BP_ZombieWaveManager | **ReceiveTick every frame** runs GetAllActorsOfClass + a loop; WaveTick (0.3 s) 3 more | the whole world is scanned every frame just to count zombies |
| BP_BattleDirector | event-driven, timers; fine | keep |

## Track C: crowd handling (biggest win first)
1. **Stagger Think** (one pin, now): BP_Zombie timer `K2Node_CallFunction_ZB6` (Think, 0.25 s, looping) InitialStartDelayVariance 0 -> 0.25. Same logic, the zombies spread over frames: no wave-start spike.
2. **Zombie registry** in the WaveManager: one array of live zombies, added on spawn and removed on death. It replaces the per-frame GetAllActorsOfClass (WaveManager Tick) and the farmer / zombie scans in Think. Cached gate / castle references at BeginPlay.
3. **Significance (distance LOD for logic)**: Think 0.25 s near the player, 0.5 s at 30-60 m, 1 s beyond; Tick off when not rendered.
4. **Animation budget**: skeletal mesh `VisibilityBasedAnimTickOption = OnlyTickPoseWhenRendered`, update-rate optimisation (URO), the engine Animation Budget Allocator. Far crowds later: vertex-animation impostors.

## Track A: battle feel (CoD-grade impact)
1. **Zombie Animation Blueprint**: a locomotion blend space, an attack slot, hit reacts as **additive directional** montages, death into ragdoll blend. It replaces the 40 PlayAnimation calls: smooth transitions, no pops, the 678 warnings gone.
2. **Hit response stack** per impact (what sells a hit in AAA shooters), in this order:
   - directional flinch (additive);
   - physical-animation pulse on the hit bone;
   - blood decal + VFX scaled by damage;
   - hit-stop 30-60 ms on heavy blows;
   - a camera kick scaled by weapon;
   - layered impact audio: flesh + armour + bone.
3. **Tentacle hit reaction** (#450): the clip is ready; it needs the BPC_TentacleSpit export.

## Track V: crisp image
- Today: 67 % screen percentage + TSR + sharpen 0.6 (i9's lag pass). That is soft by design. Target: the image AAA shooters hold:
  - TSR at **75-100 % with history at 200 %**;
  - tonemapper sharpen around 0.5;
  - mip bias tuned for foliage;
  - no motion blur on the weapon / HUD;
  - DOF only in cinematics.

  The headroom comes from Track C (CPU), so Track C goes first.
- Measure with locked camera A/B (base colour + lit) at the gate and on the wall walk.

## Track L: logic hygiene
- **Zero log errors** policy: the 1205 fault errors (F11 / F12) were array reads without guards. Next: a `BPFL_Castle` with safe helpers (SafeGetInt / SafeGetFloat), used wherever a raw index read is.
- **Replace Delay** in zombie logic with timers that are cleared on death.
- **After-save health check** (proposed in chat 1228): log errors, component-copy overrides, references to hidden pieces.

## Needs from i9 (request filed)
A **profiled wave** on the Master, in Play, at wave 3-4 with the most zombies:
- `stat unit`, `stat game`, `stat anim`, `stat ai` (screenshots or a log dump);
- the zombie count at that moment.

Optional: a 10 s Unreal Insights trace. This sets the baseline every fix above is measured against.
