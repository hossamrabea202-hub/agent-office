// #500 point 3: one place for the game's tuning numbers. Edit them in Project Settings > Game > Castle Defender; saved in Config/DefaultGame.ini
// (plain text: diffs and git history show every change). C++ reads them with GetDefault<UCDSettings>(); Blueprints with "Get CD Settings".
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
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie")
	float ZombieSoldierRange = 2500.f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie")
	float ZombieSoldierHeightRange = 250.f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie")
	float ZombieFarmerRange = 2500.f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie")
	float ZombieNearPlayer = 3000.f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Zombie")
	float ZombieMidPlayer = 6000.f;

	// ---- crowd (crowd/CROWD_PLAN.md)
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd")
	bool bCrowdManagesBodyCollision = false;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd")
	float CrowdFullDetailRange = 2500.f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd")
	float CrowdUpdateInterval = 0.25f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Crowd")
	int32 MaxAliveZombies = 60;

	// ---- data tables (point 3): one row per zombie type / soldier rank instead of numbers spread over Blueprint nodes
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Data", meta = (RequiredAssetDataTags = "RowStructure=/Script/CastleDefender.ZombieTypeRow"))
	TSoftObjectPtr<UDataTable> ZombieTypes;
};

// One zombie type (ZType in BP_Zombie). Make a Data Table with this row struct; the wave manager / BP_Zombie read their numbers from it.
USTRUCT(BlueprintType)
struct CASTLEDEFENDER_API FZombieTypeRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 ZType = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	float MaxHP = 100.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	float AttackDamage = 10.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	float XPValue = 10.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FVector2D WalkSpeedRange = FVector2D(80.f, 145.f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	float RunnerChance = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FVector2D ScaleRange = FVector2D(0.9f, 1.12f);
};
