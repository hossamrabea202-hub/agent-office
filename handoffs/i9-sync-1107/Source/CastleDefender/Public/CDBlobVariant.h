// Slime blob variation (owner, 2026-11-06: "make a variation, some spawn zombies some spawn big mouth").
// Touches no Blueprint: when BP_JellyBlob spawns, a share of blobs become a darker, larger crimson variant. When such a blob hatches
// (BP_ZombieJellyShield appears) the hatched zombie and its shield are replaced by a BP_FleshBrute. A cap keeps it fair.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDBlobVariant.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDBlobVariantSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()
public:
	virtual bool DoesSupportWorldType(const EWorldType::Type T) const override { return T == EWorldType::Game || T == EWorldType::PIE; }
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

private:
	FDelegateHandle SpawnHandle;
	void OnSpawned(AActor* A);
	void MakeVariant(AActor* Blob);
	void Hatch(AActor* Shield);
};
