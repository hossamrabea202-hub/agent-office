# #322 part 2 variables

## ABP_FleshBrute

| Name | Default | Meaning |
|---|---|---|
| SeqA | FB_ZA_Idle_A | clip in channel A |
| SeqB | FB_ZA_Idle_A | clip in channel B |
| TimeA | 0 | state |
| TimeB | 0 | state |
| RateA | 0 | state |
| RateB | 0 | state |
| LoopA | true | state |
| LoopB | true | state |
| UseB | false | state: B is the live channel |
| Alpha | 0 | state: 0 = A, 1 = B |
| Gait | 0 | state: speed match of the looping (gait) clips |
| Jitter | 0 | rolled per brute at spawn |
| JitterMin | 9 | slowest own rhythm |
| JitterMax | 06 | fastest own rhythm |
| Heavy | 92 | gait weight: below 1 = heavier, slower steps |
| GaitMin | 8 | gait rate when nearly stopped (+-20 % rule) |
| GaitMax | 2 | gait rate cap when pushed faster than max speed |
| BlendTime | 25 | s crossfade between clips |

## BP_FleshBrute

| Name | Default | Meaning |
|---|---|---|
| FBAnim | - | the mesh's ABP_FleshBrute (set at BeginPlay) |
