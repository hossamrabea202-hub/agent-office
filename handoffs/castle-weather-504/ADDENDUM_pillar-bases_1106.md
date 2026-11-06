# #504 addendum: pillar and wall FEET read as fake (owner, 2026-11-06, interior view)

Owner screenshot (interior hall: square stone pillars on cobbles, barrel, armour stand, purple reveal ring) with three
pillar bases circled: "speaking of weathering, very fake!". Owner's order: do THIS first, Stage 01 day-night/fog/grade
wait until it is discussed.

## Why it reads fake (audit session, read-only, from the screenshot)
1. No contact occlusion: Lumen GI has been off since 11-04, SSAO alone leaves no darkening where pillar meets floor.
   The base edge floats.
2. No base grime / edge wear: the block texture tiles unchanged down to the floor, arrises are razor sharp, every pillar
   is the same material copy (no per-instance tint).
3. Floor decals have hard edges: the damp patch bottom-left ends in a straight cut, the mud smear has a visible boundary,
   both sit on top of the cobble relief instead of in it.

## What to do (same CW504 method: ISM cards, tag CW504, one MI per layer, undo = --remove)
0. Identify the pillar/wall meshes and their MI in that hall (click one, note StaticMesh + material path). #504's note
   "Family C already has a base dirt band in its material" applies to the exterior kit; CHECK whether these interior
   pillars are that family before adding anything (no doubling, PERFECT_CASTLE #7).
1. Contact first, cheap: this is half the fix and costs no cards. Run the Stage 01 Lumen profile L1
   (s01_lumen_ab_ue.py L1: GI Medium, DFAO on, reflections stay SSR) and look at this hall (bookmark it as V02i).
   If the bases ground themselves at <= +3 ms GPU, keep L1 as the candidate and tune everything below WITH it on.
2. New layer FOOT: a height-gradient grime band on every pillar and wall foot, 0-35 cm, strongest in the inside corners
   (two faces meeting) and under the arrises; same Modulate card material as LEDGE with a vertical gradient mask and
   per-instance seed. MaxOpacity start 0.45. It is a gradient card, not a flat band.
3. Edge wear on the pillar arrises: a thin lighter chip/scuff card 0-120 cm, one Strength value per run, sparse (not every
   edge; weight the edges on the walking side).
4. Macro variation: one per-instance tint/brightness offset per pillar (custom data on the card seed, or a small MI family),
   so no two pillars read identical.
5. Floor decals: OWNER SAYS LEAVE THE WET PUDDLES ALONE. Do not touch BP_MudPad, M_MudPuddle, MPC_Weather.Wet or any
   #410 rain-wet actor. The hard-cut dark patch bottom-left is only fair game if it is a plain stain decal and not a
   puddle; if in doubt, skip it. Owner quote: "just dont mess up my castle entrance and wet puddles".
6. After step 1 and 2 are both on: re-check FOOT opacity. Contact AO + grime band together will go muddy; back one off.

## Owner limits (2026-11-06)
- "do it your way, just dont mess up my castle entrance and wet puddles": this pass is the INTERIOR hall only. No cards,
  cvar-driven look changes or decal edits at the castle entrance / gate (V02 exterior), none on the four CDLock Mason
  towers, none on any puddle or wet-system actor. Lumen L1 is global, so judge it at V02 too and report if the gate
  changes; the owner decides there.

## Gates
- Before/after at V02i, locked exposure (grey ball 118 sRGB), Lit view, Play stopped.
- stat unit: Draw/GPU change < 0.3 ms for the cards (ISM, unlit), plus the L1 cost reported separately.
- Nothing saved until the owner OKs the before/after.
