# Miner NPC gear (#202 item 7) — TGA (Claude), 2026-10-30

Original procedural attachables for the #201 mine workers. Sources: `tools/tga/miner/` (`build_miner.py` →
`bake_miner.py` → `lookdev_miner.py`). Run `import_minergear_ue.py` in the UE 5.3 editor (`py "<path>"`).

| Mesh | Tris | Pivot / attach |
|---|---|---|
| SM_MinerPick | 0.3k | pivot = grip (12 cm up the haft), haft along +Z, prongs along ±X → `hand_r` socket (Mannequin) / `RightHand` (SK_Zombie names) |
| SM_MinerHelmet | 1.7k | pivot = head centre at the cap rim, front = −Y → `head` / `Head` socket, ~+9 cm up |
| SM_MinerSatchel | 0.9k | pivot = top of the strap → `spine_03` / `Spine2`, hanging at the hip |

- Pick: oiled, hand-darkened ash haft; tapered, slightly drooping iron prongs and collar.
- Helmet: hardened leather cap with crossing iron bands and a brim, a candle stub in an iron cup at the front; the flame
  is in `T_MinerGear_E` → M_MinerGear emissive (GlowIntensity 8). Add a small point light on the NPC (warm, ~150 cm) for
  the mine.
- Satchel: leather bag bulging with ore, flap, iron buckle, shoulder strap.
- One shared 2048² atlas (≈1770 px/m): wood / iron (mostly rusted, bare spots metallic) / leather / wax / flame by a
  baked material id. pbr_check OK. No collision (attachables). Socket offsets need a quick in-editor nudge per rig.

Screens: `screens/`.
