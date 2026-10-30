# Variables on BP_DayNight

| Name | Type | Default | Meaning |
|---|---|---|---|
| Hour | float | 9.0 | time of day 0..24 (runtime) |
| StartHour | float | 9.0 | hour at Play |
| DayLengthMin | float | 10.0 | real minutes per full day |
| SunYaw | float | 35.0 | compass direction of the sun's path |
| MoonLux | float | 0.6 | moon strength at midnight |
| FogDay | float | 0.02 | fog density by day |
| FogNightExtra | float | 0.03 | extra fog density at night |
| IsNight | bool | false | true from sunset to sunrise |
| Sun | Directional Light (object ref) | – | found at BeginPlay |
| Sky | Sky Light (object ref) | – | found at BeginPlay |
| Fog | Exponential Height Fog (object ref) | – | found at BeginPlay |

Tick *Instance Editable* on the first seven so they can be changed on the placed actor.

```
BPVar(VarName="Hour",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D01,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="Hour",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="9.0")
BPVar(VarName="StartHour",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D02,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="StartHour",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="9.0")
BPVar(VarName="DayLengthMin",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D03,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="DayLengthMin",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="10.0")
BPVar(VarName="SunYaw",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D04,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="SunYaw",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="35.0")
BPVar(VarName="MoonLux",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D05,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="MoonLux",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.6")
BPVar(VarName="FogDay",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D06,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FogDay",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.02")
BPVar(VarName="FogNightExtra",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D07,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FogNightExtra",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.03")
BPVar(VarName="IsNight",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D08,VarType=(PinCategory="bool"),FriendlyName="IsNight",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="Sun",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D09,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.DirectionalLight'"),FriendlyName="Sun",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Sky",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D0A,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.SkyLight'"),FriendlyName="Sky",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Fog",VarGuid=6D1E0C4A5B8D4E1F9A2B3C4D5E6F7D0B,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.ExponentialHeightFog'"),FriendlyName="Fog",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
```
