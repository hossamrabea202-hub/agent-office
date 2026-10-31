# #351 A real meadow outside the castle: grass, flowers and bushes

By `adjustedfilm (Claude)`, 2026-10-31. Owner: *"the ground outside the castle is made of grass scattered, but nature has
grass and flowers and bushes."*

**Why it looks like that now:** the project only has 2 wild-grass scans and 1 dead shrub among its plants. There are no
flowers and no living bushes. TGA is building a flora kit (#352): 4 wildflowers, 2 bushes and a fern.

## What the script does (`place_meadow_ue.py`)

It places ONE actor, `Meadow351`, made of instanced meshes. The scatter follows how real meadows grow (research:
`handoffs/knowledge/research_notes/environment_vegetation.md`):

| Plant | Where it grows |
|---|---|
| grass clumps | everywhere open, thick in lush patches and thin on trampled ground (large-scale noise) |
| flowers | each species in its own patches (seeds fall near the parent plant), only on gentle open ground |
| bushes | at edges (near rocks, walls, trees, buildings), rarely in the open |
| ferns | at edges, on the shady side |
| dead shrubs | dry, steeper slopes (20–35°) |
| nothing | slopes over 35°, anything that is not the landscape (rocks, buildings, mesh roads), inside the castle box |

**Performance:**
- Instances fade out with distance: grass 35–55 m, flowers 25–42 m, bushes 90–150 m.
- Only bushes and dead shrubs cast shadows.
- Nothing has collision.

Plants are found by name anywhere in the project. When TGA's kit is imported, a re-run picks it up automatically.

## Steps (Master)

1. `py "<repo>/handoffs/meadow-351/place_meadow_ue.py" --list`. This is read-only; push `meadow_list.txt`.
2. `py ".../place_meadow_ue.py" --dry-run`. Check the counts.
3. `py ".../place_meadow_ue.py"`. Then take a **before/after screenshot** from the castle wall looking out, and post it on
   #351 with `shot.js --card 351`.
4. Undo: `--remove`. It deletes Meadow351 and nothing else.
5. When TGA's #352 kit is imported, run step 3 again (it replaces Meadow351).

Options: `--radius 22000` (cm around the castle) and `--seed 351`.

## Tests

1. From the wall, the land outside shows lush and thin grass patches, flower patches, and bushes along rocks and walls.
2. No plants on rock faces, roofs or roads, or inside the castle.
3. FPS about the same as before. If not, run again with `--radius 15000`.

## Fix 2026-10-31 night: roads stay bare (Master's report on #351)

The gate road is a **decal** (`Env_WornGround_Decal`) on a landscape with no paint layers. The old script could not see
it, so grass grew on the road and the Master cleared it by hand. The script now builds a road mask first:

1. **Road decals.** A decal counts as a road when its label or material contains road / path / worn / trail / track / dirt.
   The test uses the decal's own rotated box, plus a 1.5 m verge.
2. **Road actors.** Any actor labelled `*Road*` or `*Path*` counts, for example **PortalRoad** and **HiddenRoad**.
   - With a spline, the mask follows the spline, 4.5 m to each side plus the verge.
   - Without a spline, it uses the actor's bounds.
3. **Bands.** The band the Master cleared by hand is built in: x −7000..300, y 1750 ± 450. Add more bands with
   `--band x0,x1,y,halfwidth`.

`--list` and `--dry-run` now print every road zone found and its size, and the dry run counts how many samples stayed
bare. **Re-run (Master):**
1. Run `--dry-run`. Check that the `road zones` list names `Env_WornGround_Decal`, PortalRoad and HiddenRoad.
2. Run the script for real. It replaces Meadow351.

Options: `--road-pad 150` (the verge, in cm).
Not run in the editor yet. The dry-run list is the check.
