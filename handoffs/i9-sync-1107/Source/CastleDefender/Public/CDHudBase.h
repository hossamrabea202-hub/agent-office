// #500 C++ round 2: native parent for the HUD chain. BP_ZombieHUD (the bottom of the 11-level chain) becomes a child of
// ACDHudBase, so every HUD level inherits these functions. The HUD's drawing, menus, shop and input stay in the Blueprints
// unless a level is listed in cd.Hud.NativeLayers (then its C++ draw function in UCDHudLayers runs instead of its graph).
//   GetActorOfClass       -> GetCachedActorOfClass   | GetAllActorsOfClass -> GetCachedActorsOfClass
//   GetAllActorsWithTag   -> GetCachedActorsWithTag  (all forward to UCDActorCache, CDActorCache.h)
//   HUD::GetTextSize      -> GetTextSizeCached       (NEW 11-05: same pins; results cached per text/font/scale/DPI)
// `stat CastleDefender` shows "HUD DrawHUD (whole chain)", "HUD GetTextSize (cached)" and one line per native layer.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "CDHudBase.generated.h"

class UFont;

UCLASS(Abstract, Blueprintable)
class CASTLEDEFENDER_API ACDHudBase : public AHUD
{
	GENERATED_BODY()

public:
	// ---------------- existing (unchanged) ----------------
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD", meta = (DeterminesOutputType = "ActorClass"))
	AActor* GetCachedActorOfClass(TSubclassOf<AActor> ActorClass);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD", meta = (DeterminesOutputType = "ActorClass", DynamicOutputParam = "OutActors"))
	void GetCachedActorsOfClass(TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD")
	void GetCachedActorsWithTag(FName Tag, TArray<AActor*>& OutActors);

	UFUNCTION(BlueprintPure, Category = "Castle Defender|HUD")
	static bool IsActorOnScreen(const AActor* Actor, float Tolerance = 0.1f);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD")
	void InvalidateHudCaches();

	// ---------------- NEW: text-size cache ----------------
	// Same pins and result as the engine node HUD::GetTextSize (Text, OutWidth, OutHeight, Font, Scale), so the editor tool
	// RetargetCallNodes can switch every GetTextSize node to this one and keep its wires. The first call for a
	// (text, font, scale, canvas DPI) measures with the canvas exactly like the engine; later calls return the stored size.
	// The cache is cleared when the viewport size or DPI changes, and is capped (cd.Hud.TextCacheMax, default 4096 entries).
	// Valid only during DrawHUD, like the engine node (outside it there is no canvas: returns 0, 0 like the engine).
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|HUD")
	void GetTextSizeCached(const FString& Text, float& OutWidth, float& OutHeight, UFont* Font = nullptr, float Scale = 1.f) const;

	virtual void DrawHUD() override;

	// #553 commander card (11-06): drawn last, on top of every HUD level, by calling BPC_CommanderCard.DrawCommander on the pawn.
	UPROPERTY(Transient) TWeakObjectPtr<UActorComponent> CommanderCard;
	void DrawCommanderCard();

private:
	// rev 2 (review P1): keyed on the FULL text (exact, case-sensitive string compare), not hash + length.
	// Two levels so a lookup never copies the string: (font, scale) -> (text -> size). One string copy per MISS only.
	// mutable: GetTextSize is const in the engine; the cache is an implementation detail of a const query.
	// Case-SENSITIVE string keys: the engine's default FString map keys ignore case, but "Gold" and "GOLD" render differently.
	struct FExactTextKeyFuncs : TDefaultMapKeyFuncs<FString, FVector2f, false>
	{
		static bool Matches(const FString& A, const FString& B) { return A.Equals(B, ESearchCase::CaseSensitive); }
		static uint32 GetKeyHash(const FString& K) { return FCrc::StrCrc32(*K); }
	};
	using FTextSizes = TMap<FString, FVector2f, FDefaultSetAllocator, FExactTextKeyFuncs>;
	mutable TMap<TPair<const UFont*, float>, FTextSizes> TextSizeCache;
	mutable int32 TextCacheEntries = 0;
	mutable FIntPoint TextCacheViewport = FIntPoint::ZeroValue;
	mutable float TextCacheDPI = 0.f;
};
