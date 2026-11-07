#include "CDTentacleEruption.h"
#include "CDEruptionShake.h"
#include "Components/StaticMeshComponent.h"
#include "Particles/ParticleSystemComponent.h"
#include "Particles/ParticleSystem.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"
#include "Components/DecalComponent.h"

static TAutoConsoleVariable<int32> CVarEruptionDebug(TEXT("cd.Eruption.Debug"), 0, TEXT("1 = log every eruption beat"));

ACDTentacleEruption::ACDTentacleEruption()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root")); SetRootComponent(Root);
	Base = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Base")); Base->SetupAttachment(Root);
	Base->SetCollisionEnabled(ECollisionEnabled::NoCollision); Base->SetVisibility(false); Base->SetCanEverAffectNavigation(false);
	BaseCollision = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BaseCollision")); BaseCollision->SetupAttachment(Root);
	BaseCollision->SetCollisionEnabled(ECollisionEnabled::NoCollision); BaseCollision->SetVisibility(false); BaseCollision->SetHiddenInGame(true); BaseCollision->SetCanEverAffectNavigation(false);
	Dome = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Dome")); Dome->SetupAttachment(Root);
	Dome->SetCollisionEnabled(ECollisionEnabled::NoCollision); Dome->SetVisibility(false); Dome->SetCastShadow(false);
	Dust = CreateDefaultSubobject<UParticleSystemComponent>(TEXT("Dust")); Dust->SetupAttachment(Root); Dust->bAutoActivate = false;

	// placeholders from the project: a sphere for the bulge, starter smoke for dust, the #542 synthesised cues, the spore base meshes
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded()) { Dome->SetStaticMesh(SphereMesh.Object); }
	static ConstructorHelpers::FObjectFinder<UParticleSystem> Smoke(TEXT("/Game/CastleDefender/AssetPacks/StarterContent/Particles/P_Smoke.P_Smoke"));
	if (Smoke.Succeeded()) { DustVentFX = Smoke.Object; DustColumnFX = Smoke.Object; }
	static ConstructorHelpers::FObjectFinder<USoundBase> Rumble(TEXT("/Game/CastleDefender/Environment/Tentacles/Rig/Style530/Sound/SW_TentacleRumble.SW_TentacleRumble"));
	if (Rumble.Succeeded()) { RumbleSound = Rumble.Object; }
	static ConstructorHelpers::FObjectFinder<USoundBase> Burst(TEXT("/Game/CastleDefender/Environment/Tentacles/Rig/Style530/Sound/SW_TentacleBurst.SW_TentacleBurst"));
	if (Burst.Succeeded()) { BreachSound = Burst.Object; }
	static ConstructorHelpers::FObjectFinder<USoundBase> Roar(TEXT("/Game/CastleDefender/Environment/Tentacles/Rig/Style530/Sound/SW_TentacleRoar.SW_TentacleRoar"));
	if (Roar.Succeeded()) { RoarSound = Roar.Object; }
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SporeA(TEXT("/Game/CastleDefender/Environment/Tentacles/SporeBase/SM_TentacleSporeBase_A.SM_TentacleSporeBase_A"));
	if (SporeA.Succeeded()) { BaseMesh = SporeA.Object; }
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SporeACol(TEXT("/Game/CastleDefender/Environment/Tentacles/SporeBase/SM_TentacleSporeBase_A_Col.SM_TentacleSporeBase_A_Col"));
	if (SporeACol.Succeeded()) { BaseCollisionMesh = SporeACol.Object; }
	TellShake = UCDEruptionShake_Tell::StaticClass();
	BreachShake = UCDEruptionShake_Breach::StaticClass();
}

void ACDTentacleEruption::BeginPlay()
{
	Super::BeginPlay();
	if (BaseMesh) { Base->SetStaticMesh(BaseMesh); }
	if (BaseCollisionMesh) { BaseCollision->SetStaticMesh(BaseCollisionMesh); }
	Base->SetWorldScale3D(FVector(BaseScale)); BaseCollision->SetWorldScale3D(FVector(BaseScale));
	Base->SetRelativeLocation(FVector(0, 0, -BaseSinkCm));
	Dome->SetRelativeScale3D(FVector(DomeRadiusCm / 50.f, DomeRadiusCm / 50.f, 0.01f)); Dome->SetRelativeLocation(FVector(0, 0, -5.f));
	if (ArmActor) { SetArmHidden(true); }
}

ACDTentacleEruption* ACDTentacleEruption::SpawnEruption(UObject* WorldContext, TSubclassOf<ACDTentacleEruption> EruptionClass, FVector GroundLocation, float Yaw, AActor* Arm, float InArmStartZ, float InArmEndZ, bool bBeginNow)
{
	UWorld* W = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
	if (!W) { return nullptr; }
	FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ACDTentacleEruption* E = W->SpawnActor<ACDTentacleEruption>(EruptionClass ? *EruptionClass : ACDTentacleEruption::StaticClass(), GroundLocation, FRotator(0, Yaw, 0), SP);
	if (!E) { return nullptr; }
	E->ArmActor = Arm; E->ArmStartZ = InArmStartZ; E->ArmEndZ = InArmEndZ;
	if (Arm) { E->SetArmHidden(true); E->SetArmZ(InArmStartZ); }
	if (bBeginNow) { E->Begin(); }
	return E;
}

void ACDTentacleEruption::Begin()
{
	if (Phase != ECDEruptionPhase::Idle) { return; }
	ArmFamily.Reset();
	if (ArmActor)
	{
		ArmFamily.Add(ArmActor);
		if (bArmMoveAttached) { TArray<AActor*> Att; ArmActor->GetAttachedActors(Att, true, true); for (AActor* A : Att) { ArmFamily.Add(A); } }
		SetArmHidden(true); SetArmZ(ArmStartZ);
	}
	SetActorTickEnabled(true);
	EnterPhase(ECDEruptionPhase::Tell);
}

void ACDTentacleEruption::Abort()
{
	SetActorTickEnabled(false);
	if (Dust) { Dust->Deactivate(); }
	if (HitStopLeft > 0.f) { UGameplayStatics::SetGlobalTimeDilation(this, 1.f); HitStopLeft = 0.f; }
	Phase = ECDEruptionPhase::Done;
}

void ACDTentacleEruption::EnterPhase(ECDEruptionPhase NewPhase)
{
	Phase = NewPhase; PhaseTime = 0.f; PhaseAlpha = 0.f;
	const FVector L = GetActorLocation();
	if (CVarEruptionDebug.GetValueOnGameThread()) { UE_LOG(LogTemp, Display, TEXT("[CD] eruption %s -> phase %d at %s"), *GetName(), int32(NewPhase), *L.ToCompactString()); }
	switch (NewPhase)
	{
	case ECDEruptionPhase::Tell:
		if (RumbleSound) { UGameplayStatics::PlaySoundAtLocation(this, RumbleSound, L, 1.f, 0.85f); }
		ShakeAll(TellShake, 1.f);
		Dome->SetVisibility(true);
		OnTell();
		break;
	case ECDEruptionPhase::Heave:
		if (DustVentFX && Dust) { Dust->SetTemplate(DustVentFX); Dust->SetRelativeScale3D(FVector(2.5f)); Dust->Activate(true); }
		if (CrackDecal) { UGameplayStatics::SpawnDecalAtLocation(this, CrackDecal, FVector(60.f, CrackRadiusCm, CrackRadiusCm), L + FVector(0, 0, 20.f), FRotator(-90.f, GetActorRotation().Yaw, 0.f), 20.f); }
		ShakeAll(TellShake, 1.6f);
		OnHeave();
		break;
	case ECDEruptionPhase::Breach:
		Dome->SetVisibility(false);
		Base->SetVisibility(true);
		BaseCollision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		if (BreachSound) { UGameplayStatics::PlaySoundAtLocation(this, BreachSound, L); }
		if (DustColumnFX && Dust) { Dust->SetTemplate(DustColumnFX); Dust->SetRelativeScale3D(FVector(6.f)); Dust->Activate(true); }
		ShakeAll(BreachShake, 1.f);
		if (HitStopSeconds > 0.f) { UGameplayStatics::SetGlobalTimeDilation(this, 0.15f); HitStopLeft = HitStopSeconds; }
		SetArmHidden(false);
		OnBreach();
		EnterPhase(ECDEruptionPhase::Rise);
		return;
	case ECDEruptionPhase::Rise:
		bRoared = false;
		break;
	case ECDEruptionPhase::Settle:
		if (ArmActor) { SetArmZ(ArmEndZ); }
		OnRiseEnd();
		break;
	case ECDEruptionPhase::Done:
		SetActorTickEnabled(false);
		if (Dust) { Dust->Deactivate(); }
		OnSettled();
		break;
	default: break;
	}
}

float ACDTentacleEruption::RiseCurve(float A, float Overshoot)
{
	// fast out of the ground, overshoot past 1, damped settle back to 1 (spec: "shoots up fast, slows at the top, shudders")
	A = FMath::Clamp(A, 0.f, 1.f);
	const float Ease = 1.f - FMath::Pow(1.f - A, 3.f);
	const float Wobble = Overshoot * FMath::Sin(A * PI * 2.2f) * FMath::Exp(-A * 2.6f);
	return Ease + Wobble * (A > 0.25f ? 1.f : A / 0.25f);
}

void ACDTentacleEruption::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	// hit-stop runs on real time
	if (HitStopLeft > 0.f)
	{
		HitStopLeft -= DeltaSeconds / FMath::Max(0.01f, UGameplayStatics::GetGlobalTimeDilation(this));
		if (HitStopLeft <= 0.f) { UGameplayStatics::SetGlobalTimeDilation(this, 1.f); }
	}
	PhaseTime += DeltaSeconds;
	switch (Phase)
	{
	case ECDEruptionPhase::Tell:
		PhaseAlpha = TellSeconds > 0.f ? PhaseTime / TellSeconds : 1.f;
		Dome->SetRelativeScale3D(FVector(DomeRadiusCm / 50.f, DomeRadiusCm / 50.f, FMath::Max(0.01f, DomeHeightCm / 50.f * 0.35f * PhaseAlpha)));
		if (PhaseAlpha >= 1.f) { EnterPhase(ECDEruptionPhase::Heave); }
		break;
	case ECDEruptionPhase::Heave:
		PhaseAlpha = HeaveSeconds > 0.f ? PhaseTime / HeaveSeconds : 1.f;
		Dome->SetRelativeScale3D(FVector(DomeRadiusCm / 50.f, DomeRadiusCm / 50.f, FMath::Max(0.01f, DomeHeightCm / 50.f * (0.35f + 0.65f * PhaseAlpha))));
		if (PhaseAlpha >= 1.f) { EnterPhase(ECDEruptionPhase::Breach); }
		break;
	case ECDEruptionPhase::Rise:
	{
		PhaseAlpha = RiseSeconds > 0.f ? PhaseTime / RiseSeconds : 1.f;
		const float C = RiseCurve(PhaseAlpha, RiseOvershoot);
		if (ArmActor) { SetArmZ(FMath::Lerp(ArmStartZ, ArmEndZ, C)); }
		Base->SetRelativeLocation(FVector(0, 0, -BaseSinkCm * (1.f - FMath::Min(1.f, PhaseAlpha * 1.6f))));
		if (!bRoared && PhaseAlpha > 0.7f && RoarSound) { bRoared = true; UGameplayStatics::PlaySoundAtLocation(this, RoarSound, GetActorLocation() + FVector(0, 0, 600.f), 1.f, 0.92f); }
		if (PhaseAlpha >= 1.f) { EnterPhase(ECDEruptionPhase::Settle); }
		break;
	}
	case ECDEruptionPhase::Settle:
		PhaseAlpha = SettleSeconds > 0.f ? PhaseTime / SettleSeconds : 1.f;
		if (PhaseAlpha >= 1.f) { EnterPhase(ECDEruptionPhase::Done); }
		break;
	default: break;
	}
}

void ACDTentacleEruption::ShakeAll(TSubclassOf<UCameraShakeBase> Shake, float Scale) const
{
	if (!Shake) { return; }
	UGameplayStatics::PlayWorldCameraShake(this, Shake, GetActorLocation(), ShakeInnerRadius, ShakeOuterRadius, 1.f, false);
	(void)Scale;
}

void ACDTentacleEruption::SetArmZ(float Z) const
{
	if (!ArmActor) { return; }
	const float Delta = Z - ArmActor->GetActorLocation().Z;
	if (FMath::IsNearlyZero(Delta, 0.01f)) { return; }
	for (const TWeakObjectPtr<AActor>& A : ArmFamily)
	{
		if (A.IsValid()) { A->AddActorWorldOffset(FVector(0, 0, Delta), false, nullptr, ETeleportType::TeleportPhysics); }
	}
	if (ArmFamily.Num() == 0) { ArmActor->AddActorWorldOffset(FVector(0, 0, Delta), false, nullptr, ETeleportType::TeleportPhysics); }
}

void ACDTentacleEruption::SetArmHidden(bool bHide) const
{
	if (!ArmActor) { return; }
	TArray<AActor*> All; All.Add(ArmActor);
	if (bArmMoveAttached) { ArmActor->GetAttachedActors(All, false, true); }
	for (AActor* A : All)
	{
		if (!A) { continue; }
		A->SetActorHiddenInGame(bHide);
		A->SetActorEnableCollision(!bHide);
		A->SetActorTickEnabled(!bHide);   // strike / spit components on the vitals stay inert while buried (the #542 indoor arm)
	}
}
