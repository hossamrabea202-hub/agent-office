// Blade trail (2026-11-06, owner: the old arc was "not following the real axis of sword attacks").
// Keeps a rolling history of the equipped KitWeapon's hilt and tip every frame; a swing draws a ribbon through the path the blade
// really took, from a little before the hit frame to a little after, then drains from the tail. One section, rebuilt only while
// visible, nothing allocated between swings. Material: the owner's classroom slash (MI_ClassroomSlash_Add), driven by MPC_CDSlash.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDSlashTrail.generated.h"

class UProceduralMeshComponent;
class UStaticMeshComponent;
class UMaterialInterface;

UCLASS()
class CASTLEDEFENDER_API UCDSlashTrailSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()
public:
	virtual bool DoesSupportWorldType(const EWorldType::Type T) const override { return T == EWorldType::Game || T == EWorldType::PIE; }
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UCDSlashTrailSubsystem, STATGROUP_Tickables); }

	// WidthMul scales the ribbon across the blade, Speed shortens the trail for quick weapons.
	void StartSwing(float WidthMul, float Speed, const FLinearColor& CoreColor, const FLinearColor& EdgeColor, float Intensity);

private:
	struct FSample { FVector Grip; FVector Dir; double Len; double Time; FVector Tip() const { return Grip + Dir * Len; } };
	TArray<FSample> Samples;
	UPROPERTY(Transient) TObjectPtr<AActor> MeshActor;
	UPROPERTY(Transient) TObjectPtr<UProceduralMeshComponent> Mesh;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> Material;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> GlowMaterial;
	TWeakObjectPtr<UStaticMeshComponent> Weapon;
	TWeakObjectPtr<UStaticMeshComponent> DefaultSword;
	double SwingAt = -100.0, WeaponSearchAt = -100.0, NextTestAttack = 0.0;
	float Width = 1.f, Pre = 0.45f, Post = 0.25f, Fade = 0.32f, SpeedMul = 1.f, BaseIntensity = 6.f;
	FLinearColor Core = FLinearColor::White, Edge = FLinearColor::White;
	double StrikeStart = -1.0, SparkAt = -100.0;
	FVector SparkPos = FVector::ZeroVector, ArcAxis = FVector::ZeroVector;
	double ArcRate = 0.0, ArcTotal = 1.0;
	bool bTestKeyDown = false;
	bool bVisible = false;

	UStaticMeshComponent* FindWeapon();
	// 11-06 night: the CK kit meshes are stored about 1 cm long and the kit's attach resets the component scale to 1, so every shop weapon was invisible and the old default sword stayed in the hand.
	void SyncHand(UStaticMeshComponent* Kit);
	void Rebuild(double Tail, double Head, float FadeA, float Life);
	bool FindStrike(double Earliest, double Latest, double& OutStart, double& OutEnd) const;
	FSample Sample(double T) const;
};
