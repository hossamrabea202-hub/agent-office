// World-backed pool lifecycle tests: a real Game world, real actors with a projectile movement component and a ticking component,
// and callbacks that destroy / release the actor at every point where the pool calls out.
#include "Misc/AutomationTest.h"
#include "CDPoolSubsystem.h"
#include "CDPoolTestActor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "TimerManager.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace CDPoolTest
{
	// A throwaway Game world with BeginPlay run, destroyed when this goes out of scope.
	struct FTestWorld
	{
		UWorld* World = nullptr;
		FTestWorld()
		{
			World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("CDPoolTestWorld"));
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			World->InitializeActorsForPlay(FURL());
			World->BeginPlay();
			// No GameMode in this world, so UWorld::BeginPlay does not dispatch actor BeginPlay: do it the way GameState would.
			if (!World->GetBegunPlay())
			{
				World->GetWorldSettings()->NotifyBeginPlay();
			}
		}
		// FTimerManager::Tick runs at most once per engine frame: advance the frame counter like the engine loop does.
		void TickTimers(float Seconds) const
		{
			for (int32 i = 0; i < 3; ++i)
			{
				++GFrameCounter;
				World->GetTimerManager().Tick(Seconds / 3.f);
			}
		}
		~FTestWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}
		UCDPoolSubsystem* Pool() const { return World->GetSubsystem<UCDPoolSubsystem>(); }
		ACDPoolTestActor* Acquire() const { return Cast<ACDPoolTestActor>(Pool()->AcquirePooledActor(ACDPoolTestActor::StaticClass(), FTransform::Identity)); }
	};

	bool Alive(const AActor* A) { return IsValid(A) && !A->IsActorBeingDestroyed(); }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDPoolLifecycleTest, "CastleDefender.Pool.Lifecycle",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCDPoolLifecycleTest::RunTest(const FString& Parameters)
{
	using namespace CDPoolTest;
	FTestWorld W;
	if (!TestNotNull(TEXT("pool subsystem exists in a Game world"), W.Pool()))
	{
		return false;
	}
	UCDPoolSubsystem* Pool = W.Pool();

	ACDPoolTestActor* A = W.Acquire();
	if (!TestNotNull(TEXT("fresh acquire spawns"), A)) { return false; }
	TestEqual(TEXT("fresh acquire calls OnAcquired once"), A->Acquired, 1);
	TestTrue(TEXT("fresh: mover active"), A->Mover->IsActive());
	TestTrue(TEXT("fresh: ticker ticks"), A->Ticker->IsComponentTickEnabled());

	A->SetActorHiddenInGame(false);
	A->SetActorEnableCollision(true);
	Pool->ReleasePooledActor(A);
	TestEqual(TEXT("released: OnReleased once"), A->Released, 1);
	TestEqual(TEXT("released: one parked"), Pool->GetPooledCount(ACDPoolTestActor::StaticClass()), 1);
	TestTrue(TEXT("parked: hidden"), A->IsHidden());
	TestFalse(TEXT("parked: no collision"), A->GetActorEnableCollision());
	TestFalse(TEXT("parked: mover inactive"), A->Mover->IsActive());
	TestFalse(TEXT("parked: ticker off"), A->Ticker->IsComponentTickEnabled());

	AddExpectedMessage(TEXT("released twice or not handed out"), ELogVerbosity::Warning, EAutomationExpectedMessageFlags::Contains, 1);
	Pool->ReleasePooledActor(A);
	TestEqual(TEXT("second release ignored"), A->Released, 1);

	ACDPoolTestActor* B = W.Acquire();
	TestTrue(TEXT("reacquire returns the parked actor"), B == A);
	TestEqual(TEXT("reacquire: OnAcquired again"), A->Acquired, 2);
	TestFalse(TEXT("reacquire: visible again"), A->IsHidden());
	TestTrue(TEXT("reacquire: collision back"), A->GetActorEnableCollision());
	TestTrue(TEXT("reacquire: mover active"), A->Mover->IsActive());
	TestTrue(TEXT("reacquire: ticker ticks"), A->Ticker->IsComponentTickEnabled());
	TestEqual(TEXT("reacquire: nothing parked"), Pool->GetPooledCount(ACDPoolTestActor::StaticClass()), 0);

	// Delayed release: parked only when the timer fires; a destroy while pending must not crash or leak a record.
	Pool->ReleasePooledActor(A, 0.5f);
	TestEqual(TEXT("delayed: not parked yet"), Pool->GetPooledCount(ACDPoolTestActor::StaticClass()), 0);
	ACDPoolTestActor* C = W.Acquire();
	TestTrue(TEXT("delayed: a pending actor is not handed out"), C && C != A);
	W.TickTimers(1.f);
	TestEqual(TEXT("delayed: parked after the timer"), Pool->GetPooledCount(ACDPoolTestActor::StaticClass()), 1);
	Pool->ReleasePooledActor(C, 0.5f);
	C->Destroy();
	W.TickTimers(1.f);
	TestEqual(TEXT("destroyed while pending: not parked"), Pool->GetPooledCount(ACDPoolTestActor::StaticClass()), 1);

	// Capacity
	Pool->MaxPerClass = 1;
	ACDPoolTestActor* D = W.Acquire();   // takes A back out
	ACDPoolTestActor* E = W.Acquire();   // fresh
	Pool->ReleasePooledActor(D);
	Pool->ReleasePooledActor(E);
	TestEqual(TEXT("capacity 1: one parked"), Pool->GetPooledCount(ACDPoolTestActor::StaticClass()), 1);
	TestFalse(TEXT("capacity 1: the extra one destroyed"), Alive(E));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDPoolReentrancyTest, "CastleDefender.Pool.Reentrancy",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCDPoolReentrancyTest::RunTest(const FString& Parameters)
{
	using namespace CDPoolTest;
	FTestWorld W;
	UCDPoolSubsystem* Pool = W.Pool();
	if (!TestNotNull(TEXT("pool"), Pool)) { return false; }
	UClass* Cls = ACDPoolTestActor::StaticClass();

	// Parks one actor with a given reaction armed for its NEXT acquire.
	auto ParkOne = [&](ECDPoolTestReaction R)
	{
		ACDPoolTestActor* A = W.Acquire();
		Pool->ReleasePooledActor(A);
		A->Reaction = R;
		return A;
	};

	{
		ACDPoolTestActor* A = ParkOne(ECDPoolTestReaction::DestroyOnAcquired);
		TestNull(TEXT("OnAcquired destroys (from pool): Acquire returns null"), W.Acquire());
		TestFalse(TEXT("... and the actor is gone"), Alive(A));
		TestEqual(TEXT("... nothing parked"), Pool->GetPooledCount(Cls), 0);
	}
	{
		ACDPoolTestActor* A = ParkOne(ECDPoolTestReaction::ReleaseOnAcquired);
		TestNull(TEXT("OnAcquired releases (from pool): Acquire returns null"), W.Acquire());
		TestEqual(TEXT("... it is parked again"), Pool->GetPooledCount(Cls), 1);
		TestTrue(TEXT("... parked hidden"), A->IsHidden());
		ACDPoolTestActor* Again = W.Acquire();
		TestTrue(TEXT("... and can be acquired normally afterwards"), Again == A);
		TestTrue(TEXT("... mover active"), A->Mover->IsActive());
		TestTrue(TEXT("... ticker ticks"), A->Ticker->IsComponentTickEnabled());
		Pool->ReleasePooledActor(A);
		A->Reaction = ECDPoolTestReaction::None;
		W.Acquire();   // drain
	}
	{
		ACDPoolTestActor* A = W.Acquire();
		A->Reaction = ECDPoolTestReaction::DestroyOnReleased;
		Pool->ReleasePooledActor(A);
		TestFalse(TEXT("OnReleased destroys: actor gone"), Alive(A));
		TestEqual(TEXT("... nothing parked"), Pool->GetPooledCount(Cls), 0);
	}
	{
		ACDPoolTestActor* A = W.Acquire();
		A->Reaction = ECDPoolTestReaction::DestroyOnMoverDeactivated;
		Pool->ReleasePooledActor(A);
		TestFalse(TEXT("mover Deactivate callback destroys during Park: actor gone"), Alive(A));
		TestEqual(TEXT("... nothing parked"), Pool->GetPooledCount(Cls), 0);
	}
	{
		ACDPoolTestActor* A = ParkOne(ECDPoolTestReaction::DestroyOnMoverActivated);
		TestNull(TEXT("mover Activate callback destroys during Acquire: null"), W.Acquire());
		TestFalse(TEXT("... actor gone"), Alive(A));
	}
	{
		ACDPoolTestActor* A = ParkOne(ECDPoolTestReaction::ReleaseOnMoverActivated);
		TestNull(TEXT("mover Activate callback releases during Acquire: null"), W.Acquire());
		TestEqual(TEXT("... parked again"), Pool->GetPooledCount(Cls), 1);
		ACDPoolTestActor* Again = W.Acquire();
		TestTrue(TEXT("... next acquire returns it"), Again == A);
		TestTrue(TEXT("... with its mover active (handed back, not lost)"), A->Mover->IsActive());
		TestTrue(TEXT("... with its ticker ticking (handed back, not lost)"), A->Ticker->IsComponentTickEnabled());
		TestFalse(TEXT("... visible"), A->IsHidden());
	}
	return true;
}

#endif
