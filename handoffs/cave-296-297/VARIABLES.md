# #297 BP_CaveDoor variables (BPVar lines in VARIABLES_BPVar.txt)

| Name | Default | Meaning |
|---|---|---|
| Target | - | INSTANCE: the other BP_CaveDoor (cave door -> dungeon door and back) |
| Prompt | [E] Go down into the mine | INSTANCE: shown when the hero comes near (dungeon door: "[E] Climb back up to the cave") |
| UseRange | 220.0 | cm: how near the hero must be |
| ExitDist | 150.0 | cm: where the hero lands in front of the Target door |
| Busy | false | scratch: a teleport is running |
| EWas | false | scratch: E held last poll |
| Shown | false | scratch: prompt shown this visit |
| PressNow | false | scratch: E pressed this poll |
