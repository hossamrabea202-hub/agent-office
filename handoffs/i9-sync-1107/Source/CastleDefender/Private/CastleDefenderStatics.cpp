#include "CastleDefenderStatics.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/App.h"

float UCastleDefenderStatics::GetFrameTimeMs()
{
	return static_cast<float>(FApp::GetDeltaTime() * 1000.0);
}

int32 UCastleDefenderStatics::CountActorsOfClass(const UObject* WorldContextObject, TSubclassOf<AActor> ActorClass)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	if (!World || !ActorClass)
	{
		return 0;
	}

	int32 Count = 0;
	for (TActorIterator<AActor> It(World, ActorClass); It; ++It)
	{
		++Count;
	}
	return Count;
}

