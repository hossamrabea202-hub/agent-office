# #487 Per-frame Blueprint work (i5, 2026-11-04)

bp_smells.js over the 193 Blueprint exports from 11-03 (older than fixes A-F, so zombie, wave manager and soldier rows may already be fixed). 106 events run every frame. Sorted by nodes; no timing was measured here.

| Nodes | Loops | Blueprint | Expensive calls reachable from Tick |
|---|---|---|---|
| 188 | 0 | BP_HeroAuras.T3D | Cast x20, GetAllActorsOfClass x2, GetActorOfClass x3, BeginDeferredActorSpawnFromClass x3 |
| 162 | 6 | BP_SoldierSword.T3D | GetAllActorsOfClass x6, SimpleMoveToLocation x3, Cast x4, SimpleMoveToActor x1, LineTraceSingle x1, PlayAnimation x1, PlayAnimMontage x4, SpawnActor x2, GetActorOfClass x1, CreateDynamicMaterialInstance x1 |
| 122 | 0 | BP_Crossbow.T3D | Cast x7, K2_SetTimer x1, PlayAnimMontage x1 |
| 85 | 4 | BP_ZombieWaveManager.T3D | GetAllActorsOfClass x3, SpawnActor x5, Delay x2, K2_SetTimer x1, SetMaterial x6, GetActorOfClass x1 |
| 69 | 0 | BP_RealmWasp.T3D | GetAllActorsOfClass x1, GetActorOfClass x1, PlayAnimation x5, Delay x1, Cast x1 |
| 63 | 0 | BP_SkillUnlockFX.T3D |  |
| 61 | 0 | BP_RealmVision.T3D |  |
| 60 | 0 | BP_ZombieCharge.T3D | GetAllActorsOfClass x1, PlayAnimation x1 |
| 54 | 1 | BPC_Weather.T3D | Cast x3, GetAllActorsWithTag x1 |
| 54 | 0 | BP_JellyBlob.T3D | CreateDynamicMaterialInstance x2, GetActorOfClass x3, BeginDeferredActorSpawnFromClass x1 |
| 46 | 0 | BP_GateBreachLeaf.T3D | GetActorOfClass x1, Delay x5 |
| 43 | 4 | BP_Whirlwind.T3D | Cast x1, GetAllActorsOfClass x4 |
| 43 | 0 | BP_RealmBreach.T3D | BeginDeferredActorSpawnFromClass x2 |
| 41 | 3 | BP_QuakeSlam.T3D | Cast x1, GetAllActorsOfClass x3 |
| 41 | 1 | BP_Fissure.T3D | Cast x1, GetAllActorsOfClass x1 |
| 41 | 0 | BP_BreachDirector.T3D | GetActorOfClass x1, BeginDeferredActorSpawnFromClass x2 |
| 39 | 0 | BP_TentacleVitals.T3D | LineTraceSingle x1, Cast x2, CreateDynamicMaterialInstance x1 |
| 38 | 3 | BP_JellyTrailManager.T3D | GetAllActorsOfClass x1, Cast x3 |
| 37 | 0 | BP_SFXWatch.T3D | GetAllActorsOfClass x1, GetActorOfClass x1, Cast x1 |
| 35 | 0 | BP_HalfHorseZombie.T3D | SimpleMoveToActor x1, PlayAnimation x5, Delay x1 |
| 34 | 0 | BP_HitFeel.T3D | GetAllActorsOfClass x1, Cast x2, Delay x1 |
| 33 | 0 | BPC_TentacleStrike.T3D | Cast x1 |
| 26 | 0 | BP_CastleGateControl.T3D | GetActorOfClass x2 |
| 25 | 0 | BP_ZombieJellyShield.T3D | Cast x3 |
| 23 | 0 | BP_JellyShieldAll.T3D | GetAllActorsOfClass x1, Cast x1, CreateDynamicMaterialInstance x1 |
| 23 | 0 | BP_BlobMine.T3D |  |
| 22 | 0 | BP_ShockRider.T3D | Cast x2, CreateDynamicMaterialInstance x1 |
| 21 | 0 | BP_MusicDirector.T3D | GetActorOfClass x2 |
| 21 | 0 | BPC_Infection.T3D | Cast x3 |
| 18 | 0 | BP_ArmoryHUD.T3D | Cast x2 |
| 17 | 0 | BP_ZombieVariety.T3D | GetAllActorsOfClass x1 |
| 17 | 0 | BP_SoldierLevelWatch.T3D | GetAllActorsOfClass x1, Cast x1 |
| 16 | 1 | BPC_MudPrints.T3D | CreateDynamicMaterialInstance x1 |
| 14 | 0 | BP_Flare.T3D |  |
| 13 | 0 | BP_Zombie.T3D | Cast x1, GetActorOfClass x1 |
| 13 | 0 | BP_FleshBrute_BAK322.T3D | Cast x1, GetActorOfClass x1 |
| 13 | 0 | BP_FleshBrute_BAK.T3D | Cast x1, GetActorOfClass x1 |
| 13 | 0 | BP_FleshBrute.T3D | Cast x1, GetActorOfClass x1 |
| 12 | 0 | BP_TradeShowcase.T3D |  |
| 12 | 0 | BP_HeroDash.T3D | Cast x1 |
