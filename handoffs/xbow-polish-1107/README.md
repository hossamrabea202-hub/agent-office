# #561 Crossbows AAA polish, pass 1: Noble crossbow textures (checkking, 2026-11-07)

Owner: "polish the xbow weapons in the game, following realism rules and maximum quality achievable with AAA methods".
Study: [RESEARCH.md](RESEARCH.md). Built on the live textures exported 11-02 (`Crossbow_1K_BaseColor`,
`Crossbow_1K_AO-...-Metallic`, same as in the 11-07 i5 sync). The mesh, UVs and normal map are unchanged.

## What was wrong (pbr_check on the live textures)
- 67 % of the wood darker than 30 sRGB: the stock read as a black-red blob.
- All steel and brass below 150 sRGB: metal looked like grey plastic, no reflections.
- Metallic was a flat 0.88 / 0.82 everywhere (54 % in-between): physically meaningless, reads as CG.
- Roughness nearly one value per part (0.30 wood, 0.36 metal).

## What pass 1 does (`tools/calib2d.py`, 2048 px, same UVs)
Oiled red-walnut stock (63 sRGB, grain kept), bone inlay kept and aged, bright worn steel (192 sRGB) under a dark oxide
film in patches and cavities, rubbed bare on edges; aged brass with tarnish in the recesses; metallic strictly 0/1;
roughness from grain, scratches and wear. Result: `pbr_check` **OK** (it was 3 fails). Lookdev (before | after, locked
exposure): fast chat `/files/102641_xbow561_lookdev_pass1.png`.

Rules applied: KB 1 (calibrated values), 3 (wear by physics), 4 (bevel width from texel density); INDUSTRY_SECRETS
rules 1, 2, 3, §1.3.1 Composite Texture, §1.3.6 Sharpen4, §1.3.8 Masks compression; owner decal rule (new material only).

## Master: steps (licensed textures are NOT in the repo)
1. Download `http://100.87.149.123:8765/files/102639_xbow561_textures_pass1.zip` and unzip to a folder, e.g.
   `C:/Unreal Backups/_claude/xbow561/` (2 PNGs: `T_Crossbow561_BaseColor.png`, `T_Crossbow561_ORM.png`).
2. `git pull`, then in the Output Log (Python):
   `py "<repo>/handoffs/xbow-polish-1107/apply_xbow561_ue.py" --src "C:/Unreal Backups/_claude/xbow561"`
   Dry run. Expect: `noble mesh slots using ... = [0]` (or a list), both sources `OK`, and the list of assets that
   reference the old material. **If BP_Crossbow / BP_TradeShowcase / BP_SoldierXbow are in that list with a material
   override on the crossbow component, note it on #561** (the swap then also needs those overrides).
3. `... --import`: imports both textures into `/Game/CastleDefender/Equipment/crossbow/Polish561/`, duplicates the old
   material to `M_Crossbow561`, re-points its 2 texture samples, sets Composite Texture on the ORM, compiles, saves.
   Expect `built ... (2 samples re-pointed, compiled, saved)`. Anything with `ERROR` → stop, post the line on #561.
4. Owner OK on the before/after first (`M:` rule). Then `... --apply`: swaps the mesh slot(s), writes
   `apply_xbow561_backup.json`. Undo: `... --revert`.

## Tests
1. `M_Crossbow561` compiles with no errors; the old `Crossbow___Baked_PBR_1K` is unchanged.
2. Play, daylight: the hero's Noble crossbow shows brown walnut wood (not black), cream bone inlay, steel that catches
   the sky on its edges, darker steel flats, yellow brass trim. Same at Vesna's showcase and on crossbow soldiers if they
   use this mesh.
3. Walk 15-20 m away: no white sparkle on the metal (Composite Texture).
4. LV4 electric overlay (#77) still shows on top.

## Next (pass 2, after export request #562)
Real-mesh retex (`tools/laptop2/retex.py`): ray-bevel edges, grip polish, dust, micro normal; lookdev on the actual
crossbow; same treatment for Golden Sovereign and the bolt.
