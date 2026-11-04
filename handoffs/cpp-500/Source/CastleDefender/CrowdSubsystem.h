// #500: one native registry and manager for the battle (point 4, shared systems): zombies, soldiers and farmers register here once,
// so no Blueprint needs GetAllActorsOfClass / GetAllActorsWithTag to find them again.
// - zombies register themselves (AZombieBase); soldiers and farmers call RegisterSoldier / RegisterFarmer from their BeginPlay until they get C++ parents;
// - optional: the C1 body-collision rule for every zombie in one loop (off by default while BPC_CrowdTier still does it);
// - native radius queries (the C3 job, without a sphere sweep).
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

	// Soldiers / farmers are still pure Blueprints: call these from their BeginPlay and EndPlay.
	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Soldier"))
	void RegisterSoldier(AActor* Soldier);

	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Soldier"))
	void UnregisterSoldier(AActor* Soldier);

	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Farmer"))
	void RegisterFarmer(AActor* Farmer);

	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Farmer"))
	void UnregisterFarmer(AActor* Farmer);

	UFUNCTION(BlueprintPure, Category = "Crowd")
	TArray<AActor*> GetSoldiers() const;

	UFUNCTION(BlueprintPure, Category = "Crowd")
	TArray<AActor*> GetFarmers() const;

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

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	void ApplyBodyCollisionRule();
	static TArray<AActor*> Resolve(const TArray<TWeakObjectPtr<AActor>>& List);

	TArray<TWeakObjectPtr<AZombieBase>> Zombies;
	TArray<TWeakObjectPtr<AActor>> Soldiers;
	TArray<TWeakObjectPtr<AActor>> Farmers;
	float Accum = 0.f;
};
