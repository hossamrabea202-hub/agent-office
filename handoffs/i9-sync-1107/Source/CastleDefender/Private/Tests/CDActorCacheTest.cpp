// Cached lookups against a real Game world: same results as the engine nodes, except the documented MaxAge delay for newly spawned actors.
#include "Misc/AutomationTest.h"
#include "CDActorCache.h"
#include "CDPoolTestActor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "Kismet/GameplayStatics.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDActorCacheTest, "CastleDefender.ActorCache.Lookups",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCDActorCacheTest::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("CDActorCacheTestWorld"));
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	World->InitializeActorsForPlay(FURL());
	World->BeginPlay();
	if (!World->GetBegunPlay())
	{
		World->GetWorldSettings()->NotifyBeginPlay();
	}
	ON_SCOPE_EXIT
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	};

	UCDActorCache* Cache = UCDActorCache::Get(World);
	if (!TestNotNull(TEXT("cache subsystem exists"), Cache)) { return false; }
	UClass* Cls = ACDPoolTestActor::StaticClass();
	const FName Tag(TEXT("CDCacheTestTag"));
	auto Spawn = [&](bool bTagged)
	{
		AActor* A = World->SpawnActor<ACDPoolTestActor>(Cls, FTransform::Identity);
		if (bTagged) { A->Tags.Add(Tag); }
		return A;
	};

	TestNull(TEXT("no actor yet -> null, like the engine node"), UCDActorCacheLibrary::CachedGetActorOfClass(World, Cls));
	AActor* A = Spawn(true);
	TestNull(TEXT("a miss is remembered for MissingRetry"), UCDActorCacheLibrary::CachedGetActorOfClass(World, Cls));
	Cache->Invalidate();
	TestTrue(TEXT("after invalidate: found"), UCDActorCacheLibrary::CachedGetActorOfClass(World, Cls) == A);
	AActor* B = Spawn(true);
	TestTrue(TEXT("singleton stays the same while it lives"), UCDActorCacheLibrary::CachedGetActorOfClass(World, Cls) == A);
	A->Destroy();
	TestTrue(TEXT("destroyed singleton -> rescanned, finds the other"), UCDActorCacheLibrary::CachedGetActorOfClass(World, Cls) == B);

	TArray<AActor*> Out, Engine;
	UCDActorCacheLibrary::CachedGetAllActorsWithTag(World, Tag, Out);
	UGameplayStatics::GetAllActorsWithTag(World, Tag, Engine);
	TestEqual(TEXT("tag list matches the engine node"), Out.Num(), Engine.Num());
	AActor* C = Spawn(true);
	UCDActorCacheLibrary::CachedGetAllActorsWithTag(World, Tag, Out);
	TestFalse(TEXT("a new tagged actor waits for MaxAge (documented delay)"), Out.Contains(C));
	B->Tags.Remove(Tag);
	UCDActorCacheLibrary::CachedGetAllActorsWithTag(World, Tag, Out);
	TestFalse(TEXT("an actor that lost the tag is filtered at once"), Out.Contains(B));
	Cache->MaxAge = 0.f;
	UCDActorCacheLibrary::CachedGetAllActorsWithTag(World, Tag, Out);
	TestTrue(TEXT("after MaxAge the new actor is there"), Out.Contains(C));

	Cache->MaxAge = 0.25f;
	UCDActorCacheLibrary::CachedGetAllActorsOfClass(World, Cls, Out);
	TestEqual(TEXT("class list: B and C"), Out.Num(), 2);
	C->Destroy();
	UCDActorCacheLibrary::CachedGetAllActorsOfClass(World, Cls, Out);
	TestEqual(TEXT("destroyed actors never appear, even from a fresh cache"), Out.Num(), 1);

	UCDActorCacheLibrary::CachedGetAllActorsWithTag(World, NAME_None, Out);
	TestEqual(TEXT("tag None -> empty"), Out.Num(), 0);
	return true;
}

#endif
