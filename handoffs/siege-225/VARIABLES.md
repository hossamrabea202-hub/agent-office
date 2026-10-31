# Variables for #225 gameplay

Add them to BP_SiegeEngine (the parent; BP_SiegeRam / BP_SiegeTower inherit them) and BP_SiegeDirector.

| Blueprint | Name | Default | Meaning |
|---|---|---|---|
| BP_SiegeEngine | Kind | 0 | 0 ram, 1 tower (children set it) |
| BP_SiegeEngine | MaxHP | 900.0 | HP at spawn |
| BP_SiegeEngine | HP | 0.0 | current HP |
| BP_SiegeEngine | BaseSpeed | 120.0 | cm/s with all 4 pushers |
| BP_SiegeEngine | Dead | False | broken (wreck) |
| BP_SiegeEngine | Pushers | - | the 4 pusher zombies |
| BP_SiegeEngine | Alive | 0 | scratch: living pushers |
| BP_SiegeEngine | NextHit | 0.0 | ram: next gate hit time |
| BP_SiegeEngine | GatePeriod | 5.0 | ram: seconds between gate hits |
| BP_SiegeEngine | RamHit | 20.0 | ram: GateDamage % per hit (before forge bands) |
| BP_SiegeEngine | BridgeT | 0.0 | tower: 0 bridge up .. 1 down |
| BP_SiegeEngine | BridgeUpRoll | 90.0 | tower: bridge roll when raised (flip to -90 if it raises downward) |
| BP_SiegeEngine | SpillLeft | 10 | tower: zombies still to spill |
| BP_SiegeEngine | SpillPeriod | 2.5 | tower: seconds between spills |
| BP_SiegeEngine | NextSpill | 0.0 | tower: next spill time |
| BP_SiegeEngine | WallPoint | - | tower: SiegeWall target (set by the director) |
| BP_SiegeEngine | BurnUntil | 0.0 | burning until this game time |
| BP_SiegeEngine | BurnDPS | 15.0 | fire damage per second |
| BP_SiegeEngine | CannonMult | 5.0 | cannonball damage multiplier (and ignites) |
| BP_SiegeEngine | IntactMesh | - | SM_Siege_Ram / _Tower |
| BP_SiegeEngine | WreckMesh | - | SM_Siege_RamWreck / _TowerWreck |
| BP_SiegeEngine | BridgeMesh | - | SM_Siege_TowerBridge |
| BP_SiegeEngine | MeshYaw | 0.0 | Body yaw so the front is +X: ram 180, tower -90 |
| BP_SiegeEngine | PusherScale | 1.25 | size of the pusher zombies |
| BP_SiegeDirector | LastWave | 0 | last wave seen |
| BP_SiegeDirector | RamFromWave | 6 | night waves from this one bring a ram |
| BP_SiegeDirector | TowerFromWave | 9 | night waves from this one bring a tower too |
| BP_SiegeDirector | BestDist | 0.0 | scratch |

### BP_SiegeEngine
```
BPVar(VarName="Kind",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E000,VarType=(PinCategory="int"),FriendlyName="Kind",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="MaxHP",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E001,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="MaxHP",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="900.0")
BPVar(VarName="HP",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E002,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="HP",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="BaseSpeed",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E003,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BaseSpeed",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="120.0")
BPVar(VarName="Dead",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E004,VarType=(PinCategory="bool"),FriendlyName="Dead",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
BPVar(VarName="Pushers",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E005,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'",ContainerType=Array),FriendlyName="Pushers",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="Alive",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E006,VarType=(PinCategory="int"),FriendlyName="Alive",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="NextHit",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E007,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="NextHit",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="GatePeriod",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E008,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="GatePeriod",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="5.0")
BPVar(VarName="RamHit",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E009,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="RamHit",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="20.0")
BPVar(VarName="BridgeT",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E00A,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BridgeT",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="BridgeUpRoll",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E00B,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BridgeUpRoll",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="90.0")
BPVar(VarName="SpillLeft",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E00C,VarType=(PinCategory="int"),FriendlyName="SpillLeft",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="10")
BPVar(VarName="SpillPeriod",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E00D,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="SpillPeriod",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="2.5")
BPVar(VarName="NextSpill",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E00E,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="NextSpill",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="WallPoint",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E00F,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'"),FriendlyName="WallPoint",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="BurnUntil",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E010,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BurnUntil",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="BurnDPS",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E011,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BurnDPS",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="15.0")
BPVar(VarName="CannonMult",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E012,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="CannonMult",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="5.0")
BPVar(VarName="IntactMesh",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E013,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.StaticMesh'"),FriendlyName="IntactMesh",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="WreckMesh",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E014,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.StaticMesh'"),FriendlyName="WreckMesh",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="BridgeMesh",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E015,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.StaticMesh'"),FriendlyName="BridgeMesh",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="MeshYaw",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E016,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="MeshYaw",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="PusherScale",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E017,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="PusherScale",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="1.25")
```

### BP_SiegeDirector
```
BPVar(VarName="LastWave",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E018,VarType=(PinCategory="int"),FriendlyName="LastWave",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="RamFromWave",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E019,VarType=(PinCategory="int"),FriendlyName="RamFromWave",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="6")
BPVar(VarName="TowerFromWave",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E01A,VarType=(PinCategory="int"),FriendlyName="TowerFromWave",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="9")
BPVar(VarName="BestDist",VarGuid=225E0A11B2C34D5E8F90A1B2C3D4E01B,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BestDist",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
```
