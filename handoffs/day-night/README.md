# Day / night system — BP_DayNight

From: hossam gmail laptop2 (Claude), 2026-10-30 (owner: "create day night system"). Blueprint-only, one new actor, nothing
existing rewired. It drives the sun, sky light and fog that are already in the level.

**What you get**
- A clock: `Hour` 0–24, a whole day in `DayLengthMin` real minutes (10 by default: 5 min day, 5 min night). Starts at 9:00.
- Sun rises 6:00, overhead 12:00, sets 18:00. Amber at the horizon, white at noon, 1–10 lux.
- Night: the same light swings round as the **moon**: cool blue, 0.6 lux. Sky light drops to 15 %. Fog thicker and blue.
- Banner: **NIGHT FALLS** / **DAWN** at the switch. `IsNight` (bool) and `Hour` are on the actor for anyone: waves, carts,
  the sword fire (`FireOn` or a low idle heat at night), torches.
- `MPC_DayNight.Night` (0..1) for materials: plug a *Collection Parameter* into any emissive (torches, windows, the
  realm) and it lights up by itself at dusk.

## Master steps (10 min)
1. Pull. `py "<repo>/handoffs/day-night/make_daynight_ue.py"` → `MPC_DayNight`.
2. New Blueprint, parent `Actor`, `/Game/CastleDefender/Environment/DayNight/BP_DayNight`. Variables from `VARIABLES.md`.
   Paste `BP_DayNight_graph.txt` (contains Event BeginPlay: delete the stub first). Refresh All Nodes, compile.
3. Place one `BP_DayNight` anywhere in the level.
4. **The Directional Light, Sky Light and Height Fog must be Mobility = Movable** (else the sun does not move at
   runtime). Sky Light: tick *Real Time Capture* so the sky colour follows the sun. The Directional Light should have
   *Atmosphere Sun Light* on (it already is if the sky works today).
5. Play. Watch 5 minutes, or set `StartHour` 17 to see dusk at once.

## Tuning (variables on the placed actor)
`DayLengthMin` 10 · `StartHour` 9 · `SunYaw` 35 (which way the sun comes from) · `MoonLux` 0.6 · `FogDay` 0.02 ·
`FogNightExtra` 0.03. Noon lux / colours are constants in the Clock chain if you want them different.

## Hooks for later (one line each)
- Waves: in `BP_ZombieWaveManager`, read `BP_DayNight.IsNight` → bigger / faster waves at night.
- Ore carts (#201): night carts carry rarer metals, zombies raid more.
- Sword fire: at night keep `FireHeat` at 0.25 idle so the blade is a torch.
- Street torches: emissive × `MPC_DayNight.Night`.
