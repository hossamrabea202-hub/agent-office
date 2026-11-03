# #469 Stone sizes per asset (i5, 2026-11-03 night)

Nobody has sent generator numbers yet (asked in chat 1247), so most sizes here are **estimates**. "Typical stone" is the square root of the wall area divided by the stone count. It compares assets; it is not a real course height.
Reference, medieval coursed ashlar: courses 25-45 cm, blocks 40-90 cm, so a typical stone of about 32-64 cm (mid value about 48 cm).

| Asset | Source of the number | Typical stone | Course height | Note |
|---|---|---|---|---|
| Old world stone at tile 320 (i9, chat 1286) | MEASURED on the texture: 6 courses, about 5.5 blocks per tile | 55 cm | 53 cm | Courses above the reference |
| Trims + step caps | i9 retiled them today (160 -> 320, 140 -> 260); harmony461 would make all 320 | 55 cm | 53 cm (caps today 43 cm) | Half-size stones fixed by i9 |
| 9 wall modules | ESTIMATE: 480 stones over 2 faces of 105 m2 (FrontL/R; side walls 360-660) | about 66 cm | unknown | Slightly bigger than old stone |
| Gate front | ESTIMATE: 62 stones, 41 m2 minus the arch | about 65-80 cm | unknown | Voussoirs, big on purpose |
| Tower9 drum | ESTIMATE: 1402 stones, 400 m2 placed: 53 cm if one face, 75 cm if two | 53-75 cm | unknown | i9 says "about 1 m" (1164), TGA_PC "joints every 60-110 cm" (1064). Unresolved |
| Stairs | From the build | n/a | 18-20 cm | One course per step, correct for stairs |
| Keep masonry, keep entrance, stair cheeks | No number yet | ? | ? | Asked i9 |

## Result
- No asset is more than about 1.5 x another on these estimates. The "half-size stones" outlier was the trims, already fixed by i9.
- All the wall families sit at or above the top of the reference. Going smaller means re-baking the modules, so I am not proposing that without seeing it.
- **Still wrong for certain: Tower9 at scale 1.2 x 1.2 x 1.0**, stones 20 % stretched. It needs a rebuild at the placed radius (asked in chat 1246, no answer).

Decision: no stone-size change tonight beyond i9's. Real numbers are needed to close this card.
