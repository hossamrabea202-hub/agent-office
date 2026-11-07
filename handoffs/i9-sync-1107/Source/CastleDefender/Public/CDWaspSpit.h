// CDWaspSpit (2026-11-06 evening, owner: "they can spit mushy slimy texture on enemies like a second attack").
//   ACDWaspSpit          - the glob: a small sphere in the caste's neon slime material, ProjectileMovement with a little gravity, a
//                          faint light. On touching anything that is not a wasp: damage, a slime splat decal on the world, and the
//                          victim gets a UCDWaspSlimeComponent. Then it is gone.
//   UCDWaspSlimeComponent- the "coated" state on the victim for SlimeSeconds: a dripping neon slime decal stuck to the body
//                          (UDecalComponent, Fade parameter counts down), the victim walks at SlimeSlow x speed (re-applied every
//                          tick after the Blueprint's own speed writes, restored at the end), and when the victim is the hero the
//                          screen gets the goo post-process (WaspSlimeScreenMaterial) fading out with the slime.
//                          A second hit refreshes the timer and adds a splat.
// Materials come from Tools/Wasp/wasp_fx_materials.py; every one is optional (null = no visual, the gameplay still happens).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/ActorComponent.h"
#include "CDWaspSpit.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UProjectileMovementComponent;
class UPointLightComponent;
class UDecalComponent;
class UMaterialInstanceDynamic;
enum class EWaspCaste : uint8;

UCLASS(NotBlueprintable)
class CASTLEDEFENDER_API ACDWaspSpit : public AActor
{
	GENERATED_BODY()
public:
	ACDWaspSpit();
	// Called by the wasp right after spawning: who spat, which caste (stats), where to.
	void Launch(AActor* Spitter, EWaspCaste InCaste, const FVector& Velocity);
	virtual void Tick(float DeltaSeconds) override;

protected:
	UFUNCTION() void OnOverlap(UPrimitiveComponent* OverlappedComp, AActor* Other, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& Sweep);
	UFUNCTION() void OnHit(UPrimitiveComponent* HitComp, AActor* Other, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit);
	void Splat(AActor* Victim, const FVector& Where, const FVector& Normal);

	UPROPERTY() TObjectPtr<USphereComponent> Sphere;
	UPROPERTY() TObjectPtr<UStaticMeshComponent> Glob;
	UPROPERTY() TObjectPtr<UProjectileMovementComponent> Move;
	UPROPERTY() TObjectPtr<UPointLightComponent> Light;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> GlobMat;
	TWeakObjectPtr<AActor> Owner_;
	EWaspCaste Caste;
	bool bDone = false;
	float Age = 0.f;
};

UCLASS(NotBlueprintable)
class CASTLEDEFENDER_API UCDWaspSlimeComponent : public UActorComponent
{
	GENERATED_BODY()
public:
	UCDWaspSlimeComponent();
	// Put slime on Victim (adds the component the first time, refreshes it after). Returns the component.
	static UCDWaspSlimeComponent* Apply(AActor* Victim, EWaspCaste Caste, const FVector& HitPoint, const FVector& FromDir);

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void OnComponentDestroyed(bool bDestroyingHierarchy) override;

protected:
	void Refresh(EWaspCaste Caste, const FVector& HitPoint, const FVector& FromDir);
	void EndSlime();

	UPROPERTY() TArray<TObjectPtr<UDecalComponent>> Decals;
	UPROPERTY() TArray<TObjectPtr<UMaterialInstanceDynamic>> DecalMats;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> ScreenMat;
	float Remaining = 0.f;
	float Total = 1.f;
	float Slow = 1.f;
	float BaseSpeed = -1.f;
	float LastSet = -1.f;
	bool bIsHero = false;
	bool bEnded = false;
};
