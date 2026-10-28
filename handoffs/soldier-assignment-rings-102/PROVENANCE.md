# Provenance and evidence

Original procedural ring geometry and HLSL authored by Codex for this owner's Castle Defender project, office task #102, on 2026-10-28. No external model, texture, paid provider or AI image was used in this package. License label `LicenseRef-Owner-Internal` records intended internal project use; it does not assert third-party rights or a public license release.

OBJ source is centimeters/Z up. Blender 4.5.4 LTS exported FBX and meter-based portable GLB. The GLB uses a simple unlit color preview material; the Unreal shaders supply runtime transparency, patterns, emblems and Depth Fade. The mesh is an intentionally open two-sided effect surface, not a collision volume or walkable structure.

`reports/asset-validation.json` records the supplied GLB policy checks. `reports/offline-validation.json` records graph-link/topology/source checks. `reports/package-verification.json` records the canonical GLB package's hashes. These are separate from UE import, shader compile, Blueprint paste, gameplay and art approval, which are not claimed. The canonical package validates geometry, not Unreal shaders.

UE 5.3 official API references used for the editor script:

- [MaterialEditingLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialEditingLibrary?application_version=5.3)
- [MaterialExpressionCustom](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialExpressionCustom?application_version=5.3)
- [MaterialExpressionDepthFade](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialExpressionDepthFade?application_version=5.3)
- [CollectionScalarParameter](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/CollectionScalarParameter?application_version=5.3)
- [FbxStaticMeshImportData](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/FbxStaticMeshImportData?application_version=5.3)

The official Python surface is version-dependent. The authorized editor agent must inspect actual errors and native node reconstruction rather than treating API documentation or offline checks as a successful editor run.
