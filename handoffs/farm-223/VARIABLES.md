# Variables for #223

On BP_FarmPlot make `Kind`, `Yield` and `PlotId` Instance Editable (eye open): they are set per placed plot.

| Blueprint | Name | Default | Meaning |
|---|---|---|---|
| BP_FarmPlot | Kind | 0 | 0 wheat, 1 cabbage (set per placed plot) |
| BP_FarmPlot | Stage | 0 | 0 bare, 1 sown, 2 growing, 3 ripe, 4 stubble |
| BP_FarmPlot | Tended | False | tended today (needed to grow) |
| BP_FarmPlot | Claimed | False | a farmer is on it |
| BP_FarmPlot | LastYield | 0 | food from the last harvest (farmer reads it) |
| BP_FarmPlot | Yield | 16 | food per harvest: 16 wheat, set 10 on cabbage plots |
| BP_FarmPlot | PlotId | 0 | unique per placed plot (0, 1, 2...): the save slot index |
| BP_FarmPlot | StageMeshes | - | 10 meshes: Kind*5+Stage (setup script fills it) |
| BP_Farmer | State | 0 | 0 idle, 1 to plot, 2 working, 3 to granary, 4 fleeing, 5 home |
| BP_Farmer | Plot | - | the claimed plot |
| BP_Farmer | Carry | 0 | food in the basket |
| BP_Farmer | HP | 100.0 | health |
| BP_Farmer | Dead | False | dead (zombies drop him as a target) |
| BP_Farmer | Danger | False | a zombie is within FleeRadius (scratch) |
| BP_Farmer | WorkUntil | 0.0 | game time the current job ends |
| BP_Farmer | WorkSeconds | 6.0 | seconds per job (sow / tend / harvest) |
| BP_Farmer | FleeRadius | 2000.0 | cm: a zombie this close sends him home |
| BP_FarmDirector | Day | 0 | days passed (dusk -> dawn) |
| BP_FarmDirector | WasNight | False | last poll was night |
| BP_FarmDirector | StartFarmers | 3 | farmers on a new game |
| BP_FarmDirector | SpawnLeft | 0 | scratch: farmers to spawn |
| BP_FarmDirector | Alive | 0 | living farmers |
| BP_FarmDirector | SaveData | - | scratch: the save array |
| BP_FarmerHire | Cost | 60 | gold per farmer (also in the banner text) |
| BP_FarmerHire | MaxFarmers | 12 | cap |
| BP_ZombieHUD | Food | 0 | the food stock (#227 eats it) |
| BP_ZombieHUD | Farmers | 0 | living farmers (shown on the HUD) |

### BP_FarmPlot
```
BPVar(VarName="Kind",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E000,VarType=(PinCategory="int"),FriendlyName="Kind",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Stage",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E001,VarType=(PinCategory="int"),FriendlyName="Stage",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Tended",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E002,VarType=(PinCategory="bool"),FriendlyName="Tended",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="Claimed",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E003,VarType=(PinCategory="bool"),FriendlyName="Claimed",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="LastYield",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E004,VarType=(PinCategory="int"),FriendlyName="LastYield",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Yield",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E005,VarType=(PinCategory="int"),FriendlyName="Yield",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="16")
BPVar(VarName="PlotId",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E006,VarType=(PinCategory="int"),FriendlyName="PlotId",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="StageMeshes",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E007,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.StaticMesh'",ContainerType=Array),FriendlyName="StageMeshes",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
```

### BP_Farmer
```
BPVar(VarName="State",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E008,VarType=(PinCategory="int"),FriendlyName="State",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Plot",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E009,VarType=(PinCategory="object",PinSubCategoryObject="/Script/Engine.BlueprintGeneratedClass'/Game/CastleDefender/Gameplay/Farm/BP_FarmPlot.BP_FarmPlot_C'"),FriendlyName="Plot",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Carry",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E00A,VarType=(PinCategory="int"),FriendlyName="Carry",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="HP",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E00B,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="HP",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="100.0")
BPVar(VarName="Dead",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E00C,VarType=(PinCategory="bool"),FriendlyName="Dead",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="Danger",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E00D,VarType=(PinCategory="bool"),FriendlyName="Danger",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="WorkUntil",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E00E,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="WorkUntil",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="WorkSeconds",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E00F,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="WorkSeconds",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="6.0")
BPVar(VarName="FleeRadius",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E010,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FleeRadius",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="2000.0")
```

### BP_FarmDirector
```
BPVar(VarName="Day",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E011,VarType=(PinCategory="int"),FriendlyName="Day",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="WasNight",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E012,VarType=(PinCategory="bool"),FriendlyName="WasNight",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="StartFarmers",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E013,VarType=(PinCategory="int"),FriendlyName="StartFarmers",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="3")
BPVar(VarName="SpawnLeft",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E014,VarType=(PinCategory="int"),FriendlyName="SpawnLeft",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Alive",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E015,VarType=(PinCategory="int"),FriendlyName="Alive",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="SaveData",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E016,VarType=(PinCategory="real",PinSubCategory="double",ContainerType=Array),FriendlyName="SaveData",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
```

### BP_FarmerHire
```
BPVar(VarName="Cost",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E017,VarType=(PinCategory="int"),FriendlyName="Cost",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="60")
BPVar(VarName="MaxFarmers",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E018,VarType=(PinCategory="int"),FriendlyName="MaxFarmers",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="12")
```

### BP_ZombieHUD
```
BPVar(VarName="Food",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E019,VarType=(PinCategory="int"),FriendlyName="Food",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Farmers",VarGuid=223F0A11B2C34D5E8F90A1B2C3D4E01A,VarType=(PinCategory="int"),FriendlyName="Farmers",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
```
