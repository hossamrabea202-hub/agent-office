#include "CDPoolSubsystem.h"
#include "CDStats.h"
#include "Engine/World.h"
#include "TimerManager.h"

DECLARE_CYCLE_STAT(TEXT("Pool Acquire"), STAT_CD_PoolAcquire, STATGROUP_CastleDefender);

void ICDPoolable::OnAcquired_Implementation() {}
void ICDPoolable::OnReleased_Implementation() {}

bool UCDPoolSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

AActor* UCDPoolSubsystem::AcquirePooledActor(TSubclassOf<AActor> Class, const FTransform& Transform)
{
	CD_SCOPE(STAT_CD_PoolAcquire);
	UWorld* World = GetWorld();
	if (!World || !*Class)
	{
		return nullptr;
	}
	AActor* Actor = nullptr;
	if (TArray<TWeakObjectPtr<AActor>>* List = Free.Find(*Class))
	{
		while (List->Num() > 0 && !Actor)
		{
			Actor = List->Pop().Get();
		}
	}
	if (Actor)
	{
		Actor->SetActorTransform(Transform, false, nullptr, ETeleportType::ResetPhysics);
		Actor->SetActorHiddenInGame(false);
		Actor->SetActorEnableCollision(true);
		Actor->SetActorTickEnabled(true);
	}
	else
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Actor = World->SpawnActor<AActor>(Class, Transform, Params);
	}
	if (Actor && Actor->GetClass()->ImplementsInterface(UCDPoolable::StaticClass()))
	{
		ICDPoolable::Execute_OnAcquired(Actor);
	}
	return Actor;
}

void UCDPoolSubsystem::ReleasePooledActor(AActor* Actor, float LifeSeconds)
{
	if (!IsValid(Actor))
	{
		return;
	}
	if (LifeSeconds > 0.f)
	{
		FTimerHandle Handle;
		TWeakObjectPtr<AActor> Weak(Actor);
		GetWorld()->GetTimerManager().SetTimer(Handle, FTimerDelegate::CreateWeakLambda(this, [this, Weak]()
		{
			if (AActor* A = Weak.Get()) { Park(A); }
		}), LifeSeconds, false);
		return;
	}
	Park(Actor);
}

void UCDPoolSubsystem::Park(AActor* Actor)
{
	if (Actor->GetClass()->ImplementsInterface(UCDPoolable::StaticClass()))
	{
		ICDPoolable::Execute_OnReleased(Actor);
	}
	TArray<TWeakObjectPtr<AActor>>& List = Free.FindOrAdd(Actor->GetClass());
	if (List.Num() >= MaxPerClass)
	{
		Actor->Destroy();
		return;
	}
	Actor->SetActorHiddenInGame(true);
	Actor->SetActorEnableCollision(false);
	Actor->SetActorTickEnabled(false);
	List.Add(Actor);
}

int32 UCDPoolSubsystem::GetPooledCount(TSubclassOf<AActor> Class) const
{
	const TArray<TWeakObjectPtr<AActor>>* List = Free.Find(*Class);
	return List ? List->Num() : 0;
}
