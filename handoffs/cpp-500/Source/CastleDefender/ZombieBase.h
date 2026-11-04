// #500: C++ parent for BP_Zombie. Holds the per-Think hot loops natively; BP_Zombie keeps its look, attacks, montages and states.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "ZombieBase.generated.h"

UCLASS(Abstract, Blueprintable)
class CASTLEDEFENDER_API AZombieBase : public ACharacter
{
	GENERATED_BODY()

public:
	AZombieBase();

	// BP_Zombie Think's target pick (nodes CX_501..zfTargetFarmer17), in one native call. Same rules as the live graph:
	// start from the player; a soldier that is not dying (LifeSpan < 0.01), within ZombieSoldierHeightRange height and ZombieSoldierRange, if strictly nearer;
	// then a farmer that is not Dead, within ZombieFarmerRange, if strictly nearer (equal distance: the earlier pick wins, soldiers before farmers).
	// Writes CurrentTarget. While BP_Zombie still reads GetOwner() as its target, it also sets Owner (bAlsoSetOwner); drop that once the Blueprint reads CurrentTarget.
	UFUNCTION(BlueprintCallable, Category = "Zombie|Brain")
	AActor* PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers);

	// The same, reading soldiers and farmers straight from the crowd registry (no arrays built per call).
	UFUNCTION(BlueprintCallable, Category = "Zombie|Brain")
	AActor* PickAndSetTargetFromRegistry();

	// The current target, or null if it was destroyed since the pick (weak reference: a dead target is never kept alive).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	AActor* GetCurrentTarget() const { AActor* T = CurrentTarget.Get(); return IsValid(T) ? T : nullptr; }

	// Call at the START of the death transition (before the death code sets its collision): the crowd manager stops touching this body.
	UFUNCTION(BlueprintCallable, Category = "Zombie|Crowd")
	void NotifyDying();

	// Think's "heavy part every Nth tick" divisor: 1 within ZombieNearPlayer, 2 within ZombieMidPlayer, else 4 (K2Node_IfThenElse_11).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	int32 GetThinkDivisor() const;

	// Near the player (ZombieNearPlayer) or rendered in the last 0.2 s (K2Node_CallFunction_42 / _43).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	bool IsFullDetail() const;

	// Dead for the crowd's purposes: being destroyed, or NotifyDying was called, or the Blueprint bool "Dead" is true. Override when a C++ death state exists.
	virtual bool IsDeadForCrowd() const;

	// Engaged by a soldier. Today BP_SoldierSword marks its zombie with CustomTimeDilation 0.999 (fragile; replace with an explicit state later).
	virtual bool IsEngagedForCrowd() const;

	// Reads a Blueprint bool variable from any object. bFound tells whether the variable exists.
	static bool ReadBlueprintBool(const UObject* Object, FName Name, bool* bFound = nullptr);

	// The pure target rule (no world), shared by PickAndSetTarget and the unit tests. Feed candidates with Consider(); Best is the chosen index or INDEX_NONE.
	struct FTargetRule
	{
		FVector Self;
		float BestDistSq;
		float SoldierRangeSq, SoldierHeightRange, FarmerRangeSq;
		int32 Best = INDEX_NONE;

		FTargetRule(const FVector& InSelf, const FVector* Player, float SoldierRange, float InSoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks);
		void ConsiderSoldier(int32 Index, const FVector& Location, bool bValid, bool bDying);
		void ConsiderFarmer(int32 Index, const FVector& Location, bool bValid, bool bDead);
	};

	// Test helper: candidates as plain data. Returns the chosen index in Soldiers (0..), Farmers (Soldiers.Num()..), or INDEX_NONE (keep the player).
	struct FCandidate
	{
		FVector Location;
		bool bValid = true;
		bool bDyingOrDead = false;
	};
	static int32 ChooseTarget(const FVector& Self, const FVector* Player, const TArray<FCandidate>& Soldiers, const TArray<FCandidate>& Farmers,
		float SoldierRange, float SoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks = true);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	TWeakObjectPtr<AActor> CurrentTarget;
	bool bDying = false;

	// Transition: BP_Zombie still uses Owner as its target slot. Turn off when the Blueprint reads CurrentTarget (Owner also drives net ownership).
	UPROPERTY(EditDefaultsOnly, Category = "Zombie|Brain")
	bool bAlsoSetOwner = true;

private:
	float DistanceToPlayer() const;
	AActor* FinishPick(AActor* Player, AActor* Picked);
};
