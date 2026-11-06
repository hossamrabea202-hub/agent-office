# Colossus animation set (card #519, follow-up of #449)

By `adjustedfilm (Claude)`, 2026-11-06. Owner: *"i want to enhance zombies animations accordingly ... specially clossals"*
(accordingly = the #449 brute method: new motion authored for the body itself, Stranger Things quality).
How it was made, with every number: [PROGRESS.md](PROGRESS.md). The brute's research notes still apply: `../brute-creature-449/RESEARCH.md`.

**Kind:** one editor Python script + one pin change in BP_ZombieWallBreaker. The death wiring follows when export #518 lands.

## What was wrong (measured on the i5 copy of the project)

The colossus is `BP_ZombieWallBreaker`: the ordinary zombie rig (`SK_Zombie`, 73 bones) scaled **x3.9-5.8** (`GiantScale`)
with `MaxWalkSpeed` **90**. It plays the human clips with `PlayAnimation`: `A_Walk` (1.2 m steps at scale 1, a 4 s cycle:
at x5 the feet travel 5x faster than the body, so the giant moonwalks at a human tempo), `A_Attack` at
`GlobalAnimRateScale` 0.45 for the smash, and a human death.

## The set (3 clips, hand-authored on the real rig in Blender, analytic leg IK, UE round-trip exact to 0.0001 deg)

| Clip | Frames | What |
|---|---|---|
| `CZ_Walk_Colossus` | 79 (2.6 s loop) | a step every 1.3 s (a 9 m body: sqrt(5) x a human's period). In place, the feet matched to **90 cm/s at x4.85** (18.6 cm/s at scale 1, 0.01 cm/s skate error). Long double support, a fast impact drop + slow recovery on every footfall, 6 cm sway (30 cm in game), hunched predator lean, heavy late arms, stabilised head, curled claws. Knees 109-129 deg, worst bone turn 4.4 deg/frame |
| `CZ_Attack_Smash` | 79, blow on frame 26 | **same length and blow frame as `A_Attack`**, so `SM_D1`/`SM_D2` and the 0.45 rate keep their timing (in game: a 1.9 s wind-up, 5.9 s total). Step in, both arms gathered overhead, a held breath, a 6-frame two-fisted blow forward onto the wall face, the mass keeps dropping on impact (shudder), long settle, step back |
| `CZ_Death_Colossus` | 121 (4.0 s), holds the last frame | the blow lands, the head snaps back, the knees give, a kneeling beat, the whole mass topples forward and slams face-down with a tremble, a rebound, the claws close, one arm drags. Sprawled flat at the end |

Previews (Blender workbench, the real mesh, before | after, local renders): `preview/CZ_Walk_Colossus_before_after.mp4`,
`preview/CZ_Attack_Smash_before_after.mp4`, `preview/CZ_Death_Colossus_before_after.mp4`. In game everything is x3.9-5.8.

`fbx/*.fbx` hold only the skeleton animation (bone names + transforms), no mesh, no textures (same decision as #516;
if the owner prefers them out of the public repo, Taildrop them to the i9).

## Steps (Master, i9)

1. `git pull` (this folder: `fbx/` 2.6 MB, `preview/` 1.5 MB).
2. Save all. Dry run: `py "<repo>/handoffs/colossus-anim-449/cz_colossus_ue.py" --dry-run`
   Log: 3 `import` lines, one `would back up A_Walk ... write CZ_Walk_Colossus into it, stomps at [0.0, 1.3] s`, `DONE dry-run`.
3. Install: `py "<repo>/handoffs/colossus-anim-449/cz_colossus_ue.py"` (about 20 s). It imports the 3 clips into
   `Zombie/Anims_Colossus/`, backs up `Zombie/Anims/A_Walk` into `Zombie/Anims_BAKCZ/`, writes the giant walk INTO
   `A_Walk` (only the breaker plays it) and puts the two `AN_ColossusStomp` notifies on the new footfalls (0.0 s, 1.3 s).
   The `A_Walk <- CZ_Walk_Colossus` line must show `"max_diff_deg": 0.0` and `"notifies": ["AN_ColossusStomp", "AN_ColossusStomp"]`.
4. **One pin, on the spot:** `BP_ZombieWallBreaker` > EventGraph > the `PlayAnimation` node right after `SM_Rate`
   (node name `SM_Anim`): set **New Anim To Play = `Anims_Colossus/CZ_Attack_Smash`**. Compile, save.
5. Play.

**Rollback:** `py ".../cz_colossus_ue.py" --restore` puts `A_Walk` (animation + notifies) back exactly; set the pin back to `A_Attack`.

## Tests (Play; `ColossusFromWave` 1 and `ColossusEvery` 1 on BP_BattleDirector, then ForceNextWave)

1. **Walk:** slow, ponderous steps, about one every 1.3 s; **the feet stay planted** while the body moves at 90 (no
   moonwalk); the body sways and dips on each footfall; the stomp shake/notify fires on the footfalls.
2. **Smash:** at the wall it gathers both arms overhead for about 2 s, then a heavy two-fisted blow. The wall damage
   lands at the same moment as before (the BP timing is untouched).
3. **Death:** still the old human death (the giant death is imported but waits for the wiring paste, export #518).
4. Ordinary zombies are untouched (they never play `A_Walk`).
5. Post a Play clip on #519.

## Pre-checks done here (scratch copy `ckw/zlab`, never the game)

| Check | Result |
|---|---|
| Blender -> UE round-trip of `ZA_Walk_A` | worst 0.00007 deg / 0.002 cm |
| Walk: planted-toe skate, knees, snaps | 0.01 cm/s, 109-129 deg, 4.4 deg/frame |
| Smash / death snaps | 36.9 deg/frame on the blow only; death 14.2 |
| Install in the lab | see PROGRESS.md (dry-run, install, restore) |

Not done: Play-testing in the game; the death wiring; the ordinary walkers (next, same pipeline).

## Rules applied

INDUSTRY_SECRETS §0 rule 8, §3.4 #2 (speed match, no play-rate hack), #5 (no pops). RESEARCH.md: Gilman's retime-don't-stretch
(the giant's tempo from sqrt(scale)), catch the weight (impact dip + slow recovery), overlap lags x1.6 for the giant;
Hickel's weight from accents; anticipation >= 0.4 s, blow over 6 frames, long settle; the death holds and goes limp.
