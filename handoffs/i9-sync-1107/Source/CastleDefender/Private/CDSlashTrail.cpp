#include "CDSlashTrail.h"
#include "CDHeroGear.h"
#include "ProceduralMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/OverlapResult.h"
#include "InputKeyEventArgs.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "SoldierBase.h"
#include "Engine/LocalPlayer.h"

static TAutoConsoleVariable<int32> CVarTrailSlices(TEXT("cd.Slash.TrailSlices"), 48, TEXT("Slices along the blade trail ribbon. The swing is resampled, so low frame rates still give a smooth arc."));
static TAutoConsoleVariable<float> CVarTrailTipReach(TEXT("cd.Slash.TipReach"), 1.7f, TEXT("How far the ribbon's outer rim reaches, in blade lengths from the grip, for a row of size 1."));
static TAutoConsoleVariable<float> CVarTrailSpan(TEXT("cd.Slash.Span"), 1.4f, TEXT("Ribbon width at the blade, in blade lengths, for a row of size 1."));
static TAutoConsoleVariable<float> CVarTrailSize(TEXT("cd.Slash.Size"), 1.25f, TEXT("Overall ribbon size on top of each sword's own."));
static TAutoConsoleVariable<float> CVarTrailPre(TEXT("cd.Slash.Pre"), 0.12f, TEXT("How far before the hit frame the strike may begin, seconds. Short: before that is the wind-up."));
static TAutoConsoleVariable<float> CVarTrailExtra(TEXT("cd.Slash.ExtraDeg"), 80.f, TEXT("Degrees the arc carries on behind the real strike, along the swing's own axis."));
static TAutoConsoleVariable<float> CVarTrailPost(TEXT("cd.Slash.Post"), 0.25f, TEXT("Seconds after the hit frame the ribbon may keep growing."));
static TAutoConsoleVariable<float> CVarTrailFade(TEXT("cd.Slash.Fade"), 0.32f, TEXT("Seconds the ribbon takes to drain from the tail."));
static TAutoConsoleVariable<float> CVarTrailTurn(TEXT("cd.Slash.Turn"), 85.f, TEXT("A blade path turning more than this many degrees between frames ends the strike (the wind-up or the recovery)."));
static TAutoConsoleVariable<float> CVarTrailGlow(TEXT("cd.Slash.Glow"), 1.f, TEXT("Brightness of the soft halo around the ribbon. 0 = off."));
static TAutoConsoleVariable<int32> CVarTrailSpark(TEXT("cd.Slash.Spark"), 1, TEXT("1 = small spark when a swing really hits an enemy."));

static TAutoConsoleVariable<float> CVarTestAttack(TEXT("cd.Test.AttackEvery"), 0.f, TEXT("Test only: clicks the left mouse button through the player controller every N seconds. 0 = off."));

UStaticMeshComponent* UCDSlashTrailSubsystem::FindWeapon()
{
	UWorld* W = GetWorld();
	if (UStaticMeshComponent* C = Weapon.Get()) { return C; }
	const double Now = W->GetRealTimeSeconds();
	if (Now - WeaponSearchAt < 1.0) { return nullptr; }
	WeaponSearchAt = Now;
	if (APawn* Pawn = UGameplayStatics::GetPlayerPawn(W, 0))
	{
		TArray<UActorComponent*> Tagged = Pawn->GetComponentsByTag(UStaticMeshComponent::StaticClass(), TEXT("KitWeapon"));
		TInlineComponentArray<UStaticMeshComponent*> All(Pawn);
		for (UStaticMeshComponent* M : All) { if (M && M->GetFName() == TEXT("Sword")) { DefaultSword = M; break; } }
		// Ground and wall splats must not paint across the hero.
		TInlineComponentArray<UPrimitiveComponent*> Prims(Pawn);
		for (UPrimitiveComponent* Prim : Prims) { if (Prim) { Prim->SetReceivesDecals(false); } }
		if (Tagged.Num() > 0) { Weapon = Cast<UStaticMeshComponent>(Tagged[0]); }
	}
	return Weapon.Get();
}

void UCDSlashTrailSubsystem::SyncHand(UStaticMeshComponent* Kit)
{
	const UStaticMesh* SM = Kit ? Kit->GetStaticMesh() : nullptr;
	const bool bHolding = SM && Kit->IsVisible();
	if (bHolding)
	{
		// Metre-sized imports are under 5 units long and need x100. Meshes already in centimetres keep x1.
		const double Want = SM->GetBoundingBox().GetSize().Z < 5.0 ? 100.0 : 1.0;
		if (!FMath::IsNearlyEqual(Kit->GetRelativeScale3D().Z, Want, 0.01)) { Kit->SetRelativeScale3D(FVector(Want)); }
	}
	if (UStaticMeshComponent* Old = DefaultSword.Get())
	{
		Old->SetVisibility(!bHolding && UCDHeroGearSubsystem::WeaponWorn(GetWorld())); // 11-07: the default sword stays away while the weapon is in the pack
		// 11-07 owner: the sword did not sit in the hand. The default sword was seated by hand in the editor: same pose, with the middles of the two handles lined up.
		const UStaticMesh* OldMesh = Old->GetStaticMesh();
		if (bHolding && OldMesh)
		{
			const double KitScale = Kit->GetRelativeScale3D().Z;
			const FRotator Rot = Old->GetRelativeRotation();
			const double Shift = (OldMesh->GetBoundingBox().Min.Z - SM->GetBoundingBox().Min.Z * KitScale) * 0.5;
			const FVector Loc = Old->GetRelativeLocation() + Rot.RotateVector(FVector(0.0, 0.0, Shift));
			if (!Kit->GetRelativeLocation().Equals(Loc, 0.01) || !Kit->GetRelativeRotation().Equals(Rot, 0.01)) { Kit->SetRelativeLocationAndRotation(Loc, Rot); }
		}
	}
}

void UCDSlashTrailSubsystem::StartSwing(float WidthMul, float Speed, const FLinearColor& CoreColor, const FLinearColor& EdgeColor, float Intensity)
{
	UWorld* W = GetWorld();
	if (!W) { return; }
	SwingAt = W->GetTimeSeconds();
	Width = FMath::Clamp(WidthMul, 0.3f, 1.6f);
	SpeedMul = FMath::Clamp(Speed, 0.5f, 2.f);
	Pre = CVarTrailPre.GetValueOnGameThread() / SpeedMul;
	Post = CVarTrailPost.GetValueOnGameThread() / SpeedMul;
	Fade = CVarTrailFade.GetValueOnGameThread() / SpeedMul;
	Core = CoreColor; Edge = EdgeColor; BaseIntensity = Intensity;
	StrikeStart = -1.0;

	// The one real hit of this swing: the same place the hero's radial damage just struck. Runs once per swing.
	SparkAt = -100.0;
	APawn* Hero = UGameplayStatics::GetPlayerPawn(W, 0);
	if (Hero && CVarTrailSpark.GetValueOnGameThread() > 0)
	{
		const FVector Origin = Hero->GetActorLocation() + Hero->GetActorForwardVector() * 120.0;
		FCollisionQueryParams Q(SCENE_QUERY_STAT(CDSlashSpark), false, Hero);
		TArray<FOverlapResult> Hits;
		W->OverlapMultiByObjectType(Hits, Origin, FQuat::Identity, FCollisionObjectQueryParams(ECC_Pawn), FCollisionShape::MakeSphere(150.f), Q);
		double Best = TNumericLimits<double>::Max();
		const FVector From = Hero->GetActorLocation();
		for (const FOverlapResult& R : Hits)
		{
			const APawn* P = Cast<APawn>(R.GetActor());
			if (!P || P->IsA<ASoldierBase>()) { continue; }
			const double D = FVector::DistSquared(P->GetActorLocation(), From);
			if (D < Best)
			{
				Best = D;
				SparkAt = SwingAt;
				if (CVarTrailSpark.GetValueOnGameThread() > 1) { UE_LOG(LogTemp, Log, TEXT("cd.Slash.Spark: hit %s"), *P->GetName()); }
				const FVector C = P->GetActorLocation();
				SparkPos = C + (From - C).GetSafeNormal2D() * 35.0 + FVector(0.0, 0.0, 30.0);
			}
		}
	}
}

// The strike starts at the hit frame the montage marks and runs until the blade turns away. Measured at 13 fps: the swing is over in 0.4 s and the tip
// reverses sharply on the wind-up and recovery, so a search around the fastest segment caught the wind-up and drew a V or a flag.
bool UCDSlashTrailSubsystem::FindStrike(double Earliest, double Latest, double& OutStart, double& OutEnd) const
{
	const int32 N = Samples.Num();
	int32 First = INDEX_NONE;
	for (int32 i = 1; i < N && Samples[i].Time <= Latest; ++i)
	{
		if (Samples[i].Time <= SwingAt) { continue; }
		const double Sp = FVector::Dist(Samples[i].Tip(), Samples[i - 1].Tip()) / FMath::Max(1e-4, Samples[i].Time - Samples[i - 1].Time);
		if (Sp > 200.0) { First = i; break; }
	}
	if (First == INDEX_NONE) { return false; }
	const double Turn = FMath::Cos(FMath::DegreesToRadians(double(CVarTrailTurn.GetValueOnGameThread())));
	const FVector Anchor = (Samples[First].Tip() - Samples[First - 1].Tip()).GetSafeNormal();
	FVector Run = Anchor;
	int32 Last = First;
	for (int32 i = First + 1; i < N && Samples[i].Time <= Latest; ++i)
	{
		const FVector Dir = (Samples[i].Tip() - Samples[i - 1].Tip()).GetSafeNormal();
		if (FVector::DotProduct(Dir, Run) < Turn) { break; }
		Last = i; Run = Dir;
	}
	Run = Anchor;
	int32 Begin = First - 1;
	for (int32 i = First - 1; i >= 1 && Samples[i - 1].Time >= Earliest; --i)
	{
		const FVector Dir = (Samples[i].Tip() - Samples[i - 1].Tip()).GetSafeNormal();
		if (FVector::DotProduct(Dir, Run) < Turn) { break; }
		Begin = i - 1; Run = Dir;
	}
	OutStart = Samples[Begin].Time;
	OutEnd = Samples[Last].Time;
	return true;
}

// Game time, not real time: the ribbon has to stay in step with the montage through hit-stop and when a slow frame clamps the time step.
void UCDSlashTrailSubsystem::Tick(float DeltaTime)
{
	UWorld* W = GetWorld();
	if (!W) { return; }
	const double Now = W->GetTimeSeconds();
	APlayerController* PC = W->GetFirstPlayerController();
	if (bTestKeyDown && PC)
	{
		bTestKeyDown = false;
		PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton, IE_Released, 0.f));
	}
	const float AttackEvery = CVarTestAttack.GetValueOnGameThread();
	if (AttackEvery > 0.f && Now >= NextTestAttack && PC)
	{
		// The real left-mouse path: key, mapping context, IA_Attack, then the hero's own graph, montage and notify. Only the OS click is skipped.
		NextTestAttack = Now + AttackEvery;
		const bool bTaken = PC->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton, IE_Pressed, 1.f));
		bTestKeyDown = true;
		const APawn* Hero = PC->GetPawn();
		UE_LOG(LogTemp, Log, TEXT("cd.Test.AttackEvery: click taken %d, hero input enabled %d, cursor %d, paused %d"), bTaken, Hero ? Hero->InputEnabled() : -1, PC->bShowMouseCursor, W->IsPaused());
	}
	if (UStaticMeshComponent* C = FindWeapon())
	{
		SyncHand(C);
		if (const UStaticMesh* SM = C->GetStaticMesh())
		{
			// Kit convention: pivot = grip, blade along +Z. Grip and blade direction are kept apart, so a sample between two frames still has the true blade length.
			const FBox B = SM->GetBoundingBox();
			const FTransform X = C->GetComponentTransform();
			const FVector TipNow = X.TransformPosition(FVector(0, 0, B.Max.Z));
			FSample S;
			S.Grip = X.GetLocation();
			S.Len = FVector::Dist(TipNow, S.Grip);
			S.Dir = S.Len > 1.0 ? (TipNow - S.Grip) / S.Len : FVector::UpVector;
			S.Time = Now;
			Samples.Add(S);
		}
	}
	int32 Old = 0;
	while (Old < Samples.Num() && Now - Samples[Old].Time > 1.2) { ++Old; }
	if (Old > 0) { Samples.RemoveAt(0, Old, EAllowShrinking::No); }

	const double Latest = FMath::Min(Now, SwingAt + Post);
	const double Earliest = SwingAt - Pre;
	const double FadeT = (Now - (SwingAt + Post)) / FMath::Max(0.01f, Fade);
	bool bDrawn = false;
	if (Now >= SwingAt && FadeT < 1.0 && Samples.Num() >= 2)
	{
		double Start, End;
		if (FindStrike(Earliest, Latest, Start, End) && End - Start > 0.005)
		{
			StrikeStart = Start;
			// The real strike is short, so the arc carries on behind it along the same axis, like the swing that led into the cut.
			const FVector D0 = Sample(Start).Dir, D1 = Sample(End).Dir;
			ArcAxis = FVector::CrossProduct(D0, D1).GetSafeNormal();
			const double Angle = FMath::Acos(FMath::Clamp(FVector::DotProduct(D0, D1), -1.0, 1.0));
			ArcRate = Angle / (End - Start);
			const double Extra = (ArcAxis.IsNearlyZero() || ArcRate < 0.5) ? 0.0 : FMath::DegreesToRadians(double(CVarTrailExtra.GetValueOnGameThread())) / ArcRate;
			ArcTotal = Angle + Extra * ArcRate; // radians swept; the ribbon is never wider than 0.6 of its length, or a short early arc reads as a flag
			const double VirtualStart = Start - Extra;
			const double Tail = FMath::Lerp(VirtualStart, End, FMath::Clamp(FadeT, 0.0, 1.0));
			const float Life = float(FMath::Clamp((Now - SwingAt) / FMath::Max(0.01, Post + Fade), 0.0, 1.0));
			Rebuild(Tail, End, FMath::Clamp(float(FadeT), 0.f, 1.f), Life);
			bDrawn = true;
		}
	}
	if (!bDrawn && bVisible && Mesh)
	{
		Mesh->ClearAllMeshSections();
		bVisible = false;
		if (UMaterialParameterCollection* MPC = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/CastleDefender/VFX/SwordSlash/MPC_CDSlash.MPC_CDSlash")))
		{
			UKismetMaterialLibrary::SetScalarParameterValue(W, MPC, TEXT("Intensity"), BaseIntensity);
		}
	}
}

// Hermite in true time through the stored poses. Direction is interpolated and renormalised, so the blade sweeps a real arc between two frames instead of cutting the chord: at 12 fps a swing is only a few samples.
UCDSlashTrailSubsystem::FSample UCDSlashTrailSubsystem::Sample(double T) const
{
	const int32 N = Samples.Num();
	int32 I = 0;
	while (I < N - 2 && Samples[I + 1].Time < T) { ++I; }
	const FSample& P1 = Samples[I]; const FSample& P2 = Samples[I + 1];
	const FSample& P0 = Samples[FMath::Max(I - 1, 0)]; const FSample& P3 = Samples[FMath::Min(I + 2, N - 1)];
	const double H = FMath::Max(1e-4, P2.Time - P1.Time);
	const double U = FMath::Clamp((T - P1.Time) / H, 0.0, 1.0);
	const double U2 = U * U, U3 = U2 * U;
	const double D1 = FMath::Max(1e-4, P2.Time - P0.Time) / H, D2 = FMath::Max(1e-4, P3.Time - P1.Time) / H;
	const auto Herm = [&](const FVector& A, const FVector& B, const FVector& C, const FVector& D)
	{
		const FVector M1 = (C - A) / D1, M2 = (D - B) / D2;
		return (2.0 * U3 - 3.0 * U2 + 1.0) * B + (U3 - 2.0 * U2 + U) * M1 + (-2.0 * U3 + 3.0 * U2) * C + (U3 - U2) * M2;
	};
	FSample Out;
	Out.Grip = Herm(P0.Grip, P1.Grip, P2.Grip, P3.Grip);
	Out.Dir = Herm(P0.Dir, P1.Dir, P2.Dir, P3.Dir).GetSafeNormal();
	Out.Len = FMath::Lerp(P1.Len, P2.Len, U);
	Out.Time = T;
	return Out;
}

void UCDSlashTrailSubsystem::Rebuild(double Tail, double Head, float FadeA, float Life)
{
	UWorld* W = GetWorld();
	if (!Mesh)
	{
		FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn; SP.ObjectFlags |= RF_Transient;
		MeshActor = W->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, SP);
		if (!MeshActor) { return; }
		Mesh = NewObject<UProceduralMeshComponent>(MeshActor, TEXT("BladeTrail"));
		Mesh->bUseAsyncCooking = false;
		Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Mesh->SetCastShadow(false);
		Mesh->bUseComplexAsSimpleCollision = false;
		MeshActor->SetRootComponent(Mesh);
		Mesh->RegisterComponent();
		Material = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/CastleDefender/VFX/SwordSlash/MI_ClassroomSlash_Add.MI_ClassroomSlash_Add"));
		GlowMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/CastleDefender/VFX/SwordSlash/M_CDSlashGlow.M_CDSlashGlow"));
	}
	const int32 Slices = FMath::Clamp(CVarTrailSlices.GetValueOnGameThread(), 6, 64);
	const float SizeMul = CVarTrailSize.GetValueOnGameThread();
	const double TipReach = 1.0 + (CVarTrailTipReach.GetValueOnGameThread() - 1.0) * Width * SizeMul;
	const double Span = FMath::Min(CVarTrailSpan.GetValueOnGameThread() * Width * SizeMul, FMath::Min(TipReach - 0.05, ArcTotal * TipReach * 0.6));  // ribbon width at the blade, in blade lengths; it never crosses the hand

	// 11-07 owner: "the flow is mirrored, the tail and the hard edge". The shader scrolls its noise along U (TexSpeedX), so U runs ALONG the arc and rises towards the tail: the noise flows back from the blade.
	// V runs across: the mask is cut off high up at the rim, which gives the hard outer edge, and falls away softly towards the hilt.
	static const float ColF[] = { 0.f, 0.35f, 0.7f, 0.9f, 1.f };   // 0 = inner edge, 1 = rim
	static const float ColV[] = { 0.92f, 0.8f, 0.62f, 0.42f, 0.28f };
	const int32 NC = UE_ARRAY_COUNT(ColF);
	const int32 NV = (Slices + 1) * NC;
	TArray<FVector> V; TArray<FVector2D> UV; TArray<int32> Tri; TArray<FVector> Nrm; TArray<FLinearColor> Col; TArray<FProcMeshTangent> Tan;
	TArray<FVector> GV; TArray<FVector2D> GUV; TArray<int32> GTri; TArray<FLinearColor> GCol;
	V.Reserve(NV); UV.Reserve(NV); Tri.Reserve(Slices * (NC - 1) * 12);
	const bool bGlow = GlowMaterial && CVarTrailGlow.GetValueOnGameThread() > 0.f;
	const float GlowAmount = CVarTrailGlow.GetValueOnGameThread() * FMath::Square(1.f - Life);
	if (bGlow) { GV.Reserve((Slices + 1) * 3); GUV.Reserve((Slices + 1) * 3); GCol.Reserve((Slices + 1) * 3); GTri.Reserve(Slices * 24); }
	for (int32 i = 0; i <= Slices; ++i)
	{
		const float A = float(i) / Slices;                // 0 = the blade now, 1 = oldest
		const double TA = FMath::Lerp(Head, Tail, double(A));
		FSample S = Sample(FMath::Max(TA, StrikeStart));
		if (TA < StrikeStart) { S.Dir = S.Dir.RotateAngleAxisRad(-ArcRate * (StrikeStart - TA), ArcAxis); }
		const FVector Rim = S.Grip + S.Dir * S.Len * TipReach;
		// Comet shape: full width and hard at the blade, thinning to nothing at the tail. The rim stays on the tip's path.
		const float Taper = FMath::Pow(FMath::Max(0.f, 1.f - FMath::Pow(A, 1.7f)), 0.7f);
		const FVector In = -S.Dir * S.Len * Span * Taper;
		// U starts inside the mask's plateau at the blade, so the head is cut hard, and leaves it about two thirds along, so the tail fades.
		const double UCoord = 0.28 + 0.64 * double(A);
		for (int32 c = 0; c < NC; ++c)
		{
			V.Add(Rim + In * (1.f - ColF[c]));
			UV.Add(FVector2D(UCoord, ColV[c]));
		}
		if (i < Slices)
		{
			for (int32 c = 0; c < NC - 1; ++c)
			{
				const int32 B = i * NC + c, Next = B + NC;
				Tri.Append({ B, B + 1, Next, Next, B + 1, Next + 1 });
				Tri.Append({ B, Next, B + 1, Next, Next + 1, B + 1 });   // the classroom material is one-sided: both windings so it reads from every camera
			}
		}
		if (bGlow)
		{
			// A soft halo a little wider than the ribbon: bright air around the cut, gone quickly.
			const FLinearColor G = (Edge * 0.5f + Core * 0.5f) * (GlowAmount * (1.f - A));
			const FVector Over = S.Dir * S.Len * 0.28 * Taper;
			GV.Add(Rim + In - Over); GV.Add(Rim + In * 0.3); GV.Add(Rim + Over);
			GUV.Add(FVector2D(0.02, 0.5)); GUV.Add(FVector2D(0.5, 0.5)); GUV.Add(FVector2D(0.98, 0.5));
			GCol.Add(G); GCol.Add(G); GCol.Add(G);
			if (i < Slices)
			{
				for (int32 c = 0; c < 2; ++c)
				{
					const int32 B = i * 3 + c, Next = B + 3;
					GTri.Append({ B, B + 1, Next, Next, B + 1, Next + 1 });
					GTri.Append({ B, Next, B + 1, Next, Next + 1, B + 1 });
				}
			}
		}
	}
	Mesh->CreateMeshSection_LinearColor(0, V, Tri, Nrm, UV, Col, Tan, false);
	if (Material) { Mesh->SetMaterial(0, Material); }
	if (bGlow)
	{
		Mesh->CreateMeshSection_LinearColor(1, GV, GTri, Nrm, GUV, GCol, Tan, false);
		Mesh->SetMaterial(1, GlowMaterial);
	}

	// Impact spark: a short star of streaks facing the camera, only on a real hit.
	const double Now = W->GetTimeSeconds();
	const float SparkT = float((Now - SparkAt) / 0.16);
	const APlayerController* PC = W->GetFirstPlayerController();
	if (GlowMaterial && SparkT < 1.f && PC && PC->PlayerCameraManager)
	{
		const FVector Cam = PC->PlayerCameraManager->GetCameraLocation();
		const FVector F = (Cam - SparkPos).GetSafeNormal();
		const FVector X = FVector::CrossProduct(F, FVector::UpVector).GetSafeNormal();
		const FVector Y = FVector::CrossProduct(F, X);
		TArray<FVector> SV; TArray<FVector2D> SUV; TArray<int32> STri; TArray<FLinearColor> SCol;
		const FLinearColor C = (Core + FLinearColor::White * 0.3f) * (0.4f * (1.f - SparkT));
		static const float Ang[] = { 0.3f, 1.25f, 2.1f, 3.3f, 4.2f, 5.3f };
		static const float Lens[] = { 55.f, 30.f, 44.f, 26.f, 50.f, 34.f };
		const float Grow = 0.45f + 0.55f * FMath::Min(1.f, SparkT * 3.f);
		for (int32 k = 0; k < 6; ++k)
		{
			const FVector D = X * FMath::Cos(Ang[k]) + Y * FMath::Sin(Ang[k]);
			const FVector Side = FVector::CrossProduct(F, D) * 5.0;
			const int32 B = SV.Num();
			const FVector End = SparkPos + D * Lens[k] * Grow;
			SV.Add(SparkPos - Side); SV.Add(SparkPos + Side); SV.Add(End - Side * 0.2); SV.Add(End + Side * 0.2);
			SUV.Add(FVector2D(0.1, 0.5)); SUV.Add(FVector2D(0.9, 0.5)); SUV.Add(FVector2D(0.1, 0.95)); SUV.Add(FVector2D(0.9, 0.95));
			SCol.Add(C); SCol.Add(C); SCol.Add(C); SCol.Add(C);
			STri.Append({ B, B + 1, B + 2, B + 2, B + 1, B + 3, B, B + 2, B + 1, B + 2, B + 3, B + 1 });
		}
		Mesh->CreateMeshSection_LinearColor(2, SV, STri, Nrm, SUV, SCol, Tan, false);
		Mesh->SetMaterial(2, GlowMaterial);
	}
	else
	{
		Mesh->ClearMeshSection(2);
	}

	// Bright at the cut, then the whole arc cools as the tail drains.
	if (UMaterialParameterCollection* MPC = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/CastleDefender/VFX/SwordSlash/MPC_CDSlash.MPC_CDSlash")))
	{
		const float Flash = 1.f + 0.4f * FMath::Square(1.f - FMath::Min(1.f, Life * 2.5f));
		UKismetMaterialLibrary::SetScalarParameterValue(W, MPC, TEXT("Intensity"), BaseIntensity * Flash * (1.f - 0.6f * FadeA));
	}
	bVisible = true;
}
