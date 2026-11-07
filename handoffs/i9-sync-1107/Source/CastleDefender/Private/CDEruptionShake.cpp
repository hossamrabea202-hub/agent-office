#include "CDEruptionShake.h"

float UCDEruptionShakePattern::Noise(float T, float Freq, float Phase)
{
	// two incommensurate sines: cheap, smooth, never visibly periodic over a 1-4 s shake
	const float A = FMath::Sin(T * Freq * 2.f * PI + Phase);
	const float B = FMath::Sin(T * Freq * 1.37f * 2.f * PI + Phase * 2.1f + 0.7f);
	return 0.65f * A + 0.35f * B;
}

void UCDEruptionShakePattern::GetShakePatternInfoImpl(FCameraShakeInfo& OutInfo) const
{
	OutInfo.Duration = FCameraShakeDuration(Duration);
	OutInfo.BlendIn = BlendIn;
	OutInfo.BlendOut = BlendOut;
}

void UCDEruptionShakePattern::StartShakePatternImpl(const FCameraShakePatternStartParams& Params)
{
	Elapsed = 0.f;
	for (float& S : Seed) { S = FMath::FRandRange(0.f, 2.f * PI); }
}

void UCDEruptionShakePattern::UpdateShakePatternImpl(const FCameraShakePatternUpdateParams& Params, FCameraShakePatternUpdateResult& OutResult)
{
	Elapsed += Params.DeltaTime;
	const float T = Elapsed;
	// envelope: blend in, hold, blend out (the shake base also applies its own blend weight; this keeps the tail soft)
	float Env = 1.f;
	if (BlendIn > 0.f && T < BlendIn) { Env = T / BlendIn; }
	else if (BlendOut > 0.f && T > Duration - BlendOut) { Env = FMath::Max(0.f, (Duration - T) / BlendOut); }
	Env *= Params.GetTotalScale();  // play-time scale (distance falloff, caller scale)
	const float L = LocationAmplitude * Env, R = RotationAmplitude * Env;
	OutResult.Location = FVector(Noise(T, LocationFrequency, Seed[0]) * L * 0.6f, Noise(T, LocationFrequency, Seed[1]) * L * 0.6f, Noise(T, LocationFrequency, Seed[2]) * L);
	OutResult.Rotation = FRotator(Noise(T, RotationFrequency, Seed[3]) * R, Noise(T, RotationFrequency, Seed[4]) * R * 0.6f, Noise(T, RotationFrequency, Seed[5]) * R * 0.4f);
	OutResult.FOV = FovAmplitude * Env * Noise(T, LocationFrequency * 0.5f, Seed[0]);
}

UCDEruptionShake_Tell::UCDEruptionShake_Tell(const FObjectInitializer& OI) : Super(OI)
{
	UCDEruptionShakePattern* P = OI.CreateDefaultSubobject<UCDEruptionShakePattern>(this, TEXT("TellPattern"));
	P->Duration = 2.6f; P->BlendIn = 0.6f; P->BlendOut = 0.8f;
	P->LocationAmplitude = 2.5f; P->LocationFrequency = 9.f;
	P->RotationAmplitude = 0.35f; P->RotationFrequency = 7.f;
	SetRootShakePattern(P);
	bSingleInstance = true;
}

UCDEruptionShake_Breach::UCDEruptionShake_Breach(const FObjectInitializer& OI) : Super(OI)
{
	UCDEruptionShakePattern* P = OI.CreateDefaultSubobject<UCDEruptionShakePattern>(this, TEXT("BreachPattern"));
	P->Duration = 1.1f; P->BlendIn = 0.02f; P->BlendOut = 0.6f;
	P->LocationAmplitude = 14.f; P->LocationFrequency = 22.f;
	P->RotationAmplitude = 2.2f; P->RotationFrequency = 16.f;
	P->FovAmplitude = 1.5f;
	SetRootShakePattern(P);
	bSingleInstance = true;
}
