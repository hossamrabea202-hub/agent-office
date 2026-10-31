# #226 Weather v1: rain, fog and storms, rolled per day with a forecast

By `adjustedfilm (Claude)`, 2026-10-31.
- **Built on:** BP_DayNight as laptop2 handed it off (`handoffs/day-night`; the Master pasted it on 10-30) and BP_NoticeHUD
  `PushNotice(Text, Tier)` from the 10-30b export.
- **Pre-checked:** `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK** (240 nodes).
- **No existing Blueprint or material is changed:**
  - the hero gets one component and one camera blendable;
  - BP_DayNight is only driven through its own `FogDay` variable at runtime.

## What the player sees

- **One weather per day.** Day 1 is clear.
  - Every dawn a notice says **"Weather today: Rain"**.
  - Every dusk it gives the forecast: **"Forecast for tomorrow: Storm"**.
  - Odds: clear 50 %, rain 20 %, fog 15 %, storm 15 %.
  - Changes blend in over 20 s.
- **Rain:**
  - Rain streaks around the camera, in two depths (far and fine, near and bigger).
  - They are anchored to the world, so they don't swim when you turn.
  - They dim at night (MPC_DayNight.Night) and flash with lightning.
  - The rain loop's volume follows the rain.
  - The fog thickens ×2.5 and the picture turns overcast: cooler, flatter, a little darker.
- **Fog:** the height fog goes to ×6. The view shortens, so zombies appear much closer. A slight overcast grade.
- **Storm:**
  - heavy rain, plus the fog ×2.5;
  - the wind source rises from 0.1 to 1.0 strength, so cloth banners and capes whip;
  - the rain slants;
  - lightning every 6–18 s: a double flicker that lifts the shadows, then thunder 0.8–3 s later (close crack or distant
    roll).
- **Wetness:** `MPC_Weather.Wet` rises over 60 s of rain and dries over 120 s, ready for a wetness layer (see Decisions).

## How it works

- **`BPC_Weather`**, the hero component "Weather":
  - **BeginPlay:** finds BP_DayNight and remembers its FogDay. Spawns BP_RainCurtain (hidden), a WindDirectionalSource and
    the rain loop (volume 0.01). Rolls tomorrow's weather.
  - **WxTick (0.1 s):**
    - detects dawn and dusk from `IsNight`;
    - eases Rain, Fog and Storm toward today's targets;
    - writes `MPC_Weather` (Rain, Fog, Storm, Wind, Wet, Flash);
    - sets `BP_DayNight.FogDay = FogBase × (1 + 1.5 rain + 5 fog + 1.5 storm)`, so its own day/night fog code keeps
      working;
    - moves the curtain to the camera;
    - sets the wind and the rain volume;
    - schedules lightning and thunder.
- **`M_Rain`:** procedural streaks (Custom HLSL), unlit, translucent, two-sided. No textures.
- **`M_WeatherGrade`:** a post-process blendable after tonemapping, on the hero cameras. When all channels are 0 it
  returns the image untouched (early out).
- **Sounds:** synthesised, licence-free (`assets/adjustedfilm/Weather226/source/make_wx_sfx.py`): an 8 s seamless rain
  loop and two thunders.

## Files

| File | What |
|---|---|
| `setup_weather226_ue.py` | Editor script, safe to re-run, with `--dry-run`. Makes MPC_Weather, M_Rain + MI_Rain_Near, M_WeatherGrade, BP_RainCurtain, the 3 sounds and BPC_Weather, all in `/Game/CastleDefender/Environment/Weather`. Adds "Weather" to the hero and the grade to the hero cameras. |
| `VARIABLES_BPVar.txt` | 19 BPVar lines for BPC_Weather. Meanings are in `VARIABLES.md`. |
| `BPC_Weather_graph.txt` | BPC_Weather EventGraph |
| `gen_weather226.py` | generator (bpkit) |

## Steps (Master: paste only)

1. **Dry-run first:** `py "<repo>/handoffs/weather-226/setup_weather226_ue.py" --dry-run`. Read the Output Log.
2. **Run it for real:** `py "<repo>/handoffs/weather-226/setup_weather226_ue.py"`, then check `setup_weather226.txt`.
3. **Add the variables.** Open BPC_Weather → My Blueprint → paste the 19 lines of `VARIABLES_BPVar.txt` on the VARIABLES
   header, one at a time, then Compile.
4. **Paste the graph.** Paste `BPC_Weather_graph.txt` into BPC_Weather's EventGraph, then Compile and Save. Compile and
   Save the hero.

**Faster test:**
1. In BPC_Weather set `BlendSec` = 3 and `PClear` = `PRain` = `PFog` = 0, so every roll is a storm.
2. On the placed BP_DayNight set `StartHour` = 5.8: dawn comes within seconds, and the storm starts.
3. For rain or fog instead, set `PRain` (or `PFog`) to 1 and keep the others at 0.
4. Put the values back afterwards: `BlendSec` 20, `PClear` 0.5, `PRain` 0.7, `PFog` 0.85, `StartHour` 9.

## Checks (Play)

1. Day 1: clear. At dusk the forecast notice appears; at the next dawn the "Weather today" notice appears.
2. **Rain:** streaks around you, still when you turn; they hide behind walls (depth). Rain sound. The fog is thicker and the
   picture slightly overcast. At night the streaks are dim.
3. **Fog:** the view distance clearly shorter, by day and at night.
4. **Storm:** the above, plus banners and capes whipping. Lightning flickers about every 6–18 s, with thunder after it.
5. **Clear again:** everything fades back within about 20 s, and the picture is exactly as before (grade at 0).
6. Two minutes of Play: no "Accessed None" from BPC_Weather.

## Decisions

- **Wet stone and wood (Lagarde values) are only a channel for now:** `MPC_Weather.Wet` 0..1.
  - Applying it means adding a wetness layer to the castle master materials: darker albedo on porous surfaces, roughness
    toward 0.1, puddles in cavities.
  - That changes existing assets, so by the keep-the-look rule it needs the owner's before/after OK first.
  - I can build it as a separate card.
- **Rain doesn't put out torches yet.** The torch and fire-pit lights belong to BP_DayNight and the sword fire.
  - A follow-up: `BPC_Weather` dims `NightLight` actors when `CurRain` > 0.5.
  - Same for the fire-slime trails, once their class is in an export.
- **Crossbow spread in a storm:** `MPC_Weather.Wind` and the component's `CurStorm` are ready. Wiring them into the
  crossbow is a small BP_Crossbow manifest for after #214 / #216, which are already queued on BP_Crossbow.
- **The rain curtain goes through roofs:** rain shows in covered places like the gatehouse. A later pass can hide it under
  roofs with a height check or a depth fade.
- **The forecast is shown as a notice** at dusk and dawn, rather than a permanent HUD line. That needs no HUD paste.

## Office rules applied

- **Industry secrets rule 10 (one wind field):** a single wind source drives all cloth, and `MPC_Weather.Wind` is there
  for foliage materials.
- **Rule 7:** lightning lifts the shadows more than the highlights, as a real flash does.
- **Realism KB:** no lighting baked into anything. The overcast grade is a mild, physically motivated sky-light drop (×0.82).
- **Decals and live materials:** untouched.
