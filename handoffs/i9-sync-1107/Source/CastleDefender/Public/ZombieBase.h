// #500: C++ parent for BP_Zombie. Holds the per-Think hot loops natively; BP_Zombie keeps its look, attacks, montages and states.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "ZombieBase.generated.h"

// 11-06 hit direction for the walker flinches (i5 #519): which side of the zombie the last damage came from.
UENUM(BlueprintType)
enum class ECDHitSide : uint8
{
	Front UMETA(DisplayName = "Front"),
	Back  UMETA(DisplayName = "Back"),
	Left  UMETA(DisplayName = "Left"),
	Right UMETA(DisplayName = "Right")
};

class UAnimMontage;

UCLASS(Abstract, Blueprintable)
class CASTLEDEFENDER_API AZombieBase : public ACharacter
{
	GENERATED_BODY()

public:
	AZombieBase();

	// BP_Zombie Think's target pick (nodes CX_501..zfTargetFarmer17), in one native call. Same rules as the live graph:
	// start from the player; a soldier that is not dying (LifeSpan < 0.01), within ZombieSoldierHeightRange height and ZombieSoldierRange, if strictly nearer;
	// then a farmer that is not Dead, within ZombieFarmerRange, if strictly nearer (equal distance: the earlier pick wins, soldiers before farmers).
	// Writes CurrentTarget. While BP_Zombie still reads GetOwner() as its target, it also sets Owner (bAlsoSetOwner); drop that once the Blueprint reads CurrentTarget.
	UFUNCTION(BlueprintCallable, Category = "Zombie|Brain")
	AActor* PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers);

	// The same, reading soldiers and farmers straight from the crowd registry (no arrays built per call).
	UFUNCTION(BlueprintCallable, Category = "Zombie|Brain")
	AActor* PickAndSetTargetFromRegistry();

	// The current target, or null if it was destroyed since the pick (weak reference: a dead target is never kept alive).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	AActor* GetCurrentTarget() const { AActor* T = CurrentTarget.Get(); return IsValid(T) ? T : nullptr; }

	// Call at the START of the death transition (before the death code sets its collision): the crowd manager stops touching this body.
	UFUNCTION(BlueprintCallable, Category = "Zombie|Crowd")
	void NotifyDying();

	// Think's "heavy part every Nth tick" divisor: 1 within ZombieNearPlayer, 2 within ZombieMidPlayer, else 4 (K2Node_IfThenElse_11).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	int32 GetThinkDivisor() const;

	// Near the player (ZombieNearPlayer) or rendered in the last 0.2 s (K2Node_CallFunction_42 / _43).
	UFUNCTION(BlueprintPure, Category = "Zombie|Brain")
	bool IsFullDetail() const;

	// Dead for the crowd's purposes: being destroyed, or NotifyDying was called, or the Blueprint bool "Dead" is true. Override when a C++ death state exists.
	virtual bool IsDeadForCrowd() const;

	// Engaged by a soldier. Today BP_SoldierSword marks its zombie with CustomTimeDilation 0.999 (fragile; replace with an explicit state later).
	virtual bool IsEngagedForCrowd() const;

	// Reads a Blueprint bool variable from any object. bFound tells whether the variable exists.
	static bool ReadBlueprintBool(const UObject* Object, FName Name, bool* bFound = nullptr);

	// The pure target rule (no world), shared by PickAndSetTarget and the unit tests. Feed candidates with Consider(); Best is the chosen index or INDEX_NONE.
	struct FTargetRule
	{
		FVector Self;
		float BestDistSq;
		float SoldierRangeSq, SoldierHeightRange, FarmerRangeSq;
		int32 Best = INDEX_NONE;

		FTargetRule(const FVector& InSelf, const FVector* Player, float SoldierRange, float InSoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks);
		void ConsiderSoldier(int32 Index, const FVector& Location, bool bValid, bool bDying);
		void ConsiderFarmer(int32 Index, const FVector& Location, bool bValid, bool bDead);
	};

	// Test helper: candidates as plain data. Returns the chosen index in Soldiers (0..), Farmers (Soldiers.Num()..), or INDEX_NONE (keep the player).
	struct FCandidate
	{
		FVector Location;
		bool bValid = true;
		bool bDyingOrDead = false;
	};
	static int32 ChooseTarget(const FVector& Self, const FVector* Player, const TArray<FCandidate>& Soldiers, const TArray<FCandidate>& Farmers,
		float SoldierRange, float SoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks = true);

	// Native brain, stage 1 (2026-11-05). Runs after the Blueprint's own tick, never replaces its Think:
	//   - Unstick: alive, not Attacking, no montage, standing still for cd.Zombie.UnstickSeconds with an AI controller
	//     -> a fresh move order to its target (CurrentTarget, else Owner, else the player). Fixes zombies frozen after a
	//     Think branch called StopMovementImmediately and never resumed.
	//   - No giant: Think turns a zombie into type 5 when its mesh GlobalAnimRateScale < 0.9, which the attack branch itself
	//     sets (0.7), so attackers became x3 belly-crawlers. With cd.Zombie.NoGiant 1 the mesh keeps its spawn size and
	//     offset, the belly-crawl / laying montages are stopped and the walk speed returns to the spawn value.
	// Counters: cd.Zombie.Report prints how often each fix fired.
	virtual void Tick(float DeltaSeconds) override;

	// 11-06 playtest: colossi are not thrown around. Every knockback in the game reaches a zombie through LaunchCharacter
	// (BP_Zombie hit reaction: push + 160 up; Obsidian shockwave). For a colossus the launch is ignored unless
	// cd.Combat.ColossusKnockback 1 (old behaviour). Ordinary zombies are unchanged.
	virtual void LaunchCharacter(FVector LaunchVelocity, bool bXYOverride, bool bZOverride) override;

	// 11-06 candle melt: remember where the last damage came from (closest point of our capsule to the damage causer), so the
	// melt can start at the sword's hit area. Falls back to the chest when nothing was recorded.
	virtual float TakeDamage(float Damage, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;
	FVector GetLastHitPoint() const;
	double GetLastHitTime() const { return LastHitTime; }

	// 11-06 hit direction (i5 flinch wiring). Valid right after ReceiveAnyDamage / AnyDamage fires (TakeDamage ran first).
	// GetLastHitLocal: unit vector in the zombie's own space pointing TOWARDS where the damage came from (X forward, Y right, no Z).
	// GetLastHitSide: that vector folded to Front / Back / Left / Right (45-degree sectors). Front when nothing was recorded.
	UFUNCTION(BlueprintPure, Category = "Zombie|Hit")
	FVector GetLastHitLocal() const { return LastHitLocal; }
	UFUNCTION(BlueprintPure, Category = "Zombie|Hit")
	ECDHitSide GetLastHitSide() const;
	// Seconds since the last damage, or -1 when never hit.
	UFUNCTION(BlueprintPure, Category = "Zombie|Hit")
	float GetLastHitAge() const;
	// Damage of the last hit and who caused it (weak: never keeps the causer alive).
	UFUNCTION(BlueprintPure, Category = "Zombie|Hit")
	float GetLastHitDamage() const { return LastHitDamage; }
	UFUNCTION(BlueprintPure, Category = "Zombie|Hit")
	AActor* GetLastHitCauser() const { AActor* A = LastHitCauser.Get(); return IsValid(A) ? A : nullptr; }

	// 11-06 directional flinch + stagger by weapon (i5 #519 brief, owner's order). Picks the hit reaction montage for the LAST hit:
	// heavy causer (class name contains one of HeavyCauserWords, or damage >= HeavyDamage) -> HitHeavy; damage >= StaggerFraction x MaxHP
	// (Blueprint float "MaxHP", else StaggerDamage) -> HitStagger; else by side: FlinchFront / FlinchBack / FlinchLeft / FlinchRight.
	// An empty set falls back to Front, then to Default (what the graph plays today). Random pick inside a set.
	UFUNCTION(BlueprintPure, Category = "Zombie|Hit")
	UAnimMontage* PickFlinchMontage(UAnimMontage* Default) const;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") TArray<TObjectPtr<UAnimMontage>> FlinchFront;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") TArray<TObjectPtr<UAnimMontage>> FlinchBack;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") TArray<TObjectPtr<UAnimMontage>> FlinchLeft;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") TArray<TObjectPtr<UAnimMontage>> FlinchRight;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") TArray<TObjectPtr<UAnimMontage>> HitStagger;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") TArray<TObjectPtr<UAnimMontage>> HitHeavy;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") float StaggerFraction = 0.4f;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") float StaggerDamage = 40.f;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") float HeavyDamage = 120.f;
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Zombie|Hit") TArray<FString> HeavyCauserWords = { TEXT("Cannon"), TEXT("Charge"), TEXT("Quake"), TEXT("Slam"), TEXT("Fissure") };

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	void CacheSpawnShape();
	void TickUnstick(float DeltaSeconds);
	void TickGroundSnap(float DeltaSeconds);   // 11-06: blob/pod zombies are spawned +95 cm then scaled up: the taller capsule ends up in the ground
	float GroundSnapTimer = 0.f;
	float GroundSnapWindow = 4.f;
	FVector GroundSnapScale = FVector::OneVector;
	void TickNoGiant();
	void TickWaveManagerRef(float DeltaSeconds);   // fills BP_Zombie.WMRef when BeginPlay found no wave manager (blob zombies)
	float WMRefRetry = 0.f;
	bool bWMRefOK = false;

	FVector SpawnMeshScale = FVector::OneVector;
	FVector SpawnMeshLocation = FVector::ZeroVector;
	float SpawnWalkSpeed = 0.f;
	bool bSpawnShapeCached = false;
	float StillSeconds = 0.f;
	float UnstickCooldown = 0.f;

	TWeakObjectPtr<AActor> CurrentTarget;
	FVector LastHitPoint = FVector::ZeroVector;
	double LastHitTime = -1.0;
	FVector LastHitLocal = FVector::ForwardVector;   // zombie-local, towards the damage source
	float LastHitDamage = 0.f;
	TWeakObjectPtr<AActor> LastHitCauser;
	bool bDying = false;

	// Transition: BP_Zombie still uses Owner as its target slot. Turn off when the Blueprint reads CurrentTarget (Owner also drives net ownership).
	UPROPERTY(EditDefaultsOnly, Category = "Zombie|Brain")
	bool bAlsoSetOwner = true;

private:
	float DistanceToPlayer() const;
	AActor* FinishPick(AActor* Player, AActor* Picked);
};
