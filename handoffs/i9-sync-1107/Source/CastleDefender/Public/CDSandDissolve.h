// CDSandDissolve (11-06, owner: "dissolve into particles and the particles flow away like sand in wind, swirly, when the big mouth dies").
//
// The Flesh Brute already dissolves through its material (M_FleshBrute DISSOLVE_MASK: noise erosion from 0.1 s to 1.7 s after
// DeathTime, hot edge) and spawns a smoke burst. This adds the sand: while the body erodes, grains lift off the body and stream
// away on the wind with a swirl, fading out. Pure C++ + one instanced-mesh component, no Niagara:
//   - grains are instances of a tiny cube on one UInstancedStaticMeshComponent (material M_CD_SandGrain: unlit, translucent,
//     per-instance custom data 0 = alpha, 1 = heat)
//   - emission: over [Delay, Delay + Duration] after the call, GrainCount grains, spawned around the body's bones (bone-based
//     surface sampling: no CPU skin access needed), rate shaped like the erosion (slow start, peak in the middle)
//   - motion per grain: drag towards the wind velocity, a swirl field (two analytic curl-like terms + a vortex around the body
//     axis), lift, gravity; alpha: fast in, long fade; the component's actor destroys itself when every grain is gone
//   - wind: MPC_Weather "WindDir"/"WindYaw"/"Wind" if present, else cd.Sand.WindYaw; strength cd.Sand.WindSpeed
// Cost: only while a brute dies: ~1800 instances x ~4 s, one transform batch update per tick. Switch: cd.Sand.Enable.
// Test without a brute: console cd.Sand.Test (a capsule-shaped burst at the player, or at the camera in the editor).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CDSandDissolve.generated.h"

class UInstancedStaticMeshComponent;
class USkinnedMeshComponent;

USTRUCT()
struct FCDSandGrain
{
	GENERATED_BODY()
	FVector Pos = FVector::ZeroVector;
	FVector Vel = FVector::ZeroVector;
	float Age = 0.f;
	float Life = 3.f;
	float Size = 2.f;      // cm
	float Phase = 0.f;     // per-grain swirl phase
	float Heat = 0.f;      // 1 at birth (glowing edge), cools to 0
	bool bAlive = false;
};

UCLASS(NotBlueprintable)
class CASTLEDEFENDER_API ACDSandDissolveActor : public AActor
{
	GENERATED_BODY()
public:
	ACDSandDissolveActor();
	virtual void Tick(float DeltaSeconds) override;

	// Body = the dying character (its skeletal mesh is sampled while it still exists); Delay/Duration = the erosion window.
	void Start(USkinnedMeshComponent* BodyMesh, const FVector& BodyCenter, float Delay, float Duration, int32 GrainCount);
	// Test burst around a capsule (no body).
	void StartCapsule(const FVector& Center, float HalfHeight, float Radius, float Delay, float Duration, int32 GrainCount);

private:
	UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Grains;
	TWeakObjectPtr<USkinnedMeshComponent> Body;
	TArray<FCDSandGrain> Sim;
	TArray<FVector> BonePos;        // last known bone positions (kept after the body is gone)
	TArray<float> BoneRadius;       // sampling radius per bone
	FVector Center = FVector::ZeroVector;
	float Elapsed = 0.f, Delay = 0.1f, Duration = 1.6f;
	int32 ToEmit = 0, Emitted = 0;
	float CapsuleHalf = 0.f, CapsuleR = 0.f;   // test mode when > 0
	FVector WindVel = FVector::ZeroVector;
	FRandomStream Rng;

	void RefreshBones();
	void EmitUpTo(int32 Target);
	FVector SamplePoint();
	FVector Swirl(const FVector& P, float T, float Phase) const;
	void PushToRender();
};

UCLASS()
class CASTLEDEFENDER_API UCDSandDissolveLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
public:
	// Call where the dissolve starts (BP_FleshBrute death chain, after DsSetCPD). Delay/Duration mirror the material's window.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|FX", meta = (DefaultToSelf = "Body"))
	static void StartSandDissolve(AActor* Body, float Delay = 0.1f, float Duration = 1.6f, int32 GrainCount = 0);

	// Wind velocity in cm/s (MPC_Weather if it has a wind parameter, else the cvars).
	static FVector GetWindVelocity(UWorld* World);
};
