# Variables to add to BP_BarracksHUD (paste each line into My Blueprint, or add by hand)

```
BPVar(VarName="RQ",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7A81,VarType=(PinCategory="int",ContainerType=Array),FriendlyName="RQ",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5)
BPVar(VarName="RQStart",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7A82,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="RQStart",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="RQDur",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7A83,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="RQDur",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="0.0")
BPVar(VarName="RecruitSeconds",VarGuid=7C1E0C4A5B8D4E1F9A2B3C4D5E6F7A84,VarType=(PinCategory="real",PinSubCategory="double"),FriendlyName="RecruitSeconds",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="6.0")
```

| Name | Type | Default | Meaning |
|---|---|---|---|
| RQ | int array | empty | queued recruit kinds: 0 sword, 1 crossbow, 2 commander |
| RQStart | float | 0 | real time when the head of the queue started loading (0 = idle) |
| RQDur | float | 0 | how long the current one takes |
| RecruitSeconds | float | 6 | soldier load time; commander = 3× |
