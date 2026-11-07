#include "ZombieBase.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "CollisionQueryParams.h"
#include "Engine/OverlapResult.h"
#include "Engine/DamageEvents.h"
#include "CDCombatRules.h"
#include "CDWeaponPerks.h"
#include "CDSettings.h"
#include "CDStats.h"
#include "CrowdSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Blueprint/AIBlueprintHelperLibrary.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"

DECLARE_CYCLE_STAT(TEXT("Zombie PickTarget"), STAT_CD_PickTarget, STATGROUP_CastleDefender);

AZombieBase::AZombieBase()
{
	PrimaryActorTick.bCanEverTick = true;
}

namespace CDZombieBrain
{
	// rev 3 (review P1-5): the native tick additions are owner-requested GAMEPLAY FIXES, not parity work, and stay on by default.
	// cd.Zombie.Baseline 1 turns ALL of them off at once (unstick, no-giant, WMRef repair, camera rule) for parity runs and
	// benchmarks against the original Blueprint behaviour; each can also be toggled alone (cd.Zombie.Unstick / NoGiant / ...).
	static int32 GBaseline = 0;
	static FAutoConsoleVariableRef CVarBaseline(TEXT("cd.Zombie.Baseline"), GBaseline, TEXT("1 = original Blueprint behaviour: every native zombie fix off (parity / benchmark baseline). 0 = fixes on (default)."));
	static int32 GUnstick = 1;
	static float GUnstickSeconds = 1.5f;
	static int32 GNoGiant = 1;
	static int32 GUnstickCount = 0, GGiantBlocked = 0, GWMRefFixed = 0;
	static FAutoConsoleVariableRef CVarUnstick(TEXT("cd.Zombie.Unstick"), GUnstick, TEXT("1 = re-issue a move order to zombies that stand still while not attacking (default)."));
	static FAutoConsoleVariableRef CVarUnstickSec(TEXT("cd.Zombie.UnstickSeconds"), GUnstickSeconds, TEXT("Seconds a zombie may stand still (not attacking, no montage) before it is sent on again."));
	static FAutoConsoleVariableRef CVarNoGiant(TEXT("cd.Zombie.NoGiant"), GNoGiant, TEXT("1 = zombies keep their spawn size and never belly-crawl (blocks Think's type-5 x3 transform). 0 = as authored."));
	static FAutoConsoleCommand CmdReport(TEXT("cd.Zombie.Report"), TEXT("Print how often the native zombie fixes fired."),
		FConsoleCommandDelegate::CreateLambda([]() { UE_LOG(LogTemp, Display, TEXT("cd.Zombie: unstick orders %d, giant transforms blocked %d, wave-manager refs fixed %d"), GUnstickCount, GGiantBlocked, GWMRefFixed); }));
}

namespace CDZombieKnock
{
	static int32 GColossusKnockback = 0;
	static FAutoConsoleVariableRef CVar(TEXT("cd.Combat.ColossusKnockback"), GColossusKnockback,
		TEXT("1 = colossi are knocked back / launched by hits like ordinary zombies (old). 0 = colossi stand their ground (default)."));
}

void AZombieBase::LaunchCharacter(FVector LaunchVelocity, bool bXYOverride, bool bZOverride)
{
	if (!CDZombieKnock::GColossusKnockback && !CDZombieBrain::GBaseline && UCDCombatRules::IsColossus(this)) { return; }
	Super::LaunchCharacter(LaunchVelocity, bXYOverride, bZOverride);
}

void AZombieBase::BeginPlay()
{
	Super::BeginPlay();   // runs the Blueprint's Event BeginPlay; registration below does not depend on it
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->RegisterZombie(this);
	}
	CacheSpawnShape();
}

void AZombieBase::CacheSpawnShape()
{
	// after the Blueprint's BeginPlay (actor scale, walk speed by type / runner) so these are the zombie's real spawn values
	if (const USkeletalMeshComponent* M = GetMesh())
	{
		SpawnMeshScale = M->GetRelativeScale3D();
		SpawnMeshLocation = M->GetRelativeLocation();
	}
	if (const UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		SpawnWalkSpeed = Move->MaxWalkSpeed;
	}
	bSpawnShapeCached = true;
}

namespace CDZombieCamera
{
	// Camera boom ignores ordinary zombies (no more camera pushed around in a crowd); colossi still block it (owner 2026-11-05).
	// Applied once, 0.5 s after spawn, so the wave manager has already given colossus zombies their material.
	static int32 GEnable = 1;
	static FAutoConsoleVariableRef CVar(TEXT("cd.Zombie.CameraIgnore"), GEnable, TEXT("1 = the camera ignores zombies except colossi (default). Applies to zombies spawned afterwards."));
	static TSet<TWeakObjectPtr<AActor>> GDone;

	static void Apply(AActor* Z)
	{
		if (!GEnable || GDone.Contains(Z) || Z->GetGameTimeSinceCreation() < 0.5f) { return; }
		if (GDone.Num() > 4096) { for (auto It = GDone.CreateIterator(); It; ++It) { if (!It->IsValid()) { It.RemoveCurrent(); } } }
		GDone.Add(Z);
		const ECollisionResponse R = UCDCombatRules::IsColossus(Z) ? ECR_Block : ECR_Ignore;
		TArray<UPrimitiveComponent*> Prims;
		Z->GetComponents(Prims);
		for (UPrimitiveComponent* P : Prims)
		{
			if (P && P->GetCollisionEnabled() != ECollisionEnabled::NoCollision) { P->SetCollisionResponseToChannel(ECC_Camera, R); }
		}
	}
}

void AZombieBase::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);   // Blueprint Event Tick first
	if (CDZombieBrain::GBaseline) { return; }   // parity baseline: nothing native after the Blueprint tick
	CDZombieCamera::Apply(this);
	TickWaveManagerRef(DeltaSeconds);
	if (IsDeadForCrowd()) { return; }
	TickNoGiant();
	TickUnstick(DeltaSeconds);
	TickGroundSnap(DeltaSeconds);
}

void AZombieBase::TickWaveManagerRef(float DeltaSeconds)
{
	// BP_Zombie sets WMRef once, in BeginPlay, with Get Actor Of Class. Zombies that spawn before the wave manager is streamed in
	// (jelly-blob zombies) keep None forever: every Think branch that reads it fails ("Accessed None ... WMRef") and they stand still.
	if (bWMRefOK) { return; }
	WMRefRetry -= DeltaSeconds;
	if (WMRefRetry > 0.f) { return; }
	WMRefRetry = 1.f;
	const FObjectPropertyBase* Prop = FindFProperty<FObjectPropertyBase>(GetClass(), TEXT("WMRef"));
	if (!Prop || !Prop->PropertyClass) { bWMRefOK = true; return; }   // not a BP_Zombie: nothing to do
	if (IsValid(Prop->GetObjectPropertyValue_InContainer(this))) { bWMRefOK = true; return; }
	if (AActor* WM = UGameplayStatics::GetActorOfClass(this, Prop->PropertyClass))
	{
		Prop->SetObjectPropertyValue_InContainer(this, WM);
		bWMRefOK = true;
		++CDZombieBrain::GWMRefFixed;
		StillSeconds = CDZombieBrain::GUnstickSeconds;   // send it on right away
	}
}

static bool IsCrawlAnimName(const FString& N)
{
	return N.Contains(TEXT("Belly_Crawling")) || N.Contains(TEXT("Laying_Idle"));
}

void AZombieBase::TickNoGiant()
{
	using namespace CDZombieBrain;
	if (!GNoGiant || !bSpawnShapeCached) { return; }
	USkeletalMeshComponent* M = GetMesh();
	if (!M) { return; }
	const bool bGrown = M->GetRelativeScale3D().GetMax() > SpawnMeshScale.GetMax() * 1.4f;
	UAnimInstance* Anim = M->GetAnimInstance();
	UAnimMontage* Current = Anim ? Anim->GetCurrentActiveMontage() : nullptr;
	// Think plays these as dynamic montages wrapped around a sequence: check the montage and its slot segments
	bool bCrawl = Current && IsCrawlAnimName(Current->GetName());
	if (!bCrawl && Current)
	{
		for (const FSlotAnimationTrack& Track : Current->SlotAnimTracks)
		{
			for (const FAnimSegment& Seg : Track.AnimTrack.AnimSegments)
			{
				const UAnimSequenceBase* Seq = Seg.GetAnimReference();
				if (Seq && IsCrawlAnimName(Seq->GetName())) { bCrawl = true; }
			}
		}
	}
	if (!bGrown && !bCrawl) { return; }
	M->SetRelativeScale3D(SpawnMeshScale);
	M->SetRelativeLocation(SpawnMeshLocation);
	if (bCrawl && Anim) { Anim->Montage_Stop(0.2f, Current); }
	if (M->GlobalAnimRateScale < 0.9f) { M->GlobalAnimRateScale = 1.f; }   // otherwise the next Think re-triggers type 5
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		if (SpawnWalkSpeed > 0.f) { Move->MaxWalkSpeed = SpawnWalkSpeed; }
	}
	++GGiantBlocked;
	StillSeconds = GUnstickSeconds;   // get it moving again right away
}

void AZombieBase::TickUnstick(float DeltaSeconds)
{
	using namespace CDZombieBrain;
	if (!GUnstick) { StillSeconds = 0.f; return; }
	UnstickCooldown = FMath::Max(0.f, UnstickCooldown - DeltaSeconds);
	AController* Ctrl = GetController();
	if (!Ctrl || Ctrl->IsPlayerController()) { return; }
	const UAnimInstance* Anim = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	const bool bBusy = ReadBlueprintBool(this, TEXT("Attacking")) || (Anim && Anim->IsAnyMontagePlaying()) || IsEngagedForCrowd();
	const bool bStill = GetVelocity().SizeSquared2D() < FMath::Square(10.f);
	StillSeconds = (bBusy || !bStill) ? 0.f : StillSeconds + DeltaSeconds;
	if (StillSeconds < GUnstickSeconds || UnstickCooldown > 0.f) { return; }

	AActor* Target = GetCurrentTarget();
	if (!Target) { Target = GetOwner(); }
	if (!Target) { Target = UGameplayStatics::GetPlayerCharacter(this, 0); }
	if (!Target || Target == this || GetDistanceTo(Target) < 150.f) { StillSeconds = 0.f; return; }
	UAIBlueprintHelperLibrary::SimpleMoveToActor(Ctrl, Target);
	++GUnstickCount;
	StillSeconds = 0.f;
	UnstickCooldown = 2.f;
}

void AZombieBase::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->UnregisterZombie(this);
	}
	CurrentTarget = nullptr;
	Super::EndPlay(EndPlayReason);
}

bool AZombieBase::ReadBlueprintBool(const UObject* Object, FName Name, bool* bFound)
{
	if (bFound) { *bFound = false; }
	if (!IsValid(Object))
	{
		return false;
	}
	const FBoolProperty* Prop = FindFProperty<FBoolProperty>(Object->GetClass(), Name);
	if (bFound) { *bFound = Prop != nullptr; }
	return Prop && Prop->GetPropertyValue_InContainer(Object);
}

bool AZombieBase::IsDeadForCrowd() const
{
	// Destruction and NotifyDying always win; the Blueprint flag can only add "dead", never hide it.
	return IsActorBeingDestroyed() || !IsValid(this) || bDying || ReadBlueprintBool(this, TEXT("Dead"));
}

void AZombieBase::NotifyDying()
{
	bDying = true;
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->RelinquishBodyCollision(this);
	}
}

bool AZombieBase::IsEngagedForCrowd() const
{
	return !FMath::IsNearlyEqual(CustomTimeDilation, 1.f);
}

float AZombieBase::DistanceToPlayer() const
{
	const AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	// GetDistanceTo(None) is 0 in Blueprint: keep that, so a missing player counts as near.
	return Player ? GetDistanceTo(Player) : 0.f;
}

AZombieBase::FTargetRule::FTargetRule(const FVector& InSelf, const FVector* Player, float SoldierRange, float InSoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks)
	: Self(InSelf)
	, BestDistSq(0.f)
	, SoldierRangeSq(FMath::Square(FMath::Max(0.f, SoldierRange)))       // settings from .ini are not clamped by the editor UI
	, SoldierHeightRange(FMath::Max(0.f, InSoldierHeightRange))
	, FarmerRangeSq(FMath::Square(FMath::Max(0.f, FarmerRange)))
{
	// Blueprint parity: with no player, GetDistanceTo(None) = 0, so nothing is "nearer" and no soldier / farmer is picked.
	// bNoPlayerBlocks = false is the alternative (pick the nearest valid target); TGA's SPEC_zombie.md decides which is intended.
	BestDistSq = Player ? FVector::DistSquared(Self, *Player) : (bNoPlayerBlocks ? 0.f : TNumericLimits<float>::Max());
}

void AZombieBase::FTargetRule::ConsiderSoldier(int32 Index, const FVector& Location, bool bValid, bool bDying)
{
	if (!bValid || bDying || FMath::Abs(Location.Z - Self.Z) >= SoldierHeightRange)
	{
		return;
	}
	const float DistSq = FVector::DistSquared(Self, Location);
	if (DistSq < SoldierRangeSq && DistSq < BestDistSq)
	{
		Best = Index;
		BestDistSq = DistSq;
	}
}

void AZombieBase::FTargetRule::ConsiderFarmer(int32 Index, const FVector& Location, bool bValid, bool bDead)
{
	if (!bValid || bDead)
	{
		return;
	}
	const float DistSq = FVector::DistSquared(Self, Location);
	if (DistSq < FarmerRangeSq && DistSq < BestDistSq)
	{
		Best = Index;
		BestDistSq = DistSq;
	}
}

int32 AZombieBase::ChooseTarget(const FVector& Self, const FVector* Player, const TArray<FCandidate>& Soldiers, const TArray<FCandidate>& Farmers,
	float SoldierRange, float SoldierHeightRange, float FarmerRange, bool bNoPlayerBlocks)
{
	FTargetRule Rule(Self, Player, SoldierRange, SoldierHeightRange, FarmerRange, bNoPlayerBlocks);
	for (int32 i = 0; i < Soldiers.Num(); ++i)
	{
		Rule.ConsiderSoldier(i, Soldiers[i].Location, Soldiers[i].bValid, Soldiers[i].bDyingOrDead);
	}
	for (int32 i = 0; i < Farmers.Num(); ++i)
	{
		Rule.ConsiderFarmer(Soldiers.Num() + i, Farmers[i].Location, Farmers[i].bValid, Farmers[i].bDyingOrDead);
	}
	return Rule.Best;
}

AActor* AZombieBase::FinishPick(AActor* Player, AActor* Picked)
{
	AActor* Best = Picked ? Picked : Player;
	CurrentTarget = Best;
	if (bAlsoSetOwner)
	{
		SetOwner(Best);
	}
	return Best;
}

// "Dying" for a soldier = a life span is set (Blueprint parity: GetLifeSpan < 0.01 means alive). Replace with an explicit state with ASoldierBase.
static bool IsSoldierDying(const AActor* Soldier) { return Soldier->GetLifeSpan() >= 0.01f; }

AActor* AZombieBase::PickAndSetTarget(const TArray<AActor*>& Soldiers, const TArray<AActor*>& Farmers)
{
	CD_SCOPE(STAT_CD_PickTarget);
	const UCDSettings* S = GetDefault<UCDSettings>();
	AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const FVector PlayerLoc = Player ? Player->GetActorLocation() : FVector::ZeroVector;
	FTargetRule Rule(GetActorLocation(), Player ? &PlayerLoc : nullptr, S->ZombieSoldierRange, S->ZombieSoldierHeightRange, S->ZombieFarmerRange, S->bZombieNoPlayerBlocksTargets);
	for (int32 i = 0; i < Soldiers.Num(); ++i)
	{
		const AActor* A = Soldiers[i];
		if (IsValid(A)) { Rule.ConsiderSoldier(i, A->GetActorLocation(), true, IsSoldierDying(A)); }
	}
	for (int32 i = 0; i < Farmers.Num(); ++i)
	{
		const AActor* A = Farmers[i];
		if (IsValid(A)) { Rule.ConsiderFarmer(Soldiers.Num() + i, A->GetActorLocation(), true, ReadBlueprintBool(A, TEXT("Dead"))); }
	}
	AActor* Picked = Rule.Best == INDEX_NONE ? nullptr : (Rule.Best < Soldiers.Num() ? Soldiers[Rule.Best] : Farmers[Rule.Best - Soldiers.Num()]);
	return FinishPick(Player, Picked);
}

AActor* AZombieBase::PickAndSetTargetFromRegistry()
{
	CD_SCOPE(STAT_CD_PickTarget);
	const UCDSettings* S = GetDefault<UCDSettings>();
	AActor* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this);
	if (!Crowd)
	{
		return FinishPick(Player, nullptr);
	}
	const FVector PlayerLoc = Player ? Player->GetActorLocation() : FVector::ZeroVector;
	FTargetRule Rule(GetActorLocation(), Player ? &PlayerLoc : nullptr, S->ZombieSoldierRange, S->ZombieSoldierHeightRange, S->ZombieFarmerRange, S->bZombieNoPlayerBlocksTargets);
	AActor* Picked = nullptr;
	int32 Index = 0;
	// rev 3 (review P1-4): NOT used by BP_Zombie today (no call in the 11-05 graph dump). Registry order = registration order,
	// which is not proven equal to the Blueprint's array order, so ties (equal distance) could pick differently: stage 2 must use
	// PickAndSetTarget(arrays) for parity, or approve a tie rule. Garbage (pending-kill) actors are skipped, as IsValid does.
	Crowd->ForEachSoldier([&](AActor* A)
	{
		const int32 Before = Rule.Best;
		// rev 4 (review 2 P0): validity is decided BEFORE anything is read from the actor. An invalid entry still takes its index
		// and still goes through ConsiderSoldier with bValid = false (which rejects it), so the index rules stay exactly as before.
		const bool bValid = IsValid(A);
		Rule.ConsiderSoldier(Index++, bValid ? A->GetActorLocation() : FVector::ZeroVector, bValid, bValid && IsSoldierDying(A));
		if (bValid && Rule.Best != Before) { Picked = A; }
	});
	Crowd->ForEachFarmer([&](AActor* A)
	{
		const int32 Before = Rule.Best;
		const bool bValid = IsValid(A);   // rev 4: same order fix as soldiers
		Rule.ConsiderFarmer(Index++, bValid ? A->GetActorLocation() : FVector::ZeroVector, bValid, bValid && ReadBlueprintBool(A, TEXT("Dead")));
		if (bValid && Rule.Best != Before) { Picked = A; }
	});
	return FinishPick(Player, Picked);
}

int32 AZombieBase::GetThinkDivisor() const
{
	const UCDSettings* S = GetDefault<UCDSettings>();
	const float Dist = DistanceToPlayer();
	return Dist < S->ZombieNearPlayer ? 1 : (Dist < S->ZombieMidPlayer ? 2 : 4);
}

bool AZombieBase::IsFullDetail() const
{
	return DistanceToPlayer() < GetDefault<UCDSettings>()->ZombieNearPlayer || WasRecentlyRendered(0.2f);
}

float AZombieBase::TakeDamage(float Damage, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	Damage *= UCDWeaponPerks::StaggerBonus(DamageCauser, this);   // 11-06 weapons: Flanged Mace crushes colossi (1 for everything else)
	const float Applied = Super::TakeDamage(Damage, DamageEvent, EventInstigator, DamageCauser);
	if (Applied > 0.f && DamageCauser && DamageCauser == UGameplayStatics::GetPlayerPawn(this, 0)) { UCDCombatRules::HeroHitStop(DamageCauser, Applied); }
	if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
	{
		LastHitPoint = static_cast<const FPointDamageEvent&>(DamageEvent).HitInfo.ImpactPoint;
	}
	else if (DamageEvent.IsOfType(FRadialDamageEvent::ClassID))
	{
		LastHitPoint = static_cast<const FRadialDamageEvent&>(DamageEvent).Origin;
	}
	else
	{
		// generic ApplyDamage (the hero's sword, soldiers): the closest point of our capsule to the causer, at the blade's height
		AActor* From = DamageCauser ? DamageCauser : (EventInstigator ? EventInstigator->GetPawn() : nullptr);
		const FVector Src = From ? From->GetActorLocation() : GetActorLocation() + GetActorForwardVector() * 60.f;
		FVector Closest = GetActorLocation();
		if (UCapsuleComponent* Cap = GetCapsuleComponent()) { Cap->GetClosestPointOnCollision(Src, Closest); }
		const float Half = GetSimpleCollisionHalfHeight();
		Closest.Z = FMath::Clamp(Src.Z + 40.f, GetActorLocation().Z - Half * 0.3f, GetActorLocation().Z + Half * 0.9f);
		LastHitPoint = Closest;
	}
	if (LastHitPoint.ContainsNaN() || LastHitPoint.IsNearlyZero()) { LastHitPoint = GetActorLocation() + FVector(0, 0, 30.f); }
	// where the damage came from, in our own space (for the directional flinch): a shot's travel direction reversed when the
	// event carries one, otherwise the causer / instigator position, otherwise the recorded hit point itself
	{
		FVector From = FVector::ZeroVector;
		if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
		{
			const FVector Shot = static_cast<const FPointDamageEvent&>(DamageEvent).ShotDirection;
			if (!Shot.IsNearlyZero()) { From = -Shot; }
		}
		if (From.IsNearlyZero())
		{
			AActor* Src = DamageCauser ? DamageCauser : (EventInstigator ? EventInstigator->GetPawn() : nullptr);
			if (Src && Src != this) { From = Src->GetActorLocation() - GetActorLocation(); }
			else { From = LastHitPoint - GetActorLocation(); }
		}
		From.Z = 0.f;
		if (From.IsNearlyZero(1.f)) { From = GetActorForwardVector(); }
		LastHitLocal = GetActorTransform().InverseTransformVectorNoScale(From.GetSafeNormal2D());
		LastHitLocal.Z = 0.f;
	}
	LastHitDamage = Applied;
	LastHitCauser = DamageCauser ? DamageCauser : (EventInstigator ? EventInstigator->GetPawn() : nullptr);
	LastHitTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	return Applied;
}

UAnimMontage* AZombieBase::PickFlinchMontage(UAnimMontage* Default) const
{
	auto Pick = [](const TArray<TObjectPtr<UAnimMontage>>& Set) -> UAnimMontage* { return Set.Num() ? Set[FMath::RandRange(0, Set.Num() - 1)].Get() : nullptr; };
	UAnimMontage* M = nullptr;
	if (LastHitTime >= 0.0)
	{
		bool bHeavy = LastHitDamage >= HeavyDamage;
		if (!bHeavy) { if (const AActor* C = LastHitCauser.Get()) { const FString N = C->GetClass()->GetName(); for (const FString& W : HeavyCauserWords) { if (!W.IsEmpty() && N.Contains(W)) { bHeavy = true; break; } } } }
		if (bHeavy) { M = Pick(HitHeavy); }
		if (!M && UCDWeaponPerks::ForceStagger(LastHitCauser.Get())) { M = Pick(HitStagger); }   // 11-06 weapons: Bone Breaker staggers every hit
		if (!M)
		{
			float Threshold = StaggerDamage;
			if (const FFloatProperty* P = FindFProperty<FFloatProperty>(GetClass(), TEXT("MaxHP"))) { Threshold = StaggerFraction * P->GetPropertyValue_InContainer(this); }
			else if (const FDoubleProperty* D = FindFProperty<FDoubleProperty>(GetClass(), TEXT("MaxHP"))) { Threshold = StaggerFraction * static_cast<float>(D->GetPropertyValue_InContainer(this)); }
			if (Threshold > 0.f && LastHitDamage >= Threshold) { M = Pick(HitStagger); }
		}
		if (!M)
		{
			switch (GetLastHitSide())
			{
			case ECDHitSide::Back:  M = Pick(FlinchBack); break;
			case ECDHitSide::Left:  M = Pick(FlinchLeft); break;
			case ECDHitSide::Right: M = Pick(FlinchRight); break;
			default: break;
			}
		}
	}
	if (!M) { M = Pick(FlinchFront); }
	return M ? M : Default;
}

ECDHitSide AZombieBase::GetLastHitSide() const
{
	if (LastHitTime < 0.0) { return ECDHitSide::Front; }
	if (FMath::Abs(LastHitLocal.X) >= FMath::Abs(LastHitLocal.Y)) { return LastHitLocal.X >= 0.f ? ECDHitSide::Front : ECDHitSide::Back; }
	return LastHitLocal.Y >= 0.f ? ECDHitSide::Right : ECDHitSide::Left;
}

float AZombieBase::GetLastHitAge() const
{
	if (LastHitTime < 0.0 || !GetWorld()) { return -1.f; }
	return static_cast<float>(GetWorld()->GetTimeSeconds() - LastHitTime);
}

FVector AZombieBase::GetLastHitPoint() const
{
	return LastHitTime >= 0.0 ? LastHitPoint : GetActorLocation() + FVector(0, 0, 30.f);
}

// 11-06 half-body zombies: BP_JellyBlob / BP_PodMelt spawn BP_Zombie at blob + 95 cm and then SetActorScale3D by the blob size.
// With scale > 1 the capsule half height grows past 95 cm, the feet sit under the landscape and walking never lifts them out.
// For the first seconds after spawn, and again whenever the actor scale changes, trace down from the capsule centre and raise
// the actor so the capsule bottom rests on the floor. One cheap trace every 0.25 s inside the window; nothing afterwards.
void AZombieBase::TickGroundSnap(float DeltaSeconds)
{
	static bool GEnable = true;
	static FAutoConsoleVariableRef CVar(TEXT("cd.Zombie.GroundSnap"), GEnable, TEXT("1 = lift zombies whose capsule bottom is below the floor after spawn / rescale (blob spawns). 0 = off."));
	if (!GEnable) { return; }
	const FVector Scale = GetActorScale3D();
	if (!Scale.Equals(GroundSnapScale, 0.01f)) { GroundSnapScale = Scale; GroundSnapWindow = 3.f; GroundSnapTimer = 0.f; }
	if (GroundSnapWindow <= 0.f) { return; }
	GroundSnapWindow -= DeltaSeconds;
	GroundSnapTimer -= DeltaSeconds;
	if (GroundSnapTimer > 0.f) { return; }
	GroundSnapTimer = 0.25f;
	UCapsuleComponent* Cap = GetCapsuleComponent(); UWorld* W = GetWorld();
	if (!Cap || !W) { return; }
	const float Half = Cap->GetScaledCapsuleHalfHeight();
	const FVector Center = GetActorLocation();
	const float Bottom = Center.Z - Half;
	FHitResult Hit; FCollisionQueryParams Q(SCENE_QUERY_STAT(ZombieGroundSnap), false, this);
	Q.AddIgnoredActor(this);
	// 11-06 b: BP_ZombieJellyShield (attached to the zombie) rescales it every tick while the BP_JellyBlob under it grows too.
	// The old trace hit the rising blob top and "lifted" the zombie onto it every tick (lift 35 -> 92 cm in the log), then it fell back.
	// Ignore everything attached to us and every blob-family actor around us: only real ground counts.
	TArray<AActor*> Attached; GetAttachedActors(Attached, true, true);
	for (AActor* A : Attached) { if (A) { Q.AddIgnoredActor(A); } }
	if (AActor* Parent = GetAttachParentActor()) { Q.AddIgnoredActor(Parent); }
	{
		TArray<FOverlapResult> Near; FCollisionShape Sph = FCollisionShape::MakeSphere(Half * 2.f + 150.f);
		FCollisionQueryParams OQ(SCENE_QUERY_STAT(ZombieGroundSnapOverlap), false, this);
		if (W->OverlapMultiByChannel(Near, Center, FQuat::Identity, ECC_WorldStatic, Sph, OQ))
		{
			for (const FOverlapResult& O : Near)
			{
				AActor* A = O.GetActor(); if (!A) { continue; }
				const FString N = A->GetClass()->GetName();
				if (N.Contains(TEXT("JellyBlob")) || N.Contains(TEXT("PodMelt")) || N.Contains(TEXT("BlobDrip")) || N.Contains(TEXT("JellyShield")) || N.Contains(TEXT("Zombie"))) { Q.AddIgnoredActor(A); }
			}
		}
	}
	// from above the head down to well below the feet: the first blocking surface under the capsule centre
	if (!W->LineTraceSingleByChannel(Hit, Center + FVector(0, 0, Half), Center - FVector(0, 0, Half * 3.f + 200.f), ECC_WorldStatic, Q)) { return; }
	const float Floor = Hit.ImpactPoint.Z;
	if (Floor > Bottom + 3.f && Floor < Center.Z + Half)   // feet below the floor, and the floor is not above the head (a roof / bridge)
	{
		const float Lift = Floor - Bottom + 2.f;
		SetActorLocation(Center + FVector(0, 0, Lift), false, nullptr, ETeleportType::TeleportPhysics);
		UE_LOG(LogTemp, Display, TEXT("[CD] ground snap: %s lifted %.0f cm (scale %.2f, half %.0f) onto %s"), *GetName(), Lift, Scale.X, Half, Hit.GetActor() ? *Hit.GetActor()->GetName() : TEXT("?"));
	}
}
