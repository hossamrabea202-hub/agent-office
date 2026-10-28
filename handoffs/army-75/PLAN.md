# #75 Bigger army: implementation + performance plan

Seat: `hossam gmail laptop2 (Claude)` (owner reassigned from adjustedfilm, 2026-10-28). Numbers are the vice
master's Decision on the card: **cap = 6 + 2 x (hero level - 1)**; Commanders unlock at hero LV5/10/15/20, each
**+20 cap** and leading his own squad of 20-30. Stress test before raising the cap past 40.

## Caps

| Hero LV | 1 | 3 | 5 | 7 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|
| Base cap | 6 | 10 | 14 | 18 | 24 | 34 | 44 |
| Commanders unlockable | 0 | 0 | 1 | 1 | 2 | 3 | 4 |
| Max army (all commanders) | 6 | 10 | 34 | 38 | 64 | 94 | 124 |

- The 4 starter soldiers count toward the cap (as today in BP_BarracksHUD's CAP).
- The commander himself doesn't count; his +20 is added when he's recruited, not when unlocked.
- A commander's squad = soldiers assigned to him (orders wheel, #12). The hero's own guard = the rest.

## Where it changes (from `handoffs/exports/commander/`)

1. **BP_BarracksHUD:** replace the constant CAP with `6 + 2 * (HeroLevel - 1) + 20 * CommandersAlive`.
   The recruit button greys out at the cap with `ARMY FULL (18/18) - level up or recruit a Commander`.
2. **Commander recruit:** today one commander for 300 gold. Allow up to `floor(HeroLevel / 5)` (max 4) commanders.
   Price rises: 300, 900, 1800, 3000. A locked one shows `COMMANDER 2 - unlocks at hero LV10`.
3. **Squads:** each commander keeps an array of up to 30 soldiers (today's single squad becomes per commander). New
   recruits join the commander with the fewest men, otherwise the hero's guard.
4. **Commander death (#15):** his squad returns to the hero's guard. The cap drops by 20 at once, but nobody is
   removed. Recruiting stays blocked until the army is under the cap again.

## Performance plan (the part that decides whether 100 soldiers is playable)

Order matters: measure first, then change only what the numbers say.

1. **Baseline:** in Play, spawn 30 / 60 / 100 soldiers plus a full wave (console spawner or a debug key). Record
   `stat unit` (Game / Draw / GPU ms), `stat anim`, `stat game` and fps on this card.
2. **Animation (usually the biggest cost):** on the soldier skeletal meshes, turn on **Update Rate Optimizations**
   (`bEnableUpdateRateOptimizations`) and set `VisibilityBasedAnimTickOption = OnlyTickPoseWhenRendered`. Far
   soldiers then animate at 1/2-1/4 rate and off-screen ones don't evaluate.
3. **Capes (Chaos cloth):** cloth only within ~15 m of the camera, at most ~10 at once. Beyond that, switch to the
   static/baked cape (cloth LOD or disable `ClothingSimulation` per component on a 0.5 s timer by distance).
4. **Thinking:** keep the soldier AI timers (0.15-0.5 s) and **stagger** them: start each timer with a random
   0-0.3 s offset so 100 soldiers don't all think on the same frame. No FindNearest / line traces per frame.
5. **Movement:** CharacterMovement `bUseRVOAvoidance` on, avoidance weight 0.5. Far soldiers (> 40 m) drop to a
   lower tick (`SetComponentTickInterval(0.1)` on movement).
6. **Rendering:** no dynamic shadows on soldiers past 25 m (`CastShadow` by distance, or LOD-based), shared
   material instances (no per-soldier dynamic materials except where the rank cape needs one), mesh LODs on the
   knight (LOD1 at 50 %, LOD2 at 25 % screen size).
7. **Budget target:** 60 fps on the owner's PC with 60 soldiers + a full wave. If 100 can't hold 45 fps after steps
   2-6, cap the 4th commander's squad at 20.

## Checks (Play)

1. LV1: recruit up to 6. Level up: +2 each level, and the label shows the new cap.
2. LV5: commander 1 unlocks (300). Recruiting him adds +20 cap, and new recruits fill his squad.
3. Kill a commander: his squad rejoins the hero, and recruiting blocks until under the cap.
4. Perf numbers at 30 / 60 / 100 recorded on the card, before and after steps 2-6.

## Exports needed (fresh)

`BP_BarracksHUD` (CAP + recruit), `BP_ArmyHUD`, `BP_SoldierCommander`, `BP_SoldierSword` / `BP_SoldierXbow`
(the BeginPlay timers + mesh/cape component settings), the hero level source (`CheckLevelUp`).
