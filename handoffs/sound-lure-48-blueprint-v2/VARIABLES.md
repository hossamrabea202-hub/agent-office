# Blueprint variables and defaults

Create at the exact paths listed in README.md. Array defaults are empty; object defaults are None.

All variables must be accessible to the other components (Private OFF). Runtime variables are transient; never save them to a SaveGame.

## BP_NoiseWorld48

Parent: Actor

| Variable | Type | Default |
|---|---|---|
| Enabled | Boolean | true |
| Accepted | Boolean | false |
| Serial | Integer | 0 |
| Count | Integer | 0 |
| WriteIndex | Integer | 0 |
| WindowStart | Float (double precision) | -1.0 |
| WindowCount | Integer | 0 |
| Now | Float (double precision) | 0.0 |
| Rain | Float (double precision) | 0.0 |
| Fog | Float (double precision) | 0.0 |
| WindToward | Vector | [0.0, 0.0, 0.0] |
| WindStrength | Float (double precision) | 0.0 |
| Ids | Integer Array | [] |
| Kinds | Integer Array | [] |
| Locations | Vector Array | [] |
| Born | Float (double precision) Array | [] |
| Until | Float (double precision) Array | [] |
| Radii | Float (double precision) Array | [] |
| Saliences | Float (double precision) Array | [] |
| Weather | Float (double precision) Array | [] |
| Winds | Vector Array | [] |
| Strengths | Float (double precision) Array | [] |

## BPC_NoiseSource48

Parent: ActorComponent

| Variable | Type | Default |
|---|---|---|
| World | BP_NoiseWorld48 Object Reference | null |
| Kind | Integer | 2 |
| NextEmitAt | Float (double precision) | -1.0 |
| Accepted | Boolean | false |
| Now | Float (double precision) | 0.0 |
| OldNext | Float (double precision) | -1.0 |

## BPC_NoiseListener48

Parent: ActorComponent

| Variable | Type | Default |
|---|---|---|
| World | BP_NoiseWorld48 Object Reference | null |
| HasGoal | Boolean | false |
| Changed | Boolean | false |
| GoalPosition | Vector | [0.0, 0.0, 0.0] |
| GoalUntil | Float (double precision) | 0.0 |
| GoalScore | Float (double precision) | 0.0 |
| GoalId | Integer | 0 |
| NextRetargetAt | Float (double precision) | 0.0 |
| LastSeen | Integer | 0 |
| ArrivalRadius | Float (double precision) | 150.0 |
| Now | Float (double precision) | 0.0 |
| Here | Vector | [0.0, 0.0, 0.0] |
| BestIndex | Integer | -1 |
| BestScore | Float (double precision) | 0.0 |
| CandidateScore | Float (double precision) | 0.0 |
| CandidateRadius | Float (double precision) | 0.0 |
