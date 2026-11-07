#include "CDEnvPerf.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Particles/ParticleSystem.h"
#include "Particles/ParticleSystemComponent.h"
#include "UObject/UObjectIterator.h"

static TAutoConsoleVariable<int32> CVarEnv(TEXT("cd.Perf.Env"), 1, TEXT("Hide and stop fire effects outside the view, slower ticks on idle jelly mines and blobs. 0 = off, everything back as authored."));
static TAutoConsoleVariable<float> CVarFireFar(TEXT("cd.Perf.FireFar"), 9000.f, TEXT("Fire effects farther than this from the camera (cm) are stopped even inside the view."));

namespace
{
	bool IsManagedFire(const UParticleSystemComponent* C)
	{
		const UParticleSystem* T = C ? C->Template.Get() : nullptr;
		if (!T) { return false; }
		const FString N = T->GetName();
		return N == TEXT("P_TorchFire") || N == TEXT("P_AshenGate_Fire");
	}
}

void UCDEnvPerfSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	SpawnHandle = InWorld.AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UCDEnvPerfSubsystem::OnSpawned));
	for (TActorIterator<AActor> It(&InWorld); It; ++It) { SlowTick(*It); }
}

void UCDEnvPerfSubsystem::Deinitialize()
{
	if (UWorld* W = GetWorld()) { W->RemoveOnActorSpawnedHandler(SpawnHandle); }
	Super::Deinitialize();
}

void UCDEnvPerfSubsystem::OnSpawned(AActor* A)
{
	SlowTick(A);
}

void UCDEnvPerfSubsystem::SlowTick(AActor* A)
{
	if (!A || CVarEnv.GetValueOnGameThread() == 0) { return; }
	const FString Name = A->GetClass()->GetName();
	if (Name.StartsWith(TEXT("BP_JellyMine"))) { A->SetActorTickInterval(0.2f); }
	else if (Name.StartsWith(TEXT("BP_JellyBlob"))) { A->SetActorTickInterval(0.1f); }
}

void UCDEnvPerfSubsystem::RefreshList()
{
	UWorld* W = GetWorld();
	Fires.Reset();
	for (TObjectIterator<UParticleSystemComponent> It; It; ++It)
	{
		if (It->GetWorld() == W && !It->IsTemplate() && IsManagedFire(*It)) { Fires.Add(*It); }
	}
}

void UCDEnvPerfSubsystem::SetFire(UParticleSystemComponent* C, bool bOn)
{
	if (bOn)
	{
		if (Off.Remove(C) > 0)
		{
			C->SetVisibility(true);
			C->SetComponentTickEnabled(true);
			C->Activate(true);
		}
	}
	else if (!Off.Contains(C))
	{
		Off.Add(C);
		C->DeactivateImmediate();
		C->SetComponentTickEnabled(false);
		C->SetVisibility(false);
	}
}

void UCDEnvPerfSubsystem::Tick(float DeltaTime)
{
	UWorld* W = GetWorld();
	if (!W) { return; }
	const double Now = W->GetRealTimeSeconds();
	if (Now < NextUpdate) { return; }
	NextUpdate = Now + 0.25;
	if (Now >= NextList) { NextList = Now + 5.0; RefreshList(); }

	const APlayerController* PC = W->GetFirstPlayerController();
	const APlayerCameraManager* Cam = PC ? PC->PlayerCameraManager.Get() : nullptr;
	const bool bEnabled = CVarEnv.GetValueOnGameThread() != 0 && Cam;
	const FVector Eye = Cam ? Cam->GetCameraLocation() : FVector::ZeroVector;
	const FVector Fwd = Cam ? Cam->GetCameraRotation().Vector() : FVector::ForwardVector;
	const double Far = CVarFireFar.GetValueOnGameThread();
	for (const TWeakObjectPtr<UParticleSystemComponent>& Weak : Fires)
	{
		UParticleSystemComponent* C = Weak.Get();
		if (!C) { continue; }
		bool bWant = true;
		if (bEnabled)
		{
			const FVector To = C->GetComponentLocation() - Eye;
			const double Dist = To.Size();
			// A wide cone plus a near ring, so a turning camera sees fire that is already burning.
			bWant = Dist < 2000.0 || (Dist < Far && FVector::DotProduct(To / FMath::Max(Dist, 1.0), Fwd) > 0.25);
		}
		SetFire(C, bWant);
	}
}
