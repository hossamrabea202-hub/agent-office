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

UCDPoolSubsystem::FRecord* UCDPoolSubsystem::FindCurrent(AActor* Actor, uint32 Generation, EState State)
{
	FRecord* R = Records.Find(Actor);
	return (R && R->Generation == Generation && R->State == State) ? R : nullptr;
}

void UCDPoolSubsystem::ResetEngineState(AActor* Actor, FParkedState& Out)
{
	// Works on a local struct only: Deactivate / SetComponentTickEnabled may run callbacks that change the pool's maps.
	if (UWorld* World = Actor->GetWorld())
	{
		World->GetTimerManager().ClearAllTimersForObject(Actor);
	}
	Actor->SetLifeSpan(0.f);
	Out.bWasHidden = Actor->IsHidden();
	Out.bHadCollision = Actor->GetActorEnableCollision();
	Out.bHadTick = Actor->IsActorTickEnabled();
	TInlineComponentArray<UActorComponent*> Components(Actor);
	for (UActorComponent* Comp : Components)
	{
		if (!IsValid(Comp))
		{
			continue;
		}
		if (UMovementComponent* Mover = Cast<UMovementComponent>(Comp))
		{
			Mover->StopMovementImmediately();
			if (Mover->IsActive())
			{
				Out.MoversOff.Add(Mover);
				Mover->Deactivate();
			}
		}
		if (Comp->IsComponentTickEnabled())
		{
			Out.TicksOff.Add(Comp);
			Comp->SetComponentTickEnabled(false);
		}
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

void UCDPoolSubsystem::RestoreComponents(const FParkedState& State)
{
	for (const TWeakObjectPtr<UActorComponent>& W : State.TicksOff)
	{
		if (UActorComponent* Comp = W.Get()) { Comp->SetComponentTickEnabled(true); }
	}
	for (const TWeakObjectPtr<UActorComponent>& W : State.MoversOff)
	{
		if (UActorComponent* Comp = W.Get()) { Comp->Activate(true); }
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
	const bool bFromPool = Actor != nullptr;
	if (bFromPool)
	{
		Actor->SetActorTransform(Transform, false, nullptr, ETeleportType::ResetPhysics);   // still hidden, still without collision
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

	// Mark it ours BEFORE any callback, and move the parked state out of the record into a local.
	FParkedState Parked;
	uint32 Generation = 0;
	{
		FRecord& Rec = Records.FindOrAdd(Actor);   // nothing between here and the end of this block can call out
		World->GetTimerManager().ClearTimer(Rec.Timer);
		Parked.TicksOff = MoveTemp(Rec.TicksOff);
		Parked.MoversOff = MoveTemp(Rec.MoversOff);
		Parked.bWasHidden = Rec.bWasHidden;
		Parked.bHadCollision = Rec.bHadCollision;
		Parked.bHadTick = Rec.bHadTick;
		Rec.State = EState::Active;
		Rec.Generation = Generation = NextGeneration++;
	}
	if (!bFromPool)
	{
		ICDPoolable::Execute_OnAcquired(Actor);   // fresh spawn: its own BeginPlay state, nothing to restore
		return Actor;
	}
	RestoreComponents(Parked);                 // may run callbacks
	ICDPoolable::Execute_OnAcquired(Actor);    // reset gameplay state while still hidden and without collision
	if (!IsValid(Actor) || !FindCurrent(Actor, Generation, EState::Active))
	{
		return IsValid(Actor) ? Actor : nullptr;   // a callback released or destroyed it: leave it as that left it
	}
	Actor->SetActorHiddenInGame(Parked.bWasHidden);
	Actor->SetActorTickEnabled(Parked.bHadTick);
	Actor->SetActorEnableCollision(Parked.bHadCollision);   // last
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
	Rec->State = EState::PendingRelease;
	if (LifeSeconds > 0.f)
	{
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
	Park(Actor, Generation);
}

void UCDPoolSubsystem::Park(AActor* Actor, uint32 ExpectedGeneration)
{
	// Never hold an FRecord pointer across anything that can call out (OnReleased, Deactivate, tick changes, Destroy): look it up again.
	if (FRecord* Rec = FindCurrent(Actor, ExpectedGeneration, EState::PendingRelease))
	{
		if (UWorld* World = GetWorld()) { World->GetTimerManager().ClearTimer(Rec->Timer); }
	}
	else
	{
		return;   // reacquired since the release was scheduled, or already parked
	}
	ICDPoolable::Execute_OnReleased(Actor);
	if (!IsValid(Actor))
	{
		Records.Remove(Actor);   // OnReleased destroyed it
		return;
	}
	PurgeInvalid(Actor->GetClass());
	if (!FindCurrent(Actor, ExpectedGeneration, EState::PendingRelease))
	{
		return;   // OnReleased re-acquired it
	}
	if (GetPooledCount(Actor->GetClass()) >= MaxPerClass)
	{
		Records.Remove(Actor);
		Actor->Destroy();
		return;
	}
	FParkedState Parked;
	ResetEngineState(Actor, Parked);            // may run callbacks: no record reference held
	if (!IsValid(Actor))
	{
		Records.Remove(Actor);
		return;
	}
	if (!FindCurrent(Actor, ExpectedGeneration, EState::PendingRelease))
	{
		RestoreComponents(Parked);              // a callback re-acquired it meanwhile: undo our component changes and stop
		return;
	}
	Actor->SetActorEnableCollision(false);      // collision off first, visibility last
	Actor->SetActorTickEnabled(false);
	Actor->SetActorHiddenInGame(true);
	FRecord* Rec = FindCurrent(Actor, ExpectedGeneration, EState::PendingRelease);
	if (!Rec)
	{
		return;
	}
	Rec->TicksOff = MoveTemp(Parked.TicksOff);
	Rec->MoversOff = MoveTemp(Parked.MoversOff);
	Rec->bWasHidden = Parked.bWasHidden;
	Rec->bHadCollision = Parked.bHadCollision;
	Rec->bHadTick = Parked.bHadTick;
	Rec->State = EState::Pooled;
	Free.FindOrAdd(Actor->GetClass()).Add(Actor);
	int32 ParkedCount = 0;
	for (const TPair<TWeakObjectPtr<UClass>, TArray<TWeakObjectPtr<AActor>>>& Pair : Free) { ParkedCount += Pair.Value.Num(); }
	SET_DWORD_STAT(STAT_CD_PoolParked, ParkedCount);
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
