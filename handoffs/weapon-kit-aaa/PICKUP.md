# #397 weapon kit AAA: pick-up note (TGA, 2026-11-01, written low on tokens)

## Done
- **Research:** `RESEARCH.md` covers forged steel, forge scale, ash, leather and brass, with sources. The calibrated values table and the 8-point recipe are in it, and the findings are added to `handoffs/knowledge/KNOWLEDGE_LOG.md`.
- **Recipe (code), in `tools/tga/weapons/`:**
  - `aaa_mats.py`: layered materials, with metallic strictly 0 / 1:
    - ground blade flats with grind streaks along the length;
    - a stoned edge band;
    - forge scale (non-metal) on forged heads next to a ground edge strip with a wavy boundary;
    - rust only in cavities;
    - hammer dimples;
    - oiled ash and oak with hand polish and a dirty butt;
    - leather with a sweat-darkened palm;
    - brass tarnish.
  - `build_weapon_aaa.py`: runs checkking's generator, unchanged on disk and patched in memory. It adds:
    - the AAA materials;
    - a **secondary edge bevel** (grind line) on every blade section;
    - point attributes `gf` / `fg` (edge distance, forged head);
    - the ORM metal threshold;
    - the metal border-texel lift.
    Output keeps the **same names, pivots and axes** (`SM_CK_<Name>`, `T_CK_<Name>_*`).
  - `lookdev_weapon.py`: the locked rig (AgX, exposure 0, key / rim / fill, 18 % card), with a **grey ball and a chrome ball**, plus a `_detail.png` close-up. It renders both BEFORE (the CK kit) and AFTER.
  - `run_batch.ps1`: builds, renders before / after, and runs pbr_check for a list of weapons.
- **Import:** `assets/tga/WeaponsAAA/import_weapons_aaa_ue.py` (DRY_RUN) imports into the **new** folder `/Game/CastleDefender/Weapons/CK_AAA/<Name>`, with `MI_CK_<Name>_AAA` parented to the existing (read-only) `M_CK_Weapon`. Texture settings: 1K cap, Sharpen4, ORM Masks with Composite = normal on G, normal BC5.
- **First result, arming sword:**
  - AAA: pbr_check **OK** (non-metal p50 57, metal p50 197);
  - the live CK version **FAILS** pbr_check (36.7 % of non-metal texels darker than 30 sRGB, 18.9 % of metal texels below 150).

## In flight / next step
1. The batch for the 5 most-seen weapons (arming sword, longsword, war axe, halberd, flanged mace) was running into `T:\waaa`:
   ```
   powershell -File R:\tools\tga\weapons\run_batch.ps1 -Out T:\waaa
   ```
   Each one gives `T:\waaa\<Name>\` (fbx and textures), `before_<Name>.png`, `after_<Name>.png` and the `_detail` versions, plus `PBRLINE` output.
2. Copy each `T:\waaa\<Name>` to `assets/tga/WeaponsAAA/<Name>/` (fbx and textures), and the renders to `renders/`.
3. Make the **before / after sheet**: per weapon, BEFORE | AFTER | AFTER detail, captioned with the pbr_check lines. Post it with `node tools/shot.js --seat "TGA (Claude)" --file <sheet> --caption "..." --card 397`, and ask the owner for an OK.
4. After the owner's OK, run the other 20 with the same command, `-Weapons <list>` (keys are in `run_batch.ps1`), then hand off to the Master:
   1. import with DRY_RUN, then for real;
   2. compare the bounds lines (live vs AAA within ~1 cm);
   3. swap only on the owner's OK, by re-pointing the BP / attach references from `CK/<Name>/SM_CK_<Name>` to `CK_AAA/<Name>/SM_CK_<Name>`.
   The #254 wiring and #95 looks keep working, because the names and pivots are the same.

## Known limits
- The grind line and stoned edge read in the `_detail` renders. At full-weapon distance the difference is mostly roughness and values (KB rule 2).
- The texture budget: authored at 2K, capped to 1K in the importer (#260).
