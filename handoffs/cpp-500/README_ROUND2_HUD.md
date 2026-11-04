# #500 C++ round 2: the HUD chain (i5, written ahead, NOT compiled yet)

Why: on i9 the HUD is now the biggest game-thread cost in a wave (UI 15 ms, i9 16:40), and after a crash the 11-level HUD Blueprint chain
(Zombie > Minimap > SkillTree > Barracks > Army > Controls > Queue > Hero > Commander > Armory > Notice, ~3,300 nodes) is slow to load.
The HUD's drawing calls ~45 world scans (repo exports 10-30 .. 11-03): ZombieHUD 8, Barracks 12, Commander 7, Queue 3, Hero 3, Army 1, Minimap 1.

## What round 2 adds
- `Source/CastleDefender/CDHudBase.h/.cpp`: **ACDHudBase** (C++ parent of BP_ZombieHUD, so all 11 levels inherit it):
  - `GetCachedActorOfClass` (kept until that actor is gone; a missing one is looked for again at most every 0.5 s),
  - `GetCachedActorsOfClass` (zombie classes: live from the crowd registry, dead included like the engine node; other classes: reused for 0.25 s),
  - `GetCachedActorsWithTag` (reused for 0.25 s; actors that lost the tag are dropped),
  - `IsActorOnScreen` (cheap "was it drawn" check), `InvalidateHudCaches`, and a `stat CastleDefender` timer for the whole HUD chain + cache hit / scan counters.
  Same pins as the engine nodes. Only difference: a list can be up to 0.25 s old (new actors show a moment later; destroyed ones never show).
- `reparent_hud_ue.py`: BP_ZombieHUD's parent HUD -> CDHudBase (dry run, backup, compiles the whole chain, saves only without new errors; `--bp` for a copy first).
- `hud_swap_scans_ue.py`: swaps every GetActorOfClass / GetAllActorsOfClass / GetAllActorsWithTag node in the 11 HUD Blueprints for the cached twin,
  in place (all links and values move; old node removed), one Blueprint at a time, dry run, backup, saves only without new errors, `--skip` for nodes
  that must stay exact, `--only` for one Blueprint.
- The drawing, menus, shop and input logic stay in Blueprint for now. That is the next step (native draw helpers per level), after this one is measured.

## Expected
HUD scans become cache reads: about -5 to -10 ms of the HUD's 15 ms on i9 in a wave (estimate). The load-after-crash time does NOT change yet
(the graphs are still there); it improves only when the drawing moves to C++ in a later step.

## Order on i9 (after the round 1 build works; reviewer's order)
1. Build the module (README_CPP.md steps 1-6) with these two new files in `Source/CastleDefender/`.
2. `py <repo>/handoffs/cpp-500/reparent_hud_ue.py --dry-run`, then `--apply`. Play: the HUD looks and works exactly as before (nothing in any graph changed).
3. `py <repo>/handoffs/cpp-500/hud_swap_scans_ue.py` (dry run: the list of nodes per Blueprint), then `--apply --only BP_CommanderHUD`, Play-check,
   then the others one by one. Skip a node with `--skip <name>` if a menu must react the same frame.
4. Measure: `stat CastleDefender` (HUD DrawHUD time, cache hits vs scans) and `measure_split_ue.py` (UI group) before / after.

## Not done yet / risks
- Only the event graphs are scanned by the swap script (where the HUD exports show the scans); function graphs are listed by the dry run only if
  they live in the event graph. Check the dry-run list against `CDEditorTools.find_expensive_calls('/Game/CastleDefender/Gameplay/Castle')`.
- C6 / C7 (Blueprint throttles of the Commander / Barracks tag scans) can stay: the cached node behind them is just cheaper.
- Not compiled, not run. i5's editor crashed at 18:09 (not during an i5 script), so nothing here was dry-run on i5 either.
