# Outside-gate soldiers disappearing — evidence and reproduction

Owner report: soldiers died outside the gate to zombies spawned from scattered blobs. The bodies disappeared and did not rise. Whether another wave started afterward is unconfirmed.

Source reviewed: `handoffs/risen-soldiers-41/bp/gen41.py`, plus #149's installed-death-hook report. This is source evidence; the latest live director/soldier exports are still requested in #166.

1. **Confirmed source failure path, lines 347–390:** SpawnActor return feeds property setters, then `NextIdx++` and `RiseLeft--` without an IsValid branch. A null spawn consumes the record. `risen41_spawn_guard.patch` changes only that transition: invalid -> retry timer, valid -> initialization and eventual consumption. Five generated-graph reachability assertions pass. Do not paste the old regenerated director; merge the narrow guard against a fresh export.
2. **Timing contract, lines 281–328:** the director notices a later Wave, sets a per-wave quota, then only rises records whose FallenWave < LastWave and age >= RescueWindow (10 s default). Same-wave waiting can explain no immediate rise; it does not prove the reported disappearance is correct.
3. **Classification risk, lines 237–255:** the outside check uses hardcoded XY bounds x=0..4600/y=0..3450. A moved castle or a location visually outside the gate but inside this rectangle can be discarded. Compare actual death coordinates with the current castle bounds before changing this rule.
4. **Missing-world risk, lines 262–268:** ReportFallen reads Wave from a found manager without the valid-manager guard used by Poll. The new trace should reveal an Accessed None or wrong/default wave rather than silently treating it as a valid record.
5. **Navigation and presentation, lines 338–346 and risen BeginPlay/Rise:** nav failure falls back to the fall location +10 cm; the rise sinks the mesh then reveals a knight follower. Check grounded spawn location, visible/hidden flags, mesh offset, compatible skeleton/leader pose and PauseThink. A valid actor can still be invisible or underground.
6. **Rescue semantics, lines 288–314:** current commander rescue marks a record rescued when a living soldier is merely nearby during the window. It is not a confirmed carry-home action. Keep this separate from the ordinary soldiers' disappearance; change it only with the actual rescue adapter contract.

## Master reproduction

Run `collect_risen_diagnostics_ue.py` during PIE at three moments: before death; immediately after one sword/crossbow soldier dies outside to a blob-spawned zombie; and after the next wave plus the 10-second window. It reads current state and writes a unique JSON snapshot under Saved/CodexDiagnostics. It never starts PIE, modifies actors, changes assets or saves a game.

Trace one identity through: soldier death hook -> one director ReportFallen -> six parallel array lengths and appended entry -> Wave/LastWave change -> NextIdx/RiseLeft -> spawn return -> BP_ZombieRisen visible skeletal components and relative Z -> active AI. Keep on-screen footage of the body during the delay. Repeat sword, crossbow and commander, plus an ordinary non-blob zombie as the control.

Use breakpoints or temporary PrintString nodes in a separate reviewed adapter when snapshots cannot catch a transition. Verify the death hook is reached on **every** damage route before FallOut/destroy; being present on one graph branch is insufficient. Do not close #41 or claim the playtest bug fixed until this reproduction passes in game.
