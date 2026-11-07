#include "CDPoolSubsystem.h"
#include "CDStats.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "GameFramework/MovementComponent.h"
#include "TimerManager.h"

DECLARE_CYCLE_STAT(TEXT("Pool Acquire"), STAT_CD_PoolAcquire, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("Pool parked actors"), STAT_CD_PoolParked, STATGROUP_CastleDefender);

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

bool UCDPoolSubsystem::IsAlive(const AActor* Actor)
{
	return IsValid(Actor) && !Actor->IsActorBeingDestroyed();
}

bool UCDPoolSubsystem::StillOurs(AActor* Actor, uint32 Generation, EState State)
{
	// Call after anything that can run a callback: the actor may be destroyed, released, re-acquired, or the pool torn down.
	return IsAlive(Actor) && FindCurrent(Actor, Generation, State) != nullptr;
}

bool UCDPoolSubsystem::ResetEngineState(AActor* Actor, uint32 Generation, FParkedState& Out)
{
	// Works on a local struct only and re-checks after every call that can run a callback. On false, Out lists exactly what was turned off so far.
	if (UWorld* World = Actor->GetWorld())
	{
		World->GetTimerManager().ClearAllTimersForObject(Actor);
	}
	Actor->SetLifeSpan(0.f);
	Out.bWasHidden = Actor->IsHidden();
	Out.bHadCollision = Actor->GetActorEnableCollision();
	Out.bHadTick = Actor->IsActorTickEnabled();
	TInlineComponentArray<UActorComponent*> Components(Actor);
	TArray<TWeakObjectPtr<UActorComponent>, TInlineAllocator<16>> Snapshot;   // weak: a callback may destroy any of them
	for (UActorComponent* Comp : Components)
	{
		Snapshot.Add(Comp);
	}
	for (const TWeakObjectPtr<UActorComponent>& W : Snapshot)
	{
		UActorComponent* Comp = W.Get();
		if (!IsValid(Comp) || Comp->GetOwner() != Actor)
		{
			continue;
		}
		if (UMovementComponent* Mover = Cast<UMovementComponent>(Comp))
		{
			Mover->StopMovementImmediately();
			if (!StillOurs(Actor, Generation, EState::PendingRelease)) { return false; }
			if (IsValid(Mover) && Mover->IsActive())
			{
				Out.MoversOff.Add(Mover);
				Mover->Deactivate();                // broadcasts OnComponentDeactivated
				if (!StillOurs(Actor, Generation, EState::PendingRelease)) { return false; }
			}
		}
		if (IsValid(Comp) && Comp->IsComponentTickEnabled())
		{
			Out.TicksOff.Add(Comp);
			Comp->SetComponentTickEnabled(false);
			if (!StillOurs(Actor, Generation, EState::PendingRelease)) { return false; }
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
	return StillOurs(Actor, Generation, EState::PendingRelease);
}

bool UCDPoolSubsystem::RestoreComponents(AActor* Actor, uint32 Generation, FParkedState& State)
{
	// Entries are removed as they are restored, so on false State holds exactly the ones still off: the caller hands them back.
	while (State.TicksOff.Num() > 0)
	{
		UActorComponent* Comp = State.TicksOff.Pop(EAllowShrinking::No).Get();
		if (IsValid(Comp))
		{
			Comp->SetComponentTickEnabled(true);
			if (!StillOurs(Actor, Generation, EState::Active)) { return false; }
		}
	}
	while (State.MoversOff.Num() > 0)
	{
		UActorComponent* Comp = State.MoversOff.Pop(EAllowShrinking::No).Get();
		if (IsValid(Comp))
		{
			Comp->Activate(true);                   // broadcasts OnComponentActivated
			if (!StillOurs(Actor, Generation, EState::Active)) { return false; }
		}
	}
	return true;
}

void UCDPoolSubsystem::HandBack(AActor* Actor, FParkedState& Rest)
{
	// Components the pool turned off and has not turned on again, after a callback took the actor away mid-way.
	// Parked again: the next Acquire turns them on. Otherwise (active for someone else, or waiting for a delayed release): turn them on now,
	// one by one, re-checking, because each call can run a callback that parks it.
	while (IsAlive(Actor) && (Rest.TicksOff.Num() > 0 || Rest.MoversOff.Num() > 0))
	{
		if (FRecord* Rec = Records.Find(Actor); Rec && Rec->State == EState::Pooled)
		{
			Rec->TicksOff.Append(MoveTemp(Rest.TicksOff));
			Rec->MoversOff.Append(MoveTemp(Rest.MoversOff));
			return;
		}
		const bool bTick = Rest.TicksOff.Num() > 0;
		UActorComponent* Comp = (bTick ? Rest.TicksOff : Rest.MoversOff).Pop(EAllowShrinking::No).Get();
		if (!IsValid(Comp))
		{
			continue;
		}
		if (bTick) { Comp->SetComponentTickEnabled(true); }
		else { Comp->Activate(true); }
	}
}

void UCDPoolSubsystem::PurgeInvalid(UClass* Class)
{
	if (TArray<TWeakObjectPtr<AActor>>* List = Free.Find(Class))
	{
		List->RemoveAll([](const TWeakObjectPtr<AActor>& W) { return !IsAlive(W.Get()); });
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
			const FRecord* Rec = IsAlive(Candidate) ? Records.Find(Candidate) : nullptr;
			if (Rec && Rec->State == EState::Pooled && Candidate->GetWorld() == World)
			{
				Actor = Candidate;
			}
		}
	}
	const bool bFromPool = Actor != nullptr;
	if (!bFromPool)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Actor = World->SpawnActor<AActor>(Class, Transform, Params);   // BeginPlay may already destroy it
		if (!IsAlive(Actor))
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
		Rec.bActorFlagsPending = bFromPool;     // the bools stay in the record until they are applied below
	}
	// From here, any callback may release, re-acquire or destroy the actor. The caller only gets it back if it is still ours, Active, this generation.
	if (!bFromPool)
	{
		ICDPoolable::Execute_OnAcquired(Actor);   // fresh spawn: its own BeginPlay state, nothing to restore
		return StillOurs(Actor, Generation, EState::Active) ? Actor : nullptr;
	}
	Actor->SetActorTransform(Transform, false, nullptr, ETeleportType::ResetPhysics);   // still hidden, still without collision
	if (!StillOurs(Actor, Generation, EState::Active) || !RestoreComponents(Actor, Generation, Parked))
	{
		HandBack(Actor, Parked);
		return nullptr;
	}
	ICDPoolable::Execute_OnAcquired(Actor);    // reset gameplay state while still hidden and without collision
	if (!StillOurs(Actor, Generation, EState::Active)) { return nullptr; }
	Actor->SetActorHiddenInGame(Parked.bWasHidden);
	if (!StillOurs(Actor, Generation, EState::Active)) { return nullptr; }
	Actor->SetActorTickEnabled(Parked.bHadTick);
	if (!StillOurs(Actor, Generation, EState::Active)) { return nullptr; }
	if (FRecord* Rec = FindCurrent(Actor, Generation, EState::Active))
	{
		Rec->bActorFlagsPending = false;        // set before the call: collision may fire overlaps that release it, which must read the live values
	}
	Actor->SetActorEnableCollision(Parked.bHadCollision);   // last: overlaps may fire here
	return StillOurs(Actor, Generation, EState::Active) ? Actor : nullptr;
}

void UCDPoolSubsystem::ReleasePooledActor(AActor* Actor, float LifeSeconds)
{
	UWorld* World = GetWorld();
	if (!IsAlive(Actor) || !World)
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

void UCDPoolSubsystem::AbandonPark(AActor* Actor, FParkedState& Parked)
{
	if (IsAlive(Actor))
	{
		HandBack(Actor, Parked);   // something else owns it now: undo the component changes made so far
	}
	else
	{
		Records.Remove(Actor);
	}
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
	if (!IsAlive(Actor))
	{
		Records.Remove(Actor);   // destroyed while the release was pending
		return;
	}
	ICDPoolable::Execute_OnReleased(Actor);
	if (!IsAlive(Actor))
	{
		Records.Remove(Actor);   // OnReleased destroyed it
		return;
	}
	if (!FindCurrent(Actor, ExpectedGeneration, EState::PendingRelease))
	{
		return;   // pool torn down meanwhile
	}
	PurgeInvalid(Actor->GetClass());
	if (GetPooledCount(Actor->GetClass()) >= MaxPerClass)
	{
		Records.Remove(Actor);   // before Destroy: EndPlay callbacks must not find a record
		Actor->Destroy();
		return;
	}
	FParkedState Parked;
	bool bKeepRecordedFlags = false, bRecHidden = false, bRecCollision = true, bRecTick = true;
	if (const FRecord* Rec = FindCurrent(Actor, ExpectedGeneration, EState::PendingRelease); Rec && Rec->bActorFlagsPending)
	{
		bKeepRecordedFlags = true;              // released from inside its own Acquire: the actor still shows the parked values
		bRecHidden = Rec->bWasHidden;
		bRecCollision = Rec->bHadCollision;
		bRecTick = Rec->bHadTick;
	}
	if (!ResetEngineState(Actor, ExpectedGeneration, Parked))
	{
		AbandonPark(Actor, Parked);
		return;
	}
	Actor->SetActorEnableCollision(false);      // collision off first, visibility last
	if (!StillOurs(Actor, ExpectedGeneration, EState::PendingRelease)) { AbandonPark(Actor, Parked); return; }
	Actor->SetActorTickEnabled(false);
	if (!StillOurs(Actor, ExpectedGeneration, EState::PendingRelease)) { AbandonPark(Actor, Parked); return; }
	Actor->SetActorHiddenInGame(true);
	FRecord* Rec = StillOurs(Actor, ExpectedGeneration, EState::PendingRelease) ? FindCurrent(Actor, ExpectedGeneration, EState::PendingRelease) : nullptr;
	if (!Rec)
	{
		AbandonPark(Actor, Parked);
		return;
	}
	Rec->TicksOff = MoveTemp(Parked.TicksOff);
	Rec->MoversOff = MoveTemp(Parked.MoversOff);
	Rec->bWasHidden = bKeepRecordedFlags ? bRecHidden : Parked.bWasHidden;
	Rec->bHadCollision = bKeepRecordedFlags ? bRecCollision : Parked.bHadCollision;
	Rec->bHadTick = bKeepRecordedFlags ? bRecTick : Parked.bHadTick;
	Rec->bActorFlagsPending = false;
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
		Count += IsAlive(W.Get()) ? 1 : 0;
	}
	return Count;
}
