# Helmet and capes: source collection handoff (#65, #67, #84)

2026-10-28 · Codex · status: **blocked on current private source assets**.

This is a tested source-collection aid, not a repaired helmet/cape package. None
of the three gameplay bugs is fixed or Play-verified by this handoff. Keep the
original cards open. No paid provider, model generation or asset replacement.

## Findings

- The existing office hero reference identifies `/Game/ShadowKight/Mesh/ShadowknightUE_SK`,
  material slots arms/chest/cloth/helmet/pants, with helmet slot index 3. Treat this
  as a reference to verify against the current export, not a selection instruction.
- The reference points to a licensed FBX on the Unreal machine at
  `C:\Unreal Backups\Castle Defender\Tools\PrivateExports\hero\ShadowknightUE_SK.fbx`.
  That project/path is absent from this Codex workspace. The public office tree
  contains no current starter-knight or royal/soldier cape source FBX.
- The exported BP_SoldierXbow inherits BP_SoldierSword. A shared parent may own
  the cape setup; inspect overrides before making duplicate fixes.
- Issue #65 identifies a horn opacity cut, but the affected mesh/UV triangles
  have not been inspected here. Do not restore opacity on the current horn mesh:
  that would bring the horns back.
- The cape cards describe cloth behaviour, but Chaos cloth vs skeletal animation
  vs material World Position Offset has not been established. Physics-body or
  cloth-weight changes alone cannot fix a WPO-driven cape.

## Receiving operator: collect sources

Only the authorized Unreal operator runs `collect_sources_ue.py`. It reads project
assets and loaded actor/component settings; it does not compile, save, reimport,
spawn actors or start PIE. It writes a unique local directory under
`Saved/CodexDiagnostics/helmet-capes-<UTC>/`. Review `inventory.json` errors and
per-property unavailability. Engine-version differences and missing CDO/SCS
components are explicit limitations, not proof that an asset has no cloth.

1. Run the script in the project's Unreal Python environment, outside PIE.
2. Correct the hero BP path in BLUEPRINTS if it differs from the known default.
   Provide live hero and sword/xbow soldier instances in the review level so their
   component overrides can be inspected (the collector itself creates none).
3. To obtain reference skeletal FBXs, set `EXPORT_FBX = True` and run again.
   Source meshes, morph targets and vertex colours are requested. This is export
   only; cloth maps/configurations and physics body geometry need native exports
   separately. Inspect exporter errors and verify the actual exported bytes.
4. Provide current knight/cape mesh + skeleton/weights, relevant armour opacity
   textures and material graph/custom HLSL, cape cloth config/paint maps if used,
   physics asset body details, and attachment/leader-pose transforms. Include a
   short idle/walk/turn/attack/aim capture so deformation can be diagnosed.
5. Keep licensed source FBXs and diagnostic output private. Share them with Codex
   through an owner-approved private location accessible to this workspace.
   Do not upload licensed meshes/textures or the raw private inventory to this
   public repository. Fresh project-authored graph exports can go under
   `handoffs/exports/codex/helmet-capes-65-67-84/` after content review.

The inventory is not a full Blueprint/material graph export. Where graph API
access fails, copy the graph text from the editor and provide custom-node HLSL
and material-function dependencies explicitly.

## Repair acceptance once sources arrive

| Card | Required repair | Evidence before closure |
|---|---|---|
| #65 | Remove only identified horn triangles; stitch shell to the actual helmet curvature, preserve unaffected vertices/UVs/weights and skeleton, patch/bake surfaces, then remove obsolete horn masking in a versioned material | Before/after close views of both sides, back and top; topology/normal/weight checks; UE review import on the existing skeleton; hero and soldier Play checks; no horns, holes or visible seam |
| #67 | Resolve the actual deformation source; keep anchors behind both shoulders; constrain lower motion and body penetration using the active deformation system | Idle, walk, run, turn, sword attack and crossbow aim, front/side/back views; original and upgraded armour; no chest/arm penetration or frontward swing |
| #84 | Keep the emblem region stable in the system that drives the cape; prevent the moving lower region covering it | Hero plus sword and crossbow recruits, all rank emblems; walk/run/turn/combat; emblem readable at gameplay distance; lower cape still moves |

Use new review assets and a dependency-isolated test setup first. Do not overwrite
the live knight, physics asset, material or map. Record import options, source
hashes, what changed and the actual Play result before integration or closure.

## Local verification of this handoff

`collect_sources_ue.py` compiled successfully with Python 3.12. Three offline
failure-path checks passed: an unavailable property is recorded without losing
other properties; a collection failure produces an explicit partial report and
unique output directory; exporter success without output bytes is rejected.
These checks use fixtures and do not establish Unreal execution compatibility.

Local game-dev capabilities and doctor ran successfully (CLI 1.5.1). That proves
local tooling availability, not access to the missing sources or engine testing.

API references checked against Epic's UE 5.3 documentation:
- https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/FbxExportOption?application_version=5.3
- https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SkeletalMesh?application_version=5.3
- https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialInterface?application_version=5.3

Next action belongs to the authorized operator: provide the current private
sources/inventory. Codex retains repair ownership; no reassignment or completion
is implied by handing in this collection aid.

