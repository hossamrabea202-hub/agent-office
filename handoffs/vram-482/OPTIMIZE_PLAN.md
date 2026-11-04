# Reaching AAA ms levels: plan (card #487, i5, 2026-11-04)

Owner's order: "go through codes and game system we built and find out how to optimize to reach AAA ms levels". Owner's priority: the most realistic castle; real stone stays.
Details: `BP_AUDIT.md` (Blueprints), `TICK_SCAN.md`, `vram_tags.csv`. Nothing here is timed unless it says so.

## Target
| Machine | Target | Budget per frame |
|---|---|---|
| Strong PC, packaged build | 30 fps first (the project is already set to 33.3 ms), then 60 fps with upscaling | 33.3 ms, then 16.7 ms |

Game thread, render thread and GPU each must fit that budget; they run side by side, so they are not added together.
Suggested 16.7 ms split for later: GPU 15, game thread 12, of which Blueprints in battle 5 and HUD 2. These are planning numbers, not measurements.

## What we know, in ms
| Measure | Value | Source |
|---|---|---|
| Battle, about 84 zombies, editor, T1000 | 250-330 ms (3-4 fps) | i9, 11-03/04 |
| 8 torches, no wave mentioned | 64 ms (15.7 fps) | i9, 11-03 |
| Editor overhead | about 25 ms | i9, 10-31 |
| Half resolution | -12 ms of 42 | i9, 10-31 |
| Lumen off | -7 ms of 42 | i9, 10-31 |
| No shadows | -6 ms of 42 | i9, 10-31 |
| Grime cards, decals | 0 ms of 42 | i9, 10-31, before the 875 strips were counted |
| Zombie LODs 10x fewer verts | no gain | i9, 11-04 |
| Fixes A-D | no gain | i9, 11-03 |

Open question: a wave may add about 200 ms, and nothing tried so far touched it. The two numbers come from different tests, so this is a clue only.
Other unknowns in every number: the castle rebuild since, CPU at up to 97 C, video memory over budget.

## Order of work
### 1. Measure (nothing else is safe to rank without this)
- `wave_sweep_ue.py` on i9 at a wave: what each feature costs. Requested.
- `stat unit` with and without a wave: Game vs Draw vs GPU.
- A packaged build on the strongest PC: the only true number.

### 2. Safe now, needed on any machine
| Fix | File | Gain |
|---|---|---|
| Video memory: HUD art to BC7, 8K capped, streaming on | `textures482_ue.py` | Could be large if memory is the limit |
| Shop keys that can never fire (logic bug, not speed) | `shop_keys_fix_ue.py` | Flares, Medics, Cavalry, Upgrades keys work |
| Half-horse + wasp Think every frame, frame-counted timers | crowd session, needs intended numbers | Real 30 vs 60 fps bug + sync path search per frame |

### 3. If the sweep shows the game thread matters (it will on a strong PC at 60 fps)
From `BP_AUDIT.md` section E, highest first:
1. Commander tag scan every frame: use the existing CommanderRef.
2. 5 zombie + 3 soldier world scans outside the crowd code: read the registry, or run on events.
3. Soldiers' remaining scans (crowd session, high risk).
4. 10 tentacles: one shared trace, cached lookups.
5. 41 mines: tick interval, cached refs, off when unseen.
6. HUD: 11-level chain, about 330 exec + 1780 pure nodes every frame with menus closed: early-outs per closed panel.
7. Pool FX, bolts and blood bursts: helps spikes rather than the average.

### 4. If the sweep shows the GPU matters
Depends on the numbers. Candidates: grass (about 43,000 tufts), translucency, particles, fog, shadows, resolution. Never baking castle stone (owner). Grime strips (`bands482_ue.py`) for draw calls.

### 5. On a strong PC: spend the headroom on realism
Already lowered for the T1000, to raise again if the budget allows: Virtual Shadow Maps, Lumen probes + mesh SDF, shadow resolution, cloud shadows, resolution 100 %.

## Limits of this audit
- Blueprints are 11-03 exports, older than fixes A-F. `BPC_VesnaTrade` draw path and `BP_CorruptionBubble_Hero` were not readable.
- Instance counts are from i5's disk, not the Master.
- The scan's triangle counts use Nanite fallbacks, so they understate real stone.
