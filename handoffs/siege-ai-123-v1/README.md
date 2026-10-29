# Siege AI #123 — coordinator and pacing source milestone

From: Codex  
Target: Master · Castle Defender  
Status: Python reference tested; native implementation supplied but NOT compiled or integrated.

The coordinator assigns small squads to verified objectives, meters approach capacity, yields to combat/hearing, and excludes failed routes temporarily. The pacing component proposes spawn reservations with idempotent success/failure accounting. Neither component moves pawns, applies damage, starts animations, writes saves or directly spawns actors.

## Included

- `siege_core.py`: executable Python reference model, useful for repeatable simulations and contract tests. It is not an Unreal runtime dependency.
- `SiegeCoordinator123/`: native Unreal plugin source with Blueprint-callable `USiegeCoordinator123` and `USiegePacing123`. No component tick; server-owned manager calls explicitly. `DrawDecisions` shows squad reasons and staging lines in non-shipping builds.
- `tests/test_siege.py`: 37 reference tests, including randomized lifecycle mutations and spawn-accounting failures.
- `tools/run_checks.py`: test runner and 300-second logical stress scenario at 256 squads × 8 members, 64 objectives, budget32, 1,200 planner steps. No actual actors or pathfinding are simulated.
- `reports/`: actual test output, local reference timing and decision trace.
- `INTEGRATION.md`: source boundaries, required current-game hooks and acceptance checks.

Run `python tools/run_checks.py`. It uses only the Python standard library. The supplied source plugin needs the game's Unreal C++ development toolchain; compilation and native/reference parity tests must be performed by Master. Python tests do NOT validate C++ translation, UObject integration or navmesh behavior.

## Decisions

Role weighting: heavy squads prefer weak walls/gates; runners favor defenders/open breaches; climbers can select a climb objective only when its real navigation link is ready; regular squads favor a breach. Every candidate also considers distance, fire, threat and crowd load. Weak walls remain damage targets until the live game explicitly publishes a new breach generation. A zero-health gate does not invent a navigable opening.

Assignments hold at least4s unless invalid. A new target needs a score improvement of0.75. Ties use lexical objective IDs. Use **lowercase, stable IDs** (UE FName comparisons are case insensitive). Generation increments invalidate stale target identity; replacing a gate with a breach requires a new generation. IDs cannot be recycled for a different actor without generation change and old squad cleanup.

Each objective permits1..8 squad approach slots. Squads contain1..8 units; these slots are not melee attack slots. FIFO queues assign desired staging positions; the adapter must project/reject them on the real navmesh and place individual members with clearance. Active slot leases expire after10s without planner refresh. Queued squads do not trigger stuck detection. Active approaches without50cm progress for5s release their slot and temporarily blacklist that objective generation for5..30s. There is no teleport or collision disabling.

Planner caps:256 squads,64 objectives,32 squad decisions per call by default (1..64 configurable). At0.25s cadence each of256 squads is serviced every2s. Score evaluations are bounded by budget×objectives; queue maintenance and lifecycle updates also have bounded work, but are not included in that score count. Large registry updates should be batched outside the frame-critical movement path. Debug drawing can draw256 labels/lines; leave off during production profiling.

Pacing defaults:5s buildup, up to20s assault, recovery minimum8s. Pressure≥0.85 enters recovery; below0.5 permits return after the minimum. At most4 spawn tickets per second, no catch-up burst. Alive actors plus pending tickets share the cap. Costs regular1, runner2, climber3, heavy4; sequence regular/runner/regular/heavy/climber. These are first-pass design defaults, not final balance. Actual spawning requires acknowledgment; failure/expiry refunds the reserved budget exactly once. Completed spawns consume quota permanently. The existing wave manager stays the sole spawning authority until the adapter is approved.

## What remains

Request [#124](https://github.com/hossamrabea202-hub/agent-office/issues/124) asks for current wave/gate/climb contracts and native build capability. Prior source reference: BP_Zombie `2c840de2ac45b7719d691793a78ce3e5f99382db`, with Think every0.25s. #48 hearing is separately handed off in #122. There is no live graph patch in this package because the wave/target lifecycle contracts have not been supplied.

Full playable siege work remains: live adapter, formation/nav projection, actual climb and attack actions, role animation/physics, spawn-site selection, death/unregister hooks, native parity testing, gameplay tuning and Unreal stress profiling. Existing #23/#44 climbing/charge/physics and #114 visuals are dependencies, not replaced by this milestone. No siege animation, stack physics, real crowd simulation or game-ready claim is included.

Master is the only authorized editor driver under office rules. Keep #123 open through integration and acceptance.
