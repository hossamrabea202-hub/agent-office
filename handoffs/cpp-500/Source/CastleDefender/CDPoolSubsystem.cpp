#include "CDPoolSubsystem.h"
#include "CDStats.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "GameFramework/MovementComponent.h"
#include "TimerManager.h"

DECLARE_CYCLE_STAT(TEXT("Pool Acquire"), STAT_CD_PoolAcquire, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("Pool parked actors"), STAT_CD_PoolParked, STATGROUP_CastleDefender);

void ICDPoolable::OnAcquired_Implementation() {}
void ICDPoolable::OnReleased_Implementation() {}

bool UCDPoolSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

bool UCDPoolSubsystem::IsPoolable(TSubclassOf<AActor> Class)
{
	return *Class && Class->ImplementsInterface(UCDPoolable::StaticClass());
}

void UCDPoolSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		for (TPair<TWeakObjectPtr<AActor>, FRecord>& Pair : Records)
		{
			World->GetTimerManager().ClearTimer(Pair.Value.Timer);
		}
	}
	Records.Reset();
	Free.Reset();
	Super::Deinitialize();
}

void UCDPoolSubsystem::ResetEngineState(AActor* Actor)
{
	if (UWorld* World = Actor->GetWorld())
	{
		World->GetTimerManager().ClearAllTimersForObject(Actor);
	}
	Actor->SetLifeSpan(0.f);
	TInlineComponentArray<UMovementComponent*> Movers(Actor);
	for (UMovementComponent* Mover : Movers)
	{
		Mover->StopMovementImmediately();
	}
	if (UPrimitiveComponent* Root = Cast<UPrimitiveComponent>(Actor->GetRootComponent()))
	{
		if (Root->IsSimulatingPhysics())
		{
			Root->SetPhysicsLinearVelocity(FVector::ZeroVector);
			Root->SetPhysicsAngularVelocityInDegrees(FVector::ZeroVector);
		}
	}
}

void UCDPoolSubsystem::PurgeInvalid(UClass* Class)
{
	if (TArray<TWeakObjectPtr<AActor>>* List = Free.Find(Class))
	{
		List->RemoveAll([](const TWeakObjectPtr<AActor>& W) { return !W.IsValid(); });
	}
	for (auto It = Records.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid())
		{
			It.RemoveCurrent();
		}
	}
}

AActor* UCDPoolSubsystem::AcquirePooledActor(TSubclassOf<AActor> Class, const FTransform& Transform)
{
	CD_SCOPE(STAT_CD_PoolAcquire);
	UWorld* World = GetWorld();
	if (!World || !*Class)
	{
		return nullptr;
	}
	if (!IsPoolable(Class))
	{
		return World->SpawnActor<AActor>(Class, Transform);   // not poolable: plain spawn, Release will destroy it
	}

	PurgeInvalid(*Class);
	AActor* Actor = nullptr;
	if (TArray<TWeakObjectPtr<AActor>>* List = Free.Find(*Class))
	{
		while (List->Num() > 0 && !Actor)
		{
			AActor* Candidate = List->Pop().Get();
			const FRecord* Rec = Candidate ? Records.Find(Candidate) : nullptr;
			if (Rec && Rec->State == EState::Pooled && Candidate->GetWorld() == World)
			{
				Actor = Candidate;
			}
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
		if (!Actor)
		{
			return nullptr;
		}
	}

	FRecord& Rec = Records.FindOrAdd(Actor);
	World->GetTimerManager().ClearTimer(Rec.Timer);
	Rec.State = EState::Active;
	Rec.Generation = NextGeneration++;
	ICDPoolable::Execute_OnAcquired(Actor);
	return Actor;
}

void UCDPoolSubsystem::ReleasePooledActor(AActor* Actor, float LifeSeconds)
{
	UWorld* World = GetWorld();
	if (!IsValid(Actor) || !World)
	{
		return;
	}
	if (Actor->GetWorld() != World)
	{
		UE_LOG(LogTemp, Warning, TEXT("CDPool: %s belongs to another world; not released here"), *Actor->GetName());
		return;
	}
	if (!IsPoolable(Actor->GetClass()))
	{
		if (LifeSeconds > 0.f)
		{
			Actor->SetLifeSpan(LifeSeconds);
		}
		else
		{
			Actor->Destroy();
		}
		return;
	}
	FRecord* Rec = Records.Find(Actor);
	if (!Rec || Rec->State != EState::Active)
	{
		UE_LOG(LogTemp, Warning, TEXT("CDPool: %s released twice or not handed out by the pool; ignored"), *Actor->GetName());
		return;
	}
	const uint32 Generation = Rec->Generation;
	if (LifeSeconds > 0.f)
	{
		Rec->State = EState::PendingRelease;
		TWeakObjectPtr<AActor> Weak(Actor);
		World->GetTimerManager().SetTimer(Rec->Timer, FTimerDelegate::CreateWeakLambda(this, [this, Weak, Generation]()
		{
			if (AActor* A = Weak.Get())
			{
				Park(A, Generation);
			}
		}), LifeSeconds, false);
		return;
	}
	Rec->State = EState::PendingRelease;
	Park(Actor, Generation);
}

void UCDPoolSubsystem::Park(AActor* Actor, uint32 ExpectedGeneration)
{
	FRecord* Rec = Records.Find(Actor);
	if (!Rec || Rec->Generation != ExpectedGeneration || Rec->State != EState::PendingRelease)
	{
		return;   // reacquired since the release was scheduled, or already parked
	}
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(Rec->Timer);
	}
	ICDPoolable::Execute_OnReleased(Actor);
	if (!IsValid(Actor))
	{
		Records.Remove(Actor);   // OnReleased destroyed it
		return;
	}
	ResetEngineState(Actor);
	PurgeInvalid(Actor->GetClass());
	TArray<TWeakObjectPtr<AActor>>& List = Free.FindOrAdd(Actor->GetClass());
	if (List.Num() >= MaxPerClass)
	{
		Records.Remove(Actor);
		Actor->Destroy();
		return;
	}
	Actor->SetActorHiddenInGame(true);
	Actor->SetActorEnableCollision(false);
	Actor->SetActorTickEnabled(false);
	Rec->State = EState::Pooled;
	List.Add(Actor);
	int32 Parked = 0;
	for (const TPair<TWeakObjectPtr<UClass>, TArray<TWeakObjectPtr<AActor>>>& Pair : Free) { Parked += Pair.Value.Num(); }
	SET_DWORD_STAT(STAT_CD_PoolParked, Parked);
}

int32 UCDPoolSubsystem::GetPooledCount(TSubclassOf<AActor> Class) const
{
	const TArray<TWeakObjectPtr<AActor>>* List = Free.Find(*Class);
	if (!List)
	{
		return 0;
	}
	int32 Count = 0;
	for (const TWeakObjectPtr<AActor>& W : *List)
	{
		Count += W.IsValid() ? 1 : 0;
	}
	return Count;
}
