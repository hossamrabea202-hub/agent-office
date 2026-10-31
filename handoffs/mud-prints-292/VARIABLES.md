# #292 BPC_MudPrints variables (BPVar lines in VARIABLES_BPVar.txt)

| Name | Default | Meaning |
|---|---|---|
| Pads | - | the BP_MudPad actors (tag MudPad), found at BeginPlay |
| Move | - | the owner's movement (no prints in the air) |
| InMud | false | standing in a puddle this tick |
| MudLeft | 0 | muddy prints still to leave |
| Prints | 6 | prints after leaving the mud ("a few steps") |
| Side | 1.0 | left / right foot (+-1) |
| LastLoc | - | where the last print was made |
| Stride | 80.0 | cm between prints |
| FootDrop | 92.0 | cm from the actor centre to the soles (capsule half height) |
| PrintMat | /Game/CastleDefender/Environment/Mud/MI_MudPrint.MI_MudPrint | the boot print decal (MI_MudPrint) |
