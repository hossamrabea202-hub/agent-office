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
