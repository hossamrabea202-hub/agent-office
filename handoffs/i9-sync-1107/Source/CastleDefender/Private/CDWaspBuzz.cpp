// CDWaspBuzz.cpp (2026-11-06): synthesised hornet wingbeat. Runs on the audio thread through the underflow callback.
#include "CDWaspBuzz.h"

UCDWaspBuzz::UCDWaspBuzz(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	SetSampleRate(22050);
	NumChannels = 1;
	Duration = INDEFINITELY_LOOPING_DURATION;
	bLooping = false;
	SoundGroup = SOUNDGROUP_Effects;
	NumSamplesToGeneratePerCallback = 1024;
	OnSoundWaveProceduralUnderflow.BindUObject(this, &UCDWaspBuzz::OnUnderflow);
}

void UCDWaspBuzz::Generate(int32 SamplesNeeded)
{
	const int32 N = FMath::Max(SamplesNeeded, 256);
	Scratch.SetNumUninitialized(N);
	const float SR = 22050.f;   // what the constructor set
	const float Beat = BeatHz.load();
	const float Want = Intensity.load();
	const float Dmg = Damage.load();

	for (int32 i = 0; i < N; ++i)
	{
		// glide pitch and loudness so parameter changes never click
		CurrentBeat += (Beat - CurrentBeat) * 0.0006f;
		CurrentGain += (Want - CurrentGain) * 0.0004f;

		Phase += double(CurrentBeat) / SR;
		if (Phase >= 1.0) { Phase -= 1.0; }
		const float Ph = float(Phase);
		// each wingbeat: a sharp pulse that decays through the cycle (the wing's snap) over a sawtooth body and a second harmonic
		const float Pulse = FMath::Exp(-Ph * 9.f);
		const float Saw = 2.f * Ph - 1.f;
		const float H2 = FMath::Sin(Ph * 2.f * PI * 2.f) * 0.35f;
		const float H3 = FMath::Sin(Ph * 2.f * PI * 3.f) * 0.12f;
		float S = Saw * 0.45f + Pulse * 0.6f + H2 + H3;
		// one-pole low-pass: takes the digital edge off
		Lowpass += (S - Lowpass) * 0.22f;
		S = Lowpass;

		// the body bob (6 Hz) and a fast shimmer (31 Hz) modulate the loudness
		FlutterPhase += 6.0 / SR; if (FlutterPhase >= 1.0) { FlutterPhase -= 1.0; }
		ShimmerPhase += 31.0 / SR; if (ShimmerPhase >= 1.0) { ShimmerPhase -= 1.0; }
		const float Flutter = 0.85f + 0.15f * FMath::Sin(2.f * PI * float(FlutterPhase));
		const float Shimmer = 0.92f + 0.08f * FMath::Sin(2.f * PI * float(ShimmerPhase));

		// hurt: random stutters, more of them the more it is hurt (a torn wing)
		if (StutterLeft > 0) { --StutterLeft; }
		else
		{
			Rng ^= Rng << 13; Rng ^= Rng >> 17; Rng ^= Rng << 5;
			const float R = float(Rng & 0xFFFF) / 65535.f;
			if (Dmg > 0.f && R < Dmg * 0.0025f) { StutterLeft = int32(SR * 0.045f); StutterGain = 0.12f; }
			else { StutterGain += (1.f - StutterGain) * 0.01f; }
		}

		const float Out = S * Flutter * Shimmer * StutterGain * CurrentGain * 0.55f;
		Scratch[i] = int16(FMath::Clamp(Out, -1.f, 1.f) * 32000.f);
	}
	QueueAudio(reinterpret_cast<const uint8*>(Scratch.GetData()), N * sizeof(int16));
}
