// #500 point 3: one place for the game's tuning numbers. Edit them in Project Settings > Game > Castle Defender; saved in Config/DefaultGame.ini
// (plain text: diffs and git history show every change). C++ reads them with GetDefault<UCDSettings>(); Blueprints with "Get CD Settings".
// Status per setting is in its tooltip: [used] = read by code now, [not wired yet] = designed, nothing reads it yet.
#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "Engine/DataTable.h"
#include "CDSettings.generated.h"

class UMaterialInterface;
class USkeletalMesh;
class UAnimSequence;
class UStaticMesh;

// One wasp caste (11-06 wasp battle system, ARealmWaspBase). Distances in cm, speeds in cm/s, times in seconds.
USTRUCT(BlueprintType)
struct CASTLEDEFENDER_API FCDWaspCasteSettings
{
	GENERATED_BODY()

	/** Actor scale (the Drone is the mesh at 1.0; the Matriarch is semi-colossal). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.2", UIMax = "6")) float Scale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1")) float MaxHP = 110.f;
	/** Extra HP per wave after the first wasp wave (keeps late waves dangerous). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float HPPerWave = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float StingDamage = 16.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) int32 XPValue = 8;

	/** Cruise speed while patrolling / flying between points. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "50")) float CruiseSpeed = 1100.f;
	/** Speed while holding a stalking point (small repositioning). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "50")) float HoverSpeed = 500.f;
	/** Attack run speed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "50")) float DiveSpeed = 2300.f;
	/** Speed of the retreat climb and of evasive rolls. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "50")) float EscapeSpeed = 1900.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "100")) float Acceleration = 3200.f;

	/** Patrol band above the ground under the swarm anchor. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float PatrolAltitudeMin = 1400.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float PatrolAltitudeMax = 2000.f;
	/** Holding point above the target before a dive. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float StalkHeight = 800.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float StalkDistance = 600.f;
	/** Seconds a wasp holds its stalking point before it dives even without the swarm's go (it gets impatient). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float StalkPatience = 3.5f;
	/** Reach of the sting in front of the wasp (plus the target's capsule radius). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float StingReach = 190.f;
	/** Stings on one target before it picks another. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1")) int32 HitsPerTarget = 2;
	/** Knockback impulse on the stung target (0 = none). The Matriarch knocks soldiers and the hero down. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float Knockback = 0.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bCameraShakeOnSting = false;

	/** Retreat when HP falls below this fraction of MaxHP. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1")) float RetreatFraction = 0.35f;
	/** Come back when HP is above this fraction again. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1")) float ReturnFraction = 0.7f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float RetreatRegenPerSecond = 4.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1")) float RetreatMaxSeconds = 25.f;
	/** Height of the retreat orbit above the ground. High enough to be out of the fight, low enough for a good shot. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float RetreatAltitude = 3200.f;
	/** How far from the nearest shooter it keeps while retreating. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float RetreatDistance = 3500.f;
	/** After this many retreats it stops fleeing and fights to the death (faster, "desperate"). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) int32 MaxRetreats = 2;

	/** Chance to roll out of the way when a crossbow soldier aims at it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1")) float DodgeChance = 0.45f;
	/** Seconds the player's camera must stay on it before it jukes (0 = never reacts to the player's aim). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float PlayerAimReactSeconds = 0.7f;
	/** Base chance that a crossbow soldier's bolt hits it (size). Evasion and distance reduce it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1")) float BaseHitChance = 0.72f;

	/** Wing buzz: fundamental in Hz at cruise (the Matriarch is lower), and volume. 0 volume = silent. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "20", UIMax = "600")) float BuzzPitchHz = 170.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "2")) float BuzzVolume = 0.55f;

	// ---- spit (second attack, 11-06 evening): a glob of neon slime; on a hit it damages, slows and coats the victim (UCDWaspSlimeComponent)
	UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bCanSpit = true;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float SpitDamage = 10.f;
	/** Spits only from a stalking point between these distances to the target. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float SpitRangeMin = 500.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) float SpitRangeMax = 2200.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.5")) float SpitCooldown = 6.f;
	/** Chance per brain tick (while in range and off cooldown) to spit instead of waiting for the dive. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1")) float SpitChance = 0.35f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "200")) float SpitSpeed = 2600.f;
	/** Glob radius (cm) and how long the slime stays on the victim; the victim moves at SlimeSlow x speed while coated. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "5")) float SpitRadius = 18.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0")) float SlimeSeconds = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.1", ClampMax = "1")) float SlimeSlow = 0.6f;
	/** Chance that a sting on the hero infects (BPC_Infection.Infected), the #156 "poison" rule. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1")) float StingInfectChance = 0.3f;
	/** The caste's neon: skin bubbles glow, spit glob, slime. Drone teal, Matriarch violet (both away from the amber torchlight). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) FLinearColor NeonColor = FLinearColor(0.15f, 0.85f, 1.f, 1.f);
	/** Materials made by Tools/Wasp/wasp_fx_materials.py (null = plain fallbacks). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UMaterialInterface> SpitMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UMaterialInterface> SlimeDecalMaterial;

	/** Materials for the mesh slots 0 body, 1 wings, 2 hair, 3 wing blur (the v2 TGA wasp). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UMaterialInterface> BodyMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UMaterialInterface> WingsMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UMaterialInterface> HairMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UMaterialInterface> WingBlurMaterial;
};

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Castle Defender"))
class CASTLEDEFENDER_API UCDSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UCDSettings();

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

	// ---- wasps (11-06, ARealmWaspBase + UCDWaspDirector). Runtime switches: cd.Wasp.Enable, cd.Wasp.Debug, cd.Wasp.Spawn, cd.Wasp.Kill.
	/** [used] First wave with wasps. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "1")) int32 WaspFirstWave = 2;
	/** [used] Drones in the first wasp wave, drones added per later wave, and the cap. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0")) int32 WaspDronesBase = 3;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0")) float WaspDronesPerWave = 1.5f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0")) int32 WaspDronesMax = 14;
	/** [used] First wave with a Matriarch, then one every Nth wave; two from WaspMatriarchPairWave on. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "1")) int32 WaspMatriarchFirstWave = 4;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "1")) int32 WaspMatriarchEveryNthWave = 3;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "1")) int32 WaspMatriarchPairWave = 10;
	/** [used] Seconds between two spawns of one flight (they arrive as a stream, not a blob). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0")) float WaspSpawnInterval = 0.7f;
	/** [used] Where the flight appears: this far from the anchor (toward the zombie spawn) and this high above the ground. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0")) float WaspSpawnDistance = 7000.f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0")) float WaspSpawnAltitude = 2600.f;
	/** [used] Swarm rules: wasps that may dive on one target at once (a Matriarch counts double), wasps that may hunt the hero at once. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "1")) int32 WaspMaxDiversPerTarget = 2;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "1")) int32 WaspMaxOnHero = 3;
	/** [used] Targets farther than this from the wasp are ignored. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "500")) float WaspAggroRange = 8000.f;
	/** [used] Seconds between brain updates (movement is every frame). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0.05", UIMax = "1")) float WaspThinkInterval = 0.15f;
	/** [used] #169 stage 3: flights only once the wave manager's SwarmUnlocked is true (set by the realm breach). Off by default because nothing sets that flag yet. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps") bool bWaspRequireSwarmUnlocked = false;
	/** [used] Seconds a fresh wasp circles the crack mouth before it heads for the battlefield (the plan: "circles once"). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps", meta = (ClampMin = "0")) float WaspOrbitSecondsAtCrack = 4.5f;
	/** [used] Turn the Blueprint wave manager's own swarm spawn off (SwarmEveryNthWave set very high) so wasps come only from this system. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps") bool bWaspReplacesBlueprintSwarm = true;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps") FCDWaspCasteSettings WaspDrone;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps") FCDWaspCasteSettings WaspMatriarch;

	/** [used] Shared wasp assets (the TGA v2 import). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<USkeletalMesh> WaspMesh;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<UAnimSequence> WaspClipHover;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<UAnimSequence> WaspClipFly;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<UAnimSequence> WaspClipDive;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<UAnimSequence> WaspClipSting;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<UAnimSequence> WaspClipDeath;
	/** [used] Spit glob mesh (engine sphere by default) and the screen-goo post-process material shown when the hero is spat on (null = none). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<UStaticMesh> WaspSpitMesh;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Assets") TSoftObjectPtr<UMaterialInterface> WaspSlimeScreenMaterial;

	// ---- crossbow soldiers against wasps (ASoldierBase anti-air layer; cd.Soldier.AntiAir 0 = off)
	/** [used] Range, damage per hit, seconds between shots, aim time before the shot, and the bolt's flight speed (BP_SoldierBolt lifespan rule: distance / 5200). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Soldiers", meta = (ClampMin = "100")) float SoldierAARange = 3200.f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Soldiers", meta = (ClampMin = "0")) float SoldierAADamage = 26.f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Soldiers", meta = (ClampMin = "0.2")) float SoldierAAReload = 2.4f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Soldiers", meta = (ClampMin = "0")) float SoldierAAAimTime = 0.35f;
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Soldiers", meta = (ClampMin = "100")) float SoldierAABoltSpeed = 5200.f;
	/** [used] A soldier busy with ground zombies only shoots a wasp that is diving at him or within this distance. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Wasps|Soldiers", meta = (ClampMin = "0")) float SoldierAASelfDefenceRange = 700.f;

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
