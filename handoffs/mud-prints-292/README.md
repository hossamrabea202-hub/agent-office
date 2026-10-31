# #292 Muddy footprints: wet mud puddles leave muddy boot prints for a few steps

By `adjustedfilm (Claude)`, 2026-10-31. Owner (W:): *"when we walk on muddy wet padds we create muddy wetty foot prins for a few steps."*
- **Pre-checked:** `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK** (80 nodes, 91 links).
- **Nothing existing is changed** except one new hero component. All materials and decals are new assets, so the
  no-live-material rule holds.

## What the player sees

- **Mud puddles** (`BP_MudPad`, a 3 m decal): uneven wet mud with a dark, glossy water centre. Being a decal, it lies on
  any ground (landscape, cobbles) without a hard edge.
- **Walk through one:** boot prints appear behind the hero, alternating left and right, about every 80 cm, facing the
  walk direction.
  - Inside the puddle they are full strength.
  - After leaving it come **6 more prints**, each fainter and less glossy than the last (the mud wears off and dries).
  - Each print stays 8 s, then fades out over 6 s.
  - No prints while jumping.

## How it works

- **`BPC_MudPrints`**, the hero component "MudPrints":
  - **BeginPlay:** collects the `MudPad` actors.
  - **Every 0.05 s:**
    1. checks whether the hero stands within a pad (140 cm × the pad's scale);
    2. after each stride while mud is left, spawns one `MI_MudPrint` decal at the feet;
    3. sets the print's Strength (prints left / 6) and its Side (left or right).
- **Materials:** procedural Custom HLSL, no textures.
  - `M_MudPrint`: sole + heel + cleats + a darker squeezed rim.
  - `M_MudPuddle`: a noisy outline with a water centre.

## Files

| File | What |
|---|---|
| `setup_mud292_ue.py` | Editor script, safe to re-run, with `--dry-run`. Makes M_MudPuddle, M_MudPrint, MI_MudPrint, BP_MudPad and BPC_MudPrints in `/Game/CastleDefender/Environment/Mud`. Adds "MudPrints" to the hero. Places 3 test puddles 4 / 8 / 12 m in front of the PlayerStart, only if the level has none (`--no-place` skips this). |
| `VARIABLES_BPVar.txt` | 10 BPVar lines for BPC_MudPrints (`VARIABLES.md`) |
| `BPC_MudPrints_graph.txt` | EventGraph |
| `gen_mud292.py` | generator (bpkit) |

## Steps (Master: paste only)

1. **Dry-run first:** `py "<repo>/handoffs/mud-prints-292/setup_mud292_ue.py" --dry-run`. Read the Output Log.
2. **Run it for real** (without `--dry-run`), then check `setup_mud292.txt`.
3. **Add the variables.** Open BPC_MudPrints → My Blueprint → paste the 10 lines of `VARIABLES_BPVar.txt` on the
   VARIABLES header, one at a time, then Compile.
4. **Paste the graph.** Paste `BPC_MudPrints_graph.txt` into its EventGraph, then Compile and Save. Compile and Save the
   hero.

## Checks (Play)

1. Walk across the 3 test puddles. Prints show inside each, then 6 fading prints after it, left / right alternating.
2. **One-moment fix (Master may do it on the spot):** if the prints point sideways, open `MI_MudPrint` and set
   **Swap = 1**. The decal's UV axes depend on the projection, and this param turns the print 90°.
3. **Prints float or don't reach the ground:** set `FootDrop` on the hero's MudPrints component to the capsule half
   height. The default is 92; the decal reaches 12 cm either side of it.
4. Jumping over a puddle: no prints in the air.
5. Two minutes of Play: no "Accessed None" from BPC_MudPrints.
6. **Placing more:** drag `BP_MudPad` wherever the ground is muddy (gate road, stables, outside the walls) and scale it
   (uniform). Detection follows the scale.

## Decisions

- **Puddles are placed actors**, not detected from the landscape's physical material. The level has no mud physical
  material yet, and changing the landscape material would break the keep-the-look rule. A later step:
  `BPC_Weather`'s `Wet` (#226) could make pads appear or grow after rain.
- **Prints use a fixed 80 cm stride, not the animation's foot plants.** Syncing them to the anim notifies needs the hero
  AnimBP export. They read as footprints from the camera distance.
- **Hero only in v1.** Soldiers and zombies would add many decals per second in battle. They can take the same
  component later with a lower print count.
- **No squelch sound yet.** It can come with the footstep pass.

## Office rules applied

- **Realism KB:**
  - wet mud albedo 0.03–0.07 linear (wet soils darken by about 2×);
  - roughness 0.03 on standing water, 0.16 on fresh wet prints, drying to about 0.5;
  - no baked lighting.
- **Industry secrets:**
  - rule 1 (calibrated values, not "game" colours);
  - rule 3 (wear by physics: prints fade and dry the farther you walk from the mud).
- **The Master only pastes:** a setup script with a dry-run, BPVar lines, a clean graph, steps and tests.
