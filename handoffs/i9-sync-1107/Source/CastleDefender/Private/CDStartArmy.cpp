// Start-of-game army formation. rev 4 (owner playtest 2026-11-06):
//  - PLACEMENT: each block (commander in front, 5 swords, 5 crossbows behind them, medic at the rear corner) is placed in OPEN
//    courtyard space: candidate block centres around the default spot are tested slot by slot (sphere clearance against walls,
//    columns, stairs, the fountain; ground at the courtyard's level), the clearest candidate nearest the default wins. Ranks are
//    spaced like a real file (cd.StartArmy.Spacing 200 cm across, 230 cm between ranks).
//  - FULL SLEEP while waiting: Blueprint brain, character movement, the AI controller and its components stop ticking; animation
//    only updates while on screen, at a reduced rate (restored exactly on wake). The cloth budget already pauses far capes.
//  - THE HERO DOES NOT WAKE THEM. A soldier only steps aside when the hero walks INTO him (within 110 cm and moving towards him),
//    then walks back to his own spot, faces the gate and sleeps again - the formation re-forms instead of crowding.
//  - WAKE (normal Blueprint behaviour from then on): a zombie within cd.StartArmy.WakeRange, or the soldier's order changed
//    (the hero gave him an order with E).
#include "CDStartArmy.h"
#include "AIController.h"
#include "Blueprint/AIBlueprintHelperLibrary.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "SoldierBase.h"
#include "TimerManager.h"
#include "ZombieBase.h"

namespace CDStartArmy
{
	static int32 GEnable = 1;
	static float GSpacing = 200.f;
	static float GRankGap = 230.f;
	static float GSideOffset = 750.f;
	static float GWakeRange = 2500.f;
	static float GClearance = 120.f;
	static int32 GFullSleep = 1;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.StartArmy.Enable"), GEnable, TEXT("1 = spawn the start army formation beside the fountain when play begins (default)."));
	static FAutoConsoleVariableRef CVarSpacing(TEXT("cd.StartArmy.Spacing"), GSpacing, TEXT("Distance between soldiers in a rank of the start formation (cm, 200)."));
	static FAutoConsoleVariableRef CVarRank(TEXT("cd.StartArmy.RankGap"), GRankGap, TEXT("Distance between ranks of the start formation (cm, 230)."));
	static FAutoConsoleVariableRef CVarWake(TEXT("cd.StartArmy.WakeRange"), GWakeRange, TEXT("An idle formation soldier wakes when a zombie is this close (cm)."));
	static FAutoConsoleVariableRef CVarSide(TEXT("cd.StartArmy.SideOffset"), GSideOffset, TEXT("Fountain centre to each formation block centre, sideways (cm) - the search starts here."));
	static FAutoConsoleVariableRef CVarClear(TEXT("cd.StartArmy.Clearance"), GClearance, TEXT("Free radius around every formation spot (cm, 120): no wall, column, stair or prop inside it."));
	static FAutoConsoleVariableRef CVarSleep(TEXT("cd.StartArmy.FullSleep"), GFullSleep, TEXT("1 = waiting soldiers also stop movement / AI controller ticks and animate only on screen (default)."));

	static const TCHAR* CommanderPath = TEXT("/Game/CastleDefender/Characters/Knight/BP_SoldierCommander.BP_SoldierCommander_C");
	static const TCHAR* SwordPath = TEXT("/Game/CastleDefender/Characters/Knight/BP_SoldierSword.BP_SoldierSword_C");
	static const TCHAR* XbowPath = TEXT("/Game/CastleDefender/Characters/Knight/BP_SoldierXbow.BP_SoldierXbow_C");
	static const TCHAR* MedicPath = TEXT("/Game/CastleDefender/Gameplay/Medics/BP_Medic.BP_Medic_C");

	// per waiting soldier (kept here so the subsystem header stays unchanged)
	struct FMeshState { TWeakObjectPtr<USkeletalMeshComponent> Mesh; EVisibilityBasedAnimTickOption Option; bool bURO; };
	struct FWaiter
	{
		FVector Spot = FVector::ZeroVector;
		FRotator Facing = FRotator::ZeroRotator;
		int32 Order = -1;
		bool bAsleep = false;
		bool bStepping = false;   // stepped aside for the hero, walking back afterwards
		double StepStart = 0.0;
		TArray<FMeshState> Meshes;
	};
	static TMap<TWeakObjectPtr<AActor>, FWaiter> GWaiters;

	static void SetAsleep(AActor* A, FWaiter& W, bool bSleep)
	{
		if (W.bAsleep == bSleep) { return; }
		W.bAsleep = bSleep;
		A->SetActorTickEnabled(!bSleep);   // the Blueprint brain (Event Tick part)
		// ...and its timer part: BP_SoldierSword (and children) run "FocusCheck" every 0.15 s by a looping Set Timer by Event,
		// which keeps firing with the actor tick off. Pause / resume that timer by its event (it keeps its phase).
		static const FName TimerEvents[] = { TEXT("FocusCheck") };
		for (const FName& Ev : TimerEvents)
		{
			if (!A->FindFunction(Ev)) { continue; }
			FTimerDynamicDelegate D; D.BindUFunction(A, Ev);
			if (bSleep) { UKismetSystemLibrary::K2_PauseTimerDelegate(D); } else { UKismetSystemLibrary::K2_UnPauseTimerDelegate(D); }
		}
		if (!GFullSleep && bSleep) { return; }
		if (ACharacter* C = Cast<ACharacter>(A))
		{
			if (UCharacterMovementComponent* M = C->GetCharacterMovement())
			{
				if (bSleep) { M->StopMovementImmediately(); }
				M->SetComponentTickEnabled(!bSleep);
			}
		}
		if (const APawn* P = Cast<APawn>(A))
		{
			if (AController* Ctrl = P->GetController())
			{
				Ctrl->SetActorTickEnabled(!bSleep);
				TInlineComponentArray<UActorComponent*> Comps(Ctrl);
				for (UActorComponent* Comp : Comps) { if (Comp) { Comp->SetComponentTickEnabled(!bSleep); } }
			}
		}
		if (bSleep)
		{
			W.Meshes.Reset();
			TInlineComponentArray<USkeletalMeshComponent*> Meshes(A);
			for (USkeletalMeshComponent* Mesh : Meshes)
			{
				W.Meshes.Add({ Mesh, Mesh->VisibilityBasedAnimTickOption, Mesh->bEnableUpdateRateOptimizations != 0 });
				Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
				Mesh->bEnableUpdateRateOptimizations = true;
			}
		}
		else
		{
			for (const FMeshState& S : W.Meshes)
			{
				if (USkeletalMeshComponent* Mesh = S.Mesh.Get()) { Mesh->VisibilityBasedAnimTickOption = S.Option; Mesh->bEnableUpdateRateOptimizations = S.bURO; }
			}
			W.Meshes.Reset();
		}
	}

	// movement + controller on, Blueprint brain still off: used for stepping aside and walking back
	static void SetWalking(AActor* A, FWaiter& W)
	{
		SetAsleep(A, W, false);
		A->SetActorTickEnabled(false);   // movement + controller run, the Blueprint brain stays off
		if (A->FindFunction(TEXT("FocusCheck"))) { FTimerDynamicDelegate D; D.BindUFunction(A, TEXT("FocusCheck")); UKismetSystemLibrary::K2_PauseTimerDelegate(D); }
		W.bAsleep = false;
	}

	static FAutoConsoleCommandWithWorld CmdSpawn(TEXT("cd.StartArmy.Spawn"), TEXT("Spawn the start army formation now."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* W)
		{
			if (UCDStartArmySubsystem* S = W ? W->GetSubsystem<UCDStartArmySubsystem>() : nullptr)
			{
				UE_LOG(LogTemp, Display, TEXT("cd.StartArmy: placed %d"), S->SpawnFormation());
			}
		}));
}

bool UCDStartArmySubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* W = Cast<UWorld>(Outer);
	return W && W->IsGameWorld() && Super::ShouldCreateSubsystem(Outer);
}

void UCDStartArmySubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	CDStartArmy::GWaiters.Reset();
	if (!CDStartArmy::GEnable) { return; }
	const FString MapName = InWorld.GetMapName();
	if (!MapName.Contains(TEXT("ThirdPersonMap")) || MapName.Contains(TEXT("MineDungeon"))) { return; }
	InWorld.GetTimerManager().SetTimer(Timer, FTimerDelegate::CreateWeakLambda(this, [this]() { SpawnFormation(); }), 0.5f, false);
}

int32 UCDStartArmySubsystem::SpawnFormation()
{
	using namespace CDStartArmy;
	UWorld* W = GetWorld();
	if (!W || bSpawned) { return 0; }
	++Attempts;

	AActor* Fountain = nullptr;
	for (TActorIterator<AActor> It(W); It; ++It)
	{
		if (It->GetClass()->GetName().StartsWith(TEXT("BP_CourtyardFountain"))) { Fountain = *It; break; }
	}
	auto RetryLater = [&](const TCHAR* Why)
	{
		UE_LOG(LogTemp, Warning, TEXT("cd.StartArmy: %s (attempt %d)"), Why, Attempts);
		if (Attempts < 5) { W->GetTimerManager().SetTimer(Timer, FTimerDelegate::CreateWeakLambda(this, [this]() { SpawnFormation(); }), 1.f, false); }
	};
	if (!Fountain) { RetryLater(TEXT("no BP_CourtyardFountain yet")); return 0; }

	UClass* Cmdr = LoadClass<AActor>(nullptr, CommanderPath);
	UClass* Sword = LoadClass<AActor>(nullptr, SwordPath);
	UClass* Xbow = LoadClass<AActor>(nullptr, XbowPath);
	UClass* Medic = LoadClass<AActor>(nullptr, MedicPath);
	if (!Cmdr || !Sword || !Xbow || !Medic) { RetryLater(TEXT("a soldier class failed to load")); return 0; }

	// the main gate is at -X from the fountain: the army faces it
	const FVector C = Fountain->GetActorLocation();
	const FVector Fwd(-1.f, 0.f, 0.f);
	const FVector Side(0.f, 1.f, 0.f);
	const FRotator Facing = Fwd.Rotation();
	const float S = GSpacing, R = GRankGap;

	// ground point under P at the courtyard's level, or false (a wall top, stairs, a hole)
	FCollisionQueryParams Q(TEXT("CDStartArmy"), false);
	auto Ground = [&](FVector& P) -> bool
	{
		FHitResult Hit;
		if (!W->LineTraceSingleByChannel(Hit, P + FVector(0, 0, 400.f), P - FVector(0, 0, 800.f), ECC_Pawn, Q)) { return false; }   // what a soldier stands on
		if (FMath::Abs(Hit.ImpactPoint.Z - C.Z) > 120.f) { return false; }
		P.Z = Hit.ImpactPoint.Z + 100.f;
		return true;
	};
	auto Clear = [&](const FVector& P, float Radius) -> bool
	{
		// only what would BLOCK a soldier (walls, columns, stairs, props); trigger volumes and decals only overlap and do not count
		return !W->OverlapBlockingTestByChannel(P + FVector(0, 0, 30.f), FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(Radius), Q);
	};

	// one block's spots relative to its centre (ahead, across): commander, 5 swords, 5 crossbows, medic
	struct FRel { int32 Kind; float Ahead; float Across; };
	TArray<FRel> Block;
	Block.Add({ 0, R, 0.f });
	for (int32 Col = -2; Col <= 2; ++Col) { Block.Add({ 1, 0.f, Col * S }); }
	for (int32 Col = -2; Col <= 2; ++Col) { Block.Add({ 2, -R, Col * S }); }

	if (Slots.Num() == 0)
	{
		for (const float SideSign : { -1.f, 1.f })
		{
			// search block centres: ahead 450..1250, sideways 500..1400 on this side; best = all spots clear with the
			// largest margin, then nearest the default spot (650 ahead, SideOffset across)
			float BestScore = -1.f; FVector2D Best(650.f, SideSign * GSideOffset);
			for (float Ahead = 450.f; Ahead <= 1250.f; Ahead += 100.f)
			{
				for (float Across = 500.f; Across <= 1400.f; Across += 100.f)
				{
					int32 Ok = 0, Roomy = 0;
					const int32 MedicSide = SideSign > 0 ? 1 : -1;
					for (int32 i = 0; i <= Block.Num(); ++i)
					{
						const float a = i < Block.Num() ? Block[i].Ahead : -2.f * R;
						const float c = i < Block.Num() ? Block[i].Across : MedicSide * 3.f * S;
						FVector P = C + Fwd * (Ahead + a) + Side * (SideSign * Across + c);
						if (!Ground(P)) { Ok = -100; break; }   // a spot off the courtyard floor rules the candidate out
						if (!Clear(P, GClearance)) { continue; }
						++Ok;
						if (Clear(P, GClearance * 1.8f)) { ++Roomy; }
					}
					if (Ok < 0) { continue; }
					const float Dist = FVector2D::Distance(FVector2D(Ahead, SideSign * Across), FVector2D(650.f, SideSign * GSideOffset));
					// most clear spots first, then most room around them, then nearest the default position
					const float Score = Ok * 100000.f + Roomy * 1000.f - Dist;
					if (Score > BestScore) { BestScore = Score; Best = FVector2D(Ahead, SideSign * Across); }
				}
			}
			UE_LOG(LogTemp, Display, TEXT("cd.StartArmy: side %.0f block centre ahead %.0f across %.0f (score %.0f: %d of %d spots clear)"), SideSign, Best.X, Best.Y, BestScore,
				BestScore > 0.f ? int32(BestScore / 100000.f) : 0, Block.Num() + 1);
			for (const FRel& Rel : Block)
			{
				UClass* Cls = Rel.Kind == 0 ? Cmdr : (Rel.Kind == 1 ? Sword : Xbow);
				Slots.Add({ Cls, float(Best.X + Rel.Ahead), float(Best.Y + Rel.Across) });
			}
			Slots.Add({ Medic, float(Best.X - 2.f * R), float(Best.Y + (SideSign > 0 ? 1.f : -1.f) * 3.f * S) });
		}
	}

	int32 Placed = 0;
	for (FSlot& Slot : Slots)
	{
		if (Slot.Spawned.IsValid() || Slot.bTried) { continue; }   // never a duplicate; a fallen soldier is not refilled
		FVector P = C + Fwd * Slot.Ahead + Side * Slot.Across;
		Ground(P);
		FActorSpawnParameters SP;
		SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
		if (AActor* A = W->SpawnActor<AActor>(Slot.Class.Get(), P, Facing, SP))
		{
			++Placed;
			Slot.Spawned = A;
			Slot.bTried = true;
			FWaiter& Wt = GWaiters.Add(A);
			Wt.Spot = A->GetActorLocation();
			Wt.Facing = Facing;
			if (const ASoldierBase* SB = Cast<ASoldierBase>(A)) { Wt.Order = SB->GetOrderCode(); }
			SetAsleep(A, Wt, true);
			Idle.Add(A);
		}
	}
	int32 Missing = 0;
	for (const FSlot& Slot : Slots) { if (!Slot.bTried) { ++Missing; } }
	if (Missing == 0) { bSpawned = true; }
	else { RetryLater(*FString::Printf(TEXT("%d of %d formation slots failed to spawn"), Missing, Slots.Num())); }
	W->GetTimerManager().SetTimer(WakeTimer, FTimerDelegate::CreateWeakLambda(this, [this]() { CheckWake(); }), 0.2f, true);
	UE_LOG(LogTemp, Display, TEXT("cd.StartArmy: placed %d (total slots %d) around %s"), Placed, Slots.Num(), *Fountain->GetName());
	return Placed;
}

void UCDStartArmySubsystem::CheckWake()
{
	using namespace CDStartArmy;
	UWorld* W = GetWorld();
	if (!W) { return; }
	const APawn* Hero = UGameplayStatics::GetPlayerPawn(W, 0);
	TArray<FVector> Zombies;
	for (TActorIterator<AZombieBase> It(W); It; ++It) { if (!It->IsDeadForCrowd()) { Zombies.Add(It->GetActorLocation()); } }
	const float WakeSq = FMath::Square(GWakeRange);
	const double Now = W->GetTimeSeconds();
	for (int32 i = Idle.Num() - 1; i >= 0; --i)
	{
		AActor* A = Idle[i].Get();
		FWaiter* Wt = GWaiters.Find(A);
		if (!A || !Wt) { Idle.RemoveAtSwap(i); continue; }
		const FVector P = A->GetActorLocation();

		// wake for good: zombies near, or an order from the hero
		bool bWake = false;
		for (const FVector& Z : Zombies) { if (FVector::DistSquared(P, Z) < WakeSq) { bWake = true; break; } }
		if (const ASoldierBase* SB = Cast<ASoldierBase>(A)) { if (SB->GetOrderCode() != Wt->Order) { bWake = true; } }
		if (bWake)
		{
			SetAsleep(A, *Wt, false);
			A->SetActorTickEnabled(true);
			GWaiters.Remove(A);
			Idle.RemoveAtSwap(i);
			continue;
		}

		// the hero walks into him: step aside (perpendicular to the hero's path, away from him), then walk back
		APawn* Pawn = Cast<APawn>(A);
		AController* Ctrl = Pawn ? Pawn->GetController() : nullptr;
		if (!Ctrl) { continue; }
		if (Hero && !Wt->bStepping)
		{
			const FVector ToMe = (P - Hero->GetActorLocation()) * FVector(1, 1, 0);
			const FVector HeroVel = Hero->GetVelocity() * FVector(1, 1, 0);
			if (ToMe.Size() < 110.f && HeroVel.Size() > 80.f && FVector::DotProduct(HeroVel.GetSafeNormal(), ToMe.GetSafeNormal()) > 0.3f)
			{
				FVector Away = FVector::CrossProduct(HeroVel.GetSafeNormal(), FVector::UpVector);
				if (FVector::DotProduct(Away, ToMe) < 0.f) { Away = -Away; }
				SetWalking(A, *Wt);
				UAIBlueprintHelperLibrary::SimpleMoveToLocation(Ctrl, P + Away * 140.f);
				Wt->bStepping = true;
				Wt->StepStart = Now;
			}
			continue;
		}
		if (Wt->bStepping)
		{
			const bool bHeroGone = !Hero || FVector::Dist2D(Hero->GetActorLocation(), Wt->Spot) > 260.f;
			if (Now - Wt->StepStart > 1.2f && bHeroGone)
			{
				if (FVector::Dist2D(P, Wt->Spot) > 35.f)
				{
					UAIBlueprintHelperLibrary::SimpleMoveToLocation(Ctrl, Wt->Spot);   // back to his own spot
					if (Now - Wt->StepStart > 12.f) { A->SetActorLocation(Wt->Spot, false, nullptr, ETeleportType::TeleportPhysics); }   // path blocked: settle
				}
				else
				{
					A->SetActorRotation(Wt->Facing);   // face the gate again and wait
					Wt->bStepping = false;
					SetAsleep(A, *Wt, true);
				}
			}
		}
	}
	if (Idle.Num() == 0) { W->GetTimerManager().ClearTimer(WakeTimer); }
}
