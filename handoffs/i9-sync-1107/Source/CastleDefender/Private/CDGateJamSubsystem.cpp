#include "CDGateJamSubsystem.h"
#include "ZombieBase.h"
#include "CrowdSubsystem.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "Components/PrimitiveComponent.h"
#include "Blueprint/AIBlueprintHelperLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/IConsoleManager.h"

namespace CDGateJam
{
	static int32 GEnable = 1;
	static float GRadius = 1200.f;    // cm around the gate control that count as "at the gate"
	static int32 GMinCount = 4;       // still zombies needed for a jam
	static float GSeconds = 3.f;      // consecutive seconds of jam before acting
	static float GStillSpeed = 15.f;  // cm/s: below this a zombie is standing
	static float GSpread = 350.f;     // half width of the fan of goals across the gateway
	static float GInsideMin = 300.f, GInsideMax = 900.f;   // how far inside the castle the goals lie
	static float GCooldown = 4.f;     // per zombie, between re-routes
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.GateJam"), GEnable, TEXT("1 = break zombie jams at a broken gate (#506): free leftover blockers, fan the goals through the gateway."));
	static FAutoConsoleVariableRef CVarRadius(TEXT("cd.GateJam.Radius"), GRadius, TEXT("Radius (cm) around the gate control that counts as 'at the gate' (1200)."));
	static FAutoConsoleVariableRef CVarMin(TEXT("cd.GateJam.MinCount"), GMinCount, TEXT("Still zombies at the gate needed before it counts as a jam (4)."));
	static FAutoConsoleVariableRef CVarSec(TEXT("cd.GateJam.Seconds"), GSeconds, TEXT("Seconds in a row the jam must hold before the breaker acts (3)."));
	static FAutoConsoleVariableRef CVarSpread(TEXT("cd.GateJam.Spread"), GSpread, TEXT("Half width (cm) of the fan of goals across the gateway (350)."));
	static FAutoConsoleVariableRef CVarCool(TEXT("cd.GateJam.Cooldown"), GCooldown, TEXT("Seconds between re-routes of the same zombie (4)."));

	static bool ClassNameStarts(const AActor* A, const TCHAR* Prefix) { return A && A->GetClass()->GetName().StartsWith(Prefix); }
}

bool UCDGateJamSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* W = Cast<UWorld>(Outer);
	return W && (W->WorldType == EWorldType::Game || W->WorldType == EWorldType::PIE);
}

bool UCDGateJamSubsystem::IsTickable() const
{
	const UWorld* W = GetWorld();
	return W && W->IsGameWorld() && !IsTemplate();
}

void UCDGateJamSubsystem::Refresh()
{
	UWorld* W = GetWorld();
	if (!W) { return; }
	TArray<TWeakObjectPtr<AActor>> Controls;
	WaveManagers.Reset();
	for (TActorIterator<AActor> It(W); It; ++It)
	{
		AActor* A = *It;
		if (CDGateJam::ClassNameStarts(A, TEXT("BP_CastleGateControl"))) { Controls.Add(A); }
		else if (CDGateJam::ClassNameStarts(A, TEXT("BP_ZombieWaveManager"))) { WaveManagers.Add(A); }
	}
	// keep the counters of gates we already know
	TArray<FGate> NewGates;
	for (const TWeakObjectPtr<AActor>& C : Controls)
	{
		FGate* Old = Gates.FindByPredicate([&](const FGate& G) { return G.Control == C; });
		NewGates.Add(Old ? *Old : FGate{ C });
	}
	Gates = MoveTemp(NewGates);
}

bool UCDGateJamSubsystem::IsGateBroken() const
{
	for (const TWeakObjectPtr<AActor>& WM : WaveManagers)
	{
		if (const AActor* A = WM.Get()) { if (AZombieBase::ReadBlueprintBool(A, TEXT("GateBroken"))) { return true; } }
	}
	return false;
}

FVector UCDGateJamSubsystem::Inward(const FVector& GateLoc) const
{
	// into the castle = towards the soldiers (their centroid), else towards the hero
	FVector Sum = FVector::ZeroVector; int32 N = 0;
	if (const UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this))
	{
		Crowd->ForEachSoldier([&](AActor* S) { Sum += S->GetActorLocation(); ++N; });
	}
	FVector To = N > 0 ? Sum / N : FVector::ZeroVector;
	if (N == 0)
	{
		if (const APawn* Hero = UGameplayStatics::GetPlayerPawn(GetWorld(), 0)) { To = Hero->GetActorLocation(); }
		else { return FVector::ForwardVector; }
	}
	FVector Dir = (To - GateLoc); Dir.Z = 0.0;
	return Dir.IsNearlyZero() ? FVector::ForwardVector : Dir.GetSafeNormal();
}

int32 UCDGateJamSubsystem::FreeBlockers(AActor* Control) const
{
	int32 Freed = 0;
	if (!Control) { return 0; }
	TArray<UPrimitiveComponent*> Prims; Control->GetComponents<UPrimitiveComponent>(Prims);
	for (UPrimitiveComponent* P : Prims)
	{
		if (!P || !P->IsCollisionEnabled()) { continue; }
		if (P->GetCollisionResponseToChannel(ECC_Pawn) != ECR_Block) { continue; }
		// a broken gate must not block pawns anywhere: the ZombieStop box, a door leaf that kept its collision, anything
		UE_LOG(LogTemp, Warning, TEXT("[CD] gatejam: %s.%s (%s) still blocks pawns at a broken gate -> collision off"), *Control->GetName(), *P->GetName(), *P->GetClass()->GetName());
		P->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		++Freed;
	}
	return Freed;
}

int32 UCDGateJamSubsystem::Break(FGate& G, bool bForce)
{
	AActor* Control = G.Control.Get();
	UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this);
	if (!Control || !Crowd) { return 0; }
	const double Now = GetWorld()->GetTimeSeconds();
	const FVector GateLoc = Control->GetActorLocation();
	const FVector In = Inward(GateLoc);
	const FVector Right = FVector::CrossProduct(FVector::UpVector, In).GetSafeNormal();
	const int32 Freed = FreeBlockers(Control);

	TArray<AActor*> Near; Crowd->GetZombiesNear(GateLoc, CDGateJam::GRadius, Near);
	int32 RerouteCount = 0, Index = 0;   // (i9 11-06: renamed, it shadowed the Rerouted map and failed the build)
	for (AActor* A : Near)
	{
		AZombieBase* Z = Cast<AZombieBase>(A);
		if (!Z || Z->IsDeadForCrowd() || Z->IsEngagedForCrowd()) { continue; }
		const bool bStill = Z->GetVelocity().SizeSquared2D() < FMath::Square(CDGateJam::GStillSpeed);
		if (!bStill && !bForce) { continue; }
		AController* Ctrl = Z->GetController();
		if (!Ctrl || Ctrl->IsPlayerController()) { continue; }
		if (const double* Last = Rerouted.Find(TWeakObjectPtr<AZombieBase>(Z))) { if (Now - *Last < CDGateJam::GCooldown) { continue; } }
		// fan: alternate left / right across the gateway, deeper for later ones, so no two share a goal
		const float Side = ((Index % 2) ? 1.f : -1.f) * CDGateJam::GSpread * FMath::FRandRange(0.25f, 1.f);
		const float Depth = FMath::Lerp(CDGateJam::GInsideMin, CDGateJam::GInsideMax, FMath::Frac(Index * 0.37f));
		const FVector Goal = GateLoc + Right * Side + In * Depth;
		UAIBlueprintHelperLibrary::SimpleMoveToLocation(Ctrl, Goal);
		Rerouted.Add(Z, Now);
		++RerouteCount; ++Index;
	}
	G.LastBreak = Now;
	G.StillChecks = 0;
	UE_LOG(LogTemp, Warning, TEXT("[CD] gatejam: %s: %d zombies near, %d still -> %d blocker(s) freed, %d re-routed through the gateway%s"),
		*Control->GetName(), Near.Num(), G.LastStill, Freed, RerouteCount, bForce ? TEXT(" (forced)") : TEXT(""));
	return RerouteCount;
}

void UCDGateJamSubsystem::Check(FGate& G)
{
	AActor* Control = G.Control.Get();
	UCrowdSubsystem* Crowd = UCrowdSubsystem::Get(this);
	if (!Control || !Crowd) { return; }
	TArray<AActor*> Near; Crowd->GetZombiesNear(Control->GetActorLocation(), CDGateJam::GRadius, Near);
	int32 Still = 0;
	for (AActor* A : Near)
	{
		const AZombieBase* Z = Cast<AZombieBase>(A);
		if (!Z || Z->IsDeadForCrowd() || Z->IsEngagedForCrowd()) { continue; }
		if (Z->GetVelocity().SizeSquared2D() < FMath::Square(CDGateJam::GStillSpeed)) { ++Still; }
	}
	G.LastNear = Near.Num(); G.LastStill = Still;
	G.StillChecks = Still >= CDGateJam::GMinCount ? G.StillChecks + 1 : 0;
	if (G.StillChecks >= FMath::CeilToInt(CDGateJam::GSeconds)) { Break(G, false); }
}

void UCDGateJamSubsystem::Tick(float DeltaTime)
{
	UWorld* W = GetWorld();
	if (!W || !CDGateJam::GEnable) { return; }
	const double Now = W->GetTimeSeconds();
	if (Now - LastScan > 10.0) { Refresh(); LastScan = Now; }
	if (Now - LastCheck < 1.0) { return; }
	LastCheck = Now;
	if (Gates.Num() == 0 || !IsGateBroken()) { for (FGate& G : Gates) { G.StillChecks = 0; } return; }
	for (FGate& G : Gates) { Check(G); }
	// forget stale re-route stamps
	for (auto It = Rerouted.CreateIterator(); It; ++It) { if (!It.Key().IsValid() || Now - It.Value() > 30.0) { It.RemoveCurrent(); } }
}

FString UCDGateJamSubsystem::Report()
{
	Refresh();
	FString S = FString::Printf(TEXT("gatejam: %d gate control(s), %d wave manager(s), gate broken %d"), Gates.Num(), WaveManagers.Num(), IsGateBroken() ? 1 : 0);
	for (FGate& G : Gates)
	{
		if (!IsGateBroken()) { break; }
		Check(G);
		S += FString::Printf(TEXT(" | %s: near %d still %d checks %d"), G.Control.IsValid() ? *G.Control->GetName() : TEXT("?"), G.LastNear, G.LastStill, G.StillChecks);
	}
	UE_LOG(LogTemp, Display, TEXT("[CD] %s"), *S);
	return S;
}

int32 UCDGateJamSubsystem::BreakJamNow()
{
	Refresh();
	int32 N = 0;
	if (!IsGateBroken()) { UE_LOG(LogTemp, Display, TEXT("[CD] gatejam: the gate is not broken, nothing to break")); return 0; }
	for (FGate& G : Gates) { Check(G); N += Break(G, true); }
	return N;
}

static FAutoConsoleCommandWithWorld GCDGateJamReport(TEXT("cd.GateJam.Report"), TEXT("Gate jam breaker state (#506)."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* W) { if (UCDGateJamSubsystem* S = W ? W->GetSubsystem<UCDGateJamSubsystem>() : nullptr) { S->Report(); } }));
static FAutoConsoleCommandWithWorld GCDGateJamBreak(TEXT("cd.GateJam.BreakNow"), TEXT("Break the zombie jam at every broken gate now (#506)."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* W) { if (UCDGateJamSubsystem* S = W ? W->GetSubsystem<UCDGateJamSubsystem>() : nullptr) { S->BreakJamNow(); } }));
