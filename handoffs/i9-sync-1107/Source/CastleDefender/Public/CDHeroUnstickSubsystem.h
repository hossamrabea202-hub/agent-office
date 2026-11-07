// #510 (owner, wave 15): the hero dropped ~20 m below the ground near X 3091 Y -7716 and was pinned against a wall for 40 s.
// Safety net for the whole map (card step 3): while the hero is BELOW the landscape surface above him by more than
// cd.Hero.UnstickDepth cm, is pushing a direction and still not moving, for cd.Hero.UnstickSeconds, he is put back on the last
// safe ground: the spot where he last stood on the landscape at least 3 s earlier (so never the pit's edge). Logs "[CD] unstick:".
// Three conditions together (under the ground + input + no movement) so a tunnel, a valley or a cutscene never triggers it.
// cd.Hero.Unstick 0 = off. The pit itself still needs the editor fix (card step 1-2).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDHeroUnstickSubsystem.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDHeroUnstickSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override;
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UCDHeroUnstickSubsystem, STATGROUP_Tickables); }

	// Console / Blueprint helper: put the hero back on the last safe ground now. Returns false if none is known yet.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Hero")
	bool UnstickNow();

private:
	struct FSample { FVector Location = FVector::ZeroVector; double Time = -1.0; };
	TArray<FSample> Safe;        // ring of safe-ground samples, one every 0.5 s
	int32 SafeHead = 0;
	double LastSampleTime = -100.0;
	double StuckSince = -1.0;
	double LastUnstick = -100.0;
	FVector LastPos = FVector::ZeroVector;

	bool PickSafe(FVector& Out) const;
	bool UnderLandscape(const class ACharacter* Hero, float& OutDepth) const;
};
