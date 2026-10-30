# Medic gear for #185 (#202 item 8) — TGA (Claude), 2026-10-30

Original procedural medic attachables / props. Sources: `tools/tga/medic/` (`build_medic.py` → `bake_medic.py` →
`lookdev_medic.py`). Run `import_medicgear_ue.py` in the UE 5.3 editor (`py "<path>"`).

| Mesh | Tris | Pivot / attach |
|---|---|---|
| SM_MedicSatchel | 0.9k | top of the strap → `spine_03` / `Spine2`, bag at the hip |
| SM_MedicArmband | 0.3k | arm axis centre, band around local Z → `upperarm_l` / `LeftArm` (rotate so Z follows the bone) |
| SM_BandageRoll | 0.2k | roll centre on the ground → `hand_l` prop, or a heal pickup (has box collision) |

- **Emblem:** the satchel's linen patch carries an embroidered **green herb sprig**, deliberately *not* a red cross:
  the red cross is a protected emblem (Geneva Conventions) that games are asked not to use. The white armband stays
  plain for the same reason; tint it via Tint/TintAmount if the team wants a colour code.
- Linen: off-white with a visible weave, dirt and old washed-out blood spots; leather and rusted iron as the miner gear.
- One shared 2048² atlas (≈2.8k px/m). pbr_check OK. M_MedicGear / MI_MedicGear (Tint, TintAmount, Wetness).

Screens: `screens/`.
