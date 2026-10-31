# #263 Infection downsides: slower walk + missed hits (owner keeps the +50 % defense)

By `checkking (Claude)`, 2026-10-31. Paste-only. The dry-run merge on the full 10-30b hero export, stacked after #255,
passes: **Validation OK** (19 nodes).

While the hero is infected (`BPC_Infection.Infected`):
1. **Walk speed ×0.75.** At the top of Tick, `CharacterMovement.MaxWalkSpeed = BaseWalkSpeed × 0.75`, and back to
   `BaseWalkSpeed` when cured. `BaseWalkSpeed` is captured from the normal speed on the first tick.
2. **25 % of sword hits miss.** The sword damage gets ×0 on a miss, rolled per hit.

**Steps** (after #255):
1. Paste the 1 BPVar line from `VARIABLES_BPVar.txt` on the hero.
2. Export the hero EventGraph and merge `manifest_hero_263.json`.
3. Paste the 19 nodes, then Compile.

**Test:** get infected (below 30 % HP): the hero walks visibly slower and about 1 in 4 swings does nothing. Cure at Vesna:
the speed is back and every swing hits again.

**Note:** if a sprint or slow effect also sets MaxWalkSpeed, set it through BaseWalkSpeed instead. That's a one-minute
fix for the Master if it shows up.
