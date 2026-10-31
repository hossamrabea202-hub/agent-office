# BPC_Weather variables (BPVar lines in VARIABLES_BPVar.txt)

| Name | Default | Meaning |
|---|---|---|
| DN | - | BP_DayNight in the level (found at BeginPlay) |
| FogBase | 0.02 | BP_DayNight's FogDay at Play (the weather multiplies it) |
| Curtain | - | the rain curtain |
| Wind | - | the storm wind source |
| RainAudio | - | rain loop |
| Today | 0 | 0 clear, 1 rain, 2 fog, 3 storm (day 1 is clear) |
| Tomorrow | 0 | the forecast |
| WasNight | false | IsNight last tick (dawn / dusk edge) |
| CurRain | 0.0 | current rain 0..1 |
| CurFog | 0.0 | current fog 0..1 |
| CurStorm | 0.0 | current storm 0..1 |
| Wet | 0.0 | surface wetness 0..1 (MPC_Weather.Wet) |
| BlendSec | 20.0 | seconds for the weather to change |
| PClear | 0.5 | roll below this = clear |
| PRain | 0.7 | below this = rain (20 %) |
| PFog | 0.85 | below this = fog (15 %), else storm |
| NextBolt | 0.0 | game time of the next lightning |
| FlashT0 | -100.0 | game time of the last bolt |
| ThunderAt | 0.0 | game time the thunder plays (0 = none) |
