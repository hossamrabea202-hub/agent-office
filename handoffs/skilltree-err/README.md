# BP_SkillTreeHUD leftover hero-cast error (i5 / adjustedfilm, 2026-11-02, i9's queue item 3)

Built on i9's export `handoffs/exports/adjustedfilm/skilltree-err/BP_SkillTreeHUD_EventGraph.txt` (10:36, after i9's fix).
Found with `handoffs/hud-split/castreads.js` (lists every read of a cast's output that is outside the cast's success path).

## Cause
The SP tick chain (`SPTickIn.then_0`) runs: level-up Branch `spIfLevelUp7` → `spIfNotFirst8` → Set SPT → Set SPN →
**cast `spAsHero2`** → Set SPPrevLevel. The cast runs **last**, but its output (`spGetLevel3` = hero Level) is read
**before** it by the Branch condition and by Set SPN. Every tick they read the previous tick's cast result: None on the
first frames and whenever the hero is missing (menu, death, respawn) → "Accessed None ... AsBP_Third_Person_Character_2"
at the Branch. (`CX_68` and `spAsHero2_c1`, the other two hero casts, are clean.)

## Fix: 4 links, no nodes added or removed (`fix_sphero_ue.py`)
| Pin | Was | Now |
|---|---|---|
| SPTickIn.then_0 | spIfLevelUp7 | **spAsHero2** (cast first) |
| spAsHero2.then | spSetSPPrevLevel13 | **spIfLevelUp7** |
| spIfNotFirst8.else | spAsHero2 | **spSetSPPrevLevel13** |
| spSetSPN12.then | spAsHero2 | **spSetSPPrevLevel13** |

CastFailed stays unlinked: with no hero, the level-up check is skipped that tick (as before).

## Apply (i9, Master)
1. `py "<repo>/handoffs/skilltree-err/fix_sphero_ue.py" --dry-run` → every node "found", every pin "ok", the `->` lists
   match the "Was" column.
2. `py ".../fix_sphero_ue.py"` → rewires, compiles, saves BP_SkillTreeHUD (one heavy save: post 'saving' first).
3. Undo: `--revert`.

## Checks (Play, 35 s like before)
- [ ] 0 "AsBP_Third_Person_Character_2" errors from BP_SkillTreeHUD (was 17-390 per run).
- [ ] Level up once: the skill-point gain still shows (SPN / SPT), and only once per level.
- [ ] Open the menu / die and respawn: no new errors.
