# #504 Castle weathering: dirt, rain streaks, cracks, lichen (i5 checkking, 2026-11-04)

Owner (Alien): *"i also love how the castle looks like but sadly it looks very clean, castles usually have dirt,
weathering, and cracks and stuff"*. Follow the real-world references in the knowledge base.

## What it adds (every layer has a physical cause: KB README rule 3, INDUSTRY_SECRETS 0.3 / 4.5)
| Layer | Where (found by line traces on the real stone) | Why |
|---|---|---|
| Rain run-off streaks | under every overhang: caps, cornices, string courses, merlon caps (`LEDGE`) | water drips off the edge, carries dirt + biofilm down (gravity) |
| Sill streaks (+ a little algae) | below the bottom of every opening in a face: arrow slits, windows (`SILL`) | water collects on the sill and runs out over it |
| Faint wash | plain top edges with no overhang (`TOP`) | rain washes over the top |
| Cracks | from sill corners (stress) + a few on big faces (frost / settlement), each with a damp halo and a stain trail below | stress concentrates at openings; water leaves the crack |
| Lichen (grey-green, rare Xanthoria yellow) | up-facing caps and tops | damp, light, bird perches |
| Lichen + dark algae film | faces turned away from the sun, low and high zones | they stay damp longest |

**Not added:** a base dirt band. Family C already has one in its material, so no doubling (PERFECT_CASTLE #7).
**Restraint:** about 2,100 cards on 334 stone pieces (i5 copy). Thinned by hand after the first pass read as a regular fringe.

## How (no live material, MI or decal is touched)
- 3 NEW procedural unlit **Modulate** card materials + 6 MIs in `/Game/CastleDefender/Environment/CastleWeather504/`
  (the #425 method: it works on the walls that have Receives Decals off, and needs no textures, so there's no pbr_check input;
  colours come from INDUSTRY_SECRETS 1.1).
- Drawn as **InstancedStaticMesh** cards, one actor per MI (**6 actors, ~6 draw calls for the whole castle**). Per-instance
  custom data 0 = random seed, so no two cards look alike. Cards sit 0.6 cm in front of the most protruding stone in their
  footprint. No collision, no shadow.
- Everything is tagged `CW504`, in the outliner folder `CastleWeather504`. Undo = `--remove`.

## Steps for i9 (Master), in the live session, Play stopped
```
py "<repo>/handoffs/castle-weather-504/build_weather504_ue.py"                 # creates + saves the 3 materials, 6 MIs
py "<repo>/handoffs/castle-weather-504/place_weather504_ue.py"                 # DRY RUN -> place_report504.txt (counts per layer)
py "<repo>/handoffs/castle-weather-504/place_weather504_ue.py" --preview <x> <y> <z> <shot dir>   # temp cards near x,y,z + before shot
py "<repo>/handoffs/castle-weather-504/shot_after504_ue.py" <shot dir>         # after shot (separate run), removes the preview
#   ---- owner's OK on the before/after ----
py "<repo>/handoffs/castle-weather-504/place_weather504_ue.py" --apply         # all cards; then Save the level
py "<repo>/handoffs/castle-weather-504/place_weather504_ue.py" --remove        # undo (deletes only CW504 actors)
```
- **Tuning is live, with no recompile:** MI scalar `MaxOpacity` / `Strength` per layer. Start: Ledge 0.68, Sill 0.7, Top 0.5,
  Crack 0.9, Lichen 0.7 / 0.6. `WallAlbedo` 0.32 = the stone the stains are calibrated against. Raise it for darker stone.
- Placer knobs at the top of `plan()`: the probabilities per layer, `COL` (column spacing 110 cm), `STEP_Z` (10 cm).

## Test list
- [ ] Build: 3 materials compile (no "Failed to compile" for `*Card504` in the log), 6 MIs saved.
- [ ] Dry run: about 2,000-2,700 cards; no layer above ~800. If `SILL` explodes, a mesh has noisy collision: check its row in the report.
- [ ] Preview at a merlon run + the gate: streaks hang only under drip edges; no card edge or square shows; no stain on the sky side.
- [ ] Play: nothing blocks the hero (no collision), `stat unit` GPU/Draw change < 0.3 ms (6 ISM draws, unlit).
- [ ] After `--apply`: save the level, rejoin check on i5 (cards persist).

## Status / what was tested (i5, 2026-11-04 22:50-23:08)
- **The Multi-User server on i9 was not answering** (the editor sat at "Looking for Server" from 22:43; the :8765 chat was
  down too), so **nothing went into the live session**. Tested offline on i5 with an unsaved temp folder (`/Game/_i5tmpCW504`)
  and nothing saved:
  - mock wall in the real kit491 stone MI (Entry map): shaders compile and render; streaks hang under the string course, cap
    and merlon caps; the crack reads as a hairline with a branch (`shots/ld504_*`);
  - i5's own copy of ThirdPersonMap (without i9's rebuild): 334 stone pieces probed, 2,162 cards placed in ~6 s, then removed
    (`shots/cw504_*`, `shots/cw504_before_after.png`). That map loads at night, so a temporary lookdev daylight was used.
- Known: on i5 some existing cards show the "Preview" shader placeholder (i5's DDC), which isn't from #504. Judge on i9.
- Lesson: materials created with `unreal.new_object` in the transient package do NOT compile (even a 1-node test). Use a
  real (unsaved) package for lookdev.

Rules applied: INDUSTRY_SECRETS 0 rules 1 (locked exposure EV 1.5 for every shot), 3 (physical cause per layer), 4 (whitewash: not
applied, because the owner loves the current stone; the cards are the 4.5 weathering cues), 10 (one shared pass, one material family).
