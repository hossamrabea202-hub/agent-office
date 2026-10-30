# Variables for #201

| Blueprint | Name | Type | Default | Meaning |
|---|---|---|---|---|
| BP_Mine | Period | float | 45.0 | seconds between carts |
| BP_Mine | VeinLeft | int | 0 | carts still to come from the current vein |
| BP_Mine | VeinMetal | int | 0 | the vein's metal (0..4) |
| BP_Mine | LastMetal | int | 0 | metal rolled for the cart being sent |
| BP_OreCart | Metal | int | 0 | 0 iron, 1 copper, 2 silver, 3 gold ore, 4 starmetal |
| BP_OreCart | HP | float | 300.0 | cart health |
| BP_OrePile | Metal | int | 0 | as above |
| BP_ZombieHUD | Ore | int **array** | [0,0,0,0,0] | the stockpile, index = metal |

Paste lines for My Blueprint (optional; adding by hand is the same):
```
BPVar(VarName="Period",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B01,VarType=(PinCategory="real",PinSubCategory="float"),FriendlyName="Period",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="45.0")
BPVar(VarName="VeinLeft",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B02,VarType=(PinCategory="int"),FriendlyName="VeinLeft",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="VeinMetal",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B03,VarType=(PinCategory="int"),FriendlyName="VeinMetal",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="LastMetal",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B04,VarType=(PinCategory="int"),FriendlyName="LastMetal",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="Metal",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B05,VarType=(PinCategory="int"),FriendlyName="Metal",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="HP",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B06,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="HP",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="300.0")
BPVar(VarName="Ore",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B07,VarType=(PinCategory="int",ContainerType=Array),FriendlyName="Ore",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="((0),(0),(0),(0),(0))")
```

Part 2 (forge), all on BP_ZombieHUD, int, default 0: `ForgeGate` (0..3), `ForgeSword`, `ForgeBolt`, `ForgePlate` (0/1).
```
BPVar(VarName="ForgeGate",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B08,VarType=(PinCategory="int"),FriendlyName="ForgeGate",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="ForgeSword",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B09,VarType=(PinCategory="int"),FriendlyName="ForgeSword",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="ForgeBolt",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B0A,VarType=(PinCategory="int"),FriendlyName="ForgeBolt",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="ForgePlate",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7B0B,VarType=(PinCategory="int"),FriendlyName="ForgePlate",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
```
