// #500: one native registry and manager for the battle (point 4, shared systems): zombies, soldiers and farmers register here once,
// so no Blueprint needs GetAllActorsOfClass / GetAllActorsWithTag to find them again.
// - zombies register themselves (AZombieBase, in its native BeginPlay / EndPlay: Blueprint children need no "call parent" for this);
// - soldiers and farmers call RegisterSoldier / RegisterFarmer from their BeginPlay and EndPlay until they get C++ parents;
// - optional: the C1 body-collision rule for every zombie in one loop (off by default while BPC_CrowdTier still does it).
//   It remembers each zombie's own collision setting and puts it back when the zombie comes into full detail again, unregisters ALIVE, or the rule is
//   switched off. The moment a zombie is dying or dead it lets go WITHOUT restoring anything: from then on the death code owns the body collision
//   (call AZombieBase::NotifyDying at the start of the death transition, before the death code sets its collision; the crowd also detects Dead itself);
// - native radius queries (the C3 job, without a sphere sweep);
// - `cd.CrowdReport` (console): registry counts against the actors really in the world, to catch a spawn path that does not register.
#pragma once

#include "CoreMinimal.h"
#include "Engine/EngineTypes.h"
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

	// Death transition starts: stop managing this zombie's body collision and forget its stored setting (nothing is restored).
	void RelinquishBodyCollision(AZombieBase* Zombie);

	// Soldiers / farmers are still pure Blueprints: call these from their BeginPlay and EndPlay (every spawn path).
	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Soldier"))
	void RegisterSoldier(AActor* Soldier);

	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Soldier"))
	void UnregisterSoldier(AActor* Soldier);

	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Farmer"))
	void RegisterFarmer(AActor* Farmer);

	UFUNCTION(BlueprintCallable, Category = "Crowd", meta = (DefaultToSelf = "Farmer"))
	void UnregisterFarmer(AActor* Farmer);

	// Copies for Blueprint. C++ should use ForEachSoldier / ForEachFarmer (no array per call).
	UFUNCTION(BlueprintCallable, Category = "Crowd")
	TArray<AActor*> GetSoldiers() const;

	UFUNCTION(BlueprintCallable, Category = "Crowd")
	TArray<AActor*> GetFarmers() const;

	template <typename F> void ForEachSoldier(F&& Fn) const { for (const TWeakObjectPtr<AActor>& W : Soldiers) { if (AActor* A = W.Get()) { Fn(A); } } }
	template <typename F> void ForEachFarmer(F&& Fn) const { for (const TWeakObjectPtr<AActor>& W : Farmers) { if (AActor* A = W.Get()) { Fn(A); } } }
	// Every registered zombie, dead or alive (same set GetAllActorsOfClass would return for AZombieBase classes).
	template <typename F> void ForEachZombie(F&& Fn) const { for (const TWeakObjectPtr<AZombieBase>& W : Zombies) { if (AZombieBase* Z = W.Get()) { Fn(Z); } } }

	// Registered zombies that are not dead (see AZombieBase::IsDeadForCrowd).
	UFUNCTION(BlueprintPure, Category = "Crowd")
	int32 GetAliveZombieCount() const;

	// False when MaxAliveZombies (Project Settings > Castle Defender) is reached. Spawners call this before SpawnActor.
	UFUNCTION(BlueprintPure, Category = "Crowd")
	bool CanSpawnZombie() const;

	// Zombies (registered, not dead) within Radius of Location.
	UFUNCTION(BlueprintCallable, Category = "Crowd")
	void GetZombiesNear(FVector Location, float Radius, TArray<AActor*>& OutZombies) const;

	// When true, the C1 rule runs here for every zombie; then BPC_CrowdTier can be removed from BP_Zombie. Switching it off restores every zombie.
	UFUNCTION(BlueprintCallable, Category = "Crowd")
	void SetManageBodyCollision(bool bOn);

	UFUNCTION(BlueprintPure, Category = "Crowd")
	bool GetManageBodyCollision() const { return bManageBodyCollision; }

	void Report() const;

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	void ApplyBodyCollisionRule();
	void RestoreBodyCollision(AZombieBase* Zombie);   // alive zombies only
	void RestoreAll();
	void PurgeInvalid();

	TArray<TWeakObjectPtr<AZombieBase>> Zombies;
	TArray<TWeakObjectPtr<AActor>> Soldiers;
	TArray<TWeakObjectPtr<AActor>> Farmers;
	// The collision each zombie's mesh had before this subsystem first changed it.
	TMap<TWeakObjectPtr<AZombieBase>, TEnumAsByte<ECollisionEnabled::Type>> OriginalCollision;
	// Zombies whose body collision now belongs to their death code.
	TSet<TWeakObjectPtr<AZombieBase>> Relinquished;

	bool bManageBodyCollision = false;
	float FullDetailRange = 2500.f;
	float UpdateInterval = 0.25f;
	int32 MaxAliveZombies = 60;
	float Accum = 0.f;
};
