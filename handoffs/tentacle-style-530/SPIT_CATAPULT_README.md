# #533 Tentacle spit and catapult (adjustedfilm, 2026-11-06)

Owner: spit blobs must land in front of the hero when he or soldiers attack; a cannon hit must be answered by swaying back like a catapult and throwing blobs into the castle. Bar: Stranger Things.

**Why the spit was invisible:** blobs are 55 cm wide and appeared from nothing 2.5 m above the ground near the hero. The tentacle never moved for them.

## What it does now (`wire_spit_ue.py`, BPC_TentacleSpit only)

- **Spit** (non-cannon hits, same `SpitEvery` 3 and `SpitCooldown` 4 s): a swallow climbs the arm, the head rears and leans at the hero, thrusts, and 3 blobs (3x bigger, about 1.65 m) fly from the head and land 4.5-12 m in front of the hero, within 60 deg of the hero's facing. They then hatch as before.
- **Catapult** (cannonball hit, once per `CatCooldown` 10 s): the sting, then IK leans the arm back away from a random `Cannon` tagged actor for 2.3 s with a strain tremor, whips it over, and 3 blobs fly to within 4-25 m of that cannon. Between catapults the #529 reactions play. Skipped during a strike and during the death clip.
- Aiming is done by FABRIK in world space, so it works for every placed and mirrored tentacle.

## Steps (Master, editor idle, not in Play)

1. `git pull`. Needs #529 and #532, both applied.
2. `py handoffs/tentacle-style-530/import_spit_ue.py --dry-run`, then with no flags.
3. `py handoffs/tentacle-style-530/wire_spit_ue.py --dry-run`, then `--apply`. It does not save if it adds compile errors, and stops if a node name changed. Save all.
4. Play.

Revert: `wire_spit_ue.py --revert`.

## Tests in Play

- Hit a tentacle 3 times with a sword: it rears and spits, 3 blobs arc down in front of the hero, then hatch.
- Fire a cannon at a tentacle: it leans back away from the castle, whips over, 3 blobs land by a cannon.
- Hit it again with a cannon within 10 s: the normal reaction plays. A hit during the 2.5 s load will cut the catapult clip; check that it does not look broken.
- Kill it with a cannonball: the death clip must play, no catapult.
- Blobs must not stop on the tentacle's own hitboxes when they leave the head. This is the first thing to check if none appear.

## Tested, and not tested

Lab, headless: import OK, dry-run, apply (207 nodes), refuses a second apply, revert (5 relinks True, 207 nodes removed), re-apply. Errors before and after are the same.

**Not tested: nothing here has run in Play.** The lab copy cannot compile this component (`OnHit`, `IsBall`: missing delegate and BP_Cannonball), before or after wiring. So landing spots, the by-name IK writes, the hitbox question and a clean compile are all unconfirmed. The previews simulate IK and ballistics in Blender.

**Known limits:**
- A soldier's hit also spits around the hero, as asked, even if the hero is far away.
- More blobs means more hatched zombies: 3 instead of 2 per spit, plus the catapult. Lower the count if waves get too heavy.
- Blobs have no flight trail or landing splat yet. At long range they are small. That is the next quality step.
- Blobs can land on walls or roofs near a cannon, and may hatch there.

## Previews

`preview/Catapult_throw.mp4`, `preview/Spit_throw.mp4`, `preview/sheet_catapult.png`. Clips: `fbx/Tentacle_SPIT.fbx` (1.75 s), `fbx/Tentacle_CATAPULT.fbx` (7.0 s, release at 2.5 s). Worst turn 29.7 deg/frame, on the whip only.
