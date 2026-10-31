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

---

## v2: no volume to place (adjustedfilm, 2026-10-31). Use this instead of v1's steps.

The look is laptop2's v1. What changes:
- **No PostProcessVolume to place.** The effect follows the hero.
- **Safe re-run.** v1 deleted its material on a re-run, which broke MI_PP_Realm. v2 rebuilds it in place.
- **Outside the realm the picture is exactly the original.** Everything is scaled by `MPC_Realm.Inside` and lerped onto
  the untouched scene sample.
- **Desaturate 10 % inside** (card spec).
- **Fades in and out over about 2 s** when you cross into the realm or out of it.
- **Where the realm is:**
  - `BPC_RealmFX`, the hero component "RealmFX", finds every actor tagged `laptop2_realm` (laptop2's #169 placement);
  - centre = their average position; radius = 0.9 × the farthest one (the wall ring).
  - No realm in the level means nothing happens.

**Pre-checked:** `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK** (44 nodes).

**Steps (Master: paste only)**
1. `py "<repo>/handoffs/realm-157/make_realm_pp_v2_ue.py"`. It makes MPC_Realm and M_PP_Realm (+ MI), adds the
   blendable to the hero cameras, and creates BPC_RealmFX on the hero as "RealmFX".
2. Add the variables: BPC_RealmFX → paste the 5 lines of `VARIABLES_BPVar.txt`, one at a time, then Compile.
3. Paste the graph: paste `BPC_RealmFX_graph.txt` into its EventGraph. Compile and Save, then the hero.

**Checks**
1. Outside the realm the picture is unchanged (compare a screenshot from before).
2. Walk through the realm gate: within about 2 s the screen edges start to bend, the colours split and the corners turn
   purple, while the centre stays clean.
3. Walk out: it fades away in about 2 s.
4. No "Accessed None" from BPC_RealmFX.

**Tuning:** set `Strength`, `EdgeStart`, `Speed`, `Split` and `TintAmount` on **M_PP_Realm itself**. The hero cameras
use M_PP_Realm directly, so changing MI_PP_Realm does nothing.

**Note for #284 (realm vanishes):** when the realm is removed in play, also set `MPC_Realm.Inside` to 0. Otherwise the
fade stays at its last value while the hero stands where the realm was.
