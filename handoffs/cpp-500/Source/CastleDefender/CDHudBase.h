// #500 C++ round 2: native parent for the HUD chain. BP_ZombieHUD (the bottom of the 11-level chain, parent HUD) becomes a child of ACDHudBase,
// so every HUD level (Minimap, SkillTree, Barracks, Army, Controls, Queue, Hero, Commander, Armory, Notice) inherits these functions.
// The HUD's drawing, menus, shop and input stay in the Blueprints. Only the expensive world lookups go native and get cached:
//   GetActorOfClass       -> GetCachedActorOfClass     (kept until that actor is gone; a missing class is looked for again at most every MissingRetry s)
//   GetAllActorsOfClass   -> GetCachedActorsOfClass    (zombie classes: read live from the crowd registry; other classes: reused for MaxAge s)
//   GetAllActorsWithTag   -> GetCachedActorsWithTag    (reused for MaxAge s)
// Same pins as the engine nodes, so hud_swap_scans_ue.py can swap them in place. Behaviour differences (all deliberate, check before swapping a node):
//   - class / tag lists can be up to MaxAge old: a new actor, or an actor that GAINS the tag, shows up to MaxAge later; destroyed actors and actors
//     that LOST the tag never show;
//   - GetCachedActorOfClass keeps the first actor it found until that actor is destroyed: a stable choice, which the engine node does not promise
//     when several actors match. Meant for singletons (wave manager, director, player helpers); the swap script leaves GetActorOfClass alone unless
//     asked (--include-single);
//   - refresh uses real time, so caches still refresh while the game is paused.
// `stat CastleDefender` shows "HUD DrawHUD (whole chain)" and the cache hit / miss counters.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "CDHudBase.generated.h"

UCLASS(Abstract, Blueprintable)
class CASTLEDEFENDER_API ACDHudBase : public AHUD
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD", meta = (DeterminesOutputType = "ActorClass"))
	AActor* GetCachedActorOfClass(TSubclassOf<AActor> ActorClass);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD", meta = (DeterminesOutputType = "ActorClass", DynamicOutputParam = "OutActors"))
	void GetCachedActorsOfClass(TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD")
	void GetCachedActorsWithTag(FName Tag, TArray<AActor*>& OutActors);

	// Rendered by any view in the last Tolerance seconds. NOT a line-of-sight test and not "on this player's screen": an approximation for cosmetic
	// HUD decisions only.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|HUD")
	static bool WasActorRecentlyRendered(const AActor* Actor, float Tolerance = 0.1f);

	// Drop every cache now (for example after a level change or a big spawn the HUD must show at once).
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD")
	void InvalidateHudCaches();

	// How old a class / tag list may be before it is scanned again, seconds.
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Castle Defender|HUD", meta = (ClampMin = "0", UIMax = "2"))
	float MaxAge = 0.25f;

	// How often a class with no actor is looked for again, seconds.
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Castle Defender|HUD", meta = (ClampMin = "0", UIMax = "5"))
	float MissingRetry = 0.5f;

	virtual void DrawHUD() override;

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
