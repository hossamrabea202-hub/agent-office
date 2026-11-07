// Cloth budget for soldier capes (owner 2026-11-05: "no high ms cost").
// Every cd.Cloth.Interval s (0.25) the nearest cd.Cloth.MaxActive (12) soldiers / medics / commanders within cd.Cloth.Range (1500 cm)
// of the camera simulate their cape cloth; every other one has its clothing simulation suspended (the cape holds its last pose).
// cd.Cloth.Budget 0 = everyone simulates, as authored. Game worlds only.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDClothBudget.generated.h"

class USkeletalMeshComponent;

UCLASS()
class CASTLEDEFENDER_API UCDClothBudgetSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

private:
	void Step();
	void ResumeAll();
	FTimerHandle Timer;
	TMap<TWeakObjectPtr<USkeletalMeshComponent>, bool> Suspended;
	float RescanIn = 0.f;
	TArray<TWeakObjectPtr<USkeletalMeshComponent>> Cloth;
};
