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
	// start from the player; take a soldier that is not dying (LifeSpan < 0.01), within 250 cm height and 2500 cm, if nearer than the current pick;
	// then a farmer that is not Dead, within 2500 cm, if nearer. Sets the result as Owner (BP_Zombie uses Owner as its target) and returns it.
	UFUNCTION(BlueprintCallable, Category = "Zombie|Brain")
	AActor* PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers);

	// Think's "heavy part every Nth tick" divisor: 1 within 3000 cm of the player, 2 within 6000, else 4 (K2Node_IfThenElse_11).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	int32 GetThinkDivisor() const;

	// Near the player (3000 cm) or rendered in the last 0.2 s (K2Node_CallFunction_42 / _43).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	bool IsFullDetail() const;

	// Reads a Blueprint bool variable (for example "Dead") from any actor; false when missing.
	static bool ReadBlueprintBool(const UObject* Object, FName Name);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(EditDefaultsOnly, Category = "Zombie|Brain")
	float SoldierRange = 2500.f;

	UPROPERTY(EditDefaultsOnly, Category = "Zombie|Brain")
	float SoldierHeightRange = 250.f;

	UPROPERTY(EditDefaultsOnly, Category = "Zombie|Brain")
	float FarmerRange = 2500.f;

private:
	float DistanceToPlayer() const;
};
