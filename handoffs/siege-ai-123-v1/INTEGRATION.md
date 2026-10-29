# Integration contract and acceptance

## Install source

Master copies `SiegeCoordinator123` to a new `Plugins/SiegeCoordinator123` directory, builds the actual game's Editor target and enables it. Never overwrite another version. If the project is Blueprint-only and native builds are unavailable, report that in #124 before attempting conversion. This handoff does not authorize replacing toolchains or mutating existing gameplay blindly.

Create a server-owned manager with SiegeCoordinator123 component. Register objectives through actor BeginPlay/EndPlay and state-change events; register squad snapshots through spawn/death/group events. No GetAllActorsOfClass on Tick. `PutSquad` updates existing native records; Python `add_squad` only creates records and tests update its input fields directly. Submit live centroid, member count, role, combat and NoiseUntil. Zero living members => RemoveSquad. RemoveObjective on destruction; publish an independently verified breach if appropriate.

Call Plan(game time,32) once every0.25s. It returns only the squads processed in that slice. Cache other decisions until their next revision. Native DesiredStagingPoint keeps objective Z; Python's 2D reference only records XY. The adapter must validate actor identity/generation and nav reachability immediately before acting, because the world may have changed after Plan.

## Movement priority and ownership

1. Death/disabled/stagger state owns the pawn; release siege membership/assignment as appropriate.
2. Existing close combat and gate attacks retain priority. The coordinator does not interrupt them.
3. Active #48 hearing investigation owns the normal-chase fallback. Set squad NoiseUntil from accepted hearing state. Do not copy a stale unexpired event blindly to the whole horde.
4. If no higher-priority action: siege Approach or Queue may supply a projected staging destination.
5. No valid siege goal => existing normal chase.

The prior zombie export's normal chase wire is `G_AtGate.false → K2Node_CallFunction_ZB28` (SimpleMoveToActor), after the attack/gate branches. #48 already proposes insertion at this wire: use one adapter that arbitrates hearing then siege, not two independent rewires or concurrent movement issuers. Do not overwrite Actor.Owner, which currently holds the combat target.

Project desired staging positions with the correct nav agent; require a complete path. Offset individual squad members into tested formation slots around the projected squad location; never issue every member the same point. Use a minimum goal displacement/revision threshold and preserve an active owned move. Report path failure immediately, and distance-to-projected-goal at a bounded cadence. A queue request should move once to a valid waiting location and then hold, not restart its path each planner call. ReportProgress describes active approach progress only. Submit Combat=true before combat starts so slots release on the next planning service; adapter can remove/reinsert the squad if immediate release is required.

Role capabilities are not implied by enum names. Runner charge requires #23's actual action/cooldown; heavy breach damage uses the existing damage interface; climber movement requires a working link/action with safe completion/failure. Set LinkReady=false until that functionality is verified. Never use a staged point to teleport through a wall.

## Pacing bridge

Add SiegePacing123 only in an isolated test map first. Do not run two wave spawners. StartRun(quota,aliveCap,gameTime,seed) consumes input from the current authoritative wave manager; it refuses a new run with active tickets or registered live actors. Sequence IDs remain monotonic within the component. Existing quota/count fields must be mapped explicitly from #124; do not infer a new save format.

Advance produces advisory tickets. Check role capability and a valid reachable spawn site; unsupported role => FailedSpawn(ticket), not silent actor substitution. Spawn on server, then ConfirmSpawn(ticket,unique lowercase actorId,gameTime). If confirmation returns false, the adapter must not admit the actor: remove/recycle the just-created candidate through the game's normal safe spawn-cancel path. Never give rewards/drops for rejected spawn candidates. Ticket expiry is3s. Pending and alive share cap; failed/expired tickets refund once. For a synchronous spawn path, verify the ticket then spawn+confirm in one frame. For async assets, load first, request tickets only when ready.

ReportDeath once from the authoritative zombie death/despawn lifecycle (duplicate reports are safe). Missing reports prevent completion; use actor EndPlay cleanup rather than clearing accounting arrays. ConfirmSpawn cannot resurrect a consumed ticket. Check float time uses the same world game clock. Pause must stop both director time and movement tracking.

Pressure input is a normalized live metric supplied by the game. Proposed initial mapping, subject to playtesting: weighted nearby combat population, recent player damage and gate danger; clamp0..1, smooth over2s. No player-adaptive difficulty is silently added until owner/Master reviews this metric. For initial tests provide a controllable debug slider.

## Acceptance before #123 completion

- Build/UHT/plugin load succeeds on actual UE version; record engine version/logs.
- Replay the reference decision scenarios through native components: matching target, slot, action, role and reservation accounting (allow float tolerances and XY/Z contract differences). Python unit tests are not this parity check.
- Test32+ squads against gate, wall, breach and a real climb link. Log objective IDs/reasons; confirm deliberate role choices and stable assignments.
- Destroy/rebuild a gate while a queue approaches; no stale generation, deleted actor or invisible target is used.
- Attack and bell interactions never fight over MoveTo or Actor.Owner. Death/stagger frees membership/queue capacity.
- Close a climb link, block a corridor and remove an objective. Units replan or use existing fallback; none teleport or remain stuck indefinitely.
- Formation projection avoids overlapping targets at narrow entrances and on uneven terrain. The reference only tests queue accounting, not physical crowd avoidance.
- Verify source/target contention and queue fairness at the maximum actual game population. Profile native coordinator, navigation, animation and rendering separately on target hardware.
- Spawn failures, async expiry, duplicate callback, duplicate actor ID, actor EndPlay and wave restart preserve budget/cap invariants; no duplicated enemies or rewards.
- Recovery pauses new reservations; current fighting enemies remain active. No mass despawn or hidden health changes.
- Multiplayer if applicable: only server mutates coordination/spawning; clients receive presentation only. No save changes from this module.
- Provide PIE video/screenshots and timings. Keep the feature opt-in until these pass.
