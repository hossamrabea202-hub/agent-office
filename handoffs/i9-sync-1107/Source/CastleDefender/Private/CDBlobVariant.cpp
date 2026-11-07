#include "CDBlobVariant.h"
#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "HAL/IConsoleManager.h"
#include "TimerManager.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

static TAutoConsoleVariable<float> CVarBigMouthChance(TEXT("cd.Blob.BigMouthChance"), 0.25f, TEXT("Share of slime blobs that hatch a big mouth instead of a zombie. 0 = off."));
static TAutoConsoleVariable<int32> CVarBigMouthMax(TEXT("cd.Blob.BigMouthMax"), 2, TEXT("Blobs hatch no big mouth while this many are alive."));

namespace
{
	const FName TagBigMouth(TEXT("BigMouthBlob"));
	const FName ParamGreen(TEXT("Green"));

	UClass* BruteClass()
	{
		static TSoftClassPtr<AActor> Soft(FSoftObjectPath(TEXT("/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute.BP_FleshBrute_C")));
		return Soft.LoadSynchronous();
	}
}

// Test only: blobs in front of the hero, so the variation can be seen without waiting for a wave.
static FAutoConsoleCommandWithWorldAndArgs GCDSpawnBlobs(TEXT("cd.Test.SpawnBlobs"), TEXT("cd.Test.SpawnBlobs N: drops N slime blobs in front of the hero."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* W)
	{
		APawn* Hero = W ? UGameplayStatics::GetPlayerPawn(W, 0) : nullptr;
		UClass* Cls = LoadClass<AActor>(nullptr, TEXT("/Game/CastleDefender/Gameplay/Tentacle/Jelly/BP_JellyBlob.BP_JellyBlob_C"));
		if (!Hero || !Cls) { return; }
		const int32 N = Args.Num() > 0 ? FCString::Atoi(*Args[0]) : 3;
		FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
		for (int32 i = 0; i < N; ++i)
		{
			const FVector At = Hero->GetActorLocation() + Hero->GetActorForwardVector() * (500.0 + 250.0 * i) + Hero->GetActorRightVector() * (i % 2 == 0 ? 200.0 : -200.0) + FVector(0.0, 0.0, 150.0);
			W->SpawnActor<AActor>(Cls, FTransform(At), SP);
		}
	}));

void UCDBlobVariantSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	SpawnHandle = InWorld.AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UCDBlobVariantSubsystem::OnSpawned));
}

void UCDBlobVariantSubsystem::Deinitialize()
{
	if (UWorld* W = GetWorld()) { W->RemoveOnActorSpawnedHandler(SpawnHandle); }
	Super::Deinitialize();
}

void UCDBlobVariantSubsystem::OnSpawned(AActor* A)
{
	if (!A || CVarBigMouthChance.GetValueOnGameThread() <= 0.f) { return; }
	const FString Name = A->GetClass()->GetName();
	const bool bBlob = Name.StartsWith(TEXT("BP_JellyBlob"));
	const bool bShield = Name.StartsWith(TEXT("BP_ZombieJellyShield"));
	if (!bBlob && !bShield) { return; }
	// Next tick: the BeginPlay of the blob has made its material, and the hatch graph has attached the shield to its zombie.
	TWeakObjectPtr<AActor> Weak(A);
	TWeakObjectPtr<UCDBlobVariantSubsystem> Self(this);
	GetWorld()->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateLambda([Self, Weak, bBlob]()
	{
		if (!Self.IsValid() || !Weak.IsValid()) { return; }
		if (bBlob) { Self->MakeVariant(Weak.Get()); } else { Self->Hatch(Weak.Get()); }
	}));
}

void UCDBlobVariantSubsystem::MakeVariant(AActor* Blob)
{
	if (FMath::FRand() >= CVarBigMouthChance.GetValueOnGameThread()) { return; }
	Blob->Tags.AddUnique(TagBigMouth);
	TInlineComponentArray<UMeshComponent*> Meshes(Blob);
	for (UMeshComponent* M : Meshes)
	{
		if (M) { M->SetVectorParameterValueOnMaterials(ParamGreen, FVector(0.42f, 0.025f, 0.05f)); }
	}
	// The blob grows from BlobScale0 in its own tick, so a larger start makes the whole variant larger.
	if (FStructProperty* P = FindFProperty<FStructProperty>(Blob->GetClass(), TEXT("BlobScale0")))
	{
		if (FVector* V = P->ContainerPtrToValuePtr<FVector>(Blob)) { *V *= 1.35; }
	}
}

void UCDBlobVariantSubsystem::Hatch(AActor* Shield)
{
	UWorld* W = GetWorld();
	AActor* Zombie = Shield->GetAttachParentActor();
	if (!W || !Zombie) { return; }
	const FVector At = Zombie->GetActorLocation();
	bool bVariant = false;
	for (TActorIterator<AActor> It(W); It; ++It)
	{
		if (It->ActorHasTag(TagBigMouth) && FVector::DistSquared(It->GetActorLocation(), At) < FMath::Square(450.0))
		{
			bVariant = true;
			It->Tags.Remove(TagBigMouth); // one blob, one hatch
			break;
		}
	}
	UClass* Brute = bVariant ? BruteClass() : nullptr;
	if (!Brute) { return; }
	int32 Alive = 0;
	for (TActorIterator<AActor> It(W, Brute); It; ++It) { ++Alive; }
	if (Alive >= CVarBigMouthMax.GetValueOnGameThread()) { return; }
	FActorSpawnParameters SP;
	SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	if (W->SpawnActor<AActor>(Brute, FTransform(FRotator(0.0, Zombie->GetActorRotation().Yaw, 0.0), At + FVector(0.0, 0.0, 60.0)), SP))
	{
		Shield->Destroy();
		Zombie->Destroy();
	}
}
