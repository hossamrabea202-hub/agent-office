// RealmWaspBase (2026-11-06, i9 Master, owner's order: "battle system for the wasps, two colours and sizes, smart, fly high,
// retreat when low HP so the player or the crossbow soldiers must shoot them; Stranger Things quality").
//
// The native zombie hornet. Spawned by UCDWaspDirector (no Blueprint needed; BP_RealmWasp stays as the legacy wasp).
// Two castes share this class:
//   Drone     - Ember skin, normal size. Fast, hit-and-run stinger. Dodges when it notices it is being aimed at.
//   Matriarch - Blight skin, semi-colossal (settings scale ~3). Slow, heavy, her sting knocks the target down and shakes the
//               camera; drones near her fight harder. Too big to dodge, so she must be out-shot.
//
// Brain (one state machine, thinks every ThinkInterval, moves every tick through CharacterMovement in Flying mode):
//   Arrive  - flies in from the spawn point high above the field (the owner wants them SEEN flying), then
//   Patrol  - circles high over the battlefield anchor (its target area), scanning for a target, then
//   Stalk   - takes a holding point above and behind the target and waits for a dive token from the director
//             (at most 2 wasps dive on one target at a time, so a swarm takes turns instead of piling up), then
//   Dive    - a fast attack run with lead on a moving target, then
//   Spit    - from the stalking point, in range and off cooldown: a wind-up (the sting clip's anticipation) then a slime glob (ACDWaspSpit)
//             that damages, slows and coats the victim; the hero also gets screen goo. Then back to Stalk.
//   Sting   - the sting clip; the hit lands at frame 13 (0.43 s, matches the TGA animation), then
//   Climb   - breaks away up and out of reach, then Stalk again (HitsPerTarget stings on one target, then a new one)
//   Evade   - a short lateral roll, used when a crossbow soldier aims at it, when the player's camera has been on it for a
//             while, or right after a hit. Interrupts Stalk / Patrol / Dive (not Sting).
//   Retreat - HP below RetreatFraction: climbs to RetreatAltitude away from the nearest shooter, weaves at speed, slowly
//             regenerates, returns when HP is back above ReturnFraction or the retreat timed out. After MaxRetreats it stops
//             fleeing and fights "desperate" (faster, no more retreats).
//   Dying   - wings stop, the death clip plays, gravity comes back, it drops; after it rests the body dissolves into sand
//             grains (UCDSandDissolveLibrary) and is destroyed.
// Damage: TakeDamage is overridden and does NOT call Super, so BP graphs on child classes never see AnyDamage (this class owns HP).
// Hit flash through the v2 body material's HitT parameter; wing blur cards get brighter with speed (BlurOpacity).
// XP: on death adds XPValue to the player's int "XP" and calls "CheckLevelUp" by reflection (what BP_RealmWasp did).
// Every number lives in UCDSettings (Project Settings > Game > Castle Defender > Wasps) with cvars for the switches.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "RealmWaspBase.generated.h"

class UCDWaspDirector;
class UAnimSequence;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UAudioComponent;
class USoundWaveProcedural;
class UCDWaspBuzz;
struct FCDWaspCasteSettings;

UENUM(BlueprintType)
enum class EWaspCaste : uint8
{
	Drone     UMETA(DisplayName = "Drone (Ember, normal)"),
	Matriarch UMETA(DisplayName = "Matriarch (Blight, semi-colossal)")
};

UENUM(BlueprintType)
enum class EWaspState : uint8
{
	Arrive, Patrol, Stalk, Dive, Sting, Climb, Evade, Retreat, Dying,
	Spit    // second attack (11-06 evening): a neon slime glob from the stalking point, see CDWaspSpit
};

UENUM()
enum class EWaspClip : uint8 { None, Hover, Fly, Dive, Sting, Death };

UCLASS(Blueprintable)
class CASTLEDEFENDER_API ARealmWaspBase : public ACharacter
{
	GENERATED_BODY()

public:
	ARealmWaspBase();

	// Call between SpawnActorDeferred and FinishSpawning (the director does). Anchor = the point the swarm orbits (the castle gate).
	void Init(EWaspCaste InCaste, const FVector& InAnchor, int32 InWave);

	UFUNCTION(BlueprintPure, Category = "Wasp") EWaspCaste GetCaste() const { return Caste; }
	UFUNCTION(BlueprintPure, Category = "Wasp") EWaspState GetState() const { return State; }
	UFUNCTION(BlueprintPure, Category = "Wasp") float GetHP() const { return HP; }
	UFUNCTION(BlueprintPure, Category = "Wasp") float GetMaxHP() const { return MaxHP; }
	UFUNCTION(BlueprintPure, Category = "Wasp") bool IsWaspDead() const { return State == EWaspState::Dying; }
	UFUNCTION(BlueprintPure, Category = "Wasp") bool IsEvading() const { return State == EWaspState::Evade; }
	UFUNCTION(BlueprintPure, Category = "Wasp") bool IsRetreating() const { return State == EWaspState::Retreat; }
	UFUNCTION(BlueprintPure, Category = "Wasp") bool IsDiving() const { return State == EWaspState::Dive || State == EWaspState::Sting; }
	UFUNCTION(BlueprintPure, Category = "Wasp") AActor* GetWaspTarget() const { AActor* T = Target.Get(); return IsValid(T) ? T : nullptr; }

	// A shooter started aiming at this wasp (crossbow soldiers call it ~0.35 s before they fire). Drones may roll out of the way.
	UFUNCTION(BlueprintCallable, Category = "Wasp")
	void NotifyAimedAt(AActor* Shooter);

	// How likely a ranged shot fired at this wasp lands, 0..1 (size, evasion, retreat distance). Used by the soldier anti-air layer.
	UFUNCTION(BlueprintPure, Category = "Wasp")
	float GetHitChanceFor(const AActor* Shooter) const;

	// Owner's test hooks (also cd.Wasp.Kill / cd.Wasp.Spawn in the director).
	UFUNCTION(BlueprintCallable, Category = "Wasp") void Kill();

	virtual float TakeDamage(float Damage, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	// ---- pure rules, shared with the automation tests (no world) ----
	// Should a wasp with HP/MaxHP and Retreats retreats so far start a retreat?  (HP fraction below RetreatFraction, retreats left)
	static bool ShouldRetreat(float HP, float MaxHP, float RetreatFraction, int32 Retreats, int32 MaxRetreats);
	// Is a retreating wasp ready to come back?  (HP fraction above ReturnFraction, or retreat lasted >= MaxSeconds)
	static bool ShouldReturn(float HP, float MaxHP, float ReturnFraction, float RetreatSeconds, float MaxSeconds);
	// Target score for one candidate. Higher is better; <= 0 means "never". Kind: 0 player, 1 crossbow soldier, 2 other soldier,
	// 3 farmer, 4 cannon (the plan's first target: a sting unloads it), 5 the castle gate control. Claims = wasps already on that target. Dist in cm.
	static float ScoreTarget(int32 Kind, float Dist, int32 Claims, float AggroRange, int32 MaxClaims);
	// Where to aim a dive at a target moving with Velocity, for a wasp Speed away: simple one-step lead, capped at MaxLeadSeconds.
	static FVector LeadPoint(const FVector& TargetPos, const FVector& TargetVel, const FVector& From, float Speed, float MaxLeadSeconds = 0.6f);

protected:
	// ---- state machine ----
	void Think(float Dt);
	void EnterState(EWaspState New);
	void TickMovement(float Dt);
	void TickVisuals(float Dt);
	void TickDying(float Dt);
	void PickTarget();
	bool TargetAlive() const;
	FVector TargetLocation() const;
	FVector TargetVelocity() const;
	float TargetRadius() const;
	FVector GroundUnder(const FVector& P, float MaxDrop = 6000.f) const;
	FVector HoldingPointFor(const FVector& TargetPos) const;
	FVector PatrolPoint(float Time) const;
	FVector RetreatPoint() const;
	AActor* NearestThreat(float& OutDist) const;
	void StartEvade(const FVector& AwayFrom);
	void DoSting();
	void DoSpit();
	void Die(AActor* Killer);
	void AwardXP();
	void ApplyCaste();
	void SetClip(EWaspClip Clip, bool bLoop, bool bForce);
	void SetSpeedLimits(float MaxSpeed, float Accel);
	void SteerTo(const FVector& Goal, float Speed, float Dt, float ArriveRadius = 60.f);
	void FaceVelocity(float Dt, float PitchScale);
	bool PlayerAimingAtMe(float& OutAngleDeg) const;
	const FCDWaspCasteSettings& Stats() const;
	void OnMatriarchStingFX(AActor* Victim, const FVector& HitPoint);

	// ---- data ----
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Wasp") EWaspCaste Caste = EWaspCaste::Drone;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Wasp") EWaspState State = EWaspState::Arrive;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Wasp") float HP = 100.f;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Wasp") float MaxHP = 100.f;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Wasp") int32 Wave = 1;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Wasp") int32 Retreats = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Wasp") bool bDesperate = false;
	FVector Anchor = FVector::ZeroVector;      // what the swarm orbits
	FVector SpawnPoint = FVector::ZeroVector;
	FVector OrbitPoint = FVector::ZeroVector;   // where it circles once after emerging (the crack TargetPoint), zero = none
	TWeakObjectPtr<AActor> Target;
	int32 TargetKind = -1;
	int32 HitsOnTarget = 0;
	FVector StateGoal = FVector::ZeroVector;   // current steering goal
	FVector EvadeDir = FVector::ZeroVector;
	float StateTime = 0.f;
	float ThinkAcc = 0.f;
	float TotalTime = 0.f;
	float PatrolPhase = 0.f;
	float PatrolRadius = 1200.f;
	float PatrolDir = 1.f;
	float RetreatTime = 0.f;
	float RegenAcc = 0.f;
	float StingTimer = -1.f;                    // counts down to the hit frame
	float SpitCooldownTimer = 0.f;
	bool bSpatThisWindup = false;
	bool bStingLanded = false;
	bool bHasDiveToken = false;
	float PlayerAimTime = 0.f;
	float AimReactCooldown = 0.f;
	float HitFlash = 0.f;
	float BlurTarget = 0.4f, BlurNow = 0.4f;
	float LastSpeed = 0.f;
	float BlockedTime = 0.f;
	float DyingTime = 0.f;
	bool bLanded = false;
	bool bDissolving = false;
	float PreferredSide = 1.f;                  // which side of the target this wasp stalks from
	float ThinkJitter = 0.f;
	float LastYaw = 0.f;                        // for the bank angle
	float AnchorGroundZ = 0.f;                  // ground under the anchor, measured once
	float LandTime = 0.f;
	float DissolveStart = 0.f;
	EWaspState ReturnState = EWaspState::Patrol; // where an Evade goes back to
	TWeakObjectPtr<AActor> LastDamageCauser;
	FVector LastHitFrom = FVector::ZeroVector;

	// animation (single-node playback; clips are switched at loop boundaries unless forced, to hide the lack of blending)
	EWaspClip CurrentClip = EWaspClip::None;
	EWaspClip PendingClip = EWaspClip::None;
	bool bPendingLoop = true;
	float PendingTime = 0.f;
	UPROPERTY() TObjectPtr<UAnimSequence> ClipHover;
	UPROPERTY() TObjectPtr<UAnimSequence> ClipFly;
	UPROPERTY() TObjectPtr<UAnimSequence> ClipDive;
	UPROPERTY() TObjectPtr<UAnimSequence> ClipSting;
	UPROPERTY() TObjectPtr<UAnimSequence> ClipDeath;
	UPROPERTY() TArray<TObjectPtr<UMaterialInstanceDynamic>> DynMats;

	// audio: a procedural wing buzz, pitch follows speed, intensity follows state
	UPROPERTY() TObjectPtr<UAudioComponent> Buzz;
	UPROPERTY() TObjectPtr<UCDWaspBuzz> BuzzGen;

	TWeakObjectPtr<UCDWaspDirector> Director;

	friend class UCDWaspDirector;
};
