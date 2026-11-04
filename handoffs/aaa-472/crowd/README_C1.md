# #493 C1: BPC_CrowdTier, zombie body collision only where it is needed (i5 for i9). Script, no paste

Why (measured on i5, `CROWD_PLAN.md`): the zombie mesh (body) collision is the biggest per-zombie cost. Switching it off beyond 15 m of the player and soldiers
(291 of 480 zombies) cut movement 62 -> 37 ms, physics wait 30 -> 8.5 ms, sync 8 -> 4 ms: **about -55 ms** of game thread. All of it off: about -92 ms at 314 zombies.

What it is: a new component `/Game/CastleDefender/Gameplay/Crowd/BPC_CrowdTier`, added to BP_Zombie. 4 times a second (start staggered over 0.25 s) it sets the zombie's mesh to
- **QueryOnly** (as now) if the zombie is on screen (rendered in the last 0.2 s), OR within 25 m of the player, OR engaged by a soldier (CustomTimeDilation not 1.0: soldiers mark their zombie 0.999);
- **NoCollision** otherwise.
Dead zombies are never touched, so ragdolls keep their physics. The capsule is untouched: zombies still block each other, the player, walls, and take capsule hits.

Who needs the body collision (from the exports): BP_Crossbow, BP_Cannonball, BPC_WeaponKit, BPC_CannonBreak, BP_SoldierSword, BP_HalfHorseZombie, BP_TentacleVitals read bone hits.
The player only hits what is on screen, and soldiers' targets are marked engaged, so those keep it. **Risk:** a weapon that hits an unseen, unengaged zombie farther than 25 m
(a cannonball fired at an off-screen crowd) hits the capsule, not the body: no bone, so no limb cut there. Check in Play.

Steps (editor idle, not in Play):
1. `py C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/crowd/crowd_tier_c1_ue.py --dry-run`
2. `py .../crowd_tier_c1_ue.py --apply --attach` -> makes and saves BPC_CrowdTier (expect `RESULT compile True | link/value failures [] | new errors []`),
   backs up `Saved/bak472/BP_Zombie.uasset.fixC1`, adds the CrowdTier component to BP_Zombie, compiles, saves.
3. Check first: BP_Zombie > Mesh > Collision Enabled is **Query Only** on your copy (it is on i5). If yours is different, tell i5 before step 2: C1 sets Query Only when "on".

Tested on i5:
- Built in temp folders (`/Game/_i5tmpC1z`): 21 nodes, compile True, 0 link failures, 0 errors, 0 warnings.
- Attached to a temp copy of BP_Zombie (`Zc1`): component added, copy compiles.
- **Not run in Play.** Python cannot add a component to a live actor or spawn actors into Play on i5, so the A/B with copies did not run.
  The rule itself was measured in Play by doing the same switch from Python (see Why).

Test (Play, editor in front, forced wave, camera at the gate):
- Shoot zombies on screen with crossbow and cannon: hits, head shots and limb cuts as before.
- Soldiers fight zombies off screen: kills still happen (turn the camera back and look).
- Zombies die and ragdoll as before; corpses do not sink or freeze.
- Measure before and after: `py .../profile/measure_split_ue.py`; CSV groups CharacterMovement, EventWait/EndPhysics and SyncBodies should drop (`node profile/csv_split.js <csv>`).

Revert: remove the CrowdTier component from BP_Zombie and save, or close the editor and copy `Saved/bak472/BP_Zombie.uasset.fixC1` back over `Content/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.uasset`.
Tune: the 25 m (`2500`) and 0.25 s are pin values in BPC_CrowdTier's graph.
