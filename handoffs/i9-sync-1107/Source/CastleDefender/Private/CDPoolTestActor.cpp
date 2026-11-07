#include "CDPoolTestActor.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "GameFramework/ProjectileMovementComponent.h"

ACDPoolTestActor::ACDPoolTestActor()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Mover = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Mover"));
	Mover->ProjectileGravityScale = 0.f;
	Mover->InitialSpeed = 100.f;
	Ticker = CreateDefaultSubobject<USceneComponent>(TEXT("Ticker"));
	Ticker->PrimaryComponentTick.bCanEverTick = true;
	Ticker->PrimaryComponentTick.bStartWithTickEnabled = true;
	Cast<USceneComponent>(Ticker)->SetupAttachment(RootComponent);
}

void ACDPoolTestActor::BeginPlay()
{
	Super::BeginPlay();
	Mover->OnComponentActivated.AddDynamic(this, &ACDPoolTestActor::HandleMoverActivated);
	Mover->OnComponentDeactivated.AddDynamic(this, &ACDPoolTestActor::HandleMoverDeactivated);
}

UCDPoolSubsystem* ACDPoolTestActor::Pool() const
{
	return GetWorld() ? GetWorld()->GetSubsystem<UCDPoolSubsystem>() : nullptr;
}

ECDPoolTestReaction ACDPoolTestActor::TakeReaction(ECDPoolTestReaction Which)
{
	if (Reaction != Which)
	{
		return ECDPoolTestReaction::None;
	}
	Reaction = ECDPoolTestReaction::None;
	return Which;
}

void ACDPoolTestActor::OnAcquired_Implementation()
{
	++Acquired;
	if (TakeReaction(ECDPoolTestReaction::DestroyOnAcquired) != ECDPoolTestReaction::None) { Destroy(); }
	else if (TakeReaction(ECDPoolTestReaction::ReleaseOnAcquired) != ECDPoolTestReaction::None) { Pool()->ReleasePooledActor(this); }
}

void ACDPoolTestActor::OnReleased_Implementation()
{
	++Released;
	if (TakeReaction(ECDPoolTestReaction::DestroyOnReleased) != ECDPoolTestReaction::None) { Destroy(); }
}

void ACDPoolTestActor::HandleMoverActivated(UActorComponent* Component, bool bReset)
{
	if (TakeReaction(ECDPoolTestReaction::ReleaseOnMoverActivated) != ECDPoolTestReaction::None) { Pool()->ReleasePooledActor(this); }
	else if (TakeReaction(ECDPoolTestReaction::DestroyOnMoverActivated) != ECDPoolTestReaction::None) { Destroy(); }
}

void ACDPoolTestActor::HandleMoverDeactivated(UActorComponent* Component)
{
	if (TakeReaction(ECDPoolTestReaction::DestroyOnMoverDeactivated) != ECDPoolTestReaction::None) { Destroy(); }
}
