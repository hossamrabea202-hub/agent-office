# #455 Fire pit: no wood through wood (i5, 2026-11-03)

Owner (Alien, card #455): "No woods over lapping each others (follow real life references)".

**Cause (my #451 bug):** `campfire_logs451.py` aimed the 7 leaning logs at one apex and extended them 5-18 % past it, so their tops ran through each other. The 2 bed logs also cut into the leaning ones.

**Fix:** `campfire_logs455.py` builds the same log shapes, but places them like a real teepee:
- the leaning logs REST on each other near the top;
- a BVH overlap test (3 mm safety skin) pushes any intersecting log out 1 cm at a time;
- a settle pass pulls each tip back until it touches a neighbour, so nothing floats.

Result: 0 overlapping pairs, every leaning log within 0.6-1.3 cm of a neighbour, 2,232 tris. Before/after: `out/ab455.png` (left #451, right #455).

## Apply (i9, Master, Alien not in Play)
1. `git pull`
2. `py handoffs/firepit-455/firepit455_ue.py import`: new asset `SM_FirePitLogs455`, the bark / end-grain MIs copied from 451, saved.
3. `py ... swap --dry-run`: 1 line, `FirePit_Firewood451 SM_FirePitLogs451 -> SM_FirePitLogs455`.
4. `py ... swap --apply`, look at the courtyard fire pit, save the map.
5. Revert: `swap --revert`.

Test: from the courtyard, no log passes through another; the logs lean and rest on each other; the fire VFX still sits in the middle.
