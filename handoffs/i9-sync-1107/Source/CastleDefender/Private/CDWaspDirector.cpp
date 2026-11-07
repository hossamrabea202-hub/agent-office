// CDWaspDirector.cpp (2026-11-06): waves -> flights, swarm coordination, anti-air queries. See the header.
#include "CDWaspDirector.h"
#include "RealmWaspBase.h"
#include "CDSettings.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "CollisionQueryParams.h"
#include "GameFramework/Character.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/PointLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/TargetPoint.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/UnrealType.h"

namespace CDWaspDir
{
	static int32 GEnable = 1;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.Wasp.Enable"), GEnable, TEXT("1 = the wave-driven wasp flights are on (default). 0 = no wasps spawn from waves (cd.Wasp.Spawn still works)."));

	static const TCHAR* WaveManagerPath = TEXT("/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager.BP_ZombieWaveManager_C");
	static const TCHAR* GatePath = TEXT("/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl.BP_CastleGateControl_C");
	static const FName NAME_Wave(TEXT("Wave")), NAME_SwarmEvery(TEXT("SwarmEveryNthWave")), NAME_SwarmLoc(TEXT("SwarmSpawnLocation")), NAME_SwarmUnlocked(TEXT("SwarmUnlocked")), NAME_GlowStrength(TEXT("GlowStrength"));
	static int32 GIgnoreUnlock = 0;
	static FAutoConsoleVariableRef CVarUnlock(TEXT("cd.Wasp.IgnoreUnlock"), GIgnoreUnlock, TEXT("1 = flights come even when bWaspRequireSwarmUnlocked is on and the realm is not breached (test)."));
	static bool ReadBool(const UObject* O, FName Name, bool& Out)
	{
		if (!O) { return false; }
		if (const FBoolProperty* P = CastField<FBoolProperty>(O->GetClass()->FindPropertyByName(Name))) { Out = P->GetPropertyValue_InContainer(O); return true; }
		return false;
	}

	static FAutoConsoleCommandWithWorldAndArgs CmdSpawn(TEXT("cd.Wasp.Spawn"), TEXT("cd.Wasp.Spawn <drones> [matriarchs] [wave]: fly a test flight in now (owner's test switch)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			UCDWaspDirector* D = World ? World->GetSubsystem<UCDWaspDirector>() : nullptr;
			if (!D) { UE_LOG(LogTemp, Warning, TEXT("cd.Wasp.Spawn: no wasp director in this world")); return; }
			const int32 Drones = Args.Num() > 0 ? FCString::Atoi(*Args[0]) : 3;
			const int32 Mats = Args.Num() > 1 ? FCString::Atoi(*Args[1]) : 0;
			const int32 Wave = Args.Num() > 2 ? FCString::Atoi(*Args[2]) : FMath::Max(1, D->GetAliveWaspCount() > 0 ? 1 : 1);
			D->SpawnFlight(Drones, Mats, Wave);
			UE_LOG(LogTemp, Display, TEXT("cd.Wasp.Spawn: flight of %d drones + %d matriarchs queued"), Drones, Mats);
		}));
	static FAutoConsoleCommandWithWorld CmdKill(TEXT("cd.Wasp.Kill"), TEXT("Kill every wasp."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
		{
			UCDWaspDirector* D = World ? World->GetSubsystem<UCDWaspDirector>() : nullptr;
			if (!D) { return; }
			int32 N = 0;
			D->ForEachWasp([&](ARealmWaspBase* W) { if (!W->IsWaspDead()) { W->Kill(); ++N; } });
			UE_LOG(LogTemp, Display, TEXT("cd.Wasp.Kill: %d wasps killed"), N);
		}));
	static FAutoConsoleCommandWithWorld CmdReport(TEXT("cd.Wasp.Report"), TEXT("Wasp system counters."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
		{
			UCDWaspDirector* D = World ? World->GetSubsystem<UCDWaspDirector>() : nullptr;
			if (!D) { return; }
			UE_LOG(LogTemp, Display, TEXT("cd.Wasp: alive %d | spawned %d killed %d | stings %d retreats %d dodges %d | soldier shots %d hits %d (%.0f%%)"),
				D->GetAliveWaspCount(), D->TotalSpawned, D->TotalKilled, D->TotalStings, D->TotalRetreats, D->TotalDodges, D->SoldierShots, D->SoldierHits,
				D->SoldierShots ? 100.f * float(D->SoldierHits) / float(D->SoldierShots) : 0.f);
		}));

	static bool ReadInt(const UObject* O, FName Name, int32& Out)
	{
		if (!O) { return false; }
		if (const FIntProperty* P = CastField<FIntProperty>(O->GetClass()->FindPropertyByName(Name))) { Out = P->GetPropertyValue_InContainer(O); return true; }
		return false;
	}
	static bool WriteInt(UObject* O, FName Name, int32 V)
	{
		if (!O) { return false; }
		if (FIntProperty* P = CastField<FIntProperty>(O->GetClass()->FindPropertyByName(Name))) { P->SetPropertyValue_InContainer(O, V); return true; }
		return false;
	}
	static bool ReadVector(const UObject* O, FName Name, FVector& Out)
	{
		if (!O) { return false; }
		const FStructProperty* P = CastField<FStructProperty>(O->GetClass()->FindPropertyByName(Name));
		if (!P || P->Struct != TBaseStructure<FVector>::Get()) { return false; }
		Out = *P->ContainerPtrToValuePtr<FVector>(O);
		return true;
	}
}

UCDWaspDirector* UCDWaspDirector::Get(const UObject* WorldContext)
{
	UWorld* W = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
	return W ? W->GetSubsystem<UCDWaspDirector>() : nullptr;
}

bool UCDWaspDirector::ShouldCreateSubsystem(UObject* Outer) const
{
	if (!Super::ShouldCreateSubsystem(Outer)) { return false; }
	const UWorld* W = Cast<UWorld>(Outer);
	return W && (W->WorldType == EWorldType::Game || W->WorldType == EWorldType::PIE);
}

void UCDWaspDirector::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	ManagerRefreshTimer = 0.f;
	WavePollTimer = 0.f;
	LastWave = -1;
}

void UCDWaspDirector::Deinitialize()
{
	Wasps.Reset(); DiveTokens.Reset(); Queue.Reset(); WaveManagers.Reset();
	Super::Deinitialize();
}

void UCDWaspDirector::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!World || !World->HasBegunPlay()) { return; }

	ManagerRefreshTimer -= DeltaTime;
	if (ManagerRefreshTimer <= 0.f) { ManagerRefreshTimer = 5.f; RefreshWaveManagers(); }

	if (CDWaspDir::GEnable)
	{
		WavePollTimer -= DeltaTime;
		if (WavePollTimer <= 0.f) { WavePollTimer = 0.5f; PollWaves(); }
	}

	if (CrackPulse > 0.f)
	{
		CrackPulse = FMath::Max(0.f, CrackPulse - DeltaTime * 0.6f);
		const float K = 1.f + 2.5f * CrackPulse;
		if (UPointLightComponent* L = CrackLight.Get()) { if (CrackLightBase > 0.f) { L->SetIntensity(CrackLightBase * K); } }
		if (UMaterialInstanceDynamic* M = CrackMat.Get()) { if (CrackGlowBase > 0.f) { M->SetScalarParameterValue(CDWaspDir::NAME_GlowStrength, CrackGlowBase * K); } }
	}

	if (Queue.Num() > 0)
	{
		SpawnTimer -= DeltaTime;
		if (SpawnTimer <= 0.f)
		{
			const FPendingSpawn P = Queue[0];
			Queue.RemoveAt(0);
			SpawnWasp(P.Caste, FlightSpawnPoint(FlightIndex++), P.Wave);
			SpawnTimer = GetDefault<UCDSettings>()->WaspSpawnInterval;
			if (Queue.Num() == 0) { FlightIndex = 0; }
		}
	}

	// drop dead entries now and then
	if (Wasps.Num() > 0 && (FlightIndex == 0) && FMath::Fmod(World->GetTimeSeconds(), 3.f) < DeltaTime)
	{
		Wasps.RemoveAll([](const TWeakObjectPtr<ARealmWaspBase>& W) { return !W.IsValid(); });
		for (auto It = DiveTokens.CreateIterator(); It; ++It) { if (!It.Key().IsValid() || !It.Value().IsValid()) { It.RemoveCurrent(); } }
	}
}

// ---------------------------------------------------------------- waves

void UCDWaspDirector::RefreshWaveManagers()
{
	UWorld* World = GetWorld();
	if (!World) { return; }
	if (!bWaveClassLookedUp)
	{
		bWaveClassLookedUp = true;
		WaveManagerClass = StaticLoadClass(AActor::StaticClass(), nullptr, CDWaspDir::WaveManagerPath);
		if (!WaveManagerClass.IsValid()) { UE_LOG(LogTemp, Warning, TEXT("cd.Wasp: %s not found; wasps only come from cd.Wasp.Spawn"), CDWaspDir::WaveManagerPath); }
	}
	WaveManagers.Reset();
	if (UClass* Cls = WaveManagerClass.Get())
	{
		for (TActorIterator<AActor> It(World, Cls); It; ++It) { WaveManagers.Add(*It); }
	}
	RefreshAnchor();
	RefreshCrack();
	if (GetDefault<UCDSettings>()->bWaspReplacesBlueprintSwarm) { DisableBlueprintSwarm(); }
}

void UCDWaspDirector::RefreshCrack()
{
	UWorld* World = GetWorld();
	if (!World || bCrackFound) { return; }
	// the crack: the static mesh actor whose mesh is SM_RealmCrack (labels are editor-only, the mesh name is not)
	AStaticMeshActor* Crack = nullptr;
	for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
	{
		const UStaticMeshComponent* C = It->GetStaticMeshComponent();
		if (C && C->GetStaticMesh() && C->GetStaticMesh()->GetName() == TEXT("SM_RealmCrack")) { Crack = *It; break; }
	}
	if (!Crack) { return; }
	bCrackFound = true;
	CrackActor = Crack;
	const FVector Loc = Crack->GetActorLocation();
	// the mouth is the pivot (bottom centre of the opening); a wasp appears 1.5 m up inside the fissure
	CrackMouth = Loc + FVector(0.f, 0.f, 150.f);
	// the orbit point: Realm_SwarmSpawn (a TargetPoint within 12 m of the crack), else 5 m up over the mouth
	CrackOrbit = Loc + FVector(0.f, 0.f, 500.f);
	float Best = 1200.f;
	for (TActorIterator<ATargetPoint> It(World); It; ++It)
	{
		const float D = FVector::Dist(It->GetActorLocation(), Loc);
		if (D < Best) { Best = D; CrackOrbit = It->GetActorLocation(); }
	}
	// the light in the mouth and the glow material, for the emergence flare
	Best = 1500.f;
	for (TActorIterator<APointLight> It(World); It; ++It)
	{
		const float D = FVector::Dist(It->GetActorLocation(), Loc);
		if (D < Best && It->PointLightComponent) { Best = D; CrackLight = It->PointLightComponent; CrackLightBase = It->PointLightComponent->Intensity; }
	}
	if (UStaticMeshComponent* C = Crack->GetStaticMeshComponent())
	{
		if (C->GetNumMaterials() > 0)
		{
			if (UMaterialInstanceDynamic* M = C->CreateAndSetMaterialInstanceDynamic(0))
			{
				CrackMat = M;
				float G = 0.f;
				if (M->GetScalarParameterValue(FMaterialParameterInfo(CDWaspDir::NAME_GlowStrength), G)) { CrackGlowBase = G; }
			}
		}
	}
	UE_LOG(LogTemp, Display, TEXT("cd.Wasp: realm crack found at %s; wasps emerge there and circle %s"), *Loc.ToString(), *CrackOrbit.ToString());
}

void UCDWaspDirector::PulseCrack(float Strength)
{
	CrackPulse = FMath::Max(CrackPulse, FMath::Clamp(Strength, 0.f, 1.f));
}

void UCDWaspDirector::RefreshAnchor()
{
	UWorld* World = GetWorld();
	if (!World) { return; }
	FVector ManagerLoc = FVector::ZeroVector; bool bManager = false;
	for (const TWeakObjectPtr<AActor>& M : WaveManagers) { if (AActor* A = M.Get()) { ManagerLoc = A->GetActorLocation(); bManager = true; break; } }

	bAnchorFound = false;
	if (UClass* Gate = StaticLoadClass(AActor::StaticClass(), nullptr, CDWaspDir::GatePath))
	{
		for (TActorIterator<AActor> It(World, Gate); It; ++It) { Anchor = It->GetActorLocation(); bAnchorFound = true; break; }
	}
	if (!bAnchorFound && bManager) { Anchor = ManagerLoc; bAnchorFound = true; }
	if (bManager)
	{
		const FVector D = (ManagerLoc - Anchor).GetSafeNormal2D();
		if (!D.IsNearlyZero()) { EnemyDir = D; }
	}
}

int32 UCDWaspDirector::ReadWave() const
{
	int32 Best = -1;
	for (const TWeakObjectPtr<AActor>& M : WaveManagers)
	{
		int32 W = 0;
		if (CDWaspDir::ReadInt(M.Get(), CDWaspDir::NAME_Wave, W)) { Best = FMath::Max(Best, W); }
	}
	return Best;
}

void UCDWaspDirector::DisableBlueprintSwarm()
{
	for (const TWeakObjectPtr<AActor>& M : WaveManagers)
	{
		int32 Cur = 0;
		if (CDWaspDir::ReadInt(M.Get(), CDWaspDir::NAME_SwarmEvery, Cur) && Cur < 1000000)
		{
			CDWaspDir::WriteInt(M.Get(), CDWaspDir::NAME_SwarmEvery, 1000000);
			if (!bSwarmDisabled) { bSwarmDisabled = true; UE_LOG(LogTemp, Display, TEXT("cd.Wasp: Blueprint swarm spawn parked (SwarmEveryNthWave = 1000000); flights come from UCDWaspDirector. Settings: bWaspReplacesBlueprintSwarm.")); }
		}
	}
}

void UCDWaspDirector::PollWaves()
{
	const int32 W = ReadWave();
	if (W < 0) { return; }
	if (LastWave < 0) { LastWave = W; return; }   // the wave the game was already on when we started: no flight for it
	if (W == LastWave) { return; }
	LastWave = W;

	const UCDSettings* S = GetDefault<UCDSettings>();
	if (W < S->WaspFirstWave) { return; }
	if (S->bWaspRequireSwarmUnlocked && !CDWaspDir::GIgnoreUnlock)
	{
		bool bUnlocked = false;
		for (const TWeakObjectPtr<AActor>& M : WaveManagers) { bool V = false; if (CDWaspDir::ReadBool(M.Get(), CDWaspDir::NAME_SwarmUnlocked, V) && V) { bUnlocked = true; break; } }
		if (!bUnlocked) { if (!bSwarmUnlockedSeen) { UE_LOG(LogTemp, Display, TEXT("cd.Wasp: wave %d, realm not breached (SwarmUnlocked false): no flight"), W); } return; }
		bSwarmUnlockedSeen = true;
	}
	const int32 Drones = FMath::Clamp(S->WaspDronesBase + FMath::RoundToInt(S->WaspDronesPerWave * float(W - S->WaspFirstWave)), 0, S->WaspDronesMax);
	int32 Matriarchs = 0;
	if (W >= S->WaspMatriarchFirstWave && ((W - S->WaspMatriarchFirstWave) % FMath::Max(1, S->WaspMatriarchEveryNthWave)) == 0)
	{
		Matriarchs = W >= S->WaspMatriarchPairWave ? 2 : 1;
	}
	if (Drones + Matriarchs > 0)
	{
		UE_LOG(LogTemp, Display, TEXT("cd.Wasp: wave %d -> flight of %d drones + %d matriarchs"), W, Drones, Matriarchs);
		SpawnFlight(Drones, Matriarchs, W);
	}
}

// ---------------------------------------------------------------- spawning

void UCDWaspDirector::SpawnFlight(int32 Drones, int32 Matriarchs, int32 ForWave)
{
	// drones lead, the matriarch comes in behind her escort
	for (int32 i = 0; i < Drones; ++i) { Queue.Add({ EWaspCaste::Drone, ForWave }); }
	for (int32 i = 0; i < Matriarchs; ++i) { Queue.Add({ EWaspCaste::Matriarch, ForWave }); }
	if (SpawnTimer <= 0.f) { SpawnTimer = 0.05f; }
}

FVector UCDWaspDirector::FlightSpawnPoint(int32 Index) const
{
	const UCDSettings* S = GetDefault<UCDSettings>();
	if (bCrackFound)
	{
		// out of the fissure: a little spread inside the mouth so a stream does not stack
		return CrackMouth + FVector(FMath::FRandRange(-60.f, 60.f), FMath::FRandRange(-60.f, 60.f), FMath::FRandRange(0.f, 120.f));
	}
	FVector Base = Anchor + EnemyDir * S->WaspSpawnDistance;
	// the Blueprint's own SwarmSpawnLocation wins when the owner placed one
	for (const TWeakObjectPtr<AActor>& M : WaveManagers)
	{
		FVector V;
		if (CDWaspDir::ReadVector(M.Get(), CDWaspDir::NAME_SwarmLoc, V) && !V.IsNearlyZero()) { Base = FVector(V.X, V.Y, Anchor.Z); break; }
	}
	const FVector Side = FVector::CrossProduct(EnemyDir, FVector::UpVector);
	const float Lateral = float((Index % 5) - 2) * 380.f + FMath::FRandRange(-120.f, 120.f);
	const float Back = float(Index / 5) * 450.f + FMath::FRandRange(0.f, 200.f);
	FVector P = Base + Side * Lateral + EnemyDir * Back;
	// altitude above the ground there
	float GroundZ = Anchor.Z;
	if (UWorld* World = GetWorld())
	{
		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, P + FVector(0, 0, 8000.f), P - FVector(0, 0, 8000.f), ECC_WorldStatic)) { GroundZ = Hit.Location.Z; }
	}
	P.Z = GroundZ + S->WaspSpawnAltitude + FMath::FRandRange(-250.f, 350.f);
	return P;
}

ARealmWaspBase* UCDWaspDirector::SpawnWasp(EWaspCaste Caste, const FVector& Location, int32 ForWave)
{
	UWorld* World = GetWorld();
	if (!World) { return nullptr; }
	const FRotator Facing = (Anchor - Location).GetSafeNormal2D().Rotation();
	const FTransform T(Facing, Location);
	ARealmWaspBase* W = World->SpawnActorDeferred<ARealmWaspBase>(ARealmWaspBase::StaticClass(), T, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
	if (!W) { UE_LOG(LogTemp, Warning, TEXT("cd.Wasp: spawn failed at %s"), *Location.ToString()); return nullptr; }
	W->Init(Caste, Anchor, ForWave);
	W->FinishSpawning(T);
	++TotalSpawned;
	if (bCrackFound) { PulseCrack(Caste == EWaspCaste::Matriarch ? 1.f : 0.6f); }
	return W;
}

// ---------------------------------------------------------------- registry and coordination

void UCDWaspDirector::Register(ARealmWaspBase* Wasp) { if (Wasp) { Wasps.AddUnique(Wasp); } }
void UCDWaspDirector::Unregister(ARealmWaspBase* Wasp) { Wasps.Remove(Wasp); DiveTokens.Remove(Wasp); }

int32 UCDWaspDirector::GetAliveWaspCount() const
{
	int32 N = 0;
	ForEachWasp([&](ARealmWaspBase* W) { if (!W->IsWaspDead()) { ++N; } });
	return N;
}

TArray<ARealmWaspBase*> UCDWaspDirector::GetWasps() const
{
	TArray<ARealmWaspBase*> Out;
	ForEachWasp([&](ARealmWaspBase* W) { Out.Add(W); });
	return Out;
}

int32 UCDWaspDirector::ClaimsOn(const AActor* Target) const
{
	if (!Target) { return 0; }
	int32 N = 0;
	ForEachWasp([&](ARealmWaspBase* W) { if (!W->IsWaspDead() && W->GetWaspTarget() == Target) { ++N; } });
	return N;
}

int32 UCDWaspDirector::HeroHunters() const
{
	const ACharacter* P = UGameplayStatics::GetPlayerCharacter(GetWorld(), 0);
	return P ? ClaimsOn(P) : 0;
}

int32 UCDWaspDirector::DiversOn(const AActor* Target) const
{
	int32 Weight = 0;
	for (const auto& Pair : DiveTokens)
	{
		const ARealmWaspBase* W = Pair.Key.Get();
		if (!W || W->IsWaspDead() || Pair.Value.Get() != Target) { continue; }
		Weight += W->GetCaste() == EWaspCaste::Matriarch ? 2 : 1;
	}
	return Weight;
}

bool UCDWaspDirector::RequestDiveToken(ARealmWaspBase* Wasp, AActor* Target)
{
	if (!Wasp || !Target) { return false; }
	if (const TWeakObjectPtr<AActor>* Held = DiveTokens.Find(Wasp)) { if (Held->Get() == Target) { return true; } }
	const int32 Weight = Wasp->GetCaste() == EWaspCaste::Matriarch ? 2 : 1;
	if (DiversOn(Target) + Weight > GetDefault<UCDSettings>()->WaspMaxDiversPerTarget) { return false; }
	DiveTokens.Add(Wasp, Target);
	return true;
}

void UCDWaspDirector::ReleaseDiveToken(ARealmWaspBase* Wasp) { DiveTokens.Remove(Wasp); }

// ---------------------------------------------------------------- anti-air

ARealmWaspBase* UCDWaspDirector::FindAntiAirTarget(const AActor* Shooter, const FVector& From, float Range, bool bNeedLOS) const
{
	UWorld* World = GetWorld();
	ARealmWaspBase* Best = nullptr;
	float BestScore = -1.f;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(WaspAALOS), false, Shooter);
	ForEachWasp([&](ARealmWaspBase* W)
	{
		if (W->IsWaspDead()) { return; }
		const FVector WL = W->GetActorLocation();
		const float D = FVector::Dist(From, WL);
		if (D > Range) { return; }
		float Score = 100.f / (1.f + D / 1000.f);
		if (W->IsDiving()) { Score += 40.f; if (W->GetWaspTarget() == Shooter) { Score += 60.f; } }
		if (W->IsRetreating()) { Score -= 10.f; }
		if (W->GetCaste() == EWaspCaste::Matriarch) { Score += 15.f; }   // the big one is the priority target
		if (W->GetMaxHP() > 0.f) { Score += (1.f - W->GetHP() / W->GetMaxHP()) * 30.f; }
		if (Score <= BestScore) { return; }
		if (bNeedLOS && World)
		{
			FHitResult Hit;
			if (World->LineTraceSingleByChannel(Hit, From, WL, ECC_Visibility, Q) && Hit.GetActor() != W) { return; }
		}
		BestScore = Score; Best = W;
	});
	return Best;
}

bool UCDWaspDirector::IsWaspThreatening(const AActor* Defender, float Radius) const
{
	if (!Defender) { return false; }
	bool bThreat = false;
	const FVector DL = Defender->GetActorLocation();
	ForEachWasp([&](ARealmWaspBase* W)
	{
		if (bThreat || W->IsWaspDead()) { return; }
		if (W->IsDiving() && W->GetWaspTarget() == Defender) { bThreat = true; return; }
		if (FVector::Dist(DL, W->GetActorLocation()) < Radius) { bThreat = true; }
	});
	return bThreat;
}
