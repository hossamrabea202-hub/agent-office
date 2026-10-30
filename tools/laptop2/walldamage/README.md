# Castle wall damage generator (#193) — v1 stand-in, handed to TGA for the night pass

`walldamage.py` (Blender 4.5 bundled Python, numpy, imports `shieldkit.py`): builds a stone wall from courses of ashlar
blocks and applies damage in physical order — impact craters, missing blocks (rubble core behind), conchoidal corner
chips (more near the top and the impacts), broken/missing merlons, a bulge above holes, rubble heaps at the foot.
`RES=low|high VARIANT=Wall|Tower|Crenel DAMAGE=0..1`. `standin_v1.png` is the clay of DAMAGE=0.6.

Owner rules (hard): never edit the live wall material or any decal/DBuffer setting. Output = NEW mesh variants that keep
material slot 0 + UV0; bake damage normal/AO/mask to UV1. Master tests one piece beside an original with decals first.

Night plan (TGA): 1) when the Master's export lands (#194), re-block the real wall/tower meshes by their course lines
(detect courses from the Megascans UV or from z-bands of the mesh) and feed them through the same damage plan;
2) chips need to read as conchoidal shells, not planar cuts — add 2–3 nested shells with fbm rims on the high;
3) 3 damage levels per piece (0.3 / 0.6 / 0.9) + 2 breach pieces; 4) bake with the staged bake (bake_shield.py, UV1),
validator + lookdev renders; 5) hand off as a mesh swap list for the Master.
