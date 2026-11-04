# #500 Moving the hot spots to C++: the transition kit (i5, written ahead, NOT compiled yet)

Written by checkking on i5 while the owner installs Visual Studio Community. **Nothing here is compiled or tested**: i5 has no compiler yet.
Expect a few compile errors on the first build; send i5 the full Output window text and it fixes them. Plain words first, details after.

## What C++ gives us, and the file for each point
| # | Point | Files | What it does |
|---|---|---|---|
| 1 | Speed in per-frame loops | `ZombieBase.*`, `CrowdSubsystem.*` | Zombie target pick (2 loops per zombie per Think) native; one crowd manager for collision tiers and "zombies near here" |
| 2 | Fewer broken pastes | `gitignore_for_project.txt`, this guide | C++ is text: git diff / review / merge. No more lost values or dead wires from graph pastes |
| 3 | One place for numbers | `CDSettings.h` | Project Settings > Game > Castle Defender (saved in Config/DefaultGame.ini); `FZombieTypeRow` for a zombie-type Data Table |
| 4 | Shared systems | `CrowdSubsystem.*` | One registry for zombies, soldiers, farmers: nobody needs GetAllActorsOfClass / WithTag again |
| 5 | Safe save games | `CDSaveGame.*` | Versioned save, step-by-step Migrate(), automatic `_bak` copy before every overwrite, never overwrites a newer save |
| 6 | Tests and profiling | `Tests/ZombieBrainTest.cpp`, `CDStats.h` | Automated test of the target rule; `stat CastleDefender` and named Insights scopes for our systems |
| 7 | Editor tools | `Source/CastleDefenderEditor/*` | `CDEditorTools.find_blueprints_with_errors`, `find_expensive_calls` (speed lint over every Blueprint graph) |
| 8 | Reuse instead of spawn | `CDPoolSubsystem.*` | Acquire / Release pooled actors (bolts, bursts, gore) + `ICDPoolable` reset hooks; Niagara/Cascade use PoolingMethod AutoRelease |

## Install and first build (i9; i5 too if possible)
1. Visual Studio Community 2022 or newer, workload **Game development with C++** (+ "Unreal Engine installer" and a Windows SDK if offered).
2. **Back up the whole project folder.** (The first C++ build turns it into a C++ project.)
3. Close the editor. Copy `handoffs/cpp-500/Source` to `C:\UnrealProjects\Castle Defender 5.8\Source`.
4. Open `CastleDefender.uproject` in a text editor and add the block from `uproject_modules.json` at top level (next to "Plugins"). Keep the JSON valid (commas).
5. Right-click `CastleDefender.uproject` > **Generate Visual Studio project files**. Open `CastleDefender.sln`, configuration **Development Editor | Win64**, **Build**.
   Errors: copy the whole Output window to `handoffs/cpp-500/build_log_<date>.txt`, push, tell i5.
6. Open the project. In the Output Log: `Automation RunTests CastleDefender` -> all green.
7. (Reviewer order: reparent a DUPLICATE first) `py <repo>/handoffs/cpp-500/reparent_zombie_ue.py --bp <duplicate> --dry-run`, then `--apply`; the real BP_Zombie only after the duplicate matches (backup, compile check, saves only without new errors).
8. Play: zombies walk, attack, die, gore, ragdoll as before (only their parent changed).
9. `stat CastleDefender` in Play shows Crowd Tick / Zombie PickTarget / Pool Acquire and the zombie count.

## Then, one system at a time (each: script with dry run + backup, measured before / after)
1. **Zombie target pick:** a graph_ops script replaces Think's two loops (CX_501 .. zfTargetFarmer17) with `PickAndSetTarget(SoldierCache, FarmerCache)`
   (needs the compiled class; i5 writes it after step 5). Later `PickAndSetTargetFromRegistry` when soldiers / farmers register (below).
2. **Registry:** BP_SoldierSword / BP_Farmer BeginPlay -> `Crowd > Register Soldier / Register Farmer`, EndPlay -> Unregister. Then the wave manager caches (fix A) can go.
3. **Collision tiers:** set `Crowd Manages Body Collision` in Project Settings, remove BPC_CrowdTier from BP_Zombie (C1). Same rule, one loop.
4. **Soldier fight loop:** an `ASoldierBase` C++ parent with the per-zombie checks of CX_145 native, fed by `GetZombiesNear` (replaces C3's sphere sweep). Needs TGA's SPEC_soldier.md.
5. **Numbers:** make `DT_ZombieTypes` (row struct ZombieTypeRow), point Project Settings > Castle Defender > Zombie Types at it, and let the wave manager read MaxHP / damage / speeds from it.
6. **Pools:** crossbow bolts, soldier bolts, BloodBurst: Acquire / Release instead of SpawnActor / SetLifeSpan; Niagara / Cascade spawners PoolingMethod AutoRelease.
7. **Saves:** move the game's save to `CDSaveSubsystem` (LoadOrCreate / Save). Keep the old save readable until every player has migrated; never delete the owner's save.

## How the team works after the switch
- **Only C++ changes need a restart.** Blueprint, level and asset edits still go live through Multi-User as today.
- After a C++ change, whoever compiled it shares `Binaries/Win64/*.dll` + `*.modules` + `Source/` + `.uproject` (sync zip, as with assets). Every editor closes, copies, reopens.
  Everybody must run the same build, or the project will not open (it asks to rebuild).
- C++ hand-offs from agents arrive as text diffs in `handoffs/`, with a build log from a machine that has Visual Studio. i5 can only pre-check C++ if Visual Studio (or the free Build Tools) is on i5 too.
- Tuning numbers move to Project Settings / Data Tables: change them there, not in graph literals.

## Risks
- First build: expect small API differences (UE 5.8): fixed in minutes from the log.
- Reparenting BP_Zombie: same parent chain (Character -> AZombieBase -> BP_Zombie), variables keep their values; the script refuses to save if new errors appear.
- Pools: a pooled actor must reset itself (OnAcquired); anything with timers or Delays must be checked before pooling it.
- Saves: version 1 starts now; the current Blueprint save stays as is until step 7.

## Files
`Source/` (copy as is) · `uproject_modules.json` · `reparent_zombie_ue.py` · `gitignore_for_project.txt` · `dump_BP_Zombie.txt`, `dump_BP_FleshBrute.txt` (live brains, 11-04) · TGA writes `SPEC_zombie.md`, `SPEC_soldier.md`.

## Review fixes (external review via Alien / i9, card #500 comment 6635467285), done 11-04 by checkking
| Review item | Fix |
|---|---|
| C1 `Super::Tick` | removed; registry purge + stats now only every UpdateInterval, not every frame |
| C2 pool delayed release race | per-actor record (Active / PendingRelease / Pooled) + generation number + stored timer handle; a timer parks only its own generation; duplicate release and other-world actors rejected with a warning; invalid entries purged before capacity checks; GetPooledCount counts valid only |
| C3 SetOwner as target | `CurrentTarget` (UPROPERTY, BlueprintReadOnly + getter); `bAlsoSetOwner = true` only for the transition (BP_Zombie still reads GetOwner). No-player rule is a setting `bZombieNoPlayerBlocksTargets` (default = Blueprint parity); TGA's spec decides |
| C4 save backup | serialize + verify in memory, write `_tmp` + read back, copy the current main byte-for-byte to `_bak` only if it is valid and abort if that fails, write main + verify, delete `_tmp`; newer-build saves load read-only and are never overwritten; Migrate steps idempotent |
| C5 pool reset | reset contract on ICDPoolable; classes without it are never pooled (Acquire spawns, Release destroys); the pool also clears timers, life span, movement and physics velocity |
| Crowd collision on death | remembers each zombie's own collision setting and restores it on death / ragdoll / unregister / switch-off; never touches a mesh that simulates physics. (BP_Zombie's death path sets the Ragdoll profile itself, so C1 in Blueprint is also safe for ragdolls) |
| Missing Dead = alive | `IsDeadForCrowd()`: the BP bool if the class has it, else "being destroyed"; overridable |
| Engaged flag | isolated in `IsEngagedForCrowd()` (still CustomTimeDilation != 1 for parity; replace with an explicit state) |
| Arrays per pick | `PickAndSetTargetFromRegistry` iterates the registry directly (ForEachSoldier / ForEachFarmer), squared distances |
| Settings validation | ClampMin / UIMax on every number, Mid >= Near enforced; tooltips say [used] or [not wired yet]; `MaxAliveZombies` read by `Crowd > Can Spawn Zombie` |
| Editor error scan | optional real recompile (`bRecompile`) |
| Build checks | direct includes in CDEditorTools.cpp; UCDPoolable Blueprintable; BuildSettingsVersion.V5 and EngineIncludeOrderVersion.Unreal5_5 pinned |
| Registry checks | `cd.CrowdReport` console command: registered vs in-world zombies, soldiers, farmers; stat counters |
| Tests | target edge cases (invalid, dying, exact range, exact height, ties, no player both rules); save path (missing, corrupt main -> backup, corrupt backup never wins, newer never overwritten, repeatable migration). Pool and PIE tests listed in the test file, need a world: added after the first build |
| Reparent: "BeginPlay must call parent" | not needed for the registry: AZombieBase registers in its native BeginPlay / EndPlay, which always run before / after the Blueprint's Event BeginPlay / EndPlay |

Still NOT implemented (designed only): alive cap enforced in spawners (needs the wave manager to call Can Spawn Zombie), DT_ZombieTypes loading, Think divisor applied in BP, soldier / farmer registration in their Blueprints, native collision parity test, save migration steps, pooled spawners, runtime / PIE integration tests.
Order (reviewer's, agreed): 1 build Runtime + Editor, UHT clean, tests green, BEFORE any reparent; 2 zombie brain on a DUPLICATE of BP_Zombie, compared with the original; 3 registry; 4 saves + pools; 5 profile each step.

## Revision 3: second review (11-04) fixes
| Review item | Fix |
|---|---|
| A newer saves overwritten by a fresh object | Save() reads every copy of the slot on disk (main / _tmp / _bak) first and refuses if any is from a newer build; read-only is now per slot |
| B _tmp never recovered | written recovery rule: among VALID copies take the highest Sequence, tie main > _tmp > _bak; _tmp wins only when its commit did not finish |
| Valid vs merely deserializable | every file is an envelope: magic, format, sequence, CRC32, length, payload; old plain saves still read (sequence 0) |
| F Save() skipped Migrate | Save() calls Migrate() before serializing |
| C death vs collision ownership | AZombieBase::NotifyDying() (call at the start of the death transition) and automatic hand-off when Dead / ragdoll is seen: the crowd forgets the zombie WITHOUT restoring; it restores only alive zombies and only its own NoCollision |
| D pool component ticks / movers | on release the pool records and turns off every component tick and deactivates active movement components; on acquire it restores exactly those, then OnAcquired |
| Park() held a record pointer across map changes | record looked up again after PurgeInvalid / OnReleased; Acquire never holds it across OnAcquired |
| E IsDeadForCrowd edge case | destruction / NotifyDying / BP Dead: any of them = dead |
| CurrentTarget | weak reference + IsValid-checked getter |
| GetZombiesNear negative radius | returns nothing for radius <= 0 or NaN |
| .ini values | clamped in code (target rule, crowd), not only in the editor UI |
| Editor recompile | documented: changes in-memory Blueprints; run on a clean editor |
| Tests | null-safe pattern everywhere, unique slot name per run (GUID), new cases for A, B (3 recovery orders), F, CRC flip, per-slot read-only, sequence after recovery |
Still open (reviewer's list): wiring CanSpawnZombie into every spawner, soldier / farmer comparison in cd.CrowdReport once their classes have C++ parents, pool + PIE integration tests (delayed release and component-tick tests first), schema validation beyond CRC. Not compiled yet.

## Revision 4: third review (11-04) fixes
| Review item | Fix |
|---|---|
| 1 failed save recovered later | backup failure now ROLLS BACK: _tmp is deleted, Save returns false, nothing committed, main untouched. Only a failed final main write keeps the verified _tmp, documented as recoverable progress |
| 2 header sequence not verified | CRC32 now covers the header fields + payload, and the header sequence must equal the save's own Sequence, else the file is Corrupt |
| 3 future format could be overwritten | file status enum: Missing / Valid / Corrupt / UnsupportedFormat / NewerVersion. UnsupportedFormat and NewerVersion make the slot read-only; Save refuses to overwrite them (checked on disk every time) |
| 4 pool reentrancy | no FRecord reference is held across Activate / Deactivate / tick changes / OnAcquired / OnReleased: state is built in a local FParkedState, the record is looked up again and its generation checked after every call-out; if a callback re-acquired the actor during parking, the pool undoes its own component changes and stops |
| 5 actor-level state | the actor's own hidden / tick / collision values are remembered when parked and restored on acquire; OnAcquired runs while hidden and without collision; collision is turned on LAST |
| 6 death integration | documented below (BP_Zombie requirement + test) |
| Timers | contract now says: the pool clears only timers bound to the actor object; OnReleased must clear timers set by components or other objects |
| Tests | future envelope format protected and bytes unchanged; header / payload sequence mismatch; flipped header byte; rollback case documented as a manual check (needs a failing file system) |

### BP_Zombie death-path requirement (for the native crowd collision rule, `bCrowdManagesBodyCollision`)
The crowd hands the body collision back without restoring it as soon as a zombie is dying or dead. So BP_Zombie's death code must set the mesh
collision it wants itself, on BOTH paths, and should call `Notify Dying` first:
- ragdoll path: already does (`SetCollisionProfileName(Ragdoll)` + `SetAllBodiesSimulatePhysics`, nodes K2Node_CallFunction_23 / _24);
- non-ragdoll path (death montage): today it only calls `SetCollisionEnabled(NoCollision)` (K2Node_CallFunction_ZB71, after Set Dead). If corpses must
  stay hittable (gore on corpses), add an explicit mesh collision set there.
Test before turning `bCrowdManagesBodyCollision` on: kill a far, unseen zombie (its body collision is off) with both death types; the corpse behaves
like one killed up close.

### Integration tests to write after the first build (need a world; reviewer's list)
Pool: delayed + immediate release + reacquire; duplicate release; destroyed while pending; cross-world; capacity; OnReleased destroys; a callback in
OnComponentActivated / Deactivated that calls back into the pool; a projectile that starts with collision disabled keeps it disabled after reuse;
an external timer firing after reacquisition. Crowd: zombie dies while its body collision is off. PIE: register, pick target, unregister, no stale ref.
