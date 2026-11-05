# #509 Castle wall props (i5 checkking, 2026-11-05)

Owner (Alien): *"the castle walls needs more props"* ... *"do these by order: defence stores, switch the wind sway off at
distance for all current game assets if necessary, timber hoarding, iron rings and brackets, drain spouts, mud weeds and
moss. follow our office realism rules"*.

## What it adds, and the real reason for each (KB rule 3, INDUSTRY_SECRETS 4.5)
| # | What | Where (found by line traces on the real walls) | Why it is there |
|---|---|---|---|
| 1 | **Defence stores**: arrow sheaves (24 arrows, the English war-arrow unit) next to a barrel, spear stooks, heaps of rounded drop-stones, water buckets + a crate | on the wall walks, against the parapet, one cluster per ~7 m (about 20 on i5's copy); stones and buckets weighted to the gate | a garrison kept its ammunition where it is used; stones go over the gate, water against fire arrows |
| 2 | **Wind sway off at distance** (WPO Disable Distance) | every swaying asset in the level: grass/plants 25 m, cloth banners 40 m, trees 50 m | VSM re-renders shadow pages for anything that moves (INDUSTRY_SECRETS 2.x, 4.4: 20-50 m) |
| 3 | **Timber hoarding** (hourd): 3 bays of 3 m + 2 end walls | outside the gate coping, centred on the gate passage | put up where the assault comes; the open drop slot along the wall face is for stones and water on the men at the gate |
| 4 | **Iron tie rings** (12), **torch brackets** (beside doors), **tie-rod anchor plates** (3 pairs) | rings 1.3 m up near the gate / stables / barracks / well; brackets 2 m up beside doors; anchors ~4.5 m up on long faces | horses and carts stop there; light where people pass; the period repair that holds a bulging wall |
| 5 | **Drain spouts** (12) + a #504 sill streak under each | at wall-walk level on the outer face, every ~9 m | the walk drains outward; the water falls clear but the wall right under the lip still stains |
| 6 | **Wall-foot mud splash + moss** cards (about 240) and **weed clumps** (about 590: grass tufts, dead stalks, poppies in the sun, foxgloves in the shade) | where the walls meet the ground; not at doors, the gate passage or paved yards | rain splash-back throws soil 30-50 cm up; that strip stays damp (moss, more on the shaded faces); the strip against the wall is never trodden, so weeds grow there |

**No doubling (#461, PERFECT_CASTLE #7):** stone that already weathers its foot in its material (family C, `M_KeepEntrance_Baked`)
or wears base-grime cards (Tower9) gets weeds only, no foot card. **Restraint:** densities were set for a lived-in garrison, not a warehouse.
**The walking lane stays clear:** every store cluster leaves at least 1 m of free wall walk (most leave 1.8-2 m).

## The new props (laptop2's CampKit pipeline, same standard: low poly + 2K bake from a high poly, pbr_check)
`SM_Camp_ArrowSheaf`, `SpearStook`, `DropStones`, `FireBucket`, `HoardingBay`, `HoardingEnd`, `TieRing`, `WallBracket`, `AnchorPlate`,
`DrainSpout` in `/Game/CastleDefender/Environment/Camp/<Item>/`. Builder: `assets/laptop2/CampKit/source/build_camp.py`.
New materials in `campmat.py`: `Feather` (grey goose), `Water`, `RiverStone`; and two calibration fixes that pbr_check asked for:
- `Iron`: oxide scale and rust are non-metal (metallic 0), bare iron 1, in-between only at layer edges (KB rule 1);
- `Shaft`: roughness varied at two more scales (hand-polished grips, dull grain), it was "nearly flat".
The barrel and crate are the existing BarracksProps.

## Steps for i9 (Master), in the live session, Play stopped. `git pull` first.
```
py "<repo>/assets/laptop2/CampKit/import_kit_ue.py" ArrowSheaf SpearStook DropStones FireBucket HoardingBay HoardingEnd TieRing WallBracket AnchorPlate DrainSpout
py "<repo>/handoffs/castle-weather-504/build_weather504_ue.py"          # #504's card materials, if not built yet (the spout streaks use them)
py "<repo>/handoffs/castle-props-509/build_foot509_ue.py"                # the wall-foot card material + 2 MIs
# dry runs: each writes a report next to it; check the counts below
py "<repo>/handoffs/castle-props-509/place_stores509_ue.py"
py "<repo>/handoffs/castle-props-509/place_fittings509_ue.py"
py "<repo>/handoffs/castle-props-509/place_foot509_ue.py"
py "<repo>/handoffs/castle-props-509/wpo_audit509_ue.py"
#   ---- owner's OK on the before/after shots ----
py "<repo>/handoffs/castle-props-509/place_stores509_ue.py" --apply
py "<repo>/handoffs/castle-props-509/place_fittings509_ue.py" --apply
py "<repo>/handoffs/castle-props-509/place_foot509_ue.py" --apply
py "<repo>/handoffs/castle-props-509/wpo_audit509_ue.py" --apply        # then Save the level
```
Undo: `--remove` on each placer (deletes only its own tag: WS509 / FX509 / FW509). The WPO change is a per-component value:
re-run the audit; to undo, set the distance back to 0 on the listed components (wpo_report509.txt).
Parts only: `place_fittings509_ue.py --only hoarding,spouts,rings,brackets,anchors`. A preview near one spot: `--near x y z radius`.

## Test list
- [ ] Import: 10 meshes, 10 MIs, no import errors. The dry runs: about 20 store clusters, 3 hoarding bays + 2 ends, ~12 spouts, ~12 rings, 3-10 brackets, 6 anchors, ~240 foot cards, ~590 weeds (i5 copy; i9's rebuild may differ).
- [ ] Gate from outside: the hoarding sits flush on the coping face, putlogs enter the wall, nothing floats; the end walls close it.
- [ ] Walk the wall walks in Play: the hero passes every cluster without snagging (arrows, spears, buckets have no collision; barrel, crate, stones do).
- [ ] Wall foot: weeds stand on the ground (not floating, not in doorways), the moss/splash band sits at the base, no square card edge.
- [ ] `stat unit` before / after: one ISM per mesh (~25 draws for everything). The WPO distance should LOWER shadow cost on the meadow.
- [ ] Night: the torch brackets are unlit stubs on purpose (a lit one needs a flame Niagara + an 1800 K light, KB rule 6): say if you want them lit.

## Status
See the bottom of this file (updated as the work goes).
