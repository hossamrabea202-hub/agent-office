#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CastleDefenderStatics.generated.h"

/** First C++ helpers for Castle Defender, callable from Blueprints. */
UCLASS()
class CASTLEDEFENDER_API UCastleDefenderStatics : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Last frame's duration in milliseconds. */
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Perf")
	static float GetFrameTimeMs();

	/** Number of live actors of the given class in the world (e.g. enemies). */
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Perf", meta = (WorldContext = "WorldContextObject"))
	static int32 CountActorsOfClass(const UObject* WorldContextObject, TSubclassOf<AActor> ActorClass);
};
