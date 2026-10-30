# Master acceptance — record actual results

Status at handoff: all editor/game checks below are **NOT RUN**. Offline results are in test-report.json.

## Isolated compile and hearing checks

1. Create variables and paste all three graphs at the exact documented paths. Record engine version and Compiler Results for WORLD, SOURCE and LISTENER. Refresh unresolved custom-event call nodes once after events are registered. All must compile without errors.
2. In a temporary test level, place one manager and test actors with source/listener components. Disable Tick. Assign World references; call listener ResetInvestigation after binding. Drive events from a temporary test actor or existing test harness. Runtime calls must execute in PIE, not editor Python.
3. Bell source Kind=0 emits at world origin. Listener Evaluate(true, (1000,0,0)) immediately: HasGoal=true, GoalPosition=(0,0,0), Changed=true. Second evaluation: same GoalId, Changed=false. At six seconds memory expires.
4. Crossbow Kind=3 at origin: fresh listeners at 300 cm hear it, at 1000 cm do not. Bell at exactly 12000 cm has zero score. Test elevation as well as horizontal distance.
5. Listener first evaluated at 0.51 s after a pulse must not acquire it. A listener evaluated outside range and then moved inward must not replay that pulse. An already-heard pulse may be remembered after 0.5 s until its memory deadline.
6. Two bell emits on the same source without six seconds between: only the first accepted. A rejected global-cap/disabled-manager event must not consume the source's cooldown.
7. Exercise manager cap using a test harness (direct Emit is allowed **only for this test**): 28 ordinary sounds in one fixed window accepted; next ordinary rejected; four bells accepted; fifth rejected. On a new one-second window accepts again. After 100+ total accepted emits, every queue array length is exactly 32 and no index warnings occur.
8. A weaker sound cannot replace the current goal. A >25% stronger new sound can replace it after one second, but not before. Equal candidate scores choose the newest serial. Combat reset consumes old sounds. Arrival clears memory.
9. Rain=1/Fog=1 gives scale 0.4875. Horizontal wind normalized toward +X with strength=1 extends +X range and shortens -X. Zero or vertical-only wind adds no range bias. Changing weather does not change an already-stored pulse.
10. Missing World produces no Accessed None; empty queue no array error. Enabled=false clears listeners. A client manager cannot emit/drive hearing. Travel/spawn creates fresh state and uses the correct world's manager.

## Full feature tests after fresh-export adapter

- Bell draws free chasers toward a reachable kill zone, without hijacking gate attacks, melee, charge, climb or death animations.
- Cannon emits on successful shots; rejected/reload shots do not. Crossbow remains quiet. One sword swing emits once even if it hits multiple enemies. Fire crackles obey the two-second cooldown.
- Navigation failure, disconnected nav islands, stacked floors and unreachable bell positions return to ordinary chase. No constant path restarts, stale callbacks or stopping someone else's movement.
- Combat/death/climb transitions clear hearing-owned movement immediately. Returning to chase cannot replay an old bell.
- Existing sleeping guards wake only if audible and through their existing state API.
- Ground/minimap rings match actual ranges, remain readable, expire and respect the chosen pooling cap. Apply the October 30 realism rules and record which are relevant.
- Compare AI decision time and movement behavior at target crowd sizes on the owner's actual hardware. The 32-slot bound is not an FPS guarantee. Record a capture and profiler evidence.

Attach compiler output, test results, game screenshots/video and relevant fresh export paths to the handoff. Keep #48 open if any full-feature check remains incomplete.
