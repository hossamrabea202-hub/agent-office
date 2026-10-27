# Obsidian Sovereign: quality review (checkking, QA + VFX)

Reviewed 2026-10-27: renders of all 11 parts, and the actual textures pulled out of the Chest Round 1 preview GLB (2K: BaseColor, Normal, ORM).

**Verdict: blockout / greybox quality, not close to AAA.** The topology numbers are clean (manifold, no overlaps), and Codex's own README says the same thing: "simplified procedural WIP". Polish alone won't get it to AAA. Most parts need a remodel.

## Geometry

| Part | Problem |
|---|---|
| All | Each piece is **one smooth shell**. Real armour is **layered plates**: separate overlapping lames, plate thickness you can see at every edge, rolled or turned edges, rivets, leather straps and buckles. None of that is modelled. |
| Helmet | Bucket/egg silhouette; visor slits are painted lines, not cut openings with depth; no breaths, hinge, comb or brow ridge. |
| Chest | Best of the set (good breastplate curve), but no fauld, no gorget join, armholes too big and soft, no straps or buckles at the sides or back. |
| Shoulders | The lames are **grooves in one surface**, not overlapping plates. They can't articulate. |
| Gauntlets | A glove-shaped tube with **straight fused fingers**. No knuckle plates, finger lames, cuff flare or leather palm. Weakest part. |
| Waist | A flat lampshade skirt with slots; tassets should be separate hanging plates on straps. |
| Boots | Rounded vases: **no sole, no heel, no sabaton lames**, no ankle articulation. |
| Cape | A **plain grey wavy sheet with no texture**. No cloth thickness, hem, weave, wear or attachment to the shoulders. |

## Textures

- **BaseColor:** one flat navy-black value everywhere, plus thin gold line art. No colour variation, no wear, no edge highlights, no grime, no scratches. The engraving reads as **drawn on**, not cut into metal.
- **Normal:** almost flat. Only the rim bevels and very faint engraving. No hammer marks, no plate surface, no micro detail.
- **ORM:** metallic 1 across the board; roughness is a smooth gradient with no breakup. Every surface looks like the same clean plastic-metal.
- **UVs:** Smart UV Project. Fragmented islands with **staircase/jagged edges** (low-quality padding), many tiny islands along seams, and roughly 55-60% of the texture actually used. Expect visible seams and wasted texel density at 4K.

## What AAA+ needs here

1. **Remodel with real plate construction:** separate lames, edge thickness, rolled edges, rivets, straps, buckles and articulation points (elbow/knee couters, finger lames, sabatons).
2. **A sculpted high poly:** hammer dents, real recessed engraving, battle damage, then a proper bake.
3. **Hand-laid UVs:** straight seams in hidden places, about 85% packing, consistent texel density, mirrored halves where it's safe.
4. **A layered material:** blackened steel with blue-purple temper colour, edge wear from curvature, grime in cavities, gold inlay set into the metal (its own roughness), micro scratches, fingerprints. Leather and cloth with real weave.
5. **Fit and skin to ShadowknightUE_SK** (still blocked on issue #1), plus LODs and a cloth sim for the cape.
