#include "CrowdSubsystem.h"
#include "ZombieBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

UCrowdSubsystem* UCrowdSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	return World ? World->GetSubsystem<UCrowdSubsystem>() : nullptr;
}

bool UCrowdSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UCrowdSubsystem::RegisterZombie(AZombieBase* Zombie)
{
	if (IsValid(Zombie))
	{
		Zombies.AddUnique(Zombie);
	}
}

void UCrowdSubsystem::UnregisterZombie(AZombieBase* Zombie)
{
	Zombies.Remove(Zombie);
}

int32 UCrowdSubsystem::GetAliveZombieCount() const
{
	int32 Count = 0;
	for (const TWeakObjectPtr<AZombieBase>& Weak : Zombies)
	{
		const AZombieBase* Zombie = Weak.Get();
		if (Zombie && !AZombieBase::ReadBlueprintBool(Zombie, TEXT("Dead")))
		{
			++Count;
		}
	}
	return Count;
}

void UCrowdSubsystem::GetZombiesNear(FVector Location, float Radius, TArray<AActor*>& OutZombies) const
{
	OutZombies.Reset();
	const float RadiusSq = Radius * Radius;
	for (const TWeakObjectPtr<AZombieBase>& Weak : Zombies)
	{
		AZombieBase* Zombie = Weak.Get();
		if (Zombie && FVector::DistSquared(Zombie->GetActorLocation(), Location) <= RadiusSq && !AZombieBase::ReadBlueprintBool(Zombie, TEXT("Dead")))
		{
			OutZombies.Add(Zombie);
		}
	}
}

void UCrowdSubsystem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	Zombies.RemoveAll([](const TWeakObjectPtr<AZombieBase>& Weak) { return !Weak.IsValid(); });

	Accum += DeltaTime;
	if (Accum < UpdateInterval)
	{
		return;
	}
	Accum = 0.f;
	if (bManageBodyCollision)
	{
		ApplyBodyCollisionRule();
	}
}

void UCrowdSubsystem::ApplyBodyCollisionRule()
{
	// Same rule as BPC_CrowdTier (crowd/README_C1.md): body collision on screen, near the player or soldier-engaged (CustomTimeDilation 0.999); off elsewhere.
	const AActor* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	const float RangeSq = FullDetailRange * FullDetailRange;
	for (const TWeakObjectPtr<AZombieBase>& Weak : Zombies)
	{
		AZombieBase* Zombie = Weak.Get();
		if (!Zombie || AZombieBase::ReadBlueprintBool(Zombie, TEXT("Dead")))
		{
			continue;
		}
		USkeletalMeshComponent* Mesh = Zombie->GetMesh();
		if (!Mesh)
		{
			continue;
		}
		const bool bNear = !Player || FVector::DistSquared(Zombie->GetActorLocation(), Player->GetActorLocation()) < RangeSq;
		const bool bFull = bNear || Zombie->WasRecentlyRendered(0.2f) || !FMath::IsNearlyEqual(Zombie->CustomTimeDilation, 1.f);
		Mesh->SetCollisionEnabled(bFull ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
	}
}

TStatId UCrowdSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UCrowdSubsystem, STATGROUP_Tickables);
}
