// SoldierBase.cpp - soldier brain stage 1. rev 3 (2026-11-06, gameplay code review):
//   P1-1 slot reservation is a NEW rule, so it is off by default (cd.Soldier.SlotReservation 0 = exact Blueprint rule);
//        Tmp.Y follows the Blueprint loop exactly (For Each without early exit: the last slot's "taken" flag; untouched
//        when there are no slots).
//   P1-2 the contract is split: property metadata cached per class AND reflection epoch; component pointers checked on
//        every instance (one bad soldier no longer decides for the class, one good one no longer vouches for the rest).
//   P1-3 the target component is validated BEFORE a slot is picked or reserved; nothing is reserved if it is missing.
#include "SoldierBase.h"
#include "CDStats.h"
#include "CDSettings.h"
#include "CDWaspDirector.h"
#include "CrowdSubsystem.h"
#include "RealmWaspBase.h"
#include "Animation/AnimMontage.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "GameFramework/DamageType.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

DECLARE_CYCLE_STAT(TEXT("Soldier ReleaseHeldZombies"), STAT_CD_SoldierRelease, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Soldier PickFreeSlot"), STAT_CD_SoldierSlot, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Soldier PruneNearZombies"), STAT_CD_SoldierPrune, STATGROUP_CastleDefender);

namespace CDSoldierBrain
{
	struct FPathStats { int64 Calls = 0; uint64 Cycles = 0; };
	static FPathStats GRelease, GSlot, GPrune;
	static const FName SB_Order(TEXT("Order"));
	static const FName SB_Goal(TEXT("Goal"));
	static const FName SB_State(TEXT("State"));
	static const FName SB_Attacking(TEXT("Attacking"));
	static const FName SB_ResumeMove(TEXT("ResumeMove"));
	static const FName SB_NearZombies(TEXT("NearZombies"));

	static double MicrosOf(const FPathStats& S)
	{
		return S.Calls ? FPlatformTime::ToMilliseconds64(S.Cycles) * 1000.0 / double(S.Calls) : 0.0;
	}
	static FAutoConsoleCommand CmdReport(TEXT("cd.Soldier.Report"), TEXT("Native soldier brain: calls and average microseconds per call."),
		FConsoleCommandDelegate::CreateLambda([]()
		{
			UE_LOG(LogTemp, Display, TEXT("cd.Soldier: ReleaseHeldZombies %lld calls, %.2f us avg | PickFreeSlot %lld calls, %.2f us avg | PruneNearZombies %lld calls, %.2f us avg"),
				GRelease.Calls, MicrosOf(GRelease), GSlot.Calls, MicrosOf(GSlot), GPrune.Calls, MicrosOf(GPrune));
		}));

	struct FScopedPathTimer
	{
		FPathStats& S; uint32 Start;
		explicit FScopedPathTimer(FPathStats& In) : S(In), Start(FPlatformTime::Cycles()) {}
		~FScopedPathTimer() { ++S.Calls; S.Cycles += FPlatformTime::Cycles() - Start; }
	};

	// Blueprint compares order codes as |Order.X - code| < 0.5
	static bool HasOrder(const USceneComponent* C, int32 Code) { return C && FMath::Abs(C->GetRelativeLocation().X - float(Code)) < 0.5f; }

	// Slot reservations: (order code, slot index, quantised slot XY) -> who and when. Game thread only.
	struct FReservation { TWeakObjectPtr<const AActor> Owner; double Time = 0.0; };
	static TMap<FString, FReservation> GReservations;
	static TWeakObjectPtr<UWorld> GReservationWorld;
	static FString SlotKey(int32 Code, const FVector& P) { return FString::Printf(TEXT("%d:%d:%d"), Code, FMath::RoundToInt(P.X), FMath::RoundToInt(P.Y)); }

	static int32 GPruneNearZombies = 1;
	static FAutoConsoleVariableRef CVarPrune(TEXT("cd.Soldier.PruneNearZombies"), GPruneNearZombies,
		TEXT("1 = drop destroyed zombies from BPC_NearZombies.NearZombies before the soldier's combat loop reads it (default). 0 = off."));

	// P1-1: reservation is opt-in; 0 (default) = the Blueprint's own "taken" rule only (behaviour 1:1).
	static int32 GSlotReservation = 0;
	static FAutoConsoleVariableRef CVarReserve(TEXT("cd.Soldier.SlotReservation"), GSlotReservation,
		TEXT("1 = a picked formation slot is reserved for 2 s so two soldiers deciding in the same frame cannot take it (gameplay change). 0 = Blueprint rule (default)."));

	// P1-2: class-level metadata only (do the Order / Goal / State properties exist with a scene-component type?),
	// cached per class and reflection epoch (a Blueprint recompile can rebuild the properties). Instance pointers: per instance.
	static uint32 GEpoch = 1;
	static uint32 Epoch()
	{
		static bool bHooked = false;
		if (!bHooked)
		{
			bHooked = true;
#if WITH_EDITOR
			FCoreUObjectDelegates::OnObjectsReinstanced.AddLambda([](const TMap<UObject*, UObject*>&) { ++GEpoch; });
#endif
		}
		return GEpoch;
	}
	struct FClassContract { uint32 Epoch = 0; bool bOK = false; };
	static TMap<TWeakObjectPtr<const UClass>, FClassContract> GContract;
	// Zombie-side members needed by ReleaseHeldZombies, validated once per zombie class.
	static TMap<TWeakObjectPtr<const UClass>, bool> GZombieContract;

	static bool ZombieContractOK(const UClass* Cls)
	{
		if (const bool* Known = GZombieContract.Find(Cls)) { return *Known; }
		const FBoolProperty* Attacking = FindFProperty<FBoolProperty>(Cls, SB_Attacking);
		const UFunction* Resume = Cls->FindFunctionByName(SB_ResumeMove);
		const bool bOK = Attacking && Resume && Resume->NumParms == 0;
		if (!bOK)
		{
			UE_LOG(LogTemp, Error, TEXT("cd.Soldier: zombie class %s is missing %s%s%s - ReleaseHeldZombies skips it (Blueprint loop would also fail)."),
				*Cls->GetName(), Attacking ? TEXT("") : TEXT("bool Attacking "), Resume ? TEXT("") : TEXT("function ResumeMove "),
				(Resume && Resume->NumParms != 0) ? TEXT("(ResumeMove has parameters) ") : TEXT(""));
		}
		GZombieContract.Add(Cls, bOK);
		return bOK;
	}
}

ASoldierBase::ASoldierBase()
{
	PrimaryActorTick.bCanEverTick = true;   // the Blueprint's Event Tick still runs (it sets its own tick interval)
}

void ASoldierBase::BeginPlay()
{
	Super::BeginPlay();   // Blueprint BeginPlay runs first, unchanged
	bContractOK = ValidateBlueprintContract();
	// Registration: the soldier Blueprint never calls RegisterSoldier (0 calls in the 11-05 dump); RegisterSoldier is
	// AddUnique, so a later Blueprint call would be harmless. Only lifecycle difference: soldiers now appear in
	// UCrowdSubsystem::GetSoldiers(), which zombies already read when present.
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this)) { Crowd->RegisterSoldier(this); }
}

void ASoldierBase::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this)) { Crowd->UnregisterSoldier(this); }
	Super::EndPlay(EndPlayReason);
}

bool ASoldierBase::ValidateBlueprintContract() const
{
	using namespace CDSoldierBrain;
	const UClass* Cls = GetClass();
	// 1. class metadata (cached per class + epoch)
	FClassContract& CC = GContract.FindOrAdd(Cls);
	if (CC.Epoch != Epoch())
	{
		CC.Epoch = Epoch();
		FString Missing;
		for (const FName& N : { SB_Order, SB_Goal, SB_State })
		{
			const FObjectPropertyBase* P = FindFProperty<FObjectPropertyBase>(Cls, N);
			if (!P) { Missing += N.ToString() + TEXT("(no property) "); continue; }
			if (!P->PropertyClass || !P->PropertyClass->IsChildOf(USceneComponent::StaticClass())) { Missing += N.ToString() + TEXT("(not a scene component) "); }
		}
		CC.bOK = Missing.IsEmpty();
		if (!CC.bOK) { UE_LOG(LogTemp, Error, TEXT("cd.Soldier: class %s breaks the soldier contract: %s- native slot picking disabled for this class."), *Cls->GetName(), *Missing); }
	}
	if (!CC.bOK) { return false; }
	// 2. this instance's component pointers (never cached across instances)
	FString Null;
	for (const FName& N : { SB_Order, SB_Goal, SB_State }) { if (!GetSlotComponent(N)) { Null += N.ToString() + TEXT(" "); } }
	if (!Null.IsEmpty()) { UE_LOG(LogTemp, Error, TEXT("cd.Soldier: %s has null %s- native slot picking disabled for this soldier."), *GetName(), *Null); return false; }
	return true;
}

USceneComponent* ASoldierBase::GetSlotComponentOf(const AActor* Actor, FName VarName)
{
	if (!IsValid(Actor)) { return nullptr; }
	const FObjectPropertyBase* Prop = FindFProperty<FObjectPropertyBase>(Actor->GetClass(), VarName);
	return Prop ? Cast<USceneComponent>(Prop->GetObjectPropertyValue_InContainer(Actor)) : nullptr;
}

USceneComponent* ASoldierBase::GetSlotComponent(FName VarName) const { return GetSlotComponentOf(this, VarName); }

int32 ASoldierBase::GetOrderCode() const
{
	const USceneComponent* C = GetSlotComponent(CDSoldierBrain::SB_Order);
	return C ? FMath::RoundToInt(C->GetRelativeLocation().X) : -1;
}

bool ASoldierBase::IsSoldierDead() const
{
	const USceneComponent* State = GetSlotComponent(CDSoldierBrain::SB_State);
	return (State && State->GetRelativeLocation().Z < 0.5f) || GetLifeSpan() > 0.01f;
}

int32 ASoldierBase::ReleaseHeldZombies(const TArray<AActor*>& Registry, float Radius, float NormalDilation)
{
	using namespace CDSoldierBrain;
	SCOPE_CYCLE_COUNTER(STAT_CD_SoldierRelease);
	FScopedPathTimer Timer(CDSoldierBrain::GRelease);
	if (Radius <= 0.f) { return 0; }
	const FVector Me = GetActorLocation();
	const float RSq = FMath::Square(Radius);
	int32 Released = 0;
	// same array, same order as the Blueprint's ForEach (the loop body only touches the zombie it tests, so order
	// does not change the result, but it is kept anyway)
	for (AActor* Z : Registry)
	{
		if (!IsValid(Z)) { continue; }
		if (FMath::Abs(Z->CustomTimeDilation - 0.999f) >= 0.0004f) { continue; }
		if (FVector::DistSquared(Z->GetActorLocation(), Me) >= RSq) { continue; }   // Blueprint: GetDistanceTo (3D) < 400
		if (!ZombieContractOK(Z->GetClass())) { continue; }
		Z->CustomTimeDilation = NormalDilation;
		FindFProperty<FBoolProperty>(Z->GetClass(), SB_Attacking)->SetPropertyValue_InContainer(Z, false);
		Z->ProcessEvent(Z->GetClass()->FindFunctionByName(SB_ResumeMove), nullptr);   // validated: no parameters
		++Released;
	}
	return Released;
}

int32 ASoldierBase::PruneNearZombies()
{
	using namespace CDSoldierBrain;
	SCOPE_CYCLE_COUNTER(STAT_CD_SoldierPrune);
	FScopedPathTimer Timer(GPrune);
	if (!GPruneNearZombies) { return 0; }
	UActorComponent* Comp = NearZombiesComp.Get();
	if (!Comp)
	{
		TInlineComponentArray<UActorComponent*> Comps; GetComponents(Comps);
		for (UActorComponent* C : Comps) { if (C && C->GetClass()->GetName().StartsWith(TEXT("BPC_NearZombies"))) { Comp = C; break; } }
		NearZombiesComp = Comp;
	}
	static TSet<FName> Reported;
	if (!Comp)
	{
		if (!Reported.Contains(GetClass()->GetFName())) { Reported.Add(GetClass()->GetFName()); UE_LOG(LogTemp, Error, TEXT("cd.Soldier: %s has no BPC_NearZombies component: PruneNearZombies does nothing"), *GetClass()->GetName()); }
		return 0;
	}
	const FArrayProperty* Arr = FindFProperty<FArrayProperty>(Comp->GetClass(), SB_NearZombies);
	const FObjectProperty* Inner = Arr ? CastField<FObjectProperty>(Arr->Inner) : nullptr;
	if (!Inner)
	{
		if (!Reported.Contains(Comp->GetClass()->GetFName())) { Reported.Add(Comp->GetClass()->GetFName()); UE_LOG(LogTemp, Error, TEXT("cd.Soldier: %s has no object-array variable NearZombies: PruneNearZombies does nothing"), *Comp->GetClass()->GetName()); }
		return 0;
	}
	FScriptArrayHelper Items(Arr, Arr->ContainerPtrToValuePtr<void>(Comp));
	int32 Removed = 0;
	for (int32 i = Items.Num() - 1; i >= 0; --i)   // O(n) over the list, n = zombies within 12 m; same order kept for the survivors
	{
		const AActor* A = Cast<AActor>(Inner->GetObjectPropertyValue(Items.GetRawPtr(i)));
		if (!IsValid(A) || A->IsActorBeingDestroyed()) { Items.RemoveValues(i, 1); ++Removed; }
	}
	return Removed;
}

// ---------------------------------------------------------------- anti-air (11-06 wasps)

namespace CDSoldierAA
{
	static int32 GEnable = 1;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.Soldier.AntiAir"), GEnable, TEXT("1 = crossbow soldiers shoot wasps (default). 0 = off."));
	static const FName NAME_Xbow(TEXT("Xbow"));
	static TWeakObjectPtr<UClass> BoltClass; static bool bBoltTried = false;
	static TWeakObjectPtr<UAnimMontage> AimMontage; static bool bAimTried = false;
	static TWeakObjectPtr<USoundBase> FireSound; static bool bSoundTried = false;
	static const TCHAR* BoltPath = TEXT("/Game/CastleDefender/Characters/Knight/BP_SoldierBolt.BP_SoldierBolt_C");
	static const TCHAR* AimPath = TEXT("/Game/CastleDefender/Gameplay/Crossbow/Anims/AM_Xbow_Aim.AM_Xbow_Aim");
	static const TCHAR* SoundPath = TEXT("/Game/CastleDefender/Gameplay/Crossbow/Audio/SFX_XbowFire.SFX_XbowFire");

	template <typename T> T* Once(TWeakObjectPtr<T>& Slot, bool& bTried, const TCHAR* Path)
	{
		if (T* P = Slot.Get()) { return P; }
		if (bTried) { return nullptr; }
		bTried = true;
		T* L = LoadObject<T>(nullptr, Path);
		Slot = L;
		if (!L) { UE_LOG(LogTemp, Warning, TEXT("cd.Soldier.AntiAir: %s not found, effect skipped"), Path); }
		return L;
	}
	static UClass* BoltOnce()
	{
		if (UClass* C = BoltClass.Get()) { return C; }
		if (bBoltTried) { return nullptr; }
		bBoltTried = true;
		UClass* L = StaticLoadClass(AActor::StaticClass(), nullptr, BoltPath);
		BoltClass = L;
		if (!L) { UE_LOG(LogTemp, Warning, TEXT("cd.Soldier.AntiAir: %s not found, bolts are invisible"), BoltPath); }
		return L;
	}
}

void ASoldierBase::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);   // the Blueprint's Event Tick, unchanged
	if (CDSoldierAA::GEnable) { TickAntiAir(DeltaSeconds); }
}

int32 ASoldierBase::GetNearZombieCount()
{
	using namespace CDSoldierBrain;
	UActorComponent* Comp = NearZombiesComp.Get();
	if (!Comp)
	{
		TInlineComponentArray<UActorComponent*> Comps; GetComponents(Comps);
		for (UActorComponent* C : Comps) { if (C && C->GetClass()->GetName().StartsWith(TEXT("BPC_NearZombies"))) { Comp = C; break; } }
		NearZombiesComp = Comp;
		if (!Comp) { return 0; }
	}
	const FArrayProperty* Arr = FindFProperty<FArrayProperty>(Comp->GetClass(), SB_NearZombies);
	if (!Arr) { return 0; }
	FScriptArrayHelper Items(Arr, Arr->ContainerPtrToValuePtr<void>(Comp));
	return Items.Num();
}

void ASoldierBase::TickAntiAir(float DeltaSeconds)
{
	AAXbowRecheck -= DeltaSeconds;
	if (AAXbowRecheck <= 0.f) { AAXbowRecheck = 2.f; bIsXbow = ActorHasTag(CDSoldierAA::NAME_Xbow); }
	if (!bIsXbow || IsSoldierDead()) { bAAAiming = false; return; }
	UCDWaspDirector* Dir = UCDWaspDirector::Get(this);
	if (!Dir || Dir->GetAliveWaspCount() == 0) { bAAAiming = false; return; }
	const UCDSettings* S = GetDefault<UCDSettings>();
	AACooldown -= DeltaSeconds;
	if (AACooldown > 0.f) { return; }
	const FVector Eye = GetActorLocation() + FVector(0.f, 0.f, 45.f);   // where the Blueprint spawns its bolt

	if (!bAAAiming)
	{
		// ground zombies first, unless a wasp is on him
		if (GetNearZombieCount() > 0 && !Dir->IsWaspThreatening(this, S->SoldierAASelfDefenceRange)) { AACooldown = 0.3f; return; }
		ARealmWaspBase* W = Dir->FindAntiAirTarget(this, Eye, S->SoldierAARange, true);
		if (!W) { AACooldown = 0.25f; return; }
		AATarget = W;
		bAAAiming = true;
		AAAimTimer = 0.f;
		W->NotifyAimedAt(this);
		if (UAnimMontage* M = CDSoldierAA::Once(CDSoldierAA::AimMontage, CDSoldierAA::bAimTried, CDSoldierAA::AimPath)) { PlayAnimMontage(M, 1.f); }
		return;
	}

	ARealmWaspBase* W = AATarget.Get();
	if (!W || W->IsWaspDead() || FVector::Dist(Eye, W->GetActorLocation()) > S->SoldierAARange * 1.25f) { bAAAiming = false; AACooldown = 0.2f; return; }
	// turn to face it (yaw only: the aim montage carries the elevation)
	const FRotator Want = (W->GetActorLocation() - Eye).Rotation();
	const FRotator Cur = GetActorRotation();
	SetActorRotation(FRotator(Cur.Pitch, FMath::FixedTurn(Cur.Yaw, Want.Yaw, 540.f * DeltaSeconds), Cur.Roll));
	AAAimTimer += DeltaSeconds;
	if (AAAimTimer >= S->SoldierAAAimTime)
	{
		FireAntiAir(W);
		bAAAiming = false;
		AACooldown = S->SoldierAAReload * FMath::FRandRange(0.9f, 1.15f);
	}
}

void ASoldierBase::FireAntiAir(ARealmWaspBase* W)
{
	UWorld* World = GetWorld();
	if (!World || !W) { return; }
	const UCDSettings* S = GetDefault<UCDSettings>();
	UCDWaspDirector* Dir = UCDWaspDirector::Get(this);
	const FVector From = GetActorLocation() + FVector(0.f, 0.f, 45.f);
	const FVector TL = W->GetActorLocation();
	const float Travel = FMath::Max(FVector::Dist(From, TL) / FMath::Max(S->SoldierAABoltSpeed, 100.f), 0.05f);
	const FVector Aim = ARealmWaspBase::LeadPoint(TL, W->GetVelocity(), From, S->SoldierAABoltSpeed, 0.5f);

	// the bolt the player sees (the graph's own rule: it lives exactly as long as the flight to the target)
	if (UClass* BC = CDSoldierAA::BoltOnce())
	{
		FActorSpawnParameters P; P.Owner = this; P.Instigator = this; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (AActor* B = World->SpawnActor<AActor>(BC, FTransform((Aim - From).Rotation(), From), P)) { B->SetLifeSpan(Travel); }
	}
	if (USoundBase* Snd = CDSoldierAA::Once(CDSoldierAA::FireSound, CDSoldierAA::bSoundTried, CDSoldierAA::SoundPath)) { UGameplayStatics::PlaySoundAtLocation(this, Snd, From, 0.7f); }
	if (Dir) { ++Dir->SoldierShots; }

	// the shot lands when the bolt would: decided now from the wasp's state at the moment of firing
	const bool bHit = FMath::FRand() < W->GetHitChanceFor(this);
	const float Dmg = S->SoldierAADamage;
	TWeakObjectPtr<ARealmWaspBase> Wasp = W;
	TWeakObjectPtr<ASoldierBase> Me = this;
	FTimerHandle H;
	World->GetTimerManager().SetTimer(H, FTimerDelegate::CreateLambda([Wasp, Me, bHit, Dmg]()
	{
		ARealmWaspBase* T = Wasp.Get();
		if (!T || T->IsWaspDead() || !bHit) { return; }
		ASoldierBase* Sh = Me.Get();
		UGameplayStatics::ApplyDamage(T, Dmg, Sh ? Sh->GetController() : nullptr, Sh, UDamageType::StaticClass());
		if (UCDWaspDirector* D = UCDWaspDirector::Get(T)) { ++D->SoldierHits; }
	}), Travel, false);
}

int32 ASoldierBase::PickFreeSlot(const TArray<FVector>& Slots, int32 OrderCode, float SlotRadius, float ReservationSeconds)
{
	SCOPE_CYCLE_COUNTER(STAT_CD_SoldierSlot);
	CDSoldierBrain::FScopedPathTimer Timer(CDSoldierBrain::GSlot);
	return FindFreeSlot(Slots, CDSoldierBrain::SB_Goal, SlotRadius, OrderCode, false, ReservationSeconds, nullptr);
}

bool ASoldierBase::AssignFreeSlot(const TArray<FVector>& Slots, FName TargetVar, float SlotRadius, int32 OrderCode, bool bMatchXbowTag, bool bWriteTmpY)
{
	using namespace CDSoldierBrain;
	SCOPE_CYCLE_COUNTER(STAT_CD_SoldierSlot);
	FScopedPathTimer Timer(CDSoldierBrain::GSlot);
	// P1-3: validate the target before anything is picked or reserved
	USceneComponent* Target = GetSlotComponent(TargetVar);
	if (!Target) { UE_LOG(LogTemp, Error, TEXT("cd.Soldier: %s has no %s component - slot not assigned."), *GetName(), *TargetVar.ToString()); }
	bool bLastTaken = false;
	const int32 Index = FindFreeSlot(Slots, TargetVar, SlotRadius, OrderCode, bMatchXbowTag, 2.f, &bLastTaken, Target != nullptr);
	// Tmp.Y: the Blueprint For Each has no early exit; it resets Tmp.Y for each slot and leaves the LAST slot's flag.
	// With no slots its body never runs, so Tmp is left untouched - same here.
	if (bWriteTmpY && Slots.Num() > 0 && bContractOK)
	{
		if (USceneComponent* Tmp = GetSlotComponent(TEXT("Tmp")))
		{
			FVector L = Tmp->GetRelativeLocation(); L.Y = bLastTaken ? 1.f : 0.f;
			Tmp->SetRelativeLocation(L, false, nullptr, ETeleportType::TeleportPhysics);
		}
	}
	if (Index == INDEX_NONE || !Target) { return false; }
	Target->SetRelativeLocation(Slots[Index], false, nullptr, ETeleportType::TeleportPhysics);   // Blueprint: Set Relative Location, bTeleport
	return true;
}

int32 ASoldierBase::FindFreeSlot(const TArray<FVector>& Slots, FName TargetVar, float SlotRadius, int32 OrderCode, bool bMatchXbowTag, float ReservationSeconds, bool* bLastTaken, bool bMayReserve)
{
	using namespace CDSoldierBrain;
	if (bLastTaken) { *bLastTaken = false; }
	if (!bContractOK || Slots.Num() == 0 || SlotRadius <= 0.f) { return INDEX_NONE; }
	UWorld* World = GetWorld();
	const UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this);
	if (!World || !Crowd) { return INDEX_NONE; }
	if (GReservationWorld.Get() != World) { GReservations.Reset(); GReservationWorld = World; }
	const double Now = World->GetTimeSeconds();
	static const FName SB_Xbow(TEXT("Xbow"));
	const bool bIAmXbow = ActorHasTag(SB_Xbow);

	// TargetVar spots of every OTHER live soldier passing the call site's filter. O(S) collect + O(K x T) compare.
	TArray<FVector2D> Taken;
	Crowd->ForEachSoldier([&](AActor* S)
	{
		if (!IsValid(S) || S == this || S->GetLifeSpan() >= 0.01f) { return; }   // Blueprint: other soldier, GetLifeSpan < 0.01
		if (OrderCode >= 0 && !HasOrder(GetSlotComponentOf(S, SB_Order), OrderCode)) { return; }
		if (bMatchXbowTag && S->ActorHasTag(SB_Xbow) != bIAmXbow) { return; }
		if (const USceneComponent* G = GetSlotComponentOf(S, TargetVar))
		{
			const FVector L = G->GetRelativeLocation();   // same space the Blueprint writes it in
			Taken.Emplace(L.X, L.Y);
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("cd.Soldier: %s has no %s component - its spot cannot be checked."), *S->GetName(), *TargetVar.ToString());
		}
	});

	const float RSq = FMath::Square(SlotRadius);
	auto IsTaken = [&](const FVector& Slot)
	{
		const FVector2D P(Slot.X, Slot.Y);
		for (const FVector2D& T : Taken) { if (FVector2D::DistSquared(P, T) < RSq) { return true; } }
		return false;
	};
	if (bLastTaken) { *bLastTaken = IsTaken(Slots.Last()); }   // what the Blueprint loop leaves in Tmp.Y
	const bool bReserve = GSlotReservation != 0 && bMayReserve;
	for (int32 i = 0; i < Slots.Num(); ++i)
	{
		if (IsTaken(Slots[i])) { continue; }
		if (!bReserve) { return i; }   // Blueprint rule: the first slot no other live soldier holds
		const FString Key = TargetVar.ToString() + TEXT(":") + SlotKey(OrderCode, Slots[i]) + (bMatchXbowTag ? (bIAmXbow ? TEXT(":x") : TEXT(":s")) : TEXT(""));
		if (const FReservation* R = GReservations.Find(Key))
		{
			const AActor* ResOwner = R->Owner.Get();
			if (ResOwner && ResOwner != this && Now - R->Time < ReservationSeconds) { continue; }   // reserved by someone else
		}
		GReservations.Add(Key, { this, Now });   // reserve at once: a second soldier this frame skips it
		return i;
	}
	return INDEX_NONE;
}
