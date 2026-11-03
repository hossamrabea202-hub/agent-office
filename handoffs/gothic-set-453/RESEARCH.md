# #453 Gothic plate harness (c. 1480): research and piece spec (i5 / adjustedfilm, 2026-11-03)

Owner (Alien): a new set "made just like the obsidian set ... something else but still real from medieval ages". Choice:
**German Gothic plate, about 1480**. In game: **the Landshut Gothic set** (named after the most famous surviving
example, below). Same structure as Obsidian (#424): 11 parts on the same bones, sold as 4 bundles at Vesna.

## Real references
- **Wallace Collection A21**, London: South German Gothic armour for man and horse, Landshut, c. 1480; one of only three
  complete medieval equestrian armours; field armour; hardened steel (~0.6 % carbon) on the lower arms and legs; maker's
  mark "R", attributed to Ulrich Rambs. [Wallace Collection press release](https://www.wallacecollection.org/documents/398/The_Wallace_Collection__Equestrian_Armour_Redisplay_Press_Release.pdf),
  [myArmoury visit](https://myarmoury.com/feature_visit_wallace.php), [Bridgeman, Landshut c. 1485 component](https://www.bridgemanimages.com/en-US/german-school/component-of-equestrian-armour-german-partially-landshut-c-1485-iron-steel-leather-felt-canvas-wood/iron-steel-leather-felt-canvas-wood-and-copper-alloy/asset/8611884)
- **KHM Vienna, Hofjagd- und Rüstkammer**: the "Sigmund of Tyrol" field armour, Lorenz Helmschmid, Augsburg, c. 1484
  (the museum notes there is no document of Sigismund ordering it). [KHM object 514252](https://www.khm.at/en/objectdb/detail/514252),
  [Lorenz Helmschmied](https://en.wikipedia.org/wiki/Lorenz_Helmschmied)
- **Met Museum**: Field armour of Maximilian I, 1479-80 (Helmschmid; sallet in a private collection, the rest in Vienna).
  [Met, The Last Knight](https://metmuseum.org/exhibitions/listings/2019/last-knight-art-armor-ambition-maximilian/video)
- Style overview: [Gothic plate armour](https://en.wikipedia.org/wiki/Gothic_plate_armour); auction catalogues of South
  German Gothic field armours ([Hermann Historica](https://www.hermann-historica.de/upload/77/77-AW/files/assets/basic-html/page-710.html),
  [Drouot lot 31](https://gazette-drouot.com/en/lots/13164394-a-south-german-gothic-full---)).

## What makes it read "Gothic, 1480" (and not Obsidian)
1. **Bright polished steel** (armour "in the white"), no black finish: F0 ~0.56-0.6, roughness 0.18-0.30 on flats, higher
   in the flutes where polishing can't reach; faint grey patina and fine directional polishing streaks; rust only in
   rivet heads and plate overlaps.
2. **Fluting and ridges**: fans of radiating flutes on breastplate, fauld lames, couters, poleyns and gauntlet cuffs;
   they stiffen the plate without weight. Flutes are geometry (or a strong normal), never a texture stripe.
3. **Cusped / scalloped edges** and pierced tracery-like borders on the edges of plates (cuff of the gauntlet, top of the
   breastplate, tassets), with turned (rolled) edges on the openings.
4. **Sallet with a long pointed tail + bevor** (chin/throat defence, can be articulated); visor slit in the sallet.
5. **Pointed sabatons** (long toes in the late 15th c.), articulated lames.
6. **Fan-shaped couters and poleyns** (elbow and knee wings), large and fluted.
7. **Small asymmetric pauldrons** (smaller than Milanese ones), fluted.
8. Straps: **red-brown leather** with iron buckles; **latten** (brass) only as a thin hint on a few rivets / borders.
9. Under it: an **arming doublet** (linen / fustian, mail voiders at the armpits) instead of Obsidian's cape.

## Piece spec (same ids, bones and knight slots as obsidian-set-v2/pieces.csv)
| Id | Piece | Bone | Gothic form | Key detail | Def (Obsidian) |
|---|---|---|---|---|---|
| 10 | Cuirass | spine | two-part breastplate (lower plackart) + backplate | radiating flutes from the waist, cusped top edge, lance rest stub on the right | 38 (45) |
| 11 | Pauldrons L/R | upperarm | small, fluted, asymmetric (left larger) | 3 lames, cusped edge | 10 (12) |
| 12 | Gauntlets L/R | hand | mitten gauntlets with a long flared pointed cuff | fluted cuff, cusped edge, knuckle ridge | 7 (8) |
| 13 | Sabatons L/R | foot | pointed toes, 6-8 lames | turned edges | 7 (8) |
| 14 | Greaves L/R | calf | closed greaves, ridged | slight flare at the ankle | 8 (10) |
| 15 | Helmet | head | sallet with long tail + visor slit, separate bevor | fluted skull, rolled edges | 13 (15) |
| 16 | Rerebraces L/R | upperarm | tubular upper-arm plates | 1 ridge | 7 (8) |
| 17 | Vambraces L/R | lowerarm | closed vambraces + fan couters | big fluted fan at the elbow | 7 (8) |
| 18 | Fauld | pelvis | 3-4 fluted lames + 2 pointed tassets | cusped tasset edges | 8 (10) |
| 19 | Cuisses L/R | thigh | cuisses + fan poleyns | fluted poleyn wing | 10 (12) |
| 20 | Doublet | spine_03 | arming doublet (cloth part, replaces the cape) | linen, mail voiders | 3 (4) |

**Bundles (as #424):** Gothic Helm (15) · Gothic Torso (10, 11, 16, 20) · Gothic Gauntlets (12, 17) · Gothic Legs
(13, 14, 18, 19). Price = sum of parts (proposed 80 % of Obsidian: plain steel, no ember magic).

**Set tiers (bundles worn):** 1: -2 % damage taken, +3 % move speed · 2: -5 %, +5 % · 3: -8 %, +7 %, faster stamina
regen · 4/4: -12 %, +10 % move speed, "Helmschmid's Edge" (+10 % sword damage). Lighter and faster than Obsidian
(-15 % / ember shockwave), so the two sets play differently. One set counts per slot.

## Build plan
1. **Modelling (TGA after #49, or TGA1):** 11 meshes fitted to `ShadowknightUE_SK` ref pose like Obsidian (same folder
   layout under `/Game/CastleDefender/Characters/Hero/Armor/LandshutGothic/`), flutes and edges in the geometry, 2K
   BaseColor / ORM / Normal per part, pbr_check, Cycles turntables at locked exposure for the shop icons.
2. **System (i5):** a second set component on the BPC_ObsidianSet v3 pattern (or a set id on the same component, decided
   on the fresh export), 4 bundle rows in BPC_VesnaTrade, inventory/Vesna doll icons. Needs fresh exports of
   BPC_ObsidianSet + BPC_VesnaTrade (requested from i9 in the fast chat, line 887).
3. **i9** applies the pre-checked hand-off, Play-tests: buy, wear, mix with Obsidian, set tiers.
