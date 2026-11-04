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

	// BP_Zombie Think's target pick (nodes CX_501..zfTargetFarmer17), in one native call. Same rules:
	// start from the player; take a soldier that is not dying (LifeSpan < 0.01), within ZombieSoldierHeightRange height and ZombieSoldierRange, if nearer than the current pick;
	// then a farmer that is not Dead, within ZombieFarmerRange, if nearer. Sets the result as Owner (BP_Zombie uses Owner as its target) and returns it.
	UFUNCTION(BlueprintCallable, Category = "Zombie|Brain")
	AActor* PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers);

	// The same, with soldiers and farmers from the crowd registry (no caches on the wave manager needed).
	UFUNCTION(BlueprintCallable, Category = "Zombie|Brain")
	AActor* PickAndSetTargetFromRegistry();

	// Think's "heavy part every Nth tick" divisor: 1 within ZombieNearPlayer, 2 within ZombieMidPlayer, else 4 (K2Node_IfThenElse_11).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	int32 GetThinkDivisor() const;

	// Near the player (ZombieNearPlayer) or rendered in the last 0.2 s (K2Node_CallFunction_42 / _43).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	bool IsFullDetail() const;

	// Reads a Blueprint bool variable (for example "Dead") from any actor; false when missing.
	static bool ReadBlueprintBool(const UObject* Object, FName Name);

	// Pure target rule, no world needed (unit-tested in Tests/ZombieBrainTest.cpp).
	struct FCandidate
	{
		FVector Location;
		bool bValid = true;
		bool bDyingOrDead = false;
	};
	// Returns the index of the chosen candidate in Soldiers (0..) or Farmers (Soldiers.Num()..), or INDEX_NONE for "keep the player".
	static int32 ChooseTarget(const FVector& Self, const FVector* Player, const TArray<FCandidate>& Soldiers, const TArray<FCandidate>& Farmers,
		float SoldierRange, float SoldierHeightRange, float FarmerRange);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	float DistanceToPlayer() const;
};
