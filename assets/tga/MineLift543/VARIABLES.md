## BP_MineLift (BPVar lines in VARIABLES_BP_MineLift_BPVar.txt)

| Name | Default | Meaning |
|---|---|---|
| Partner | - | INSTANCE: the other BP_MineLift (set by import_mine543_ue.py --place) |
| Gate | - | INSTANCE, top only: MineGate_Up (the hut door it opens) |
| IsTop | false | INSTANCE: true on MineLift_Top |
| RopeTop | 115.0 | INSTANCE cm: where the rope leaves (top: the drum, 115; bottom: the shaft top, 1450) |
| PromptTop | [E] Open the mine door | shown at the hut door |
| PromptBottom | [E] Ride the bucket up | shown at the bucket in the dungeon |
| ArriveText | The old mine, 50 m down | notice on arrival below |
| ArriveTextTop | Back up at the mine entrance | notice on arrival above |
| UseRange | 220.0 | cm: how near the hero must be |
| DDoor | 0.8 | s: the door swing |
| DTop | 4.5 | s: the top leg (8.5 m) |
| DBottom | 5.4 | s: the bottom leg (10.2 m); keep DBottom = DTop x 1.2 so the speed matches at the swap |
| Phase | 0 | scratch: ride state 0..8 |
| T | 0.0 | scratch: time in this phase |
| EWas | false | scratch |
| PressNow | false | scratch |
| Shown | false | scratch |

## BP_MineFind (BPVar lines in VARIABLES_BP_MineFind_BPVar.txt)

| Name | Default | Meaning |
|---|---|---|
| Prompt | [E] Take the sword | shown near the find |
| FoundText | You found the Ulfberht sword | notice when taken (the card shows) |
| UseRange | 220.0 | cm |
| Taken | false | scratch |
| CardOn | false | scratch |
| EWas | false | scratch |
| PressNow | false | scratch |
| Shown | false | scratch |

