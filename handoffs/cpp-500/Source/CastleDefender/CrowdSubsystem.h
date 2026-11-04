// #500: one native manager for all zombies (replaces per-zombie Blueprint polling step by step).
// - keeps the zombie list (AZombieBase registers itself), so nobody needs GetAllActorsOfClass;
// - optional: the C1 body-collision rule for every zombie in one loop (off by default while BPC_CrowdTier still does it);
// - GetZombiesNear: native radius query for soldiers (the C3 job, without a sphere sweep).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CrowdSubsystem.generated.h"

class AZombieBase;

UCLASS()
class CASTLEDEFENDER_API UCrowdSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	static UCrowdSubsystem* Get(const UObject* WorldContext);

	void RegisterZombie(AZombieBase* Zombie);
	void UnregisterZombie(AZombieBase* Zombie);

	UFUNCTION(BlueprintPure, Category = "Crowd")
	int32 GetAliveZombieCount() const;

	// Zombies (registered, not Dead) within Radius of Location. Native loop: ~100 zombies cost microseconds.
	UFUNCTION(BlueprintCallable, Category = "Crowd")
	void GetZombiesNear(FVector Location, float Radius, TArray<AActor*>& OutZombies) const;

	// When true, this subsystem applies the C1 rule to every zombie 4x a second, and BPC_CrowdTier can be removed from BP_Zombie.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Crowd")
	bool bManageBodyCollision = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Crowd")
	float FullDetailRange = 2500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Crowd")
	float UpdateInterval = 0.25f;

	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	void ApplyBodyCollisionRule();

	TArray<TWeakObjectPtr<AZombieBase>> Zombies;
	float Accum = 0.f;
};
