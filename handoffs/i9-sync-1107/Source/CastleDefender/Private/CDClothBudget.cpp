#include "CDClothBudget.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

namespace CDClothBudget
{
	static int32 GBudget = 1;
	static int32 GMaxActive = 12;
	static float GRange = 1500.f;
	static float GInterval = 0.25f;
	static FAutoConsoleVariableRef CVarBudget(TEXT("cd.Cloth.Budget"), GBudget, TEXT("1 = only the nearest soldiers simulate cape cloth (default). 0 = all simulate."));
	static FAutoConsoleVariableRef CVarMax(TEXT("cd.Cloth.MaxActive"), GMaxActive, TEXT("Most soldiers whose cape cloth simulates at once."));
	static FAutoConsoleVariableRef CVarRange(TEXT("cd.Cloth.Range"), GRange, TEXT("Capes farther than this from the camera (cm) are paused."));
	static FAutoConsoleVariableRef CVarInterval(TEXT("cd.Cloth.Interval"), GInterval, TEXT("How often the cloth budget is re-evaluated (s). Takes effect next play."));

	static bool IsSoldierClass(const UClass* C)
	{
		for (; C; C = C->GetSuperClass())
		{
			const FString N = C->GetName();
			if (N.StartsWith(TEXT("BP_Soldier")) || N.StartsWith(TEXT("BP_Medic"))) { return true; }
		}
		return false;
	}
}

bool UCDClothBudgetSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* W = Cast<UWorld>(Outer);
	return W && W->IsGameWorld() && Super::ShouldCreateSubsystem(Outer);
}

void UCDClothBudgetSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	InWorld.GetTimerManager().SetTimer(Timer, FTimerDelegate::CreateWeakLambda(this, [this]() { Step(); }),
		FMath::Max(0.05f, CDClothBudget::GInterval), true, 0.5f);
}

void UCDClothBudgetSubsystem::Deinitialize()
{
	if (UWorld* W = GetWorld()) { W->GetTimerManager().ClearTimer(Timer); }
	ResumeAll();   // rev 3 (review P2-3): never leave a cape suspended by this subsystem behind
	Super::Deinitialize();
}

void UCDClothBudgetSubsystem::ResumeAll()
{
	for (auto& KV : Suspended)
	{
		USkeletalMeshComponent* M = KV.Key.Get();
		if (M && KV.Value) { M->ResumeClothingSimulation(); }
	}
	Suspended.Reset();
}

void UCDClothBudgetSubsystem::Step()
{
	using namespace CDClothBudget;
	UWorld* W = GetWorld();
	if (!W) { return; }

	// rescan soldiers once a second (they are recruited and die during play)
	RescanIn -= GInterval;
	if (RescanIn <= 0.f)
	{
		RescanIn = 1.f;
		Cloth.Reset();
		for (TActorIterator<ACharacter> It(W); It; ++It)
		{
			if (!IsSoldierClass(It->GetClass())) { continue; }
			TArray<USkeletalMeshComponent*> Meshes;
			It->GetComponents(Meshes);
			for (USkeletalMeshComponent* M : Meshes)
			{
				if (M && M->GetSkeletalMeshAsset() && M->GetSkeletalMeshAsset()->GetMeshClothingAssets().Num() > 0) { Cloth.Add(M); }
			}
		}
	}

	FVector View = FVector::ZeroVector;
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(W, 0))
	{
		FRotator R;
		PC->GetPlayerViewPoint(View, R);
	}

	// nearest first
	TArray<TPair<float, USkeletalMeshComponent*>> Sorted;
	for (const TWeakObjectPtr<USkeletalMeshComponent>& WM : Cloth)
	{
		if (USkeletalMeshComponent* M = WM.Get()) { Sorted.Emplace(FVector::DistSquared(M->GetComponentLocation(), View), M); }
	}
	Sorted.Sort([](const TPair<float, USkeletalMeshComponent*>& A, const TPair<float, USkeletalMeshComponent*>& B) { return A.Key < B.Key; });

	const float RangeSq = FMath::Square(GRange);
	for (int32 i = 0; i < Sorted.Num(); ++i)
	{
		USkeletalMeshComponent* M = Sorted[i].Value;
		const bool bWantSim = !GBudget || (i < GMaxActive && Sorted[i].Key < RangeSq);
		bool& bIsSuspended = Suspended.FindOrAdd(M);
		if (bWantSim && bIsSuspended) { M->ResumeClothingSimulation(); bIsSuspended = false; }
		else if (!bWantSim && !bIsSuspended) { M->SuspendClothingSimulation(); bIsSuspended = true; }
	}
	// rev 3 (review P2-3): a mesh that left the managed set while still suspended (class changed, rescan dropped it) is resumed
	TSet<USkeletalMeshComponent*> Managed;
	for (const TPair<float, USkeletalMeshComponent*>& E : Sorted) { Managed.Add(E.Value); }
	for (auto It = Suspended.CreateIterator(); It; ++It)
	{
		USkeletalMeshComponent* M = It.Key().Get();
		if (!M) { It.RemoveCurrent(); continue; }
		if (!Managed.Contains(M)) { if (It.Value()) { M->ResumeClothingSimulation(); } It.RemoveCurrent(); }
	}
}
