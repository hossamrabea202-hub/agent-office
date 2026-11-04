# Engineering knowledge: frame time and the move to C++ (2026-11-04, checkking on i5)

Read before any speed work or C++ work. Sources: `handoffs/aaa-472/profile/MEASURE_i5_2026-11-04.md`, `handoffs/aaa-472/crowd/CROWD_PLAN.md`, `handoffs/cpp-500/README_CPP.md`.

## Measuring right (tested)
- **The editor caps itself at 3 fps (333 ms) when it is not the front window.** Measure with the editor in front, or turn off
  Editor Preferences > Performance > "Use Less CPU when in Background". Numbers taken in the background are not real.
- Use the CSV profiler (`csvprofile start/stop`) for Game / GPU / Render thread ms and per-group costs, and an Insights trace
  (`Trace.File cpu,frame` + `stat namedevents`) to name Blueprints. Scripts: `handoffs/aaa-472/profile/measure_split_ue.py`, `trace_wave_ue.py`, `csv_split.js`, `insights_bp_callers.js`.
- Compare CSV groups, not only fps: the zombie count changes during a run. Forcing a wave on all 6 wave managers stacks waves (our 300-480 zombie runs).
- "Tick less often" (tick intervals) does nothing while every frame is longer than the interval: cut work first, then throttle.

## Where a battle frame goes (i5, 142 zombies, editor in front: 161 ms, game thread = the frame, GPU 42 ms)
- Soldier Tick ~15 ms per soldier (loops every zombie every frame) -> fixes K, C3.
- Zombie body (mesh) collision + movement + physics wait: the biggest per-zombie cost (~55-92 ms at 300-480 zombies) -> fix C1.
- Zombie Think + Tick ~19 ms (target pick loops over all soldiers and farmers per zombie) -> C++ AZombieBase.
- HUD ~12 ms: ZombieHUD LineOfSightTo per zombie per frame (C5), Commander / Barracks world tag scans (C6, C7).
- Already right: zombie meshes have Update Rate Optimization and Only Tick Pose When Rendered.

## Rules learned
1. Never scan the world per frame (GetAllActorsOfClass / WithTag / GetActorOfClass / GetAllWidgetsOfClass): keep a registry, cache refs.
2. Never loop all zombies per soldier (or all soldiers per zombie) per frame: use a near list.
3. Body collision only where something can hit it (on screen, near the player, engaged).
4. Every spawn path needs the same alive cap.
5. Per-tick counters (`X = X + 1` on Tick) change speed with fps: scale by DeltaSeconds.
6. Blueprints: impure node outputs keep their last value, so "skip this scan for 0.5 s" is safe for readers downstream.

## C++ plan (#500)
- Convert only the hot spots (zombie brain, soldier fight loop, crowd manager) as C++ **parent classes**; Blueprints stay children for look and tuning.
- The kit (written ahead, not compiled yet): `handoffs/cpp-500/` (README_CPP.md) and all code as one text file: [CPP_TRANSITION_CODE.txt](CPP_TRANSITION_CODE.txt).
- Visual Studio Community is free for individuals and small teams (up to 5 users, under 250 PCs / US$1M a year); Unreal's royalty is separate.
- After a C++ change everyone needs the same compiled Binaries; Multi-User does not carry compiled code, editors restart.
