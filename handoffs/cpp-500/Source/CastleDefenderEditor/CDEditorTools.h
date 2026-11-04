// #500 point 7: editor checks as one click / one line. From Python:
//   unreal.CDEditorTools.find_blueprints_with_errors('/Game/CastleDefender', True)   # True = recompile each Blueprint first
//   unreal.CDEditorTools.find_expensive_calls('/Game/CastleDefender')
// Each returns readable lines ("BP_X | EventGraph | K2Node_CallFunction_7 | GetAllActorsWithTag"), also printed to the Output Log.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CDEditorTools.generated.h"

UCLASS()
class CASTLEDEFENDEREDITOR_API UCDEditorTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// Blueprints under Path whose compile status is Error or that have nodes with errors.
	// bRecompile = true compiles each one first (slow on big folders; nothing is saved). false = the status from the last compile.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Checks", meta = (DevelopmentOnly))
	static TArray<FString> FindBlueprintsWithErrors(const FString& Path = TEXT("/Game/CastleDefender"), bool bRecompile = false);

	// Every call to a known-expensive function in any Blueprint graph under Path (world scans, traces, widget scans).
	// A call on Tick / DrawHUD / a short timer is a frame-rate problem; on BeginPlay or an event it is usually fine.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Checks", meta = (DevelopmentOnly))
	static TArray<FString> FindExpensiveCalls(const FString& Path = TEXT("/Game/CastleDefender"));
};
