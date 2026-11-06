# i9 Master run-sheet: zombie + colossus animation sets (#519)

From `adjustedfilm (Claude)` on the i5, 2026-11-06. Owner: *"hand everything to i9"*. Everything below is pushed on `main`.
Nothing is in the game yet. Do these in order; each step is pre-checked in a scratch copy (dry-run, install, exact restore).

## 1. Colossus set (hand-off #520), about 1 minute

```
git pull
py "<repo>/handoffs/colossus-anim-449/cz_colossus_ue.py" --dry-run
py "<repo>/handoffs/colossus-anim-449/cz_colossus_ue.py"
```
Expect: 3 imports into `Zombie/Anims_Colossus/`, then `A_Walk <- CZ_Walk_Colossus {"max_diff_deg": 0.0, "notifies": ["AN_ColossusStomp", "AN_ColossusStomp"]}`.
Backup: `Zombie/Anims_BAKCZ/A_Walk`. Rollback: `--restore`.

Then one pin by hand: `BP_ZombieWallBreaker` > EventGraph > the `PlayAnimation` node after `SM_Rate` (named `SM_Anim`):
**New Anim To Play = `Anims_Colossus/CZ_Attack_Smash`**. Compile, save. (Same 79 frames and blow frame as `A_Attack`, so
`SM_D1` / `SM_D2` and the 0.45 rate keep their timing.)

## 2. Walker set (hand-off #521), about 1 minute

```
py "<repo>/handoffs/colossus-anim-449/zw_walkers_ue.py" --dry-run
py "<repo>/handoffs/colossus-anim-449/zw_walkers_ue.py"
```
Expect: 11 imports into `Zombie/Anims_Walkers/`, 14 `<-` lines all `"max_diff_deg": 0.0`, `ZA_Walk_A` with 2 stomp notifies.
Backups: `Zombie/Anims_BAKZW/` (14). Rollback: `--restore`. Compile `ABP_Zombie` (nothing to change). Save all.

## 3. Play-test (post a clip on #519)

- Colossus (`ColossusFromWave` 1, `ColossusEvery` 1 on BP_BattleDirector, ForceNextWave): slow heavy steps about every
  1.3 s, feet planted (no moonwalk), stomp shake on the footfalls; at the wall a 2 s overhead gather, then the smash,
  wall damage at the same moment as before.
- Walkers (wave 1+): idles sway/breathe/twitch; walkers limp at 113 with planted feet; runners lurch with arms out; hits
  snap back with no one-frame pop; a heavy hit drops to a knee; a death folds face-down and stays; claw and bite land at
  the old moments.
- Blends smooth, no new log errors. If anything is off, `--restore` on the script in question and say so on #519.

## 4. Export #518 (so the giant death can be wired)

Whole-BP T3D of `BP_ZombieWallBreaker` and `BP_Zombie` into `handoffs/exports/adjustedfilm/colossus-anim/`. With it I build
the paste that plays `Anims_Colossus/CZ_Death_Colossus` on the colossus's death (the parent now plays deaths as montages,
which a `PlayAnimation` breaker cannot run, so I need the current graph, not the 11-03 copy).

## Owner decision (still open)

`fbx/*.fbx` (14 clips) are in the public repo: skeleton animation only, no mesh, no textures (as with #516). If the owner
wants them out, say so: I remove them and Taildrop them to the i9 instead.

Full detail: [README.md](README.md), [PROGRESS.md](PROGRESS.md). Previews: `preview/*.mp4` (real mesh, before | after).
