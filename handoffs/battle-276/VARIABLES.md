# Variables for #276 (BP_BattleDirector)

| Name | Default | Meaning |
|---|---|---|
| LastWave | 0 | last wave seen |
| WasNight | False | last poll was night |
| Plan | 0 | tonight's plan: 0 feint, 1 pincer, 2 hold & rush |
| Holding | False | escorts are holding (hold & rush) |
| Go | False | scratch |
| BestDist | 0.0 | scratch |
| Spot | - | scratch: chosen breach spot |
| Candidates | - | scratch: unbroken breach spots |
| Escorts | - | escort zombies not yet released |
| Engines | - | tonight's siege engines |
| FlankOffset | 1500.0 | cm left / right of the director for flank A / B |
| ColossusFromWave | 4 | first day wave with a colossus |
| ColossusEvery | 3 | then every Nth day wave |
| ColossusHorde | 12 | zombies with each colossus |
| SiegeFromWave | 6 | first night wave with siege engines |
| TowerFromWave | 9 | towers from this night wave |
| FeintSize | 8 | zombies in the feint |
| FeintDelay | 20.0 | s between the feint and the real attack |
| EscortSize | 8 | escorts per engine (x1.5 when holding) |
| EscortMarch | 130.0 | escort walk speed while marching with an engine |
| EscortRun | 420.0 | escort speed when they charge |
| RushDist | 2500.0 | engine this close to its target -> charge |

```
BPVar(VarName="LastWave",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E000,VarType=(PinCategory="int"),FriendlyName="LastWave",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="WasNight",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E001,VarType=(PinCategory="bool"),FriendlyName="WasNight",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="Plan",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E002,VarType=(PinCategory="int"),FriendlyName="Plan",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Holding",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E003,VarType=(PinCategory="bool"),FriendlyName="Holding",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="Go",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E004,VarType=(PinCategory="bool"),FriendlyName="Go",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="BestDist",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E005,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BestDist",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="Spot",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E006,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'"),FriendlyName="Spot",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Candidates",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E007,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'",ContainerType=Array),FriendlyName="Candidates",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Escorts",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E008,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'",ContainerType=Array),FriendlyName="Escorts",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Engines",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E009,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'",ContainerType=Array),FriendlyName="Engines",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="FlankOffset",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E00A,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FlankOffset",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="1500.0")
BPVar(VarName="ColossusFromWave",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E00B,VarType=(PinCategory="int"),FriendlyName="ColossusFromWave",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="4")
BPVar(VarName="ColossusEvery",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E00C,VarType=(PinCategory="int"),FriendlyName="ColossusEvery",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="3")
BPVar(VarName="ColossusHorde",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E00D,VarType=(PinCategory="int"),FriendlyName="ColossusHorde",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="12")
BPVar(VarName="SiegeFromWave",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E00E,VarType=(PinCategory="int"),FriendlyName="SiegeFromWave",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="6")
BPVar(VarName="TowerFromWave",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E00F,VarType=(PinCategory="int"),FriendlyName="TowerFromWave",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="9")
BPVar(VarName="FeintSize",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E010,VarType=(PinCategory="int"),FriendlyName="FeintSize",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="8")
BPVar(VarName="FeintDelay",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E011,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FeintDelay",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="20.0")
BPVar(VarName="EscortSize",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E012,VarType=(PinCategory="int"),FriendlyName="EscortSize",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="8")
BPVar(VarName="EscortMarch",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E013,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="EscortMarch",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="130.0")
BPVar(VarName="EscortRun",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E014,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="EscortRun",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="420.0")
BPVar(VarName="RushDist",VarGuid=276E0A11B2C34D5E8F90A1B2C3D4E015,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="RushDist",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="2500.0")
```
