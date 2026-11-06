# #450 tentacle cannon reactions (adjustedfilm, 2026-11-06)

Owner: *"tentacle reaction: very subtle and boring, not breath-taking"*, then: *"animate the tentacle reaction to the cannon
so it becomes on the same level of Netflix Stranger Things"*.

**What happens today (export 11-03):** a cannonball hit on a tentacle spawns a plasma burst and takes HP; the 76 m arm
does not move at all (`BP_TentacleVitals`, the `BP_Cannonball` branch `CX_199 -> CX_200 -> CX_129`). Sword and bolt hits
play the 3 s wobble montage from #450 phase 2. The death is a 1.6 s delay, then a 7.5 s sink, with smoke, shake and sound.

**New clips (24 fps, whole-arm performances on `SK_CorruptedTentacle_01`, start at rest, A/B end at rest, C holds):**

| Clip | Length | What |
|---|---|---|
| `AS_Tentacle_CannonA` (head hit) | 4.0 s | the head snaps away in 2 frames (44 deg), the shock runs down the arm (25 ms per segment), the top folds over and whips; the arm rears back, then thrashes forward and sideways twice with a twist; a 9 Hz spasm decays; a last shiver; back to rest |
| `AS_Tentacle_CannonB` (body hit) | 4.0 s | the arm buckles at the hit (a kink at seg 6), the top folds over the kink and whips; rear, thrashes, spasm, rest |
| `AS_Tentacle_CannonC` (death) | 6.0 s | the killing hit, three convulsions that grow (26, 34, 42 deg per segment) with twist, a rigid 11 Hz tremor, then the arm folds over from the base and collapses; holds |

Tip travel: A/B up to 90 m from rest (the idle sways 27 m), C 100 m. `preview/`: `CannonA|B|C_vs_idle.mp4` (idle | new) and stills.
Generator: `gen_cannon.py` (`<rig.fbx> <out.fbx> A|B|C [amp]`, same conventions as `gen_react.py`; A/B at amp 0.75, C at 0.6).

**Wiring (`wire_cannon_ue.py`, UE 5.8 graph editing from Python, no paste; tested on a copy):**
- cannonball hit: `CX_200.then` -> mesh (`GetComponentByClass` SkeletalMeshComponent) -> `GetPostProcessInstance` ->
  Branch(RandomBool) -> `Montage_Play` A or B -> `CX_129` (CastFailed also -> `CX_129`);
- death: `CX_162.then` (the explosion sound) -> same chain -> `Montage_Play` C -> `CX_163` (the 1.6 s delay, then the sink):
  the arm convulses and collapses while it sinks. `--no-death` skips this part.
Every new node sits on y = 9500; `--revert` removes them and relinks the two chains. The script stops if a node name is
missing (then send i5 a fresh export; request filed on #25).

## Steps (Master, editor idle, not in Play)

1. `git pull`. If the #457 slot fix is not applied yet: `py handoffs/tentacle-anim-457/fix_pp_input_ue.py --dry-run` then `--apply`
   (without the slot no montage shows on the tentacle).
2. `py handoffs/tentacle-anim-457/import_cannon_ue.py --dry-run`, then without: 3 clips (96 / 96 / 144 frames, 24 fps) +
   3 montages in `Environment/Tentacles/Rig/Polish457/`.
3. `py handoffs/tentacle-anim-457/wire_cannon_ue.py --dry-run` (two `WOULD add` lines), then `--apply`: every `exec` True,
   `compile True`, errors `[]`. Save all.
4. Play: fire a cannon at a tentacle.

## Tests

- A cannonball hit: the arm snaps and whips at once (no delay), rears, thrashes twice, shudders, settles back into the sway
  in about 4 s; A and B alternate at random. The plasma burst, HP and the sword-hit wobble are unchanged.
- The killing hit: the arm convulses three times, stiffens with a tremor, folds over and collapses while it sinks.
- Hits during a strike (FABRIK) blend over it; if the strike aim looks off during a reaction, lower the montage blend in
  `AM_Tentacle_CannonA/B` (slot weight) and tell me.
- Too strong or too weak: one number, `amp` in `gen_cannon.py` (0.75 / 0.6 now), re-run steps 2.

Revert: `wire_cannon_ue.py --revert`. Rules: INDUSTRY_SECRETS 0.8, 3.4 #5 (no pops except the impact itself), RESEARCH.md
(#449): anticipation before the thrash, overlap along the arm (25 ms per segment), the mass keeps going on impact, a long settle.
