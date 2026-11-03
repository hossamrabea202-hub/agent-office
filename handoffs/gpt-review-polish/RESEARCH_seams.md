# #451: how real stone castles meet, and how AAA kits hide seams (i5, 2026-11-03)

Owner order (2026-11-03): go around the castle, find surfaces, hard edges and cube faces where stone walls don't meet
correctly, study real-world references for each problem, and fix like AAA technical artists. Don't touch the decals.

## Real masonry: what a junction looks like in life
| Junction | Real world | So in the game |
|---|---|---|
| Wall corner | **Quoins**: larger dressed blocks bonded alternately into both faces (often long-and-short), so a corner never reads as two slabs touching. [Quoin](https://en.wikipedia.org/wiki/Quoin), [long-and-short quoins](https://rammtimetrail.org.uk/Object/818/) | Two wall pieces meeting at 90 deg need overlap (one runs past the other) or a corner/pillar piece; never a butt joint showing a straight slit or a flat end face. |
| Wall top | **Coping / capping stones** span the full wall width to shed water. [Parts of walls](https://chestofbooks.com/architecture/Building-Construction-3-1/Parts-Of-Walls.html) | No open wall-top showing the mesh's flat cap or a gap between wall and walkway; a coping/trim piece or the walkway overlaps it. |
| Wall foot | A **plinth**, a projecting base that adds stability, often stepped out. [Trim Castle excavation](https://excavations.ie/?p=10207) | Walls go INTO the ground (sunk 10-30 cm) or stand on a plinth; never floating with a light slit, never a razor-straight line on flat ground. |
| Joints | Lime mortar joints in rubble are wide and **recessed**, not spread over the faces; rake-out depth at least twice the joint width, about 40 mm in rubble. [Lime pointing](https://buildingconservation.com/articles/pointing/lime-pointing.htm), [repointing guide](https://www.southkesteven.gov.uk/sites/default/files/2023-09/Repointing.pdf) | A seam between two pieces should read like one more mortar joint (dark, recessed, about 1-4 cm), not a hairline of light and not a perfect flat plane change. |
| Bond | Courses run continuously; a later addition shows a **straight joint** (a vertical seam with no bonding), which masons avoid except at deliberate building phases. | A long vertical seam through every course is the giveaway of modular kits: break it with overlap, offset, or a pillar/buttress. |

## AAA practice for modular kits
- **Overlap instead of touching.** Z-fighting only happens when two faces share one plane; sinking pieces slightly into
  each other is normal and invisible. [UE forum](https://forums.unrealengine.com/t/how-to-avoid-z-fighting-in-modular-assets-e-g-overlapping-wooden-frames-of-medieval-walls/97540)
- **Offset coplanar faces by a few mm to cm**, or make one piece a little thicker, so that piece wins the depth test
  everywhere (base-building games use pieces about half a unit thicker). [UE forum](https://forums.unrealengine.com/t/question-building-modular-building-assets-for-player-usage-but-how-do-i-deal-with-z-fighting/939800)
- **Trim and caps** hide seams and end faces. [Polycount trim sheets](https://polycount.com/discussions/tagged/trimsheet)
- **Grid discipline + world-aligned textures** so the stone pattern flows across pieces with no texture seam.
  [80.lv modular UE5](https://80.lv/articles/mastering-modular-procedural-techniques-for-old-west-town-in-ue5)
- Engine primitives (Cube/Plane) must never show in the final scene: replace with a real kit piece, or hide them if
  they only block light or collision.

## Fix rules for this card (derived)
1. GAP 0.3-25 cm between aligned pieces: move or scale the smaller piece so it overlaps the bigger one by 2-5 cm
   (the slit becomes a joint inside the overlap). Never move gameplay pieces (gate, stairs with nav, cannons).
2. ZFIGHT (coplanar shared face): push the smaller piece back 0.5-1 cm along the face normal, or scale its thickness
   +1 %, so one face always wins.
3. FLOAT 2-60 cm: lower the piece onto the ground and 10 cm into it (real walls sit in the ground / on a footing).
4. CUBE: replace with the matching kit piece if one exists; otherwise hide it if it adds nothing visible; never delete.
5. Every move is a script with `--dry-run`, a JSON backup of the old transforms and `--revert`. Decals and decal cards
   are excluded from the scan and never moved.
