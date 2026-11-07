#include "CDActorCache.h"
#include "CDStats.h"
#include "CrowdSubsystem.h"
#include "ZombieBase.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

DECLARE_CYCLE_STAT(TEXT("Cached lookups"), STAT_CD_CachedLookups, STATGROUP_CastleDefender);
DECLARE_DWORD_ACCUMULATOR_STAT(TEXT("Lookup cache hits"), STAT_CD_LookupHits, STATGROUP_CastleDefender);
DECLARE_DWORD_ACCUMULATOR_STAT(TEXT("Lookup cache scans"), STAT_CD_LookupScans, STATGROUP_CastleDefender);

UCDActorCache* UCDActorCache::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	return World ? World->GetSubsystem<UCDActorCache>() : nullptr;
}

double UCDActorCache::Now() const
{
	const UWorld* World = GetWorld();
	return World ? World->GetRealTimeSeconds() : 0.0;
}

void UCDActorCache::Resolve(const TArray<TWeakObjectPtr<AActor>>& In, TArray<AActor*>& Out)
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

AActor* UCDActorCache::GetActorOfClass(TSubclassOf<AActor> ActorClass)
{
	CD_SCOPE(STAT_CD_CachedLookups);
	if (!*ActorClass)
	{
		return nullptr;
	}
	FSingleCache& C = Singles.FindOrAdd(*ActorClass);
	AActor* Cached = C.Actor.Get();
	if (IsValid(Cached) && !Cached->IsActorBeingDestroyed())
	{
		INC_DWORD_STAT(STAT_CD_LookupHits);
		return Cached;
	}
	const double T = Now();
	if (C.MissedAt >= 0.0 && T - C.MissedAt < MissingRetry)
	{
		INC_DWORD_STAT(STAT_CD_LookupHits);
		return nullptr;   // looked very recently and there was none
	}
	INC_DWORD_STAT(STAT_CD_LookupScans);
	AActor* Found = UGameplayStatics::GetActorOfClass(this, ActorClass);
	C.Actor = Found;
	C.MissedAt = Found ? -1.0 : T;
	return Found;
}

void UCDActorCache::GetAllActorsOfClass(TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors)
{
	CD_SCOPE(STAT_CD_CachedLookups);
	OutActors.Reset();
	if (!*ActorClass)
	{
		return;
	}
	// Zombies: the crowd registry is exact and costs nothing. Only used once BP_Zombie is reparented to AZombieBase (registry non-empty).
	if (ActorClass->IsChildOf(AZombieBase::StaticClass()))
	{
		if (const UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
		{
			UClass* Wanted = *ActorClass;
			Crowd->ForEachZombie([&OutActors, Wanted](AZombieBase* Z)
			{
				if (Z->IsA(Wanted) && !Z->IsActorBeingDestroyed()) { OutActors.Add(Z); }
			});
			INC_DWORD_STAT(STAT_CD_LookupHits);
			return;
		}
	}
	FListCache& C = ClassLists.FindOrAdd(*ActorClass);
	const double T = Now();
	if (C.Time < 0.0 || T - C.Time >= MaxAge)
	{
		INC_DWORD_STAT(STAT_CD_LookupScans);
		TArray<AActor*> Found;
		UGameplayStatics::GetAllActorsOfClass(this, ActorClass, Found);
		C.Actors.Reset(Found.Num());
		for (AActor* A : Found) { C.Actors.Add(A); }
		C.Time = T;
	}
	else
	{
		INC_DWORD_STAT(STAT_CD_LookupHits);
	}
	Resolve(C.Actors, OutActors);
}

void UCDActorCache::GetAllActorsWithTag(FName Tag, TArray<AActor*>& OutActors)
{
	CD_SCOPE(STAT_CD_CachedLookups);
	OutActors.Reset();
	if (Tag.IsNone())
	{
		return;   // the engine node returns nothing for None as well
	}
	FListCache& C = TagLists.FindOrAdd(Tag);
	const double T = Now();
	if (C.Time < 0.0 || T - C.Time >= MaxAge)
	{
		INC_DWORD_STAT(STAT_CD_LookupScans);
		TArray<AActor*> Found;
		UGameplayStatics::GetAllActorsWithTag(this, Tag, Found);
		C.Actors.Reset(Found.Num());
		for (AActor* A : Found) { C.Actors.Add(A); }
		C.Time = T;
	}
	else
	{
		INC_DWORD_STAT(STAT_CD_LookupHits);
	}
	Resolve(C.Actors, OutActors);
	// A tagged actor whose tag was removed since the scan is dropped here, so the list never shows something that no longer matches.
	OutActors.RemoveAll([Tag](const AActor* A) { return !A->ActorHasTag(Tag); });
}

void UCDActorCache::Invalidate()
{
	Singles.Reset();
	ClassLists.Reset();
	TagLists.Reset();
}

AActor* UCDActorCacheLibrary::CachedGetActorOfClass(const UObject* WorldContextObject, TSubclassOf<AActor> ActorClass)
{
	UCDActorCache* Cache = UCDActorCache::Get(WorldContextObject);
	return Cache ? Cache->GetActorOfClass(ActorClass) : UGameplayStatics::GetActorOfClass(WorldContextObject, ActorClass);
}

void UCDActorCacheLibrary::CachedGetAllActorsOfClass(const UObject* WorldContextObject, TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors)
{
	if (UCDActorCache* Cache = UCDActorCache::Get(WorldContextObject))
	{
		Cache->GetAllActorsOfClass(ActorClass, OutActors);
		return;
	}
	UGameplayStatics::GetAllActorsOfClass(WorldContextObject, ActorClass, OutActors);
}

void UCDActorCacheLibrary::CachedGetAllActorsWithTag(const UObject* WorldContextObject, FName Tag, TArray<AActor*>& OutActors)
{
	if (UCDActorCache* Cache = UCDActorCache::Get(WorldContextObject))
	{
		Cache->GetAllActorsWithTag(Tag, OutActors);
		return;
	}
	UGameplayStatics::GetAllActorsWithTag(WorldContextObject, Tag, OutActors);
}

void UCDActorCacheLibrary::InvalidateCachedLookups(const UObject* WorldContextObject)
{
	if (UCDActorCache* Cache = UCDActorCache::Get(WorldContextObject))
	{
		Cache->Invalidate();
	}
}
