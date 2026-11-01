# #390 WinterKeep: snow trails (BPC_SnowTrails)

By `adjustedfilm (Claude)`, 2026-11-01. Design: [RESEARCH.md §4](../RESEARCH.md). Feet press real-looking tracks into
the snow around the player. Tracks fill back in over about 3 minutes, faster in a blizzard.

**How it works**
- `RT_WK_TrailA` (2048², R16F) holds snow height for a 64 m window around the player (3.1 cm per texel).
  1 means untouched snow; 0 means pressed 12 cm deep.
- Every 0.05 s, `BPC_SnowTrails` does this:
  1. It rolls the window with the player, snapped to 25 cm, so the copy stays texel-exact.
  2. It finds the planted feet of up to 8 characters within 30 m, 16 stamps at most. A foot counts as planted when the
     `foot_l` / `foot_r` bone is less than 14 cm above the mesh origin. Each stamp is an ellipse, 30 × 13 cm, along the
     character's facing.
  3. It draws `M_WK_TrailUpdate` into B (shift, refill, stamps), then copies B back into A.
- `M_WK_Landscape` reads A and does three things:
  - its own 16-step POM, which skips flat untouched snow;
  - packed-snow albedo 0.66 and roughness 0.50 in the track;
  - a normal from the height gradient, plus a little AO in the bottom.
- Trails only appear on snow layers: fresh 1.0, packed 0.5, forest floor 0.6. Rock, ice, road and melt get none.
- There's **no WPO, no tessellation, no PDO** (PDO tanks VSM; INDUSTRY_SECRETS §4.4).

**Decisions**
- The trails live on a level actor (`BP_WK_Snow` with the `SnowTrails` component), not on the hero. ThirdPersonMap and
  the hero Blueprint are not touched.
- There are no footprint decals in v1; tracks come from the RT only. Bone names are variables (`FootL` / `FootR`). If a
  skeleton has no such bone, it stamps at the mesh origin, which makes a body-width track.

## Steps (Master)

`S = <repo>/handoffs/winter-map/ue/winterkeep_ue.py`

1. `git pull`. Then `py S --dry-run`. Every line must say `OK`, including the 6 new `trails:` lines.
2. `py S --step assets`. This rebuilds `M_WK_Landscape` **in place**, so the landscape keeps it. It also makes:
   - `/Game/CastleDefender/WinterKeep/MPC_WK_Snow`
   - `Trails/RT_WK_TrailA`, `RT_WK_TrailB`
   - `Trails/M_WK_TrailUpdate`, `M_WK_TrailCopy`

   Open `M_WK_Landscape` once and check that it compiles with no errors. There are 3 Custom nodes; their names start
   with "trail".
3. Open WinterKeep. Run `py S --step trails --dry-run`, then `py S --step trails`. This creates
   `WinterKeep/Blueprints/BPC_SnowTrails` and `BP_WK_Snow` (with the SnowTrails component), and places `WK_Snow`.
4. Open **BPC_SnowTrails**:
   - Paste the 6 lines of `trails/VARIABLES_BPVar.txt` one at a time on the VARIABLES header, then **Compile**.
   - In the EventGraph, select all and delete, then paste `trails/BPC_SnowTrails_graph.txt` (118 nodes).
   - **Compile** and **Save**.
5. Play in WinterKeep and walk on fresh snow.

## Tests

1. **Walk 10 m on fresh snow.** A line of single footprints stays behind you, about 12 cm deep, with lit and shaded
   walls. The bottoms are a bit greyer (0.66 packed) and smoother.
2. **Run 40 m away and come back.** Prints beyond 32 m vanish at the window edge with a soft fade, not a hard line.
   Prints still inside the window stay in the same world place. They don't slide while you move.
3. **Wait 3 minutes.** The prints fill back in. With `--step light --preset blizzard` (SnowFall 1.0) this takes about
   45 s.
4. **Zombies or soldiers within 30 m** leave prints too, up to 8 characters.
5. **Rock, ice, the road and the bridge** show no prints.
6. **No stretch or smear when you stand still.** If you see a smear, the shift isn't texel-exact; report it.
7. **Performance (`stat unit`):** GPU cost under 0.3 ms. The two RT draws are about 0.05 ms each.

**If no prints appear:**
- The hero's foot bones may not be `foot_l` / `foot_r`. Set `FootL` / `FootR` on `WK_Snow` > SnowTrails to the
  skeleton's names.
- Or the bones may sit higher than 14 cm. Raise `PlantZ` to 20.

Push `ue/wk390_log.txt` and a screenshot when done.

## Files

| File | What |
|---|---|
| `gen_snowtrails.py` | generator (bpkit); `"<blender python>" -I gen_snowtrails.py`, then `tools/applyall/fix_impure.py` |
| `BPC_SnowTrails_graph.txt` | EventGraph paste (checked: `applyall check`, Validation OK) |
| `VARIABLES_BPVar.txt` | 6 variables: Chars, Origin, Slot, FootL, FootR, PlantZ |
| `../ue/winterkeep_ue.py` | `--step assets` (MPC, RTs, draw materials, POM branch), `--step trails` (BPs + placement) |
