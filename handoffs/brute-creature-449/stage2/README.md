# #449 stage 2: the Flesh Brute's new creature clip set (install)

By `adjustedfilm (Claude)`, 2026-11-06. Owner: *"i want stranger things netflix series quality"*, then option 2 (new
animation made for this body), then *"Good, do stage 2 / stage 3"* and *"Yes, build the handoff"*.
How it was made: [PROGRESS.md](PROGRESS.md). Research: [../RESEARCH.md](../RESEARCH.md).

**Kind:** one editor Python script. No Blueprint paste.
**Run after #515** (stage 1, `../fb449_creature_ue.py`). The order doesn't break anything: stage 1 now skips the
clips that stage 2 has replaced.

## What changes in the game

11 hand-authored clips, made on the brute's own rig in Blender. The legs use analytic IK, so the feet never slide. They
are imported into `FleshBrute/Anims_Creature/`. The #449 layer (jaw, tongue, flesh, heft) runs on them. Then the
script **writes them into the clips the game already plays**, so the BP, the montages and the blend space need no rewiring:

| Game clip (what the BP / blend space calls) | Now holds | Notes |
|---|---|---|
| FB_ZA_Idle_A (blend space 0) | **CR_Idle_Hunt** | heavy breathing, weight shift, hunting head twitch, sniff, claw flex (4 s loop) |
| FB_A_Walk (blend space **71.5**) | **CR_Walk_Heavy** | crouched lumber matched to MaxWalkSpeed 71.5, no foot skate (was 20, so the brute mostly jogged) |
| FB_A_Run (blend space **170**) | **CR_Charge** | heavy charge; it only plays if the brute ever goes faster than 71.5 |
| FB_A_Attack | **CR_Attack_Slam** | overhead two-hand slam. **Same length (79 frames); the hit lands on frame 26 as before** |
| FB_ZA_Attack_D | **CR_Attack_Swipe** | claw whip + bite lunge. **Same length (60 frames); hit at frame 14–15** |
| FB_A_Hit, FB_ZA_Taking_Damage_A / D | **CR_Hit_Front** | 0.9 s: snap, knees buckle, heavy recovery |
| FB_ZA_Taking_Damage_B / E | **CR_Hit_Left** | |
| FB_ZA_Taking_Damage_C / F | **CR_Hit_Right** | |
| FB_A_Death | **CR_Death_Forward** | kneels, topples onto the belly, slam, claw twitch; holds the last frame |

Imported but **not wired yet**: **CR_Roar_Threat** (threat roar) and **CR_Death_Side** (topples onto its side). Both
need small BP changes (roar on first sight, a random pick between the 2 deaths, hit direction from the hit's side).
That needs a fresh BP_FleshBrute export (request filed with this hand-off).

Untouched: crawls, bursts (blob rise), laying, impaled and the other attack clips (stage 1 layer only).

## Steps (Master, i9)

1. `git pull` (this folder has `fbx/` with the 11 clips, 9.5 MB).
2. Save all. Run the dry run: `py "<repo>/handoffs/brute-creature-449/stage2/fb449_stage2_ue.py" --dry-run`
   The log lists 11 imports, 13 `would back up … and write …` lines and 3 `BS` lines, then `DONE dry-run, nothing changed`.
3. Install: `py "<repo>/handoffs/brute-creature-449/stage2/fb449_stage2_ue.py"` (about 30 s). Every `FB_… <- CR_…`
   line must show `"max_diff_deg": 0.0`. Backups: `FleshBrute/Anims_BAK449S2/` (13 clips) and
   `Anim/BS_FleshBrute_Locomotion_BAK449S2`.
4. Compile ABP_FleshBrute (Anim/) and BP_FleshBrute (nothing to change in them). Save. Play.

**Rollback:** `py ".../stage2/fb449_stage2_ue.py" --restore` puts all 13 clips and the blend space back exactly. It was
tested: same frame counts and lengths, pose difference < 0.0001°.

## Tests (Play, wave 3, or `FromWave` = 1 on the BruteDirector)

1. **Idle:** the brute breathes, shifts its weight, twitches its head and sniffs. The maw is mostly closed with the
   teeth showing.
2. **Walk:** a heavy, crouched lumber. **The feet don't slide** at its normal speed, and there's no jogging.
3. **Slam attack:** arms overhead, a held beat, then a heavy blow down. **The damage lands when the arms hit**, the same
   moment as before.
4. **Swipe attack:** a claw whip across with a bite. The damage is on the whip.
5. **Hits:** a sharp snap and a buckle. No one-frame pops.
6. **Death:** it falls forward onto its belly and stays down (no stand-up, no T-pose).
7. Blends between all of them are smooth (the ABP's 0.2–0.25 s crossfades). No new log errors.
8. Post a Play clip on #449 / this hand-off.

## Pre-checks done here (scratch copy of the project, never the game)

| Check | Result |
|---|---|
| Blender → UE round-trip of a clip | 0.0005° / 0.0004 cm |
| Authoring checks (per clip, printed) | feet planted with 0.00 cm/s skate; knees never locked; worst bone turn ≤ 17°/frame except the strikes and the side-death impact (27–48°, by design) |
| In UE, `ue_pops.py` | 0 bones over 12°/frame in walk and idle |
| Layer on the CR clips | strike frames found: slam 26, swipe 15; footfalls found in walk and charge |
| Install | 13/13 written, `max_diff_deg` 0.0; lengths and frame counts match the CR clips |
| `--restore` | all 13 + blend space back; same lengths; < 0.0001° |
| Stage 1 re-run after stage 2 | skips the stage-2 clips (guard) |
| Previews | `preview/*.mp4`, real mesh, before \| after (local renders) |

Not done: **Play-testing in the game.** The previews are Blender workbench renders, not the game's lighting.

## Notes

- `fbx/*.fbx` hold only skeleton animation (the brute's bone names and transforms), with **no mesh and no textures**.
  If the owner prefers them out of the public repo too, send them by Taildrop like TGA's binaries, and the script reads
  them from `stage2/fbx/` on the i9.
- Rules applied: INDUSTRY_SECRETS §0 rule 8 and §3.4 (#2 the speed match instead of a play-rate hack, #5 no pops,
  #9 variation via the per-clip jaw seed). Film rules from RESEARCH.md: Gilman's retiming, heft and catch-the-weight,
  overlap lags; Hickel's weight from accents, not slow motion; anticipation → 5–6-frame strike → long settle.
