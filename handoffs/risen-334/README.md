# #334 Risen soldiers: no more long neck (part A), no fading corpses (part B)

By `adjustedfilm (Claude)`, 2026-10-31. Owner `W:`: *"when soldier resurruct like zombie he has a very long silly neck?
when he dies he fades away? not raelistic"*.

## Part A: the long neck (here)

**Cause:** the #41 risen soldier shows the knight body on top of a hidden zombie and copies the zombie's bones 1:1
(Set Leader Pose). The two skeletons have different proportions, so the knight gets the zombie's neck length. The #41
README flagged this as its biggest risk.

**Fix:** retarget instead of copying, the same way the knight follower works (ABP_KnightFollow).
- **RTG_Zombie_to_Knight:** source is the zombie rig (IKR_Zombie_Src, already made for the Flesh Brute) and target is
  the knight's rig.
- **ABP_RisenKnight:** one Retarget Pose From Mesh node that reads the zombie it is attached to.

The knight keeps its own bone lengths and moves like the zombie.

### Steps (Master)

1. `py "<repo>/handoffs/risen-334/setup_risenneck334_ue.py" --dry-run`, then run it without `--dry-run`.
   - It makes RTG_Zombie_to_Knight (chains auto-mapped and auto-aligned) and an empty ABP_RisenKnight on the knight skeleton.
   - The log lists each chain mapping. A chain that shows `NONE` gets mapped by hand in the retargeter: a one-minute fix.
2. Open ABP_RisenKnight's AnimGraph. Paste `ABP_RisenKnight_AnimGraph.txt` (1 node), wire it to **Output Pose**,
   then compile and save.
3. `py ".../setup_risenneck334_ue.py" --finish --dry-run`, then run it without `--dry-run`. It sets BP_ZombieRisen
   `UseLeaderPose` = false and makes KnightMesh use ABP_RisenKnight. It compiles and saves.

Optional check: open RTG_Zombie_to_Knight and scrub any zombie walk. The knight should walk with a normal neck.

### Tests (Play)

1. Let a soldier die outside the walls, then start the next wave. He rises with a **normal neck and head**, in his own
   armour, and moves like a zombie.
2. Arms and legs don't twist. If the hands or fingers look odd, check the `chain` lines in the log.
3. No T-pose. A T-pose means step 2's wire to Output Pose is missing.

## Part B: corpses fading away

The fix is to make fallen soldiers stay down: they keep their ragdoll and settle, then sink slowly into the ground after a
while instead of fading, with a cap on how many bodies stay. This waits on export request "#334: export BP_ZombieRisen +
BP_SoldierSword", which shows where the fade happens.

## Part A v2 (2026-11-06): the retarget done right (`rt334_risen_fix_ue.py`)

Owner: *"soldiers that turned to zombies look so silly"*. Checked in a scratch copy of the project: the 10-31 setup mapped a
**6-chain** zombie rig (Spine, Head, arms, legs) onto the knight's **18 chains** with an unverified map and no alignment
(UE 5.3 had no `auto_align`), so the knight's neck, clavicles and hands were left to chance.

**Fix (one script, dry-run first):** `IKR_Zombie_Src` gets the same 18 chains as `IK_ShadowKnight` (neck, clavicles,
10 finger chains); `RTG_Zombie_to_Knight` is re-mapped (FUZZY) and **auto-aligned on both sides** (UE 5.8); the script
prints the map and stops if any knight chain is unmapped (in the scratch copy: **18/18**). It then re-asserts
`BP_ZombieRisen`: `KnightMesh` = Animation Blueprint / `ABP_RisenKnight`, `UseLeaderPose` default = false, compile, save.
`ABP_RisenKnight` keeps its Retarget Pose From Mesh node from 10-31.

**Proof:** the new zombie clips (#521) batch-retargeted onto the knight in the scratch copy: `preview/Risen_Walk_before_after.mp4`
and `preview/Risen_Idle_before_after.mp4` (knight pack clip | the shamble on the knight), `preview/Risen_Attack_threeqS_026.png`.
The knight keeps its own proportions: a normal neck, arms reaching, the crouch, no twist.

Steps (Master): `py "<repo>/handoffs/risen-334/rt334_risen_fix_ue.py" --dry-run`, then without `--dry-run`. Read the
`chain map` line (18/18). Play: let a soldier die outside the walls, next wave he rises in his armour and shambles like the
new zombies, normal neck and head, no T-pose, no twisted arms. If he T-poses, ABP_RisenKnight lost its Retarget Pose From
Mesh node (paste `ABP_RisenKnight_AnimGraph.txt` again, wire to Output Pose).
