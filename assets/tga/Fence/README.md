# Road fence segments (#202 item 3) — TGA (Claude), 2026-10-30

Original procedural split-rail fence for the #201 cart road. Sources: `tools/tga/fence/` (`build_fence.py` →
`bake_fence.py` → `lookdev_fence.py`). Run `import_fence_ue.py` in the UE 5.3 editor (`py "<path>"`).

| Mesh | Length | Tris | Notes |
|---|---|---|---|
| SM_Fence_2m | 2 m | 150 | post + 2 sagging rails |
| SM_Fence_3m | 3 m | 150 | |
| SM_Fence_4m | 4 m | 150 | rails sag more |
| SM_Fence_Broken | 3 m | 450 | post leaning out, top rail snapped (one half hanging, the other on the ground), splinters |

- Each segment starts at its post (pivot at the post's foot, posts sink 25 cm into the ground, 1.2 m above) and runs
  along +X; the next segment's post closes the run, so snap them at 200 / 300 / 400 cm and end a run with a 2 m piece.
- One shared 2048² atlas (≈450 px/m): BaseColor sRGB, ORM (R AO, G roughness, B metallic = 0), Normal DirectX. The
  ore-shed wood: grain along each timber, sun-greyed tops, damp base. pbr_check OK.
- M_Fence / MI_Fence: Tint, TintAmount, Wetness. Box collision per segment.

Screens: `screens/`.
