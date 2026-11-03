# #472 crowd fix A: zombie registry, Think on caches, move guard, Delay guards, no-op cleanup (i5 for i9)

Built on i9's 11-03 20:05 exports (`handoffs/exports/adjustedfilm/faults-1205/`). **Those may be older than your graphs, so build on a fresh export (step 2).**

**Pre-checked:** `applyall merge` Validation OK on both graphs; `fix_impure`; `applyall check` OK; no node lost an exec input; every variable reference checked against the new-variable list and the live graphs. Variable script tested on i5 on a temporary copy.
**NOT checked:** the graphs have never been pasted or compiled, and nothing has been played. i5 can't do a whole-graph paste, and nobody was at the i5 screen to approve GUI control. Your compile in step 4 is the first real test.

## What the audit got wrong (read this first)
| ROADMAP said | The graph says |
|---|---|
| Zombies have no AnimBP | `ABP_Zombie` exists and is the mesh's anim class: blend space -> DefaultSlot -> output |
| 40 x PlayAnimation pop | 28 are orphans (dead code); 12 are wired, all on the death path. Attacks and stagger already use slot montages |
| The 678 "AnimBP mode" warnings come from PlayAnimation | They most likely come from the 12 `SetPlayRate` / `SetPosition` calls on the mesh, which log this and do nothing in AnimBP mode (from my knowledge of the engine source; not run) |
| Think scans farmers / zombies | Think scans **soldiers + farmers**, and looks up WM and gate. The zombie scans are in the WaveManager |
| 1 WaveManager scans per frame | **5** are placed, each scanned every frame; only the first one's NearGate was read |

Newly found: **SimpleMoveToActor runs in every Think**, so a synchronous path search + abort 4 x a second per zombie. It is probably dearer than the scans, but that is unmeasured until the profile arrives (#473).

GetAllActorsOfClass walks that class's instances, not the whole world (engine behaviour, from memory), so the old gate / manager lookups were cheap. The real costs were the zombie and soldier loops.

## Steps (Master, not in Play)
1. Back up: keep the fresh exports from step 2. They are the revert.
2. Export fresh `BP_ZombieWaveManager` and `BP_Zombie` (whole .T3D or EventGraph Ctrl+A / Ctrl+C), then:
   ```
   python handoffs/aaa-472/fixes/build_472.py <WM export> <Zombie export>
   ```
   It must end with `OK: paste ...`. If it stops on a missing node, a graph changed under the fix: send i5 the export, don't patch it.
3. `py handoffs/aaa-472/fixes/add_vars_472_ue.py --dry-run`, then `--apply`. It adds:
   - WM: RegHost, ZombieReg, SoldierCache, FarmerCache, GateCache;
   - Zombie: WMRef, LastMoveGoal, LastMoveAt.
4. BP_ZombieWaveManager > EventGraph: Ctrl+A, Delete, paste `wm_merged.txt`. Compile. Then BP_Zombie > EventGraph: same with `zombie_merged.txt`. Compile, save both. **WM first**: the zombie paste reads its variables.
5. Check that all 4 child classes compile: BP_ZombieRisen, BP_HalfHorseZombie, BP_RealmWasp, BP_ZombieWallBreaker.

## Test list (Play, wave 3+)
- [ ] Zombies spawn and the wave counts advance; a new wave starts when few are left. (ZombieReg drives the 45 cap and `Wave + 3`.)
- [ ] Zombies at the closed gate still damage it: GateDamage rises, the gate breaks. (NearGate now updates 4 x a second.)
- [ ] Zombies chase the player, turn to nearby soldiers and farmers, go back to the player when the target dies.
- [ ] A moving player does not shake them off (the engine re-paths a moving goal), and they don't stand idle while the player walks around them.
- [ ] Kill a brute during its gate slam and during its rise: the corpse no longer jumps or resumes.
- [ ] Log: the "Currently in Animation Blueprint mode" count drops from 678 to about 0 (CX_97 on death stays quiet, because the mesh is single-node by then); no new `Accessed None`.
- [ ] `stat unit` / `stat game` / `stat ai` at the same wave: put before / after in `handoffs/aaa-472/profile/` (#473).

## Revert
Paste the step 2 exports back into the two EventGraphs, compile, save. The new variables can stay, or `add_vars_472_ue.py --revert`.

## What changes (node level)
- **BP_ZombieWaveManager**
  - ReceiveTick removed. Its chain now hangs on the custom event RegNear (0.25 s timer, host only).
  - RegRefresh (1 s, host only) fills ZombieReg, SoldierCache, FarmerCache, GateCache.
  - WV_26, CX_1 and GT4 scans removed; WV_27, CX_2 and GT5 read the registry.
- **BP_Zombie**
  - BeginPlay caches WMRef and registers. New ReceiveEndPlay removes from the registry.
  - CX_502, zfQAllFarmer1, CX_398, CX_57, G_GetGate and CX_81 removed; consumers read the caches.
  - IsValid guard in both target loops. `IfMoveNeeded` in front of ZB28.
  - InitialStartDelayVariance 0.25 on ZB6 (fix 1; harmless if already applied).

**Decision:** a dead zombie stays in the registry until EndPlay, because the old count also included corpses (lifespan 6 s). This keeps wave pacing identical.
**Decision:** RegRefresh re-reads the world once a second, because HalfHorse, RealmWasp and WallBreaker override BeginPlay without calling the parent, so they never self-register. They do inherit EndPlay.
**Decision:** only the host runs RegNear. It is the manager GetActorOfClass returns, which is what BP_CastleGateControl reads. All 5 are not spatially loaded, so the host can't stream out; the gate IS spatially loaded, so it is re-read each refresh rather than cached once.

## Delay audit (problem 4)
A Delay on a destroyed actor is dropped by the engine, so the risk is only the corpse window (6 s lifespan).

| Delay | After it | Action |
|---|---|---|
| CX_53 (2 s) | rate change on the corpse | **guarded** |
| CX_434 (5.4 s) | rate change, then Attacking off | **guarded** |
| CX_448 (2.8 s) | emitter + 207 uu teleport, a corpse jump | **guarded** |
| CX_92 (2.4 s), plus CX_78's else | emitter Deactivate must still run; then rate change | **guarded after Deactivate** |
| CX_25, CX_77, ZB41 | already check Dead | none |
| ZB51, ZB86, S_Wait | clear flags, then ZB10 checks Dead | none |
| CX_565 (0.9 s) | death dust, meant to run on the corpse | none |

Guards rather than timers: same logic, far less rewiring.

Rules applied (INDUSTRY_SECRETS): none; this is logic, no visual change.

## Not in this fix (next)
- Death still uses PlayAnimation (pop, leaves AnimBP mode): montage step.
- Directional / additive hit reacts.
- Significance (Think rate by distance).
