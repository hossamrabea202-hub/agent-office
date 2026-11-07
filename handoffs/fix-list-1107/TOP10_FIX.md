# Castle Defender: top 10 fixes (i5 / checkking, 2026-11-07)

Only fixes to what already exists. No new features. Most important first: what the owner sees most, then what breaks play.
Sources: owner play bugs in i9's report (cafeteria #25, comment 6702700372), fast chat 1706, open cards, the i5 game copy
synced today (`C:\UnrealProjects\Castle Defender 5.8`, read only), `handoffs/gpt-review-polish`. Nothing here is changed
or handed off yet. "Likely cause" is not proven unless it says so.

| # | Fix | Size |
|---|---|---|
| 1 | Day looks dark, brown and washed out | medium |
| 2 | Half zombies | medium |
| 3 | Play tests wipe the owner's saves | small |
| 4 | Man the walls: only 4 of 10 crossbows get there | medium |
| 5 | Sword slash is tiny | small |
| 6 | Hero face, hands and neck go black, with an orange glow | small |
| 7 | Inventory does not match what the hero wears | medium |
| 8 | Berserk comes too late (hero at 20 % HP) | small |
| 9 | Gate repair traps the hero; hero locked outside | medium |
| 10 | Pale disc on the tentacle bases | small |

---

## 1. Day looks dark, brown and washed out (owner play, fast chat 1706)
- **Player sees:** every day is a brown murk; colours flat, nothing reads as sunny.
- **Cause (found by i9, chat 1706):** `BPC_Weather` starts every run in Fog (`Today = 2`) and can never roll clear (`PClear = 0`),
  so fog eases up to 6x. Also sun intensity 2 / sky 1 against exposure metered at 5.66 / 2, a grey fog colour written
  by `BP_DayNight`, and a zombie tint on top.
- **Fix:** (a) `BPC_Weather`: clear weather possible and the default for day 1 (`PClear` > 0, `Today` = clear). (b) Lock
  exposure (manual EV) and set sun / sky to calibrated daylight per `handoffs/knowledge` (lookdev, locked exposure).
  (c) `BP_DayNight`: fog colour from the sky, not a fixed grey. (d) Keep the zombie tint only at night / in the realm.
  Before / after at hours 8, 10, 12, 15, 22 from the same two cameras as 1706.
- **Size:** medium (weather default is small; exposure + grade needs lookdev).

## 2. Half zombies (owner play, still open)
- **Player sees:** zombies with part of the body missing.
- **Likely cause:** the far-zombie GPU crowd (`CDHordeSubsystem` / `CDHordeAnimData`, 11-05) draws a crowd mesh with
  "one material per mesh slot"; a missing or wrong crowd material on some slots, or bone indices past the baked range,
  would draw only part of the body. Second suspect: the hand-off between crowd instance and real actor (promote/demote)
  showing both or neither for a frame. Not proven.
- **Fix:** `cd.Horde` off vs on A/B in one Play: if half zombies vanish, check every zombie type's crowd material array
  matches its slot count and re-run `-run=CDBakeHorde`; if they stay, check the gore/dismember state reset (#483 fix F
  "gore" wires) on spawn.
- **Size:** medium.

## 3. Play tests wipe the owner's saves (i9 report)
- **Player sees:** progress, armory and infection state gone after someone tests.
- **Cause:** Play-in-Editor writes the real slots `CastleSave`, `CastleSaveArmory`, `CastleSaveInfection`.
  `CDSaveGame.cpp` (`UCDSaveSubsystem::Save` / `LoadOrCreate`) has no check for an editor Play world.
- **Fix:** in `UCDSaveSubsystem`, when the world is a PIE world add a suffix (`_PIE`) to every slot name (load and save), so
  tests never touch the owner's files. Plus a one-off backup of the 3 slots before the next test.
- **Size:** small.

## 4. Man the walls: only 4 of 10 crossbows reach the wall (i9 report, card #209, #120)
- **Player sees:** order "man the walls", most crossbowmen stand in the yard; front gate-wall posts never used. Same
  family: soldiers cannot climb the round-tower stairs to man cannons (#120).
- **Likely cause:** posts placed where the navmesh does not reach (wall walks / stairs not connected after the castle
  rebuild; stair step height / agent radius too tight on the spiral).
- **Fix:** with Show Navigation, connect every post to the yard (nav links or fixed stair collision), move unreachable
  posts onto the mesh, and have the order skip a post that has no path and take the next free one. Test: 10 of 10.
- **Size:** medium.

## 5. Sword slash is tiny (owner play)
- **Player sees:** the blade trail is a small thin smear; hits feel weak.
- **Likely cause:** the new blade slash in the owner shader (i9 report) uses the trail width / socket distance of the old
  short sword, and the trail is scaled with the hero, not the blade length.
- **Fix:** set trail width from the blade length (base to tip sockets), longer life (~0.12-0.18 s), brighter core; check
  on each shop sword.
- **Size:** small.

## 6. Hero face, hands and neck go black, with an orange glow (card #442)
- **Player sees:** the face reads as a black blob with an orange shine.
- **Likely cause:** `VisorFill` light from #435 too hot and too close on the head, plus skin materials (head / hands) going
  dark under the new exposure (ties to fix 1).
- **Fix:** VisorFill: lower intensity, warm-white not orange, no specular on skin or drop it; check skin base colour and
  subsurface against the PBR checklist. Lit front shots before / after.
- **Size:** small.

## 7. Inventory does not match the hero (owner play)
- **Player sees:** the bag shows gear the hero is not wearing (or the other way round).
- **Likely cause:** inventory slots are filled from the save (`CastleSaveArmory`) while the hero mesh is set by
  `CDHeroGear` / `BPC_ObsidianSet` at start; the two are not refreshed from one source (Obsidian now off at start).
- **Fix:** one source of truth: on load and on every equip, the inventory UI reads the hero's equipped list, and the hero
  mesh is built from the same list.
- **Size:** medium.

## 8. Berserk comes too late, at 20 % HP (owner play)
- **Player sees:** Berserk only starts when the hero is almost dead, so it hardly helps.
- **Cause (code):** `CDCombatRules.cpp` notes "Berserk starts at 85" damage taken; the start check in `BP_Berserk` uses a
  near-death threshold. The end rule (`cd.Hero.BerserkEndDamage` 12) was just added.
- **Fix:** Decision: start at 50 % HP (the owner can tune it), as a CVar like the end rule
  (`cd.Hero.BerserkStartDamage`), and keep the heal-to-end rule.
- **Size:** small.

## 9. Gate repair traps the hero; hero locked outside (card #78)
- **Player sees:** repair the gate while standing in it and the hero is stuck inside the gate; or locked out.
- **Cause:** rebuilding restores the closed gate leaves with collision on top of the hero.
- **Fix:** the repaired gate comes back open; if the hero is outside and the gate is closed, the nearest free soldier
  inside pulls the lever (this is the owner's own fix design on #78, not a new feature).
- **Size:** medium.

## 10. Pale disc on the tentacle bases (owner play)
- **Player sees:** a light round patch on the ground where each tentacle comes out.
- **Likely cause:** the #539 spore skirt decal (i5's own work, chat 1707): after i9 moved the bases to where each arm meets
  the ground, the decal no longer sits under the arm and its pale centre shows.
- **Fix:** move the decal with the base (attach it), darker / wetter centre, soft edge fade, no flat albedo disc.
- **Size:** small.

---

## Next in line (did not make the 10)
- #447 / #451 courtyard stair walls: stepped white blocks behind the hero (rebuild as real masonry, owner asked).
- #67 / #104 hero cape clips through the body; soldier capes left lying on the ground.
- #218 ability slots 4-6 stay locked after leveling.
- #178 rock by the barracks has no collision.
- #19 crossbow camera lags when aiming up at a tentacle.
- Forge renders as white plastic (`SM_Camp_Forge` UVs, gpt-review-polish batch 4).
