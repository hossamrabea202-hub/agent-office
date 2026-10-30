# Variables and defaults

Create only under `/Game/Codex/CastleAftermath_v1`. Parent: ActorComponent; Tick off.

## BPC_ConvoyJob50

| Variable | Type | Default |
|---|---|---|
| OrderId | Integer | 0 |
| State | Integer | 0 |
| Accepted | Boolean | false |
| MoveAllowed | Boolean | false |
| ThreatActive | Boolean | false |
| DeployRequested | Boolean | false |
| ShouldTargetConvoy | Boolean | false |
| WheelL | Double | 0.0 |
| WheelR | Double | 0.0 |
| WheelRadiusCm | Double | 55.4 |
| MaximumTravelCmPerSec | Double | 180.0 |
| WheelSampleAccepted | Boolean | false |

## BPC_GateAftermath162

| Variable | Type | Default |
|---|---|---|
| BlastRevision | Integer | 0 |
| Scars | Integer | 0 |
| RepairBands | Integer | 0 |
| Broken | Boolean | false |
| PieceCount | Integer | 0 |
| DebrisRemaining | Integer | 0 |
| PieceStates | Integer Array | [] |
| SalvageCount | Integer | 0 |
| JobId | Integer | 0 |
| LastJobId | Integer | 0 |
| Stage | Integer | 0 |
| ClearOnly | Boolean | false |
| StageSeconds | Double | 0.0 |
| PendingPiece | Integer | -1 |
| ReadyToRestore | Boolean | false |
| Accepted | Boolean | false |
| WorkActive | Boolean | false |
| SnapshotStage | Integer | 0 |
| BuildProgress | Double | 0.0 |

## BPC_BlobMorph164

| Variable | Type | Default |
|---|---|---|
| SpawnId | Integer | 0 |
| State | Integer | 0 |
| Age | Double | 0.0 |
| Melt | Double | 0.0 |
| Form | Double | 0.04 |
| WobbleStrength | Double | 1.0 |
| BlobWeight | Double | 0.96 |
| PuddleWeight | Double | 0.0 |
| Accepted | Boolean | false |
| ReadyForHandoff | Boolean | false |
| MeltSeconds | Double | 1.6 |
| RiseSeconds | Double | 4.2 |

## BPC_HumanReaction163

| Variable | Type | Default |
|---|---|---|
| LastEventId | Integer | 0 |
| ActiveKind | Integer | -1 |
| Until | Double | 0.0 |
| GlobalCooldownUntil | Double | 0.0 |
| LookCooldownUntil | Double | 0.0 |
| FearCooldownUntil | Double | 0.0 |
| CrewCooldownUntil | Double | 0.0 |
| ReliefCooldownUntil | Double | 0.0 |
| Accepted | Boolean | false |
| LastNow | Double | 0.0 |

## BPC_FallenRecord41

| Variable | Type | Default |
|---|---|---|
| FallenId | Integer | 0 |
| DeathWave | Integer | 0 |
| DeathTime | Double | 0.0 |
| Kind | Integer | 0 |
| State | Integer | 0 |
| Accepted | Boolean | false |
| SpawnRequested | Boolean | false |
| BudgetConsumed | Boolean | false |
| Attempts | Integer | 0 |
| RetryAt | Double | 0.0 |
| LastNow | Double | 0.0 |
