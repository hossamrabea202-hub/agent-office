# Realm dressing (#202 item 10) — TGA (Claude), 2026-10-30

Original procedural realm props to scatter round the Realm crack (#171) and the breach (#190). Sources:
`tools/tga/realmdress/` (`build_realm.py` → `bake_realm.py` → `lookdev_realm.py`). Run `import_realmdressing_ue.py`.

| Mesh | Tris | What |
|---|---|---|
| SM_Realm_SpitSac | 8.6k | a tentacle-burrow spit sac: earth mound broken open by roots, a ribbed fleshy stalk, a swollen glowing sac (~1.4 m) |
| SM_Realm_SporeVent | 6.7k | a ridged fleshy chimney (~0.85 m) with a glowing pink mouth and pale spore nodules round its foot |

- Built like the v2 zombies (lofts + blobs fused by a voxel remesh, smoothed, organic surface noise, decimated).
  Pivots on the ground under each piece.
- One shared 2048² atlas (≈510 px/m): earth on the mound, dark realm flesh with thin pink veins, a membrane sac,
  pale spores, and `T_RealmDress_E` (veins / sac / vent mouth / spores) → pink emissive (GlowIntensity 4, the
  RealmCrack/wasp pink). pbr_check OK. M_RealmDress / MI_RealmDress. 26-DOP collision.
- Idea for life: pulse GlowIntensity 2→6 over ~2 s in a tiny BP, and puff a spore particle from the vent mouth.

Screens: `screens/`.
