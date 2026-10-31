# #262 Texture plan

From TGA (Claude), 2026-10-31, an owner assignment relayed by checkking. It builds on #260 (texture budget script) and #261 (the Master's trim sheets).

## Result (step 5)

| | Before | After | Saved |
|---|---|---|---|
| **Repo texture sources (disk)** | 2,102 MB | 930 MB | **1,172 MB (−56 %)** |
| **GPU memory after import** (BC compression + mips, estimated) | 2,496 MB | 1,119 MB | **1,377 MB (−55 %)** |

- **Packaged build:** it shrinks by about the GPU figure, because cooked textures are the compressed mips.
- **#260 script:** the Master can still run checkking's budget script. After this pass it should find almost nothing left to cap, apart from the E1 exceptions below.

## What was done

1. **Audit:** `texture_audit.py` → **AUDIT.md** + `audit.json`.
   - Covers 695 textures in 38 kits (checkking, Codex, laptop2, tga): size, role, disk MB and GPU MB, now and at the budget.
   - Also gives each mesh's median texel density (UV length ÷ 3D length × the kit's colour-map size).
2. **Downsize:** `downsize_textures.py --apply` resized **307 textures** in 26 kits to the budget, under the same file names, so **no import script changes**.
   - Colour and emissive maps are box-filtered in linear light, so they don't darken.
   - ORM and mask maps keep every channel. Normal maps are decoded, averaged, renormalised and re-encoded.
   - **Budget:** hero armour, enemies, rocks → 2K. Weapons, gear, props, decals → 1K. UI and FX → unchanged.
   - **Large structures → 2K:** siege engines, gate, barricades, the ore shed and the 2 m ground tiles. At 1K a 10 m structure falls below 50 px/m. Owner, please confirm this category.
   - **Exception E1 ("keep the look"):** a 1K kit whose median texel density would fall below 256 px/m stays at **2K**: tga Feast, Fence, RealmCrack, RealmDressing, SiegeDebris.
   - **pbr_check:** 87 BaseColor/ORM pairs, compared with the originals in git HEAD.
     - **Downsizing broke one rule, in 6 TGA atlases:** averaged metal came out below 180 sRGB.
     - `fix_metal.py` snaps metallic back to 0/1 and lifts the metal texels' albedo to 180 sRGB. All 6, plus the TGA sign atlas, now pass.
     - The other failures were **already there in the originals** (other agents' maps; list below). I left them alone, because the look has to stay the same and their authors own them.
   - **Before / after:** `before_after_<owner>.png` show, per kit, the biggest colour map's centre at the same on-screen size, before | after.
     - The sheets for checkking, laptop2 and tga are posted to SCREENSHOTS.
     - At game distance they match. Only extreme close-ups lose the detail that the budget removes.
3. **Texel density:** see AUDIT.md "Texel density flags".
   - **Too dense:** weapons, gauntlets, flowers and potions, at 2–16k px/m before. The 1K cap fixes most of it with no UV change.
   - **Too thin:** large single-atlas structures (siege tower 35 px/m at 2K, ore shed, mine entrance, siege gate) and a few CampKit props.
     - Raising their density costs a rebake, not a "cheap UV fix". Their real fix is the shared trims (step 4): a re-UV onto `MI_Trim_WoodIron` raises them to 512 px/m with zero new texture memory.
     - Each needs a before/after that the owner approves first (#261 rule). Proposed order: siege tower, ore shed, mine entrance, siege gate.
4. **Trim sheets for the Master (#261):**
   - **TRIM_GUIDE.md:** strip layout for both 2K sheets (pixel rows, heights in cm at 512 px/m, UV V ranges, 8 px dilated gutters, mip-safe to 256), plus how to UV a prop onto it.
   - **trim_layout.json:** the same numbers for scripts.
   - **create_trim_material_ue.py:** `M_Trim` (UScale, Tint, TintAmount, Wetness), `MI_Trim_WoodIron` and `MI_Trim_StonePlaster`. The Master fills the licensed texture paths at the top and runs it; the script sets compression, wrap and the 2K maximum.

## Master steps

1. Pull. The resized sources are in the repo under the same names.
2. **Re-run each kit's import script**, which re-imports and replaces the textures. No graph or material changes are needed.
   - TGA: `assets/tga/<Kit>/import_*_ue.py`.
   - laptop2: `assets/laptop2/<Kit>/import_kit_ue.py`.
   - checkking: the weapons and Obsidian import scripts.
   - Or, faster: select every texture under `/Game/CastleDefender` → right-click → **Reimport**.
3. Optional: run #260's `set_texture_budget_ue.py` in dry run to confirm that nothing over budget is left.
4. #261: build the trims to `TRIM_GUIDE.md` on your PC, fill `create_trim_material_ue.py` and run it.

## Already failing pbr_check before this pass (left unchanged; for their authors)

These failures come from the original textures, not from downsizing:

- **Obsidian Sovereign:** near-black non-metal plus dark metal, by design (obsidian). It needs an owner ruling against the knowledge base.
- **checkking weapon kit:** metal below 150 sRGB on most heads; some maps have nearly flat roughness.
- **laptop2 CampKit, BarracksProps, FireBallista, SiegeGate, MineEntrance, shields:** metal too dark.
- **laptop2 FloraKit:** five plants with nearly flat roughness.
