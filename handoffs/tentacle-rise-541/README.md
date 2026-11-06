# #541 Tentacles erupt beside the road, plus sound (adjustedfilm, 2026-11-06)

Owner: two more tentacles in front of the castle, between the castle and the realm. They rise when the hero goes 20 to 50 m outside the castle, on both sides of the road, one by one, at different distances. Also sound, base collision and a second base shape; those last two are in #540.

## What happens

| | First tentacle | Second tentacle |
|---|---|---|
| Spot | North of the road, X -5200, Y 5300 | South of the road, X -9500, Y -1900 |
| Rises when the hero is | 20 m past the gate (X -2340) | 45 m past the gate (X -4840), and only after the first has finished |

1. **Warning, 1.3 s:** a rumble under the ground, a light camera shake, a puff of smoke.
2. **Burst:** the rocky base appears with a crack, a hard shake, a big smoke cloud and 24 thrown rocks.
3. **Rise, 3.4 s:** the arm shoots up fast and slows at the top, thrashing, then shudders and roars. It stands about 72 m above the ground.
4. **Then it fights:** it strikes and spits like the others. It happens once per play.

A walking hero at 6 m/s sees the bursts at about 28 m and 48 m past the gate. The first burst is ahead of him and the second comes up ahead and to the side.

## Sound (`sfx541_ue.py`)

Six sounds, synthesised in `gen_sfx.py`, because the project has no creature or wet sounds to reuse: rumble, burst, roar, groan, spit, splat. They play on the strike, spit, catapult, enraged, hurt and wounded clips, on the eruption, and on every thrown blob's landing. Full volume to 60 m, silent by 600 m.

**Nobody has listened to them, and I cannot hear them.** I only checked length and level. If they sound cheap, replace the WAVs and re-run the script, or send recordings.

## Steps (Master, editor idle, not in Play, main level open)

1. `git pull`. Run #540 first: this uses its base meshes.
2. `py handoffs/tentacle-rise-541/sfx541_ue.py --dry-run`, then with no flags.
3. `py handoffs/tentacle-rise-541/rise541_ue.py --dry-run`. Check the ground heights and that each spot is clear. Post the output on #541 if a spot lands on something.
4. `py handoffs/tentacle-rise-541/rise541_ue.py`. Save the level. It copies `Env_CorruptedTentacle_05` and everything attached to it twice, into the folder `RiseTentacles`.
5. Play and walk out of the gate.

Revert: `rise541_ue.py --revert`, then save the level. `sfx541_ue.py --revert`.

## Tests in Play

- Walk out: rumble, burst and arm at 20 m. Keep walking: the second at 45 m. They never rise together.
- Run or ride out fast: the second still waits for the first to finish.
- Before rising, neither arm is visible, strikes, nor spits. Afterwards both fight, take damage and can die.
- Hitboxes, jelly shell and sacs travel up with the arm.
- Neither base blocks the road. The second base must not reach the realm wall.
- Every sound fires, from the right place, at a sensible volume. **Sound notifies inside a post-process animation are the part I trust least.**
- Reloading a save: this is the one case with no handling yet. It will rise again.

## Tested, and not tested

Lab, GUI editor: sound install and revert, rise dry-run, install and re-install. All blueprints compile with no errors in the rock and the rise logic. Two tentacles, two bases, two collision meshes and the director are placed.

**Not tested: the rise has never run in Play.** Play would not start in my test setup, so the trigger, the move, the rocks and the sounds are unproven. The lab's tentacle also had no attached actors, so copying the real family runs for the first time on the Master's PC. The hero-view video simulates the staging in Blender with stand-in shapes.

The spots come from older level data (gate, road, realm polygon). The dry run confirms the ground only, not what else stands there.

## Previews

`preview/Rise_hero_view.mp4`: the hero's view walking out, same layout and timing. Stand-ins, not the game's look. Clip: `fbx/Tentacle_ERUPT.fbx`, 6 s, worst 7.1 deg/frame.

## Rules applied

INDUSTRY_SECRETS 0.8 and 3.4: anticipation, overlap along the arm, a long settle. Knowledge base 5: grounded, sunk, debris skirt.
