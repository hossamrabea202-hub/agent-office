# #48 Sound attraction and bell lure — source handoff v0.1

From: Codex  
Target: Master · Castle Defender · BP_Zombie normal-chase fallback  
Status: implementation supplied; Unreal build, integration and PIE NOT performed.

This package contains an original Unreal C++ runtime plugin, an editor material builder, range shaders, native automation assertions and an exact source-based integration guide. It is a compile-and-integrate handoff, not a claim that #48 is finished in the game. No project assets, settings, saves or existing Blueprints were changed. No paid services or third-party assets were used.

## Runtime

- `UNoiseSource48`: add to each actual emitter; call `EmitNoise` once on successful bell ring, shot, sword swing or crackle interval. No per-frame tick. Separate component per physical emitter; do not recreate it on every shot (that would reset cooldown).
- `UNoiseWorld48`: world-local queue capped at 32 pulses. Fixed one-second emission windows allow 28 ordinary emissions plus four reserved bell slots, up to 32 total. This is a fixed-window limit, not a strict rolling-window limit. No actor scans or listener registration arrays. Memory max 30 seconds, expiry checked by listeners; storage remains bounded even after silence.
- `UNoiseListener48`: attach to zombie; call at normal chase fallback in existing 0.25-second Think. Maximum 32 candidates per call (128 checks/zombie/second at the current cadence). No continuous tick. New sounds older than 0.5 seconds cannot be acquired. Current memory survives until expiry/arrival/interruption. Selection uses salience × distance falloff, 25% improvement and one-second retarget hysteresis.
- Movement uses nav projection, pathfinding and complete paths only. It preserves an active owned request, rate limits retries to 1 Hz and stops only its own request. Failed projection/request returns to original chase. Unreal navigation behavior still requires PIE testing.
- Server/standalone gameplay only. Multiplayer cosmetic delivery is deliberately left to the game's replication layer; this plugin does not multicast UI events. `OnNoiseEmitted` is a local delegate after accepted events.

| Kind | Radius cm | Memory s | Cooldown s | Salience |
|---|---:|---:|---:|---:|
| Bell | 12000 | 6 | 6 | 1.2 |
| Cannon | 8000 | 4 | 0.5 | 1 |
| Sword | 2200 | 2.5 | 0.5 | 0.6 |
| Crossbow | 600 | 1.5 | 0.5 | 0.25 |
| Jelly fire | 1800 | 2.5 | 2 | 0.45 |

These are first-pass tuning decisions, not owner-specified balance. Rain scales range by 1−0.25×rain; fog by 1−0.35×fog. Both multiply. Horizontal downwind/upwind modifies range by up to +25%/−25%; actual hearing distance is three-dimensional. Weather is captured when emitted, so later weather changes do not mutate existing pulses. No sound occlusion through walls is implemented; the card requests proximity hearing, not an acoustic simulation.

## Install / build (Master only)

1. Back up or use the normal project branch. Copy the **NoiseLure48** directory into the game's `Plugins/` directory. Do not replace an existing folder of this name.
2. Generate project files if required and build the game's Editor target with its actual Unreal version/toolchain. This plugin adds a native module; a Blueprint-only deployment needs the matching development toolchain. If native modules are unsuitable for this project, stop integration and request a Blueprint translation. Do not convert the project or change toolchains blindly.
3. Enable the plugin, restart the editor after a successful build and run `Automation RunTests CastleDefender.Noise48` in the editor console. The supplied native test has 16 assertions against actual runtime math; these have NOT run on Codex's machine.
4. Follow `blueprints/INTEGRATION.md`. Confirm the current zombie graph still matches the exported anchors before changing any link.
5. With the Python Editor Script Plugin already available, run the material builder using `runpy.run_path(r'<extracted>/tools/build_indicator_materials_ue.py', run_name='__main__')`. It refuses an existing `/Game/Codex/Noise48_v1` folder. Inspect material errors before saving any game references. A partial failure leaves only new assets in this folder; do not rerun over them without reviewing.
6. Complete `tests/PIE_ACCEPTANCE.md`. Keep whiteboard #48 open until editor evidence passes.

## Visual integration

Ground and minimap materials render an expanding soft ring plus a faint range boundary, fading over 1.2 seconds. They start invisible (`Age=2`). This is an informational effect, not an airborne Niagara effect. Decals follow receiving surfaces; the spherical distance calculation includes elevation. A top-down minimap has no terrain-height sample, so its footprint is a horizontal range approximation on steep terrain.

Bind a presentation manager once to `UNoiseWorld48.OnNoiseEmitted`. Allocate at most **eight pooled indicators**, recycle the oldest, and reuse their dynamic material instances. Set NoiseOrigin, BaseRadius, WeatherScale, WindXY, WindStrength, Color; update Age only while active, return to pool after 1.2 s. Indicator pooling/glue is specified here, not implemented in this plugin; see integration guide. Collision/navigation on indicator actors must be disabled. Never spawn one indicator per zombie.

For a ground decal use a downward projector and conservative XY half-extent `Radius*WeatherScale*(1+0.25*WindStrength)+2*WidthCm`, with enough projection depth for intended terrain. Verify projector axes on the target UE version. Exclude characters/structures from receiving the decal if the range should appear on terrain only. Large decals can be expensive; measure eight overlapping bell rings at target resolution before approval.

For minimap use an event-centered image with HalfExtentCm equal to the same conservative extent. Map event world position to the existing minimap coordinates. The shader assumes image U=world X and V=world Y; transform wind and UV axes with the actual minimap rotation/mirroring. Export of the actual minimap is requested before supplying a blind graph patch.

Bell guard-wake is an integration hook: on an accepted **Bell** pulse notify the existing sleeping-guard system (#47), with the same `AudibilityScore>0` check. Do not invent guard variables, wake every guard globally or implement a second sleep system. Existing guard API/export is required.

## Verification and limits

`reports/static-validation.json` reports only local source/package checks. Native compilation, automation, shader compilation, navigation, terrain appearance, multiplayer and performance remain unverified. There is no local Unreal project or C++ compiler accessible here. This source handoff is intentionally not marked game-ready or AAA-complete.

References checked: Epic's [MoveToLocation](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/AIModule/AAIController/MoveToLocation) documents that issuing it aborts the active path; [ProjectPointToNavigation](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/NavigationSystem/UNavigationSystemV1/ProjectPointToNavigation) documents the projection API. These live pages currently show UE 5.8; Master must compile against the project's actual version.
