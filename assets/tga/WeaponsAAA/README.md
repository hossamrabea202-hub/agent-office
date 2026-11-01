# Weapon kit AAA (#397, TGA): first 5 weapons

These are AAA versions of checkking's CK kit: the arming sword, longsword, war axe, halberd and flanged mace.
- **Same names, pivots and axes** as the live kit (`SM_CK_<Name>`, `T_CK_<Name>_BaseColor / _ORM / _Normal_DirectX`).
- **New assets only:** the live CK kit and `M_CK_Weapon` aren't touched.
- **Recipe and sources:** `handoffs/weapon-kit-aaa/RESEARCH.md`.
- **Tools:** `tools/tga/weapons` (`build_weapon_aaa.py`, `aaa_mats.py`, `lookdev_weapon.py`, `run_batch.ps1`).
- **pbr_check: all 5 AAA OK; all 5 live CK FAIL** (too-black non-metal and too-dark metal).
- **Before / after:** `handoffs/weapon-kit-aaa/renders/before_after_5.jpg`, with per-weapon renders in `<Name>/renders/`.
- **Import:** `import_weapons_aaa_ue.py` (DRY_RUN) imports into `/Game/CastleDefender/Weapons/CK_AAA/<Name>`. Swap only after the owner's OK.
