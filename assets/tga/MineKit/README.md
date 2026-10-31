# #309 Underground mine dungeon kit (for #297, the cave door destination)

From TGA (Claude), 2026-10-31. This is original procedural work; the sources are in `tools/tga/mine/`. There are no licensed textures.

## Meshes (`fbx/`, Z up, 1 unit = 1 cm in UE)

| Mesh | Tris | Notes |
|---|---|---|
| `SM_Mine_Tunnel_Straight` / `_Turn` / `_T` / `_DeadEnd` / `_Slope15` | 9-12k | **Watertight carved rock**: a rock block minus a swept tunnel void, using an exact boolean. 0 open edges. 3 m wide × 2.8 m high, floor at z = 0. |
| `SM_Mine_Chamber` | 32k | 11 × 10 m hall, 5 m high, with tunnel openings at both ends (x = 0 and x = 14 m). |
| `SM_Mine_TimberSet` | 180 | Two oak props, a cap beam, wedges, iron spikes and a band. Fits the tunnel; place one every 2-3 m. |
| `SM_Mine_Rail_4m` | 120 | Two rails and 6 oak sleepers, gauge 60 cm. Snaps on the 4 m grid. |
| `SM_Mine_Cart` | 868 | Oak tub with iron bands, wheels and an ore load (ore material). 1.2 × 0.8 m. |
| `SM_Mine_OreVein` | 12k | Ore face, 3.2 × 2.6 m, faces +X. Push it into a chamber wall. It has metallic chalcopyrite veins (#201). |
| `SM_Mine_SpoilHeap` | 1.9k | Ø 4.4 m. |
| `SM_Mine_Lantern` | 108 | Hook, iron frame and glowing glass (`MI_MineGlow`), with a socket **`Light`**: attach a PointLight there (KB rule 6). |
| `SM_Mine_Door` + `SM_Mine_DoorFrame` | 1.3k + 84 | Oak planks, 3 iron straps, studs and a ring pull. 1.2 × 2.2 m, faces **+X**, pivot at the bottom centre, as asked for BP_CaveDoor (#297). |

**Grid:**
- **Modules:** each tunnel module covers x 0..4 m and y −2..2 m, with tunnels on the cell centre lines.
- **Joins:** the rock displacement fades to zero at every module face, so neighbours join seamlessly when snapped by 400 cm with yaw in 90° steps.
- **Branches:** in UE the Turn's and T's branch leaves towards **−Y**, because the FBX mirrors Blender +Y. Rotate the piece by 180° for +Y.
- **Slope:** `_Slope15` rises 107 cm over 4 m.

## Materials and textures (all pass pbr_check)

| Set | Size | Notes |
|---|---|---|
| `T_MineRock` | 2K, tiles every 2 m | Hewn dark rock: KB dark rock albedo, pick strokes, ochre iron staining. Baked from a seamless high-res height patch. |
| `T_MineOak` | 1K | Old oak: grain along U, splits, grey weathering. |
| `T_MineIron` | 1K | Wrought iron with rust patches: metal 1, and metal 0 where rusted. |
| `T_MineOre` | 1K | Rock with brassy metallic veins that glint under lantern light. |

**M_MineSurface** parameters: `Tiling`, `Tint` and `Wetness`.
- **Damp:** the carved rock's **vertex colour R = wetness**. It is strongest in a band along the floor and in **drip streaks running down by gravity**, and it darkens the colour (×0.55) and makes it glossy (roughness 0.15).
- **Props:** have Wetness 0.

**Collision:** the tunnels and chamber use complex-as-simple, so you walk the real rock. The props have 26-DOP hulls.

## Master / adjustedfilm steps

1. `py ".../assets/tga/MineKit/import_mine_ue.py"`. It runs `DRY_RUN = True` first (it lists the files). Then set `DRY_RUN = False`.
   - It imports into `/Game/CastleDefender/Environment/Mine`.
   - Material slots are matched by name.
2. **Build the dungeon sub-level** (adjustedfilm, #297). The preview layout (`renders/mine_layout.jpg`, from `tools/tga/mine/lookdev_mine.py`) is:
   - **Rock pieces:**
     - chamber at (0, 0, 0)
     - Straight at x = 1400 cm
     - T at 1800
     - DeadEnd at 2200
     - Straight at −400
     - Turn at −400 with yaw 180
   - **Props:**
     - TimberSets every 2 m in the tunnels
     - Rails along y = 0 from x = −200
     - Cart at x = 850
     - OreVein against the south chamber wall
     - SpoilHeap at (1050, −320)
     - Door + DoorFrame at the tunnel end
   - **Lanterns:** each one gets a PointLight of about 300-500 lm, warm (1.0, 0.62, 0.3), with a small source radius.
3. **NavMesh:** a NavMeshBoundsVolume over the dungeon, so the stand-in workers can walk.

## Test list

1. **Seams:** snap a Straight to the Chamber and a T. There's no seam or gap at the joins.
2. **Wet rock:**
   - the floor and the lower walls are darker and glossier
   - streaks run down the walls
   - the ceiling is dry
3. **Lanterns:** they glow, and their light pools on the rock. The ore veins glint when the camera moves.
4. **Walking:** the hero walks the floor and up the slope, and doesn't snag on the timber props.

## Notes

- **Bake approach (industry standard for modular caves):** the big rock shape lives in the mesh (voxel-sculpted, then decimated), and the fine detail is a tiling set baked from a seamless high-res height patch. One 2K rock set covers every piece at a crisp density, where a per-piece bake would be blurry.
- **Workers:** stand-in soldier bodies with laptop2's miner gear (#247) belong to the #297 sub-level, not this kit.
