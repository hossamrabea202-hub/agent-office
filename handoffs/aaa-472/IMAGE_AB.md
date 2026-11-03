# #472 Track V: crisp image, measure before changing (i5 for i9)

**Decision: i5 changes no image setting tonight.** The game renders at 67 % + TSR with Alien's OK (chat 947). Going higher costs GPU, and i9's lag pass showed half res saves 12 ms of a 42 ms frame, so resolution is a real GPU cost on the T1000.

**Roadmap correction:** it said the headroom for a sharper image comes from Track C. Track C frees the game thread (CPU). It only buys resolution if the frame is CPU-limited, so `stat unit` decides this: compare Game and Draw against GPU in the profiled wave (#473).

## The A/B (Play, locked camera, one spot at the gate, one on the wall walk; 10 s each; note `stat unit` GPU ms + a screenshot)
Paste each line in the console:

| Run | Console |
|---|---|
| A: today | `r.ScreenPercentage 67` |
| B | `r.ScreenPercentage 75` |
| C | `r.ScreenPercentage 85` |
| D: cheap crisp, no res change | `r.ScreenPercentage 67` then `r.Tonemapper.Sharpen 0.5` |

Editor overhead is about 25 ms of the frame (chat 947), so compare the GPU column, not fps. A shipping build's real fps (i9's queue) is the better final number.

## Decision rule
- Pick the highest run that adds **no more than 2 ms GPU** at the gate.
- If GPU already eats the frame budget, keep 67 %.
- The change goes in DefaultEngine.ini only after Alien's OK, since he approved the current value. Back up the ini first.

Put the numbers and screenshots in `handoffs/aaa-472/profile/` with #473. i5 reads them and writes the recommendation; nothing to debug on your side.

## Already right, leave alone
- `r.TSR.History.ScreenPercentage=100`: it was chosen for cost; 200 would double TSR's cost.
- `r.TSR.Velocity.Extrapolation=1`, `r.TSR.History.SampleCount=24` (PostFX pass 10-27).
- Fortnite's sharpen value is 0.5 (INDUSTRY_SECRETS section on TSR); the current 0.6 is close. Above that, halos start on stone edges.
