#include "CDHudBase.h"
#include "CDActorCache.h"
#include "CDStats.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "HAL/IConsoleManager.h"

DECLARE_CYCLE_STAT(TEXT("HUD DrawHUD (whole chain)"), STAT_CD_HudDraw, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("HUD GetTextSize (cached)"), STAT_CD_HudTextSize, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("HUD text size cache misses"), STAT_CD_HudTextMiss, STATGROUP_CastleDefender);

namespace CDHudBase
{
	static int32 GTextCacheMax = 4096;
	static int32 GTextCache = 0;   // rev 2: OFF by default, so the retargeted Blueprint path is the exact engine path until switched on
	static FAutoConsoleVariableRef CVarMax(TEXT("cd.Hud.TextCacheMax"), GTextCacheMax, TEXT("Most cached HUD text sizes before the cache is cleared."));
	static FAutoConsoleVariableRef CVarOn(TEXT("cd.Hud.TextCache"), GTextCache, TEXT("1 = GetTextSizeCached uses the cache. 0 (default) = measures every call exactly like the engine node HUD::GetTextSize."));
}

void ACDHudBase::DrawHUD()
{
	CD_SCOPE(STAT_CD_HudDraw);
	Super::DrawHUD();   // runs every Blueprint level's Receive Draw HUD (native layers are called from inside those graphs)
	DrawCommanderCard();   // #553: the commander window draws last, over everything (also while paused)
}

void ACDHudBase::DrawCommanderCard()
{
	if (!Canvas) { return; }
	UActorComponent* C = CommanderCard.Get();
	if (!C)
	{
		APawn* Pawn = GetOwningPawn();
		if (!Pawn) { return; }
		for (UActorComponent* Comp : Pawn->GetComponents())
		{
			if (Comp && Comp->GetClass()->GetName().StartsWith(TEXT("BPC_CommanderCard"))) { C = Comp; CommanderCard = Comp; break; }
		}
		if (!C) { return; }
	}
	static const FName NAME_DrawCommander(TEXT("DrawCommander"));
	UFunction* F = C->FindFunction(NAME_DrawCommander);
	if (!F) { return; }
	struct { AHUD* Hud; int32 SizeX; int32 SizeY; } Params{ this, Canvas->SizeX, Canvas->SizeY };
	C->ProcessEvent(F, &Params);
}

AActor* ACDHudBase::GetCachedActorOfClass(TSubclassOf<AActor> ActorClass) { return UCDActorCacheLibrary::CachedGetActorOfClass(this, ActorClass); }
void ACDHudBase::GetCachedActorsOfClass(TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors) { UCDActorCacheLibrary::CachedGetAllActorsOfClass(this, ActorClass, OutActors); }
void ACDHudBase::GetCachedActorsWithTag(FName Tag, TArray<AActor*>& OutActors) { UCDActorCacheLibrary::CachedGetAllActorsWithTag(this, Tag, OutActors); }
bool ACDHudBase::IsActorOnScreen(const AActor* Actor, float Tolerance) { return IsValid(Actor) && Actor->WasRecentlyRendered(FMath::Max(0.f, Tolerance)); }
void ACDHudBase::InvalidateHudCaches()
{
	UCDActorCacheLibrary::InvalidateCachedLookups(this);
	TextSizeCache.Reset();
	TextCacheEntries = 0;
}

void ACDHudBase::GetTextSizeCached(const FString& Text, float& OutWidth, float& OutHeight, UFont* Font, float Scale) const
{
	CD_SCOPE(STAT_CD_HudTextSize);
	OutWidth = 0.f;
	OutHeight = 0.f;
	if (!Canvas) { return; }   // engine node: no canvas outside DrawHUD -> 0, 0 (it also logs a warning; we stay quiet here)
	UFont* UseFont = Font ? Font : GEngine->GetMediumFont();   // same default font as AHUD::GetTextSize

	if (!CDHudBase::GTextCache)
	{
		Canvas->TextSize(UseFont, Text, OutWidth, OutHeight, Scale, Scale);   // exactly the engine path
		return;
	}
	// sizes depend on the canvas DPI scale through the font cache: clear on viewport / DPI change
	const FIntPoint View(Canvas->SizeX, Canvas->SizeY);
	const float DPI = Canvas->GetDPIScale();
	if (View != TextCacheViewport || DPI != TextCacheDPI || TextCacheEntries >= CDHudBase::GTextCacheMax)
	{
		TextSizeCache.Reset();
		TextCacheEntries = 0;
		TextCacheViewport = View;
		TextCacheDPI = DPI;
	}
	FTextSizes& ForFont = TextSizeCache.FindOrAdd(TPair<const UFont*, float>(UseFont, Scale));
	if (const FVector2f* Hit = ForFont.Find(Text))   // exact, case-sensitive string compare, no copy
	{
		OutWidth = Hit->X;
		OutHeight = Hit->Y;
		return;
	}
	INC_DWORD_STAT(STAT_CD_HudTextMiss);
	Canvas->TextSize(UseFont, Text, OutWidth, OutHeight, Scale, Scale);
	ForFont.Add(Text, FVector2f(OutWidth, OutHeight));
	++TextCacheEntries;
}
