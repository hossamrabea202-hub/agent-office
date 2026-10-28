# Connect to the current game

Fresh source request: [#110](https://github.com/hossamrabea202-hub/agent-office/issues/110). Export order writes/reads, initial spawn, death/cleanup and Settings handlers from the **current saved** SoldierSword, Xbow and commander/recruit Blueprints. Confirm inheritance first. This file is the integration contract, not a blind replacement for an existing EventGraph.

## Order contract

`StyleIndex` is a display ID defined here. Resolve the current order enum/integer/name to these semantic values at the authoritative existing order-change point. Never wire the game's raw Order integer straight to StyleIndex without checking the actual table.

| SemanticStyle | Meaning | Ground marking |
| --- | --- | --- |
| 0 | Idle / unassigned / unknown display fallback | Gray-green dashes + three dots |
| 1 | Follow | Blue full ring + double chevron |
| 2 | Guard | Brass four arcs + shield |
| 3 | Hold | Pale desaturated green eight dashes + square |
| 4 | Patrol | Green dotted route + route arrow |
| 5 | Man cannon | Copper ring + aiming mark |
| 6 | Strike team | Muted red two arcs + crossed blades |
| 7 | Guard team | Violet four arcs + paired shields |

Match the existing order-wheel legend in the same change. If the game has extra orders or uses different meanings/colors, extend the display contract and both shader palettes together before calling integration complete. Unknown raw values should log once in development and display Idle; do not change the soldier's actual command to fit this table.

## Required existing-Blueprint hooks

1. **Spawn once:** add a variable `AssignmentMarker102` of BP_AssignmentMarker102 Object Reference to the common soldier parent. At the existing successful spawn/BeginPlay path, IsValid-guard it; if missing, Spawn Actor from Class BP_AssignmentMarker102, identity scale, **Owner = Self**, collision handling Always Spawn, transform using the current soldier location. Store the return value. The marker attaches itself. With deferred spawn, supply Owner before Finish Spawning and send state only after Finish Spawning. Do not also spawn it in Xbow/commander children when they call parent BeginPlay.
2. **Initialize and change orders:** after successful marker spawn, compute SemanticStyle from the current game order and call `AssignmentMarker102 → SetAssignment102`. After every real assignment/order write, update the marker through this same mapping. Include commander/team overrides and cannon assignment/release where they bypass the general order setter. This is event-driven; no extra per-frame MID writes.
3. **Life:** at the first authoritative death/despawn event, IsValid-guard and call `SetMarkerAlive102(false)` before ragdoll/delayed corpse cleanup. On any supported resurrection/reuse, initialize the mapped style and call `SetMarkerAlive102(true)` after the soldier is live. Destroy the marker when the soldier is finally removed; the marker's own invalid-Owner cleanup is a fallback. This is cosmetic and must never write health or order state.
4. **Settings:** add “Show soldier assignment rings” using the existing Settings widget/save mechanism. Apply the loaded preference with Kismet Material Library **Set Scalar Parameter Value**, Collection=`MPC_Assignment102`, Parameter Name=`ShowMarkers`, Value=1 or 0. On checkbox change apply immediately and persist through the current settings save path. Do not overwrite unrelated saved settings. This MPC suppresses both shader layers immediately; the next 0.2s marker tick also skips ground traces while disabled. Apply the preference at world initialization so the default 1 does not briefly show rings for users who disabled them.

For a networked game, cosmetics must exist on the rendering client(s), including late join/relevancy and replicated order OnRep paths. This default actor is non-replicated and looks up player camera index 0. The supplied single-camera contract does not claim split-screen/network validation; adapt spawning and visibility explicitly if the project uses either.

## Ground trace and movement

Trace Start=OwnerLocation+(0,0,100), End=OwnerLocation+(0,0,-350), simple collision, `ObjectTypes` default WorldStatic only, ignore Owner and Self, debug off. Confirm **ObjectTypeQuery1 resolves to WorldStatic** in the recipient project. This avoids standing on other soldiers. If walkable terrain uses a custom object type or moving platforms, use the project's actual ground filter and test it; do not add Pawn/WorldDynamic broadly without checking false hits.

ImpactPoint → SetActorLocation; MakeRotFromZ(ImpactNormal) → SetActorRotation. Collision sweep false, teleport true. The absolute-rotation/scale root preserves the traced plane while parent attachment follows soldier translation continuously. No hit → hidden. Dead/global hidden/camera missing/>60m → hidden and no trace. Returning into range → refresh then reveal. At 5Hz, height/normal can lag on sudden height changes; review at maximum movement speed, and raise update rate or use the existing movement-floor data if needed after profiling. The upper rim is a plane-aligned mesh with Depth Fade, not a fully terrain-deformed ring.

## Graph reference for reconstruction

BeginPlay → AttachToActor(Owner, KeepWorld location/rotation/scale) → GroundDecal.CreateDynamicMaterialInstance → store GroundMID → AirRim.CreateDynamicMaterialInstance(slot 0) → store AirMID → SetActorTickInterval(0.2) → Refresh gates.

Tick / SetMarkerAlive102 after storing bool → Owner IsValid? (false: DestroyActor) → MarkerAlive? → MPC ShowMarkers>0.5? → Camera IsValid? → Distance(Owner,Camera)<=6000? → LineTraceSingleForObjects → hit? → SetActorLocationAndRotation → Unhide. Every failed visibility/trace gate hides.

SetAssignment102(SemanticStyle int) → Convert int to float → GroundMID.SetScalarParameterValue(StyleIndex) → AirMID.SetScalarParameterValue(StyleIndex). HLSL rounds/clamps 0–7. Call only after the spawn has completed and both MIDs exist.

## Rollback

Disconnect the new cosmetic spawn/order/life hooks and the new Settings MPC call using the pre-edit exports as reference; preserve existing gameplay flow. Remove/destroy only the newly spawned AssignmentMarker102 actors. Keep the asset folder as an isolated candidate until review is complete. No save migration or global renderer rollback should be needed.
