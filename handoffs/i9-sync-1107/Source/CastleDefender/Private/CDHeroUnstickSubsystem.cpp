#include "CDHeroUnstickSubsystem.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/CapsuleComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Kismet/GameplayStatics.h"
#include "CollisionQueryParams.h"
#include "HAL/IConsoleManager.h"

namespace CDUnstick
{
	static int32 GEnable = 1;
	static float GDepth = 300.f;       // cm below the landscape surface above the hero
	static float GSeconds = 3.f;       // how long all three conditions must hold
	static float GMinSpeed = 40.f;     // cm/s: slower than this while pushing a direction = not moving
	static float GSafeAge = 3.f;       // s: use a safe sample at least this old (never the pit's edge)
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.Hero.Unstick"), GEnable, TEXT("1 = hero under the landscape + pushing + not moving for cd.Hero.UnstickSeconds is put back on the last safe ground (#510)."));
	static FAutoConsoleVariableRef CVarDepth(TEXT("cd.Hero.UnstickDepth"), GDepth, TEXT("Centimetres below the landscape surface that count as 'under the ground' (300)."));
	static FAutoConsoleVariableRef CVarSeconds(TEXT("cd.Hero.UnstickSeconds"), GSeconds, TEXT("Seconds the stuck conditions must hold before the teleport (3)."));
	static FAutoConsoleVariableRef CVarSpeed(TEXT("cd.Hero.UnstickMinSpeed"), GMinSpeed, TEXT("Below this horizontal speed (cm/s) while pushing a direction the hero counts as not moving (40)."));
	static FAutoConsoleVariableRef CVarAge(TEXT("cd.Hero.UnstickSafeAge"), GSafeAge, TEXT("The safe-ground sample used is at least this many seconds old (3)."));
	static const int32 RingSize = 16;  // 16 x 0.5 s = 8 s of history

	static bool IsLandscape(const UPrimitiveComponent* C)
	{
		return C && C->GetClass()->GetName().Contains(TEXT("Landscape"));
	}
}

bool UCDHeroUnstickSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* W = Cast<UWorld>(Outer);
	return W && (W->WorldType == EWorldType::Game || W->WorldType == EWorldType::PIE);
}

bool UCDHeroUnstickSubsystem::IsTickable() const
{
	const UWorld* W = GetWorld();
	return W && W->IsGameWorld() && !IsTemplate();
}

bool UCDHeroUnstickSubsystem::UnderLandscape(const ACharacter* Hero, float& OutDepth) const
{
	OutDepth = 0.f;
	const UWorld* W = GetWorld();
	if (!W || !Hero) { return false; }
	const FVector Loc = Hero->GetActorLocation();
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CDUnstick), false, Hero);
	FHitResult Hit;
	// from 40 m above the hero down to his feet: the first blocking thing above him
	const bool bHit = W->LineTraceSingleByChannel(Hit, Loc + FVector(0, 0, 4000.0), Loc, ECC_WorldStatic, Params);
	if (!bHit || !CDUnstick::IsLandscape(Hit.GetComponent())) { return false; }
	float HalfHeight = 90.f;
	if (const UCapsuleComponent* Cap = Hero->GetCapsuleComponent()) { HalfHeight = Cap->GetScaledCapsuleHalfHeight(); }
	OutDepth = static_cast<float>(Hit.ImpactPoint.Z - (Loc.Z - HalfHeight));   // surface above the feet, positive = under the ground
	return OutDepth > CDUnstick::GDepth;
}

bool UCDHeroUnstickSubsystem::PickSafe(FVector& Out) const
{
	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	// newest sample that is at least GSafeAge old; else the oldest we have
	const FSample* Best = nullptr; const FSample* Oldest = nullptr;
	for (const FSample& S : Safe)
	{
		if (S.Time < 0.0) { continue; }
		if (!Oldest || S.Time < Oldest->Time) { Oldest = &S; }
		if (Now - S.Time >= CDUnstick::GSafeAge && (!Best || S.Time > Best->Time)) { Best = &S; }
	}
	const FSample* Use = Best ? Best : Oldest;
	if (!Use) { return false; }
	Out = Use->Location;
	return true;
}

bool UCDHeroUnstickSubsystem::UnstickNow()
{
	ACharacter* Hero = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(GetWorld(), 0));
	FVector Target;
	if (!Hero || !PickSafe(Target)) { UE_LOG(LogTemp, Warning, TEXT("[CD] unstick: no safe ground known yet")); return false; }
	const FVector From = Hero->GetActorLocation();
	if (UCharacterMovementComponent* Move = Hero->GetCharacterMovement()) { Move->StopMovementImmediately(); }
	Hero->SetActorLocation(Target + FVector(0, 0, 20.0), false, nullptr, ETeleportType::TeleportPhysics);
	LastUnstick = GetWorld()->GetTimeSeconds();
	StuckSince = -1.0;
	UE_LOG(LogTemp, Warning, TEXT("[CD] unstick: hero moved from %s back to safe ground %s"), *From.ToCompactString(), *Target.ToCompactString());
	return true;
}

void UCDHeroUnstickSubsystem::Tick(float DeltaTime)
{
	UWorld* W = GetWorld();
	if (!W || !CDUnstick::GEnable) { return; }
	ACharacter* Hero = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(W, 0));
	if (!Hero) { return; }
	UCharacterMovementComponent* Move = Hero->GetCharacterMovement();
	if (!Move) { return; }
	const double Now = W->GetTimeSeconds();
	const FVector Loc = Hero->GetActorLocation();

	// 1. remember safe ground: standing on the landscape, every 0.5 s
	if (Now - LastSampleTime >= 0.5 && Move->IsMovingOnGround() && CDUnstick::IsLandscape(Move->CurrentFloor.HitResult.GetComponent()))
	{
		if (Safe.Num() < CDUnstick::RingSize) { Safe.AddDefaulted(CDUnstick::RingSize); }
		Safe[SafeHead] = { Loc, Now };
		SafeHead = (SafeHead + 1) % CDUnstick::RingSize;
		LastSampleTime = Now;
	}

	// 2. stuck test: under the landscape + pushing a direction + not moving, all together for GSeconds
	const float Speed2D = static_cast<float>(FVector(Loc.X - LastPos.X, Loc.Y - LastPos.Y, 0.0).Size() / FMath::Max(DeltaTime, 1e-3f));
	LastPos = Loc;
	const bool bPushing = !Hero->GetLastMovementInputVector().IsNearlyZero(0.05f);
	float Depth = 0.f;
	const bool bStuck = Now - LastUnstick > 5.0 && bPushing && Speed2D < CDUnstick::GMinSpeed && UnderLandscape(Hero, Depth);
	if (!bStuck) { StuckSince = -1.0; return; }
	if (StuckSince < 0.0) { StuckSince = Now; return; }
	if (Now - StuckSince >= CDUnstick::GSeconds)
	{
		UE_LOG(LogTemp, Warning, TEXT("[CD] unstick: hero %.0f cm under the landscape at %s, pushing but not moving for %.1f s"), Depth, *Loc.ToCompactString(), Now - StuckSince);
		UnstickNow();
	}
}

// console: cd.Hero.UnstickNow = put the hero back on the last safe ground right away (owner's panic button)
static FAutoConsoleCommandWithWorld GCDUnstickNow(TEXT("cd.Hero.UnstickNow"), TEXT("Put the hero back on the last safe landscape spot now (#510)."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* W)
	{
		if (UCDHeroUnstickSubsystem* S = W ? W->GetSubsystem<UCDHeroUnstickSubsystem>() : nullptr) { S->UnstickNow(); }
	}));
