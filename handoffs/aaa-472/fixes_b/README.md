# #472 fix B: zombie deaths blend inside ABP_Zombie, hit reacts by side (i5 for i9). Paste AFTER crowd fix A

This is the corrected problem 3. `ABP_Zombie` already exists (blend space -> DefaultSlot -> output), so there is no new AnimBP.

**Pre-checked:** merge Validation OK on fix A's output; `fix_impure`; `check` OK; 0 PlayAnimation, 0 SetPlayRate, 0 SetPosition left in the graph; `make_death_montages_ue.py` ran on i5 in a temp folder (12 montages, no auto blend out, blend in 0.15, DefaultSlot) and `--revert` deleted them; the Montage_Play and SetAnimationMode signatures were read from the i5 editor.
**NOT checked:** never pasted, compiled or played. The look needs a Play check.

## What changes
1. **Death:** the 12 PlayAnimation calls dropped the zombie out of AnimBP mode with a one-frame pop. They become Montage_Play on `AM_ZDeath_*`, blended in over 0.15 s and holding the last pose. Same clips, same odds.
2. **WallBreaker:** it starts a PlayAnimation in its own BeginPlay, so it sits in single-node mode where a montage would not show. The death path first calls `SetAnimationMode(AnimationBlueprint, force = false)`: a no-op for all other zombies. Its death pose may still pop once, as it does today.
3. **Hit from behind:** when the causer is behind (dot < -0.25) the stagger plays ZA_Taking_Damage_C; otherwise the old random pick, minus C (that slot now plays B).
   - **Why C:** its hips jolt +17 on Y at the first sample, where mesh yaw -90 makes +Y the actor's forward. B, D, E, F jolt -8 to -24. This comes from sampled bone data only: **nobody has seen it yet**. If it looks wrong, it is a one-rewire change.

Left / right is not possible with these clips: they have almost no sideways hip motion.

## Steps (Master, not in Play, after fix A is saved)
1. `py handoffs/aaa-472/fixes_b/make_death_montages_ue.py --dry-run`, then `--apply`. Makes 12 assets in `Zombie/Anim/Death`.
2. Export fresh BP_Zombie (whole .T3D or EventGraph), then `python handoffs/aaa-472/fixes_b/build_472b.py <export>`. It must end `OK: paste ...`.
3. BP_Zombie > EventGraph: Ctrl+A, Delete, paste `zombie_b_merged.txt`. Compile, save. Check the 4 child classes compile.

## Test list (Play)
- [ ] Kill walkers, runners and a brute: the death blends in with no pop, and the body stays down until it disappears at 6 s (it must not stand back up).
- [ ] Kill a zombie mid-attack and mid-stagger: the death still plays.
- [ ] Kill a WallBreaker: its death plays.
- [ ] Risen soldiers die correctly (the knight mesh follows through leader pose).
- [ ] Gore: limbs still come off on kills.
- [ ] Hit from behind: the zombie jolts forward. Hit from the front: it recoils back.
- [ ] Log: no "Currently in Animation Blueprint mode" lines left, no new `Accessed None`.

## Revert
Paste the step 2 export back, compile, save. Then `make_death_montages_ue.py --revert`.

Rules applied (INDUSTRY_SECRETS): "zombie motion variation": clip variety kept, none of the 12 picks removed.

## Next: additive flinch for brutes (not in this fix)
Brutes have no hit reaction. An additive montage in DefaultSlot would stop their looping crawl, because their crawl is itself a slot montage in the same slot group. It needs a second slot in its own group in the ABP_Zombie AnimGraph, plus additive copies of the hit clips.
