# Perfect castle: shared checklist for i9 + i5 (card #486)

Owner (Alien, 2026-11-04): "i want a perfect castle cooperte with i9", "the most realistic castle ever". The castle comes first; speed comes out of everything else.
"Perfect" is the owner's call in Play. This list is what we can check before showing him. Status is as of 09:35; i9 updates what is on his map, i5 keeps the file.

## Who does what
- **i9:** all castle geometry and materials on the Master, all renders and Play checks, final look decisions (he leads #486).
- **i5:** this audit after each rebuild; reading i9's shots against the list; pre-checked scripts when i9 asks; research into anything that reads wrong. i5's map does not have the rebuild, so i5 models nothing on the castle unless i9 asks.

## Stone
| # | Check | How to test | Status |
|---|---|---|---|
| 1 | Every visible stone surface is real carved stone, no box with a projected texture | Fresh scan: visible pieces still on M_Castle_StoneWall_World | Unknown after i9's rebuild (74 pieces done, merlons next) |
| 2 | No joint crosses a stone or an edge | Close shots at corners, gate, merlons | Open: merlons known bad |
| 3 | Stone size in range: courses 25-45 cm, blocks 40-90 cm, bigger at the base | Generator numbers per asset | Walls OK (28-46 / 45-115). Keep, Tower9, new SM_Curtain / SM_Mason: i9 to confirm |
| 4 | No stretch: all stone at uniform scale | After-save health check STRETCH | Open: Tower9 stones 20 % wide at 1.2 x 1.2 x 1.0, textures fixed by i9 |
| 5 | Colour comes from a real scan, no game-art textures | Scan: textures on stone MIs | Open: T_TilingRock (Paragon) on baked modules, gone only if those modules are gone |
| 6 | One stone family at every junction: wall to tower, wall to gate, keep | Lit + BaseColor shots at each junction | Harmony + tone pass done; recheck on the rebuild |
| 7 | Weathering has a physical cause: band at the base, rain below ledges, moss in damp, no doubled dirt | Close shots with strips hidden (bands482_ue.py) | Open: 875 strips still doubling the material band, check after rebuild |

## Light
| # | Check | How to test | Status |
|---|---|---|---|
| 8 | Stones shadow each other at game distance | realism_ab_ue.py variant B, C | Waiting on i9's run |
| 9 | Exposure, sun, sky and fog set on purpose | realism_ab_ue.py --dump | Waiting on i9. Noon sun was lowered to 4 for an overcast look |
| 10 | Judged with locked exposure | Knowledge base rule | Each A/B |

## Shape
| # | Check | How to test | Status |
|---|---|---|---|
| 11 | Merlons, crenels, walk: a soldier fits and can fight from them | Play at wall walk, sizes from i9 | i9 next (inner-side crenellations) |
| 12 | Medieval logic: nothing floats, everything carries load | Walk the castle in Play | Open |
| 13 | Roads and yard meet the walls cleanly | Close shots | Wagon ruts done; ground2 still open |

## Must keep working
| # | Check | How to test | Status |
|---|---|---|---|
| 14 | Nav, breach and gate still work after each rebuild | nav 8/8, breach test | i9: nav 8/8 after the arcade |
| 15 | No invisible walls | After-save health HIDDEN_BLOCK | 70 fixed. New: old boxes are now invisible colliders on purpose, check they match the new faces |
| 16 | Video memory not over budget | Editor warning | 92 MB over on i9's last report |
