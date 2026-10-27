# Hero reference (#1)

- Hero BP: BP_ThirdPersonCharacter. Driving mesh `Mesh` = SKM_Quinn_Simple (hidden) with AnimBP **ABP_Quinn**; the visible knight is component **KnightMesh** = `/Game/ShadowKight/Mesh/ShadowknightUE_SK`, following the Quinn pose (see BP_ThirdPersonCharacter.t3d for KnightMesh transform).
- ShadowknightUE_SK material slots in order: arms, chest, cloth, helmet, pants.
- FBX: exported to the owner's PC at `C:\Unreal Backups\Castle Defender\Tools\PrivateExports\hero\ShadowknightUE_SK.fbx` (licensed, NOT in this repo). Owner: share it with checkking privately. `HeroHead` was not found by that name; Greystone head asset name needed from the owner/Vice.
- Camera pitch limits: default PlayerCameraManager -89.9 / 89.9.
