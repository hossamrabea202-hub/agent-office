#include "CrowdSubsystem.h"
#include "CDSettings.h"
#include "CDStats.h"
#include "ZombieBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"

DECLARE_CYCLE_STAT(TEXT("Crowd Tick"), STAT_CD_CrowdTick, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Crowd ZombiesNear"), STAT_CD_ZombiesNear, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("Zombies registered"), STAT_CD_Zombies, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("Soldiers registered"), STAT_CD_Soldiers, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("Farmers registered"), STAT_CD_Farmers, STATGROUP_CastleDefender);

static FAutoConsoleCommandWithWorld GCDCrowdReport(
	TEXT("cd.CrowdReport"),
	TEXT("Castle Defender: crowd registry counts against the actors really in the world."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
	{
		if (const UCrowdSubsystem* Crowd = World ? World->GetSubsystem<UCrowdSubsystem>() : nullptr)
		{
			Crowd->Report();
		}
	}));

UCrowdSubsystem* UCrowdSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	return World ? World->GetSubsystem<UCrowdSubsystem>() : nullptr;
}

bool UCrowdSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UCrowdSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	const UCDSettings* Settings = GetDefault<UCDSettings>();
	bManageBodyCollision = Settings->bCrowdManagesBodyCollision;
	FullDetailRange = Settings->CrowdFullDetailRange;
	UpdateInterval = FMath::Max(0.05f, Settings->CrowdUpdateInterval);
	FullDetailRange = FMath::Max(0.f, FullDetailRange);
	MaxAliveZombies = FMath::Max(0, Settings->MaxAliveZombies);   // values from .ini are not clamped by the editor UI
}

void UCrowdSubsystem::Deinitialize()
{
	RestoreAll();
	Super::Deinitialize();
}

void UCrowdSubsystem::RegisterZombie(AZombieBase* Zombie)
{
	if (IsValid(Zombie) && Zombie->GetWorld() == GetWorld())
	{
		Zombies.AddUnique(Zombie);
	}
}

void UCrowdSubsystem::UnregisterZombie(AZombieBase* Zombie)
{
	if (Zombie && !Zombie->IsDeadForCrowd() && !Relinquished.Contains(Zombie))
	{
		RestoreBodyCollision(Zombie);
	}
	OriginalCollision.Remove(Zombie);
	Relinquished.Remove(Zombie);
	Zombies.Remove(Zombie);
}

void UCrowdSubsystem::RelinquishBodyCollision(AZombieBase* Zombie)
{
	if (Zombie)
	{
		OriginalCollision.Remove(Zombie);
		Relinquished.Add(Zombie);
	}
}

void UCrowdSubsystem::RegisterSoldier(AActor* Soldier)
{
	if (IsValid(Soldier) && Soldier->GetWorld() == GetWorld())
	{
		Soldiers.AddUnique(Soldier);
	}
}

void UCrowdSubsystem::UnregisterSoldier(AActor* Soldier)
{
	Soldiers.Remove(Soldier);
}

void UCrowdSubsystem::RegisterFarmer(AActor* Farmer)
{
	if (IsValid(Farmer) && Farmer->GetWorld() == GetWorld())
	{
		Farmers.AddUnique(Farmer);
	}
}

void UCrowdSubsystem::UnregisterFarmer(AActor* Farmer)
{
	Farmers.Remove(Farmer);
}

TArray<AActor*> UCrowdSubsystem::GetSoldiers() const
{
	TArray<AActor*> Out;
	ForEachSoldier([&Out](AActor* A) { Out.Add(A); });
	return Out;
}

TArray<AActor*> UCrowdSubsystem::GetFarmers() const
{
	TArray<AActor*> Out;
	ForEachFarmer([&Out](AActor* A) { Out.Add(A); });
	return Out;
}

int32 UCrowdSubsystem::GetAliveZombieCount() const
{
	int32 Count = 0;
	for (const TWeakObjectPtr<AZombieBase>& Weak : Zombies)
	{
		const AZombieBase* Zombie = Weak.Get();
		if (Zombie && !Zombie->IsDeadForCrowd())
		{
			++Count;
		}
	}
	return Count;
}

bool UCrowdSubsystem::CanSpawnZombie() const
{
	return MaxAliveZombies <= 0 || GetAliveZombieCount() < MaxAliveZombies;
}

void UCrowdSubsystem::GetZombiesNear(FVector Location, float Radius, TArray<AActor*>& OutZombies) const
{
	CD_SCOPE(STAT_CD_ZombiesNear);
	OutZombies.Reset();
	if (!(Radius > 0.f))
	{
		return;   // negative, zero or NaN radius: nothing
	}
	const float RadiusSq = Radius * Radius;
	for (const TWeakObjectPtr<AZombieBase>& Weak : Zombies)
	{
		AZombieBase* Zombie = Weak.Get();
		if (Zombie && FVector::DistSquared(Zombie->GetActorLocation(), Location) <= RadiusSq && !Zombie->IsDeadForCrowd())
		{
			OutZombies.Add(Zombie);
		}
	}
}

void UCrowdSubsystem::SetManageBodyCollision(bool bOn)
{
	if (bManageBodyCollision && !bOn)
	{
		RestoreAll();
	}
	bManageBodyCollision = bOn;
}

void UCrowdSubsystem::PurgeInvalid()
{
	Zombies.RemoveAll([](const TWeakObjectPtr<AZombieBase>& Weak) { return !Weak.IsValid(); });
	Soldiers.RemoveAll([](const TWeakObjectPtr<AActor>& Weak) { return !Weak.IsValid(); });
	Farmers.RemoveAll([](const TWeakObjectPtr<AActor>& Weak) { return !Weak.IsValid(); });
	for (auto It = Relinquished.CreateIterator(); It; ++It)
	{
		if (!It->IsValid())
		{
			It.RemoveCurrent();
		}
	}
	for (auto It = OriginalCollision.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid())
		{
			It.RemoveCurrent();
		}
	}
}

void UCrowdSubsystem::Tick(float DeltaTime)
{
	// No Super::Tick: the base has nothing to do and the reviewer flagged it for 5.8.
	CD_SCOPE(STAT_CD_CrowdTick);
	Accum += DeltaTime;
	if (Accum < UpdateInterval)
	{
		return;
	}
	Accum = 0.f;
	PurgeInvalid();
	SET_DWORD_STAT(STAT_CD_Zombies, Zombies.Num());
	SET_DWORD_STAT(STAT_CD_Soldiers, Soldiers.Num());
	SET_DWORD_STAT(STAT_CD_Farmers, Farmers.Num());
	if (bManageBodyCollision)
	{
		ApplyBodyCollisionRule();
	}
}

void UCrowdSubsystem::RestoreBodyCollision(AZombieBase* Zombie)
{
	if (!Zombie)
	{
		return;
	}
	if (const TEnumAsByte<ECollisionEnabled::Type>* Original = OriginalCollision.Find(Zombie))
	{
		// Alive zombies only (callers check); only undo our own change (the mesh is still at the NoCollision we set).
		USkeletalMeshComponent* Mesh = Zombie->GetMesh();
		if (Mesh && !Mesh->IsSimulatingPhysics() && Mesh->GetCollisionEnabled() == ECollisionEnabled::NoCollision)
		{
			Mesh->SetCollisionEnabled(Original->GetValue());
		}
		OriginalCollision.Remove(Zombie);
	}
}

void UCrowdSubsystem::RestoreAll()
{
	for (const TWeakObjectPtr<AZombieBase>& Weak : Zombies)
	{
		AZombieBase* Zombie = Weak.Get();
		if (Zombie && !Zombie->IsDeadForCrowd() && !Relinquished.Contains(Zombie))
		{
			RestoreBodyCollision(Zombie);
		}
	}
	OriginalCollision.Reset();
	Relinquished.Reset();
}

void UCrowdSubsystem::ApplyBodyCollisionRule()
{
	// Same rule as BPC_CrowdTier (crowd/README_C1.md): body collision as the zombie had it on screen, near the player or engaged; off elsewhere.
	const AActor* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	const float RangeSq = FullDetailRange * FullDetailRange;
	for (const TWeakObjectPtr<AZombieBase>& Weak : Zombies)
	{
		AZombieBase* Zombie = Weak.Get();
		if (!Zombie)
		{
			continue;
		}
		USkeletalMeshComponent* Mesh = Zombie->GetMesh();
		if (!Mesh || Relinquished.Contains(Zombie))
		{
			continue;
		}
		if (Mesh->IsSimulatingPhysics() || Zombie->IsDeadForCrowd())
		{
			RelinquishBodyCollision(Zombie);   // dying / ragdoll: the death code owns the body from now on, nothing is restored
			continue;
		}
		const bool bNear = !Player || FVector::DistSquared(Zombie->GetActorLocation(), Player->GetActorLocation()) < RangeSq;
		const bool bFull = bNear || Zombie->WasRecentlyRendered(0.2f) || Zombie->IsEngagedForCrowd();
		if (bFull)
		{
			RestoreBodyCollision(Zombie);
		}
		else if (Mesh->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
		{
			OriginalCollision.FindOrAdd(Zombie, Mesh->GetCollisionEnabled());
			Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		}
	}
}

void UCrowdSubsystem::Report() const
{
	int32 WorldZombies = 0;
	for (TActorIterator<AZombieBase> It(GetWorld()); It; ++It)
	{
		++WorldZombies;
	}
	UE_LOG(LogTemp, Display, TEXT("cd.CrowdReport: zombies registered %d / in world %d (alive %d, cap %d) | soldiers %d | farmers %d | body collision managed %s, %d changed"),
		Zombies.Num(), WorldZombies, GetAliveZombieCount(), MaxAliveZombies, Soldiers.Num(), Farmers.Num(), bManageBodyCollision ? TEXT("yes") : TEXT("no"), OriginalCollision.Num());
}

TStatId UCrowdSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UCrowdSubsystem, STATGROUP_Tickables);
}
