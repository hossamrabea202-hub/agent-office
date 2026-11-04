// #500 point 8: reuse short-lived actors (bolts, blood bursts, gore pieces) instead of spawning and destroying one per hit.
// Blueprint: "Acquire Pooled Actor" instead of SpawnActor, "Release Pooled Actor" instead of DestroyActor / SetLifeSpan.
// An actor class can implement ICDPoolable (OnAcquired / OnReleased) to reset itself. For Niagara / Cascade effects use the engine's own
// pooling instead: set PoolingMethod = AutoRelease on SpawnSystemAtLocation / SpawnEmitterAtLocation (all 49 spawners use None today, BP_AUDIT C).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "UObject/Interface.h"
#include "CDPoolSubsystem.generated.h"

UINTERFACE(BlueprintType)
class CASTLEDEFENDER_API UCDPoolable : public UInterface
{
	GENERATED_BODY()
};

class CASTLEDEFENDER_API ICDPoolable
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintNativeEvent, Category = "Pool")
	void OnAcquired();

	UFUNCTION(BlueprintNativeEvent, Category = "Pool")
	void OnReleased();
};

UCLASS()
class CASTLEDEFENDER_API UCDPoolSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Pool", meta = (DeterminesOutputType = "Class"))
	AActor* AcquirePooledActor(TSubclassOf<AActor> Class, const FTransform& Transform);

	// Hides the actor, turns off its collision and ticking, and keeps it for the next Acquire. LifeSeconds > 0: release after that delay.
	UFUNCTION(BlueprintCallable, Category = "Pool")
	void ReleasePooledActor(AActor* Actor, float LifeSeconds = 0.f);

	UFUNCTION(BlueprintPure, Category = "Pool")
	int32 GetPooledCount(TSubclassOf<AActor> Class) const;

	// Per class, at most this many are kept; extra releases are destroyed.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pool")
	int32 MaxPerClass = 64;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	void Park(AActor* Actor);

	TMap<UClass*, TArray<TWeakObjectPtr<AActor>>> Free;
};
