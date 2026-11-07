// CDSandDissolve.cpp - see the header. 11-06, i9 Master.
#include "CDSandDissolve.h"
#include "CDStats.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkinnedMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "UObject/ConstructorHelpers.h"

DECLARE_CYCLE_STAT(TEXT("SandDissolve Tick"), STAT_CD_SandTick, STATGROUP_CastleDefender);

namespace CDSand
{
	static int32 GEnable = 1;
	static int32 GGrains = 2600;
	static float GWindYaw = 35.f;        // degrees, where the sand goes when MPC_Weather has no wind
	static float GWindSpeed = 260.f;     // cm/s
	static float GSwirl = 1.0f;          // swirl amount
	static float GLift = 55.f;           // cm/s^2 upward while hot
	static float GLife = 3.8f;           // mean grain life, s
	static float GSize = 5.0f;           // grain size, cm
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.Sand.Enable"), GEnable, TEXT("1 = the Flesh Brute's dissolve sheds sand grains that blow away (default)."));
	static FAutoConsoleVariableRef CVarGrains(TEXT("cd.Sand.Grains"), GGrains, TEXT("Grains per death (default 1800)."));
	static FAutoConsoleVariableRef CVarYaw(TEXT("cd.Sand.WindYaw"), GWindYaw, TEXT("Wind direction (deg) when MPC_Weather has no wind parameter."));
	static FAutoConsoleVariableRef CVarSpeed(TEXT("cd.Sand.WindSpeed"), GWindSpeed, TEXT("Wind speed the grains drift towards (cm/s)."));
	static FAutoConsoleVariableRef CVarSwirl(TEXT("cd.Sand.Swirl"), GSwirl, TEXT("Swirl strength (1 = as designed, 0 = straight wind)."));
	static FAutoConsoleVariableRef CVarLift(TEXT("cd.Sand.Lift"), GLift, TEXT("Upward lift while a grain is still hot (cm/s^2)."));
	static FAutoConsoleVariableRef CVarLife(TEXT("cd.Sand.Life"), GLife, TEXT("Mean grain life (s)."));
	static FAutoConsoleVariableRef CVarSize(TEXT("cd.Sand.Size"), GSize, TEXT("Grain size (cm)."));

	static const TCHAR* GrainMeshPath = TEXT("/Engine/BasicShapes/Cube.Cube");
	static const TCHAR* GrainMatPath = TEXT("/Game/CastleDefender/VFX/Sand/M_CD_SandGrain.M_CD_SandGrain");
	static const TCHAR* WeatherMPC = TEXT("/Game/CastleDefender/Environment/Weather/MPC_Weather.MPC_Weather");

	// erosion-shaped emission: slow start, peak in the middle, tail (integrated so Target(t) = total * S(t))
	static float EmissionShape(float U) { U = FMath::Clamp(U, 0.f, 1.f); return U * U * (3.f - 2.f * U); }

	static FAutoConsoleCommandWithWorldAndArgs CmdTest(TEXT("cd.Sand.Test"), TEXT("Sand dissolve test burst at the player (or the camera): cd.Sand.Test [grains]"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (!World) { return; }
			FVector At = FVector::ZeroVector;
			if (Args.Num() >= 4) { At = FVector(FCString::Atof(*Args[1]), FCString::Atof(*Args[2]), FCString::Atof(*Args[3])); }   // cd.Sand.Test <grains> <x> <y> <z>
			else if (APawn* P = UGameplayStatics::GetPlayerPawn(World, 0)) { At = P->GetActorLocation() + P->GetActorForwardVector() * 250.f; }
			else if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0)) { FRotator R; PC->GetPlayerViewPoint(At, R); At += R.Vector() * 400.f; }
			UE_LOG(LogTemp, Display, TEXT("cd.Sand.Test at %s"), *At.ToString());
			ACDSandDissolveActor* A = World->SpawnActor<ACDSandDissolveActor>(At, FRotator::ZeroRotator);
			if (A) { A->StartCapsule(At, 130.f, 55.f, 0.1f, 1.6f, Args.Num() > 0 ? FCString::Atoi(*Args[0]) : GGrains); }
		}));
}

ACDSandDissolveActor::ACDSandDissolveActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostPhysics;
	Grains = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Grains"));
	SetRootComponent(Grains);
	Grains->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Grains->SetCastShadow(false);
	Grains->SetReceivesDecals(false);
	Grains->NumCustomDataFloats = 2;
	Grains->SetMobility(EComponentMobility::Movable);
	Grains->SetAbsolute(true, true, true);
	Rng.Initialize(FMath::Rand());
}

void ACDSandDissolveActor::Start(USkinnedMeshComponent* BodyMesh, const FVector& BodyCenter, float InDelay, float InDuration, int32 GrainCount)
{
	Body = BodyMesh; Center = BodyCenter; Delay = FMath::Max(0.f, InDelay); Duration = FMath::Max(0.2f, InDuration);
	ToEmit = FMath::Clamp(GrainCount > 0 ? GrainCount : CDSand::GGrains, 50, 20000);
	WindVel = UCDSandDissolveLibrary::GetWindVelocity(GetWorld());
	if (UStaticMesh* M = LoadObject<UStaticMesh>(nullptr, CDSand::GrainMeshPath)) { Grains->SetStaticMesh(M); }
	if (UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr, CDSand::GrainMatPath)) { Grains->SetMaterial(0, Mat); }
	else { UE_LOG(LogTemp, Warning, TEXT("cd.Sand: material %s missing, grains use the cube's default material"), CDSand::GrainMatPath); }
	Sim.Reserve(ToEmit);
	RefreshBones();
	SetLifeSpan(Delay + Duration + CDSand::GLife * 2.5f + 2.f);   // safety net
}

void ACDSandDissolveActor::StartCapsule(const FVector& InCenter, float HalfHeight, float Radius, float InDelay, float InDuration, int32 GrainCount)
{
	CapsuleHalf = HalfHeight; CapsuleR = Radius;
	Start(nullptr, InCenter, InDelay, InDuration, GrainCount);
}

void ACDSandDissolveActor::RefreshBones()
{
	USkinnedMeshComponent* M = Body.Get();
	if (!M) { return; }
	const int32 N = M->GetNumBones();
	if (N <= 0) { return; }
	BonePos.SetNum(N); BoneRadius.SetNum(N);
	for (int32 i = 0; i < N; ++i)
	{
		BonePos[i] = M->GetBoneTransform(i).GetLocation();
		const int32 Parent = M->GetParentBone(M->GetBoneName(i)) != NAME_None ? M->GetBoneIndex(M->GetParentBone(M->GetBoneName(i))) : INDEX_NONE;
		const float Len = Parent >= 0 ? float(FVector::Dist(BonePos[i], M->GetBoneTransform(Parent).GetLocation())) : 20.f;
		BoneRadius[i] = FMath::Clamp(Len * 0.45f + 5.f, 6.f, 45.f);   // the flesh around a bone: about half its length
	}
	Center = M->Bounds.Origin;
}

FVector ACDSandDissolveActor::SamplePoint()
{
	if (CapsuleHalf > 0.f || BonePos.Num() == 0)
	{
		// capsule surface
		const float Z = Rng.FRandRange(-CapsuleHalf, CapsuleHalf);
		const float A = Rng.FRandRange(0.f, 2.f * PI);
		const float R = CapsuleR * Rng.FRandRange(0.85f, 1.05f);
		return Center + FVector(FMath::Cos(A) * R, FMath::Sin(A) * R, Z);
	}
	const int32 i = Rng.RandRange(0, BonePos.Num() - 1);
	const FVector Dir = Rng.VRand();
	return BonePos[i] + Dir * BoneRadius[i] * Rng.FRandRange(0.7f, 1.05f);
}

void ACDSandDissolveActor::EmitUpTo(int32 Target)
{
	while (Emitted < Target)
	{
		FCDSandGrain G;
		G.Pos = SamplePoint();
		const FVector Out = (G.Pos - Center).GetSafeNormal2D();
		G.Vel = Out * Rng.FRandRange(10.f, 45.f) + FVector(0, 0, Rng.FRandRange(5.f, 35.f)) + WindVel * 0.15f;
		G.Life = CDSand::GLife * Rng.FRandRange(0.55f, 1.45f);
		G.Size = CDSand::GSize * Rng.FRandRange(0.5f, 1.4f);
		G.Phase = Rng.FRandRange(0.f, 2.f * PI);
		G.Heat = 1.f;
		G.bAlive = true;
		Sim.Add(G);
		++Emitted;
	}
}

FVector ACDSandDissolveActor::Swirl(const FVector& P, float T, float Phase) const
{
	// two curl-like terms (different scales, drifting with time) + a vortex around the body's vertical axis
	const FVector L = (P - Center) * 0.012f;
	const float t = T * 1.3f + Phase;
	const FVector A(FMath::Sin(L.Y * 2.1f + t) * FMath::Cos(L.Z * 1.3f - t * 0.7f), FMath::Sin(L.Z * 1.7f + t * 0.9f) * FMath::Cos(L.X * 1.9f + t * 0.5f), FMath::Sin(L.X * 2.3f - t * 0.8f) * FMath::Cos(L.Y * 1.1f + t));
	const FVector B(FMath::Cos(L.Z * 4.7f + t * 2.2f), FMath::Sin(L.X * 5.1f - t * 1.9f), FMath::Cos(L.Y * 4.3f + t * 2.6f) * 0.5f);
	FVector Radial = (P - Center); Radial.Z = 0.f;
	const float R = FMath::Max(Radial.Size(), 20.f);
	const FVector Tangent = FVector(-Radial.Y, Radial.X, 0.f) / R;        // around the body axis
	const float Vortex = 90.f * FMath::Exp(-R / 180.f);                     // strongest near the body, fades with distance
	return A * 70.f + B * 30.f + Tangent * Vortex;
}

void ACDSandDissolveActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	SCOPE_CYCLE_COUNTER(STAT_CD_SandTick);
	const float Dt = FMath::Min(DeltaSeconds, 0.05f);
	Elapsed += Dt;
	if (Body.IsValid()) { RefreshBones(); }

	// emission over the erosion window
	const float U = (Elapsed - Delay) / Duration;
	if (U > 0.f && Emitted < ToEmit) { EmitUpTo(FMath::Min(ToEmit, FMath::CeilToInt(ToEmit * CDSand::EmissionShape(U)))); }
	if (Elapsed > Delay + Duration + 0.2f && Emitted < ToEmit) { EmitUpTo(ToEmit); }

	// motion
	const float T = GetWorld() ? GetWorld()->GetTimeSeconds() : Elapsed;
	int32 Alive = 0;
	for (FCDSandGrain& G : Sim)
	{
		if (!G.bAlive) { continue; }
		G.Age += Dt;
		if (G.Age >= G.Life) { G.bAlive = false; continue; }
		++Alive;
		const float LifeU = G.Age / G.Life;
		G.Heat = FMath::Max(0.f, 1.f - G.Age * 1.6f);
		const FVector Target = WindVel * (0.6f + 0.6f * LifeU) + Swirl(G.Pos, T, G.Phase) * CDSand::GSwirl;
		const float Drag = 1.6f;                                                        // 1/s: how fast the grain takes the air's speed
		G.Vel += (Target - G.Vel) * FMath::Min(1.f, Drag * Dt);
		G.Vel.Z += (CDSand::GLift * G.Heat - 90.f * (1.f - G.Heat) * (0.3f + 0.7f * LifeU)) * Dt;   // lift while hot, then sinks gently
		G.Pos += G.Vel * Dt;
	}
	PushToRender();
	if (Emitted >= ToEmit && Alive == 0) { Destroy(); }
}

void ACDSandDissolveActor::PushToRender()
{
	if (!Grains) { return; }
	const int32 Want = Sim.Num();
	while (Grains->GetInstanceCount() < Want) { Grains->AddInstance(FTransform::Identity, true); }
	TArray<FTransform> Xf; Xf.Reserve(Want);
	for (int32 i = 0; i < Want; ++i)
	{
		const FCDSandGrain& G = Sim[i];
		const float LifeU = G.Life > 0.f ? G.Age / G.Life : 1.f;
		const float Alpha = G.bAlive ? FMath::Clamp(FMath::Min(G.Age * 6.f, 1.f) * (1.f - FMath::Clamp((LifeU - 0.55f) / 0.45f, 0.f, 1.f)), 0.f, 1.f) : 0.f;
		const float S = G.bAlive ? G.Size * (0.6f + 0.4f * (1.f - LifeU)) * 0.01f : 0.f;   // cube is 100 cm
		const FQuat Rot = FQuat(FVector(0.3f, 0.5f, 0.8f).GetSafeNormal(), G.Phase + G.Age * 3.f);
		Xf.Add(FTransform(Rot, G.Pos, FVector(S)));
		Grains->SetCustomDataValue(i, 0, Alpha, false);
		Grains->SetCustomDataValue(i, 1, G.Heat, false);
	}
	Grains->BatchUpdateInstancesTransforms(0, Xf, true, false, false);
	Grains->MarkRenderStateDirty();
}

FVector UCDSandDissolveLibrary::GetWindVelocity(UWorld* World)
{
	FVector Dir = FRotator(0.f, CDSand::GWindYaw, 0.f).Vector();
	float Speed = CDSand::GWindSpeed;
	if (World)
	{
		if (UMaterialParameterCollection* MPC = LoadObject<UMaterialParameterCollection>(nullptr, CDSand::WeatherMPC))
		{
			if (UMaterialParameterCollectionInstance* Inst = World->GetParameterCollectionInstance(MPC))
			{
				FLinearColor V; float S;
				if (Inst->GetVectorParameterValue(TEXT("WindDir"), V) && FVector(V.R, V.G, 0.f).SizeSquared() > 0.01f) { Dir = FVector(V.R, V.G, 0.f).GetSafeNormal(); }
				else if (Inst->GetScalarParameterValue(TEXT("WindYaw"), S)) { Dir = FRotator(0.f, S, 0.f).Vector(); }
				if (Inst->GetScalarParameterValue(TEXT("WindStrength"), S) && S > 0.f) { Speed = CDSand::GWindSpeed * FMath::Clamp(S, 0.2f, 3.f); }
				else if (Inst->GetScalarParameterValue(TEXT("Wind"), S) && S > 0.f) { Speed = CDSand::GWindSpeed * FMath::Clamp(S, 0.2f, 3.f); }
			}
		}
	}
	return Dir * Speed + FVector(0, 0, 25.f);
}

void UCDSandDissolveLibrary::StartSandDissolve(AActor* Body, float Delay, float Duration, int32 GrainCount)
{
	if (!CDSand::GEnable || !IsValid(Body)) { return; }
	UWorld* World = Body->GetWorld();
	if (!World) { return; }
	USkinnedMeshComponent* Mesh = nullptr;
	if (const ACharacter* C = Cast<ACharacter>(Body)) { Mesh = C->GetMesh(); }
	if (!Mesh) { Mesh = Body->FindComponentByClass<USkinnedMeshComponent>(); }
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ACDSandDissolveActor* A = World->SpawnActor<ACDSandDissolveActor>(Body->GetActorLocation(), FRotator::ZeroRotator, P);
	if (!A) { return; }
	if (Mesh) { A->Start(Mesh, Mesh->Bounds.Origin, Delay, Duration, GrainCount); }
	else { A->StartCapsule(Body->GetActorLocation(), 120.f, 50.f, Delay, Duration, GrainCount); }
}
