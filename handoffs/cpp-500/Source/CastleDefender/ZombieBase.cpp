#include "ZombieBase.h"
#include "CDSettings.h"
#include "CDStats.h"
#include "CrowdSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"

DECLARE_CYCLE_STAT(TEXT("Zombie PickTarget"), STAT_CD_PickTarget, STATGROUP_CastleDefender);

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

int32 AZombieBase::ChooseTarget(const FVector& Self, const FVector* Player, const TArray<FCandidate>& Soldiers, const TArray<FCandidate>& Farmers,
	float SoldierRange, float SoldierHeightRange, float FarmerRange)
{
	int32 Best = INDEX_NONE;
	float BestDist = Player ? FVector::Dist(Self, *Player) : 0.f;
	for (int32 i = 0; i < Soldiers.Num(); ++i)
	{
		const FCandidate& S = Soldiers[i];
		if (!S.bValid || S.bDyingOrDead || FMath::Abs(S.Location.Z - Self.Z) >= SoldierHeightRange)
		{
			continue;
		}
		const float Dist = FVector::Dist(Self, S.Location);
		if (Dist < SoldierRange && Dist < BestDist)
		{
			Best = i;
			BestDist = Dist;
		}
	}
	for (int32 i = 0; i < Farmers.Num(); ++i)
	{
		const FCandidate& F = Farmers[i];
		if (!F.bValid || F.bDyingOrDead)
		{
			continue;
		}
		const float Dist = FVector::Dist(Self, F.Location);
		if (Dist < FarmerRange && Dist < BestDist)
		{
			Best = Soldiers.Num() + i;
			BestDist = Dist;
		}
	}
	return Best;
}

AActor* AZombieBase::PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers)
{
	CD_SCOPE(STAT_CD_PickTarget);
	const UCDSettings* Settings = GetDefault<UCDSettings>();
	AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const FVector PlayerLoc = Player ? Player->GetActorLocation() : FVector::ZeroVector;

	TArray<FCandidate> S, F;
	S.Reserve(Soldiers.Num());
	F.Reserve(Farmers.Num());
	for (const AActor* A : Soldiers)
	{
		// Soldier "dying" = LifeSpan set (BP_Zombie: GetLifeSpan < 0.01 means alive).
		S.Add({ IsValid(A) ? A->GetActorLocation() : FVector::ZeroVector, IsValid(A), IsValid(A) && A->GetLifeSpan() >= 0.01f });
	}
	for (const AActor* A : Farmers)
	{
		F.Add({ IsValid(A) ? A->GetActorLocation() : FVector::ZeroVector, IsValid(A), ReadBlueprintBool(A, TEXT("Dead")) });
	}
	const int32 Pick = ChooseTarget(GetActorLocation(), Player ? &PlayerLoc : nullptr, S, F,
		Settings->ZombieSoldierRange, Settings->ZombieSoldierHeightRange, Settings->ZombieFarmerRange);
	AActor* Best = Pick == INDEX_NONE ? Player : (Pick < Soldiers.Num() ? Soldiers[Pick] : Farmers[Pick - Soldiers.Num()]);
	SetOwner(Best);
	return Best;
}

AActor* AZombieBase::PickAndSetTargetFromRegistry()
{
	UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this);
	return Crowd ? PickAndSetTarget(Crowd->GetSoldiers(), Crowd->GetFarmers()) : PickAndSetTarget({}, {});
}

int32 AZombieBase::GetThinkDivisor() const
{
	const UCDSettings* Settings = GetDefault<UCDSettings>();
	const float Dist = DistanceToPlayer();
	return Dist < Settings->ZombieNearPlayer ? 1 : (Dist < Settings->ZombieMidPlayer ? 2 : 4);
}

bool AZombieBase::IsFullDetail() const
{
	return DistanceToPlayer() < GetDefault<UCDSettings>()->ZombieNearPlayer || WasRecentlyRendered(0.2f);
}
