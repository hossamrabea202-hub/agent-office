// Cached world lookups for ANY Blueprint (HUDs, BP_SoldierSword, BP_JellyBlob, ...), measured 2026-11-04 in real gameplay on the T1000 laptop:
// GetAllActorsWithTag walks all ~4,500 actors per call (BarracksHUD, CommanderHUD, SoldierSword: ~0.9 ms each, every frame) and GetActorOfClass
// is called ~45 times per frame (JellyBlob alone 19). Together ~6 ms of the game thread.
//
// Drop-in replacements with the SAME pins as the engine nodes, so a node swap keeps every link:
//   Get Actor Of Class        -> CD Cached Get Actor Of Class      (kept until that actor is gone; a class with none is looked for again every MissingRetry s)
//   Get All Actors Of Class   -> CD Cached Get All Actors Of Class (zombie classes: live from the crowd registry; others: reused for MaxAge s)
//   Get All Actors With Tag   -> CD Cached Get All Actors With Tag (reused for MaxAge s; actors that lost the tag are filtered out)
// The one intended difference: a NEW actor can appear in a list up to MaxAge (0.25 s) late, and a singleton lookup keeps returning the same actor
// while it lives. Destroyed actors never appear. Ages use real time, so lists keep refreshing while the game is paused.
// Keep the engine node where a result must be exact this frame. `stat CastleDefender` shows hits and scans.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDActorCache.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDActorCache : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	static UCDActorCache* Get(const UObject* WorldContextObject);

	AActor* GetActorOfClass(TSubclassOf<AActor> ActorClass);
	void GetAllActorsOfClass(TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors);
	void GetAllActorsWithTag(FName Tag, TArray<AActor*>& OutActors);
	void Invalidate();

	// How old a class / tag list may be before it is scanned again, seconds.
	float MaxAge = 0.25f;
	// How often a class with no actor is looked for again, seconds.
	float MissingRetry = 0.5f;

private:
	struct FListCache
	{
		TArray<TWeakObjectPtr<AActor>> Actors;
		double Time = -1.0;
	};
	struct FSingleCache
	{
		TWeakObjectPtr<AActor> Actor;
		double MissedAt = -1.0;
	};

	double Now() const;
	static void Resolve(const TArray<TWeakObjectPtr<AActor>>& In, TArray<AActor*>& Out);

	TMap<TWeakObjectPtr<UClass>, FSingleCache> Singles;
	TMap<TWeakObjectPtr<UClass>, FListCache> ClassLists;
	TMap<FName, FListCache> TagLists;
};

UCLASS()
class CASTLEDEFENDER_API UCDActorCacheLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Cached Lookups", meta = (WorldContext = "WorldContextObject", DeterminesOutputType = "ActorClass", DisplayName = "CD Cached Get Actor Of Class"))
	static AActor* CachedGetActorOfClass(const UObject* WorldContextObject, TSubclassOf<AActor> ActorClass);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Cached Lookups", meta = (WorldContext = "WorldContextObject", DeterminesOutputType = "ActorClass", DynamicOutputParam = "OutActors", DisplayName = "CD Cached Get All Actors Of Class"))
	static void CachedGetAllActorsOfClass(const UObject* WorldContextObject, TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Cached Lookups", meta = (WorldContext = "WorldContextObject", DisplayName = "CD Cached Get All Actors With Tag"))
	static void CachedGetAllActorsWithTag(const UObject* WorldContextObject, FName Tag, TArray<AActor*>& OutActors);

	// Drop every cached result now (for example right after a big spawn that must show at once).
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Cached Lookups", meta = (WorldContext = "WorldContextObject", DisplayName = "CD Invalidate Cached Lookups"))
	static void InvalidateCachedLookups(const UObject* WorldContextObject);
};
