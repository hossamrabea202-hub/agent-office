// CDWaspSpit.cpp - the wasps' second attack. See the header.
#include "CDWaspSpit.h"
#include "RealmWaspBase.h"
#include "CDSettings.h"
#include "ZombieBase.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/DecalComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/DamageType.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Sound/SoundBase.h"

namespace CDSpit
{
	static int32 GEnable = 1;
	static FAutoConsoleVariableRef CVar(TEXT("cd.Wasp.Spit"), GEnable, TEXT("1 = wasps spit slime globs as a second attack (default). 0 = off."));
	static int32 GScreenGoo = 1;
	static FAutoConsoleVariableRef CVarGoo(TEXT("cd.Wasp.ScreenGoo"), GScreenGoo, TEXT("1 = the hero's screen gets the slime post-process when spat on (default). 0 = off."));
	static const FName NAME_Color(TEXT("Color")), NAME_Fade(TEXT("Fade")), NAME_Wasp(TEXT("Wasp"));
	static TWeakObjectPtr<USoundBase> GSplatSound; static bool bSoundTried = false;

	static const FCDWaspCasteSettings& Stats(EWaspCaste C)
	{
		const UCDSettings* S = GetDefault<UCDSettings>();
		return C == EWaspCaste::Matriarch ? S->WaspMatriarch : S->WaspDrone;
	}
	static bool IsWaspSide(const AActor* A)
	{
		return A && (A->IsA<ARealmWaspBase>() || A->IsA<ACDWaspSpit>() || A->ActorHasTag(NAME_Wasp) || A->IsA<AZombieBase>());
	}
}

// ---------------------------------------------------------------- the glob

ACDWaspSpit::ACDWaspSpit()
{
	PrimaryActorTick.bCanEverTick = true;
	Sphere = CreateDefaultSubobject<USphereComponent>(TEXT("Sphere"));
	Sphere->InitSphereRadius(18.f);
	Sphere->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Sphere->SetCollisionObjectType(ECC_WorldDynamic);
	Sphere->SetCollisionResponseToAllChannels(ECR_Overlap);
	Sphere->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
	Sphere->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	Sphere->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	Sphere->SetGenerateOverlapEvents(true);
	RootComponent = Sphere;

	Glob = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Glob"));
	Glob->SetupAttachment(Sphere);
	Glob->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Glob->SetCastShadow(false);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Sphere);
	Light->SetIntensity(1200.f);
	Light->SetAttenuationRadius(260.f);
	Light->SetCastShadows(false);
	Light->bUseInverseSquaredFalloff = false;

	Move = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Move"));
	Move->bRotationFollowsVelocity = true;
	Move->ProjectileGravityScale = 0.55f;
	Move->bShouldBounce = false;
	Move->InitialSpeed = 0.f;
	Move->MaxSpeed = 6000.f;
	InitialLifeSpan = 5.f;
}

void ACDWaspSpit::Launch(AActor* Spitter, EWaspCaste InCaste, const FVector& Velocity)
{
	Owner_ = Spitter;
	Caste = InCaste;
	const FCDWaspCasteSettings& C = CDSpit::Stats(Caste);
	const UCDSettings* S = GetDefault<UCDSettings>();
	Sphere->SetSphereRadius(C.SpitRadius);
	if (UStaticMesh* M = S->WaspSpitMesh.LoadSynchronous())
	{
		Glob->SetStaticMesh(M);
		const float MeshR = FMath::Max(M->GetBounds().SphereRadius, 1.f);
		Glob->SetRelativeScale3D(FVector(C.SpitRadius * 1.15f / MeshR));
	}
	if (UMaterialInterface* Mat = C.SpitMaterial.LoadSynchronous())
	{
		GlobMat = UMaterialInstanceDynamic::Create(Mat, this);
		GlobMat->SetVectorParameterValue(CDSpit::NAME_Color, C.NeonColor);
		Glob->SetMaterial(0, GlobMat);
	}
	Light->SetLightColor(C.NeonColor);
	Light->SetIntensity(Caste == EWaspCaste::Matriarch ? 3000.f : 1200.f);
	if (Spitter) { Sphere->IgnoreActorWhenMoving(Spitter, true); }
	Move->Velocity = Velocity;
	Move->Activate(true);
	Sphere->OnComponentBeginOverlap.AddDynamic(this, &ACDWaspSpit::OnOverlap);
	Sphere->OnComponentHit.AddDynamic(this, &ACDWaspSpit::OnHit);
}

void ACDWaspSpit::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Age += DeltaSeconds;
	// a wobbling, stretching glob: squash along the flight, pulse
	if (Glob)
	{
		const float P = 1.f + 0.12f * FMath::Sin(Age * 23.f);
		FVector Sc = Glob->GetRelativeScale3D();
		const float Base = Sc.GetMax() / FMath::Max(1.f + 0.12f, 0.01f);
		Glob->SetRelativeScale3D(FVector(Base * (1.f + 0.25f) * P, Base * P, Base / P));
	}
}

void ACDWaspSpit::OnOverlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32, bool, const FHitResult& Sweep)
{
	if (bDone || !Other || Other == this || Other == Owner_.Get() || CDSpit::IsWaspSide(Other)) { return; }
	const FVector Where = (Sweep.bBlockingHit || !Sweep.ImpactPoint.IsZero()) ? FVector(Sweep.ImpactPoint) : GetActorLocation();
	Splat(Other, Where, -Move->Velocity.GetSafeNormal());
}

void ACDWaspSpit::OnHit(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, FVector, const FHitResult& Hit)
{
	if (bDone) { return; }
	if (Other && CDSpit::IsWaspSide(Other)) { return; }
	Splat(Other, Hit.ImpactPoint, Hit.ImpactNormal);
}

void ACDWaspSpit::Splat(AActor* Victim, const FVector& Where, const FVector& Normal)
{
	bDone = true;
	const FCDWaspCasteSettings& C = CDSpit::Stats(Caste);
	UWorld* World = GetWorld();
	if (Victim && Victim->CanBeDamaged())
	{
		AActor* Spitter = Owner_.Get();
		APawn* SpitterPawn = Cast<APawn>(Spitter);
		UGameplayStatics::ApplyDamage(Victim, C.SpitDamage, SpitterPawn ? SpitterPawn->GetController() : nullptr, Spitter ? Spitter : this, UDamageType::StaticClass());
		UCDWaspSlimeComponent::Apply(Victim, Caste, Where, Normal);
	}
	// a splat on the world under the hit (decal on the ground / wall), fades with its own life
	if (World && !Cast<ACharacter>(Victim)) // 11-06 night: a splat on a character projected over the whole body as one flat neon sheet
	{
		if (UMaterialInterface* DM = C.SlimeDecalMaterial.LoadSynchronous())
		{
			const float Size = C.SpitRadius * 3.5f;
			if (UDecalComponent* D = UGameplayStatics::SpawnDecalAtLocation(World, DM, FVector(Size * 0.6f, Size, Size), Where, (-Normal).Rotation(), 14.f))
			{
				D->SetFadeOut(9.f, 5.f, false);
				if (UMaterialInstanceDynamic* Dyn = D->CreateDynamicMaterialInstance()) { Dyn->SetVectorParameterValue(CDSpit::NAME_Color, C.NeonColor * 0.55f); Dyn->SetScalarParameterValue(CDSpit::NAME_Fade, 1.f); }
			}
		}
		if (!CDSpit::bSoundTried)
		{
			CDSpit::bSoundTried = true;
			CDSpit::GSplatSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/Audio/SFX_FleshHit.SFX_FleshHit"));
		}
		if (USoundBase* Snd = CDSpit::GSplatSound.Get()) { UGameplayStatics::PlaySoundAtLocation(this, Snd, Where, 0.7f, 0.55f); }
	}
	Move->StopMovementImmediately();
	Sphere->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Glob->SetVisibility(false);
	Light->SetIntensity(0.f);
	SetLifeSpan(0.2f);
}

// ---------------------------------------------------------------- the coated victim

UCDWaspSlimeComponent::UCDWaspSlimeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;   // after the victim's own Tick wrote its speed
}

UCDWaspSlimeComponent* UCDWaspSlimeComponent::Apply(AActor* Victim, EWaspCaste Caste, const FVector& HitPoint, const FVector& FromDir)
{
	if (!IsValid(Victim)) { return nullptr; }
	UCDWaspSlimeComponent* Comp = Victim->FindComponentByClass<UCDWaspSlimeComponent>();
	if (!Comp)
	{
		Comp = NewObject<UCDWaspSlimeComponent>(Victim, TEXT("WaspSlime"));
		Comp->RegisterComponent();
		Comp->AddTickPrerequisiteActor(Victim);
		if (const ACharacter* Hero = UGameplayStatics::GetPlayerCharacter(Victim, 0)) { Comp->bIsHero = (Hero == Victim); }
	}
	Comp->Refresh(Caste, HitPoint, FromDir);
	return Comp;
}

void UCDWaspSlimeComponent::Refresh(EWaspCaste Caste, const FVector& HitPoint, const FVector& FromDir)
{
	const FCDWaspCasteSettings& C = CDSpit::Stats(Caste);
	const UCDSettings* S = GetDefault<UCDSettings>();
	AActor* Victim = GetOwner();
	Remaining = FMath::Max(Remaining, C.SlimeSeconds);
	Total = FMath::Max(Total, C.SlimeSeconds);
	Slow = FMath::Min(Slow, C.SlimeSlow);
	bEnded = false;

	// a dripping splat stuck to the body (at most 3)
	if (Decals.Num() < 3)
	{
		if (UMaterialInterface* DM = C.SlimeDecalMaterial.LoadSynchronous())
		{
			USceneComponent* Attach = Victim->GetRootComponent();
			float R = 60.f;
			if (const ACharacter* Ch = Cast<ACharacter>(Victim)) { R = Ch->GetCapsuleComponent()->GetScaledCapsuleRadius() * 1.4f; }
			UDecalComponent* D = NewObject<UDecalComponent>(Victim);
			D->SetDecalMaterial(DM);
			D->DecalSize = FVector(R * 0.8f, R * 0.65f, R * 0.65f); // 11-06 night: was 1.6, it coated head and shoulders in one flat sheet
			D->SetupAttachment(Attach);
			D->RegisterComponent();
			const FVector Dir = FromDir.IsNearlyZero() ? FVector::ForwardVector : FromDir.GetSafeNormal();
			D->SetWorldLocationAndRotation(HitPoint + Dir * 10.f, (-Dir).Rotation());
			D->SetRelativeLocation(D->GetRelativeLocation() + FVector(FMath::FRandRange(-8.f, 8.f), FMath::FRandRange(-8.f, 8.f), FMath::FRandRange(-20.f, 20.f)));
			if (UMaterialInstanceDynamic* Dyn = D->CreateDynamicMaterialInstance()) { Dyn->SetVectorParameterValue(CDSpit::NAME_Color, C.NeonColor * 0.45f); Dyn->SetScalarParameterValue(CDSpit::NAME_Fade, 1.f); DecalMats.Add(Dyn); }
			Decals.Add(D);
		}
	}
	if (bIsHero && CDSpit::GScreenGoo && !ScreenMat)
	{
		if (UMaterialInterface* PP = S->WaspSlimeScreenMaterial.LoadSynchronous())
		{
			ScreenMat = UMaterialInstanceDynamic::Create(PP, this);
			ScreenMat->SetVectorParameterValue(CDSpit::NAME_Color, C.NeonColor);
		}
	}
}

void UCDWaspSlimeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	AActor* Victim = GetOwner();
	if (!Victim || bEnded) { return; }
	Remaining -= DeltaTime;
	const float Fade = FMath::Clamp(Remaining / FMath::Max(Total, 0.1f), 0.f, 1.f);
	for (UMaterialInstanceDynamic* M : DecalMats) { if (M) { M->SetScalarParameterValue(CDSpit::NAME_Fade, Fade); } }

	// slow: the victim's Blueprint writes MaxWalkSpeed itself every tick, so clamp after it (post-update tick group), remembering the raw value
	if (ACharacter* Ch = Cast<ACharacter>(Victim))
	{
		UCharacterMovementComponent* M = Ch->GetCharacterMovement();
		const float Raw = M->MaxWalkSpeed;
		if (BaseSpeed < 0.f || FMath::Abs(Raw - LastSet) > 1.f) { BaseSpeed = Raw; }   // the owner changed it: new base
		LastSet = BaseSpeed * FMath::Lerp(1.f, Slow, FMath::Clamp(Fade * 2.f, 0.f, 1.f));
		M->MaxWalkSpeed = LastSet;
	}
	if (bIsHero && ScreenMat && CDSpit::GScreenGoo)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(Victim, 0))
		{
			if (PC->PlayerCameraManager)
			{
				ScreenMat->SetScalarParameterValue(CDSpit::NAME_Fade, Fade);
				FPostProcessSettings PPS;
				PPS.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, ScreenMat));
				PC->PlayerCameraManager->AddCachedPPBlend(PPS, FMath::Clamp(Fade * 0.6f, 0.f, 0.6f)); // 11-06 night: a hint of goo, it washed the whole picture
			}
		}
	}
	if (Remaining <= 0.f) { EndSlime(); }
}

void UCDWaspSlimeComponent::EndSlime()
{
	if (bEnded) { return; }
	bEnded = true;
	if (ACharacter* Ch = Cast<ACharacter>(GetOwner()))
	{
		UCharacterMovementComponent* M = Ch->GetCharacterMovement();
		if (BaseSpeed > 0.f && FMath::Abs(M->MaxWalkSpeed - LastSet) < 1.f) { M->MaxWalkSpeed = BaseSpeed; }
	}
	for (UDecalComponent* D : Decals) { if (D) { D->DestroyComponent(); } }
	Decals.Reset(); DecalMats.Reset();
	ScreenMat = nullptr;
	DestroyComponent();
}

void UCDWaspSlimeComponent::OnComponentDestroyed(bool bDestroyingHierarchy)
{
	if (!bEnded)
	{
		bEnded = true;
		if (ACharacter* Ch = Cast<ACharacter>(GetOwner()))
		{
			if (UCharacterMovementComponent* M = Ch->GetCharacterMovement()) { if (BaseSpeed > 0.f && FMath::Abs(M->MaxWalkSpeed - LastSet) < 1.f) { M->MaxWalkSpeed = BaseSpeed; } }
		}
		for (UDecalComponent* D : Decals) { if (D) { D->DestroyComponent(); } }
	}
	Super::OnComponentDestroyed(bDestroyingHierarchy);
}
