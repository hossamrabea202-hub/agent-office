# Siege gate (#29): water-worn wooden double gate with a lever

Made 2026-10-30 by `hossam gmail laptop2 (Claude)` for the border gap on the east side (the owner's blue marks). It fits
the siege barricade kit: bark log posts and lintel with hemp lashings, plank leaves (ledges, Z-braces, strap hinges,
clench nails), a drop bar, and a lever post with a rope to the lintel. The wood is worn by water: wet band, tide lines,
algae and rot at the bottom, rain streaks from the top, rust runs below every nail. Knowledge-base standard, 4K bake.

Pieces (one texture `T_SiegeGate`): `SM_SiegeGate_Frame` (posts, lintel, pintles, brackets), `_LeafL`, `_LeafR`
(pivot = hinge line, swing about Z), `_Bar` (lift to open), `_Lever` (pivot = the arm's pin). Opening 5.8 m, leaves
3.25 m tall. Outside (toward the realm) = -Y.

## Placement and the E prompt

`handoffs/player-boundaries-29/place_border_v4.py` places the gate with the whole border (frame + pieces at their
pivots, chevals flanking it). Behaviour for the editor driver: a `BP_SiegeGate` that holds the 5 meshes and an E prompt
on the lever ("Open the gate" / "Close the gate", #68 look). On open: rotate Lever -35° over 0.4 s, lift Bar 0.4 m, swing
LeafL -95° and LeafR +95° over 2.5 s (ease out) with a wood groan. On close: the reverse. NavMesh: a Nav Modifier volume
in the opening toggled with the leaves, so soldiers and zombies path through only when it is open.

## Unreal

`py "<repo>/assets/laptop2/SiegeGate/import_kit_ue.py"` → `/Game/CastleDefender/Environment/Boundaries/SiegeGate/`,
MI of `M_LP2Weapon`, 3 LODs, box collision per piece. `source/` rebuilds it.
