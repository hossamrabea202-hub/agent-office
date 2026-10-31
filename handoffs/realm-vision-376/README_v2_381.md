# #381 Realm vision v2: swallowed by the bubble, a pink-orange dream inside, and a living jelly bubble

By `adjustedfilm (Claude)`, 2026-10-31 late. It builds on #379, which is pasted and works (you can get inside).
The owner's notes:
- "the feeling of being absorbed in or consumed in rather than just 1 frame world next frame realm";
- "bubble was static";
- "more distortion dreamlike state, pinkish orange semi scary fantasy comfortable yet unsettling dream, you made it only
  dark green";
- "your realm is very very dark".

**Decision:** the owner's colours win over the card. There is no dark-green vignette. The crossing vignette is a warm
maroon-rose, and the whole look is **brighter** than v1: exposure +0.25 instead of −0.35, with lifted warm shadows.

## What changes

1. **Absorption, not a cut.**
   - The look follows the distance to the real membrane, along 6 directions. Outside, from 10 m to 0 m, it rises from
     0 to 0.35: a "pull". Inside, from 0 to 8 m, it rises from 0.35 to 1. It is smooth both ways and per frame.
   - **Entering** plays a 1.5 s one-shot: a jelly lens from the edges inward, a colour-fringe spike, a wet blur, and the
     membrane closing in and opening again.
   - **Leaving** plays a 0.8 s "peel": the lens pushes outward and the world peels back in.
2. **The dream inside** is a new post-process material, `M_RealmDream`, tuned on `MI_RealmDream`:
   - a slow sinuous warp and a slow swirl at the edges;
   - the view breathes with the bubble;
   - a drifting ghost double image;
   - a soft pink-orange glow (halation) and colour split;
   - warm lifted shadows, so it is not dark;
   - rose-orange screen edges with a slow heartbeat pulse, for the "unsettling" part.
   The colour grade on `Vision` is now warm and bright.
3. **A living jelly bubble.** This is a **copy** of the bubble's current material, `*_Jelly`, with World Position Offset:
   - slow breathing about its own centre (0.2 Hz);
   - ripples travelling over the surface;
   - a soft sway.
   It stays in place. Any MI values the owner tuned are copied over. The bubble's mesh, placement and current material are
   **not** touched. The swap needs the owner's OK and is reversible.
4. **One clock.** `MPC_RealmDream.BreathHz` drives the jelly, the view's breathing and the weight pulse, so they move
   together. The rate is tunable as `BreathHz` on Realm_Vision.

Mock: `preview_dream381.png`. It is numpy, not the engine, on a lookdev shot. Left to right: v1 dark green (rejected),
v2 inside, v2 at the crossing.

## Steps (Master: paste only, about 10 minutes)

1. `py "<repo>/handoffs/realm-vision-376/setup_realmvision381_ue.py" --check`. This is read-only. Push
   `realmvision381_check.txt`.
   - It lists every realm post-process volume, with its exposure, gain and vignette.
   - If an old one (for example `PPV_Realm`) has negative exposure or a heavy vignette, it is part of the "very dark".
     Run `--mute-old-ppv` after step 5. It is reversible with `--unmute-old-ppv`.
2. `py ".../setup_realmvision381_ue.py" --dry-run`, then run it without `--dry-run`. It makes:
   - `MPC_RealmDream`;
   - `M_RealmDream` + `MI_RealmDream`;
   - the bubble's `*_Jelly` copy;
   - the bright look + the dream blendable on BP_RealmVision **and** on the placed Realm_Vision.
3. BP_RealmVision → My Blueprint: paste the **8 new** lines of `VARIABLES_v2_BPVar.txt`, one at a time. The 8 v1
   variables stay. Compile.
4. EventGraph: press Ctrl+A, then Delete. Paste `BP_RealmVision_v2_graph.txt` (477 nodes). Compile, then Save.
5. Play, using the checks below.
6. **Jelly bubble, after the owner's OK:** `--swap-bubble --dry-run`, then `--swap-bubble`. Undo with `--revert-bubble`.

Pre-checked: `fix_impure.py` finds nothing to fix, and `applyall check` passes (**Validation: OK**, 477 nodes,
822 links). Not compiled yet, because that needs the editor.

## Checks (Play)

1. Walk towards the bubble from 10 m out. The world slowly warms and starts to drift. Nothing switches suddenly.
2. Step through the wall. You feel swallowed for about 1.5 s: the edges bend inward, the colours split, things blur,
   and the rose edge closes in and opens. Then you are in the dream: warm, bright, slowly flowing, with a faint ghost
   image, and the edges pulse like a slow heartbeat.
3. Walk deeper in. The dream gets stronger. Walk to the wall. It weakens towards the pull level.
4. Walk out. A 0.8 s peel, then the normal world.
5. Inside, the image must be **brighter** than v1, never dark.
6. After `--swap-bubble`: the bubble breathes, ripples and sways in place, in time with the inner breathing.
7. Two minutes of Play: no "Accessed None".
8. Screenshots with `tools/shot.js --card 381`.

## Tuning (owner, in Details; live in PIE)

| Where | Values |
|---|---|
| `MI_RealmDream` | Warp, Ghost, Glow, Lift, Haze, Lens (crossing strength), Chroma, Heart, HeartHz |
| `Realm_Vision → Realm Vision` | PullDist 1000, DeepDist 800, PullMax 0.35, EnterTime 1.5, ExitTime 0.8, FadeSpeed, BreathHz 0.2, BreathAmt |
| `Realm_Vision → Vision → Post Process Settings` | the colour grade |
| `*_Jelly` material instance | JellyBreath 0.015, JellyRipple 60 cm, JellyRippleLen 1500, JellyRippleSpeed 300, JellyWobble 0.01 |
