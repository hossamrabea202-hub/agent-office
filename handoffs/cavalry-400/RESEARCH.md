# #400 Stables, horses, knights, heavy cavalry: research (checkking, 2026-11-01)

Owner's order: "W: stables, horses, knights, heavy cavalary". Cards #401 stables, #402 destrier, #403 cavalry knights,
#404 heavy cavalry gameplay. This file is the study done before building (rule `M:` / visual rule). Items marked
**[UNVERIFIED]** are single-source or my inference; they are tested in lookdev and logged in `KNOWLEDGE_LOG.md`.

## 1. Medieval stables (#401)

What survives is thin: Giles Worsley calls the medieval stable "an archaeological black hole" (Exeter *Warhorse*
project). The best evidence:

- **Veselí nad Moravou castle (CZ), 13th–14th c.:** a timber stable in the bailey, studied with soil chemistry,
  pollen and parasites (PLOS ONE, doi 10.1371/journal.pone.0089273). Used for couriers', workers' and battle horses.
  Floor layers were dung, straw and hay; the stable was cleaned and re-floored many times.
- **Manorland, Co. Meath (IE):** a stable inside a keep's outer enclosure: post-holes, **pad-stones** under the
  posts, **stall divisions** and **drainage gullies**.
- **Tattershall (Lincs.):** accounts name a "great stable"; it's being looked for (Warhorse project).
- **Montfort (IL), Teutonic Order:** stables next to the gate (found 2014). Near the gate is the usual place: horses
  leave fast, dung leaves without crossing the court.

### What we build from it (Decision)

| Feature | Value | Why |
|---|---|---|
| Plan | 4-bay timber range, **16 × 7 m**, lean-to roof against the wall side, open front with a 2 m eaves overhang | lean-to ranges against the curtain wall are the common castle type; open front reads in third person |
| Frame | oak posts 25 × 25 cm on **pad-stones** (no posts in the ground: rot), tie beams, braces | Manorland pad-stones; standard medieval carpentry |
| Infill | wattle-and-daub panels, **limewashed** (albedo 0.40–0.45, never 255) | INDUSTRY_SECRETS rule 4 (castles were whitewashed), §1.1 plaster |
| Stalls | **6 standing (tie) stalls 1.6 × 3.0 m** + **2 loose boxes 3.2 × 3.2 m** for the destriers | medieval horses mostly ≤ 14.2 hands (see §2), so small stalls; the best horses get boxes [UNVERIFIED stall sizes, inferred from 14–15 hh horses] |
| Stall walls | heavy oak **kicking boards** 1.4 m high, top rail polished by chewing (crib-biting) | wear with a cause: the top rail edge is smoother and paler where horses chew |
| Feeding | wall **manger** (trough) at chest height, **hay rack** above, slanting | hay rack above the manger is standard in surviving later stables |
| Floor | packed earth + **straw bedding**, a cobbled strip along the open front with a **drain gully** | Manorland gullies; Veselí floor layers |
| Roof | oak shingles (castle courts burn; shingle reads cleaner than thatch next to the keep) | Decision; thatch kept as option |
| Props | tack pegs with saddles/bridles, water trough, wheelbarrow-free (anachronism check: wheelbarrows exist from c. 1170, allowed), dung heap outside, pitchfork, buckets | KCD rule: "people smell the inaccuracy" when small details miss |

Wear by cause (KB rule 3): grey sun-bleach on the front posts and shingles, dark wet band and splashed muck on the
bottom 30 cm of the stall boards, urine-stained straw (yellow-brown, glossier) at the back of each stall, cobweb/dust on
up-facing beams, chew marks on the rails, rust streaks under every iron ring.

## 2. Horses (#402)

- **Size:** Exeter study of 1,964 bones from 171 English sites (Outram et al. 2022, *Int. J. Osteoarchaeology*):
  most medieval horses were **under 14.2 hands (1.47 m)**; destriers were large for their time but far smaller than
  modern heavy breeds; selection was for temperament and build as much as height. A ~14–15 hand horse carries an
  armoured knight fine.
- **Decision:** our destrier is **15 hands (1.52 m at the withers)**, deep chest, short strong back, thick crested
  neck (stallion), heavy hindquarters: a compact Iberian/Friesian-like build, **not** a Shire. Same scale as TGA's #155
  horse (withers ~1.5 m), so the two share proportions and the pipeline.
- **Coats:** bay, grey (dappled), black. No measured spectral albedo exists (searched: only CIE L\*a\*b\* coat studies, e.g.
  Posavje horses, Slovenia, which show bay/chestnut vary a lot in lightness). Values therefore follow the KB fur row
  (roughness 0.65–0.75) and dyed/natural dark floors: black coat ≥ 40 sRGB (dark natural material, never pure black),
  bay body ~100/62/40 sRGB with black points, grey 150 with dapples.
- **Coat detail:** at gameplay distance hair-stroke normal + sheen reads as coat (TGA's lesson: smooth hide up close).
  Mane and tail are **mesh strands (cards)**, the forelock too; a groom only if the camera gets close.
- **Realism tells:** a horse's living look comes from the head: big dark wet eye with a highlight, mobile ears, nostril
  flare, and the neck/head bob in walk and gallop. Rockstar's RDR2 horses (AI and Games breakdown via 80.lv) stress
  lateral movement, terrain response and a personality layer: we add head bob, ear turns in idle, and tail swish.

## 3. Tack and barding (#402)

- **War saddle:** wooden tree (pommel, cantle, two side bars), covered in leather or heavy cloth; **high pommel and
  high cantle** so the knight isn't pushed back off the horse when the lance hits (Fitzwilliam, Met, Worcester museum
  records). Breast strap and crupper hold it in place.
- **Bridle:** headstall, browband, noseband, curb bit, long reins.
- **Barding:** **chanfron** (face plate, ears to muzzle, eye flanges), **crinet** (articulated neck lames over the mane),
  **caparison** (cloth cover over everything, carrying the heraldry). Horse armour spreads through the 14th–15th c.
  after Bannockburn and Crécy (horses killed by infantry and archers). Usually mail or plate **under** a caparison.
- **Decision (v1):** saddle + bridle + chanfron + **quilted/cloth caparison in the castle's colours** (cloth hides the
  legs' top and the belly, which also hides deformation). Crinet as plate lames on the neck. Full plate peytral/crupper
  only in a v2 if the owner wants it.

## 4. Knights (#403)

- Mounted knight look c. 1300–1350 (matches the castle): **great helm** or bascinet, mail + coat of plates, **surcoat
  in the same heraldry as the caparison**, heater shield on the left, **couched lance** (3–3.5 m ash shaft, vamplate
  optional, iron head).
- Heraldry: plain bold tinctures read at distance; keep dyes in the measured wool range (dark dyes 41–73 sRGB,
  roughness 0.8–0.96, INDUSTRY_SECRETS §1.1) and saturation ≤ 60 %.

## 5. Heavy cavalry behaviour (#404)

- **Charge:** knights in closed ranks, lance couched under the arm, full gallop at impact; the French way was a long
  double line (*en haie*), the German a deeper wedge. The hard part was keeping the line and spacing while
  accelerating so top speed comes **at** impact (Wikipedia "Lance", "Cavalry tactics"). Reenactment evidence says the
  couched charge works without stirrups too, so no need to fuss over that.
- **Weakness:** cavalry that stops inside a crowd loses its whole advantage. It must **ride through, wheel, re-form,
  charge again** (the classic charge cycle).
- **Game translation (Decision):** a squad of 4 knights. States: *Form up* (line abreast, 3 m apart) → *Charge*
  (accelerate over ~3 s to 9 m/s, lance down) → *Impact* (first target takes heavy damage scaled by speed, zombies in a
  cone are knocked back, the lance can break: 30 %) → *Ride through* (no stopping, sword hits on the way) → *Wheel* (turn
  out 25–35 m past) → *Re-form* → repeat. If speed falls under 3 m/s with ≥ 4 zombies within 3 m, the knight is
  "bogged": it takes double damage until it rides out. That gives the player a reason to aim charges and not throw
  cavalry into a mob. Details in `GAMEPLAY.md`.

## Sources

- Exeter Warhorse project: https://medievalwarhorse.exeter.ac.uk/2022/05/
- Veselí stable, PLOS ONE: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3966733/ (summary: https://madbarn.com/research/medieval-horse-stable-the-results-of-multi-proxy-interdisciplinary-research)
- Manorland stable: https://irishhistory.com/?p=190545
- Montfort stables: https://www.adrianjboas.com/post/on-locating-the-stables
- Horse size (Outram et al. 2022): https://eprints.whiterose.ac.uk/178141/1/oa.3038.pdf ;
  https://discovermagazine.com/the-sciences/medieval-warhorses-were-more-like-ponies ;
  https://equineink.com/2022/03/06/re-envisioning-the-medieval-charger/
- Barding: https://en.wikipedia.org/wiki/Barding ; https://archaeotravel.eu/the-practice-of-barding-horses-in-the-history-of-armouring/ ;
  https://www.futuremuseum.co.uk/collections/features/online-exhibitions/dean-castle-arms-and-armour/armour/horses-chanfron ;
  https://www.wikiwand.com/en/articles/Crinet
- Saddles: https://worcester.emuseum.com/objects/47950/war-saddle ; https://data.fitzmuseum.cam.ac.uk/id/object/18668 ;
  https://www.metmuseum.org/art/collection/search/25402 ; https://journals.iaepan.pl/fah/article/download/2074/2540
- Lance and charge: https://en.wikipedia.org/wiki/Lance ; https://cavac.at/cavacopedia/Cavalry_tactics
- Coat colour: https://www.dlib.si/stream/URN:NBN:SI:DOC-323OGSZS/f6c33c9d-b1cb-4d62-a395-9f4e73ce899c/PDF
- RDR2 horses: https://80.lv/articles/making-believable-in-game-horses-for-red-dead-redemption-2
- Not found: a measured horse-coat albedo; measured medieval stall sizes (stall sizes above are inferred).
