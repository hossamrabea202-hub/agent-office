// #500 point 8: reuse short-lived actors (bolts, blood bursts, gore pieces) instead of spawning and destroying one per hit.
// Blueprint: "Acquire Pooled Actor" instead of SpawnActor, "Release Pooled Actor" instead of DestroyActor / SetLifeSpan.
//
// RESET CONTRACT: only classes that implement ICDPoolable are pooled. OnAcquired must bring the actor back to a just-spawned state
// (BeginPlay does NOT run again): health / damage state, velocity, projectile movement, ignored actors, attached children, effects, delegates.
// OnReleased must stop everything it started, INCLUDING timers set by its components or by other objects for it: the pool only clears timers bound
// to the actor object itself (ClearAllTimersForObject). The pool also: clears the life span, zeroes physics velocity, stops and DEACTIVATES active
// movement components, turns off every component tick (actor tick and component ticks are separate in Unreal), and remembers the actor's own
// hidden / tick / collision values before turning collision off, tick off and hiding it. On Acquire it re-enables exactly those component ticks and
// re-activates exactly those movers, calls OnAcquired while the actor is still hidden and without collision, then puts back the actor's own
// visibility and tick, and its collision LAST (so overlaps never see old state).
// Component Activate / Deactivate can run callbacks that call back into the pool: no record reference is held across them; the record is looked
// up again and its generation checked after every such call.
// A class without ICDPoolable is spawned normally by Acquire and destroyed by Release: never pooled.
//
// Lifecycle per actor: Active -> (Release with delay) PendingRelease -> Pooled -> (Acquire) Active ... Each Acquire bumps a generation number;
// a delayed release only parks the actor if it is still the same generation and still pending, so an old timer can never park a reused actor.
//
// Niagara / Cascade effects: use the engine's pooling instead (PoolingMethod = AutoRelease on SpawnSystemAtLocation / SpawnEmitterAtLocation).
#pragma once

#include "CoreMinimal.h"
#include "Engine/TimerHandle.h"
#include "Subsystems/WorldSubsystem.h"
#include "UObject/Interface.h"
#include "CDPoolSubsystem.generated.h"

UINTERFACE(BlueprintType, Blueprintable)
class CASTLEDEFENDER_API UCDPoolable : public UInterface
{
	GENERATED_BODY()
};

class CASTLEDEFENDER_API ICDPoolable
{
	GENERATED_BODY()

public:
	// Reset to a just-spawned state (see the contract above).
	UFUNCTION(BlueprintNativeEvent, Category = "Pool")
	void OnAcquired();

	// Stop everything this actor started (sounds, effects, timers it owns elsewhere).
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

	// Active actor only (a second release, or a release of something this pool did not hand out, is ignored with a warning).
	// LifeSeconds > 0: release after that delay. Non-poolable classes are destroyed.
	UFUNCTION(BlueprintCallable, Category = "Pool")
	void ReleasePooledActor(AActor* Actor, float LifeSeconds = 0.f);

	UFUNCTION(BlueprintPure, Category = "Pool")
	int32 GetPooledCount(TSubclassOf<AActor> Class) const;

	UFUNCTION(BlueprintPure, Category = "Pool")
	static bool IsPoolable(TSubclassOf<AActor> Class);

	// Per class, at most this many are kept parked; extra releases are destroyed.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pool", meta = (ClampMin = "0"))
	int32 MaxPerClass = 64;

	virtual void Deinitialize() override;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	enum class EState : uint8 { Active, PendingRelease, Pooled };
	struct FRecord
	{
		EState State = EState::Active;
		uint32 Generation = 0;
		FTimerHandle Timer;
		TArray<TWeakObjectPtr<UActorComponent>> TicksOff;      // component ticks the pool turned off
		TArray<TWeakObjectPtr<UActorComponent>> MoversOff;     // movement components the pool deactivated
		bool bWasHidden = false, bHadCollision = true, bHadTick = true;   // the actor's own values before parking
	};
	// Built in a local while engine calls run (they may call back into the pool), then moved into the record after a fresh lookup.
	struct FParkedState
	{
		TArray<TWeakObjectPtr<UActorComponent>> TicksOff, MoversOff;
		bool bWasHidden = false, bHadCollision = true, bHadTick = true;
	};

	void Park(AActor* Actor, uint32 ExpectedGeneration);
	void PurgeInvalid(UClass* Class);
	FRecord* FindCurrent(AActor* Actor, uint32 Generation, EState State);
	static void ResetEngineState(AActor* Actor, FParkedState& Out);
	static void RestoreComponents(const FParkedState& State);

	TMap<TWeakObjectPtr<AActor>, FRecord> Records;
	TMap<TWeakObjectPtr<UClass>, TArray<TWeakObjectPtr<AActor>>> Free;
	uint32 NextGeneration = 1;
};
