# #530 Tentacle style pass: strike and hunting idle (adjustedfilm, 2026-11-06)

Bar: Netflix Stranger Things. New clips for `SK_CorruptedTentacle_01`, with a wiring script. Lab-tested in the scratch project.
**Not play-tested and never seen in the engine's viewport.** The strike previews use a Python copy of the game's FABRIK.

## What changes

| Clip | Length | Performance |
|---|---|---|
| `AS_Tentacle_Strike` | 7.6 s, hit on frame 96 | The arm gathers into an S-coil while the head searches, locks on and goes still, then a growing 14 Hz quiver. The strike takes 5 frames, base first, tip last. On contact the head buckles and a shock runs down the arm while the heavy middle keeps going. The head drags out last, then a damped wave, a shiver and rest. |
| `AS_Tentacle_Hunt_A` | 40 s loop | Head-led looks with holds, a startle twitch right before a look, a breath that climbs the arm. |
| `AS_Tentacle_Hunt_B` | 40 s loop | Same language: lurks low and curled, slower and deeper breath, different looks and twitches. |
| `AS_Tentacle_Hunt_C` | 40 s loop | Same language: tall and jumpy, quicker breath, four twitches. |
| `AS_Tentacle_Wounded` | 20 s loop | Sag to one side, laboured breaths, tremor bursts. **Imported only, nothing plays it.** It needs a decision on when a tentacle counts as wounded. |

Measured by `gen_style.py`:

| Clip | Worst turn | Outside the strike | Tip travel from frame 1 | Loop seam |
|---|---|---|---|---|
| Strike | 37.6 deg/frame at the hit | 3.8 deg/frame | 118 m (clip alone, before FABRIK) | ends at rest |
| Hunt A | 11.2 deg/frame (a twitch) | | 50 m | 0.000 deg |
| Hunt B | 10.0 deg/frame (a twitch) | | 33 m | 0.000 deg |
| Hunt C | 9.7 deg/frame (a twitch) | | 38 m | 0.000 deg |
| Wounded | 5.9 deg/frame | | 8 m | 0.000 deg |

For scale, the old idle sways its tip within a 27 m radius. If Hunt A looks too big in the level, lower `amp` in `gen_style.py`.

**Idle mapping, written into the clips in place:** Ripple -> A, Sway000 and Sway020 -> B, Sway030 and Sway040 -> C, and Polish457 A/B/C -> A/B/C if they exist.
So every placed tentacle and its JellyShell change with no level edit and keep their own rate and start position.

**Strike timing (`wire_strike_ue.py`):** a strike now plays `AM_Tentacle_Strike` when State becomes 1. Defaults change as follows, so the hit stays on frame 96:

| Default | Old | New |
|---|---|---|
| WobbleTime | 2.4 | 2.4 |
| WindupTime | 1.3 | 1.39 (computed as 4.0 - WobbleTime - 0.21) |
| StrikeTime | 0.3 | 0.21, which is 5 frames |
| RecoverTime | 2.0 | 3.0, the long settle |

A strike occupies its tentacle 1 s longer, so strikes come slightly less often.

## Steps (Master, editor idle, not in Play)

1. `git pull`.
2. If the #457 slot fix is not applied: `py handoffs/tentacle-anim-457/fix_pp_input_ue.py --dry-run`, then `--apply`. Without the slot no montage shows.
3. `py handoffs/tentacle-style-530/style_install_ue.py --dry-run`, then run it without flags. Expect 5 imports, 1 montage, and every `wrote` line at `worst deg 0.0`.
4. `py handoffs/tentacle-style-530/wire_strike_ue.py --dry-run`, then `--apply`. Expect `exec links [True, True, True, True]` and `hit at 4.0 s`. Save all.
   - The script compares compile errors with those before it ran, and does not save if it added any.
   - It stops if `K2Node_VariableSet_11` or `CX_55` is missing. Then send i5 a fresh export of BPC_TentacleStrike.
5. Play.

**Revert:** `wire_strike_ue.py --revert` and `style_install_ue.py --restore`. Run the revert on the same PC as the apply, because it reads `wire_strike_backup.json`.

## Tests in Play

- Idle: no two tentacles move alike. Heads turn first and the body follows, with holds. Occasional sharp twitches, no pops, no visible loop jump at 40 s.
- Strike: coil, stillness and quiver, the 5-frame whip, the hit FX exactly on contact, the head dragging out last, about 3 s of settle back into the idle.
- A cannon hit during a strike: the reaction montage replaces the strike clip in the same slot and FABRIK keeps aiming. The arm must not pop. This is the combination I trust least.
- JellyShell, sacs and hitboxes follow, and the shell does not drift from the arm during the idle.

## What was tested, and what was not

Lab `ckw/zlab`, headless UE 5.8. Logs are in `ckw/ztools/style/t*.txt`.

| Test | Result |
|---|---|
| Install dry-run | Changes nothing, lists 5 idle clips |
| Install | 5 x `worst deg 0.0` against the authored clips |
| Restore | 0.00004 deg and 0 cm at worst against the backups, over 17 frames on all 14 bones |
| Reinstall | 5 x 0.0 deg |
| Wire dry-run, apply | 4 exec links True, errors unchanged, hit at 4.0 s |
| Wire apply when already wired | Refuses (`already wired, 5 nodes`) |
| Wire revert | 5 nodes removed, relinked, defaults back to 1.3 / 0.3 / 2.0 |

**Not verified:**
- The montage playing under FABRIK in the engine. Headless has no game running. The composite in the previews is my simulation, with Reach 90 m and one target position assumed.
- A clean compile in the real project. The lab copy already fails on `OnRevengeHit` (nodes `CX_6`, `CX_7`) because its delegate source is missing there, both before and after wiring.
- The live node names. The lab copy dates from the 11-04 sync, so a fresh export is requested. The script stops safely if they changed.

**Not in this card:** soldier targeting. The lab's BPC_TentacleStrike only targets cannons, and #333's pack targeting and blast are still design notes. These clips do not depend on the target, so they will suit soldiers once that exists.

## Previews (`preview/`, real mesh, Workbench)

- `Strike_before_after.mp4`: today | new, both with the simulated FABRIK. `StrikeClip_only.mp4`: the clip alone.
- `Hunt_A_before_after.mp4`: Ripple | Hunt A, 24 s. `Hunt_B_vs_C.mp4`: the two variants, 24 s.
- `Wounded_before_after.mp4`: Ripple | Wounded, 12 s. `sheet_strike.png`, `sheet_hunt.png`: stills.

## Regenerating

```bash
blender -b --factory-startup -P gen_style.py -- <SK_CorruptedTentacle_01_Anim_Ripple.fbx> fbx/Tentacle_STRIKE.fbx STRIKE
```

`style_render.py` needs the licensed mesh FBX, which stays in `ckw/ztools/fbx_tent` and is never committed. The clip FBX files here hold no mesh.

## Rules applied

INDUSTRY_SECRETS 0.8 and 3.4 (motion is the biggest tell, variation per creature, each actor keeps its own play rate, no pops except the impact). #449 RESEARCH.md: anticipation, overlap along the arm, the mass keeps going on impact, a long settle.
