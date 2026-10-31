# #277 Crossbow flares: a barracks upgrade, flares only at spotted threats at night

By `adjustedfilm (Claude)`, 2026-10-31, from the owner's idea in chat.
- **Built on** `handoffs/exports/master/2026-10-30b`:
  - BP_ZombieHUD `Gold` (the same path as TGA's farmer hire);
  - BP_NoticeHUD `PushNotice`;
  - BP_CastleSave `Data`, saved like the weapon kit;
  - BP_SoldierXbow, BP_Zombie and BP_NPC_Barracks;
  - BP_DayNight `IsNight` and #138's BP_ZombieWallBreaker.
- **Pre-checked:** `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK** on both graphs:
  - `BP_Flare`: 81 nodes;
  - `BPC_Flares`: 154 nodes.
- **No existing Blueprint is changed.**

## What the player sees

1. **Buying it.** At the barracks NPC a notice says *"[F] Crossbow flares: 400 gold. At night your crossbowmen light up
   the threats they spot."*
   - Press **F** to buy it, once. It is saved.
   - With too little gold: *"Not enough gold: crossbow flares cost 400."*
2. **At night,** about once a second a random crossbowman looks out for threats.
   - **What counts:** the best zombie between 14 m (he can see that close anyway) and 60 m. The nearest counts first,
     and a colossus counts 40 m nearer.
   - **When he fires:** only if no flare already burns over that spot. **No threat, no flare.** At most one flare
     every 6 s and 3 burning at once, so the sky is never full of them.
3. **The flare:**
   - It launches with a thunk and a whoosh, arcs up and ignites 22 m over the threat with a pop.
   - Then it hangs, drifting down at 0.55 m/s and swaying gently, with a magnesium hiss.
   - **The light:** 4500 K, 3500 cd, reaching 60 m. It flickers like burning magnesium and casts moving shadows. It
     glows in fog and rain (volumetric scattering).
   - It burns 26 s and fades over the last 2.5 s.
   - The player sees what is coming in the dark (a horde, a colossus, the pushers of a siege engine) and can defend.

## How it works

- **`BPC_Flares`**, the hero component "Flares":
  - **BeginPlay:** finds BP_DayNight and loads `CastleSaveFlares`.
  - **`FlareKeys`** (0.05 s): edge-detects F, so a tap isn't missed. Pays from `BP_ZombieHUD.Gold`, saves, and shows a
    notice.
  - **`FlarePoll`** (1 s):
    - the barracks prompt, once per visit;
    - the spotting pass: one random crossbowman, one loop over the zombies, then one loop over the burning flares for
      the "already lit" check;
    - then it spawns BP_Flare at the crossbowman (+1.6 m) and gives it the target.
- **`BP_Flare`:**
  - **BeginPlay:** finds its light and plays the launch sound.
  - **Tick:**
    - flight: 1.4 s ease-out arc;
    - ignite: pop, plus an attached burn loop that stops when the flare is destroyed;
    - hang: descends with a sway; the light's intensity is ramp × flicker × fade;
    - burn-out: destroys itself.

## Files

| File | What |
|---|---|
| `setup_flares277_ue.py` | Editor script, safe to re-run, with `--dry-run`. Makes M_FlareCore, BP_Flare (Core sphere and FlareLight), the 3 sounds and BPC_Flares in `/Game/CastleDefender/Gameplay/Flares`, and adds "Flares" to the hero. |
| `VARIABLES_BPVar.txt` | 8 BPVar lines for BP_Flare and 15 for BPC_Flares. Defaults and meanings are in `VARIABLES.md`. |
| `BP_Flare_graph.txt`, `BPC_Flares_graph.txt` | the two EventGraphs |
| `gen_flares277.py` | generator (bpkit) |
| `assets/adjustedfilm/Flares277/` | `sfx/*.wav` and `source/make_flare_sfx.py` (synthesised, licence-free) |

## Steps (Master: paste only)

1. **Dry-run first:** `py "<repo>/handoffs/flares-277/setup_flares277_ue.py" --dry-run`.
2. **Run it for real:** `py "<repo>/handoffs/flares-277/setup_flares277_ue.py"`, then check `setup_flares277.txt`.
3. **Add the variables.** BP_Flare → My Blueprint → paste its 8 BPVar lines, one at a time, then Compile. Then
   BPC_Flares with its 15 lines, then Compile.
4. **Paste the graphs.** Paste `BP_Flare_graph.txt` into BP_Flare's EventGraph, then Compile and Save. Then paste
   `BPC_Flares_graph.txt` into BPC_Flares, then Compile and Save.
   - Paste BP_Flare **first**, because BPC_Flares spawns it.
5. **Compile and save the hero.**

**Faster test:** give yourself 400 gold. On the placed BP_DayNight set `StartHour` = 18.5 (night). Have 2–3 crossbowmen
and start a wave. Put `StartHour` back to 9.

## Checks (Play)

1. At the barracks: the notice appears once per visit. F with ≥ 400 gold takes 400 gold and shows the confirmation. F
   again does nothing (already owned). With < 400 gold: the "not enough gold" notice.
2. **By day:** no flares.
3. **At night with zombies 14–60 m from a crossbowman:**
   - a flare launches from him with a thunk, arcs, pops 22 m over the zombies, and lights the area for about 26 s while
     drifting and swaying;
   - its shadows move;
   - a second flare comes only for a different, unlit group;
   - never more than 3 at once, and at least 6 s apart.
4. **At night with no zombies around:** no flares.
5. A colossus wall-breaker gets the flare before a closer ordinary zombie (unless that one is about 40 m nearer).
6. Save, then load: the upgrade is still owned.
7. Two minutes of night Play: no "Accessed None" from BP_Flare or BPC_Flares, and fps holds with 3 flares burning (each
   is one shadow-casting point light).

## Decisions

- **The purchase happens at the barracks NPC with F**, not on a new card in the barracks menu. Adding a card means
  re-pasting the big BP_BarracksHUD; this needs no HUD change.
- **Night only.** By day the threats are visible. Fog days could use flares too later, through `BPC_Weather.CurFog`.
- **Rain doesn't shorten the flare in v1.** That keeps this card independent of #226 being pasted. Later, `Life` can be
  scaled by `MPC_Weather.Rain`.
- **No muzzle animation on the crossbowman.** The flare leaves from his position, 1.6 m up. A firing montage can be
  added once the crossbow anim set is in an export.
- **The upgrade lives in its own save slot** (`CastleSaveFlares`), like the weapon kit (`CastleSaveWeapons`). A new game
  keeps it unless the game clears these slots, exactly as for the weapons.
- **A smoke trail** needs a Niagara system. Left for a follow-up, because there is no Niagara authoring from Python in 5.3.

## Office rules applied

- **Industry secrets rule 6 / Kelvin table:** magnesium flare light at 4500 K, with a flicker of 23 Hz + 61 Hz on a slow
  drift.
- **Rule 7:** real moving shadows and volumetric glow, not a flat light.
- **Rule 10:** one light source per flare; nothing faked in the HUD.
- **Decals and live materials:** untouched. Only new assets are added.
