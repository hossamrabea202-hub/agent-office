# #169 stage 1 — closed tentacle realm (laptop2)

Run order in the editor (game level open), each a `py "<repo>/..."`:

1. Imports (skip the ones already done):
   `assets/laptop2/SiegeGate/import_kit_ue.py` (the wooden double gate, 5 meshes, hinge pivots) ·
   `assets/laptop2/FloraKit/import_flora_ue.py` (realm plants, blob mines, egg clusters) ·
   `assets/laptop2/CampKit/import_kit_ue.py TorchPost` ·
   `assets/laptop2/RealmKit/import_realm_ue.py` (the dome mesh).
2. `handoffs/realm-169/make_realm_membrane.py` → `M_RealmMembrane` / `MI_RealmMembrane` (v2, per the concept: glassy
   membrane with a cell network and bright veins, rim, breathing). **One hand step:** open `M_RealmMembrane`, drag the
   Multiply node labelled `WPO_OUT` into *World Position Offset*, Apply (Python cannot connect WPO in 5.3). That is the wobble.
3. `handoffs/realm-169/place_realm_ue.py` → everything below, in `Gameplay/Realm`, labels `Realm_*`, tag `laptop2_realm`.
   Re-run any time: it removes its own actors first and touches nothing else (`PPV_Realm` and the old `Realm_Bubble` stay;
   hide the old sphere once the dome is in).
4. Look check from the owner's camera (-7945, 454, 1932 / yaw 157.6 pitch -11), day and night. Tune on `MI_RealmBubble2`:
   `ClearOpacity` 0.04, `WallOpacity` 0.18, `VeinOpacity` 0.55, `RimOpacity` 0.5, `Glow` 2.0 (night 1.2), `WobbleCm` 60.
   `Realm_Light_Core` (pink, 40 000 cd) is what Lumen sees; drop it if the inside blows out.

**v2 changes (2026-10-30 10:40, after the Master's report):** dome scale fixed (the unit mesh is 100 cm/unit: now
156 × 84 m, 85 m tall, front edge 1.8 m behind the wall, placed *last* so its collision never catches the ground traces,
which is why 0 plants were placed before); traces ignore everything the script placed; watchtowers every 30 m + two
flanking the gate; torch posts at the gate. Still to come: the arched gate with iron bands (the kit's 4K lands ~11:45,
an arch variant after), banners on the towers.

What the script places: the 120 m palisade wall P4→P1 (spikes to the road), watchtowers at both ends, the gate at
X -15000 (`Realm_Gate_Frame/LeafL/LeafR/Bar/Lever`, leaves/bar/lever movable, `Realm_Gate_Trigger` TargetPoint on the road
side for the E prompt), chevals flanking it, the breach pair `Realm_Wall_Breach_A/B` at X -10500 + `Realm_Breach_Point`
(Codex: swap them for `SM_SiegeBarricade_Breach` at the breach wave), the dome `Realm_Dome` with core + fill lights,
26 corrupt patches, 102 realm plants, 22 blob mines, 7 egg clusters, `Realm_Spawn_Zombie_00..11`, `Realm_Spawn_Giant_00/01`,
`Realm_Spawn_Wasp` (north, the mountain crack), and torch posts every 12 m outside the wall.

**Gate behaviour without a new Blueprint:** `handoffs/realm-169/place_realm_gate_bp.py` (run after step 3) spawns the
level's own `BP_CastleGateControl` at the realm gate and swaps its door/lever meshes for the siege gate leaves on that
instance (E prompt, swing, zombie block, damage/repair all come for free). Play-test E; if a leaf swings the wrong way,
mirror the pivot Y in the script or flip the open angle on the instance.

For Codex / TGA (only if the reuse above is not enough): hinge = the LeafL/LeafR actor pivots; open = yaw ∓95° over 1.2 s (ease out), Bar up 40 cm first,
Lever -35°. Zombies never open it; the leaves block nav when closed (Nav Modifier in the opening).
