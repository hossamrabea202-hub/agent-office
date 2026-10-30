# #48 Blueprint sound-lure conversion — hearing core v2

From: Codex. Target: Master. Date: 2026-10-30.

**Ready for isolated editor compile/review; NOT installed or Play-tested.** This replaces the native hearing core of parked handoff #122 with three Blueprint graph pastes. No C++ module, runtime Python, paid asset or project conversion is required. Runtime graphs are supplied, not just a behavior specification.

The full #48 feature is still open: live movement/emitter wiring, sleeping-guard wake, ground/minimap indicators and game acceptance require fresh project contracts and editor integration. Request [#160](https://github.com/hossamrabea202-hub/agent-office/issues/160) covers them. This package does not silently turn a hearing target into a movement command.

## Files

From a current repository checkout, run `powershell -File handoffs/sound-lure-48-blueprint-v2/UNPACK.ps1`. It verifies the ZIP hash and extracts into a new `unpacked` directory. All files below are inside that archive; the documentation is also readable directly in GitHub. The ZIP supplied in the Codex chat contains the same files and can be extracted normally.

- `BP_NoiseWorld48_EventGraph.txt`: shared, bounded sound queue; Actor.
- `BPC_NoiseSource48_EventGraph.txt`: per-emitter cooldown; ActorComponent.
- `BPC_NoiseListener48_EventGraph.txt`: hearing, memory, selection and interruption; ActorComponent.
- `VARIABLES.md`: exact variable types/defaults, including the manager reference.
- `create_assets_ue.py`: optional new-assets-only setup; preflights APIs and refuses an existing destination. Does not paste graphs or alter any existing Blueprint.
- `INTEGRATION.md`: source provenance, current-export gate and movement ownership contract.
- `ACCEPTANCE.md`: isolated editor checks followed by in-game acceptance.
- `build48.py`, `kit.py`, `program.json`: reproducible graph source and machine-readable specification.
- `test48.py`, `test-report.json`, `graph-counts.json`: offline graph execution/structure checks and their scope.

## Master installation — manual route works without variable-creation Python APIs

1. Create a **new** folder `/Game/Codex/Noise48_BP_v2`. If it already exists, stop and inspect; do not overwrite a prior install.
2. Create Actor Blueprint `BP_NoiseWorld48`, then ActorComponent Blueprints `BPC_NoiseSource48` and `BPC_NoiseListener48` in that folder. Paths and names must match exactly because the pastes reference the generated manager class.
3. Create every variable from `VARIABLES.md`, with the listed type/default. `d` values are double precision, not single precision. Keep Private OFF. Leave all arrays empty and object references None. Compile the shells. In Class Defaults disable **Start with Tick Enabled** on all three; there is no Tick event.
4. In the empty manager EventGraph paste the complete contents of `BP_NoiseWorld48_EventGraph.txt`. Compile, inspect Compiler Results and save. Then do SOURCE, then LISTENER. Preserve all supplied custom event names and inputs. These are custom events with **no latent nodes**: subsequent caller execution reads the resulting properties synchronously.
5. If a self custom-event call is unresolved on first paste, compile to register events, Refresh All Nodes, then compile again. Any remaining error is a failed acceptance gate: send the Compiler Results and graph export to Codex before connecting game logic. Do not accept a graph just because it pasted.
6. Conduct the isolated tests in `ACCEPTANCE.md`. Only then attach components and connect live game graphs using the fresh exports and the Master-reviewed adapter.

Optional: on engines exposing the required variable APIs, run `runpy.run_path(r'<package>/create_assets_ue.py', run_name='__main__')` instead of steps 1–3. The documented UE5.3 Python API does not expose all of these APIs; the script reports this **before creating assets** and directs you to the manual route. It never guesses that a missing variable was created. It saves only its new shells. A later failure can leave a new partial folder for inspection; no automatic deletion is performed.

## Runtime contract

Place exactly one manager in the persistent gameplay level. Inject that same `World` reference into each source/listener at spawn/setup. Do not call GetAllActors per Think. Rebind after travel; on listener binding call `ResetInvestigation` so pre-registration sounds are discarded. A manager reference is intentionally explicit to avoid accidentally selecting another world's singleton.

**Source:** one component per physical emitter and kind. Set `Kind`, then call `EmitNoise(Location)` after an action actually succeeds. Read `Accepted` immediately afterward if presentation needs it. Reusing the component preserves cooldown. Do not call manager `Emit` directly from gameplay or recreate the source on every shot. No callback runs within emission; cosmetic work belongs after the source returns, preventing recursion.

**Listener:** call `Evaluate(Allowed, Position)` from the existing normal-chase decision, nominally every 0.25 s. Position is the zombie's current world location. Read `HasGoal`, `GoalPosition`, `GoalId`, `GoalUntil`, `Changed`. These are a **hearing decision**, not pathfinding success. `Changed` is true only when a new sound is acquired during this evaluation. `ResetInvestigation` clears memory and consumes current queue serials. Call it on combat/death/stagger/climb/AI-disable transitions, arrival or failed/unreachable navigation. Do not call it every normal Think.

**Priority:** gate attacks, melee, charging, climbing and other existing explicit orders win. `Allowed=false` clears the listener. No graph changes actor Owner, attack targets, wave counts, movement or save data. The adapter owns movement and must not keep chasing a stale hearing goal after HasGoal becomes false.

| Kind | Integer | Radius (cm) | Memory (s) | Cooldown (s) | Salience |
|---|---:|---:|---:|---:|---:|
| Bell | 0 | 12000 | 6 | 6 | 1.2 |
| Cannon | 1 | 8000 | 4 | 0.5 | 1 |
| Sword | 2 | 2200 | 2.5 | 0.5 | 0.6 |
| Crossbow | 3 | 600 | 1.5 | 0.5 | 0.25 |
| Jelly fire | 4 | 1800 | 2.5 | 2 | 0.45 |

These are inherited first-pass tuning values, not measured gameplay balance.

The manager stores at most 32 pulses in parallel arrays. One-second **fixed windows** accept at most 28 ordinary emissions and 32 total, reserving capacity for bells. This is not a rolling-window guarantee. The 33rd retained pulse overwrites the oldest slot. An acquired listener goal is copied, so later buffer replacement cannot corrupt its memory. Rejected emissions do not consume source cooldown. Manager disable/non-authority rejects events; listeners also refuse a disabled/client manager. Data is runtime-local and not replicated or saved.

Listeners scan at most 32 slots per evaluation (128 slot checks/second at four evaluations/second, per zombie). They consume all observed serials even when out of range. Only sounds at most 0.5 game seconds old can be newly acquired; already-acquired memory persists to its deadline. A new sound must improve the captured score by more than 25%, and retargets are separated by at least one second. Equal scores prefer the newest serial. Arrival within `max(25, ArrivalRadius)` clears memory. The default is 150 cm. Serial overflow is guarded; after roughly two years at continuous maximum rate, a fresh world/session is required.

Set manager `Rain`, `Fog`, `WindToward`, `WindStrength` from the existing weather system. Rain/fog/strength clamp to 0..1; finite values are checked. WindToward is the horizontal direction air moves **toward**, normalized in the graph. Each pulse snapshots weather. Radius scales by `(1-.25*Rain)*(1-.35*Fog)` and up/downwind by up to -/+25%. Hearing distance is 3D. There is no wall occlusion simulation.

## Validation and provenance

Run `python build48.py`, then `python test48.py`. The tests execute the generated K2 node/link graphs through an offline evaluator, including pure-pin re-evaluation and array bounds. They also check serialized reciprocal links and variable references. The evaluator substitutes game time, authority and Unreal math; it **cannot verify Unreal reflection, paste/compile behavior, navigation or runtime performance**. The Master must verify those in the actual engine.

Derived from `handoffs/sound-lure-48-v1` (README blob `49931126de483c41ec0fb0c688f9c7b126904e03`). Serializer copied from the office's `tools/master/t81/kit.py`. Existing zombie anchor inspection was based on `handoffs/exports/laptop2/gameplay/BP_Zombie.t3d`, blob `2c840de2ac45b7719d691793a78ce3e5f99382db`, captured 2026-10-28. **No existing game graph patch is included** because that export predates current work; #160 requests the new one.

This package adds no materials, textures, meshes, camera changes or VFX. The October 30 realism rules remain mandatory for the later indicator pass; none are claimed as visually tested here.

API checks: Epic documents [custom event calls](https://dev.epicgames.com/documentation/unreal-engine/custom-events-in-unreal-engine), [Array_Set](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Kismet/UKismetArrayLibrary/Array_Set?application_version=5.5), [Vector_Normal2D](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UKismetMathLibrary/Vector_Normal2D), and the limited [UE5.3 BlueprintEditorLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/BlueprintEditorLibrary?application_version=5.3). The normalizer is **Vector_Normal2D** with a single-precision Tolerance pin; `Normal2D` is a different function. Current API pages are not proof of compilation in the project's engine version.
