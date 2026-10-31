# Feast set for #227 — TGA (Claude), 2026-10-31

Art for the courtyard banquet (the food / morale logic and the HUD stay with the Master). Original procedural work.
Sources: `tools/tga/feast/` (`build_feast.py` → `bake_feast.py` → `lookdev_feast.py`). `build_feast.py` reuses the
timber/log helpers from `tools/tga/siege/build_siege.py`. Run `import_feast_ue.py` in the UE 5.3 editor (`py "<path>"`);
it lands in `/Game/CastleDefender/Props/Feast`.

| Mesh | Tris | What |
|---|---|---|
| SM_Feast_Table | 11.6k | 3 m oak trestle table laid for a feast: linen runner, a roast on a carving board, 4 loaves, a cheese wheel, a bowl of apples, 8 pewter plates + tankards, 3 candles |
| SM_Feast_TableBare | 1.1k | the same table cleared, for normal days |
| SM_Feast_Bench | 0.5k | 3 m bench, seat 45 cm |
| SM_Feast_Torch | 2.5k | 1.9 m standing torch on a tripod: iron basket, pitch-soaked head, a mesh flame |

- **Feast toggle:** put the bare table in the courtyard and swap it for `SM_Feast_Table` when the feast starts (same transform). Place a bench on each side at ±72 cm in Y.
- **Sockets:**
  - Both tables have `Seat_0..7` sockets: 4 places per side, at the bench line, 45 cm up.
  - The torch has a `Flame` socket (0, 0, 192): attach a warm point light (≈2700 K) and a fire Niagara there.
  - The mesh flame glows through `GlowIntensity`; set it to 0 if the Niagara flame replaces it.
- **Texture atlas:** one 4096² atlas (`T_Feast_BC/_ORM/_N/_E`) for all four meshes.
  - Contents: oiled oak with wine stains, crusty bread with flour, a roast, a cheese rind, apples, pewter (metal), linen, wax, pitch and iron.
  - `_E` holds only the flames. pbr_check OK.
  - Material: `M_Feast` / `MI_Feast` with Tint, TintAmount, Wetness, GlowTex and GlowIntensity (8).
- **Collision:** a box on the tables and the bench, 10-DOP on the torch.
- **Honest notes:**
  - The mesh flames look solid in daylight. They are meant for night with a light and FX on the `Flame` socket.
  - Food is welded to the table mesh, so it can't be eaten piece by piece. If the feast should empty over time, ask and I'll split the food into separate meshes.

Screens: `screens/`.
