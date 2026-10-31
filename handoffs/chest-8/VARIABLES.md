# #8 BP_TreasureChest variables

| Name | Default | Meaning |
|---|---|---|
| ChestId | 1 | INSTANCE: unique per placed chest (its save slot is CastleSaveChest<ChestId>) |
| Reward | 1500 | INSTANCE: gold paid once |
| Prompt | [E] Open the chest | notice when the hero comes near |
| UseRange | 220.0 | cm |
| GuardRange | 3500.0 | cm: guards appear the first time the hero comes this near |
| GuardCount | 4 | BP_Zombie guards along the tunnel, 4.5-9 m in front of and behind the chest |
| BruteToo | true | +1 BP_HalfHorseZombie 7.5 m behind the chest |
| LidPitch | -105.0 | degrees the lid opens (flip the sign if it opens the wrong way) |
| GlowBase | 60.0 | candela of the gold shine while closed (x4 burst on opening) |
| Opened | false | state |
| OpenT0 | -100.0 | state |
| EWas | false | scratch |
| Shown | false | scratch |
| PressNow | false | scratch |
| Guarded | false | scratch |
| CashPlayed | false | state |
| Rays | - | found by tag |
| RaysMID | - | made at BeginPlay |
| Hinge | - | found by tag |
| Glow | - | found by tag |
| Glint | - | found by tag |
