# Colossus animation set (card #519, follow-up of #449)

By `adjustedfilm (Claude)`, 2026-11-06. Owner: *"i want to enhance zombies animations accordingly ... specially clossals"*
(accordingly = the #449 brute method: new motion authored for the body itself, Stranger Things quality).
How it was made, with every number: [PROGRESS.md](PROGRESS.md). The brute's research notes still apply: `../brute-creature-449/RESEARCH.md`.

**Kind:** two editor Python scripts (`cz_colossus_ue.py` = the colossus, hand-off #520; `zw_walkers_ue.py` = the ordinary
walkers, stage 3 below) + one pin change in BP_ZombieWallBreaker. The giant death wiring follows when export #518 lands.

## What was wrong (measured on the i5 copy of the project)

The colossus is `BP_ZombieWallBreaker`: the ordinary zombie rig (`SK_Zombie`, 73 bones) scaled **x3.9-5.8** (`GiantScale`)
with `MaxWalkSpeed` **90**. It plays the human clips with `PlayAnimation`: `A_Walk` (1.2 m steps at scale 1, a 4 s cycle:
at x5 the feet travel 5x faster than the body, so the giant moonwalks at a human tempo), `A_Attack` at
`GlobalAnimRateScale` 0.45 for the smash, and a human death.

## The set (3 clips, hand-authored on the real rig in Blender, analytic leg IK, UE round-trip exact to 0.0001 deg)

| Clip | Frames | What |
|---|---|---|
| `CZ_Walk_Colossus` | 79 (2.6 s loop) | a step every 1.3 s (a 9 m body: sqrt(5) x a human's period). In place, the feet at **30 cm/s at scale 1 = the breaker's MaxWalkSpeed (30 x GiantScale) at every size** (0.01 cm/s skate error; needs the rate-1.0 paste, step 4). Long double support, a fast impact drop + slow recovery on every footfall, 6 cm sway (30 cm in game), hunched predator lean, heavy late arms, stabilised head, curled claws. Knees 109-129 deg, worst bone turn 4.4 deg/frame |
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
4. **The breaker paste** (`gen_cz519.py` -> `BP_ZombieWallBreaker_CZ519_graph.txt` + `manifest_cz519.json`, built on
   export #518 of 09:24 and pre-checked: fix_impure, applyall merge `Validation: OK`, +54 link entries as expected):
   - add the variable from [VARIABLES.md](VARIABLES.md) (`GiantDead`, Boolean), compile;
   - EventGraph > Ctrl+A, Ctrl+C -> `live.t3d`, then
     `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/colossus-anim-449/manifest_cz519.json --out merged.t3d`
     (or, if the graph has not changed since 09:24, paste `merged_cz519.t3d` as it is);
   - EventGraph > Ctrl+A, Delete, Ctrl+V, Refresh All Nodes, compile, save.
   What it does: (a) **GlobalAnimRateScale 0.2 -> 1.0** at BeginPlay and after every smash. The breaker slowed the human
   walk to 0.2 to hide its 1.2 m steps; the giant walk is authored at **30 cm/s per unit of scale = MaxWalkSpeed
   (30 x GiantScale)**, so at rate 1 the feet match the ground at any size. (b) The smash plays `CZ_Attack_Smash`
   (same 79 frames / blow 26 as A_Attack, so the 0.45 rate and the 1.5 s / 1.7 s delays keep their timing). (c) An
   AnyDamage override: Parent (HP, gore, XP, the candle melt, the human death montage) -> if Dead and not GiantDead ->
   GiantDead = true, rate 1.0, `PlayAnimation(CZ_Death_Colossus)`: single-node mode takes over, so the giant death
   plays from frame 0 instead of the human montage.
5. Play.

**Rollback:** `py ".../cz_colossus_ue.py" --restore` puts `A_Walk` (animation + notifies) back exactly; set the pin back to `A_Attack`.

## Tests (Play; `ColossusFromWave` 1 and `ColossusEvery` 1 on BP_BattleDirector, then ForceNextWave)

1. **Walk:** slow, ponderous steps, about one every 1.3 s; **the feet stay planted** while the body moves at 90 (no
   moonwalk); the body sways and dips on each footfall; the stomp shake/notify fires on the footfalls.
2. **Smash:** at the wall it gathers both arms overhead for about 2 s, then a heavy two-fisted blow. The wall damage
   lands at the same moment as before (the BP timing is untouched).
3. **Death:** the killing blow snaps the head back, the knees give, the whole mass topples forward and slams. The
   candle melt (C++, `cd.Zombie.CandleMelt`) hides the mesh about 2.3 s in, so the slam at 2.0 s still shows; turn the
   melt off to see the full 4 s. No T-pose, no stand-up.
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

## Stage 3: the ordinary walkers (`zw_walkers_ue.py`, run AFTER the colossus script)

**What was wrong (measured):** the six retargeted hit clips (`ZA_Taking_Damage_A-F`) pop 90-173 deg in one frame on
38-43 bones in their first 3 frames (retarget pops); `ZA_Run_A` and `A_Run` pop their toes 37-39 deg with the feet
13 cm under the ground; `A_Death` pops 45 deg; `ZA_Attack_D` pops 46 bones. The blend space speeds (0 / 113 / 249 / 350)
were already matched by the Master, so the walkers do not skate: the problem is the motion itself.

11 clips, same pipeline, written INTO the clips the game plays (lengths and strike frames kept, so the ABP, the
`AM_ZFlinch_*` / `AM_ZDeath_A_Death` montages and the BP timers need no change):

| Game clip | Now holds | Frames | What |
|---|---|---|---|
| `ZA_Idle_A` (blend space 0) | `ZW_Idle_Shamble` | 119 (4 s loop) | sway on planted feet, ragged breathing (3 per loop), a lolling scan, a head twitch, a double sniff, claw flex |
| `ZA_Walk_A` (113) | `ZW_Walk_Shamble` | 30 (1.0 s) | shamble matched to 113 cm/s (0 skate), the right leg drags (limp 0.6: shorter lift, a hitch, a bigger drop), arms reaching 28 deg, lolling head. Keeps 2 `AN_ColossusStomp` notifies on the footfalls |
| `ZA_Run_A` (249) | `ZW_Run_Lurch` | 20 (0.67 s) | lurching run at 249, arms reaching 45 deg, lean 18 deg, a slight limp |
| `A_Run` (350) | `ZW_Sprint` | 16 (0.53 s) | full sprint at 350, lean 22 deg, arms grasping ahead |
| `ZA_Taking_Damage_A/B/C` | `ZW_Hit_Flinch` | 20 | a chest hit: 3-frame snap back, arms thrown up, heavy recovery |
| `ZA_Taking_Damage_D/E` | `ZW_Hit_Stagger` | 40 | a heavy hit: thrown back, a step back that catches the weight, recovery |
| `ZA_Taking_Damage_F` | `ZW_Hit_Side` | 30 | struck on its left: the torso twists right, the head whips |
| `A_Hit` | `ZW_Hit_Heavy` | 60 | knocked down onto a knee, a beat, climbs back up |
| `A_Death` (montage `AM_ZDeath_A_Death`) | `ZW_Death_Collapse` | 89 | head snaps back, the legs fold, a kneeling beat, topples face-down with a slam, the claws close, an arm drags; holds |
| `A_Attack` (strike frame 26) | `ZW_Attack_Claw` | 79 | the left arm winds up behind, the body twists into a rake to 0.9 m ahead, the other arm low |
| `ZA_Attack_D` (strike frame 16) | `ZW_Attack_Bite` | 60 | both hands grab forward at chest height, the head lunges and the bite clamps with a shudder |

Previews: `preview/ZW_*_before_after.mp4` (11). Not written: `ZA_Walk_B/C` (unused by the blend space), the 11 other
death picks (they are `ZA_Burst_*` blob-rise clips and `ZA_Laying_Idle_B`, used as deaths by the `AM_ZDeath_*` montages: a
later BP change could point them at `ZW_Death_Collapse` and variants), crawls, bursts, impaled, laying.

Steps (Master): `git pull`; `py ".../zw_walkers_ue.py" --dry-run` (11 import lines, 14 `would back up` lines);
`py ".../zw_walkers_ue.py"` (about 40 s; every `<-` line `"max_diff_deg": 0.0`; `ZA_Walk_A` shows 2 stomp notifies); compile
`ABP_Zombie` (nothing to change); Play. Rollback: `--restore` (tested: exact). Backups: `Zombie/Anims_BAKZW/` (14 clips).

Tests (Play, wave 1+): idle zombies sway, breathe and twitch; walkers limp at 113 with planted feet; runners lurch with their
arms out; a hit snaps the zombie back and it recovers without a pop; a heavy hit drops it to a knee; a death folds and
falls face down and stays; the claw rake and the bite land at the old moments (the damage timing is untouched).

## Stage 4: real deaths for every pick (`zw_deaths_ue.py` + the BP_Zombie paste `manifest_zd519.json`)

BP_Zombie picks one of 12 death montages; 11 wrap the blob-rise clips `ZA_Burst_A-K` and `ZA_Laying_Idle_B` (a zombie
dies by playing its spawn animation). The raw burst clips are untouched (the wave manager plays them for the rise);
only what the death picks play changes.

| New clip / montage | Frames | What |
|---|---|---|
| `ZW_Death_Back` / `AM_ZDeath_ZW_Back` | 89 | hit from the front: thrown back, a stumbling step, sits down hard, flat on its back, the arm slides off |
| `ZW_Death_Side` / `AM_ZDeath_ZW_Side` | 89 | struck on its left: the legs give, it crumples onto its right side, the top arm and leg flop down |
| `ZW_Death_Crumple` / `AM_ZDeath_ZW_Crumple` | 89 | the strings cut: straight down onto both knees, a beat, folds forward into a heap |
| `ZW_Death_Collapse` / `AM_ZDeath_ZW_Collapse` | 89 | the #521 collapse as a montage |

Picks after the paste: Back x3 (`Burst_A/D/G`), Side x3 (`B/E/H`), Crumple x3 (`C/F/I`), Collapse x3 (`K`, `Laying_Idle_B`
and `A_Death`). Previews: `preview/ZW_Death_Back|Side|Crumple_before_after.mp4` (before = the blob rise they replace).

Steps (Master, after #521): `py ".../zw_deaths_ue.py" --dry-run` then `py ".../zw_deaths_ue.py"` (imports 3 clips, creates
the 4 montages in `Zombie/Anim/Death/`, DefaultSlot, blend 0.25; touches no existing asset). Then the paste: BP_Zombie >
EventGraph > Ctrl+A, Ctrl+C -> `live.t3d`;
`python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/colossus-anim-449/manifest_zd519.json --out merged.t3d`
(or paste `merged_zd519.t3d` if the graph has not changed since export #518); Ctrl+A, Delete, Ctrl+V, Refresh All Nodes,
compile, save. Pre-checked on #518: 11 pasted `Montage_Play` nodes, 33 rewires, `Validation: OK`, +44 link entries as
expected. Rollback: paste the `live.t3d` you copied (the 4 new montages can stay). Test: kill 10 zombies, see four
different real deaths and never a blob rise; the candle melt still runs on top.

## Stage 5: crawlers, the spawn rise, the knock-down (`zw_crawl_rise_ue.py`, no paste)

**What was wrong (measured):** the two crawl loops slide (planted hands at about 50 cm/s against `MaxWalkSpeed` 45) and
pop. The spawn "rise" `ZA_Burst_H` is a 5-frame pop from the rest pose onto the ground followed by 85 motionless frames,
played at rate 0.5 while the BP waits 5.4 s: the dead pause the owner rejected on #164 (the blob VFX is Codex's part;
this is the body). `ZA_Laying_Idle_A` (after a knock-down) pops 124 deg.

| Game clip | Now holds | Frames | What |
|---|---|---|---|
| `ZA_Belly_Crawling_A` | `ZW_Crawl_A` | 60 (2 s loop) | belly crawl, both arms alternate, hands placed by IK and matched to **45 cm/s (0.00 skate)**, legs trail and kick a little, head up and searching |
| `ZA_Belly_Crawling_B` | `ZW_Crawl_B` | 66 | the one-arm drag variant (the right arm barely pulls), more roll |
| `ZA_Burst_H` | `ZW_Rise` | 90 | **continuous**: a heap on the ground -> the head lifts with a shudder -> pushes the chest up -> onto one knee, the foot plants and catches the weight -> hauls up into the walking stance by frame 78 (in game x0.5 = 5.2 s, inside the 5.4 s wait) |
| `ZA_Laying_Idle_A` | `ZW_Laying_Stunned` | 180 | lies stunned, a twitch, rolls flat, a weak push that sags, then up on the hands ready to rise |

Previews: `preview/ZW_Crawl_A|ZW_Crawl_B|ZW_Rise|ZW_Laying_Stunned_before_after.mp4`. Note: `ZA_Burst_H` is also wrapped
by the death montage `AM_ZDeath_ZA_Burst_H`; after stage 4's paste that montage is no longer picked.

Steps (Master, any time after #521): `py ".../zw_crawl_rise_ue.py" --dry-run` (4 import + 4 `would back up` lines), then
`py ".../zw_crawl_rise_ue.py"` (every `<-` line `"max_diff_deg": 0.0`). Rollback `--restore` (tested exact). Tests: a
crawler keeps its hands planted at 45; a spawning zombie rises in one continuous motion with no pause and no pop; a
zombie knocked flat by a cannon or a charge lies stunned and gets up without a snap.

## Stage 6: the colossus roars at spawn and looms when stuck (paste 2: `manifest_cz519b.json`)

Two more colossus clips (imported by the updated `cz_colossus_ue.py`, so re-run it or import them by hand):

| Clip | Frames | What |
|---|---|---|
| `CZ_Roar` | 90 (3 s) | gathers (sinks, curls, fists), explodes up and open with a trembling roar and a head sweep, settles |
| `CZ_Idle_Loom` | 120 (4 s loop) | a heavy breath, the head swings left then right searching, a twitch, the claws flex |

The paste (`gen_cz519b.py` -> `BP_ZombieWallBreaker_CZ519b_graph.txt` + `manifest_cz519b.json`, 16 nodes, 8 rewires) goes
ON TOP of paste 1: it was merged on the fresh 10:05 export (which already holds #522): `Validation: OK`, +36 link
entries as expected, `merged_cz519b.t3d`. (a) BeginPlay: after the stats, PlayAnimation(CZ_Roar) -> Delay 3 s -> the
old walk and the BreakerThink timer: the giant roars once before it moves. (b) The #317 stuck watchdog: when
`StuckTicks` becomes 1 it plays the loom idle (loop) instead of walking in place; when it moves again it plays the
walk again, then the old reset. Steps: EventGraph > Ctrl+A, Ctrl+C -> `live.t3d`; `applyall merge --live live.t3d
--manifest handoffs/colossus-anim-449/manifest_cz519b.json --out merged.t3d` (or paste `merged_cz519b.t3d` if the graph is
still the 10:05 one); Ctrl+A, Delete, Ctrl+V, Refresh All Nodes, compile, save. Tests: a spawning colossus roars for
3 s, then walks; one wedged against a wall looms and breathes instead of treadmilling, and walks on when freed.

Note on the whole-BP exports made after 10:00: they list every EventGraph node twice (a generic-named, unlinked copy
with the same NodeGuid). `t3d_eventgraph.js` drops the copies (95 on the breaker, 843 on the zombie, which is exactly
what the Master counted), so applyall sees the real graph.

**Crowd desync (checked, no change needed):** `BPC_ZombieDesync` already sets each zombie's `GlobalAnimRateScale` to a
random 0.82-1.18 and yaws it +-15 deg at BeginPlay, and the wave manager staggers spawns, so walkers drift out of step
within a cycle or two. A per-instance start offset in the blend space would remove the first second of lock-step; not
worth an ABP edit now.

## Rules applied

INDUSTRY_SECRETS §0 rule 8, §3.4 #2 (speed match, no play-rate hack), #5 (no pops). RESEARCH.md: Gilman's retime-don't-stretch
(the giant's tempo from sqrt(scale)), catch the weight (impact dip + slow recovery), overlap lags x1.6 for the giant;
Hickel's weight from accents; anticipation >= 0.4 s, blow over 6 frames, long settle; the death holds and goes limp.
