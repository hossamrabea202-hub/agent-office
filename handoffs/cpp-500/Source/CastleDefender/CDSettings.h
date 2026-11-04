// #500 point 3: one place for the game's tuning numbers. Edit them in Project Settings > Game > Castle Defender; saved in Config/DefaultGame.ini
// (plain text: diffs and git history show every change). C++ reads them with GetDefault<UCDSettings>(); Blueprints with "Get CD Settings".
// Status per setting is in its tooltip: [used] = read by code now, [not wired yet] = designed, nothing reads it yet.
#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "Engine/DataTable.h"
#include "CDSettings.generated.h"

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Castle Defender"))
class CASTLEDEFENDER_API UCDSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UCDSettings() { CategoryName = TEXT("Game"); }

	UFUNCTION(BlueprintPure, Category = "Castle Defender", meta = (DisplayName = "Get CD Settings"))
	static const UCDSettings* Get() { return GetDefault<UCDSettings>(); }

	// ---- zombie brain (BP_Zombie Think, read from the live graph 11-04)
	/** [used] Soldier range for a zombie's target pick, cm. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie", meta = (ClampMin = "0", UIMax = "10000"))
	float ZombieSoldierRange = 2500.f;

	/** [used] Max height difference to a soldier target, cm (soldiers up on the wall are ignored). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie", meta = (ClampMin = "0", UIMax = "2000"))
	float ZombieSoldierHeightRange = 250.f;

	/** [used] Farmer range for a zombie's target pick, cm. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie", meta = (ClampMin = "0", UIMax = "10000"))
	float ZombieFarmerRange = 2500.f;

	/** [used] Within this distance to the player a zombie thinks fully every Think (divisor 1), cm. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie", meta = (ClampMin = "0", UIMax = "20000"))
	float ZombieNearPlayer = 3000.f;

	/** [used] Within this distance divisor 2, beyond it 4, cm. Must be >= ZombieNearPlayer. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie", meta = (ClampMin = "0", UIMax = "40000"))
	float ZombieMidPlayer = 6000.f;

	/** [used] Blueprint parity: with no player, no soldier / farmer is picked (GetDistanceTo(None) = 0). Off = pick the nearest valid target. TGA's spec decides. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie")
	bool bZombieNoPlayerBlocksTargets = true;

	// ---- crowd (crowd/CROWD_PLAN.md)
	/** [used] Run the C1 body-collision rule natively (then remove BPC_CrowdTier). Off until parity is tested. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd")
	bool bCrowdManagesBodyCollision = false;

	/** [used] Full body collision within this distance of the player, cm. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd", meta = (ClampMin = "0", UIMax = "20000"))
	float CrowdFullDetailRange = 2500.f;

	/** [used] Seconds between crowd updates (min 0.05). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd", meta = (ClampMin = "0.05", UIMax = "2"))
	float CrowdUpdateInterval = 0.25f;

	/** [used by Crowd > Can Spawn Zombie; spawners not wired yet] Alive zombie cap; 0 = no cap. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd", meta = (ClampMin = "0", UIMax = "500"))
	int32 MaxAliveZombies = 60;

	// ---- data tables (point 3)
	/** [not wired yet] One row per zombie type (FZombieTypeRow); the wave manager will read MaxHP / damage / speeds from it. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Data", meta = (RequiredAssetDataTags = "RowStructure=/Script/CastleDefender.ZombieTypeRow"))
	TSoftObjectPtr<UDataTable> ZombieTypes;

#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& Event) override
	{
		Super::PostEditChangeProperty(Event);
		ZombieMidPlayer = FMath::Max(ZombieMidPlayer, ZombieNearPlayer);
	}
#endif
};

// One zombie type (ZType in BP_Zombie). [not wired yet] Make a Data Table with this row struct; nothing reads it until the wave manager is converted.
USTRUCT(BlueprintType)
struct CASTLEDEFENDER_API FZombieTypeRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
	int32 ZType = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
	float MaxHP = 100.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
	float AttackDamage = 10.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
	float XPValue = 10.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FVector2D WalkSpeedRange = FVector2D(80.f, 145.f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1"))
	float RunnerChance = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FVector2D ScaleRange = FVector2D(0.9f, 1.12f);
};
