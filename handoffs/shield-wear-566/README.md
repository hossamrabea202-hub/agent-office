# #566 Swordsmen shield: different scratches and wear on every soldier

By i5 `adjustedfilm (Claude)`, 2026-11-07. Owner: "different variations of scratches and wear down so not all swordsmen soldiers be wearing a duplicate".

**Why they were duplicates:** `BP_SoldierSword` (construction script) makes a dynamic instance of `M_Shield_Paint_AAA` on the shield (`SM_Shield`, element 0) and sets a random `Tint` (0.55-1.15) and `Wear` (0-0.3). The shader code used a fixed scratch seed (1.7) and fixed noise, so chips, scratches and dirt were identical on every soldier; Wear only added roughness.

**Fix:** a NEW material `/Game/CastleDefender/Equipment/Weapons/Shield/Var566/M_Shield_Paint_Var` (the live `M_Shield_Paint_AAA` is not touched). It is the same shader and wiring (BaseColor x Tint, Roughness + Wear, world-space normal), plus a per-soldier seed hashed from the Tint and Wear the BP already sets. Each soldier gets his own chip layout, scratch directions, 0-3 sword cuts into the wood, dirt level, wear level and sun fade. `WearSeed` param: -1 = automatic (default), 0 = the original look, > 0 = fixed.

Preview (offline numpy port, stand-in wood colour; first = original, then 6 soldiers): `preview_seeds.png`.

## Steps for the Master (editor)
1. `py "<repo>/handoffs/shield-wear-566/make_shield_paint_var_ue.py" --dry-run`: expect `wood texture ... found` and `target free`.
2. `py "<repo>/handoffs/shield-wear-566/make_shield_paint_var_ue.py" --build`: expect `BUILD DONE`, no shader errors in the Output Log.
3. **One field in BP_SoldierSword** (Construction Script): the `Create Dynamic Material Instance` node on **Shield** (Element Index 0, today Source Material = `M_Shield_Paint_AAA`): set **Source Material = `M_Shield_Paint_Var`**. Nothing else changes (the Tint and Wear nodes stay). Compile, save.
4. Undo: set Source Material back to `M_Shield_Paint_AAA`, then `--revert`.

## Tests
- Play, look at 6+ swordsmen side by side: chips, scratches and cuts differ on each shield; the colour family is the same as before.
- Hero's Gilded Shield (uses `M_Shield_Paint_AAA` directly) must look unchanged.
- Not done on i5: lookdev in UE (the i5 editor cannot open the game yet, missing C++ binaries). The script was run headless in an empty UE 5.8.4 test project: built OK, compiles with 0 errors, 1,719 pixel instructions vs 1,661 for the original (+3.5%).

Rules applied (INDUSTRY_SECRETS section 0): 3 (every wear layer has a cause: impacts chip the rim first, cuts from sword strokes, dirt low and at the edges, sun fade), 2 (roughness varies with chips, cuts and dirt), 10 (same shader family for all soldiers). New material only, live one untouched.
