# #386 Jelly blob enemies: wet organic slime, not cartoon red bubbles

By `adjustedfilm (Claude)`, 2026-10-31 late. Owner: "nothing changed still red bubbles" (he calls them cartoonish).
Research: `handoffs/blob-realism-293/RESEARCH.md` (Stranger Things' Mind Flayer goop, The Thing). Dark, desaturated flesh;
wet and dry patches; subsurface light, not glow; never candy colours.

## What changes

`M_JellyBlob_Real` is a **copy** of `M_JellyBlob`. Its motion is untouched: flight jiggle, splat, column and hatch, all
the parameters (LandT HatchT ZShield TScale BornT Green), and every wire, **including World Position Offset**. So
**nothing needs hand-wiring.** Only the look code changes:
- **Colour:** dark bile-olive to maroon. It keeps a faint hint of the tentacle's shield colour.
- **Inside:** bruise-dark masses (parasite shadows) and thin darker veins, all low saturation.
- **Membrane:** nearly opaque at the thick centre, thinner at the rim. A dim warm light comes through the rim
  instead of a glow.
- **Wetness:** wet, glossy patches against tacky, drier patches (roughness 0.07–0.42), not even toy gloss.
- **The #382 lesson:** the facing uses `abs(N·V)`, so back faces don't light up.

`MI_JellyBlob_Real` is a copy of `MI_JellyBlob` (same values). Specular goes to 0.5. The live `M_JellyBlob` is never edited.

## Steps (Master: paste only, about 5 minutes)

1. `py "<repo>/handoffs/jellyblob-real-386/setup_realblob386_ue.py" --info`. This is read-only. Push
   `realblob386_info.txt`. It shows how the look node's inputs map. If a line says "input not found: default", it still
   works; tell me anyway.
2. `py ".../setup_realblob386_ue.py" --dry-run`, then run it without `--dry-run`. This builds the two new assets.
   If compiling `M_JellyBlob_Real` shows an HLSL error, post the error line on #386 and I fix it at once.
3. `py ".../setup_realblob386_ue.py" --preview`. Two spheres appear 4 m in front of the editor camera:
   `Lookdev386_Old` (left) and `Lookdev386_New` (right). Screenshot them in daylight and post with
   `tools/shot.js --card 386`. Then run `--preview-remove`.
4. **After the owner's OK:** `--swap --dry-run`, then `--swap`. `MI_JellyBlob` gets the new parent, so every blob in
   the game changes. Undo with `--revert`.

Not compiled yet, because that needs the editor.

## Checks (Play, after the swap)

1. A blob in flight is a dark, wet, fleshy lump with darker shapes inside. It is not red and not see-through.
2. It splats, rises into a column and hatches exactly as before.
3. In sunlight, highlights break up: wet spots against duller spots.
4. At the edge there is a faint warm see-through rim. No glow at night.
5. The health bars are unchanged.

Not in this card: the slime trail (`M_JellyTrail_v3`) is untouched. A slow peristaltic wave would change the vertex
part, which the hatch timing depends on; ask if you want it as a separate step.

Rules applied:
- realism KB: albedo 0.03–0.15 for dark organics, no emissive biology;
- INDUSTRY_SECRETS rule 1: lookdev at locked exposure, via the preview spheres;
- M:-style: new assets only, before/after, swap on OK with a revert.
