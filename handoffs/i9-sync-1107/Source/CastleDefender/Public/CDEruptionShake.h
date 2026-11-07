// Castle Defender, 2026-11-06. Camera shakes for the tentacle ground eruption (card #545, SPEC_1106.md).
// Self-contained pattern (no EngineCameras dependency): decaying noise on location + rotation.
#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraShakeBase.h"
#include "CDEruptionShake.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDEruptionShakePattern : public UCameraShakePattern
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float Duration = 1.2f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float BlendIn = 0.05f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float BlendOut = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float LocationAmplitude = 6.f;     // cm
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float LocationFrequency = 18.f;   // Hz
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float RotationAmplitude = 1.2f;    // degrees
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float RotationFrequency = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Shake") float FovAmplitude = 0.f;

protected:
	virtual void GetShakePatternInfoImpl(FCameraShakeInfo& OutInfo) const override;
	virtual void StartShakePatternImpl(const FCameraShakePatternStartParams& Params) override;
	virtual void UpdateShakePatternImpl(const FCameraShakePatternUpdateParams& Params, FCameraShakePatternUpdateResult& OutResult) override;
	virtual bool IsFinishedImpl() const override { return Elapsed >= Duration; }

private:
	float Elapsed = 0.f;
	float Seed[6] = { 0, 0, 0, 0, 0, 0 };
	static float Noise(float T, float Freq, float Phase);
};

// Light rumble under the feet: the TELL (-4 s to -1.5 s). Long, low amplitude.
UCLASS(Blueprintable)
class CASTLEDEFENDER_API UCDEruptionShake_Tell : public UCameraShakeBase
{
	GENERATED_BODY()
public:
	UCDEruptionShake_Tell(const FObjectInitializer& OI);
};

// The BREACH hit: short, hard, mostly vertical.
UCLASS(Blueprintable)
class CASTLEDEFENDER_API UCDEruptionShake_Breach : public UCameraShakeBase
{
	GENERATED_BODY()
public:
	UCDEruptionShake_Breach(const FObjectInitializer& OI);
};
