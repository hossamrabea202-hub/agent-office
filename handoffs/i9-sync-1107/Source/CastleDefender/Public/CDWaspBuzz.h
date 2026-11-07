// CDWaspBuzz (2026-11-06): the wasp's wing sound, synthesised. The project has no insect recording, and a buzz that follows the
// real flight (pitch up in a dive, a nervous flutter while hovering, a sick stutter when the wasp is hurt) sells a creature better
// than a looped sample anyway. One USoundWaveProcedural per wasp, filled from the audio thread:
//   wingbeat = pulse train at BeatHz (a hornet's 100-200 Hz) with a sawtooth body and a soft low-pass, plus a second harmonic,
//   amplitude modulated by a slow flutter (the body bob), a random stutter when Damage > 0, and a shimmer tremolo.
// Parameters are atomics written by the game thread (SetBeat / SetIntensity / SetDamage).
#pragma once

#include "CoreMinimal.h"
#include "Sound/SoundWaveProcedural.h"
#include <atomic>
#include "CDWaspBuzz.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDWaspBuzz : public USoundWaveProcedural
{
	GENERATED_BODY()

public:
	UCDWaspBuzz(const FObjectInitializer& ObjectInitializer);

	// Beat frequency in Hz (pitch), overall loudness 0..1, hurt stutter 0..1. Thread-safe.
	void SetBeat(float Hz) { BeatHz.store(FMath::Clamp(Hz, 20.f, 800.f)); }
	void SetIntensity(float I) { Intensity.store(FMath::Clamp(I, 0.f, 1.f)); }
	void SetDamage(float D) { Damage.store(FMath::Clamp(D, 0.f, 1.f)); }

	// Fill the ring buffer: called by the audio thread through OnSoundWaveProceduralUnderflow.
	void Generate(int32 SamplesNeeded);
	void OnUnderflow(USoundWaveProcedural* Wave, int32 SamplesNeeded) { Generate(SamplesNeeded); }

private:
	std::atomic<float> BeatHz{ 170.f };
	std::atomic<float> Intensity{ 0.6f };
	std::atomic<float> Damage{ 0.f };
	double Phase = 0.0;          // wingbeat phase 0..1
	double FlutterPhase = 0.0;
	double ShimmerPhase = 0.0;
	float Lowpass = 0.f;
	float StutterGain = 1.f;
	int32 StutterLeft = 0;
	uint32 Rng = 0x9E3779B9u;
	float CurrentBeat = 170.f;
	float CurrentGain = 0.f;
	TArray<int16> Scratch;
};
