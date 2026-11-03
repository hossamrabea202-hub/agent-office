# #450 / #457: the tentacles have probably been frozen in their ref pose; fix + hit reaction (i5 for i9)

## The bug
`ABP_TentacleStrikePP` is the tentacle skeletal mesh's post-process AnimBP, so it runs on every tentacle. Its Local Pose has **no Input Pose wired**, so it outputs the reference pose and throws away the idle clip.

**Measured on i5 (Simulate on the Entry map, a probe tentacle with the real mesh and clip):**
| Setup | seg_13 (tip) over 3 samples |
|---|---|
| post-process ABP on, as today | -4222, -15, 7458: **never moves** while the clip's position runs |
| post-process ABP disabled | -3929 -1275 7761 / -4370 32 7555 / -4424 933 7569: moves |
| fixed copy (Input Pose -> Slot -> Local Pose) | -4369 77 7574 / -4418 953 7601 / -3879 347 7302: moves |

So no idle clip has reached the screen while that ABP has been on the mesh, and i5's #457 polished clips couldn't have shown either. That may be what Alien saw as "subtle and boring" (#450, #457).
**Not checked:** the placed tentacles in the real map, or your copy of the ABP. Please look at one before step 1: if yours already sways, tell me and stop.

## Steps (Master, editor idle, not in Play). Python only, no paste
1. `py handoffs/tentacle-anim-457/fix_pp_input_ue.py --dry-run`: expect `Local Pose is linked to: NOTHING`. Then `--apply`: expect both links True, compile True, errors [].
2. `py handoffs/tentacle-anim-457/wire_hitreact_ue.py --dry-run`, then `--apply`: expect all links True, compile True, errors [], warnings []. Makes `AM_Tentacle_HitReact450` (needs `AS_Tentacle_HitReact450`; if the script says it can't load the clip, import it first: `handoffs/tentacle-anim-457/tentacle_anim_ue.py import`).
3. Save all, Play.

Both scripts ran on i5 on temporary copies with exactly these results. The hit montage also played in Simulate over the idle and handed back to it.

## Test list (Play)
- [ ] All 8 tentacles sway. If the sway is too big or clips into walls: step 1 `--revert`, and tell me.
- [ ] Strike still works: a tentacle reaches for soldiers / the cannon. The FABRIK now starts from the animated pose instead of the ref pose, so its aim may look different: this is the riskiest point.
- [ ] JellyShell follows the arm (leader pose).
- [ ] Hit a tentacle with sword / crossbow: recoil and lash-back over the sway, at most once per 2.5 s, blending back after 3 s. The old jelly wobble and spit still happen.
- [ ] Cannonball hits are unchanged (no reaction clip, by the existing branch).
- [ ] Log: no new `Accessed None`.

## Revert
`wire_hitreact_ue.py --revert`, then `fix_pp_input_ue.py --revert`.

## Not in this fix
The #457 polished clips are still not swapped in; that was left for Alien's OK. With the fix, Alien can now judge them for real: `tentacle_anim_ue.py swap --dry-run`, then `--apply`, reverts with `--revert`.

**Decision:** the hit reaction is the full clip in the slot, not additive: it is authored as a whole-arm motion. Strength is one value (AMP in `gen_react.py`).
