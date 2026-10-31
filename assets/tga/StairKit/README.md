# #279 AAA stair kit: one watertight hero mesh per flight, high poly baked to low poly

From TGA (Claude), 2026-10-31, on the owner's order (priority 3). This is original procedural work; the sources are in `tools/tga/stairs/`.

## What's in it

| | |
|---|---|
| **Flights** | 120 meshes: `SM_Stair_W{120,200,300,400}_{Solid,Soffit}_N{02..16}` (`fbx/`). Each is **one watertight mesh**, checked in Blender: every edge is manifold. The steps, both side walls, the base or soffit and the back are one closed element, **≤ 646 tris** (owner limit 1k). |
| **High → low** | 4 sculpted high-poly step modules, about 45k tris each, 2 m wide (rise 18 cm, going 30 cm). They are baked once to a **2K strip atlas** with Cycles selected-to-active: Normal (DirectX), AO, and height from the high-poly position. Curvature comes from the height. |
| **Variants** | 0 light wear; 1 two blocks with a mortar joint; 2 heavy wear (always the **bottom step**), damp and moss at the foot; 3 joint + crack + moss. Each flight picks a variant per step, so neighbouring steps differ. |
| **Wear** | Every edge is bevelled. Noses and corners are chipped. Treads are **dished** in the middle (deepest on the worn variants). Noses are rounded off where people step. |
| **Material** | Castle sandstone, with grime in cavities and joints, at the riser feet and under the next riser. Edges are worn lighter. Tread centres are **polished smoother** (roughness drops by about 0.38). Damp and moss sit at the feet. `T_StairKit_BC/ORM/N`, 2K. `_Curv` and `_H` are kept for reference. |
| **Slot 1** | Sides, soffit and back use the castle wall material `MI_Castle_StoneWall_World` with metre-planar UVs, so wall-hugging flights read as part of the wall. The MI is used, never edited. |
| **UVs** | UV0 for textures, UV1 for the lightmap (authored). The texel density is about 1,000 px/m (10 px/cm) on every step. |
| **Collision** | `UCX_` convex ramp per flight: pawns glide up, while traces still hit the real steps. |

**The trick (trim-module bake):** every flight's riser, nose and tread strips point at the same baked strips. So 120 flights cost **one** 2K texture set and **one** MI, and each stays a single mesh. Wider flights tile the 2 m strip, so a 4 m flight shows two stones per step with a joint; narrower flights crop it, so nothing is stretched.

## Master steps

1. **Import:** `py ".../assets/tga/StairKit/import_stairkit_ue.py"`. It imports into `/Game/CastleDefender/Props/StairKit`: 120 SM, 3 textures, `M_StairKit` and `MI_StairKit` (Tint, TintAmount, Wetness), and sets slot 1 to the wall MI.
2. **Place:** run `py ".../assets/tga/StairKit/place_stairkit_ue.py"` with the game level open. It runs with `DRY_RUN = True` first:
   - It finds the `SM_StairTread_*` actors itself and chains them into flights.
   - It prints each flight's steps, rise, going, width and the kit piece and scale it picks.
   - It writes `Saved/stair279_report.json`. **Post that file on #279.**

   Then set `DRY_RUN = False` and run it again:
   - The old treads, and the `Cube_*` / `SM_StoneModule_*` blocks under them, go to the folder `Stairs_Old_279`, hidden with their collision off (tag `Stair279_Old`). `StairRamp_*` nav ramps stay.
   - The kit flights are placed as `Stair279_NN` in the folder `Stairs_279`.
   - Save the level.
3. **Undo:** set `UNDO = True` (and `DRY_RUN = False`) and run it. It deletes the new flights and restores the old actors.
4. **Rebuild the NavMesh** (Build Paths) and save.

**Decision (TGA):**
- `Solid` flights by default: masonry down to the ground, the classic castle stair. Set `STYLE = 'Soffit'` for flights that should float with a sloped underside.
- Kit widths are 1.2, 2, 3 and 4 m. The placement script scales to the measured width, rise and going, normally within ±20%.
- Flights over 16 steps are split into pieces.

## v2 (after the #301 revert)

The owner found three problems: half-height flights, wall and tower stairs gone, and flights poking through walls. The v2 fixes, checked offline against the Master's read-only dump (`handoffs/exports/master/stair279_dump.json`):

- **Orientation is read, not assumed.** v1 assumed the FBX mirrors Blender +Y to UE −Y; the flights climbed backwards. v2 reads each imported kit mesh's bounds to see which way it climbs and widens.
- **Every flight is verified before it's placed.** The script transforms the mesh's own step centres through the real rotation and scale and checks them against the old treads. Any flight that is more than 8 cm off is **skipped** and keeps its old actors.
- **No split pieces.** The castle's flights are 13, 20 and 31 steps, all about 2 m wide. The kit now has `SM_Stair_W200_*_N17..N32` (152 flights, max 770 tris, all watertight), so each flight is one piece. v1 stacked a floating upper piece over hidden blocks.
- **Hiding is exact.** Only the flight's treads are hidden, plus blocks lying *fully* inside its own volume. On the real dump that's 9 flights: 188 treads + 190 riser blocks = 378 actors, and none wider than its stair (v1 hid 546). The report lists every hidden actor under its flight.

**Re-run steps:**
1. `import_stairkit_ue.py`. It picks up the 32 new FBX.
2. `place_stairkit_ue.py` with **DRY_RUN = True**. Post `Saved/stair279_report.json`.
3. When the owner is happy, set DRY_RUN = False.

## Test list

1. **The dry run** finds every flight, and each flight's step count matches what you see.
2. **After placing,** each kit flight sits exactly on the old stair:
   - its top tread is level with the wall walk or landing
   - there are no gaps at the bottom
   - it climbs the right way
3. **Walking:** the hero and soldiers walk up and down smoothly, and the NavMesh still crosses the stairs.
4. **Close-up:**
   - rounded, chipped noses
   - darker joints and riser feet
   - smoother, slightly glossy tread centres
   - moss only at the bottom steps
5. **Undo** restores the old box stairs exactly.

## Notes

- **Export request:** the stair export (#300) is no longer needed to place the kit, because the script measures the stairs itself. The report JSON lets me check the fit; if a chain is skipped as bent, its line says so.
- **Spiral stairs:** if some stairs are spirals (the tower-9 stairs are separate meshes and are not touched), tell me. A spiral kit would be a follow-up.
