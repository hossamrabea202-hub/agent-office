#include "CDCombatRules.h"
#include "TimerManager.h"
#include "Camera/PlayerCameraManager.h"
#include "CDRevealVideoSubsystem.h"
#include "UObject/UnrealType.h"
#include "EngineUtils.h"
#include "Navigation/PathFollowingComponent.h"
#include "GameFramework/Controller.h"
#include "ZombieBase.h"
#include "Animation/AnimMontage.h"
#include "SoldierBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Actor.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInterface.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Components/StaticMeshComponent.h"
#include "Containers/Ticker.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/DelayedAutoRegister.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "GameFramework/Pawn.h"

namespace CDCombatRules
{
	static int32 GColossusHeadshot = 0;
	static int32 GGateDebris = 1;
	static FAutoConsoleVariableRef CVarDebris(TEXT("cd.Combat.GateDebris"), GGateDebris, TEXT("1 = the gate breach throws physics debris (default)."));
	static FAutoConsoleVariableRef CVar(TEXT("cd.Combat.ColossusHeadshot"), GColossusHeadshot, TEXT("1 = colossi can be killed by a crossbow headshot (old rule). 0 = no headshots on colossi (default)."));
}

bool UCDCombatRules::IsColossus(const UObject* Zombie)
{
	const AActor* A = Cast<AActor>(Zombie);
	if (!A) { return false; }
	for (const UClass* C = A->GetClass(); C; C = C->GetSuperClass())
	{
		const FString N = C->GetName();
		if (N.Contains(TEXT("WallBreaker")) || N.Contains(TEXT("Colossus"))) { return true; }
	}
	TArray<USkeletalMeshComponent*> Meshes;
	A->GetComponents(Meshes);
	for (const USkeletalMeshComponent* M : Meshes)
	{
		if (!M) { continue; }
		for (int32 i = 0; i < M->GetNumMaterials(); ++i)
		{
			const UMaterialInterface* Mat = M->GetMaterial(i);
			if (Mat && Mat->GetName().Contains(TEXT("Colossus"))) { return true; }
		}
	}
	return false;
}

namespace CDMenuClick
{
	static float GGrace = 0.35f;
	static FAutoConsoleVariableRef CVar(TEXT("cd.Combat.MenuClickGrace"), GGrace, TEXT("Seconds after a HUD menu hides the mouse cursor during which a click does not attack (0.35)."));
	static double GLastCursorShown = -1000.0;
	// once per frame: remember when any game world's player last had the menu cursor showing (menus pause the game, so the
	// press that closes a menu can reach the attack input a frame later - after the cursor is already hidden)
	static FDelayedAutoRegisterHelper GRegister(EDelayedRegisterRunPhase::EndOfEngineInit, []()
	{
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float)
		{
			if (!GEngine) { return true; }
			for (const FWorldContext& Ctx : GEngine->GetWorldContexts())
			{
				UWorld* W = Ctx.World();
				if (!W || !W->IsGameWorld()) { continue; }
				const APlayerController* PC = W->GetFirstPlayerController();
				if (PC && PC->bShowMouseCursor) { GLastCursorShown = FPlatformTime::Seconds(); }
			}
			return true;
		}));
	});
}

bool UCDCombatRules::GateHeroAttack(bool bIn, const UObject* WorldContextObject)
{
	if (!bIn) { return false; }
	if (UCDRevealVideoSubsystem::IsRevealPlaying()) { return false; }   // 11-06 owner: no sword while a reveal video plays
	const APlayerController* PC = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
	if (PC && PC->bShowMouseCursor) { return false; }
	return FPlatformTime::Seconds() - CDMenuClick::GLastCursorShown > CDMenuClick::GGrace;
}

static TAutoConsoleVariable<float> CVarHitStop(TEXT("cd.Hit.Stop"), 1.f, TEXT("Multiplies the length of the hero hit-stop. 0 = off."));

void UCDCombatRules::HeroHitStop(AActor* Hero, float Damage)
{
	const float Mul = CVarHitStop.GetValueOnGameThread();
	UWorld* World = Hero ? Hero->GetWorld() : nullptr;
	if (!World || Mul <= 0.f || Damage <= 0.f) { return; }
	static double Busy = -1.0;
	const double Now = World->GetRealTimeSeconds();
	if (Now < Busy) { Busy = -1.0; } // a new Play session restarted the clock
	if (Now < Busy + 0.12) { return; } // a sweep hitting many enemies freezes once
	if (!FMath::IsNearlyEqual(Hero->CustomTimeDilation, 1.f)) { return; } // something else owns the hero clock right now
	Busy = Now;
	Hero->CustomTimeDilation = 0.08f;
	const float Seconds = FMath::Clamp(0.035f + Damage / 1500.f, 0.035f, 0.09f) * Mul;
	FTimerHandle Unused;
	TWeakObjectPtr<AActor> Weak(Hero);
	World->GetTimerManager().SetTimer(Unused, FTimerDelegate::CreateLambda([Weak]()
	{
		if (AActor* A = Weak.Get()) { if (FMath::IsNearlyEqual(A->CustomTimeDilation, 0.08f)) { A->CustomTimeDilation = 1.f; } } // Berserk may have set its own speed meanwhile
	}), Seconds, false);
}

static TAutoConsoleVariable<float> CVarBerserkEnd(TEXT("cd.Hero.BerserkEndDamage"), 12.f, TEXT("Berserk ends once DamageTaken is at or below this (250 kills, Berserk starts at 85 and heals 20). Negative = old behaviour, 8 s only."));

static FDoubleProperty* HeroDamageProp(const AActor* Hero) { return Hero ? FindFProperty<FDoubleProperty>(Hero->GetClass(), TEXT("DamageTaken")) : nullptr; }

bool UCDCombatRules::BerserkShouldEnd(bool bIn, const UObject* WorldContextObject)
{
	if (bIn) { return true; }
	const float Limit = CVarBerserkEnd.GetValueOnGameThread();
	if (Limit < 0.f) { return false; }
	const AActor* Hero = UGameplayStatics::GetPlayerPawn(WorldContextObject, 0);
	const FDoubleProperty* P = HeroDamageProp(Hero);
	return P && P->GetPropertyValue_InContainer(Hero) <= Limit;
}

// Test only: writes the DamageTaken value of the hero directly.
static FAutoConsoleCommandWithWorldAndArgs GCDTestHeroDamage(TEXT("cd.Test.HeroDamage"), TEXT("cd.Test.HeroDamage N: sets DamageTaken of the hero."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* W)
	{
		AActor* Hero = W ? UGameplayStatics::GetPlayerPawn(W, 0) : nullptr;
		if (FDoubleProperty* P = HeroDamageProp(Hero)) { if (Args.Num() > 0) { P->SetPropertyValue_InContainer(Hero, FCString::Atod(*Args[0])); } }
	}));

AActor* UCDCombatRules::SafeYard(AActor* In)
{
	if (In) { return In; }
	static TSoftClassPtr<AActor> Soft(FSoftObjectPath(TEXT("/Game/CastleDefender/Gameplay/Castle/BP_CannonOrder.BP_CannonOrder_C")));
	UClass* Cls = Soft.LoadSynchronous();
	return Cls ? Cls->GetDefaultObject<AActor>() : nullptr;
}

bool UCDCombatRules::HasClearLineToCamera(const AActor* Actor)
{
	UWorld* World = Actor ? Actor->GetWorld() : nullptr;
	if (!World) { return false; }
	APlayerController* PC = World->GetFirstPlayerController();
	if (!PC || !PC->PlayerCameraManager) { return true; }
	struct FEntry { double At = -1.0; bool bClear = true; };
	static TMap<TWeakObjectPtr<const AActor>, FEntry> Cache;
	static double NextPrune = 0.0;
	const double Now = World->GetTimeSeconds();
	if (Now < NextPrune - 60.0) { Cache.Reset(); NextPrune = 0.0; } // a new Play session restarted the clock
	if (Now >= NextPrune)
	{
		NextPrune = Now + 5.0;
		for (auto It = Cache.CreateIterator(); It; ++It) { if (!It.Key().IsValid()) { It.RemoveCurrent(); } }
	}
	FEntry& E = Cache.FindOrAdd(Actor);
	if (E.At >= 0.0 && Now >= E.At && Now - E.At < 0.25) { return E.bClear; }
	FCollisionQueryParams Q(SCENE_QUERY_STAT(CDBarLOS), false, Actor);
	Q.AddIgnoredActor(PC->GetPawn());
	const FVector From = PC->PlayerCameraManager->GetCameraLocation();
	const FVector To = Actor->GetActorLocation() + FVector(0.0, 0.0, 60.0);
	FHitResult Hit;
	const bool bHit = World->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Q);
	E.bClear = !bHit || Cast<APawn>(Hit.GetActor()) != nullptr; // another creature in the way is not a wall
	E.At = Now;
	return E.bClear;
}

double UCDCombatRules::SafeLifeSpan(const AActor* Actor)
{
	return Actor ? Actor->GetLifeSpan() : 0.0;
}

bool UCDCombatRules::GateWheelKey(bool bIn, const UObject* WorldContextObject)
{
	if (!bIn) { return false; }
	const APlayerController* PC = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
	APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	if (!Pawn) { return bIn; }
	for (UActorComponent* Comp : Pawn->GetComponents())
	{
		if (!Comp || !Comp->GetClass()->GetName().StartsWith(TEXT("BPC_CommanderCard"))) { continue; }
		const FBoolProperty* Open = FindFProperty<FBoolProperty>(Comp->GetClass(), TEXT("Open"));
		const FBoolProperty* Near = FindFProperty<FBoolProperty>(Comp->GetClass(), TEXT("NearCommander"));
		const bool bOpen = Open && Open->GetPropertyValue_InContainer(Comp);
		const bool bNear = Near && Near->GetPropertyValue_InContainer(Comp);
		return !(bOpen || bNear);
	}
	return bIn;
}

namespace CDReach
{
	static int32 GEnable = 1;
	static FAutoConsoleVariableRef CVar(TEXT("cd.Combat.ReachableGoals"), GEnable, TEXT("1 = soldiers do not walk towards targets they cannot reach (they hold instead). 0 = old behaviour."));
	struct FEntry { FVector Goal = FVector(FLT_MAX); double When = -100.0; bool bReachable = true; };
	static TMap<TWeakObjectPtr<const AActor>, FEntry> GCache;
}

FVector UCDCombatRules::ReachableGoal(FVector Goal, const UObject* WorldContextObject)
{
	const APawn* Pawn = Cast<APawn>(WorldContextObject);
	if (!CDReach::GEnable || !Pawn) { return Goal; }
	UWorld* W = Pawn->GetWorld();
	UNavigationSystemV1* Nav = W ? FNavigationSystem::GetCurrent<UNavigationSystemV1>(W) : nullptr;
	if (!Nav) { return Goal; }
	const double Now = W->GetTimeSeconds();
	CDReach::FEntry& E = CDReach::GCache.FindOrAdd(Pawn);
	if (CDReach::GCache.Num() > 512) { for (auto It = CDReach::GCache.CreateIterator(); It; ++It) { if (!It.Key().IsValid()) { It.RemoveCurrent(); } } }
	// 11-06 perf: a moving target re-pathed every frame (5 sync paths/frame for 10 swordsmen = 9 ms). Re-path at most every 0.3 s when the goal moved, every 0.75 s otherwise.
	if (Now - E.When > 0.75 || (Now - E.When > 0.3 && FVector::DistSquared2D(E.Goal, Goal) > FMath::Square(150.f)))
	{
		const UNavigationPath* Path = Nav->FindPathToLocationSynchronously(W, Pawn->GetActorLocation(), Goal, const_cast<APawn*>(Pawn));
		// no nav data at all -> leave the Blueprint alone; a partial path = the goal is cut off (walls)
		E.bReachable = !Path || !Path->IsValid() ? (Path == nullptr) : !Path->IsPartial();
		if (Path && Path->IsValid() && !Path->IsPartial()) { E.bReachable = true; }
		E.Goal = Goal; E.When = Now;
	}
	return E.bReachable ? Goal : Pawn->GetActorLocation();
}

bool UCDCombatRules::GateHeadshot(bool bIn, UObject* Zombie)
{
	return bIn && (CDCombatRules::GColossusHeadshot || !IsColossus(Zombie));
}

void UCDCombatRules::SpawnGateDebris(const UObject* WorldContextObject, FVector Location, int32 Count)
{
	if (!CDCombatRules::GGateDebris) { return; }
	UWorld* W = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	static TWeakObjectPtr<UStaticMesh> Mesh;
	if (!Mesh.IsValid()) { Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/CastleDefender/Props/Aftermath/SiegeDebris/SM_Debris_Beams.SM_Debris_Beams")); }
	if (!W || !Mesh.IsValid()) { return; }
	const float MeshSize = FMath::Max(1.f, Mesh->GetBounds().BoxExtent.GetMax() * 2.f);
	for (int32 i = 0; i < FMath::Clamp(Count, 0, 30); ++i)
	{
		const FVector P = Location + FVector(FMath::FRandRange(-60.f, 60.f), FMath::FRandRange(-200.f, 200.f), FMath::FRandRange(-40.f, 120.f));
		FActorSpawnParameters SP;
		SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AStaticMeshActor* A = W->SpawnActor<AStaticMeshActor>(P, FRotator(FMath::FRandRange(0.f, 360.f), FMath::FRandRange(0.f, 360.f), FMath::FRandRange(0.f, 360.f)), SP);
		if (!A) { continue; }
		UStaticMeshComponent* C = A->GetStaticMeshComponent();
		C->SetMobility(EComponentMobility::Movable);
		C->SetStaticMesh(Mesh.Get());
		A->SetActorScale3D(FVector(FMath::FRandRange(45.f, 90.f) / MeshSize));   // pieces 45-90 cm long
		C->SetCollisionProfileName(TEXT("PhysicsActor"));
		C->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
		C->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
		C->SetCastShadow(false);
		C->SetSimulatePhysics(true);
		// thrown inward, away from the gate (+X is the courtyard)
		C->AddImpulse(FVector(FMath::FRandRange(350.f, 900.f), FMath::FRandRange(-350.f, 350.f), FMath::FRandRange(250.f, 600.f)), NAME_None, true);
		C->AddAngularImpulseInDegrees(FVector(FMath::FRandRange(-720.f, 720.f), FMath::FRandRange(-720.f, 720.f), FMath::FRandRange(-720.f, 720.f)), NAME_None, true);
		A->SetLifeSpan(6.f);
	}
}

namespace CDFollow
{
	static int32 GEnable = 1;
	static float GHold = 190.f;
	static float GDist = 150.f;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.Soldier.FollowFix"), GEnable, TEXT("1 = followers (order 2) hold near the hero instead of chasing a facing-relative slot (default). 0 = Blueprint slot."));
	static FAutoConsoleVariableRef CVarHold(TEXT("cd.Soldier.FollowHold"), GHold, TEXT("A follower within this distance of the hero (cm) stays put."));
	static FAutoConsoleVariableRef CVarDist(TEXT("cd.Soldier.FollowDist"), GDist, TEXT("A follower farther away walks to this distance from the hero (cm), on its own side."));
}

FVector UCDCombatRules::FollowGoal(FVector Goal, const UObject* WorldContextObject)
{
	const APawn* Pawn = Cast<APawn>(WorldContextObject);
	const ASoldierBase* Soldier = Cast<ASoldierBase>(Pawn);
	if (!CDFollow::GEnable || !Soldier || Soldier->GetOrderCode() != 2) { return Goal; }
	const APawn* Hero = UGameplayStatics::GetPlayerPawn(WorldContextObject, 0);
	if (!Hero) { return Goal; }
	const FVector Me = Pawn->GetActorLocation();
	const FVector H = Hero->GetActorLocation();
	const float D = FVector::Dist2D(Me, H);
	if (D <= CDFollow::GHold)
	{
		// close enough: hold. Re-issuing SimpleMoveToLocation(own spot) every Think made the follower spin / circle in place
		// (11-06 owner: "one standing still, the other rotating around him"), so stop the move request outright.
		if (AController* Ctl = Pawn->GetController())
		{
			if (UPathFollowingComponent* PF = Ctl->FindComponentByClass<UPathFollowingComponent>())
			{
				if (PF->GetStatus() != EPathFollowingStatus::Idle) { Ctl->StopMovement(); }
			}
		}
		return Me;
	}
	FVector Dir = (Me - H).GetSafeNormal2D();
	if (Dir.IsNearlyZero()) { Dir = -Hero->GetActorForwardVector().GetSafeNormal2D(); }
	FVector Slot = H + Dir * CDFollow::GDist;
	Slot.Z = H.Z;
	return Slot;
}

UAnimMontage* UCDCombatRules::ZombieFlinch(UAnimMontage* Default, const UObject* WorldContextObject)
{
	static bool GEnable = true;
	static FAutoConsoleVariableRef CVar(TEXT("cd.Zombie.DirectionalFlinch"), GEnable, TEXT("1 = flinch by hit side + stagger/heavy by damage (AZombieBase sets). 0 = the old front/back only."));
	const AZombieBase* Z = Cast<AZombieBase>(WorldContextObject);
	return (GEnable && Z) ? Z->PickFlinchMontage(Default) : Default;
}

FString UCDCombatRules::GrantChestExtras(const UObject* WorldContextObject, int32 SkillPoints, int32 Potions)
{
	UWorld* W = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
	if (!W) { return TEXT("no world"); }
	FString Out;
	// potions: the hero's potion belt component, int "Potions"
	if (APawn* Hero = UGameplayStatics::GetPlayerPawn(W, 0))
	{
		for (UActorComponent* C : Hero->GetComponents())
		{
			if (!C || !C->GetClass()->GetName().StartsWith(TEXT("BPC_PotionBelt"))) { continue; }
			if (FIntProperty* P = FindFProperty<FIntProperty>(C->GetClass(), TEXT("Potions")))
			{
				const int32 Now = P->GetPropertyValue_InContainer(C); P->SetPropertyValue_InContainer(C, Now + Potions);
				Out += FString::Printf(TEXT("potions %d -> %d; "), Now, Now + Potions);
			}
			break;
		}
	}
	// skill points: the skill tree HUD actor, double "SPT" (the pool the tree spends from)
	for (TActorIterator<AActor> It(W); It; ++It)
	{
		AActor* A = *It;
		if (!A || !A->GetClass()->GetName().StartsWith(TEXT("BP_SkillTreeHUD"))) { continue; }
		if (FDoubleProperty* D = FindFProperty<FDoubleProperty>(A->GetClass(), TEXT("SPT")))
		{
			const double Now = D->GetPropertyValue_InContainer(A); D->SetPropertyValue_InContainer(A, Now + SkillPoints);
			Out += FString::Printf(TEXT("SPT %.0f -> %.0f; "), Now, Now + SkillPoints);
		}
		else if (FFloatProperty* F = FindFProperty<FFloatProperty>(A->GetClass(), TEXT("SPT")))
		{
			const float Now = F->GetPropertyValue_InContainer(A); F->SetPropertyValue_InContainer(A, Now + SkillPoints);
			Out += FString::Printf(TEXT("SPT %.0f -> %.0f; "), Now, Now + SkillPoints);
		}
		break;
	}
	UE_LOG(LogTemp, Display, TEXT("[CD] chest extras: %s"), *Out);
	return Out;
}
