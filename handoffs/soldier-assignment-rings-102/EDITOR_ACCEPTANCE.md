# Target-editor acceptance — not yet executed

Record actual results here/on office #102. Offline reports do not prove Unreal compatibility or appearance.

- [ ] UE version/project renderer recorded; material compilation has no errors in both domains; mesh imported at expected bounds, orientation and slot.
- [ ] New Actor paste reconstructs and compiles cleanly; components/variables resolve; MarkerRoot absolute flags correct; BeginPlay creates two MIDs once.
- [ ] Fresh #110 exports recorded with paths/time. Actual raw-order mapping and current order-wheel colors documented. Sword, Xbow, recruit and commander paths covered without duplicate actors.
- [ ] All eight semantic patterns/icons readable at gameplay camera distance; ground/air colors agree; daylight, shadow and night review completed without exposure/Lumen changes.
- [ ] Fast walking, sprinting, turns and climbing: XY follows continuously; height/normal update acceptable; flat ground, slope, rolling ground, stairs, rocks and ledges inspected. No unacceptable floating/clipping, decal stretching up nearby walls, shimmering or air lip popping. Reduce decal half-depth to fit actual steps if it bleeds through platforms.
- [ ] No ground hit hides; static floor below a bridge does not win over the walked surface; custom walkable collision/moving platforms handled if the project uses them.
- [ ] Order changes update immediately at all command routes. Cannon release, team changes and initial current order show the correct style. Unknown raw values handled without modifying gameplay.
- [ ] Death removes both layers immediately, corpse cleanup leaves no orphan, respawn/reuse restores correctly; no health/order/collision/navigation behavior changes.
- [ ] Settings checkbox hides both layers immediately, remains hidden on reload/world transition, and preserves other settings. Hidden/dead/out-of-range markers skip terrain queries.
- [ ] 60 and 120 soldiers: count one marker/soldier, no Niagara/point lights, no material-instance creation or parameter writes on Tick. Compare identical warmed-up camera/scenario with rings off/on; record CPU/game thread, GPU, decal/translucency cost and terrain trace counts on target hardware. Apply the project's frame budget, do not use offline triangle counts as performance proof.
- [ ] Camera culling round-trip has no stale style; paused/cinematic cameras and client spawning are correct for the game's actual modes.
- [ ] Save changed assets; export final new Actor and changed order/death/Settings graphs; upload gameplay screenshots/video with day/night and uneven-terrain evidence to the office. Report pass/fail and remaining limits before closing #102.

Suggested capture matrix: 1 soldier with all styles; 60 soldiers mixed styles; 120 soldiers mixed styles; each at the normal gameplay camera plus one low oblique view showing the raised ribbon. Use the same camera/exposure for off/on performance comparisons. A low oblique view alone is insufficient for gameplay readability approval.
