# #44 variables

| Blueprint | Name | Default | Meaning |
|---|---|---|---|
| BP_ZombieTower | Spot | - | set by the director |
| BP_ZombieTower | CastleCenter | 964,1750,0 | a point inside the castle (the player start): sets which side is "in" |
| BP_ZombieTower | HP | 600.0 | base HP: at 0 the tower topples |
| BP_ZombieTower | GrowEvery | 1.8 | s per absorbed zombie |
| BP_ZombieTower | ClimbEvery | 2.0 | s per zombie over the wall |
| BP_ZombieTower | AbsorbRadius | 1200.0 | cm |
| BP_ZombieTower | LeanPerLayer | 25.0 | cm each layer leans onto the wall |
| BP_ZombieTower | SwayDeg | 4.0 | sway at full height |
| BP_ZombieTower | Inward | 0,0,0 | state |
| BP_ZombieTower | GroundZ | 0.0 | state |
| BP_ZombieTower | WallTopZ | 0.0 | state |
| BP_ZombieTower | WallWalk | 0,0,0 | state |
| BP_ZombieTower | Spacing | 180.0 | state |
| BP_ZombieTower | TowerYaw | 0.0 | state |
| BP_ZombieTower | Tiers | - | state |
| BP_ZombieTower | Absorbed | - | state |
| BP_ZombieTower | Count | 0 | state |
| BP_ZombieTower | NextAbsorb | 0.0 | state |
| BP_ZombieTower | NextClimb | 0.0 | state |
| BP_ZombieTower | Breached | false | state |
| BP_ZombieTower | Falling | false | state |
| BP_ZombieTower | FallT0 | 0.0 | state |
| BP_ZombieTower | FallDir | 1.0 | state |
| BP_ZombieTower | Landed | false | state |
| BP_ZombieTower | LandAt | 0,0,0 | state |
| BP_ZombieTower | Best | - | scratch |
| BP_ZombieTower | BestD | 0.0 | scratch |
| BP_ZombieTower | Climber | - | scratch |
| BP_TowerDirector | FromWave | 4 | first wave with towers |
| BP_TowerDirector | MaxTowers | 2 | towers standing at once |
| BP_TowerDirector | GatherMin | 6 | zombies at a breach spot to start one |
| BP_TowerDirector | GatherRadius | 700.0 | cm |
| BP_TowerDirector | Cooldown | 40.0 | s between new towers |
| BP_TowerDirector | NextTowerAt | 0.0 | state |
| BP_TowerDirector | Crowd | 0 | scratch |
| BP_TowerDirector | Spots | - | state |
| BP_TowerDirector | SpotTower | - | state |
