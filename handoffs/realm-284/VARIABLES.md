# Variables for #284

| Blueprint | Name | Default | Meaning |
|---|---|---|---|
| BP_Cannonball | Bounced | False | already bounced off the dome once |
| BP_Cannonball | BounceVel | - | velocity after the bounce |
| BP_RealmDirector | Collapsed | False | the realm is gone |
| BP_RealmDirector | Dome | - | the dome actor (tag RealmBubble) |
| BP_RealmDirector | DomeOrigin | - | dome bounds centre |
| BP_RealmDirector | DomeExtent | - | dome bounds half size |
| BP_RealmDirector | DomeScale | - | dome scale when the collapse starts |
| BP_RealmDirector | Soldiers | - | scratch |
| BP_RealmDirector | DeadCount | 0 | tentacles fallen |
| BP_RealmDirector | TentaclesToKill | 2 | falls needed for the collapse |
| BP_RealmDirector | SoldierDPS | 25.0 | Health per second each soldier in reach takes off a tentacle |
| BP_RealmDirector | HitRange | 450.0 | cm: soldier reach to a tentacle |
| BP_RealmDirector | FadeT | 0.0 | collapse progress 0..1 |

### BP_Cannonball
```
BPVar(VarName="Bounced",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E000,VarType=(PinCategory="bool"),FriendlyName="Bounced",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="BounceVel",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E001,VarType=(PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),FriendlyName="BounceVel",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
```

### BP_RealmDirector
```
BPVar(VarName="Collapsed",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E002,VarType=(PinCategory="bool"),FriendlyName="Collapsed",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="Dome",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E003,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'"),FriendlyName="Dome",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="DomeOrigin",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E004,VarType=(PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),FriendlyName="DomeOrigin",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="DomeExtent",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E005,VarType=(PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),FriendlyName="DomeExtent",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="DomeScale",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E006,VarType=(PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),FriendlyName="DomeScale",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Soldiers",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E007,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'",ContainerType=Array),FriendlyName="Soldiers",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="DeadCount",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E008,VarType=(PinCategory="int"),FriendlyName="DeadCount",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="TentaclesToKill",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E009,VarType=(PinCategory="int"),FriendlyName="TentaclesToKill",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="2")
BPVar(VarName="SoldierDPS",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E00A,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="SoldierDPS",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="25.0")
BPVar(VarName="HitRange",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E00B,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="HitRange",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="450.0")
BPVar(VarName="FadeT",VarGuid=284E0A11B2C34D5E8F90A1B2C3D4E00C,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FadeT",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
```
