# #44 Zombie towers: zombies stack to climb the wall

By `adjustedfilm (Claude)`, 2026-10-31. This is the owner's "game changer" pick. Card #44: *zombies climb on each other
to build a wobbling tower against the castle wall… cut or blast the bottom zombie and the whole tower topples: onto the
horde (great), or onto your own wall posts and towers (bad).*

Built on `handoffs/exports/master/2026-10-30b`:
- BP_Zombie (`Dead`, `Mesh`, `CharacterMovement`);
- BP_ZombieWaveManager (`Wave`);
- BP_NoticeHUD `PushNotice`;
- the LineTraceSingle / BreakHitResult pin layouts copied from BP_SoldierSword.

Towers stand at the existing `BP_WallBreachSpot` actors (#138), so they only form where the wall has a breach spot.

## Pre-checks (done)

| Graph | fix_impure | applyall check |
|---|---|---|
| `BP_ZombieTower_graph.txt` | no changes | 325 nodes, 382 links, **OK** |
| `BP_TowerDirector_graph.txt` | no changes | 73 nodes, 91 links, **OK** |

**No existing Blueprint changes.** There are no self-calls to own events (the #254 lesson): the polls run on timers, and the
director calls `Init` on the tower.

## What the player sees

1. **From wave 4:** when 6+ zombies crowd one breach spot (within 7 m), a tower starts there and the banner warns
   **"Zombies are piling up against the wall!"**
   - At most 2 towers stand at once, and a new one needs a 40 s cooldown.
2. **The tower grows:** every 1.8 s the nearest zombie (within 12 m) climbs onto it.
   - Its look (mesh, animation and materials, so the zombie variants show) becomes the next figure in the pile.
   - **The layers are 5 / 4 / 3 / 2 / 1**, each one standing on the shoulders below and leaning a little more onto the
     wall. The layer height is sized to the real wall: a trace finds the ground and the wall top.
   - The tower **sways**, more the higher it gets.
   - The absorbed zombies stay alive (hidden and frozen), so the wave counts stay right.
3. **Full (15) = breach:** every 2 s one of them climbs out **onto the wall-walk**, and the banner says **"The zombies are
   over the wall!"** New zombies keep joining and climbing.
4. **Topple it:** hit the base (sword, bolts or cannon; 600 HP). **"The zombie tower topples!"** It falls like a tree in
   1.1 s.
   - **Hit from the walls or the inside:** it falls **outward onto the horde**. The landing does 400 damage in 3.5 m, and
     30 % of its zombies get up there, the rest die (their own death code, so kills and gold count).
   - **Hit from outside (the hero on the ground):** it falls **into the wall**, and the crush lands on your wall posts.
     That's the "real decision about *when*" the card asks for.

## Steps (Master)

1. Run `py "<repo>/handoffs/zombie-towers-44/setup_towers44_ue.py" --dry-run`, then without `--dry-run`. It makes, in
   `/Game/CastleDefender/Gameplay/Siege`:
   - BP_ZombieTower, with Base and Tier00..Tier14;
   - BP_TowerDirector.
2. Paste the BPVar lines of `VARIABLES_BPVar.txt`: 28 on BP_ZombieTower, then 9 on BP_TowerDirector. Compile each.
3. Paste `BP_ZombieTower_graph.txt` into BP_ZombieTower, and `BP_TowerDirector_graph.txt` into BP_TowerDirector. Compile
   and save.
4. Run `py ".../setup_towers44_ue.py" --place` (dry-run first). It places one **TowerDirector** in ThirdPersonMap.

## Tests (Play)

1. **Quick start:** set `FromWave` = 1 and `GatherMin` = 3 on the placed TowerDirector. Let zombies reach the walls: a
   tower starts at a breach spot with the banner.
2. **Watch it grow:** zombies vanish into the pile one by one, and the pile rises and sways against the wall.
3. **Let it fill:** zombies appear on the wall-walk one every 2 s, with the "over the wall" banner.
4. **Shoot the base from the wall** (crossbow or cannon): it topples outward, the landing kills the zombies under it, and
   a few get up.
5. **Next tower, hit from outside on foot:** it falls into the wall.
6. No "Accessed None" in the log.

## One-minute fixes / tuning

| If / to | Change |
|---|---|
| "in" and "out" are the wrong way at some spot | `CastleCenter` on BP_ZombieTower (default 964, 1750, 0 = the player start) must be a point inside the castle |
| tower figures too low or too high | `Spacing` is computed. Clamp it in the graph's `FClamp` (0.9–2.6 m), or change `LeanPerLayer` (25 cm) |
| harder / easier to topple | `HP` (600) |
| more / fewer towers | `MaxTowers` (2), `Cooldown` (40 s), `GatherMin` (6), `FromWave` (4) on the TowerDirector |
| it falls the wrong way (pitch sign) | flip the `-90.0` Multiply constant in the Fall section |

## Rules applied

- **INDUSTRY_SECRETS §3, motion:**
  - each tier keeps the zombie's own animation, so the pile writhes rather than standing frozen;
  - the sway grows with height;
  - the fall eases in like a tree under gravity.
- **Readable from far away:** the banners and the sway.
