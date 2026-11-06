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

## 5. Hit direction + stagger by weapon: yours to finish (owner, 2026-11-06 12:20)

**What the graph does today (BP_Zombie, export #518 / fresh-1106):** `ReceiveAnyDamage` (K2Node_Event_ZB60) -> gore,
HP, hit-stop -> `K2Node_VariableSet_6` (LastFlinchAt) -> `K2Node_IfThenElse_15` (condition `K2Node_PromotableOperator_17`
<- `K2Node_CallFunction_58`, a front/back test) -> `Montage_Play` `AM_ZFlinch_Back` (K2Node_CallFunction_59) or
`AM_ZFlinch_Front` (K2Node_CallFunction_60), both at **InPlayRate 3.0**. Deaths: 12 picks, now the ZW montages (#523).

**Clips you can use (already in the game since #521, written into the old assets):**
`ZA_Taking_Damage_A/B/C` = `ZW_Hit_Flinch` (chest, 20 f), `ZA_Taking_Damage_D/E` = `ZW_Hit_Stagger` (heavy, a step back,
40 f), `ZA_Taking_Damage_F` = `ZW_Hit_Side` (struck on its LEFT, twists right, 30 f), `A_Hit` = `ZW_Hit_Heavy` (knocked
to a knee, 60 f), `ZA_Laying_Idle_A` = `ZW_Laying_Stunned` (flat, 180 f, after LaunchCharacter). Missing: a RIGHT-side
twist and a back flinch; say the word and I author them in 10 minutes (`tools/zperf_walkers.py`: HIT_SIDE mirrored).

**Two ways to get the side:** (a) BP: dot/cross of (DamageCauser location - zombie location) with the actor forward
and right vectors -> front / back / left / right (wrong for bolts and cannon when the causer is the shooter or the
projectile); (b) C++: `AZombieBase::TakeDamage` already has the hit point for the candle melt; expose the local-space
hit direction (or an enum) to BP and branch on it. Stagger by weapon: branch on the causer class / damage amount:
sword -> flinch (A-C), bolt -> flinch, cannon or charge -> `ZW_Hit_Heavy` or the knock-down path (LaunchCharacter +
`ZA_Laying_Idle_A`), >= 40 % MaxHP in one hit -> stagger (D-E).

**Tools (handoffs/colossus-anim-449):** `tools/t3d_nodes.js <export> <words>` lists any export's nodes with their
links (I used it for every trace above); `t3d_eventgraph.js <whole-BP export> <out>` flattens your whole-BP export into
the clipboard layout applyall reads and drops the duplicate unlinked copies your post-10:00 exporter writes;
`gen_cz519.py` / `gen_zd519.py` show the bpkit paste pattern (nodes + manifest rewires, `fix_impure`, `applyall merge`).
