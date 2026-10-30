# Siege debris set for #162 battle memory (#202 item 9) — TGA (Claude), 2026-10-30

Original procedural aftermath props. Sources: `tools/tga/debris/` (`build_debris.py` → `bake_debris.py` →
`lookdev_debris.py`). Run `import_debris_ue.py` in the UE 5.3 editor (`py "<path>"`).

| Mesh | Tris | What |
|---|---|---|
| SM_Debris_BrokenCart | 4.3k | supply cart rolled on its side: bed planks + cross-bearers, one spoked wheel (iron tyre, one broken spoke) still on the axle, the other torn off and lying flat, snapped shaft with splinters |
| SM_Debris_Beams | 2.1k | three 20 cm beams fallen across each other, jagged splintered ends |
| SM_Debris_Palisade | 0.6k | five sharpened palisade logs torn down, a scrap of binding rope across them |

- Pivots on the ground at each pile centre; rotate Z freely. Suggested #162 use: cart on the road after a convoy raid,
  beams/palisade at the gate after a breach (keeps clear of TGA's #193 wall geometry).
- One shared 2048² atlas (≈310 px/m): the ore-shed wood, plus fire-blackened char patches with grey ash, rusty iron.
  pbr_check OK. M_Debris / MI_Debris (Tint, TintAmount, Wetness). 18-DOP collision.
- Honest note: the rope uses the wood material (reads as a dark cord at gameplay distance).

Screens: `screens/`.
