# #561 crossbows: how real ones look, and how AAA studios make them read real (checkking, 2026-11-07)

Short study before building, per the `M:` rule. Values come from our knowledge base (`handoffs/knowledge`); history is
general reference knowledge, marked [UNVERIFIED] where I had no source open.

## What a real 15th-century crossbow is made of
| Part | Real material | What it looks like in life | So in the game |
|---|---|---|---|
| Stock (tiller) | walnut, pear, yew or maple, oiled or waxed ([Crossbow](https://en.wikipedia.org/wiki/Crossbow), [Arbalest](https://en.wikipedia.org/wiki/Arbalest)) | warm mid-brown, never near-black; grain visible; the oil finish rubs through to lighter wood on edges and where hands hold it | stock albedo ~55-75 sRGB, saturation ~60 %, roughness 0.45-0.65 with grain, lighter + smoother on edges |
| Inlay | bone or staghorn veneer, engraved, lines filled dark (German hunting crossbows, e.g. the Met's crossbow of Count Ulrich V of Württemberg, 1460) [UNVERIFIED: no page open] | ivory-cream, warm, a soft satin sheen, dirt in the engraving | bone 0.79/0.79/0.66 linear (KB §1.1), aged warmer; roughness ~0.5, grime in cavities |
| Prod (bow) | composite horn/sinew, later steel | steel prods: forged, dark scale on the flats, bright where polished/wiped | **bare steel ≥ 180 sRGB with metallic 1**; the dark look is an oxide/mill-scale film (non-metal) in patches and cavities, rubbed off at edges |
| Stirrup, nut pin, trigger, bands | wrought iron | same as the prod, more rust in corners | same steel logic |
| Fittings, rivets, trim | brass or gilt copper | warm yellow metal, dark brown tarnish in recesses, bright where rubbed | brass ≈ 0.72/0.54/0.27 linear (KB lists 0.91/0.78/0.42 for clean brass; aged is darker), metallic 1; tarnish = non-metal brown in cavities |
| String | twisted hemp/linen, waxed | dull, rough | roughness 0.8+, albedo ≥ 30 sRGB |
| Bolt (quarrel) | ash shaft, forged square bodkin head, 2-3 vanes of wood, leather or parchment ([Quarrel](https://en.wikipedia.org/wiki/Quarrel)) | short and thick next to an arrow | pass 2 (needs the bolt FBX) |

## How AAA teams make weapons read real (what I used)
1. **Calibrated values first** (KB rule 1, INDUSTRY_SECRETS rule 1): our source failed `pbr_check` on all three gates
   (67 % of wood below 30 sRGB, all metal below 150 sRGB, 54 % in-between metallic: the asset used a flat 0.88 / 0.82).
   Fixed: wood 63 sRGB median, steel 192, metallic strictly 0/1.
2. **Dark metal = a non-metal film over bright metal**, not dark metal (KB playbook, retex.py step 3; Unity's
   best-practice guide: in-between metallic only for dirt over metal). This keeps the designer's dark look and makes the
   edges catch light like a real forged piece.
3. **Wear in physical order** (KB rule 3, INDUSTRY_SECRETS rule 3): base → grain → edges → cavities, no global grunge.
   Edges = UV-island borders (on a hard-surface kit each island ends at a hard edge), broken up with noise, 4 texels wide
   at 2K (~2-3 mm, KB rule 4). Cavities = the asset's own baked AO.
4. **Roughness carries the realism** (INDUSTRY_SECRETS rule 2): never flat. Steel 0.2-0.5 with scratches, oxide 0.7+,
   brass 0.25-0.45, wood 0.35-0.85 following its grain (pores rougher).
5. **Composite Texture** (INDUSTRY_SECRETS §1.3.1): the new ORM gets the crossbow normal map as composite (roughness
   from normal variance) so the weapon does not sparkle at a distance. **Sharpen4 mips** on the BaseColor (§1.3.6),
   **Masks compression** on the ORM (§1.3.8).
6. **New material, never the live one** (owner decal rule, `M:` rule): the old material is duplicated, the copy points at
   the new textures, the swap is a script with dry run, backup and revert.

## Pass 2 (waiting on export request #562)
Run `tools/laptop2/retex.py` on the real mesh: ray-bevel edges instead of island borders, real up-facing dust, hand polish
on the grip (the stock where the hands sit), wood grain direction along the stock, micro normal detail; then lookdev on
the real crossbow (locked exposure, grey + chrome ball) and the same for Golden Sovereign and the bolt.
