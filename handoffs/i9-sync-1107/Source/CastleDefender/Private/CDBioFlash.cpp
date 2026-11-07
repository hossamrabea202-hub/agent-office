#include "CDBioFlash.h"
#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
	TAutoConsoleVariable<int32> CVarBioFlash(TEXT("cd.Blob.BioFlash"), 1, TEXT("1 = jelly mines and blobs flash with a sliding bio shine when touched or hit, until they hatch. 0 = off."));
	TAutoConsoleVariable<float> CVarBioBoost(TEXT("cd.Blob.BioBoost"), 5.f, TEXT("Brightness of the bio reaction overlay."));
	const float GBioSeconds = 3.3f;   // the blob hatches 3 s after TrigT, the shader's last pulse fades just after

	bool IsBlobClass(const UClass* C)
	{
		for (; C; C = C->GetSuperClass())
		{
			if (C->GetName().StartsWith(TEXT("BP_JellyBlob"))) { return true; }
		}
		return false;
	}

	bool ReadTrigT(const AActor* A, double& Out)
	{
		const FProperty* P = A->GetClass()->FindPropertyByName(TEXT("TrigT"));
		if (const FDoubleProperty* D = CastField<FDoubleProperty>(P)) { Out = D->GetPropertyValue_InContainer(A); return true; }
		if (const FFloatProperty* F = CastField<FFloatProperty>(P)) { Out = F->GetPropertyValue_InContainer(A); return true; }
		return false;
	}
}

void UCDBioFlash::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	Overlay = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/CastleDefender/VFX/BioFlash/M_CD_BioFlash.M_CD_BioFlash"));
	if (!Overlay) { UE_LOG(LogTemp, Warning, TEXT("[CD] bio flash: M_CD_BioFlash not found, off")); return; }
	for (TActorIterator<AActor> It(&InWorld); It; ++It) { Track(*It); }
	SpawnHandle = InWorld.AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateWeakLambda(this, [this](AActor* A) { Track(A); }));
}

void UCDBioFlash::Deinitialize()
{
	if (UWorld* W = GetWorld()) { W->RemoveOnActorSpawnedHandler(SpawnHandle); }
	Blobs.Reset();
	Mids.Reset();
	Live.Reset();
	Super::Deinitialize();
}

void UCDBioFlash::Track(AActor* A)
{
	if (A && IsBlobClass(A->GetClass()))
	{
		FBlob B;
		B.Actor = A;
		Blobs.Add(MoveTemp(B));
	}
}

void UCDBioFlash::Start(FBlob& B)
{
	AActor* A = B.Actor.Get();
	if (!A || !Overlay) { return; }
	UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(Overlay, this);
	Mid->SetScalarParameterValue(TEXT("Boost"), CVarBioBoost.GetValueOnGameThread());
	Live.Add(Mid);
	Mids.Add(B.Actor, Mid);
	TInlineComponentArray<UMeshComponent*> Comps(A);
	for (UMeshComponent* M : Comps)
	{
		if (M && M->IsVisible() && !M->bHiddenInGame)
		{
			M->SetOverlayMaterial(Mid);
			B.Meshes.Add(M);
		}
	}
	B.bActive = true;
}

void UCDBioFlash::Finish(FBlob& B)
{
	for (const TWeakObjectPtr<UMeshComponent>& M : B.Meshes)
	{
		if (M.IsValid()) { M->SetOverlayMaterial(nullptr); }
	}
	if (const TWeakObjectPtr<UMaterialInstanceDynamic>* Found = Mids.Find(B.Actor))
	{
		if (Found->IsValid()) { Live.Remove(Found->Get()); }
		Mids.Remove(B.Actor);
	}
	B.Meshes.Reset();
	B.bActive = false;
}

void UCDBioFlash::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	const UWorld* W = GetWorld();
	if (!W || !CVarBioFlash.GetValueOnGameThread()) { return; }
	const double Now = W->GetTimeSeconds();
	for (int32 k = Blobs.Num() - 1; k >= 0; --k)
	{
		FBlob& B = Blobs[k];
		const AActor* A = B.Actor.Get();
		double TrigT = -1.0;
		if (!A || !ReadTrigT(A, TrigT))
		{
			if (B.bActive) { Finish(B); }
			Blobs.RemoveAtSwap(k);
			continue;
		}
		if (TrigT < 0.0) { continue; }
		const float Age = float(Now - TrigT);
		if (Age >= GBioSeconds)
		{
			Finish(B);
			Blobs.RemoveAtSwap(k);   // one reaction per blob: TrigT is set once
			continue;
		}
		if (!B.bActive) { Start(B); }
		if (const TWeakObjectPtr<UMaterialInstanceDynamic>* Mid = Mids.Find(B.Actor))
		{
			if (Mid->IsValid()) { (*Mid)->SetScalarParameterValue(TEXT("Age"), FMath::Max(Age, 0.001f)); }
		}
	}
}

TStatId UCDBioFlash::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UCDBioFlash, STATGROUP_Tickables);
}
