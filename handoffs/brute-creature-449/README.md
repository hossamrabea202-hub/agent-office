# #449 Flesh Brute ("big mouth"): creature animation layer, film-style

By `adjustedfilm (Claude)`, 2026-11-06. Owner: *"re animate the big mouth.. his animation looks silly. check how Marvel
and Netflix and Scifi animate then apply"*, and *"i want stranger things netflix series quality"*.
Research and sources: [RESEARCH.md](RESEARCH.md).

**Kind:** one editor Python script. No Blueprint paste and no ABP change.
**Built on:** the live assets in the laptop copy of `Castle Defender 5.8` (synced 11-03): `FleshBrute/Anims/FB_*` (37 clips),
`Anim/BS_FleshBrute_Locomotion` and `Anim/ABP_FleshBrute` (i9's 11-02 build).

## Why it looked silly (measured on all 37 clips)

1. **The mouth is dead.** `jaw`, `tongue_01-03` and the 9 flesh bones move **0.0°** in every clip. The artist's rest pose is
   the showcase gape, so the brute walks around with its maw frozen wide open.
2. **It jogs.** The blend space puts FB_A_Run (a 0.8 s human jog) at speed 100, and the brute moves at 71.5. Most of the
   time it plays the jog.
3. **No weight.** Nothing answers the pelvis swing: no flesh, no head lag and no footfall shock.
4. **Even timing and pops.** The attacks are even-spaced human swipes. 16 clips snap **25–99° in one frame**, mostly at
   their start (Taking_Damage_B: 99°).

## What the script does

It bakes these layers into the FB_* clips themselves. The blend space, the montages and all 40 BP calls pick them up
with no rewiring.

| Layer | What you see |
|---|---|
| Jaw performance | The maw rests **closed to a parted, teeth-showing breath**. It gapes past the showcase pose in the attack wind-up (the telegraph), **snaps shut on the strike**, drops slack on hits, hangs open on death and roars on burst, with an 8–12 Hz tremble while it gapes. Closed = 50°, measured on the real mesh (`preview/jaw_side_*.png`) |
| Tongue | It lags the head and curls with the jaw |
| Flesh | Belly, sides, breasts and butt react to acceleration (belly 3.0 Hz, damping 0.35, soft limit 6 cm), so the steps and hits shake the mass |
| Heft | Each footfall sends a shock up spine → neck → head. The head and neck lag the chest |
| Retime (attacks) | The wind-up lingers and whips into the strike, then a long heavy settle. **Strike frame and clip length unchanged**, so damage timing is the same |
| De-pop | Single-frame snaps over 25° are eased into their neighbours |
| Gait | The blend-space run sample moves 100 → 79 at rate 0.8 (the −20 % rule). It lumbers instead of jogging, and its speed is the same |

## Steps (Master, i9)

1. `git pull`.
2. Save all, then run the dry run:
   `py "<repo>/handoffs/brute-creature-449/fb449_creature_ue.py" --dry-run`
   The Output Log shows one `FB449 <clip> {...}` line per clip (37) and `DONE dry-run, nothing changed`.
3. Run it for real: `py "<repo>/handoffs/brute-creature-449/fb449_creature_ue.py"`. It takes about 15 s and saves:
   - the backups in `FleshBrute/Anims_BAK449/` (37 clips) and `Anim/BS_FleshBrute_Locomotion_BAK449`;
   - the baked `FB_*` clips (each tagged `FB449`) and the blend space.
4. Compile ABP_FleshBrute and BP_FleshBrute (there's nothing to change in them), then Play.

- **Too much or too little:** run `--strength 0.7` (or 1.2). It always re-bakes from the backups, so it never stacks.
- **Rollback:** `py ".../fb449_creature_ue.py" --restore` copies every clip back from the backup. For the gait, copy
  `BS_FleshBrute_Locomotion_BAK449` back over the blend space.

## Tests (Play, wave 3, or `FromWave` = 1 on the BruteDirector)

1. Idle and walk: the maw is **mostly closed** with the teeth showing, and opens and closes slowly as it breathes. It no
   longer hangs frozen open.
2. Walk: the brute lumbers with long, slower strides, not a jog. The feet don't skate more than before.
3. Attack: the maw opens wide in the wind-up, then slams shut on the hit. The damage lands at the same moment as before.
4. Hit: the head snaps, the jaw drops slack and the belly shakes. There's no one-frame pop at the start of the hit.
5. Death: the jaw hangs open. Burst (risen from a blob): a roar.
6. No new log errors. No T-pose.
7. Post a Play clip on #449.

## Pre-checks done here (scratch copy, never the game project)

Run in `C:\Users\hossam.rabea\ckw\fblab`, a separate UE 5.8 project holding a **copy** of the FleshBrute folder, headless:

| Check | Result |
|---|---|
| Dry run, all 37 clips | OK. FK matches Unreal's own pose **0.000 cm** on every clip |
| Apply | 37 clips baked and saved, 37 backups + BS backup on disk |
| Read back | The baked clips hold the new jaw: attack range 57°, walk breath 11° (before: 0° everywhere) |
| `--restore` | Restored clips are back to exactly 0° jaw motion |
| Renders on the real mesh | `preview/*.mp4` and `*.png`, before | after (workbench, local only) |

The full per-clip report (strike frames, footfalls, de-popped frames, jaw range, flesh amounts) is in
[lab_report_2026-11-06.json](lab_report_2026-11-06.json).

## Not done / limits

- **Not Play-tested in the game.** That's test list 1–7 above.
- The layer is baked, so a hit doesn't react to where it lands. The physics hit reaction (INDUSTRY_SECRETS §3.4 #6) is
  a separate card.
- **Stranger Things quality needs new source motion made for this body.** This layer fixes the three biggest tells on
  retargeted human zombie clips. The rest is a creature-specific clip set: hand-keyed, or a creature-performer mocap
  session (RESEARCH.md, "The honest ceiling"). The layer runs on top of a new set unchanged.

**Rules applied (INDUSTRY_SECRETS):** §0 rule 8 (motion is the biggest tell), §3.4 #2 (±20 % rate), #5 (no snapping: the
de-pop), #9 (variation: the per-clip jaw seed). Film rules: Gilman's retime, heft and catch-the-weight; ILM's speed with
accents; the Hulk face-carries-performance rule.
