// RealmWaspBase.cpp - the native zombie hornet (2026-11-06). See the header for the state machine.
#include "RealmWaspBase.h"
#include "CDWaspDirector.h"
#include "CDWaspBuzz.h"
#include "CDWaspSpit.h"
#include "CDSettings.h"
#include "CDStats.h"
#include "CDActorCache.h"
#include "CDSandDissolve.h"
#include "CrowdSubsystem.h"
#include "SoldierBase.h"
#include "ZombieBase.h"
#include "AIController.h"
#include "Animation/AnimSequence.h"
#include "Camera/CameraShakeBase.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/AudioComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "CollisionQueryParams.h"
#include "DrawDebugHelpers.h"
#include "Engine/DamageEvents.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/DamageType.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "UObject/UnrealType.h"

DECLARE_CYCLE_STAT(TEXT("Wasp Think"), STAT_CD_WaspThink, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Wasp Move"), STAT_CD_WaspMove, STATGROUP_CastleDefender);

namespace CDWasp
{
	static int32 GDebug = 0;
	static FAutoConsoleVariableRef CVarDebug(TEXT("cd.Wasp.Debug"), GDebug, TEXT("1 = draw each wasp's state, HP and goal."));
	static int32 GAudio = 1;
	static FAutoConsoleVariableRef CVarAudio(TEXT("cd.Wasp.Audio"), GAudio, TEXT("1 = procedural wing buzz on (default). 0 = silent wasps."));
	static int32 GSpit = 1;
	static FAutoConsoleVariableRef CVarSpit(TEXT("cd.Wasp.SpitAttack"), GSpit, TEXT("1 = wasps use the spit attack from their stalking point (default). 0 = stings only."));
	static int32 GPlayerAimReact = 1;
	static FAutoConsoleVariableRef CVarAim(TEXT("cd.Wasp.PlayerAimReact"), GPlayerAimReact, TEXT("1 = drones juke when the hero's camera stays on them (default). 0 = off."));

	static const TCHAR* StateName(EWaspState S)
	{
		switch (S)
		{
		case EWaspState::Arrive: return TEXT("Arrive"); case EWaspState::Patrol: return TEXT("Patrol"); case EWaspState::Stalk: return TEXT("Stalk");
		case EWaspState::Dive: return TEXT("Dive"); case EWaspState::Sting: return TEXT("Sting"); case EWaspState::Climb: return TEXT("Climb");
		case EWaspState::Evade: return TEXT("Evade"); case EWaspState::Retreat: return TEXT("Retreat"); case EWaspState::Dying: return TEXT("Dying"); case EWaspState::Spit: return TEXT("Spit");
		}
		return TEXT("?");
	}

	// Assets other systems made, found by path once (null = the effect is skipped, never a crash).
	template <typename T> T* LoadOnce(TWeakObjectPtr<T>& Slot, bool& bTried, const TCHAR* Path)
	{
		if (T* P = Slot.Get()) { return P; }
		if (bTried) { return nullptr; }
		bTried = true;
		T* Loaded = LoadObject<T>(nullptr, Path);
		Slot = Loaded;
		if (!Loaded) { UE_LOG(LogTemp, Warning, TEXT("cd.Wasp: asset %s not found, effect skipped"), Path); }
		return Loaded;
	}
	static UClass* LoadClassOnce(TWeakObjectPtr<UClass>& Slot, bool& bTried, const TCHAR* Path)
	{
		if (UClass* C = Slot.Get()) { return C; }
		if (bTried) { return nullptr; }
		bTried = true;
		UClass* Loaded = StaticLoadClass(UObject::StaticClass(), nullptr, Path);
		Slot = Loaded;
		if (!Loaded) { UE_LOG(LogTemp, Warning, TEXT("cd.Wasp: class %s not found, effect skipped"), Path); }
		return Loaded;
	}
	static TWeakObjectPtr<UClass> GBloodClass, GShakeClass, GCannonClass, GGateClass; static bool bBlood = false, bShake = false, bCannon = false, bGate = false;
	static const TCHAR* GatePath = TEXT("/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl.BP_CastleGateControl_C");
	static const FName NAME_bLoaded(TEXT("bLoaded")), NAME_Infected(TEXT("Infected"));
	static TWeakObjectPtr<USoundBase> GFleshHit; static bool bFlesh = false;
	static const TCHAR* BloodPath = TEXT("/Game/CastleDefender/VFX/BP_BloodBurst.BP_BloodBurst_C");
	static const TCHAR* ShakePath = TEXT("/Game/CastleDefender/Gameplay/Cannon/BP_CannonShake_Impact.BP_CannonShake_Impact_C");
	static const TCHAR* CannonPath = TEXT("/Game/CastleDefender/Gameplay/Cannon/BP_Cannon.BP_Cannon_C");
	static const TCHAR* FleshPath = TEXT("/Game/Audio/SFX_FleshHit.SFX_FleshHit");

	static const FName NAME_HitT(TEXT("HitT")), NAME_BlurOpacity(TEXT("BlurOpacity")), NAME_WingBlur(TEXT("WingBlur")), NAME_Wetness(TEXT("Wetness"));
	static const FName NAME_IsDead(TEXT("IsDead")), NAME_Dead(TEXT("Dead")), NAME_XP(TEXT("XP")), NAME_CheckLevelUp(TEXT("CheckLevelUp")), NAME_Xbow(TEXT("Xbow"));
	constexpr float StingHitTime = 0.43f;     // frame 13 of 30 at 30 fps (TGA #338)
	constexpr float StingClipTime = 1.0f;
	constexpr float EvadeTime = 0.55f;
}

// ---------------------------------------------------------------- pure rules

bool ARealmWaspBase::ShouldRetreat(float InHP, float InMaxHP, float RetreatFraction, int32 InRetreats, int32 MaxRetreats)
{
	if (InMaxHP <= 0.f || InHP <= 0.f) { return false; }
	if (InRetreats >= MaxRetreats) { return false; }
	return InHP / InMaxHP < RetreatFraction;
}

bool ARealmWaspBase::ShouldReturn(float InHP, float InMaxHP, float ReturnFraction, float RetreatSeconds, float MaxSeconds)
{
	if (InMaxHP <= 0.f) { return true; }
	return InHP / InMaxHP >= ReturnFraction || RetreatSeconds >= MaxSeconds;
}

float ARealmWaspBase::ScoreTarget(int32 Kind, float Dist, int32 Claims, float AggroRange, int32 MaxClaims)
{
	if (Dist > AggroRange || Claims >= MaxClaims) { return 0.f; }
	float Base = 0.f;
	switch (Kind)
	{
	case 4: Base = 120.f; break;   // cannons first (#169 stage 3: "1 cannons, 2 castle"); a sting unloads one
	case 1: Base = 90.f; break;    // a crossbow soldier: the thing that can hurt the swarm
	case 0: Base = 85.f; break;    // the hero
	case 2: Base = 60.f; break;    // other soldiers
	case 5: Base = 55.f; break;    // the castle gate control
	case 3: Base = 35.f; break;    // farmers
	default: return 0.f;
	}
	return Base / (1.f + Dist / 2000.f) * FMath::Max(0.05f, 1.f - 0.25f * float(Claims));
}

FVector ARealmWaspBase::LeadPoint(const FVector& TargetPos, const FVector& TargetVel, const FVector& From, float Speed, float MaxLeadSeconds)
{
	if (Speed <= 1.f) { return TargetPos; }
	const float T = FMath::Clamp(FVector::Dist(From, TargetPos) / Speed, 0.f, MaxLeadSeconds);
	return TargetPos + TargetVel * T;
}

// ---------------------------------------------------------------- setup

ARealmWaspBase::ARealmWaspBase()
{
	PrimaryActorTick.bCanEverTick = true;
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
	AIControllerClass = AAIController::StaticClass();
	bUseControllerRotationPitch = bUseControllerRotationYaw = bUseControllerRotationRoll = false;

	UCharacterMovementComponent* M = GetCharacterMovement();
	M->DefaultLandMovementMode = MOVE_Flying;
	M->GravityScale = 0.f;
	M->bOrientRotationToMovement = false;
	M->bUseControllerDesiredRotation = false;
	M->bRunPhysicsWithNoController = true;
	M->MaxFlySpeed = 1100.f;
	M->BrakingDecelerationFlying = 2600.f;
	M->MaxAcceleration = 3200.f;
	M->bUseRVOAvoidance = false;
	M->bCanWalkOffLedges = true;

	UCapsuleComponent* Cap = GetCapsuleComponent();
	Cap->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);   // slips past soldiers and zombies to reach its sting
	Cap->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	Cap->SetGenerateOverlapEvents(false);

	GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));   // the mesh faces +Y (TGA export), the actor faces +X
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	Tags.Add(TEXT("Wasp"));
	Tags.Add(TEXT("Flyer"));
}

const FCDWaspCasteSettings& ARealmWaspBase::Stats() const
{
	const UCDSettings* S = GetDefault<UCDSettings>();
	return Caste == EWaspCaste::Matriarch ? S->WaspMatriarch : S->WaspDrone;
}

void ARealmWaspBase::Init(EWaspCaste InCaste, const FVector& InAnchor, int32 InWave)
{
	Caste = InCaste;
	Anchor = InAnchor;
	Wave = InWave;
	const UCDSettings* S = GetDefault<UCDSettings>();
	const FCDWaspCasteSettings& C = Stats();
	MaxHP = C.MaxHP + C.HPPerWave * float(FMath::Max(0, InWave - S->WaspFirstWave));
	HP = MaxHP;
	SetActorScale3D(FVector(C.Scale));
}

void ARealmWaspBase::ApplyCaste()
{
	const UCDSettings* S = GetDefault<UCDSettings>();
	const FCDWaspCasteSettings& C = Stats();
	USkeletalMeshComponent* Skel = GetMesh();

	if (USkeletalMesh* SK = S->WaspMesh.LoadSynchronous())
	{
		Skel->SetSkeletalMeshAsset(SK);
		// capsule around the body, mesh centred in it (bounds in mesh space, actor scale applies on top)
		const FBoxSphereBounds B = SK->GetBounds();
		const float R = FMath::Clamp(FMath::Max(B.BoxExtent.X, B.BoxExtent.Y) * 0.55f, 25.f, 400.f);
		const float H = FMath::Clamp(B.BoxExtent.Z * 0.9f, R, 600.f);
		GetCapsuleComponent()->SetCapsuleSize(R, H, true);
		Skel->SetRelativeLocation(FVector(0.f, 0.f, -B.Origin.Z));
	}
	else { UE_LOG(LogTemp, Error, TEXT("cd.Wasp: WaspMesh %s did not load; the wasp is invisible"), *S->WaspMesh.ToString()); }

	ClipHover = S->WaspClipHover.LoadSynchronous();
	ClipFly = S->WaspClipFly.LoadSynchronous();
	ClipDive = S->WaspClipDive.LoadSynchronous();
	ClipSting = S->WaspClipSting.LoadSynchronous();
	ClipDeath = S->WaspClipDeath.LoadSynchronous();
	if (!ClipHover || !ClipFly || !ClipDive || !ClipSting || !ClipDeath) { UE_LOG(LogTemp, Error, TEXT("cd.Wasp: one or more wasp clips did not load (check Project Settings > Castle Defender > Wasps > Assets)")); }

	DynMats.Reset();
	const TSoftObjectPtr<UMaterialInterface>* Slots[4] = { &C.BodyMaterial, &C.WingsMaterial, &C.HairMaterial, &C.WingBlurMaterial };
	for (int32 i = 0; i < 4; ++i)
	{
		UMaterialInterface* M = Slots[i]->LoadSynchronous();
		if (!M || i >= Skel->GetNumMaterials()) { DynMats.Add(nullptr); continue; }
		UMaterialInstanceDynamic* D = UMaterialInstanceDynamic::Create(M, this);
		Skel->SetMaterial(i, D);
		DynMats.Add(D);
	}
	Skel->SetCastShadow(true);
}

void ARealmWaspBase::BeginPlay()
{
	Super::BeginPlay();
	UCDWaspDirector* Dir = UCDWaspDirector::Get(this);
	Director = Dir;
	if (Dir) { Dir->Register(this); }
	if (Anchor.IsNearlyZero()) { Anchor = Dir ? Dir->GetAnchor() : GetActorLocation(); }
	if (MaxHP <= 0.f) { Init(Caste, Anchor, Wave); }   // placed in a level by hand: Init never ran

	ApplyCaste();
	GetCharacterMovement()->SetMovementMode(MOVE_Flying);
	SpawnPoint = GetActorLocation();
	if (Dir && Dir->HasCrack() && FVector::Dist(SpawnPoint, Dir->GetCrackMouth()) < 1500.f) { OrbitPoint = Dir->GetCrackOrbitPoint(); }
	AnchorGroundZ = GroundUnder(Anchor).Z;
	PreferredSide = FMath::RandBool() ? 1.f : -1.f;
	PatrolPhase = FMath::FRandRange(0.f, 2.f * PI);
	PatrolDir = FMath::RandBool() ? 1.f : -1.f;
	PatrolRadius = FMath::FRandRange(900.f, 1600.f) * (Caste == EWaspCaste::Matriarch ? 1.3f : 1.f);
	ThinkJitter = FMath::FRandRange(0.f, GetDefault<UCDSettings>()->WaspThinkInterval);
	LastYaw = GetActorRotation().Yaw;

	const FCDWaspCasteSettings& C = Stats();
	if (CDWasp::GAudio && C.BuzzVolume > 0.f)
	{
		BuzzGen = NewObject<UCDWaspBuzz>(this);
		BuzzGen->SetBeat(C.BuzzPitchHz);
		BuzzGen->SetIntensity(0.6f);
		USoundAttenuation* Att = NewObject<USoundAttenuation>(this);
		Att->Attenuation.bAttenuate = true;
		Att->Attenuation.bSpatialize = true;
		Att->Attenuation.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
		Att->Attenuation.AttenuationShape = EAttenuationShape::Sphere;
		Att->Attenuation.AttenuationShapeExtents = FVector(Caste == EWaspCaste::Matriarch ? 900.f : 500.f, 0.f, 0.f);
		Att->Attenuation.FalloffDistance = Caste == EWaspCaste::Matriarch ? 6000.f : 3800.f;
		Att->Attenuation.dBAttenuationAtMax = -60.f;
		Buzz = UGameplayStatics::SpawnSoundAttached(BuzzGen, GetMesh(), NAME_None, FVector::ZeroVector, EAttachLocation::KeepRelativeOffset, false, C.BuzzVolume, 1.f, 0.f, Att, nullptr, false);
	}

	SetClip(EWaspClip::Fly, true, true);
	EnterState(EWaspState::Arrive);
}

void ARealmWaspBase::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UCDWaspDirector* Dir = Director.Get()) { Dir->ReleaseDiveToken(this); Dir->Unregister(this); }
	if (Buzz) { Buzz->Stop(); }
	Super::EndPlay(EndPlayReason);
}

// ---------------------------------------------------------------- tick

void ARealmWaspBase::Tick(float DeltaSeconds)
{
	// No Super::Tick on purpose: a Blueprint child's Event Tick must not fight this brain (BP_RealmWasp moved itself with SetActorLocation).
	if (State == EWaspState::Dying) { TickDying(DeltaSeconds); TickVisuals(DeltaSeconds); return; }
	TotalTime += DeltaSeconds;
	StateTime += DeltaSeconds;
	ThinkAcc += DeltaSeconds;
	const float Interval = GetDefault<UCDSettings>()->WaspThinkInterval;
	if (ThinkAcc >= Interval + ThinkJitter)
	{
		ThinkJitter = 0.f;
		const float Dt = ThinkAcc;
		ThinkAcc = 0.f;
		CD_SCOPE(STAT_CD_WaspThink);
		Think(Dt);
	}
	{
		CD_SCOPE(STAT_CD_WaspMove);
		TickMovement(DeltaSeconds);
	}
	TickVisuals(DeltaSeconds);
}

void ARealmWaspBase::Think(float Dt)
{
	const UCDSettings* S = GetDefault<UCDSettings>();
	const FCDWaspCasteSettings& C = Stats();
	UCDWaspDirector* Dir = Director.Get();
	AimReactCooldown -= Dt;
	SpitCooldownTimer -= Dt;

	// a hurt wasp leaves the fight; one that already spent its retreats fights to the death, faster
	if (State != EWaspState::Retreat && State != EWaspState::Sting && ShouldRetreat(HP, MaxHP, C.RetreatFraction, Retreats, C.MaxRetreats))
	{
		EnterState(EWaspState::Retreat);
		return;
	}
	if (!bDesperate && Retreats >= C.MaxRetreats && MaxHP > 0.f && HP / MaxHP < C.RetreatFraction) { bDesperate = true; }

	switch (State)
	{
	case EWaspState::Arrive:
		if (!OrbitPoint.IsNearlyZero())
		{
			// out of the crack: up to the orbit point, one circle around it, then off to the battlefield
			const float Orbit = S->WaspOrbitSecondsAtCrack;
			const float A = PatrolPhase + PatrolDir * (StateTime / FMath::Max(Orbit, 0.5f)) * 2.f * PI;
			StateGoal = OrbitPoint + FVector(FMath::Cos(A), FMath::Sin(A), 0.f) * 700.f + FVector(0.f, 0.f, 120.f * FMath::Sin(A * 2.f));
			if (StateTime > Orbit + 1.2f) { OrbitPoint = FVector::ZeroVector; StateTime = 0.f; }
			break;
		}
		StateGoal = PatrolPoint(TotalTime);
		if (FVector::Dist(GetActorLocation(), StateGoal) < 700.f || StateTime > 25.f) { EnterState(EWaspState::Patrol); }
		break;

	case EWaspState::Patrol:
		if (!TargetAlive()) { PickTarget(); }
		if (TargetAlive()) { EnterState(EWaspState::Stalk); break; }
		StateGoal = PatrolPoint(TotalTime);
		break;

	case EWaspState::Stalk:
	{
		if (!TargetAlive() || HitsOnTarget >= C.HitsPerTarget)
		{
			Target = nullptr; HitsOnTarget = 0;
			PickTarget();
			if (!TargetAlive()) { EnterState(EWaspState::Patrol); break; }
		}
		StateGoal = HoldingPointFor(TargetLocation());
		const bool bInPosition = FVector::Dist(GetActorLocation(), StateGoal) < 380.f;
		// second attack: a slime glob from here, when in range, off cooldown, and the dice say so
		if (CDWasp::GSpit && C.bCanSpit && SpitCooldownTimer <= 0.f && StateTime > 0.6f)
		{
			const float D = FVector::Dist(GetActorLocation(), TargetLocation());
			if (D >= C.SpitRangeMin && D <= C.SpitRangeMax && FMath::FRand() < C.SpitChance * (Dt / 0.15f)) { EnterState(EWaspState::Spit); break; }
		}
		if (bInPosition || StateTime > C.StalkPatience * 1.5f)
		{
			if (!bHasDiveToken && Dir) { bHasDiveToken = Dir->RequestDiveToken(this, GetWaspTarget()); }
			if (bHasDiveToken || StateTime > C.StalkPatience) { EnterState(EWaspState::Dive); }
		}
		break;
	}

	case EWaspState::Dive:
	{
		if (!TargetAlive()) { EnterState(EWaspState::Climb); break; }
		const FVector TL = TargetLocation();
		StateGoal = LeadPoint(TL, TargetVelocity(), GetActorLocation(), C.DiveSpeed);
		const float Reach = C.StingReach + TargetRadius();
		if (FVector::Dist(GetActorLocation(), TL) <= Reach) { EnterState(EWaspState::Sting); }
		else if (StateTime > 4.5f) { EnterState(EWaspState::Climb); }   // missed: break off and set up again
		break;
	}

	case EWaspState::Sting:
		if (StateTime >= CDWasp::StingClipTime) { EnterState(EWaspState::Climb); }
		break;

	case EWaspState::Spit:
		if (!TargetAlive()) { EnterState(EWaspState::Patrol); break; }
		if (!bSpatThisWindup && StateTime >= 0.36f) { bSpatThisWindup = true; DoSpit(); }
		if (StateTime >= 0.9f) { EnterState(EWaspState::Stalk); }
		break;

	case EWaspState::Climb:
		if (StateTime > 1.3f || FVector::Dist(GetActorLocation(), StateGoal) < 200.f)
		{
			if (TargetAlive() && HitsOnTarget < C.HitsPerTarget) { EnterState(EWaspState::Stalk); }
			else { Target = nullptr; HitsOnTarget = 0; EnterState(EWaspState::Patrol); }
		}
		break;

	case EWaspState::Evade:
		if (StateTime >= CDWasp::EvadeTime) { EnterState(ReturnState == EWaspState::Dive ? EWaspState::Stalk : ReturnState); }
		break;

	case EWaspState::Retreat:
		RetreatTime += Dt;
		HP = FMath::Min(MaxHP, HP + C.RetreatRegenPerSecond * Dt);
		StateGoal = RetreatPoint();
		if (ShouldReturn(HP, MaxHP, C.ReturnFraction, RetreatTime, C.RetreatMaxSeconds)) { Target = nullptr; EnterState(EWaspState::Patrol); }
		break;

	default: break;
	}

	// the hero's crosshair resting on a drone makes it juke (not while stinging, retreating or already rolling)
	if (CDWasp::GPlayerAimReact && C.PlayerAimReactSeconds > 0.f && AimReactCooldown <= 0.f &&
		(State == EWaspState::Stalk || State == EWaspState::Patrol || State == EWaspState::Dive || State == EWaspState::Arrive))
	{
		float Angle = 0.f;
		if (PlayerAimingAtMe(Angle))
		{
			PlayerAimTime += Dt;
			if (PlayerAimTime >= C.PlayerAimReactSeconds)
			{
				PlayerAimTime = 0.f;
				AimReactCooldown = FMath::FRandRange(1.4f, 2.4f);
				if (ACharacter* P = UGameplayStatics::GetPlayerCharacter(this, 0)) { StartEvade(P->GetActorLocation()); }
				if (Dir) { ++Dir->TotalDodges; }
			}
		}
		else { PlayerAimTime = FMath::Max(0.f, PlayerAimTime - Dt * 2.f); }
	}
}

void ARealmWaspBase::EnterState(EWaspState New)
{
	UCDWaspDirector* Dir = Director.Get();
	const bool bLeavingAttack = (State == EWaspState::Dive || State == EWaspState::Sting) && New != EWaspState::Sting;
	if (bLeavingAttack && bHasDiveToken) { if (Dir) { Dir->ReleaseDiveToken(this); } bHasDiveToken = false; }
	if (New != EWaspState::Evade) { ReturnState = New; }
	State = New;
	StateTime = 0.f;
	const FCDWaspCasteSettings& C = Stats();
	const FVector Loc = GetActorLocation();

	switch (New)
	{
	case EWaspState::Arrive:  StateGoal = PatrolPoint(TotalTime); SetClip(EWaspClip::Fly, true, true); BlurTarget = 0.7f; break;
	case EWaspState::Patrol:  SetClip(EWaspClip::Fly, true, false); BlurTarget = 0.6f; break;
	case EWaspState::Stalk:   SetClip(EWaspClip::Hover, true, false); BlurTarget = 0.4f; break;
	case EWaspState::Dive:    SetClip(EWaspClip::Dive, true, true); BlurTarget = 1.0f; break;
	case EWaspState::Sting:   SetClip(EWaspClip::Sting, false, true); StingTimer = CDWasp::StingHitTime; bStingLanded = false; BlurTarget = 0.5f; break;
	case EWaspState::Spit:    SetClip(EWaspClip::Sting, false, true); bSpatThisWindup = false; SpitCooldownTimer = C.SpitCooldown * FMath::FRandRange(0.85f, 1.25f); BlurTarget = 0.45f; break;
	case EWaspState::Climb:
	{
		const FVector Away = (Loc - (TargetAlive() ? TargetLocation() : Anchor)).GetSafeNormal2D();
		StateGoal = Loc + Away * 900.f + FVector(0.f, 0.f, 700.f);
		SetClip(EWaspClip::Fly, true, true); BlurTarget = 0.9f;
		break;
	}
	case EWaspState::Evade:   SetClip(EWaspClip::Fly, true, true); BlurTarget = 1.0f; break;
	case EWaspState::Retreat:
		++Retreats; RetreatTime = 0.f;
		if (Dir) { ++Dir->TotalRetreats; }
		SetClip(EWaspClip::Fly, true, true); BlurTarget = 1.0f;
		StateGoal = RetreatPoint();
		break;
	case EWaspState::Dying:   break;
	}
}

// ---------------------------------------------------------------- movement

void ARealmWaspBase::SetSpeedLimits(float MaxSpeed, float Accel)
{
	UCharacterMovementComponent* M = GetCharacterMovement();
	M->MaxFlySpeed = MaxSpeed;
	M->MaxAcceleration = Accel;
	M->BrakingDecelerationFlying = Accel * 0.8f;
}

void ARealmWaspBase::SteerTo(const FVector& Goal, float Speed, float Dt, float ArriveRadius)
{
	SetSpeedLimits(Speed, Stats().Acceleration);
	const FVector Loc = GetActorLocation();
	const FVector To = Goal - Loc;
	const float D = To.Size();
	if (D < ArriveRadius) { BlockedTime = 0.f; return; }   // let braking settle it
	const float Scale = FMath::Clamp(D / (ArriveRadius * 3.f), 0.35f, 1.f);
	AddMovementInput(To / D, Scale);
	// stuck against a wall or a roof: lift the goal
	if (GetVelocity().Size() < Speed * 0.12f && D > ArriveRadius * 2.f) { BlockedTime += Dt; } else { BlockedTime = 0.f; }
	if (BlockedTime > 0.6f) { StateGoal.Z += 450.f; BlockedTime = 0.f; }
}

void ARealmWaspBase::FaceVelocity(float Dt, float PitchScale)
{
	const FVector V = GetVelocity();
	const FRotator Cur = GetActorRotation();
	if (V.SizeSquared() < 120.f * 120.f)
	{
		SetActorRotation(FMath::RInterpTo(Cur, FRotator(0.f, Cur.Yaw, 0.f), Dt, 4.f));
		LastYaw = Cur.Yaw;
		return;
	}
	FRotator Want = V.Rotation();
	Want.Pitch = FMath::Clamp(Want.Pitch * PitchScale, -55.f, 40.f);
	const float YawRate = FMath::FindDeltaAngleDegrees(LastYaw, Want.Yaw) / FMath::Max(Dt, 0.001f);
	Want.Roll = FMath::Clamp(YawRate * 0.11f, -50.f, 50.f);   // bank into the turn
	LastYaw = Want.Yaw;
	SetActorRotation(FMath::RInterpTo(Cur, Want, Dt, 6.f));
}

void ARealmWaspBase::TickMovement(float Dt)
{
	const FCDWaspCasteSettings& C = Stats();
	const float Mult = bDesperate ? 1.2f : 1.f;
	const FVector Loc = GetActorLocation();

	switch (State)
	{
	case EWaspState::Arrive:
	case EWaspState::Patrol:
		SteerTo(StateGoal, C.CruiseSpeed * Mult, Dt, 250.f);
		FaceVelocity(Dt, 0.45f);
		break;

	case EWaspState::Stalk:
	{
		SteerTo(StateGoal, C.HoverSpeed * Mult, Dt, 90.f);
		if (TargetAlive())
		{
			FRotator Want = (TargetLocation() - Loc).Rotation();
			Want.Pitch = FMath::Clamp(Want.Pitch, -35.f, 10.f);
			Want.Roll = 0.f;
			SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, Dt, 5.f));
			LastYaw = GetActorRotation().Yaw;
		}
		break;
	}

	case EWaspState::Spit:
	{
		SetSpeedLimits(C.HoverSpeed, C.Acceleration);
		if (TargetAlive())
		{
			FRotator Want = (TargetLocation() - Loc).Rotation(); Want.Roll = 0.f;
			Want.Pitch = FMath::Clamp(Want.Pitch, -40.f, 15.f);
			SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, Dt, 9.f));
			LastYaw = GetActorRotation().Yaw;
		}
		break;
	}

	case EWaspState::Dive:
		SteerTo(StateGoal, C.DiveSpeed * Mult, Dt, 20.f);
		FaceVelocity(Dt, 1.0f);
		break;

	case EWaspState::Sting:
	{
		SetSpeedLimits(C.HoverSpeed, C.Acceleration);
		if (TargetAlive())
		{
			// hang on the target's shoulder for the strike, nose down on it
			const FVector TL = TargetLocation();
			const FVector Toward = (TL - Loc).GetSafeNormal();
			const FVector Hold = TL - Toward * (C.StingReach * 0.6f + TargetRadius()) + FVector(0.f, 0.f, 60.f);
			const FVector To = Hold - Loc;
			if (To.Size() > 40.f) { AddMovementInput(To.GetSafeNormal(), 0.6f); }
			FRotator Want = Toward.Rotation(); Want.Roll = 0.f;
			SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, Dt, 10.f));
		}
		if (StingTimer > 0.f)
		{
			StingTimer -= Dt;
			if (StingTimer <= 0.f && !bStingLanded) { bStingLanded = true; DoSting(); }
		}
		break;
	}

	case EWaspState::Climb:
		SteerTo(StateGoal, C.EscapeSpeed * Mult, Dt, 100.f);
		FaceVelocity(Dt, 0.8f);
		break;

	case EWaspState::Evade:
		SetSpeedLimits(C.EscapeSpeed * Mult, C.Acceleration * 1.5f);
		AddMovementInput(EvadeDir, 1.f);
		FaceVelocity(Dt, 0.6f);
		break;

	case EWaspState::Retreat:
	{
		SteerTo(StateGoal, C.EscapeSpeed * Mult, Dt, 300.f);
		// weave: a sideways component that flips with time, so a shot needs timing
		const FVector Fwd = GetVelocity().GetSafeNormal2D();
		const FVector Side = FVector::CrossProduct(Fwd, FVector::UpVector);
		AddMovementInput(Side, 0.55f * FMath::Sin(TotalTime * 3.1f + PatrolPhase));
		FaceVelocity(Dt, 0.5f);
		break;
	}
	default: break;
	}
}

// ---------------------------------------------------------------- places

FVector ARealmWaspBase::GroundUnder(const FVector& P, float MaxDrop) const
{
	FHitResult Hit;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(WaspGround), false, this);
	if (GetWorld() && GetWorld()->LineTraceSingleByChannel(Hit, P + FVector(0, 0, 200.f), P - FVector(0, 0, MaxDrop), ECC_WorldStatic, Q)) { return Hit.Location; }
	return FVector(P.X, P.Y, AnchorGroundZ);
}

FVector ARealmWaspBase::PatrolPoint(float Time) const
{
	const FCDWaspCasteSettings& C = Stats();
	const float AngVel = PatrolDir * (C.CruiseSpeed / FMath::Max(PatrolRadius, 200.f)) * 0.6f;
	const float A = PatrolPhase + Time * AngVel;
	const float R = PatrolRadius * (1.f + 0.2f * FMath::Sin(Time * 0.37f + PatrolPhase));
	const float Alt = FMath::Lerp(C.PatrolAltitudeMin, C.PatrolAltitudeMax, 0.5f + 0.5f * FMath::Sin(Time * 0.23f + PatrolPhase));
	return FVector(Anchor.X + FMath::Cos(A) * R, Anchor.Y + FMath::Sin(A) * R, AnchorGroundZ + Alt);
}

FVector ARealmWaspBase::HoldingPointFor(const FVector& TP) const
{
	const FCDWaspCasteSettings& C = Stats();
	FVector Fwd = FVector::ForwardVector;
	if (const AActor* T = GetWaspTarget()) { Fwd = T->GetActorForwardVector().GetSafeNormal2D(); if (Fwd.IsNearlyZero()) { Fwd = FVector::ForwardVector; } }
	const FVector Right = FVector::CrossProduct(FVector::UpVector, Fwd);
	FVector P = TP - Fwd * C.StalkDistance * 0.6f + Right * PreferredSide * C.StalkDistance * 0.8f + FVector(0.f, 0.f, C.StalkHeight);
	const float GroundZ = GroundUnder(P).Z;
	P.Z = FMath::Max(P.Z, GroundZ + 300.f);
	return P;
}

AActor* ARealmWaspBase::NearestThreat(float& OutDist) const
{
	AActor* Best = nullptr; OutDist = TNumericLimits<float>::Max();
	const FVector Loc = GetActorLocation();
	auto Consider = [&](AActor* A) { if (!IsValid(A)) { return; } const float D = FVector::Dist(Loc, A->GetActorLocation()); if (D < OutDist) { OutDist = D; Best = A; } };
	if (ACharacter* P = UGameplayStatics::GetPlayerCharacter(this, 0)) { if (!AZombieBase::ReadBlueprintBool(P, CDWasp::NAME_IsDead)) { Consider(P); } }
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->ForEachSoldier([&](AActor* A)
		{
			if (!A->ActorHasTag(CDWasp::NAME_Xbow)) { return; }
			if (const ASoldierBase* SB = Cast<ASoldierBase>(A)) { if (SB->IsSoldierDead()) { return; } }
			Consider(A);
		});
	}
	return Best;
}

FVector ARealmWaspBase::RetreatPoint() const
{
	const FCDWaspCasteSettings& C = Stats();
	float D = 0.f;
	const AActor* Threat = NearestThreat(D);
	const FVector Loc = GetActorLocation();
	const FVector From = Threat ? Threat->GetActorLocation() : Anchor;
	FVector Away = (Loc - From).GetSafeNormal2D();
	if (Away.IsNearlyZero()) { Away = FVector(FMath::Cos(PatrolPhase), FMath::Sin(PatrolPhase), 0.f); }
	FVector P = From + Away * C.RetreatDistance;
	P.Z = AnchorGroundZ + C.RetreatAltitude + 300.f * FMath::Sin(TotalTime * 0.8f + PatrolPhase);
	return P;
}

// ---------------------------------------------------------------- targets

void ARealmWaspBase::PickTarget()
{
	const UCDSettings* S = GetDefault<UCDSettings>();
	UCDWaspDirector* Dir = Director.Get();
	const FVector Loc = GetActorLocation();
	Target = nullptr; TargetKind = -1; HitsOnTarget = 0;
	float Best = 0.f;
	auto Consider = [&](AActor* A, int32 Kind)
	{
		if (!IsValid(A)) { return; }
		const float D = FVector::Dist(Loc, A->GetActorLocation());
		const int32 Claims = Dir ? Dir->ClaimsOn(A) : 0;
		const int32 MaxClaims = Kind == 0 ? S->WaspMaxOnHero : S->WaspMaxDiversPerTarget + 1;
		const float Sc = ScoreTarget(Kind, D, Claims, S->WaspAggroRange, MaxClaims) * FMath::FRandRange(0.9f, 1.1f);
		if (Sc > Best) { Best = Sc; Target = A; TargetKind = Kind; }
	};
	if (ACharacter* P = UGameplayStatics::GetPlayerCharacter(this, 0)) { if (!AZombieBase::ReadBlueprintBool(P, CDWasp::NAME_IsDead)) { Consider(P, 0); } }
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->ForEachSoldier([&](AActor* A)
		{
			if (const ASoldierBase* SB = Cast<ASoldierBase>(A)) { if (SB->IsSoldierDead()) { return; } }
			Consider(A, A->ActorHasTag(CDWasp::NAME_Xbow) ? 1 : 2);
		});
		Crowd->ForEachFarmer([&](AActor* A) { if (!AZombieBase::ReadBlueprintBool(A, CDWasp::NAME_Dead)) { Consider(A, 3); } });
	}
	if (UClass* CannonClass = CDWasp::LoadClassOnce(CDWasp::GCannonClass, CDWasp::bCannon, CDWasp::CannonPath))
	{
		if (UCDActorCache* Cache = UCDActorCache::Get(this))
		{
			TArray<AActor*> Cannons;
			Cache->GetAllActorsOfClass(CannonClass, Cannons);
			for (AActor* A : Cannons) { Consider(A, 4); }
		}
	}
	if (UClass* GateClass = CDWasp::LoadClassOnce(CDWasp::GGateClass, CDWasp::bGate, CDWasp::GatePath))
	{
		if (UCDActorCache* Cache = UCDActorCache::Get(this)) { if (AActor* G = Cache->GetActorOfClass(GateClass)) { Consider(G, 5); } }
	}
}

bool ARealmWaspBase::TargetAlive() const
{
	AActor* T = Target.Get();
	if (!IsValid(T)) { return false; }
	if (const ASoldierBase* SB = Cast<ASoldierBase>(T)) { if (SB->IsSoldierDead()) { return false; } }
	bool bFound = false;
	const bool bDead = AZombieBase::ReadBlueprintBool(T, TargetKind == 0 ? CDWasp::NAME_IsDead : CDWasp::NAME_Dead, &bFound);
	if (bFound && bDead) { return false; }
	if (T->GetLifeSpan() > 0.f && T->GetLifeSpan() < 0.01f) { return false; }
	return FVector::Dist(GetActorLocation(), T->GetActorLocation()) < GetDefault<UCDSettings>()->WaspAggroRange * 1.5f;
}

FVector ARealmWaspBase::TargetLocation() const
{
	const AActor* T = GetWaspTarget();
	return T ? T->GetActorLocation() : Anchor;
}

FVector ARealmWaspBase::TargetVelocity() const
{
	const AActor* T = GetWaspTarget();
	return T ? T->GetVelocity() : FVector::ZeroVector;
}

float ARealmWaspBase::TargetRadius() const
{
	if (const ACharacter* Ch = Cast<ACharacter>(GetWaspTarget())) { return Ch->GetCapsuleComponent()->GetScaledCapsuleRadius(); }
	return 100.f;
}

bool ARealmWaspBase::PlayerAimingAtMe(float& OutAngleDeg) const
{
	const APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PC || !PC->PlayerCameraManager) { return false; }
	const FVector CamLoc = PC->PlayerCameraManager->GetCameraLocation();
	const FVector CamDir = PC->PlayerCameraManager->GetActorForwardVector();
	const FVector To = GetActorLocation() - CamLoc;
	const float D = To.Size();
	if (D < 50.f || D > 5500.f) { return false; }
	OutAngleDeg = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(CamDir, To / D), -1.f, 1.f)));
	const float MyRadius = GetCapsuleComponent()->GetScaledCapsuleRadius();
	const float Thresh = FMath::RadiansToDegrees(FMath::Atan(MyRadius * 2.5f / D)) + 2.5f;
	return OutAngleDeg < Thresh;
}

// ---------------------------------------------------------------- fight

void ARealmWaspBase::StartEvade(const FVector& AwayFrom)
{
	if (State == EWaspState::Sting || State == EWaspState::Dying || State == EWaspState::Retreat) { return; }
	if (State != EWaspState::Evade) { ReturnState = (State == EWaspState::Dive || State == EWaspState::Spit) ? EWaspState::Stalk : State; }
	const FVector Loc = GetActorLocation();
	const FVector ToMe = (Loc - AwayFrom).GetSafeNormal();
	FVector Side = FVector::CrossProduct(ToMe, FVector::UpVector).GetSafeNormal();
	if (Side.IsNearlyZero()) { Side = FVector::RightVector; }
	Side *= FMath::RandBool() ? 1.f : -1.f;
	EvadeDir = (Side + FVector(0.f, 0.f, FMath::FRandRange(-0.35f, 0.5f))).GetSafeNormal();
	if (bHasDiveToken) { if (UCDWaspDirector* Dir = Director.Get()) { Dir->ReleaseDiveToken(this); } bHasDiveToken = false; }
	State = EWaspState::Evade;   // keep ReturnState as set above (EnterState would overwrite it)
	StateTime = 0.f;
	SetClip(EWaspClip::Fly, true, true);
	BlurTarget = 1.f;
}

void ARealmWaspBase::NotifyAimedAt(AActor* Shooter)
{
	const FCDWaspCasteSettings& C = Stats();
	if (!Shooter || C.DodgeChance <= 0.f || AimReactCooldown > 0.f) { return; }
	if (State != EWaspState::Stalk && State != EWaspState::Patrol && State != EWaspState::Dive && State != EWaspState::Arrive) { return; }
	if (FMath::FRand() >= C.DodgeChance) { return; }
	AimReactCooldown = 1.2f;
	StartEvade(Shooter->GetActorLocation());
	if (UCDWaspDirector* Dir = Director.Get()) { ++Dir->TotalDodges; }
}

float ARealmWaspBase::GetHitChanceFor(const AActor* Shooter) const
{
	const FCDWaspCasteSettings& C = Stats();
	float P = C.BaseHitChance;
	if (State == EWaspState::Evade) { P *= 0.35f; }
	else if (State == EWaspState::Retreat) { P *= 0.85f; }
	else if (State == EWaspState::Dive) { P *= 0.9f; }
	else if (State == EWaspState::Stalk || State == EWaspState::Sting || State == EWaspState::Spit) { P *= 1.1f; }   // a hovering wasp is the easy shot
	if (Shooter && FVector::Dist(Shooter->GetActorLocation(), GetActorLocation()) > 2200.f) { P *= 0.85f; }
	return FMath::Clamp(P, 0.02f, 0.98f);
}

void ARealmWaspBase::DoSting()
{
	AActor* T = GetWaspTarget();
	if (!T) { return; }
	const FCDWaspCasteSettings& C = Stats();
	const FVector Loc = GetActorLocation();
	const FVector TL = T->GetActorLocation();
	const float Reach = (C.StingReach + TargetRadius()) * 1.6f + 120.f;
	if (FVector::Dist(Loc, TL) > Reach) { return; }   // the target got away during the wind-up

	UGameplayStatics::ApplyDamage(T, C.StingDamage, GetController(), this, UDamageType::StaticClass());
	++HitsOnTarget;
	if (UCDWaspDirector* Dir = Director.Get()) { ++Dir->TotalStings; }
	// the plan's two extras: a stung cannon loses its load (the crew must reload); a sting on the hero may infect (BPC_Infection)
	if (TargetKind == 4)
	{
		if (FBoolProperty* P = CastField<FBoolProperty>(T->GetClass()->FindPropertyByName(CDWasp::NAME_bLoaded))) { P->SetPropertyValue_InContainer(T, false); }
	}
	else if (TargetKind == 0 && C.StingInfectChance > 0.f && FMath::FRand() < C.StingInfectChance)
	{
		TInlineComponentArray<UActorComponent*> Comps; T->GetComponents(Comps);
		for (UActorComponent* Comp : Comps)
		{
			if (!Comp || !Comp->GetClass()->GetName().StartsWith(TEXT("BPC_Infection"))) { continue; }
			if (FBoolProperty* P = CastField<FBoolProperty>(Comp->GetClass()->FindPropertyByName(CDWasp::NAME_Infected))) { if (!P->GetPropertyValue_InContainer(Comp)) { P->SetPropertyValue_InContainer(Comp, true); UE_LOG(LogTemp, Display, TEXT("cd.Wasp: the sting infected the hero")); } }
			break;
		}
	}

	const FVector HitPoint = TL + (Loc - TL).GetSafeNormal() * TargetRadius() * 0.8f + FVector(0.f, 0.f, 40.f);
	if (UClass* Blood = CDWasp::LoadClassOnce(CDWasp::GBloodClass, CDWasp::bBlood, CDWasp::BloodPath))
	{
		FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		GetWorld()->SpawnActor<AActor>(Blood, FTransform((Loc - TL).GetSafeNormal().Rotation(), HitPoint), P);
	}
	if (USoundBase* Snd = CDWasp::LoadOnce(CDWasp::GFleshHit, CDWasp::bFlesh, CDWasp::FleshPath))
	{
		UGameplayStatics::PlaySoundAtLocation(this, Snd, HitPoint, Caste == EWaspCaste::Matriarch ? 1.1f : 0.8f, Caste == EWaspCaste::Matriarch ? 0.8f : 1.15f);
	}
	if (C.Knockback > 0.f)
	{
		if (ACharacter* Ch = Cast<ACharacter>(T))
		{
			const FVector Dir = (TL - Loc).GetSafeNormal2D();
			Ch->LaunchCharacter(Dir * C.Knockback + FVector(0.f, 0.f, C.Knockback * 0.45f), true, true);
		}
	}
	if (C.bCameraShakeOnSting) { OnMatriarchStingFX(T, HitPoint); }
}

void ARealmWaspBase::DoSpit()
{
	AActor* T = GetWaspTarget();
	UWorld* World = GetWorld();
	if (!T || !World) { return; }
	const FCDWaspCasteSettings& C = Stats();
	const FVector Mouth = GetActorLocation() + GetActorForwardVector() * (GetCapsuleComponent()->GetScaledCapsuleRadius() + C.SpitRadius) + FVector(0.f, 0.f, -10.f);
	const FVector Aim = LeadPoint(TargetLocation() + FVector(0.f, 0.f, 30.f), TargetVelocity(), Mouth, C.SpitSpeed, 0.8f);
	const FVector To = Aim - Mouth;
	const float D = To.Size();
	const float Flight = D / FMath::Max(C.SpitSpeed, 1.f);
	// gravity compensation for the glob's 0.55 gravity scale
	FVector Vel = To.GetSafeNormal() * C.SpitSpeed + FVector(0.f, 0.f, 0.5f * 980.f * 0.55f * Flight);
	FActorSpawnParameters P; P.Owner = this; P.Instigator = this; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (ACDWaspSpit* Glob = World->SpawnActor<ACDWaspSpit>(ACDWaspSpit::StaticClass(), FTransform(Vel.Rotation(), Mouth), P))
	{
		Glob->Launch(this, Caste, Vel);
	}
	if (USoundBase* Snd = CDWasp::LoadOnce(CDWasp::GFleshHit, CDWasp::bFlesh, CDWasp::FleshPath))
	{
		UGameplayStatics::PlaySoundAtLocation(this, Snd, Mouth, 0.5f, Caste == EWaspCaste::Matriarch ? 0.5f : 0.75f);
	}
	if (UCDWaspDirector* Dir = Director.Get()) { ++Dir->TotalStings; }
}

void ARealmWaspBase::OnMatriarchStingFX(AActor* Victim, const FVector& HitPoint)
{
	if (UClass* Shake = CDWasp::LoadClassOnce(CDWasp::GShakeClass, CDWasp::bShake, CDWasp::ShakePath))
	{
		if (Shake->IsChildOf(UCameraShakeBase::StaticClass()))
		{
			UGameplayStatics::PlayWorldCameraShake(this, Shake, HitPoint, 300.f, 2600.f, 1.3f);
		}
	}
}

float ARealmWaspBase::TakeDamage(float Damage, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	// Deliberately not Super::TakeDamage: this class owns HP and death; a Blueprint child's AnyDamage never runs.
	if (State == EWaspState::Dying || Damage <= 0.f) { return 0.f; }
	HP -= Damage;
	HitFlash = 1.f;
	LastDamageCauser = DamageCauser;
	LastHitFrom = DamageCauser ? DamageCauser->GetActorLocation() : (EventInstigator && EventInstigator->GetPawn() ? EventInstigator->GetPawn()->GetActorLocation() : GetActorLocation() - GetActorForwardVector() * 100.f);
	if (BuzzGen) { BuzzGen->SetDamage(1.f - FMath::Clamp(HP / FMath::Max(MaxHP, 1.f), 0.f, 1.f)); }

	if (HP <= 0.f)
	{
		Die(EventInstigator && EventInstigator->GetPawn() ? EventInstigator->GetPawn() : DamageCauser);
		return Damage;
	}
	// a hit shoves it and often makes it roll away (not in the middle of a sting; a retreating wasp just keeps going)
	if (State != EWaspState::Sting && State != EWaspState::Retreat)
	{
		const FVector Shove = (GetActorLocation() - LastHitFrom).GetSafeNormal() * (Caste == EWaspCaste::Matriarch ? 150.f : 420.f);
		GetCharacterMovement()->Velocity += Shove;
		if (FMath::FRand() < (Caste == EWaspCaste::Matriarch ? 0.1f : 0.4f)) { StartEvade(LastHitFrom); }
	}
	return Damage;
}

void ARealmWaspBase::Kill()
{
	if (State != EWaspState::Dying) { HP = 0.f; Die(nullptr); }
}

void ARealmWaspBase::Die(AActor* Killer)
{
	UCDWaspDirector* Dir = Director.Get();
	if (bHasDiveToken && Dir) { Dir->ReleaseDiveToken(this); bHasDiveToken = false; }
	State = EWaspState::Dying;
	StateTime = 0.f; DyingTime = 0.f; bLanded = false; bDissolving = false;
	if (Dir) { ++Dir->TotalKilled; }
	AwardXP();

	SetClip(EWaspClip::Death, false, true);
	UCharacterMovementComponent* M = GetCharacterMovement();
	M->StopMovementImmediately();
	M->GravityScale = 1.4f;
	M->SetMovementMode(MOVE_Falling);
	// a small tumble: keep some of the last velocity sideways
	M->Velocity = GetVelocity() * 0.3f + FVector(0.f, 0.f, 80.f);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	if (BuzzGen) { BuzzGen->SetDamage(1.f); }
	SetLifeSpan(14.f);   // safety net: nothing stays forever
}

void ARealmWaspBase::TickDying(float Dt)
{
	DyingTime += Dt;
	UCharacterMovementComponent* M = GetCharacterMovement();
	if (!bLanded && (M->IsMovingOnGround() || DyingTime > 4.f))
	{
		bLanded = true;
		LandTime = DyingTime;
		M->StopMovementImmediately();
		M->SetMovementMode(MOVE_None);
	}
	if (bLanded)
	{
		// the wings are still: the death clip has its own two spasms, then it rests; the last roll is a slow settle
		const float Settle = FMath::Clamp((DyingTime - LandTime) / 1.5f, 0.f, 1.f);
		FRotator R = GetActorRotation();
		R.Pitch = FMath::Lerp(R.Pitch, 0.f, Settle * 0.2f);
		SetActorRotation(R);
	}
	if (bLanded && !bDissolving && DyingTime > LandTime + 2.4f)
	{
		bDissolving = true;
		DissolveStart = DyingTime;
		UCDSandDissolveLibrary::StartSandDissolve(this, 0.05f, 1.3f, Caste == EWaspCaste::Matriarch ? 1600 : 520);
		SetLifeSpan(1.6f);
	}
	if (bDissolving && DyingTime > DissolveStart + 0.9f && GetMesh()->IsVisible()) { GetMesh()->SetVisibility(false, true); }
	if (BuzzGen) { BuzzGen->SetIntensity(FMath::Max(0.f, 0.5f - DyingTime * 0.45f)); }
	if (Buzz && DyingTime > 1.3f && Buzz->IsPlaying()) { Buzz->Stop(); }
	// a landed body darkens and wets (the rot shows)
	if (DynMats.Num() > 0 && DynMats[0]) { DynMats[0]->SetScalarParameterValue(CDWasp::NAME_Wetness, FMath::Clamp(DyingTime * 0.3f, 0.f, 0.8f)); }
}

void ARealmWaspBase::AwardXP()
{
	ACharacter* P = UGameplayStatics::GetPlayerCharacter(this, 0);
	if (!P) { return; }
	if (FIntProperty* XP = CastField<FIntProperty>(P->GetClass()->FindPropertyByName(CDWasp::NAME_XP)))
	{
		XP->SetPropertyValue_InContainer(P, XP->GetPropertyValue_InContainer(P) + Stats().XPValue);
	}
	if (UFunction* F = P->FindFunction(CDWasp::NAME_CheckLevelUp)) { if (F->NumParms == 0) { P->ProcessEvent(F, nullptr); } }
}

// ---------------------------------------------------------------- visuals

void ARealmWaspBase::SetClip(EWaspClip Clip, bool bLoop, bool bForce)
{
	if (Clip == CurrentClip && !bForce) { PendingClip = EWaspClip::None; return; }
	UAnimSequence* A = nullptr;
	switch (Clip)
	{
	case EWaspClip::Hover: A = ClipHover; break; case EWaspClip::Fly: A = ClipFly; break; case EWaspClip::Dive: A = ClipDive; break;
	case EWaspClip::Sting: A = ClipSting; break; case EWaspClip::Death: A = ClipDeath; break; default: break;
	}
	if (!A) { return; }
	USkeletalMeshComponent* Skel = GetMesh();
	if (!bForce && CurrentClip != EWaspClip::None && PendingTime < 0.6f)
	{
		// single-node playback has no blending: switch at the loop seam, where the TGA clips meet their own first frame
		const float Pos = Skel->GetPosition();
		const UAnimationAsset* Cur = Skel->AnimationData.AnimToPlay;
		const float Len = Cur ? Cur->GetPlayLength() : 0.f;
		if (Len > 0.3f && Pos > 0.08f && Pos < Len - 0.08f) { PendingClip = Clip; bPendingLoop = bLoop; return; }
	}
	Skel->PlayAnimation(A, bLoop);
	Skel->SetPlayRate(1.f);
	CurrentClip = Clip;
	PendingClip = EWaspClip::None;
	PendingTime = 0.f;
}

void ARealmWaspBase::TickVisuals(float Dt)
{
	if (PendingClip != EWaspClip::None) { PendingTime += Dt; SetClip(PendingClip, bPendingLoop, false); }

	const FCDWaspCasteSettings& C = Stats();
	const float Speed = GetVelocity().Size();
	LastSpeed = Speed;
	USkeletalMeshComponent* Skel = GetMesh();
	if (State != EWaspState::Dying)
	{
		if (CurrentClip == EWaspClip::Fly || CurrentClip == EWaspClip::Hover) { Skel->SetPlayRate(FMath::Clamp(0.85f + 0.5f * Speed / FMath::Max(C.CruiseSpeed, 1.f), 0.7f, 1.6f)); }
		else if (CurrentClip == EWaspClip::Dive) { Skel->SetPlayRate(1.2f); }
	}

	HitFlash = FMath::Max(0.f, HitFlash - Dt * 4.f);
	BlurNow = FMath::FInterpTo(BlurNow, State == EWaspState::Dying ? 0.f : FMath::Max(BlurTarget, FMath::Clamp(Speed / FMath::Max(C.DiveSpeed, 1.f), 0.f, 1.f)), Dt, 5.f);
	if (DynMats.Num() >= 4)
	{
		if (DynMats[0]) { DynMats[0]->SetScalarParameterValue(CDWasp::NAME_HitT, HitFlash); }
		if (DynMats[1]) { DynMats[1]->SetScalarParameterValue(CDWasp::NAME_WingBlur, BlurNow * 0.6f); }
		if (DynMats[3]) { DynMats[3]->SetScalarParameterValue(CDWasp::NAME_BlurOpacity, 0.25f + 0.75f * BlurNow); }
	}

	if (BuzzGen && State != EWaspState::Dying)
	{
		BuzzGen->SetBeat(C.BuzzPitchHz * (0.85f + 0.4f * FMath::Clamp(Speed / FMath::Max(C.DiveSpeed, 1.f), 0.f, 1.f)));
		float I = 0.6f;
		switch (State)
		{
		case EWaspState::Stalk: I = 0.45f; break; case EWaspState::Dive: I = 1.f; break; case EWaspState::Sting: I = 0.8f; break;
		case EWaspState::Evade: I = 0.95f; break; case EWaspState::Retreat: I = 0.8f; break; case EWaspState::Spit: I = 0.7f; break; default: break;
		}
		BuzzGen->SetIntensity(I);
	}

	if (CDWasp::GDebug && GetWorld())
	{
		const FString Txt = FString::Printf(TEXT("%s %s %.0f/%.0f%s%s"), Caste == EWaspCaste::Matriarch ? TEXT("MATRIARCH") : TEXT("drone"), CDWasp::StateName(State), HP, MaxHP,
			bHasDiveToken ? TEXT(" [dive]") : TEXT(""), bDesperate ? TEXT(" DESPERATE") : TEXT(""));
		DrawDebugString(GetWorld(), GetActorLocation() + FVector(0, 0, 120.f * GetActorScale3D().Z), Txt, nullptr, State == EWaspState::Retreat ? FColor::Yellow : (IsDiving() ? FColor::Red : FColor::Cyan), 0.f, true);
		if (State != EWaspState::Dying) { DrawDebugLine(GetWorld(), GetActorLocation(), StateGoal, FColor(80, 200, 255), false, 0.f, 0, 2.f); }
	}
}
