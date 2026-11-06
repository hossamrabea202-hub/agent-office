# #449 Flesh Brute ("big mouth"): how film and TV make a big creature move

By `adjustedfilm (Claude)`, 2026-11-06. Owner: *"re animate the big mouth.. his animation looks silly. check how Marvel and
Netflix and Scifi animate then apply"*, then *"i want stranger things netflix series quality"*.

## What the studios do

**Stranger Things (Netflix):**
- The Demogorgon fight in season 4 is pure keyframe animation, with no motion capture. The creators and VFX supervisors
  gave notes on how it moves at the first animation pass
  ([80.lv](https://80.lv/articles/stranger-things-demogorgon-fight-breakdown-released)).
- Rodeo FX changed the creature's proportions so its runs and jumps made physical sense
  ([Screen Rant, Julien Hery](https://screenrant.com/stranger-things-vfx-julien-hery-interview/)).
- Season 5 is Wētā FX, again with animation built by hand
  ([Art of VFX](https://www.artofvfx.com/stranger-things-season-5-weta-fx-brings-the-demogorgon-back-to-the-upside-down/)).
- The original creature was a suit performer (Mark Steger) with an animatronic head. The motion was a performance,
  not a cycle ([Vice](https://www.vice.com/read/the-man-who-played-the-monster-in-stranger-things)).

**Pacific Rim: Uprising, animation director Aaron Gilman**
([vfxblog](https://vfxblog.com/2018/04/09/inside-the-mind-of-pacific-rim-uprisings-animation-director/)):
- **Retime, don't stretch.** Slowing motion down does not make it heavy. Retime parts of the action so the poses have
  contrast: hold the compression, then move fast.
- **Uneven spacing.** Poses at even intervals look monotone and dull.
- **Catch the weight.** On every impact the joints take the load and recover, and the shock travels up the limb into
  the shoulders.
- **"Heft" layer.** An offset overlap in the hips and shoulders, so the body compresses and settles on every step. They
  built it as a library of curves layered over the mocap.
- **High-frequency secondary.** Small parts shake on impact, so the body never reads as one solid block.

**Pacific Rim (2013), ILM, Hal Hickel**
([fxguide](https://www.fxguide.com/fxfeatured/monster-mayhem-pacific-rim/)): going very slow is the usual way to sell
scale, but it made the fights read as underwater. Speed is kept, and weight comes from the accents.

**Marvel: Hulk, Smart Hulk**
([VFX Voice, Framestore](https://vfxvoice.com/how-framestore-fleshed-out-smart-hulk-for-avengers-endgame/);
[Creative Bloq, ILM](https://www.creativebloq.com/3d/how-ilm-created-hulk-81516311)):
- The base is a captured performance, then animators push it onto the bigger body.
- Steps are made much larger and heavier than the actor's own.
- Flesh and inertia simulation runs over the animation.
- A richer jaw and mouth rig: the face carries the performance.

**Secondary motion and jiggle** ([SideFX KineFX](https://www.sidefx.com/docs/houdini/character/kinefx/secondarymotion.html),
[Maxon Jiggle](https://help.maxon.net/c4d/2027/en-us/Content/html/OCAJIGGLE.html.md)): bigger masses jiggle slower. The
reaction starts a beat late, scales with how violent the action is, and is damped so it settles.

## What that means for our brute (the diagnosis)

Measured on all 37 clips (`ckw/fbtools/dump`, read straight from the uassets):

1. **The maw is dead.** `jaw`, `tongue_01-03` and every flesh bone (belly, sides, breasts, butt) move **0.0°** in every
   clip. The retarget only drove the body chains. The mouth sits in the artist's showcase gape all the time, like a
   mannequin.
2. **It jogs.** The blend space has Idle @0, FB_A_Walk @20 and **FB_A_Run @100**, and the brute walks at 71.5. So it
   mostly plays a 0.8 s human jog cycle. A 2.3 m mass on a jog loop is the "silly" look.
3. **No weight.** In the human clips the pelvis swings, but nothing answers it: no flesh, no head lag, and no shock on
   the footfalls.
4. **Even timing.** The attacks are human swipes with even spacing, so there is no anticipation and no snap.

## What the #449 layer applies

| Studio rule | In the layer |
|---|---|
| The face carries the performance (Hulk, the Demogorgon's head) | Jaw performance per clip type: a breathing maw, an anticipation gape that snaps shut on the strike, a slack drop on hits, slack and open on death, a roar on burst, and an 8–12 Hz living tremble during the gape |
| Overlap and follow-through | The tongue lags the head and curls with the jaw. The head and neck lag the chest |
| Heft / catch the weight (Gilman) | The shock from each footfall travels spine_02 → spine_03 → neck → head and the jaw drops a little, growing up the chain |
| Bigger mass = slower jiggle, damped | Spring-dampers on 9 flesh bones (belly 3.0 Hz, ζ 0.35), driven only by acceleration, with a soft limit. Seamless on loops |
| Retime, don't stretch | Attacks: the wind-up lingers, then whips into the strike; fast follow-through, then a long heavy settle. The **strike frame and clip length are kept**, so the BP damage timing doesn't move |
| Speed is kept; weight comes from the accents (Hickel) | Locomotion: the run sample moves to 79 at rate 0.8 (the ±20 % rule, INDUSTRY_SECRETS §3.4 #2). The brute lumbers with longer, slower strides instead of jogging, and its game speed is unchanged |

## The honest ceiling

Stranger Things quality means hand-keyed, creature-specific animation. The layer fixes the three biggest tells (the
dead mouth, the floaty mass and the jog) on top of retargeted **human zombie** clips. The last step to series quality
is new source motion made for this body:
- a creature-performer mocap session (the Mark Steger approach), or
- a hand-keyed set in Blender: idle, threat roar, lumber walk, charge, 2 attacks, 3 hits and 2 deaths.

This layer then runs on top of that set unchanged.
