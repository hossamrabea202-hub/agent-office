# #2 exports for checkking (from hossam gmail, Master), 2026-10-27

All three items from your PLAN.md "Needed from the Master first":

| File | What |
|---|---|
| `BP_SoldierLevelUpFX.t3d` | Full Blueprint export (graphs: EventGraph, ReceiveBeginPlay, ReceiveTick, ConstructionScript). |
| `BP_SoldierLevelUpFX_components.txt` | Its components (a .t3d of a Blueprint holds no components): class, relative transform, mesh, materials, light. |
| `levelup_assets.txt` | Every asset in `/Game/CastleDefender/VFX/LevelUp/` with its class (20). |
| `NS_LevelUp_None.txt` | The Niagara system breakdown. |

## Key finding: `NS_LevelUp_None` is EMPTY

It has **no emitters, no renderers and no User Parameters**, only the default system scripts. Spawning it at 0.45 (soldier) or 1.0 (hero) draws nothing. Everything you see on a soldier level-up is `BP_SoldierLevelUpFX` at scale 0.33:

- **Pillar** and **Pillar2**: engine cylinders with `MI_SoldierLvl_WallInner` / `MI_SoldierLvl_WallOuter`.
- **Ring**: a ground plane with `M_LvlUp_Ring`.
- **Orb** and **Aura**: spheres with `M_LvlUp_Orb` / `M_LvlUp_Aura`.
- **Glow**: a point light, radius 420, intensity driven by `C_LvlUp_Light` from the graph.

The scale curves `C_LvlUp_*` animate them in ReceiveTick.

So step 1 of your plan (duplicate and tone down the Niagara system) has nothing to tone down. The "hero-sized" read comes from this actor. Pick one:

- **(a)** tune `BP_SoldierLevelUpFX` itself (lower pillar heights and opacity, light intensity and radius, shorter curves) and attach it to the soldier;
- **(b)** build a real small `NS_LevelUp_Soldier` from scratch and retire the actor for soldiers.

The crowd throttle and the sound changes in your plan still apply either way. Hand the result to me as usual: a Python editor script plus the paste.
