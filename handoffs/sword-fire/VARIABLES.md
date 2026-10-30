# Variables to add to BP_ThirdPersonCharacter

| Name | Type | Default | Meaning |
|---|---|---|---|
| FireMID | Material Instance Dynamic (object ref) | – | the overlay instance on the sword |
| FireLight | Point Light Component (object ref) | – | the sword's light |
| FireHeat | float | 0.0 | current heat 0..1 |
| FireOn | bool | true | master switch (#95 element choice can drive it) |
| FireRange | float | 600.0 | cm: zombies closer than this light the blade |
| FireNear | bool | false | scratch: a zombie was in range this tick |

```
BPVar(VarName="FireMID",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C01,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.MaterialInstanceDynamic'"),FriendlyName="FireMID",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="FireLight",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C02,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.PointLightComponent'"),FriendlyName="FireLight",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="FireHeat",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C03,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FireHeat",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="FireOn",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C04,VarType=(PinCategory="bool"),FriendlyName="FireOn",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="True")
BPVar(VarName="FireRange",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C05,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="FireRange",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="600.0")
BPVar(VarName="FireNear",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C06,VarType=(PinCategory="bool"),FriendlyName="FireNear",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="False")
```

Burn + fire slash (same paste, v2):

| Name | Type | Default | Meaning |
|---|---|---|---|
| Burning | Actor (object ref) **array** | empty | zombies on fire, oldest first |
| BurnEnd | float **array** | empty | world time each burn ends (same order) |
| BurnDamage | float | 5.0 | damage per 0.25 s tick (= 20 per second) |
| BurnTime | float | 3.0 | seconds a zombie burns after a hot hit |

```
BPVar(VarName="Burning",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C07,VarType=(PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class'/Script/Engine.Actor'",ContainerType=Array),FriendlyName="Burning",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="BurnEnd",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C08,VarType=(PinCategory="real",PinSubCategory="double",ContainerType=Array),FriendlyName="BurnEnd",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="BurnDamage",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C09,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BurnDamage",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="5.0")
BPVar(VarName="BurnTime",VarGuid=5F1E0C4A5B8D4E1F9A2B3C4D5E6F7C0A,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="BurnTime",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="3.0")
```
