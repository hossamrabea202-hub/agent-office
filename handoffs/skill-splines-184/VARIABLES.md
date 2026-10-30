# Variables to add to BP_SkillTreeHUD

```
BPVar(VarName="SPT",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7A91,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="SPT",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="SPN",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7A92,VarType=(PinCategory="int"),FriendlyName="SPN",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
BPVar(VarName="SPPrevLevel",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7A93,VarType=(PinCategory="int"),FriendlyName="SPPrevLevel",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0")
```

| Name | Type | Meaning |
|---|---|---|
| SPT | float | real time the current burst started (0 = none) |
| SPN | int | levels gained in that burst (reserved for a bigger burst later) |
| SPPrevLevel | int | last seen hero level (0 = not initialised, so the first frame does not fire) |
