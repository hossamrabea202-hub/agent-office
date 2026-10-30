# Castle wall damage generator (#193) â€” v1 stand-in, handed to TGA for the night pass

`walldamage.py` (Blender 4.5 bundled Python, numpy, imports `shieldkit.py`): builds a stone wall from courses of ashlar
blocks and applies damage in physical order â€” impact craters, missing blocks (rubble core behind), conchoidal corner
chips (more near the top and the impacts), broken/missing merlons, a bulge above holes, rubble heaps at the foot.
`RES=low|high VARIANT=Wall|Tower|Crenel DAMAGE=0..1`. `standin_v1.png` is the clay of DAMAGE=0.6.

Owner rules (hard): never edit the live wall material or any decal/DBuffer setting. Output = NEW mesh variants that keep
material slot 0 + UV0; bake damage normal/AO/mask to UV1. Master tests one piece beside an original with decals first.

Night plan (TGA): 1) when the Master's export lands (#194), re-block the real wall/tower meshes by their course lines
(detect courses from the Megascans UV or from z-bands of the mesh) and feed them through the same damage plan;
2) chips need to read as conchoidal shells, not planar cuts â€” add 2â€“3 nested shells with fbm rims on the high;
3) 3 damage levels per piece (0.3 / 0.6 / 0.9) + 2 breach pieces; 4) bake with the staged bake (bake_shield.py, UV1),
validator + lookdev renders; 5) hand off as a mesh swap list for the Master.

## v2 (TGA, 2026-10-30, #193)

- **Blocks:** rounded boxes with **even vertex density** (`rounded_box`: a welded lattice of the box surface pulled
  onto a radius-bevel SDF; 1.5 cm high / 9 cm low; bevel 1.2-2.4 cm). v1's superellipsoid crowded its vertices on the
  edges, so faces were nearly empty and fractures crumpled.
- **Chips are real conchoidal fractures** (`conchoidal`), chipped in **metric** space so they're round, not
  stretched:
  - vertices inside a large fracture sphere set just outside the corner are projected onto it: a shallow concave
    scoop with a sharp rim
  - a nested inner shell scoops deeper
  - a coarse ragged rim
  - stepped (sawtooth) shell ridges round the impact point
- **Spalling:** blocks beside a missing block spall on the corners that face the hole. Tool marks now run along the
  surface normal, in metres.
- **Missing blocks:** the radius was widened (v1 rarely caught a block). Levels: 0.3 = chips + one strike, 0.6 = holes
  + spalling, 0.9 = battered breach. See `standin_v2_sheet.jpg`.
- **Next, when export #194 lands:** re-block the real meshes by their course lines and run them through the same
  plan. 3 levels per piece + 2 breach pieces; UV0 and slot 0 kept, damage baked to UV1. The Master does the
  side-by-side test first.