# Creature studio method: how film creature teams get "real", and what we can copy in UE (TGA PC, 2026-11-06, #338)

The owner's bar is "Stranger Things series quality, not a game asset". These notes cover how ILM, Weta FX, Framestore,
DNEG, Aaron Sims Creative (ASC) and the Stranger Things creature team (the Duffer brothers with practical shops and
VFX vendors) work. Each studio item is followed by **For us:** what it means for a UE 5 game creature made by agents
with Blender.

Sources are public making-of talks, VFX breakdowns and interviews, written down from memory with no fresh web check. Items marked
[UNVERIFIED] are specific claims to confirm before quoting.

## 1. Design: reference, silhouette, anatomy that could exist

- **Reference boards first, real animals before monsters.**
  - ASC and Weta start a creature from biology boards: anatomy plates, macro photos, how the animal moves, and a "what
    would happen to it" board (injury, disease, parasite).
  - The Stranger Things Demogorgon started from real anatomy too: a humanoid frame with a flower-like head. Its
    believability comes from the parts that behave like real tissue (wet petal edges, muscles, teeth).
  - ASC did the design and digital work. A practical suit was built and performed, and CG extended the head petals
    [UNVERIFIED split of vendors].
  - **For us:** pin real references per creature in the card before modelling. For the wasp:
    - *Vespa mandarinia* and *Vespa crabro* macro shots (head, mandibles, thorax pile, gaster bands)
    - *Ophiocordyceps* parasitised insects (fungal stalks out of the joints)
    - dried and rotting insects (collapsed eyes, broken membranes, dust)
- **Silhouette first.**
  - Every studio judges the design as a black fill at thumbnail size before any detail. If the black shape doesn't say
    "hornet" (wasp waist, long gaster with a sting, raptorial legs, big mandibles), no texture will save it.
  - **For us:** render a silhouette pass (flat black on white) from the side, the front and below, the player's usual
    view, and check it before texturing.
- **Big / medium / small forms, with rest areas.**
  - Primary forms are the head, thorax and gaster masses. Secondary forms are the plates, segments and joints. Tertiary
    forms are the pits, hairs, scratches and veins.
  - Leave rest areas, where detail is calm, so the eye knows where to look: roughly 60 % calm, 30 % medium, 10 % busy.
  - Uniform noise everywhere reads as CG.
  - **For us:** put the busy detail where the story is (the rot at the joints, the face) and keep the large tergite
    plates calm.
- **Anatomy that could exist.**
  - ILM's rule for the Jurassic Park dinosaurs was to grow them from living relatives (birds, big cats) and keep the
    mechanics honest. Joints bend only where a real joint is, and mass sits over the supports.
  - **For us:** model the insect segments in their true order (head, pronotum, mesoscutum, scutellum, propodeum,
    petiole, 6 gaster segments; legs = coxa, trochanter, femur, tibia, 5 tarsal segments, claws). Bend the mesh only
    at those joints.
- **Scale changes physics.**
  - A wasp scaled to 1.9 m cannot beat its wings 100-200 times a second like a real one. Film creatures get slower,
    heavier motion when they are big.
  - **For us:** a heavy 10-15 Hz wingbeat reads as huge. Sell the speed with motion blur (a blur card), not with
    frequency.
- **Asymmetry and history.**
  - Practical creatures look real because nothing is mirrored perfectly. One mandible is chipped, one wing is torn, a
    leg is missing a tarsus.
  - **For us:** damage one side more than the other, and give each damage a cause.

## 2. Surface: layers from the inside out

- **Weta builds bodies inside out:** skeleton, then muscle, then fat, then skin, and simulates the tissue. Skin slides
  over muscle and wrinkles where it compresses.
  - **For us:** no tissue sim. Fake it with real geometry layers:
    - inner flesh under the broken chitin
    - wet tissue in the joints
    - hairs as real strands
    - plus secondary motion bones
- **Look development is shared across all these studios** (Framestore, DNEG, ILM):
  - Every asset is judged on a turntable under a neutral HDRI with a grey ball, a chrome ball and a colour chart, at a
    locked exposure.
  - Shot lighting comes later. An asset that only looks good in one shot isn't finished.
  - **For us:** same rule (INDUSTRY_SECRETS 0.1): grey ball metered to 118 sRGB, the exposure locked, before and after
    at the same exposure.
- **Layer the materials like a practical paint job:**
  1. base colour
  2. colour variation at three scales
  3. thin-part translucency
  4. dirt by cause
  5. wet only where fluid is
  6. dust on top

  Practical creature painters (the Stranger Things suit painters, Weta Workshop) work the same way: translucent layers
  over a sculpt, so the colour has depth.
  - **For us:** paint in this layer order and keep each layer's cause written in the script.
- **Insect-specific tells (what separates a hornet from a plastic toy):**
  - Chitin is a thin, slightly translucent shell. It glows amber where it is thin and backlit: leg edges, antenna
    tips, wing veins, the rims of the gaster segments.
    - **For us:** Subsurface/Two-Sided Foliage on the thin parts, or a transmission mask.
  - The pile of fine hairs (setae) on the head and thorax breaks the specular highlight. A smooth thorax is the number-one
    "CG insect" tell.
    - **For us:** real strand geometry, a few thousand short tapered cards, plus a fuzz roughness boost.
  - Compound eyes are not mirror-glossy everywhere: each facet has its own highlight. Dead eyes go milky, collapse and
    dry.
  - Wings are thin film with veins, wrinkles and corrugation. Seen through, they show a faint rainbow (thin-film
    interference). In motion they are a blurred fan.
  - Wet versus dry contrast: on a rotting insect, the chitin stays dry and dusty and only the tissue is wet. Wet
    everywhere reads as rubber.
- **Rot by biology (the zombie story):**
  - What breaks down first is the soft parts: intersegmental membranes, wing membranes and eyes. Chitin plates survive
    and gape apart at the joints, so the rot reads at the joints, not as spots on the plates.
  - Parasitic fungi (*Ophiocordyceps*) grow out through the soft joints as pale stalks with darker fruiting tips. This
    is a real, readable silhouette cue, and it matches the Stranger Things Upside Down look of organic growth and
    floating spores.

## 3. Motion: weight, overlap, character

- **Drivers and followers (ILM, Weta animation leads):** the driving motion (here the wingbeat) moves the core, and
  everything hanging off it follows a few frames late and settles: overlap and follow-through.
  - For a flying insect:
    - each downstroke lifts the body a little
    - the gaster lags the thorax pitch and overshoots
    - the legs trail and swing with drag
    - the antennae flick late
  - **For us:** simulate the followers as damped springs on the driver curves, over several loops. Take the last loop,
    so the cycle is seamless and still has overlap.
- **Arcs and no perfect loops.** Real flight has small drift, roll and yaw noise, and an animal corrects all the time.
  - **For us:** layer low-amplitude noise of 2-3 frequencies that resolve within the loop length.
- **Staccato (the Stranger Things trick):**
  - Its creatures alternate stillness with sudden fast moves. Insects do this naturally: a hover hold, then a snap turn.
  - The contrast is what feels wrong and scary.
  - **For us:** add twitch holds in the hover (antennae and head snap, then hold) and a short cocked anticipation before
    the dive.
- **Anticipation and recovery on attacks.** The gaster cocks forward before the sting (anticipation), strikes fast in
  2-3 frames, holds on the hit, then recovers slowly.
- **Motion blur is part of the creature.** In film the wings are a blur disc 90 % of the time.
  - **For us:** a dedicated blur card. It's a fan the size of the stroke arc with a faint vein smear and soft alpha, so
    the wings read in Play at any frame rate. The real membranes stay too, dithered, for the stroke extremes and slow
    motion.

## 4. Readability in the game (where film and games differ)

- **Value contrast against the backdrop.** Film controls every frame; we don't.
  - A dark brown wasp against a dark realm sky vanishes, which is one of the reasons the owner "never saw them fly".
  - **For us:**
    - keep the warning colours (amber bands) bright enough to read at 30 m
    - give the wings a lit edge
    - add a restrained emissive on the fungal tips (spores) as the creature's signature
- **Readable at three distances (DNEG/ILM digi-double practice).** Check close-up (1 m), mid (8 m) and gameplay
  distance (25-40 m). Detail that only reads at 1 m is free but must not turn into noise at 40 m.

## 5. Checklist we apply (the wasp v2 card #338 follows it)

1. Reference board in the card (real species, parasite, decay).
2. Silhouette pass: side, front and below.
3. True segment order, joints only at real joints.
4. Primary / secondary / tertiary forms with rest areas, asymmetry with causes.
5. Inside-out layers: flesh under the broken chitin, hairs as strands, thin-part translucency.
6. Material layers in order, wet only on tissue, pbr_check clean.
7. Locked-exposure lookdev at three distances, before and after.
8. Motion: driver plus damped followers, seamless loops with noise, staccato holds, anticipation on attacks.
9. Wing blur cards, so flight reads in Play.
10. Game readability: value contrast and signature emissive, checked at gameplay distance.
