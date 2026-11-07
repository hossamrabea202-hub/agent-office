#include "CDLockSubsystem.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Components/PrimitiveComponent.h"
#include "TimerManager.h"

static const FName CDLockTag(TEXT("CDLock"));

bool UCDLockSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* W = Cast<UWorld>(Outer);
	return W && (W->WorldType == EWorldType::Game || W->WorldType == EWorldType::PIE);
}

void UCDLockSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	Enforce(true);
	// a second pass after the level scripts and directors have run their BeginPlay (some hide actors by tag)
	InWorld.GetTimerManager().SetTimer(RecheckHandle, [this]() { Enforce(true); }, 2.0f, false);
}

int32 UCDLockSubsystem::EnforceLocks()
{
	int32 Fixed = 0;
	UWorld* W = GetWorld();
	if (!W) { return 0; }
	for (TActorIterator<AActor> It(W); It; ++It)
	{
		AActor* A = *It;
		if (!A || !A->ActorHasTag(CDLockTag)) { continue; }
		bool bTouched = false;
		if (A->IsHidden()) { A->SetActorHiddenInGame(false); bTouched = true; }
		if (!A->GetActorEnableCollision()) { A->SetActorEnableCollision(true); bTouched = true; }
		if (A->IsActorBeingDestroyed() || !IsValid(A)) { UE_LOG(LogTemp, Error, TEXT("[CDLock] %s is being destroyed - a locked actor must never be deleted"), *A->GetName()); }
		TArray<UPrimitiveComponent*> Prims; A->GetComponents<UPrimitiveComponent>(Prims);
		for (UPrimitiveComponent* P : Prims)
		{
			if (P && !P->IsVisible()) { P->SetVisibility(true, true); bTouched = true; }
			if (P && P->bHiddenInGame) { P->SetHiddenInGame(false, true); bTouched = true; }
		}
		if (bTouched) { ++Fixed; }
	}
	return Fixed;
}

void UCDLockSubsystem::Enforce(bool bLog)
{
	const int32 Fixed = EnforceLocks();
	if (bLog && Fixed > 0) { UE_LOG(LogTemp, Warning, TEXT("[CDLock] %d locked actor(s) were hidden or disabled and have been forced back on"), Fixed); }
	else if (bLog) { UE_LOG(LogTemp, Display, TEXT("[CDLock] lock check: all locked actors visible")); }
}
