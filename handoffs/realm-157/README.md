# #157 Tentacle realm: screen-edge distortion (post process)

The owner's idea: inside the tentacle minefield "the edges and corners of the screen get some distortion, like it's a
realm". `make_realm_pp.py` builds it: `M_PP_Realm` / `MI_PP_Realm` in `/Game/CastleDefender/Realm/`.

What it does: the centre of the screen stays clean (so the fight is readable); from `EdgeStart` outward the picture
bends with slow living noise, the colours split (chromatic), and the corners breathe a purple tint and darken.

Editor driver steps:
1. `py "<repo>/handoffs/realm-157/make_realm_pp.py"`
2. Drop a **PostProcessVolume** over the realm area (the #29 border's east gate side), *not* unbound, Blend Radius 800,
   Post Process Materials: `MI_PP_Realm`, weight 1. Crossing the gate fades it in over the blend radius.
3. Tune on the MI: Strength 0.8, EdgeStart 0.45, Speed 0.35, Split 0.004, TintAmount 0.35. Keep Strength ≤ 1.
4. Pair it with the realm fog from the knowledge base (cold fog colour, low height fog density 0.04) and the realm
   flora kit (`assets/laptop2/FloraKit`: Bloodcap, SporeStalk, TentacleFern, CorruptPatch, BlobMine, EggCluster).
