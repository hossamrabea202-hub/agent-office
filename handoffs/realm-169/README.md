# #169 stage 1 — closed tentacle realm (laptop2)

Run order in the editor (game level open), each a `py "<repo>/..."`:

1. Imports (skip the ones already done):
   `assets/laptop2/SiegeGate/import_kit_ue.py` (the wooden double gate, 5 meshes, hinge pivots) ·
   `assets/laptop2/FloraKit/import_flora_ue.py` (realm plants, blob mines, egg clusters) ·
   `assets/laptop2/CampKit/import_kit_ue.py TorchPost` ·
   `assets/laptop2/RealmKit/import_realm_ue.py` (the dome mesh).
2. `handoffs/realm-169/make_realm_bubble.py` → `M_RealmBubble2` / `MI_RealmBubble2`.
3. `handoffs/realm-169/place_realm_ue.py` → everything below, in `Gameplay/Realm`, labels `Realm_*`, tag `laptop2_realm`.
   Re-run any time: it removes its own actors first and touches nothing else (`PPV_Realm` and the old `Realm_Bubble` stay;
   hide the old sphere once the dome is in).
4. Look check from the owner's camera (-7945, 454, 1932 / yaw 157.6 pitch -11), day and night. Tune on `MI_RealmBubble2`:
   `HazeOpacity` 0.10, `RimOpacity` 0.45, `TentacleContrast` 0.6, `DripAmount` 0.5, `Glow` 1.5 (night: 0.8). The dome's
   `Realm_Light_Core` (purple, 60 000 cd) is what Lumen sees; drop it to 25 000 if the inside blows out.

What the script places: the 120 m palisade wall P4→P1 (spikes to the road), watchtowers at both ends, the gate at
X -15000 (`Realm_Gate_Frame/LeafL/LeafR/Bar/Lever`, leaves/bar/lever movable, `Realm_Gate_Trigger` TargetPoint on the road
side for the E prompt), chevals flanking it, the breach pair `Realm_Wall_Breach_A/B` at X -10500 + `Realm_Breach_Point`
(Codex: swap them for `SM_SiegeBarricade_Breach` at the breach wave), the dome `Realm_Dome` with core + fill lights,
26 corrupt patches, 102 realm plants, 22 blob mines, 7 egg clusters, `Realm_Spawn_Zombie_00..11`, `Realm_Spawn_Giant_00/01`,
`Realm_Spawn_Wasp` (north, the mountain crack), and torch posts every 12 m outside the wall.

For Codex (BP_RealmGate): hinge = the LeafL/LeafR actor pivots; open = yaw ∓95° over 1.2 s (ease out), Bar up 40 cm first,
Lever -35°. Zombies never open it; the leaves block nav when closed (Nav Modifier in the opening).
