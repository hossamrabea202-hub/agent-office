#include "CDSoldierPrompt.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"

namespace CDSoldierPrompt
{
	static int32 GEnable = 1;
	static float GSeconds = 2.0f;
	static float GFadeIn = 0.3f;
	static float GFadeOut = 0.6f;
	static float GReArmDistance = 1500.f;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.SoldierPrompt.Enable"), GEnable, TEXT("1 = soldier [E] prompt shows briefly once per approach (default). 0 = always shown, as authored."));
	static FAutoConsoleVariableRef CVarSeconds(TEXT("cd.SoldierPrompt.Seconds"), GSeconds, TEXT("How long the soldier [E] prompt stays up, fades included (s)."));
	static FAutoConsoleVariableRef CVarReArm(TEXT("cd.SoldierPrompt.ReArmDistance"), GReArmDistance, TEXT("The hero must get farther than this (cm) from a soldier before his prompt can show again."));

	struct FEntry
	{
		double ShownAt = -1.0;   // world time the current show window started, -1 = not shown since armed
		bool bArmed = true;      // true = the next approach shows the prompt
	};
	static TMap<TWeakObjectPtr<AActor>, FEntry> GEntries;
	static TWeakObjectPtr<UWorld> GPromptWorld;
}

float UCDSoldierPromptLibrary::PromptAlpha(AActor* Soldier, const UObject* WorldContextObject, bool bTrigger)
{
	using namespace CDSoldierPrompt;
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	if (!World || !IsValid(Soldier)) { return 0.f; }
	if (GPromptWorld.Get() != World) { GEntries.Reset(); GPromptWorld = World; }   // new play session
	const double Now = World->GetTimeSeconds();
	const APawn* Hero = UGameplayStatics::GetPlayerPawn(World, 0);

	// re-arm every soldier the hero has walked away from; drop dead entries
	for (auto It = GEntries.CreateIterator(); It; ++It)
	{
		AActor* S = It.Key().Get();
		if (!S) { It.RemoveCurrent(); continue; }
		if (!It.Value().bArmed && Hero && Now - It.Value().ShownAt > GSeconds && S->GetDistanceTo(Hero) > GReArmDistance)
		{
			It.Value().bArmed = true;
			It.Value().ShownAt = -1.0;
		}
	}

	FEntry& E = GEntries.FindOrAdd(Soldier);
	if (bTrigger && E.bArmed && E.ShownAt < 0.0)
	{
		E.ShownAt = Now;
		E.bArmed = false;
	}
	if (E.ShownAt < 0.0) { return 0.f; }
	const float T = float(Now - E.ShownAt);
	if (T >= GSeconds) { return 0.f; }
	const float In = GFadeIn > 0.f ? FMath::Clamp(T / GFadeIn, 0.f, 1.f) : 1.f;
	const float Out = GFadeOut > 0.f ? FMath::Clamp((GSeconds - T) / GFadeOut, 0.f, 1.f) : 1.f;
	return FMath::Min(In, Out);
}

bool UCDSoldierPromptLibrary::GateSoldierPrompt(bool bIn, UObject* Soldier, const UObject* WorldContextObject)
{
	if (!CDSoldierPrompt::GEnable) { return bIn; }
	if (!bIn) { return false; }
	return PromptAlpha(Cast<AActor>(Soldier), WorldContextObject, true) > 0.01f;
}

FLinearColor UCDSoldierPromptLibrary::FadeSoldierPrompt(FLinearColor In, UObject* Soldier, const UObject* WorldContextObject)
{
	if (!CDSoldierPrompt::GEnable) { return In; }
	In.A *= PromptAlpha(Cast<AActor>(Soldier), WorldContextObject, false);
	return In;
}
