# Enraged tentacles (adjustedfilm, 2026-11-06)

Owner: "what if we kept hitting it, why would it stay idle". A tentacle under attack now fights back instead of returning to the calm idle.

## What it does (`wire_rage_ue.py`, BPC_TentacleSpit)

| State | Trigger | What you see |
|---|---|---|
| Enraged | Any hit. Every new hit restarts the 8 s. | Fast thrashing loop with a strain tremor and head jabs. The head leans at the attacker. It spits every 2 hits with a 3 s cooldown, instead of 3 and 4 s. |
| Enraged and hurt | Same, below 35 % health | Sags, shakes harder, slower lurches. |
| Calm | No hit for 8 s | The clip blends out over 1 s, the head relaxes, spit timing returns to normal, and the hunting idle shows again. |
| Wounded | Calm and below 35 % health | The wounded idle. A new hit stops it at once. |

Hit reactions, spit, catapult, strike and death all keep priority. Each loop picks a random rate between 0.85 and 1.15, so tentacles stay out of step.

**Not changed:** strike frequency. Strikes already retry every 0.5 s, so only spit gets faster.

## Steps (Master, editor idle, not in Play)

1. `git pull`. Needs #534. Run #535 and #536 too if not done.
2. `py handoffs/tentacle-style-530/import_spit_ue.py`. This re-imports the spit and catapult clips, which is harmless, and adds three clips and their montages.
3. `py handoffs/tentacle-style-530/wire_rage_ue.py --dry-run`, then `--apply`. It does not save if it adds compile errors, and stops if a node name changed. Save all.
4. Play.

Revert: `wire_rage_ue.py --revert`. Run it before `wire_spit_ue.py --revert`.

## Tests in Play

- Keep hitting a tentacle: it thrashes the whole time, with reactions on top, and never shows the calm idle.
- Stop for 8 s: it settles back into the hunting idle with no pop.
- Bring it under 35 %, keep hitting, then stop: it shakes and sags, then goes to the wounded idle. Hit it again: straight back to rage.
- Kill it: the death clip plays and nothing restarts over it.
- Spit, catapult and strike still play during rage, and the head lean does not fight them.
- Hit one tentacle only: the others keep hunting.

## Tested, and not tested

Lab, headless: import OK. Wiring dry-run, apply (122 nodes), refuses a second apply, revert (3 relinks True), re-apply. Compile errors the same before and after.

**Not run in Play.** The lab cannot compile BPC_TentacleSpit. Unconfirmed: all the transitions above, and the blend between rage and hit reactions. Below 35 % is measured from the highest health seen, which is the 100000 set at BeginPlay.

## Previews

`preview/Enraged_vs_hunting.mp4`, `preview/EnragedHurt_vs_Wounded.mp4`, `preview/sheet_enraged.png`: clips alone, without the head lean. Enraged: worst turn 14.3 deg/frame, seamless. Hurt: 9.1 deg/frame, seamless.
