# #11 Survivors: variables (the BPVar lines are in VARIABLES_BPVar.txt)

| Blueprint | Name | Type | Default | Meaning |
|---|---|---|---|---|
| BPC_Survivors | LastArrival | real | -1000.0 | game time of the last arrival |
| BPC_Survivors | MinGap | real | 150.0 | s between two arrivals |
| BPC_Survivors | Chance | real | 0.12 | chance per 3 s poll once the gap is over (about one every 3-4 min when calm) |
| BPC_Survivors | FirstDelay | real | 120.0 | no survivor in the first 2 minutes of a game |
| BPC_Survivors | MaxWaiting | int | 2 | at most this many survivors around at once |
| BPC_Survivors | ArriveDist | real | 3000.0 | cm outside the gate |
| BPC_Survivors | CastleCentre | vector | 2300.000000,1725.000000,0.000000 | centre of the #41 castle box; outside = away from it |
| BP_Survivor | State | int | 0 | 0 to the gate, 1 waiting, 2 to the barracks, 3 healing |
| BP_Survivor | Inside | vector | 0,0,0 | just inside the gate |
| BP_Survivor | HealSpot | vector | 0,0,0 | next to the barracks NPC |
| BP_Survivor | HealT0 | real | 0.0 | game time healing started |
| BP_Survivor | HealSeconds | real | 60.0 | seconds to heal |
| BP_Survivor | FullUntil | real | 0.0 | shows "army full" until this time |
| BP_Survivor | MaxArmy | int | 30 | no take-in when the army (all BP_SoldierSword incl. crossbow / commanders) is this big |
| BP_Survivor | CastleCentre | vector | 2300.000000,1725.000000,0.000000 | same as BPC_Survivors |
| BP_Survivor | Label | TextRenderComponent | - | the floating line over his head |
