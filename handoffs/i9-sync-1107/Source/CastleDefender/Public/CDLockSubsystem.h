// 11-06 owner's order: actors tagged CDLock (the castle's main towers) must never be disabled. This world subsystem forces them
// visible, collidable and un-destroyed at every BeginPlay and logs any actor that something else hid. Editor scripts must skip the tag too.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDLockSubsystem.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDLockSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;

	// Re-asserts the lock now (also callable from Blueprint / console helpers). Returns how many actors it had to fix.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Lock")
	int32 EnforceLocks();

private:
	void Enforce(bool bLog);
	FTimerHandle RecheckHandle;
};
