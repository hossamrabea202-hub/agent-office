# Build the new marker Actor

Only the authorized editor agent performs these steps. Work outside PIE. The project must provide the Python Editor Script Plugin and Editor Scripting Utilities for the asset builder. Check current project setup before enabling anything; the script does not edit plugins or project settings.

## 1. Create the material and mesh assets

Extract the entire package. In the Unreal Output Log's **Python** input, execute the local script (replace the example path):

Use **Tools → Execute Python Script** and select `build_assets_ue.py`, or run this Python command, which sets the source path for relative file lookup:

```python
import runpy; runpy.run_path(r"D:\handoffs\soldier-assignment-rings-102\build_assets_ue.py", run_name="__main__")
```

The result is saved only after successful asset creation in `reports/ue-build-result.json`; the report does not certify shader compilation. If a partial run fails, inspect Output Log and the newly created folder. Preserve the failed candidate or use a new versioned destination; do not rerun over it. The fixed paths in the paste must change together if the destination changes.

Inspect both material compiler results. Ground: Deferred Decal / Translucent, Base Color + small Emissive + Opacity. Air: Surface / Translucent / Unlit / Two Sided, normal depth testing, Depth Fade 6 cm. Check that the `ShowMarkers` collection parameter works in both domains. The project renderer and receiver materials must support these decal outputs. Do not change project rendering settings to hide a compile or renderer compatibility failure; record and adapt the candidate.

Verify mesh local bounds: **135 × 135 × 16 cm**, Z from approximately 2 to 18 cm, pivot at the floor under the center. If FBX converts axes unexpectedly, repair import orientation and recheck bounds before using it. The OBJ fallback is centimeters/Z up and also needs the bound check. Assign `M_Assignment102_Air` to material slot 0. No mesh collision.

## 2. Create `/Game/Codex/AssignmentMarkers102_v1/BP_AssignmentMarker102`

Parent class **Actor**. Add a plain SceneComponent named **MarkerRoot** as the root. Add these children:

| Component | Settings |
| --- | --- |
| `MarkerRoot` | Mobility Movable; **Absolute Location false, Absolute Rotation true, Absolute Scale true**; world scale 1,1,1 |
| `GroundDecal` | DecalComponent; relative location 0,0,0; rotation Pitch **-90**, Yaw 0, Roll 0; `Decal Size` **X=60, Y=85, Z=85 cm**; material `M_Assignment102_Ground`; fade screen size start at 0.01; sort order 0 |
| `AirRim` | StaticMeshComponent; mesh `SM_Assignment102_AirRim`; relative location **0,0,6 cm**, rotation 0,0,0, scale 1; material `M_Assignment102_Air`; mobility Movable; Collision Preset NoCollision; Generate Overlap Events false; Cast Shadow false; Receives Decals false; Can Ever Affect Navigation false |

The decal projects along local X. The -90 pitch points projection down local -Z; after the Actor aligns its Z to the hit normal, it projects toward the ground. X is projection half-depth; Y/Z are half-extents. Confirm circle size and direction visually in this engine before continuing.

Class Defaults: Start With Tick Enabled true; Tick Interval 0.2; Actor Hidden In Game true; Replicates false. This is a local cosmetic actor. It adds no gameplay collision. Do not register gameplay damage, selection, navigation or overlap behavior on it.

Create variables, with these exact names:

| Variable | Type | Default |
| --- | --- | --- |
| `GroundMID` | Material Instance Dynamic **Object Reference** | None |
| `AirMID` | Material Instance Dynamic **Object Reference** | None |
| `MarkerAlive` | Boolean | true |

`GroundDecal` and `AirRim` component variables must be accessible in the graph. Compile the empty Actor once to register variables and components.

## 3. Paste the new Actor graph

Delete only the template's unused BeginPlay/Tick/overlap nodes in this **new** Blueprint. Copy the entire raw `blueprints/BP_AssignmentMarker102_EventGraph.t3d` file to the clipboard and paste into EventGraph. Example PowerShell on the editor's machine:

```powershell
Get-Content -Raw -LiteralPath '.\blueprints\BP_AssignmentMarker102_EventGraph.t3d' | Set-Clipboard
```

Paste with Ctrl+V, select the imported nodes, Refresh/Reconstruct Nodes, compile and save. It should contain BeginPlay, Tick, `SetAssignment102(int SemanticStyle)` and `SetMarkerAlive102(bool Alive)`. Check component references and native function signatures. Engine paste/reconstruction has not been tested here: if a pin is orphaned or a native overload differs, recreate that native node using the named function and reconnect per `GAME_INTEGRATION.md`. Never accept a compile with warnings about unresolved references.

BeginPlay attaches to **Owner**, creates the two MIDs once and refreshes terrain. Owner must already be the soldier when this actor begins play. Absolute root rotation/scale prevent soldier yaw and scale from tilting/scaling the effect. Tick checks owner validity, life, global Settings and player-camera distance, then traces static world. A hit positions/rotates the Actor and reveals it; no hit hides it; invalid Owner destroys it. `SetMarkerAlive102` reruns the same gates immediately. `SetAssignment102` updates the two MID style parameters immediately.

## 4. Single-marker inspection

Spawn from a known test soldier with its Owner pin set. Check slow and fast walking, rapid turns and a slope. The ring must track owner translation continuously between terrain updates. Turn the Settings MPC off and confirm both layers disappear. Test the eight styles before adding the hooks to all soldiers.

Troubleshooting: no ground ring → inspect receiver decals, material compiler/domain, projection rotation/volume and trace hit; no air → inspect mesh Z axis/scale, material slot, depth test/Depth Fade and MID creation; effect yaw/scale drifts → fix MarkerRoot absolute flags; effect trails in XY → attachment failed/Owner missing. A bright halo requires the game's existing bloom; the mesh itself remains emissive when bloom is off. Do not introduce global exposure or Lumen changes for this effect.
