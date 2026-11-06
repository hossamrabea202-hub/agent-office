# #545 i5 part of the eruption (adjustedfilm, 2026-11-06)

Everything the spec gives i5, in its order. Spec: `SPEC_1106.md`. The base fix (step 1) is already pushed: see `../tentacle-spore-base-539/REVISION_1106.md`.

**Do not re-run `tentacle-rise-541/rise541_ue.py`.** It is replaced by your BP_TentacleEruption. Its sound script stays.

## Run these (Master, editor idle, not in Play)

1. `git pull`.
2. `py handoffs/tentacle-spore-base-539/sporebase_ue.py --reimport --dry-run`, then `--reimport`. Save the level.
3. `py handoffs/tentacle-eruption-cinematic/wire_outdoor_gate_ue.py --dry-run`, then `--apply`. Do this **before** any eruption test. It does not save if it adds compile errors, and stops if a node name changed.
4. `py handoffs/tentacle-eruption-cinematic/eruption_assets_ue.py --dry-run`, then with no flags.

Revert: `wire_outdoor_gate_ue.py --revert`; `eruption_assets_ue.py --revert`.

## What you get, and how BP_TentacleEruption uses it

**Outdoor gate and inert switch** (BPC_TentacleStrike, BPC_TentacleSpit)
- New bool `Inert` on both, default false, instance editable, exposed on spawn. Spawn the arm's vitals with it true. When the rise ends call `SetBoolPropertyByName(component, 'Inert', false)` on both components.
- While `Inert`, nothing runs: no strike, spit, rage or hit logic.
- A strike needs its target outside the castle box (X -1900..6500, Y -1900..5350), and a trace from 300 m above the target must not first meet a StaticMeshActor other than the target.
- No spit at the hero while he is inside the box. The catapult still throws into the castle, as the owner ordered.
- **Decision for the owner:** this stops strikes on cannons inside the castle box, as the order says. `GateCannons = false` on BPC_TentacleStrike lets cannons skip the box test again.

**Clips.** `AM_Tentacle_Rise` (6.5 s) for the first eruption, `AM_Tentacle_RiseFast` (4.2 s) for later ones. Play in the post-process slot at T0. Both start wound and end at rest. Each bone follows a hand-keyed driver through its own spring, softer towards the tip.

| Rise beat (s) | Rise | RiseFast |
|---|---|---|
| Uncoil | 0.15 to 1.4 | 0.1 to 0.87 |
| Snap, 2-3 frames | 1.45 | 0.9 |
| Hold with tremor | to 1.95 | to 1.2 |
| Slow settle | to 6.5 | to 4.2 |

The clips hold no height. Move the actor: Z from `Final - (80 - H) x Scale x 100` to `Final`, where H is the rig height at the ground. Ease out cubic over 2.5 s (1.6 s for RiseFast), so the top arrives at the snap. Hide the arm until T0: at its start height the tip is just under the ground.

**Dome.** `SM_EruptDome`, 70 m across, faces up, material `M_EruptDome`. Place it at the eruption point with its rim just under the terrain. Animate `Heave` through a dynamic material instance: 0 to 0.3 during TELL, up to 1.0 during HEAVE, with `HeightCm` 100. Its soil colour is a stand-in for the terrain; check it at the real spot. Hide it at the breach.

**Crack decal.** `M_EruptCrack`, deferred decal, new material only. Animate `Reveal` 0 to 1 through HEAVE: cracks open from the centre outward along the fissures. `RevealSoft` sets the edge. Sized for about 40 m. Spawn its decal only for the eruption.

**Slabs.** `SM_EruptSlab_S`, `_M`, `_L` (about 3, 7 and 15 m long), closed solids with the base's rock material, for your Geometry Collection in Fracture Mode. Throw 8 to 12 at most, per the spec.

**Collision reminder.** If the BP spawns a base's `_Col` mesh, keep its component invisible and never un-hide it: that is what the owner saw as the "silly blocky".

## Tested, and not tested

Lab, headless unless noted:
- **Base:** the fixed mesh rendered in a GUI Unreal editor with a grey ball and locked exposure. The crust is lit and there are no boxes (`../tentacle-spore-base-539/review/ue_lab_*.png`). Shape A only: this laptop ran out of memory building both while another session used its editor too. Shape B has the same fixes, confirmed in its mesh data only.
- **Gate:** dry-run, apply, refuses a second apply, revert, re-apply. Compile errors unchanged on both components.
- **Assets:** dry-run and two installs. Clip lengths and mesh sizes correct, WPO link made.
- **Crack albedo:** `pbr_check` values 38/51/55 sRGB.

**Not tested: nothing here has run in Play.** Unproven:
- the gate's trace against real castle roofs,
- the `Inert` handover,
- the clips in the slot,
- the dome and decal on the terrain: neither has ever been seen rendered, in any engine view,
- the frame budget. The dome is non-Nanite because it uses World Position Offset.

## Rules applied

SPEC_1106 realism rules: each layer has a physical cause; nothing glows. INDUSTRY_SECRETS 0.8, 3.4. Knowledge base 1, 3. `creature_studio_method.md`: driver + damped followers, snap, hold, slow recovery.

## Added 2026-11-06 evening (your BP_TentacleEruption needs these)

- Give each runtime base actor the tag `SporeBase`. The tentacle death finds its base by that tag and darkens it (#551).
- Spawn the ground skirt with the base: a DecalActor, material `M_SporeSkirt`, rotation (0, -90, yaw), `decal_size (350, R, R)` with R = 12500 x base scale, base component `receives_decals = False`. Same as `sporebase_ue.py`.
- Rerun `sporebase_ue.py --reimport` and `eruption_assets_ue.py`: new crust, skirt textures, `Dead` value on `M_TentacleSporeBase`, crack roughness fixed (pbr_check OK).
