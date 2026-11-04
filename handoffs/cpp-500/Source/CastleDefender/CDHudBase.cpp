#include "CDHudBase.h"
#include "CDStats.h"
#include "CrowdSubsystem.h"
#include "ZombieBase.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"
#include "Kismet/GameplayStatics.h"

DECLARE_CYCLE_STAT(TEXT("HUD DrawHUD (whole chain)"), STAT_CD_HudDraw, STATGROUP_CastleDefender);
DECLARE_DWORD_ACCUMULATOR_STAT(TEXT("HUD cache hits"), STAT_CD_HudHits, STATGROUP_CastleDefender);
DECLARE_DWORD_ACCUMULATOR_STAT(TEXT("HUD cache scans"), STAT_CD_HudScans, STATGROUP_CastleDefender);

void ACDHudBase::DrawHUD()
{
	CD_SCOPE(STAT_CD_HudDraw);
	Super::DrawHUD();   // runs the Blueprint Receive Draw HUD event; each HUD level still calls (or not) its parent level as its graph does today
}

double ACDHudBase::Now() const
{
	return FPlatformTime::Seconds();   // real time: refreshes while the game is paused
}

void ACDHudBase::Resolve(const TArray<TWeakObjectPtr<AActor>>& In, TArray<AActor*>& Out)
{
	Out.Reset(In.Num());
	for (const TWeakObjectPtr<AActor>& W : In)
	{
		AActor* A = W.Get();
		if (IsValid(A) && !A->IsActorBeingDestroyed())
		{
			Out.Add(A);
		}
	}
}

AActor* ACDHudBase::GetCachedActorOfClass(TSubclassOf<AActor> ActorClass)
{
	if (!*ActorClass)
	{
		return nullptr;
	}
	FSingleCache& C = Singles.FindOrAdd(*ActorClass);
	AActor* Cached = C.Actor.Get();
	if (IsValid(Cached) && !Cached->IsActorBeingDestroyed())
	{
		INC_DWORD_STAT(STAT_CD_HudHits);
		return Cached;
	}
	const double T = Now();
	if (C.MissedAt >= 0.0 && T - C.MissedAt < MissingRetry)
	{
		INC_DWORD_STAT(STAT_CD_HudHits);
		return nullptr;   // looked very recently and there was none
	}
	INC_DWORD_STAT(STAT_CD_HudScans);
	AActor* Found = UGameplayStatics::GetActorOfClass(this, ActorClass);
	C.Actor = Found;
	C.MissedAt = Found ? -1.0 : T;
	return Found;
}

void ACDHudBase::GetCachedActorsOfClass(TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors)
{
	OutActors.Reset();
	if (!*ActorClass)
	{
		return;
	}
	// Zombies: the crowd registry is exact and costs nothing, no cache needed. Dead zombies included, like GetAllActorsOfClass.
	if (ActorClass->IsChildOf(AZombieBase::StaticClass()))
	{
		if (const UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
		{
			UClass* Wanted = *ActorClass;
			Crowd->ForEachZombie([&OutActors, Wanted](AZombieBase* Z)
			{
				if (Z->IsA(Wanted) && !Z->IsActorBeingDestroyed()) { OutActors.Add(Z); }
			});
			INC_DWORD_STAT(STAT_CD_HudHits);
			return;
		}
	}
	FListCache& C = ClassLists.FindOrAdd(*ActorClass);
	const double T = Now();
	if (C.Time < 0.0 || T - C.Time >= MaxAge)
	{
		INC_DWORD_STAT(STAT_CD_HudScans);
		TArray<AActor*> Found;
		UGameplayStatics::GetAllActorsOfClass(this, ActorClass, Found);
		C.Actors.Reset(Found.Num());
		for (AActor* A : Found) { C.Actors.Add(A); }
		C.Time = T;
	}
	else
	{
		INC_DWORD_STAT(STAT_CD_HudHits);
	}
	Resolve(C.Actors, OutActors);
}

void ACDHudBase::GetCachedActorsWithTag(FName Tag, TArray<AActor*>& OutActors)
{
	OutActors.Reset();
	FListCache& C = TagLists.FindOrAdd(Tag);
	const double T = Now();
	if (C.Time < 0.0 || T - C.Time >= MaxAge)
	{
		INC_DWORD_STAT(STAT_CD_HudScans);
		TArray<AActor*> Found;
		UGameplayStatics::GetAllActorsWithTag(this, Tag, Found);
		C.Actors.Reset(Found.Num());
		for (AActor* A : Found) { C.Actors.Add(A); }
		C.Time = T;
	}
	else
	{
		INC_DWORD_STAT(STAT_CD_HudHits);
	}
	Resolve(C.Actors, OutActors);
	// A tagged actor whose tag was removed since the scan is dropped here, so the list never shows something that no longer matches.
	OutActors.RemoveAll([Tag](const AActor* A) { return !A->ActorHasTag(Tag); });
}

bool ACDHudBase::WasActorRecentlyRendered(const AActor* Actor, float Tolerance)
{
	return IsValid(Actor) && Actor->WasRecentlyRendered(FMath::Max(0.f, Tolerance));
}

void ACDHudBase::InvalidateHudCaches()
{
	Singles.Reset();
	ClassLists.Reset();
	TagLists.Reset();
}
