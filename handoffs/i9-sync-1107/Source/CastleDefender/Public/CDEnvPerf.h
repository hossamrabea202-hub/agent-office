// Environment perf (2026-11-06 night). The frame dump showed about 170 Cascade fire components (torches, gate fires) ticking all the time, seen or not,
// and idle jelly mines and blobs ticking every frame. Fire outside the view is hidden and stopped, and comes back before it enters the view.
// Mines and blobs tick less often. Switch: cd.Perf.Env 0 restores everything.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDEnvPerf.generated.h"

class UParticleSystemComponent;

UCLASS()
class CASTLEDEFENDER_API UCDEnvPerfSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()
public:
	virtual bool DoesSupportWorldType(const EWorldType::Type T) const override { return T == EWorldType::Game || T == EWorldType::PIE; }
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UCDEnvPerfSubsystem, STATGROUP_Tickables); }

private:
	TArray<TWeakObjectPtr<UParticleSystemComponent>> Fires;
	TSet<TWeakObjectPtr<UParticleSystemComponent>> Off;
	FDelegateHandle SpawnHandle;
	double NextUpdate = 0.0, NextList = 0.0;
	void OnSpawned(AActor* A);
	void SlowTick(AActor* A);
	void RefreshList();
	void SetFire(UParticleSystemComponent* C, bool bOn);
};
