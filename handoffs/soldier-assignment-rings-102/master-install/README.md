# #102 / #113 assignment rings — installed by the Master (2026-10-28)

**In the project now (`/Game/Codex/AssignmentMarkers102_v1/`):** MPC_Assignment102 (ShowMarkers=1), M_Assignment102_Ground (deferred decal, 522 instr.), M_Assignment102_Air (unlit translucent), SM_Assignment102_AirRim (135×135×16 cm, Z 2–18), MI_*_0..7, **BP_AssignmentMarker102** (MarkerRoot abs rot/scale, GroundDecal, AirRim, GroundMID/AirMID/MarkerAlive, graph pasted, compiles) and **BPC_AssignmentRing**.

**Soldier hook = a component, no soldier graph edits.** `BPC_AssignmentRing` is on `BP_SoldierSword` (so Xbow + Commander inherit it): BeginPlay spawns the marker with Owner = the soldier; every 0.5 s it reads the soldier's `Order` channel (RelativeLocation.X, rounded, clamped 0–7) and calls `SetAssignment102` when it changes; when the soldier's Mesh starts simulating physics (ragdoll) it calls `SetMarkerAlive102(false)` once.

**Order → style is currently identity** (raw Order.X = StyleIndex). Known: swords idle = 0 (gray dashes), the two wall crossbows start at Order 4 (green dotted). Owner Play-test tells us which wheel order shows which ring; remap is a tiny change in `gen_ring3.py` (a Select/Switch before `SetAssignment102`).

Fixes to Codex's package needed for UE 5.3 (all in `tools/master/h113/`): VectorParameter output is '' not 'RGB'; ComponentMask/DepthFade inputs are '' (connect() now retries real pin names); preview-MI StyleIndex set is non-fatal; `Greater_FloatFloat`/`Conv_IntToFloat` → `_DoubleDouble`/`_IntToDouble`; `GetScalarParameterValue` is impure in 5.3 → wired into the exec chain; `BreakHitResult` lives in GameplayStatics, not KismetSystemLibrary (the node silently vanished on paste).

Checked: materials compile; editor-world preview of styles 1–4 on the courtyard cobbles (`shots/master-102-rings-styles1-4-editor.jpg`); Simulate: every soldier spawns a marker, styles follow Order.X. Markers stay hidden in Simulate by design (no player camera) → **ground tracking / hide-at-60 m / death need a Play test by the owner.**
Not done: the Settings checkbox ("Show soldier assignment rings" → MPC ShowMarkers) — needs the Settings widget paste; rings are always on until then.
