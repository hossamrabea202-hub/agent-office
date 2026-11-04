#include "ZombieBase.h"
#include "CrowdSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"

AZombieBase::AZombieBase()
{
	PrimaryActorTick.bCanEverTick = true;
}

void AZombieBase::BeginPlay()
{
	Super::BeginPlay();
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->RegisterZombie(this);
	}
}

void AZombieBase::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->UnregisterZombie(this);
	}
	Super::EndPlay(EndPlayReason);
}

bool AZombieBase::ReadBlueprintBool(const UObject* Object, FName Name)
{
	if (!IsValid(Object))
	{
		return false;
	}
	const FBoolProperty* Prop = FindFProperty<FBoolProperty>(Object->GetClass(), Name);
	return Prop && Prop->GetPropertyValue_InContainer(Object);
}

float AZombieBase::DistanceToPlayer() const
{
	const AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	// GetDistanceTo(None) is 0 in Blueprint: keep that, so a missing player counts as near.
	return Player ? GetDistanceTo(Player) : 0.f;
}

AActor* AZombieBase::PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers)
{
	AActor* Best = UGameplayStatics::GetPlayerCharacter(this, 0);
	float BestDist = Best ? GetDistanceTo(Best) : 0.f;
	const float MyZ = GetActorLocation().Z;

	for (AActor* Soldier : Soldiers)
	{
		if (!IsValid(Soldier) || Soldier->GetLifeSpan() >= 0.01f)
		{
			continue;
		}
		if (FMath::Abs(Soldier->GetActorLocation().Z - MyZ) >= SoldierHeightRange)
		{
			continue;
		}
		const float Dist = GetDistanceTo(Soldier);
		if (Dist < SoldierRange && Dist < BestDist)
		{
			Best = Soldier;
			BestDist = Dist;
		}
	}

	for (AActor* Farmer : Farmers)
	{
		if (!IsValid(Farmer) || ReadBlueprintBool(Farmer, TEXT("Dead")))
		{
			continue;
		}
		const float Dist = GetDistanceTo(Farmer);
		if (Dist < FarmerRange && Dist < BestDist)
		{
			Best = Farmer;
			BestDist = Dist;
		}
	}

	SetOwner(Best);
	return Best;
}

int32 AZombieBase::GetThinkDivisor() const
{
	const float Dist = DistanceToPlayer();
	return Dist < 3000.f ? 1 : (Dist < 6000.f ? 2 : 4);
}

bool AZombieBase::IsFullDetail() const
{
	return DistanceToPlayer() < 3000.f || WasRecentlyRendered(0.2f);
}
