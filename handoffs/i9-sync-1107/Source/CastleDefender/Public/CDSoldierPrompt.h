// "[E]" prompt over a nearby soldier / commander (BP_BarracksHUD draws it): owner rule 2026-11-05.
//   - When the hero walks up to a soldier the prompt fades in, holds, fades out (cd.SoldierPrompt.Seconds, default 2 s), then stays hidden.
//   - It comes back for that soldier only after the hero has been farther than cd.SoldierPrompt.ReArmDistance (default 15 m) and returns,
//     so soldiers that follow or guard the hero (they stay close) do not keep the prompt on screen.
//   - Pressing E still works the whole time: only the drawing is gated, not the key branch.
// Wired into BP_BarracksHUD with UCDEditorTools::InsertPinFilter (gate on the draw Branch, fade on the two DrawText colours).
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CDSoldierPrompt.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDSoldierPromptLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// bIn = the HUD's own "show the prompt" condition. Returns bIn && the prompt is inside its short show window for Soldier.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|HUD", meta = (WorldContext = "WorldContextObject"))
	static bool GateSoldierPrompt(bool bIn, UObject* Soldier, const UObject* WorldContextObject);

	// Colour with its alpha scaled by the prompt's fade for Soldier (0 outside the show window).
	UFUNCTION(BlueprintPure, Category = "Castle Defender|HUD", meta = (WorldContext = "WorldContextObject"))
	static FLinearColor FadeSoldierPrompt(FLinearColor In, UObject* Soldier, const UObject* WorldContextObject);

	static float PromptAlpha(AActor* Soldier, const UObject* WorldContextObject, bool bTrigger);
};
