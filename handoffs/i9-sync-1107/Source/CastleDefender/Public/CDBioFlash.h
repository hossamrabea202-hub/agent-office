// Bio reaction on jelly mines and blobs (owner, 2026-11-07: "a shine slide of bio activity, a glimpse that something happened,
// immediate reaction to touch or shoot or attack, then the hatch").
// BP_JellyBlob sets TrigT the moment the hero crosses TriggerRadius or the blob takes damage, and hatches 3 s later.
// The visible mesh of a mine is Crust, on the shared corruption bubble material, so nothing is added to that material: from TrigT on,
// each visible mesh of the blob gets the additive overlay M_CD_BioFlash, with elapsed seconds written every frame (no shader clock).
// Touches no Blueprint. cd.Blob.BioFlash 0 turns it off; cd.Blob.BioBoost scales the brightness.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDBioFlash.generated.h"

class UMaterialInterface;
class UMaterialInstanceDynamic;
class UMeshComponent;

UCLASS()
class CASTLEDEFENDER_API UCDBioFlash : public UTickableWorldSubsystem
{
	GENERATED_BODY()
public:
	virtual bool DoesSupportWorldType(const EWorldType::Type T) const override { return T == EWorldType::Game || T == EWorldType::PIE; }
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	struct FBlob
	{
		TWeakObjectPtr<AActor> Actor;
		bool bActive = false;
		TArray<TWeakObjectPtr<UMeshComponent>> Meshes;
	};
	TArray<FBlob> Blobs;
	UPROPERTY() TObjectPtr<UMaterialInterface> Overlay = nullptr;
	UPROPERTY() TArray<TObjectPtr<UMaterialInstanceDynamic>> Live;   // keeps the running overlays alive
	TMap<TWeakObjectPtr<AActor>, TWeakObjectPtr<UMaterialInstanceDynamic>> Mids;
	FDelegateHandle SpawnHandle;
	void Track(AActor* A);
	void Start(FBlob& B);
	void Finish(FBlob& B);
};
