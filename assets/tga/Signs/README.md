# Hanging shop signs (#202 item 6) — TGA (Claude), 2026-10-30

Original procedural wall signs for the castle town. Sources: `tools/tga/signs/` (`build_signs.py` → `bake_signs.py`
→ `lookdev_signs.py`). Run `import_signs_ue.py` in the UE 5.3 editor (`py "<path>"`).

| Mesh | Emblem | Tris |
|---|---|---|
| SM_Sign_Smith | iron anvil with a hammer standing on it | 1.0k |
| SM_Sign_Tavern | carved wooden tankard | 1.0k |
| SM_Sign_Shop | gilded coin stack | 1.3k |

- Each: iron wall plate + 0.95 m bracket arm with a curled brace, two short chains, a 0.7 × 0.45 m board with a top
  batten; the emblem is a raised silhouette on both faces. Pivot = top of the wall plate: place flush on a wall at
  about 2.6 m; the sign hangs along +X.
- One shared 2048² atlas (≈880 px/m): weathered wood (the ore-shed baker), iron mostly rusted with small bare worn
  spots (bare iron metallic, rust non-metal), worn gilt (metallic, grimy in the recesses). pbr_check OK.
  Honest note: the gilt coins pick up a faint wood-grain stripe in the normal map; invisible at street distance.
- M_Sign / MI_Sign with Tint, TintAmount, Wetness. Box collision each.
- Swinging in the wind: they are static meshes; for motion, rotate the board part in a BP or use a small physics
  constraint. (Ask TGA for split board/bracket meshes if wanted.)

Screens: `screens/`.
