# #2 Soldier level-up FX: less dramatic than the hero

From checkking (Claude), VFX Artist. Built on `handoffs/exports/checkking/BP_SoldierLevelWatch.t3d` and `BP_ThirdPersonCharacter.t3d` (live exports, 2026-10-27). Plan only: nothing to paste yet.

## What runs today

`BP_SoldierLevelWatch` ticks over every `BP_SoldierSword`. When the Rank component's `RelativeLocation.Y` (level) is above `RelativeScale3D.X + 0.5` (last level seen) and the soldier is older than 2 s, it:

1. spawns `BP_SoldierLevelUpFX` at the feet (scale 0.33) and attaches it with KeepWorld;
2. spawns **the hero's own system** `NS_LevelUp_None` at the feet with `SpawnSystemAtLocation`, scale 0.45, **not attached**;
3. plays `SFX_BookAcquired` at volume 0.5, pitch 1.3;
4. stores the new level in `RelativeScale3D.X`.

The hero uses the same `NS_LevelUp_None`, attached to the mesh at scale 1.

## Why it still reads as "hero-sized"

- Scaling a Niagara system shrinks its size, not its brightness, light radius, bloom or particle count. A 0.45 copy of the hero burst is still a hero burst.
- The Niagara part isn't attached, so a walking soldier leaves it behind, and it reads as a ground explosion rather than "this soldier got stronger".
- At the end of a wave several soldiers level at once, and every one gets the full burst and sound in the same frame.

## Plan

1. **Own system `NS_LevelUp_Soldier`**, duplicated from `NS_LevelUp_None` and toned down: about 30% of the spawn count, no light renderer (or a light radius under 60), about 40% of the emissive, half the lifetime, and a thin rising ring at chest height instead of the full column. Colour: the soldier's rank tint (blue for now, as today).
2. **Attach it** to the soldier (`SpawnSystemAttached` to the soldier's Mesh, KeepRelativeOffset, +88 Z), so it follows him.
3. **Crowd throttle**: at most one soldier burst every 0.15 s. If 3 or more level in the same second, the rest get just the ring and no sound.
4. **Sound**: volume 0.5 → 0.3, keep pitch 1.3.
5. Keep `BP_SoldierLevelUpFX` only if it adds something the new system doesn't (to be decided from the export below).

## Needed from the Master first (no blind pastes)

Into `handoffs/exports/checkking/levelup/`:

- `BP_SoldierLevelUpFX.t3d`: the full Blueprint export, like the others.
- `levelup_assets.txt`: every asset in `/Game/CastleDefender/VFX/LevelUp/` with its class.
- `NS_LevelUp_None.txt`: its emitters, and for each emitter the renderers (sprite / ribbon / mesh / light) and the spawn module and its rate or burst count. Also the system's User Parameters with their default values (from the Niagara editor's User Parameters panel; a copy-paste of the panel is fine).

Once those are in, I'll hand over a Python editor script that duplicates and tunes the system, plus the paste for the attach, throttle and sound changes.
