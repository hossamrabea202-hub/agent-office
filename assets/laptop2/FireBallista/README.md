# Fire-spear launcher (#10): torsion ballista with a brazier

Made 2026-10-30 by `hossam gmail laptop2 (Claude)`. A medieval torsion ballista on a lashed tripod stand with a swivel,
and an iron brazier of glowing coals beside it to light the pitch-wrapped spears. Knowledge-base standard, 4K bake,
emissive coals (ember pulse in `M_LP2Weapon`).

Pieces (one texture `T_FireBallista`): `SM_FireBallista_Base` (stand, swivel, brazier, coals; pivot at ground centre),
`_Frame` (the launcher; pivot = the swivel at 1.42 m: yaw to aim), `_Slider` (the firing bar with the claw; pivot at
its rear: slide forward 0.8 m on release), `_Spear` (pivot at the butt; it flies). Muzzle at +X, 1.35 m out, 1.6 m up.
`ballista_meta.json` has the pivots and the muzzle.

## Behaviour (editor driver)

`BP_FireBallista`: E to man it (a soldier can be ordered to crew it like the cannon, order 3). Aim with the camera (yaw
the Frame). Fire: Slider forward, the Spear spawns as a projectile from the muzzle (a copy of `SM_FireBallista_Spear`
with a fire Niagara on the tow wrap; use the #32 fire trail), 40 m/s, reload 6 s (the windlass turns). On hit: 60 damage
in 1.5 m and sets zombies alight (the #32 burning state). Lighting the spear at the brazier is a 1 s animation before
the first shot. The brazier's coals light the area: pair the emissive with a real orange point light (1200 cd, flicker).

## Unreal

`py "<repo>/assets/laptop2/FireBallista/import_kit_ue.py"` → `/Game/CastleDefender/Weapons/FireBallista/`. `source/`
rebuilds it.
