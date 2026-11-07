// Test-only poolable actor for CastleDefender.Pool.* automation tests (Private/Tests/CDPoolTest.cpp). Not for gameplay; hidden from class pickers.
// Each Reaction makes one callback do something hostile (destroy / release / re-acquire itself) to prove the pool survives it.
#pragma once

#include "CoreMinimal.h"
#include "CDPoolSubsystem.h"
#include "GameFramework/Actor.h"
#include "CDPoolTestActor.generated.h"

class UProjectileMovementComponent;

UENUM()
enum class ECDPoolTestReaction : uint8
{
	None,
	DestroyOnAcquired,
	ReleaseOnAcquired,
	DestroyOnReleased,
	DestroyOnMoverDeactivated,
	ReleaseOnMoverActivated,
	DestroyOnMoverActivated
};

UCLASS(NotBlueprintable, HideDropdown, NotPlaceable)
class CASTLEDEFENDER_API ACDPoolTestActor : public AActor, public ICDPoolable
{
	GENERATED_BODY()

public:
	ACDPoolTestActor();

	UPROPERTY() TObjectPtr<UProjectileMovementComponent> Mover;
	UPROPERTY() TObjectPtr<UActorComponent> Ticker;   // a plain ticking component

	ECDPoolTestReaction Reaction = ECDPoolTestReaction::None;
	int32 Acquired = 0, Released = 0;

	virtual void OnAcquired_Implementation() override;
	virtual void OnReleased_Implementation() override;
	virtual void BeginPlay() override;

private:
	UFUNCTION() void HandleMoverActivated(UActorComponent* Component, bool bReset);
	UFUNCTION() void HandleMoverDeactivated(UActorComponent* Component);
	ECDPoolTestReaction TakeReaction(ECDPoolTestReaction Which);   // fires once
	UCDPoolSubsystem* Pool() const;
};
