# #322 part 2: Flesh Brute animation polish (blends, heavy gait, play-rate variety, HP ×4)

By `adjustedfilm (Claude)`, 2026-10-31. Owner `W:`: *"polish big mouth animations"*. Part 1 (waves) is hand-off #324.
Built on the Master's export `handoffs/exports/adjustedfilm/brute-322/BP_FleshBrute_EventGraph.txt` (2026-10-31 15:18).
Generator: `gen_brute322p2.py` (Blender's Python, `-I`).

## What the player gets

- **No more snapping.** Before, every clip change was a hard cut, because the brute used `PlayAnimation` (single-node
  mode). Now its mesh runs **ABP_FleshBrute**: 2 clip channels and a Two Way Blend. Each new clip fades in over 0.25 s.
- **Same behaviour.** Every one of the 40 clip calls, 12 play-rate calls and 1 set-position call in the brute's graph is kept
  and moved onto the ABP:
  - one-shots (death, laying, bursts, hits) still **hold their last frame**;
  - the backwards burst (rate −1) still plays backwards;
  - `GlobalAnimRateScale` (25 uses) still works.
- **Heavy gait matched to the move speed.** Walk, run and crawl cycles follow the brute's real speed (speed ÷ max speed),
  times Heavy 0.92. The rate stays within 0.8–1.2 (INDUSTRY_SECRETS §3.4 rule 2, the ±20 % rule).
- **Play-rate variety.** Each brute rolls its own rhythm (0.9–1.06) at spawn. Loops start at a random point of the cycle
  (§3.4 rule 9), so a group never walks in step.
- **HP ×4.** The 3 MaxHP sets (by ZType) go from 260 / 60 / 100 to **1040 / 240 / 400**.

## Pre-checks (done)

| Check | Result |
|---|---|
| `applyall check BP_FleshBrute_EventGraph_v2.txt` | 782 nodes, 883 links, **Validation OK** (export: 777 / 877; −52 unused Mesh getters, +53 FBAnim getters, +4 BeginPlay nodes) |
| `applyall check ABP_FleshBrute_EventGraph.txt` | 102 nodes, 120 links, **Validation OK** |
| `applyall check ABP_FleshBrute_AnimGraph.txt` | 8 nodes, 7 links, **Validation OK** |
| `fix_impure.py` ABP EventGraph | **no changes** |
| `fix_impure.py` BP_FleshBrute v2 | wants to split `CX_538` and `K2Node_DynamicCast_ZV33`. Those are the brute's **own existing** casts, already wired into the exec chain, so they need no split (and the split would leave one-way links). Left as they are. |
| `PlayAnimation` / mesh `SetPlayRate` / `SetPosition` left in v2 | **0** |

## Steps (Master)

1. `py "<repo>/handoffs/brute-anim-322/setup_brute322p2_ue.py" --dry-run`, then run it without `--dry-run`. It makes
   **ABP_FleshBrute** (SK_FleshBrute skeleton) and a backup **BP_FleshBrute_BAK322**.
2. **Open ABP_FleshBrute:**
   1. Paste the 18 lines of `ABP_VARIABLES_BPVar.txt` one at a time on the VARIABLES header, then Compile.
   2. EventGraph: paste `ABP_FleshBrute_EventGraph.txt`. Compile.
   3. AnimGraph: paste `ABP_FleshBrute_AnimGraph.txt`. Wire **FB_Blend → Output Pose** (1 wire). Compile, save.
3. `py ".../setup_brute322p2_ue.py" --finish --dry-run`, then without `--dry-run`. It sets BP_FleshBrute's Mesh to
   Use Animation Blueprint + ABP_FleshBrute. If the log says `MANUAL:`, set those 2 fields in Class Defaults → Mesh → Animation
   (a one-minute fix).
4. **Open BP_FleshBrute:**
   1. Paste the line of `BRUTE_VARIABLES_BPVar.txt` (FBAnim). Compile.
   2. EventGraph: **Ctrl+A, Delete, then paste `BP_FleshBrute_EventGraph_v2.txt`** (the whole graph, with the changes in it).
      Compile, save.

Rollback: BP_FleshBrute_BAK322 is the brute before step 4.

## Tests (Play)

1. Brutes walk in with wave 3 (or `FromWave` = 1 on the BruteDirector for a quick test). **No T-pose**, no snapping
   between walk, attack, hit and death.
2. Two brutes side by side don't step in sync.
3. A blocked brute's legs slow down; a running one doesn't skate.
4. Death and laying poses still hold (no stand-up after the clip ends). The burst-backwards get-up still plays.
5. A brute takes about 4× the hits it took before.
6. No "Accessed None" in the log. If there is one on `FBAnim`, step 3 didn't set the Anim Class.

## Tuning (ABP_FleshBrute class defaults)

| Variable | Default | What it does |
|---|---|---|
| BlendTime | 0.25 | seconds of crossfade between clips |
| Heavy | 0.92 | gait weight: lower = heavier, slower steps |
| GaitMin / GaitMax | 0.8 / 1.2 | gait rate limits (±20 % rule) |
| JitterMin / JitterMax | 0.9 / 1.06 | each brute's own rhythm |

**Rules applied (INDUSTRY_SECRETS):** §0 rule 8 (motion is the biggest tell), §3.4 #2 (±20 % rate rule), #5 (blended
transitions instead of cuts), #9 (per-zombie variation: play rate, random start).
