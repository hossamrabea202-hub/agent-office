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
	Super::BeginPlay();   // runs the Blueprint's Event BeginPlay; registration below does not depend on it
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
	CurrentTarget = nullptr;
	Super::EndPlay(EndPlayReason);
}

bool AZombieBase::ReadBlueprintBool(const UObject* Object, FName Name, bool* bFound)
{
	if (bFound) { *bFound = false; }
	if (!IsValid(Object))
	{
		return false;
	}
	const FBoolProperty* Prop = FindFProperty<FBoolProperty>(Object->GetClass(), Name);
	if (bFound) { *bFound = Prop != nullptr; }
	return Prop && Prop->GetPropertyValue_InContainer(Object);
}

bool AZombieBase::IsDeadForCrowd() const
{
	bool bFound = false;
	const bool bDead = ReadBlueprintBool(this, TEXT("Dead"), &bFound);
	return bFound ? bDead : (IsActorBeingDestroyed() || !IsValid(this));
}

bool AZombieBase::IsEngagedForCrowd() const
{
	return !FMath::IsNearlyEqual(CustomTimeDilation, 1.f);
}

float AZombieBase::DistanceToPlayer() const
{
	const AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	// GetDistanceTo(None) is 0 in Blueprint: keep that, so a missing player counts as near.
	return Player ? GetDistanceTo(Player) : 0.f;
}

AZombieBase::FTargetRule::FTargetRule(const FVector& InSelf, const FVector* Player, float SoldierRange, float InSoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks)
	: Self(InSelf)
	, SoldierRangeSq(SoldierRange * SoldierRange)
	, SoldierHeightRange(InSoldierHeightRange)
	, FarmerRangeSq(FarmerRange * FarmerRange)
{
	// Blueprint parity: with no player, GetDistanceTo(None) = 0, so nothing is "nearer" and no soldier / farmer is picked.
	// bNoPlayerBlocks = false is the alternative (pick the nearest valid target); TGA's SPEC_zombie.md decides which is intended.
	BestDistSq = Player ? FVector::DistSquared(Self, *Player) : (bNoPlayerBlocks ? 0.f : TNumericLimits<float>::Max());
}

void AZombieBase::FTargetRule::ConsiderSoldier(int32 Index, const FVector& Location, bool bValid, bool bDying)
{
	if (!bValid || bDying || FMath::Abs(Location.Z - Self.Z) >= SoldierHeightRange)
	{
		return;
	}
	const float DistSq = FVector::DistSquared(Self, Location);
	if (DistSq < SoldierRangeSq && DistSq < BestDistSq)
	{
		Best = Index;
		BestDistSq = DistSq;
	}
}

void AZombieBase::FTargetRule::ConsiderFarmer(int32 Index, const FVector& Location, bool bValid, bool bDead)
{
	if (!bValid || bDead)
	{
		return;
	}
	const float DistSq = FVector::DistSquared(Self, Location);
	if (DistSq < FarmerRangeSq && DistSq < BestDistSq)
	{
		Best = Index;
		BestDistSq = DistSq;
	}
}

int32 AZombieBase::ChooseTarget(const FVector& Self, const FVector* Player, const TArray<FCandidate>& Soldiers, const TArray<FCandidate>& Farmers,
	float SoldierRange, float SoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks)
{
	FTargetRule Rule(Self, Player, SoldierRange, SoldierHeightRange, FarmerRange, bNoPlayerBlocks);
	for (int32 i = 0; i < Soldiers.Num(); ++i)
	{
		Rule.ConsiderSoldier(i, Soldiers[i].Location, Soldiers[i].bValid, Soldiers[i].bDyingOrDead);
	}
	for (int32 i = 0; i < Farmers.Num(); ++i)
	{
		Rule.ConsiderFarmer(Soldiers.Num() + i, Farmers[i].Location, Farmers[i].bValid, Farmers[i].bDyingOrDead);
	}
	return Rule.Best;
}

AActor* AZombieBase::FinishPick(AActor* Player, AActor* Picked)
{
	AActor* Best = Picked ? Picked : Player;
	CurrentTarget = Best;
	if (bAlsoSetOwner)
	{
		SetOwner(Best);
	}
	return Best;
}

// "Dying" for a soldier = a life span is set (Blueprint parity: GetLifeSpan < 0.01 means alive). Replace with an explicit state with ASoldierBase.
static bool IsSoldierDying(const AActor* Soldier) { return Soldier->GetLifeSpan() >= 0.01f; }

AActor* AZombieBase::PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers)
{
	CD_SCOPE(STAT_CD_PickTarget);
	const UCDSettings* S = GetDefault<UCDSettings>();
	AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const FVector PlayerLoc = Player ? Player->GetActorLocation() : FVector::ZeroVector;
	FTargetRule Rule(GetActorLocation(), Player ? &PlayerLoc : nullptr, S->ZombieSoldierRange, S->ZombieSoldierHeightRange, S->ZombieFarmerRange, S->bZombieNoPlayerBlocksTargets);
	for (int32 i = 0; i < Soldiers.Num(); ++i)
	{
		const AActor* A = Soldiers[i];
		if (IsValid(A)) { Rule.ConsiderSoldier(i, A->GetActorLocation(), true, IsSoldierDying(A)); }
	}
	for (int32 i = 0; i < Farmers.Num(); ++i)
	{
		const AActor* A = Farmers[i];
		if (IsValid(A)) { Rule.ConsiderFarmer(Soldiers.Num() + i, A->GetActorLocation(), true, ReadBlueprintBool(A, TEXT("Dead"))); }
	}
	AActor* Picked = Rule.Best == INDEX_NONE ? nullptr : (Rule.Best < Soldiers.Num() ? Soldiers[Rule.Best] : Farmers[Rule.Best - Soldiers.Num()]);
	return FinishPick(Player, Picked);
}

AActor* AZombieBase::PickAndSetTargetFromRegistry()
{
	CD_SCOPE(STAT_CD_PickTarget);
	const UCDSettings* S = GetDefault<UCDSettings>();
	AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this);
	if (!Crowd)
	{
		return FinishPick(Player, nullptr);
	}
	const FVector PlayerLoc = Player ? Player->GetActorLocation() : FVector::ZeroVector;
	FTargetRule Rule(GetActorLocation(), Player ? &PlayerLoc : nullptr, S->ZombieSoldierRange, S->ZombieSoldierHeightRange, S->ZombieFarmerRange, S->bZombieNoPlayerBlocksTargets);
	AActor* Picked = nullptr;
	int32 Index = 0;
	Crowd->ForEachSoldier([&](AActor* A)
	{
		const int32 Before = Rule.Best;
		Rule.ConsiderSoldier(Index++, A->GetActorLocation(), true, IsSoldierDying(A));
		if (Rule.Best != Before) { Picked = A; }
	});
	Crowd->ForEachFarmer([&](AActor* A)
	{
		const int32 Before = Rule.Best;
		Rule.ConsiderFarmer(Index++, A->GetActorLocation(), true, ReadBlueprintBool(A, TEXT("Dead")));
		if (Rule.Best != Before) { Picked = A; }
	});
	return FinishPick(Player, Picked);
}

int32 AZombieBase::GetThinkDivisor() const
{
	const UCDSettings* S = GetDefault<UCDSettings>();
	const float Dist = DistanceToPlayer();
	return Dist < S->ZombieNearPlayer ? 1 : (Dist < S->ZombieMidPlayer ? 2 : 4);
}

bool AZombieBase::IsFullDetail() const
{
	return DistanceToPlayer() < GetDefault<UCDSettings>()->ZombieNearPlayer || WasRecentlyRendered(0.2f);
}
