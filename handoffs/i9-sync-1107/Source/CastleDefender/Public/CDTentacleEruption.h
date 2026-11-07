// Castle Defender, 2026-11-06. Tentacle ground eruption: a RUNTIME event, never a pre-placed base (card #545, SPEC_1106.md step 2).
// Beats (spec): TELL -4 s (rumble, light shake, ground bulge) -> HEAVE -1.5 s (crack, dust vents) -> BREACH 0 (base + slabs,
// dust column, hard shake, hit-stop, boom) -> RISE 0..2.5 s (arm up with overshoot + damped settle) -> SETTLE to 7 s.
// Step 2 scope: timeline + placeholder dust + shake + sound, base and arm spawned/revealed at T0. Niagara, slabs, crack
// decal, Sequencer shot come in later steps and hook into the Blueprint events below. Nothing is placed in the level by this file.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CDTentacleEruption.generated.h"

class UStaticMeshComponent;
class UParticleSystem;
class UParticleSystemComponent;
class USoundBase;
class UCameraShakeBase;
class UMaterialInterface;

UENUM(BlueprintType)
enum class ECDEruptionPhase : uint8 { Idle, Tell, Heave, Breach, Rise, Settle, Done };

UCLASS(Blueprintable)
class CASTLEDEFENDER_API ACDTentacleEruption : public AActor
{
	GENERATED_BODY()
public:
	ACDTentacleEruption();

	// ---- timing (seconds), spec defaults
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Timing") float TellSeconds = 2.5f;     // -4.0 .. -1.5
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Timing") float HeaveSeconds = 1.5f;    // -1.5 .. 0
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Timing") float RiseSeconds = 2.5f;     // 0 .. 2.5
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Timing") float SettleSeconds = 4.5f;   // 2.5 .. 7
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Timing") float HitStopSeconds = 0.1f;  // global time dilation dip at BREACH
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Timing") float RiseOvershoot = 0.12f;  // 12 % past the end height, then damped settle

	// ---- base (spawned at T0, never visible before)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Base") TObjectPtr<UStaticMesh> BaseMesh;        // SM_TentacleSporeBase_A/B
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Base") TObjectPtr<UStaticMesh> BaseCollisionMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Base") float BaseScale = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Base") float BaseSinkCm = 40.f;           // base starts this much lower and heaves up to its rest height during BREACH..RISE
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Base") float DomeRadiusCm = 900.f;        // ground bulge stand-in during TELL/HEAVE (hidden dome, scaled up; WPO material later)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Base") float DomeHeightCm = 120.f;

	// ---- arm: the tentacle family to reveal and raise at T0 (already placed hidden underground, like rise541 did) or spawned by the caller
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Arm") TObjectPtr<AActor> ArmActor;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Arm") float ArmStartZ = 0.f;           // world Z while hidden
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Arm") float ArmEndZ = 0.f;             // world Z at rest
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Arm") bool bArmMoveAttached = true;     // move everything attached to the arm with it

	// ---- placeholders (step 2): swapped for Niagara / authored assets in later steps
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|FX") TObjectPtr<UParticleSystem> DustVentFX;    // HEAVE: small vents
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|FX") TObjectPtr<UParticleSystem> DustColumnFX;  // BREACH: column
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|FX") TObjectPtr<UMaterialInterface> CrackDecal; // HEAVE: radial crack (optional)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|FX") float CrackRadiusCm = 700.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Audio") TObjectPtr<USoundBase> RumbleSound;    // TELL
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Audio") TObjectPtr<USoundBase> BreachSound;    // BREACH
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Audio") TObjectPtr<USoundBase> RoarSound;      // end of RISE
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Camera") TSubclassOf<UCameraShakeBase> TellShake;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Camera") TSubclassOf<UCameraShakeBase> BreachShake;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Camera") float ShakeInnerRadius = 1500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Eruption|Camera") float ShakeOuterRadius = 9000.f;

	// ---- control
	UFUNCTION(BlueprintCallable, Category = "Eruption") void Begin();                 // starts at TELL
	UFUNCTION(BlueprintCallable, Category = "Eruption") void Abort();                 // stops everything, leaves whatever is already out
	UFUNCTION(BlueprintPure, Category = "Eruption") ECDEruptionPhase GetPhase() const { return Phase; }
	UFUNCTION(BlueprintPure, Category = "Eruption") float GetPhaseAlpha() const { return PhaseAlpha; }
	UFUNCTION(BlueprintPure, Category = "Eruption") bool IsDone() const { return Phase == ECDEruptionPhase::Done; }

	// Spawn one at a ground point and start it. Base/arm/FX come from the class defaults of EruptionClass (a Blueprint child sets them).
	UFUNCTION(BlueprintCallable, Category = "Eruption", meta = (WorldContext = "WorldContext"))
	static ACDTentacleEruption* SpawnEruption(UObject* WorldContext, TSubclassOf<ACDTentacleEruption> EruptionClass, FVector GroundLocation, float Yaw, AActor* Arm, float InArmStartZ, float InArmEndZ, bool bBeginNow = true);

	// ---- hooks for the later steps (Niagara, slabs, Sequencer): fire once per beat
	UFUNCTION(BlueprintImplementableEvent, Category = "Eruption") void OnTell();
	UFUNCTION(BlueprintImplementableEvent, Category = "Eruption") void OnHeave();
	UFUNCTION(BlueprintImplementableEvent, Category = "Eruption") void OnBreach();
	UFUNCTION(BlueprintImplementableEvent, Category = "Eruption") void OnRiseEnd();
	UFUNCTION(BlueprintImplementableEvent, Category = "Eruption") void OnSettled();

	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> Root;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Base;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> BaseCollision;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Dome;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UParticleSystemComponent> Dust;

private:
	ECDEruptionPhase Phase = ECDEruptionPhase::Idle;
	float PhaseTime = 0.f;
	float PhaseAlpha = 0.f;
	float HitStopLeft = 0.f;
	bool bRoared = false;
	TArray<TWeakObjectPtr<AActor>> ArmFamily;

	void EnterPhase(ECDEruptionPhase NewPhase);
	void ShakeAll(TSubclassOf<UCameraShakeBase> Shake, float Scale) const;
	void SetArmZ(float Z) const;
	void SetArmHidden(bool bHidden) const;
	static float RiseCurve(float Alpha, float Overshoot);
};
