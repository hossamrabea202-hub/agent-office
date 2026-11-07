#include "CDPerfTuning.h"
#include "CDStats.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "ProfilingDebugging/CsvProfiler.h"

DECLARE_CYCLE_STAT(TEXT("Perf tuning LOD"), STAT_CD_PerfTuning, STATGROUP_CastleDefender);
CSV_DEFINE_CATEGORY(CastleDefender, true);

namespace CDPerf
{
	// Nothing changes unless cd.Perf.Enable is 1 AND the individual rule is on. Everything is applied and reverted live (4x per second),
	// so the CSV profiler's A/B mode can flip cd.Perf.Enable inside one run: -csvABTest="cd.Perf.Enable=0,1".
	int32 Enable = 0;
	int32 SoldierDriverMeshNoCollision = 1;
	int32 SoldierURO = 1;
	int32 ZombieSkipFloorChecks = 1;
	float ZombieBodyLODDistance = 3500.f;
	float ZombieMoveTickLODDistance = 4000.f;
	// Measuring only: > 0 flips Enable every ABPeriod seconds and writes CastleDefender/PerfEnable to the CSV each frame, so on / off can be
	// compared inside one run under the same load (the engine's -csvABTest cannot see cvars of game modules: they load after it starts).
	float ABPeriod = 0.f;

	FAutoConsoleVariableRef CVar0(TEXT("cd.Perf.Enable"), Enable, TEXT("Master switch for the Castle Defender crowd perf rules (0 = everything as authored)."));
	FAutoConsoleVariableRef CVar1(TEXT("cd.Perf.SoldierDriverMeshNoCollision"), SoldierDriverMeshNoCollision, TEXT("Soldiers' hidden CharacterMesh0: NoCollision while alive."));
	FAutoConsoleVariableRef CVar2(TEXT("cd.Perf.SoldierURO"), SoldierURO, TEXT("Update-rate optimisation on soldiers' skeletal meshes."));
	FAutoConsoleVariableRef CVar3(TEXT("cd.Perf.ZombieSkipFloorChecks"), ZombieSkipFloorChecks, TEXT("Zombies' CharacterMovement bAlwaysCheckFloor off."));
	FAutoConsoleVariableRef CVar4(TEXT("cd.Perf.ZombieBodyLODDistance"), ZombieBodyLODDistance, TEXT("Zombie mesh collision off beyond this distance from the player, cm (0 = off)."));
	FAutoConsoleVariableRef CVar6(TEXT("cd.Perf.ABPeriod"), ABPeriod, TEXT("Measuring only: flip cd.Perf.Enable every this many seconds (0 = off)."));
	FAutoConsoleVariableRef CVar5(TEXT("cd.Perf.ZombieMoveTickLODDistance"), ZombieMoveTickLODDistance, TEXT("Unrendered zombies beyond this distance tick movement at 10 Hz, cm (0 = off)."));

	// Blueprint classes are matched by the name of the class or any Blueprint parent, so children (BP_ZombieRisen, ...) count too.
	bool ClassChainStartsWith(const UClass* Class, const TCHAR* Prefix)
	{
		for (; Class; Class = Class->GetSuperClass())
		{
			if (Class->GetName().StartsWith(Prefix)) { return true; }
		}
		return false;
	}

	bool IsRagdollOrDying(const USkeletalMeshComponent* Mesh)
	{
		return !Mesh || Mesh->IsSimulatingPhysics() || Mesh->GetCollisionProfileName() == TEXT("Ragdoll");
	}

	bool IsDeadBlueprintFlag(const AActor* Actor)
	{
		const FBoolProperty* Dead = FindFProperty<FBoolProperty>(Actor->GetClass(), TEXT("Dead"));
		return Dead && Dead->GetPropertyValue_InContainer(Actor);
	}
}

static FAutoConsoleCommandWithWorld GCDPerfReport(TEXT("cd.Perf.Report"), TEXT("Castle Defender: what the perf tuning rules changed."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
	{
		if (const UCDPerfTuning* T = World ? World->GetSubsystem<UCDPerfTuning>() : nullptr) { T->Report(); }
	}));

bool UCDPerfTuning::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UCDPerfTuning::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	SpawnHandle = InWorld.AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UCDPerfTuning::OnActorSpawned));
	for (TActorIterator<ACharacter> It(&InWorld); It; ++It)
	{
		Consider(*It);
	}
}

void UCDPerfTuning::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(SpawnHandle);
	}
	Super::Deinitialize();
}

void UCDPerfTuning::OnActorSpawned(AActor* Actor)
{
	Consider(Actor);   // only remembered here; rules are applied on the next update, after the Blueprint's own BeginPlay
}

void UCDPerfTuning::Consider(AActor* Actor)
{
	ACharacter* Character = Cast<ACharacter>(Actor);
	if (!IsValid(Character) || Character->IsActorBeingDestroyed())
	{
		return;
	}
	if (CDPerf::ClassChainStartsWith(Character->GetClass(), TEXT("BP_SoldierSword")))
	{
		Soldiers.Add(Character);
	}
	else if (CDPerf::ClassChainStartsWith(Character->GetClass(), TEXT("BP_Zombie")))
	{
		Zombies.Add(Character);
	}
}

void UCDPerfTuning::Tick(float DeltaTime)
{
	if (CDPerf::ABPeriod > 0.f)
	{
		ABAccum += DeltaTime;
		if (ABAccum >= CDPerf::ABPeriod)
		{
			ABAccum = 0.f;
			CDPerf::Enable = CDPerf::Enable ? 0 : 1;
			Accum = 1.f;   // apply the new state on this frame
		}
	}
	CSV_CUSTOM_STAT(CastleDefender, PerfEnable, CDPerf::Enable, ECsvCustomStatOp::Set);
	Accum += DeltaTime;
	if (Accum < 0.25f)
	{
		return;
	}
	Accum = 0.f;
	CD_SCOPE(STAT_CD_PerfTuning);
	Soldiers.RemoveAll([](const TWeakObjectPtr<ACharacter>& W) { return !W.IsValid(); });
	Zombies.RemoveAll([](const TWeakObjectPtr<ACharacter>& W) { return !W.IsValid(); });
	UpdateSoldiers();
	UpdateZombies();
}

void UCDPerfTuning::SetBodyOff(ACharacter* C, bool bOff)
{
	USkeletalMeshComponent* Mesh = C->GetMesh();
	if (!Mesh)
	{
		return;
	}
	if (bOff && !BodiesOff.Contains(C) && Mesh->GetCollisionEnabled() == ECollisionEnabled::QueryOnly)
	{
		Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		BodiesOff.Add(C);
	}
	else if (!bOff && BodiesOff.Contains(C))
	{
		// Only undo our own change: if the Blueprint set a profile meanwhile (death ragdoll), leave it.
		if (Mesh->GetCollisionEnabled() == ECollisionEnabled::NoCollision && !CDPerf::IsRagdollOrDying(Mesh))
		{
			Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		}
		BodiesOff.Remove(C);
	}
}

void UCDPerfTuning::UpdateSoldiers()
{
	for (const TWeakObjectPtr<ACharacter>& W : Soldiers)
	{
		ACharacter* S = W.Get();
		if (!S || S->IsActorBeingDestroyed())
		{
			continue;
		}
		const bool bDying = CDPerf::IsRagdollOrDying(S->GetMesh()) || CDPerf::IsDeadBlueprintFlag(S);
		if (bDying)
		{
			BodiesOff.Remove(S);   // the death code owns the body now
		}
		else
		{
			SetBodyOff(S, CDPerf::Enable && CDPerf::SoldierDriverMeshNoCollision);
		}
		const bool bURO = CDPerf::Enable && CDPerf::SoldierURO;
		TInlineComponentArray<USkeletalMeshComponent*> Meshes(S);
		for (USkeletalMeshComponent* M : Meshes)
		{
			bool* Original = OriginalURO.Find(M);
			if (bURO && !Original)
			{
				OriginalURO.Add(M, M->bEnableUpdateRateOptimizations);
				M->bEnableUpdateRateOptimizations = true;   // tick option left as authored: the driver mesh is never rendered
			}
			else if (!bURO && Original)
			{
				M->bEnableUpdateRateOptimizations = *Original;
				OriginalURO.Remove(M);
			}
		}
	}
	for (auto It = OriginalURO.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid()) { It.RemoveCurrent(); }
	}
}

void UCDPerfTuning::UpdateZombies()
{
	const APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	const float BodySq = FMath::Square(CDPerf::ZombieBodyLODDistance);
	const float MoveSq = FMath::Square(CDPerf::ZombieMoveTickLODDistance);
	for (const TWeakObjectPtr<ACharacter>& W : Zombies)
	{
		ACharacter* Z = W.Get();
		USkeletalMeshComponent* Mesh = Z ? Z->GetMesh() : nullptr;
		if (!Mesh || Z->IsActorBeingDestroyed())
		{
			continue;
		}
		const bool bDying = CDPerf::IsRagdollOrDying(Mesh) || CDPerf::IsDeadBlueprintFlag(Z);
		const float DistSq = Player ? FVector::DistSquared(Z->GetActorLocation(), Player->GetActorLocation()) : 0.f;

		// Body collision: off when far, back on when near or when the rules are switched off. Never touched once dying.
		if (bDying)
		{
			BodiesOff.Remove(Z);
		}
		else
		{
			SetBodyOff(Z, CDPerf::Enable && CDPerf::ZombieBodyLODDistance > 0.f && Player && DistSq > BodySq);
		}

		if (UCharacterMovementComponent* Move = Z->GetCharacterMovement())
		{
			// Floor checks: bAlwaysCheckFloor is true on every zombie as authored; restore exactly that.
			Move->bAlwaysCheckFloor = !(CDPerf::Enable && CDPerf::ZombieSkipFloorChecks);

			// Movement tick rate: 10 Hz only when far AND not seen recently.
			const bool bWantSlow = CDPerf::Enable && !bDying && CDPerf::ZombieMoveTickLODDistance > 0.f && Player && DistSq > MoveSq && !Z->WasRecentlyRendered(0.25f);
			if (bWantSlow && !SlowMovers.Contains(Z))
			{
				Move->SetComponentTickInterval(0.1f);
				SlowMovers.Add(Z);
			}
			else if (!bWantSlow && SlowMovers.Contains(Z))
			{
				Move->SetComponentTickInterval(0.f);
				SlowMovers.Remove(Z);
			}
		}
	}
	for (auto It = BodiesOff.CreateIterator(); It; ++It) { if (!It->IsValid()) { It.RemoveCurrent(); } }
	for (auto It = SlowMovers.CreateIterator(); It; ++It) { if (!It->IsValid()) { It.RemoveCurrent(); } }
}

void UCDPerfTuning::Report() const
{
	UE_LOG(LogTemp, Display, TEXT("cd.Perf.Report: enable %d | soldiers %d | zombies %d | bodies off %d | slow movers %d | URO changed %d | rules: driverNoCol %d uro %d floor %d bodyLOD %.0f moveLOD %.0f"),
		CDPerf::Enable, Soldiers.Num(), Zombies.Num(), BodiesOff.Num(), SlowMovers.Num(), OriginalURO.Num(), CDPerf::SoldierDriverMeshNoCollision, CDPerf::SoldierURO,
		CDPerf::ZombieSkipFloorChecks, CDPerf::ZombieBodyLODDistance, CDPerf::ZombieMoveTickLODDistance);
}

TStatId UCDPerfTuning::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UCDPerfTuning, STATGROUP_Tickables);
}
