# #322 Big mouth (Flesh Brute) in the waves, and the gate brutes removed (part 1 of 2)

By `adjustedfilm (Claude)`, 2026-10-31. Owner `W:`: *"polish big mouth animations, integrate them in waves not just a couple
at the gate at the start which actually needs to be removed"*.

- **Part 1 (here):** brutes come in the waves, and the brutes placed at the gate are removed.
- **Part 2:** the animation polish. It waits on export request "#322: export BP_FleshBrute …", because no export has the
  brute's graph or its FB_ animations yet.

## Pre-checks (done)

| Check | Result |
|---|---|
| `fix_impure.py BP_BruteDirector_graph.txt` | **no changes** |
| `applyall check` | 74 nodes, 94 links, **Validation OK** |
| existing Blueprints changed | **none**. It only reads each BP_ZombieWaveManager's `Wave` and `HorseSpawnLocation` (10-30b export). |

## What the player gets

- **Brutes join the waves from wave 3:**

  | Wave | Brutes per wave manager |
  |---|---|
  | 3–4 | 1 |
  | 5–6 | 2 |
  | 7–8 | 3 |
  | 9+ | 4 (cap) |

- **They arrive spread through the wave,** one every 9 s, not as a clump.
- **They come from where that manager's half-horse zombies come from** (`HorseSpawnLocation`), within 3 m, so they march in
  with the wave. If a manager has no horse spot, they use the manager's own location.
- **A loaded game doesn't replay old waves:** the director remembers each manager's wave from the start.
- **No brutes stand at the gate at the start any more.**

## Steps (Master)

1. Run `py "<repo>/handoffs/brute-waves-322/setup_brute322_ue.py" --dry-run`, then run it without `--dry-run`. It makes
   `/Game/CastleDefender/Gameplay/Castle/BP_BruteDirector`.
2. Open BP_BruteDirector. Paste the 9 lines of `VARIABLES_BPVar.txt` one at a time, then Compile.
3. Paste `BP_BruteDirector_graph.txt` into its EventGraph. Compile and save.
4. Run `py ".../setup_brute322_ue.py" --finish --dry-run`, then without `--dry-run`. It sets `BruteClass` = BP_FleshBrute
   and places one **BruteDirector** in ThirdPersonMap.
   - If the log says "set BruteClass by hand", pick BP_FleshBrute in BP_BruteDirector's Class Defaults. That's a
     one-minute fix.
5. Run `py ".../setup_brute322_ue.py" --remove-gate-brutes --dry-run`. Check that it lists only the brutes at BreachSpot
   A/B/C, then run it without `--dry-run`. Every removed one is logged in `removed_brutes.txt` (label, location,
   rotation).

## Tests (Play)

1. **At the start:** no brute at the gate.
2. **Waves 1–2:** no brutes.
3. **Wave 3:** one brute marches in with the wave, from the horse side. To test quickly, set `FromWave` = 1 on the
   placed BruteDirector.
4. **Wave 5:** two brutes, about 9 s apart.
5. No "Accessed None" in the log.

## Tuning (BruteDirector details panel)

| Variable | Default | What it does |
|---|---|---|
| `FromWave` | 3 | first wave with a brute |
| `Every` | 2 | one more brute every N waves after that |
| `MaxPerWave` | 4 | cap per wave per manager |
| `Stagger` | 9 s | gap between brutes of one wave |
