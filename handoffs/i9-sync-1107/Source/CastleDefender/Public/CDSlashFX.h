// Per-sword hero slash, built on the classroom Sword Slash effect (Niagara + M_ClassroomSlash).
// Sits at the top of the hero's SpawnSlashFX event: a sword with a row below plays its own slash through the Handled pin;
// any other weapon, or no weapon, leaves through UseOldSlash and the old slash runs unchanged.
// Sword looks are the GSlashes table in CDSlashFX.cpp. They reach the material through MPC_CDSlash, so there is one parameter
// set and no material instance per sword. Effects come from the Niagara pool, so fast swings do not allocate new components.
// cvars: cd.Slash.Enable 1 (0 = old slash for everything), cd.Slash.IntensityMul 1, cd.Slash.ScaleMul 1.
// Test: cd.Slash.Test <kit row> plays a sword's slash in front of the player without changing the weapon.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CDSlashFX.generated.h"

UENUM(BlueprintType)
enum class ECDSlashResult : uint8 { Handled, UseOldSlash };

UCLASS()
class CASTLEDEFENDER_API UCDSlashFX : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// Same inputs as the SpawnSlashFX event. The event fires up to 3 times per swing with TimeOffset 0, 0.06 and 0.12;
	// each sword decides how many of those layers it plays.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Weapons", meta = (ExpandEnumAsExecs = "Result", DefaultToSelf = "Hero"))
	static void PlaySwordSlash(AActor* Hero, double Roll, double ZUp, double TimeOffset, double ScaleMul, ECDSlashResult& Result);

	// Plays a kit row's slash directly. Returns false when the row has no sword slash or the assets are missing.
	static bool PlayRow(AActor* Hero, int32 KitIndex, double Roll, double ZUp, double TimeOffset, double ScaleMul);
};
