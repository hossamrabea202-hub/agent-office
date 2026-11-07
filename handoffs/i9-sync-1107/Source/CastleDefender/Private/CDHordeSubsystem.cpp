#include "CDHordeSubsystem.h"
#include "ZombieBase.h"
#include "CDHordeAnimData.h"
#include "CDStats.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/DecalComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/DamageType.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "NavigationSystem.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "UObject/UnrealType.h"
#if WITH_EDITOR
#include "StaticMeshCompiler.h"
#include "TextureCompiler.h"
#endif

CSV_DECLARE_CATEGORY_EXTERN(CastleDefender);

DECLARE_CYCLE_STAT(TEXT("Horde Tick"), STAT_CD_HordeTick, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Horde Move"), STAT_CD_HordeMove, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Horde Combat"), STAT_CD_HordeCombat, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Horde Promotion"), STAT_CD_HordePromotion, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Horde Instances"), STAT_CD_HordeInstances, STATGROUP_CastleDefender);
DECLARE_CYCLE_STAT(TEXT("Horde Flow Build"), STAT_CD_HordeFlow, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("Horde agents alive"), STAT_CD_HordeAlive, STATGROUP_CastleDefender);
DECLARE_DWORD_COUNTER_STAT(TEXT("Horde promoted"), STAT_CD_HordePromoted, STATGROUP_CastleDefender);

namespace CDHorde
{
	static int32 FullBudget = 48;
	static float PromoteRange = 3000.f;
	static float MeltChance = 1.0f;   // 11-06 owner: every zombie death melts (was 0.35)
	static int32 CandleMelt = 1;
	static float MeltSpeed = 120.f;   // cm/s: how fast the melt front spreads from the hit point
	static float MeltCollapse = 1.35f; // s after the start: the sudden full meltdown
	static float MeltDescent = 62.f;   // cm/s: how fast the melt line creeps down inside the front
	static int32 MeltRealZombies = 1;
	static float SoldierDPS = 30.f;
	static float XbowDPS = 15.f;
	static float XbowRange = 2500.f;
	static float TargetRange = 2500.f;
	static int32 Shadows = 1;
	static int32 SwapsPerTick = 4;
	static float FieldExtent = 15000.f;
	static float PoolSeconds = 6.f;

	static FAutoConsoleVariableRef CVarBudget(TEXT("cd.Horde.FullBudget"), FullBudget, TEXT("Most agents shown as real BP_Zombie actors at once (nearest the camera)."));
	static FAutoConsoleVariableRef CVarRange(TEXT("cd.Horde.PromoteRange"), PromoteRange, TEXT("Agents nearer the camera than this (cm) become real zombies, within the budget."));
	static FAutoConsoleVariableRef CVarMelt(TEXT("cd.Horde.MeltChance"), MeltChance, TEXT("Share of deaths that melt into mush and leave a wet pool (0..1)."));
	static FAutoConsoleVariableRef CVarCandle(TEXT("cd.Zombie.CandleMelt"), CandleMelt, TEXT("1 = real zombies melt like a candle from the sword hit outward (material WPO via custom primitive data 8-14), then collapse. 0 = old scale squash."));
	static FAutoConsoleVariableRef CVarMeltSpeed(TEXT("cd.Zombie.MeltSpeed"), MeltSpeed, TEXT("Melt front speed from the hit point (cm/s)."));
	static FAutoConsoleVariableRef CVarMeltDescent(TEXT("cd.Zombie.MeltDescent"), MeltDescent, TEXT("How fast the melt line creeps down inside the front (cm/s)."));
	static FAutoConsoleVariableRef CVarMeltCollapse(TEXT("cd.Zombie.MeltCollapse"), MeltCollapse, TEXT("Seconds after the melt starts until the sudden full collapse."));
	static FAutoConsoleVariableRef CVarMeltReal(TEXT("cd.Horde.MeltRealZombies"), MeltRealZombies, TEXT("1: real BP_Zombie deaths can melt too."));
	static FAutoConsoleVariableRef CVarSDPS(TEXT("cd.Horde.SoldierDPS"), SoldierDPS, TEXT("Damage per second a sword soldier deals to a far agent in reach."));
	static FAutoConsoleVariableRef CVarXDPS(TEXT("cd.Horde.XbowDPS"), XbowDPS, TEXT("Damage per second a crossbow soldier deals to a far agent in range."));
	static FAutoConsoleVariableRef CVarXRange(TEXT("cd.Horde.XbowRange"), XbowRange, TEXT("Crossbow range against agents (cm)."));
	static FAutoConsoleVariableRef CVarTRange(TEXT("cd.Horde.TargetRange"), TargetRange, TEXT("Agents chase a soldier, farmer or the hero within this range (cm), else follow the flow field."));
	static FAutoConsoleVariableRef CVarShadows(TEXT("cd.Horde.Shadows"), Shadows, TEXT("1: crowd instances cast dynamic shadows."));
	static FAutoConsoleVariableRef CVarSwaps(TEXT("cd.Horde.SwapsPerTick"), SwapsPerTick, TEXT("Most promotions and demotions per 0.25 s step (spawn hitch control)."));
	static FAutoConsoleVariableRef CVarExtent(TEXT("cd.Horde.FieldExtent"), FieldExtent, TEXT("Half size of the flow-field square around the goal (cm). Takes effect on the next build."));
	static FAutoConsoleVariableRef CVarPool(TEXT("cd.Horde.PoolSeconds"), PoolSeconds, TEXT("How long a melt pool stays before it fades (s)."));

	static const TCHAR* DataPath = TEXT("/Game/CastleDefender/Horde/DA_HordeZombie.DA_HordeZombie");
	static const TCHAR* ZombiePath = TEXT("/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C");
	static constexpr int32 NumCustom = 6;   // clipStart, clipFrames, clipStartTime, fps (negative = hold last frame), meltStart, tint

	static FProperty* Prop(const UObject* O, FName N) { return O ? O->GetClass()->FindPropertyByName(N) : nullptr; }

	static bool GetBool(const UObject* O, FName N)
	{
		const FBoolProperty* P = CastField<FBoolProperty>(Prop(O, N));
		return P && P->GetPropertyValue_InContainer(O);
	}
	static void SetBool(UObject* O, FName N, bool V)
	{
		if (FBoolProperty* P = CastField<FBoolProperty>(Prop(O, N))) { P->SetPropertyValue_InContainer(O, V); }
	}
	static double GetNum(const UObject* O, FName N, double Default)
	{
		const FNumericProperty* P = CastField<FNumericProperty>(Prop(O, N));
		if (!P) { return Default; }
		const void* Ptr = P->ContainerPtrToValuePtr<void>(O);
		return P->IsFloatingPoint() ? P->GetFloatingPointPropertyValue(Ptr) : double(P->GetSignedIntPropertyValue(Ptr));
	}
	static void SetNum(UObject* O, FName N, double V)
	{
		FNumericProperty* P = CastField<FNumericProperty>(Prop(O, N));
		if (!P) { return; }
		void* Ptr = P->ContainerPtrToValuePtr<void>(O);
		if (P->IsFloatingPoint()) { P->SetFloatingPointPropertyValue(Ptr, V); }
		else { P->SetIntPropertyValue(Ptr, int64(FMath::RoundToInt(V))); }
	}
}

static FAutoConsoleCommandWithWorldAndArgs GCDHordeSpawn(TEXT("cd.Horde.Spawn"), TEXT("cd.Horde.Spawn <count> [radius]: add horde agents (radius 0 = a ring 70-120 m from the goal)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
	{
		if (UCDHordeSubsystem* H = World ? World->GetSubsystem<UCDHordeSubsystem>() : nullptr)
		{
			const int32 N = Args.Num() > 0 ? FCString::Atoi(*Args[0]) : 100;
			const float R = Args.Num() > 1 ? FCString::Atof(*Args[1]) : 0.f;
			const int32 Placed = H->SpawnAgents(N, FVector::ZeroVector, R);
			UE_LOG(LogTemp, Display, TEXT("cd.Horde.Spawn: placed %d of %d"), Placed, N);
		}
	}));
static FAutoConsoleCommandWithWorld GCDHordeClear(TEXT("cd.Horde.Clear"), TEXT("Remove every horde agent and the real zombies standing in for them."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World) { if (UCDHordeSubsystem* H = World ? World->GetSubsystem<UCDHordeSubsystem>() : nullptr) { H->ClearAll(); } }));
static FAutoConsoleCommandWithWorld GCDHordeReport(TEXT("cd.Horde.Report"), TEXT("Horde counts by state, flow field and pools."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World) { if (const UCDHordeSubsystem* H = World ? World->GetSubsystem<UCDHordeSubsystem>() : nullptr) { H->Report(); } }));

UCDHordeSubsystem* UCDHordeSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	return World ? World->GetSubsystem<UCDHordeSubsystem>() : nullptr;
}

bool UCDHordeSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UCDHordeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
}

void UCDHordeSubsystem::Deinitialize()
{
	Agents.Reset();
	RealMelts.Reset();
	Pools.Reset();
	Super::Deinitialize();
}

bool UCDHordeSubsystem::IsTickable() const
{
	return !IsTemplate() && GetWorld() && GetWorld()->HasBegunPlay();
}

TStatId UCDHordeSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UCDHordeSubsystem, STATGROUP_Tickables);
}

bool UCDHordeSubsystem::EnsureAssets()
{
	if (Data && ZombieClass) { return true; }
	if (bAssetsTried) { return false; }
	bAssetsTried = true;
	Data = LoadObject<UCDHordeAnimData>(nullptr, CDHorde::DataPath);
	ZombieClass = LoadClass<ACharacter>(nullptr, CDHorde::ZombiePath);
	if (!Data || !Data->Mesh || !Data->BoneTexture || !ZombieClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("Horde: missing assets (data %d, mesh %d, bones %d, zombie class %d). Run the CDBakeHorde commandlet."),
			Data != nullptr, Data && Data->Mesh, Data && Data->BoneTexture, ZombieClass != nullptr);
		return false;
	}
#if WITH_EDITOR
	// Editor / -game from the editor compiles textures and meshes in the background: until then the texture reports a 32x32 placeholder.
	if (Data->BoneTexture) { FTextureCompilingManager::Get().FinishCompilation({ Data->BoneTexture.Get() }); }
	if (Data->Mesh) { FStaticMeshCompilingManager::Get().FinishCompilation({ Data->Mesh.Get() }); }
#endif
	FString Why;
	if (!Data->IsValidContract(Why))
	{
		UE_LOG(LogTemp, Warning, TEXT("Horde: %s breaks the bake contract: %s"), *Data->GetName(), *Why);
		Data = nullptr;
		return false;
	}
	Data->ClipsForRole(TEXT("Walk"), WalkClips);
	Data->ClipsForRole(TEXT("Run"), RunClips);
	Data->ClipsForRole(TEXT("Attack"), AttackClips);
	Data->ClipsForRole(TEXT("Death"), DeathClips);
	Data->ClipsForRole(TEXT("Idle"), IdleClips);
	if (RunClips.Num() == 0) { RunClips = WalkClips; }
	if (IdleClips.Num() == 0) { IdleClips = WalkClips; }
	if (const ACharacter* CDO = ZombieClass->GetDefaultObject<ACharacter>())
	{
		if (CDO->GetMesh()) { MeshRelative = CDO->GetMesh()->GetRelativeTransform(); }
		if (CDO->GetCapsuleComponent()) { CapsuleHalfHeight = CDO->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(); }
	}
	return WalkClips.Num() > 0 && AttackClips.Num() > 0 && DeathClips.Num() > 0;
}

bool UCDHordeSubsystem::EnsureRenderer()
{
	if (ISM) { return true; }
	if (!EnsureAssets()) { return false; }
	UWorld* World = GetWorld();
	FActorSpawnParameters SP;
	SP.ObjectFlags |= RF_Transient;
	SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	RenderHost = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, SP);
	if (!RenderHost) { return false; }
	ISM = NewObject<UInstancedStaticMeshComponent>(RenderHost, TEXT("HordeISM"), RF_Transient);
	ISM->SetMobility(EComponentMobility::Movable);
	ISM->SetStaticMesh(Data->Mesh);
	for (int32 i = 0; i < Data->Materials.Num(); ++i) { ISM->SetMaterial(i, Data->Materials[i]); }
	ISM->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ISM->SetCanEverAffectNavigation(false);
	ISM->SetCastShadow(CDHorde::Shadows != 0);
	ISM->SetNumCustomDataFloats(CDHorde::NumCustom);
	RenderHost->SetRootComponent(ISM);
	ISM->RegisterComponent();
	return true;
}

int32 UCDHordeSubsystem::AllocAgent()
{
	if (FreeSlots.Num() > 0) { return FreeSlots.Pop(EAllowShrinking::No); }
	const int32 I = Agents.AddDefaulted();
	InstanceXf.Add(FTransform(FQuat::Identity, FVector(0, 0, -100000), FVector(0.001f)));
	CustomData.AddZeroed(CDHorde::NumCustom);
	ISM->AddInstance(InstanceXf[I], true);
	return I;
}

void UCDHordeSubsystem::WriteCustomData(int32 Index, float MeltStart)
{
	const FCDHordeAgent& A = Agents[Index];
	float* C = &CustomData[Index * CDHorde::NumCustom];
	if (Data && Data->Clips.IsValidIndex(A.Clip))
	{
		const FCDHordeClip& Clip = Data->Clips[A.Clip];
		C[0] = float(Clip.StartFrame);
		C[1] = float(Clip.NumFrames);
		C[3] = Clip.bLoop ? Clip.FPS : -Clip.FPS;
	}
	C[4] = MeltStart;
	C[5] = A.Scale > 1.3f ? 1.f : 0.f;
	ISM->SetCustomData(Index, TArrayView<const float>(C, CDHorde::NumCustom), false);
	bCustomDirty = true;
}

void UCDHordeSubsystem::SetClip(int32 Index, const TArray<int32>& Choices, bool bRandomPhase)
{
	if (Choices.Num() == 0 || !Data) { return; }
	FCDHordeAgent& A = Agents[Index];
	const int32 Pick = Choices[FMath::RandRange(0, Choices.Num() - 1)];
	if (Pick == A.Clip && !bRandomPhase) { return; }
	A.Clip = Pick;
	const float Now = GetWorld()->GetTimeSeconds();
	// Random phase so a crowd never walks in step; the material subtracts the start time.
	CustomData[Index * CDHorde::NumCustom + 2] = bRandomPhase ? Now - FMath::FRand() * Data->Clips[Pick].Length() : Now;
	WriteCustomData(Index, CustomData[Index * CDHorde::NumCustom + 4]);
}

int32 UCDHordeSubsystem::SpawnAgents(int32 Count, FVector Center, float Radius, float MaxHP, float AttackDamage, float Speed, bool bRunner, float Scale, int32 ZType)
{
	if (Count <= 0 || !EnsureRenderer()) { return 0; }
	UWorld* World = GetWorld();
	UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (BuildCursor < 0) { BuildCursor = 0; }   // start the flow field now
	int32 Placed = 0;
	for (int32 n = 0; n < Count; ++n)
	{
		FVector P;
		if (Radius <= 0.f)
		{
			const float Ang = FMath::FRand() * 2.f * PI;
			const float Dist = FMath::FRandRange(7000.f, 12000.f);
			P = Goal + FVector(FMath::Cos(Ang) * Dist, FMath::Sin(Ang) * Dist, 0.f);
		}
		else
		{
			P = Center + FVector(FMath::VRand().X, FMath::VRand().Y, 0.f).GetSafeNormal2D() * FMath::Sqrt(FMath::FRand()) * Radius;
		}
		FNavLocation Out;
		if (!Nav || !Nav->ProjectPointToNavigation(P, Out, FVector(600.f, 600.f, 5000.f))) { continue; }
		const int32 I = AllocAgent();
		FCDHordeAgent& A = Agents[I];
		A = FCDHordeAgent();
		A.Scale = Scale;
		A.Pos = Out.Location + FVector(0, 0, CapsuleHalfHeight * Scale);
		A.Yaw = (Goal - A.Pos).Rotation().Yaw;
		A.MaxHP = MaxHP;
		A.HP = MaxHP;
		A.AttackDamage = AttackDamage;
		A.Speed = (bRunner ? 2.f : 1.f) * Speed * FMath::FRandRange(0.85f, 1.15f);
		A.bRunner = bRunner;
		A.ZType = ZType;
		A.State = ECDHordeState::Move;
		A.NextThink = World->GetTimeSeconds() + FMath::FRand() * 0.5f;
		CustomData[I * CDHorde::NumCustom + 4] = 0.f;
		SetClip(I, bRunner ? RunClips : WalkClips, true);
		++NumAlive;
		++Placed;
	}
	return Placed;
}

int32 UCDHordeSubsystem::GetAliveCount() const
{
	return NumAlive;
}

void UCDHordeSubsystem::SetGoal(FVector NewGoal)
{
	Goal = NewGoal;
	bFlowReady = false;
	BuildCursor = Agents.Num() > 0 ? 0 : -1;
}

void UCDHordeSubsystem::ClearAll()
{
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		if (ACharacter* C = Agents[i].Actor.Get()) { C->Destroy(); }
		Agents[i].State = ECDHordeState::Free;
		Agents[i].Actor.Reset();
		InstanceXf[i].SetScale3D(FVector(0.001f));
	}
	FreeSlots.Reset();
	for (int32 i = Agents.Num() - 1; i >= 0; --i) { FreeSlots.Add(i); }
	NumAlive = 0;
	NumPromoted = 0;
	if (ISM) { PushInstances(); }
}

// ---------------------------------------------------------------- flow field

bool UCDHordeSubsystem::CellOf(const FVector& P, int32& OutX, int32& OutY) const
{
	if (Dim <= 0) { return false; }
	OutX = FMath::FloorToInt((P.X - FieldOrigin.X) / CellSize);
	OutY = FMath::FloorToInt((P.Y - FieldOrigin.Y) / CellSize);
	return OutX >= 0 && OutY >= 0 && OutX < Dim && OutY < Dim;
}

void UCDHordeSubsystem::BuildFlowStep(int32 Budget)
{
	CD_SCOPE(STAT_CD_HordeFlow);
	UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	if (!Nav) { return; }
	if (BuildCursor == 0)
	{
		CellSize = 150.f;
		Dim = FMath::Clamp(FMath::CeilToInt(2.f * CDHorde::FieldExtent / CellSize), 16, 600);
		FieldOrigin = Goal - FVector(Dim * CellSize * 0.5f, Dim * CellSize * 0.5f, 0.f);
		CellZ.Init(NAN, Dim * Dim);
		CellCost.Init(TNumericLimits<float>::Max(), Dim * Dim);
		CellDir.Init(FVector2f::ZeroVector, Dim * Dim);
		GDim = FMath::CeilToInt(Dim * CellSize / GridCell);
		GridHead.Init(INDEX_NONE, GDim * GDim);
	}
	const int32 Total = Dim * Dim;
	const int32 End = FMath::Min(Total, BuildCursor + Budget);
	for (int32 c = BuildCursor; c < End; ++c)
	{
		const int32 X = c % Dim, Y = c / Dim;
		const FVector P = FieldOrigin + FVector((X + 0.5f) * CellSize, (Y + 0.5f) * CellSize, 0.f);
		FNavLocation Out;
		if (Nav->ProjectPointToNavigation(FVector(P.X, P.Y, Goal.Z), Out, FVector(CellSize * 0.45f, CellSize * 0.45f, 4000.f)))
		{
			CellZ[c] = Out.Location.Z;
		}
	}
	BuildCursor = End;
	if (BuildCursor >= Total) { SolveFlow(); }
}

void UCDHordeSubsystem::SolveFlow()
{
	CD_SCOPE(STAT_CD_HordeFlow);
	int32 GX, GY;
	if (!CellOf(Goal, GX, GY)) { bFlowReady = false; return; }
	// nearest walkable cell to the goal
	int32 Start = INDEX_NONE;
	float BestD = TNumericLimits<float>::Max();
	for (int32 r = 0; r < 20 && Start == INDEX_NONE; ++r)
	{
		for (int32 y = GY - r; y <= GY + r; ++y)
		for (int32 x = GX - r; x <= GX + r; ++x)
		{
			if (x < 0 || y < 0 || x >= Dim || y >= Dim) { continue; }
			const int32 c = y * Dim + x;
			if (FMath::IsNaN(CellZ[c])) { continue; }
			const float D = FMath::Square(x - GX) + FMath::Square(y - GY);
			if (D < BestD) { BestD = D; Start = c; }
		}
	}
	if (Start == INDEX_NONE) { bFlowReady = false; return; }

	struct FNode { float Cost; int32 Cell; bool operator<(const FNode& O) const { return Cost < O.Cost; } };
	TArray<FNode> Heap;
	CellCost[Start] = 0.f;
	Heap.HeapPush({ 0.f, Start });
	static const int32 DX[8] = { 1, -1, 0, 0, 1, 1, -1, -1 };
	static const int32 DY[8] = { 0, 0, 1, -1, 1, -1, 1, -1 };
	static const float DC[8] = { 1.f, 1.f, 1.f, 1.f, 1.4142f, 1.4142f, 1.4142f, 1.4142f };
	while (Heap.Num() > 0)
	{
		FNode N;
		Heap.HeapPop(N, EAllowShrinking::No);
		if (N.Cost > CellCost[N.Cell]) { continue; }
		const int32 X = N.Cell % Dim, Y = N.Cell / Dim;
		for (int32 k = 0; k < 8; ++k)
		{
			const int32 NX = X + DX[k], NY = Y + DY[k];
			if (NX < 0 || NY < 0 || NX >= Dim || NY >= Dim) { continue; }
			const int32 NC = NY * Dim + NX;
			if (!CanStep(NX, NY, X, Y)) { continue; }   // agents walk from NC toward N.Cell
			const float NewCost = N.Cost + DC[k];
			if (NewCost < CellCost[NC]) { CellCost[NC] = NewCost; Heap.HeapPush({ NewCost, NC }); }
		}
	}
	for (int32 c = 0; c < Dim * Dim; ++c)
	{
		if (CellCost[c] == TNumericLimits<float>::Max() || c == Start) { continue; }
		const int32 X = c % Dim, Y = c / Dim;
		float Best = CellCost[c];
		FVector2f Dir = FVector2f::ZeroVector;
		for (int32 k = 0; k < 8; ++k)
		{
			const int32 NX = X + DX[k], NY = Y + DY[k];
			if (NX < 0 || NY < 0 || NX >= Dim || NY >= Dim) { continue; }
			const int32 NC = NY * Dim + NX;
			if (CellCost[NC] < Best && CanStep(X, Y, NX, NY)) { Best = CellCost[NC]; Dir = FVector2f(float(DX[k]), float(DY[k])); }
		}
		CellDir[c] = Dir.GetSafeNormal();
	}
	bFlowReady = true;
}

FVector2f UCDHordeSubsystem::FlowDir(const FVector& P, float& OutGroundZ, bool& bOutInField) const
{
	int32 X, Y;
	bOutInField = false;
	OutGroundZ = NAN;
	if (!CellOf(P, X, Y)) { return FVector2f(FVector2D(Goal - P).GetSafeNormal()); }
	const int32 c = Y * Dim + X;
	OutGroundZ = CellZ.IsValidIndex(c) ? CellZ[c] : NAN;
	if (!bFlowReady || CellDir[c].IsNearlyZero()) { return FVector2f(FVector2D(Goal - P).GetSafeNormal()); }
	bOutInField = true;
	return CellDir[c];
}

bool UCDHordeSubsystem::CanStep(int32 FX, int32 FY, int32 TX, int32 TY) const
{
	if (FX < 0 || FY < 0 || TX < 0 || TY < 0 || FX >= Dim || FY >= Dim || TX >= Dim || TY >= Dim) { return false; }
	const float ZF = CellZ[FY * Dim + FX], ZT = CellZ[TY * Dim + TX];
	if (FMath::IsNaN(ZF) || FMath::IsNaN(ZT) || FMath::Abs(ZT - ZF) > MaxStepHeight) { return false; }
	if (FX != TX && FY != TY)
	{
		const float Z1 = CellZ[FY * Dim + TX], Z2 = CellZ[TY * Dim + FX];
		if (FMath::IsNaN(Z1) || FMath::IsNaN(Z2) || FMath::Abs(Z1 - ZF) > MaxStepHeight || FMath::Abs(Z2 - ZF) > MaxStepHeight) { return false; }
	}
	return true;
}

bool UCDHordeSubsystem::CanMove(const FVector& From, const FVector& To) const
{
	if (Dim <= 0 || BuildCursor < Dim * Dim || CellZ.Num() != Dim * Dim) { return true; }   // not sampled yet: trust the move
	int32 FX, FY, TX, TY;
	const bool bFrom = CellOf(From, FX, FY), bTo = CellOf(To, TX, TY);
	if (!bFrom && !bTo) { return true; }   // outside the field
	if (bFrom != bTo) { return bTo ? !FMath::IsNaN(CellZ[TY * Dim + TX]) : true; }   // entering the field: only onto walkable ground
	if (FX == TX && FY == TY) { return true; }
	if (FMath::Abs(TX - FX) > 1 || FMath::Abs(TY - FY) > 1) { return false; }   // a step never skips a cell
	return CanStep(FX, FY, TX, TY);
}

// ---------------------------------------------------------------- grid

int32 UCDHordeSubsystem::GridIndex(const FVector& P) const
{
	const int32 X = FMath::Clamp(FMath::FloorToInt((P.X - FieldOrigin.X) / GridCell), 0, GDim - 1);
	const int32 Y = FMath::Clamp(FMath::FloorToInt((P.Y - FieldOrigin.Y) / GridCell), 0, GDim - 1);
	return Y * GDim + X;
}

void UCDHordeSubsystem::RebuildGrid()
{
	if (GDim <= 0)
	{
		// field not started yet: a grid around the goal anyway
		Dim = Dim > 0 ? Dim : FMath::Clamp(FMath::CeilToInt(2.f * CDHorde::FieldExtent / 150.f), 16, 600);
		FieldOrigin = Goal - FVector(Dim * 150.f * 0.5f, Dim * 150.f * 0.5f, 0.f);
		GDim = FMath::CeilToInt(Dim * 150.f / GridCell);
	}
	GridHead.Init(INDEX_NONE, GDim * GDim);
	GridNext.SetNumUninitialized(Agents.Num());
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		const ECDHordeState S = Agents[i].State;
		if (S != ECDHordeState::Move && S != ECDHordeState::Attack) { GridNext[i] = INDEX_NONE; continue; }
		const int32 g = GridIndex(Agents[i].Pos);
		GridNext[i] = GridHead[g];
		GridHead[g] = i;
	}
}

template <typename F>
void UCDHordeSubsystem::ForEachNear(const FVector& P, float Radius, F&& Fn) const
{
	if (GDim <= 0) { return; }
	const int32 R = FMath::Max(1, FMath::CeilToInt(Radius / GridCell));
	const int32 CX = FMath::Clamp(FMath::FloorToInt((P.X - FieldOrigin.X) / GridCell), 0, GDim - 1);
	const int32 CY = FMath::Clamp(FMath::FloorToInt((P.Y - FieldOrigin.Y) / GridCell), 0, GDim - 1);
	for (int32 y = FMath::Max(0, CY - R); y <= FMath::Min(GDim - 1, CY + R); ++y)
	for (int32 x = FMath::Max(0, CX - R); x <= FMath::Min(GDim - 1, CX + R); ++x)
	{
		for (int32 i = GridHead[y * GDim + x]; i != INDEX_NONE; i = GridNext[i]) { Fn(i); }
	}
}

// ---------------------------------------------------------------- passes

void UCDHordeSubsystem::RefreshDefenders()
{
	Defenders.Reset();
	LiveRealZombies.Reset();
	UWorld* World = GetWorld();
	APawn* Player = UGameplayStatics::GetPlayerPawn(World, 0);
	if (!ZombieClass && !bAssetsTried) { ZombieClass = LoadClass<ACharacter>(nullptr, CDHorde::ZombiePath); }   // the melt for real zombies needs no baked data
	for (TActorIterator<ACharacter> It(World); It; ++It)
	{
		ACharacter* C = *It;
		if (!IsValid(C)) { continue; }
		const UClass* Cls = C->GetClass();
		if (ZombieClass && Cls->IsChildOf(ZombieClass))
		{
			if (!SeenDead.Contains(C)) { LiveRealZombies.Add(C); }   // its Dead flag is watched every frame (CheckRealDeaths)
			continue;
		}
		const FString Name = Cls->GetName();
		FDefender D;
		D.Actor = C;
		D.Pos = C->GetActorLocation();
		if (C == Player)
		{
			D.Reach = 0.f; D.DPS = 0.f; D.bRanged = false;   // the hero fights the real zombies near the camera himself
		}
		else if (Name.Contains(TEXT("Soldier")) || Name.Contains(TEXT("Knight")))
		{
			if (C->GetLifeSpan() > 0.01f) { continue; }   // dying soldier (same rule as the zombie brain)
			D.bRanged = Name.Contains(TEXT("Xbow"));
			D.Reach = D.bRanged ? CDHorde::XbowRange : 220.f;
			D.DPS = D.bRanged ? CDHorde::XbowDPS : CDHorde::SoldierDPS;
		}
		else if (Name.Contains(TEXT("Farmer")))
		{
			if (CDHorde::GetBool(C, TEXT("Dead"))) { continue; }
			D.Reach = 0.f; D.DPS = 0.f; D.bRanged = false;
		}
		else
		{
			continue;
		}
		Defenders.Add(D);
	}
	for (auto It = SeenDead.CreateIterator(); It; ++It) { if (!It->IsValid()) { It.RemoveCurrent(); } }
}

void UCDHordeSubsystem::ThinkAndMove(float Dt, float Now)
{
	CD_SCOPE(STAT_CD_HordeMove);
	const float TRangeSq = FMath::Square(CDHorde::TargetRange);
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		FCDHordeAgent& A = Agents[i];
		if (A.State != ECDHordeState::Move && A.State != ECDHordeState::Attack) { continue; }

		// think: pick the nearest defender in range, staggered twice a second
		if (Now >= A.NextThink)
		{
			A.NextThink = Now + 0.5f;
			AActor* Best = nullptr;
			float BestD = TRangeSq;
			for (const FDefender& D : Defenders)
			{
				if (FMath::Abs(D.Pos.Z - A.Pos.Z) > 250.f) { continue; }
				const float DSq = FVector::DistSquared2D(D.Pos, A.Pos);
				if (DSq < BestD) { BestD = DSq; Best = D.Actor.Get(); }
			}
			A.Target = Best;
		}

		AActor* T = A.Target.Get();
		const float Reach = 110.f * A.Scale + 45.f;
		FVector2f Desired;
		float GroundZ;
		bool bInField;
		const FVector2f Flow = FlowDir(A.Pos, GroundZ, bInField);
		if (IsValid(T))
		{
			const FVector TP = T->GetActorLocation();
			const float Dist = FVector::Dist2D(TP, A.Pos);
			const FVector2f ToT = FVector2f(FVector2D(TP - A.Pos).GetSafeNormal());
			if (A.State == ECDHordeState::Attack)
			{
				if (Dist > Reach * 1.6f) { A.State = ECDHordeState::Move; SetClip(i, A.bRunner ? RunClips : WalkClips, true); }
				else { A.Yaw = FMath::RadiansToDegrees(FMath::Atan2(ToT.Y, ToT.X)); A.Vel = FVector2f::ZeroVector; continue; }
			}
			else if (Dist < Reach)
			{
				A.State = ECDHordeState::Attack;
				A.NextAttack = Now + FMath::FRandRange(0.4f, 1.0f);
				SetClip(i, AttackClips, false);
				continue;
			}
			// chase: straight when close, else along the field (walls)
			Desired = (Dist < 1200.f || !bInField) ? ToT : (ToT * 0.4f + Flow * 0.6f).GetSafeNormal();
		}
		else
		{
			if (A.State == ECDHordeState::Attack) { A.State = ECDHordeState::Move; SetClip(i, A.bRunner ? RunClips : WalkClips, true); }
			const float GoalDist = FVector::Dist2D(Goal, A.Pos);
			Desired = GoalDist < 250.f ? FVector2f::ZeroVector : Flow;
		}

		// separation from neighbours
		FVector2f Push = FVector2f::ZeroVector;
		const float SepR = 75.f * A.Scale;
		int32 Seen = 0;
		ForEachNear(A.Pos, SepR, [&](int32 j)
		{
			if (j == i || Seen > 10) { return; }
			const FVector2f D = FVector2f(FVector2D(A.Pos - Agents[j].Pos));
			const float L = D.Size();
			const float R = SepR + 75.f * Agents[j].Scale * 0.5f;
			if (L < R && L > 1.f) { Push += D / L * (R - L) / R; ++Seen; }
		});

		FVector2f V = Desired * A.Speed + Push * 220.f;
		const float VMax = A.Speed * 1.25f;
		if (V.SizeSquared() > VMax * VMax) { V = V.GetSafeNormal() * VMax; }
		A.Vel = FMath::Lerp(A.Vel, V, FMath::Min(1.f, Dt * 6.f));

		// every step obeys the flow-field rules (walls, ledges, corners), also while chasing a target straight on
		FVector Next = A.Pos + FVector(A.Vel.X, A.Vel.Y, 0.f) * Dt;
		if (!CanMove(A.Pos, Next))
		{
			const FVector NX(Next.X, A.Pos.Y, A.Pos.Z), NY(A.Pos.X, Next.Y, A.Pos.Z);
			const FVector NF = A.Pos + FVector(Flow.X, Flow.Y, 0.f) * A.Speed * Dt;   // blocked chase: fall back to the field
			Next = CanMove(A.Pos, NX) ? NX : (CanMove(A.Pos, NY) ? NY : (CanMove(A.Pos, NF) ? NF : A.Pos));
			if (Next == A.Pos) { A.Vel = FVector2f::ZeroVector; }
		}
		float NZ;
		bool bF;
		FlowDir(Next, NZ, bF);
		if (!FMath::IsNaN(NZ)) { Next.Z = FMath::FInterpTo(A.Pos.Z, NZ + CapsuleHalfHeight * A.Scale, Dt, 10.f); }
		A.Pos = Next;
		if (A.Vel.SizeSquared() > 100.f)
		{
			const float TargetYaw = FMath::RadiansToDegrees(FMath::Atan2(A.Vel.Y, A.Vel.X));
			A.Yaw = FMath::FixedTurn(A.Yaw, TargetYaw, 360.f * Dt);
		}
	}
}

void UCDHordeSubsystem::Kill(int32 Index, float Now)
{
	FCDHordeAgent& A = Agents[Index];
	--NumAlive;
	A.StateTime = 0.f;
	A.NextAttack = 0.f;   // reused as "pool spawned" flag while melting
	A.Vel = FVector2f::ZeroVector;
	if (FMath::FRand() < CDHorde::MeltChance)
	{
		A.State = ECDHordeState::Melting;
		WriteCustomData(Index, Now);
	}
	else
	{
		A.State = ECDHordeState::Dying;
		SetClip(Index, DeathClips, false);
	}
}

void UCDHordeSubsystem::Combat(float Dt, float Now)
{
	CD_SCOPE(STAT_CD_HordeCombat);
	// agents bite
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		FCDHordeAgent& A = Agents[i];
		if (A.State != ECDHordeState::Attack || Now < A.NextAttack) { continue; }
		A.NextAttack = Now + 1.6f;
		if (AActor* T = A.Target.Get())
		{
			UGameplayStatics::ApplyDamage(T, A.AttackDamage, nullptr, nullptr, UDamageType::StaticClass());
		}
	}
	// soldiers cut and shoot, four times a second
	CombatAccum += Dt;
	if (CombatAccum < 0.25f) { return; }
	const float Step = CombatAccum;
	CombatAccum = 0.f;
	for (const FDefender& D : Defenders)
	{
		if (D.DPS <= 0.f || !D.Actor.IsValid()) { continue; }
		const FVector P = D.Actor->GetActorLocation();
		int32 Best = INDEX_NONE;
		float BestD = FMath::Square(D.Reach);
		ForEachNear(P, D.Reach, [&](int32 j)
		{
			const FCDHordeAgent& A = Agents[j];
			if (A.HP <= 0.f || FMath::Abs(A.Pos.Z - P.Z) > 300.f) { return; }
			const float DSq = FVector::DistSquared2D(A.Pos, P);
			if (DSq < BestD) { BestD = DSq; Best = j; }
		});
		if (Best != INDEX_NONE)
		{
			Agents[Best].HP -= D.DPS * Step;
			if (Agents[Best].HP <= 0.f) { Kill(Best, Now); }
		}
	}
}

int32 UCDHordeSubsystem::ApplyRadialDamageToAgents(FVector Origin, float Radius, float Damage)
{
	if (GridHead.Num() == 0) { return 0; }
	const float Now = GetWorld()->GetTimeSeconds();
	TArray<int32> Hit;
	ForEachNear(Origin, Radius, [&](int32 j)
	{
		if (Agents[j].HP > 0.f && FVector::DistSquared(Agents[j].Pos, Origin) < Radius * Radius) { Hit.Add(j); }
	});
	for (int32 j : Hit)
	{
		Agents[j].HP -= Damage;
		if (Agents[j].HP <= 0.f) { Kill(j, Now); }
	}
	return Hit.Num();
}

void UCDHordeSubsystem::Promote(int32 Index)
{
	FCDHordeAgent& A = Agents[Index];
	UWorld* World = GetWorld();
	FActorSpawnParameters SP;
	SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	ACharacter* C = World->SpawnActor<ACharacter>(ZombieClass, A.Pos + FVector(0, 0, 5.f), FRotator(0.f, A.Yaw, 0.f), SP);
	if (!C) { A.PromoteCooldown = World->GetTimeSeconds() + 2.f; return; }
	// same order as the wave manager: spawn, then the type values, then ResumeMove
	C->SetActorScale3D(FVector(A.Scale));
	if (UCharacterMovementComponent* M = C->GetCharacterMovement()) { M->MaxWalkSpeed = A.Speed; }
	for (int32 m = 0; m < A.ActorMaterials.Num(); ++m) { if (A.ActorMaterials[m]) { C->GetMesh()->SetMaterial(m, A.ActorMaterials[m]); } }
	CDHorde::SetNum(C, TEXT("ZType"), A.ZType);
	CDHorde::SetBool(C, TEXT("Runner"), A.bRunner);
	CDHorde::SetNum(C, TEXT("MaxHP"), A.MaxHP);
	CDHorde::SetNum(C, TEXT("AttackDamage"), A.AttackDamage);
	CDHorde::SetNum(C, TEXT("XPValue"), A.XPValue);
	CDHorde::SetNum(C, TEXT("DamageTaken"), FMath::Max(0.f, A.MaxHP - A.HP));
	if (UFunction* F = C->FindFunction(TEXT("ResumeMove")))
	{
		if (F->NumParms == 0) { C->ProcessEvent(F, nullptr); }
	}
	A.Actor = C;
	A.State = ECDHordeState::Promoted;
	InstanceXf[Index].SetScale3D(FVector(0.001f));
	++NumPromoted;
}

void UCDHordeSubsystem::Demote(int32 Index)
{
	FCDHordeAgent& A = Agents[Index];
	ACharacter* C = A.Actor.Get();
	if (!C) { return; }
	A.MaxHP = float(CDHorde::GetNum(C, TEXT("MaxHP"), A.MaxHP));
	A.HP = A.MaxHP - float(CDHorde::GetNum(C, TEXT("DamageTaken"), 0.0));
	A.AttackDamage = float(CDHorde::GetNum(C, TEXT("AttackDamage"), A.AttackDamage));
	A.XPValue = float(CDHorde::GetNum(C, TEXT("XPValue"), A.XPValue));
	A.ZType = int32(CDHorde::GetNum(C, TEXT("ZType"), A.ZType));
	A.bRunner = CDHorde::GetBool(C, TEXT("Runner"));
	if (const UCharacterMovementComponent* M = C->GetCharacterMovement()) { A.Speed = M->MaxWalkSpeed; }
	A.Scale = float(C->GetActorScale3D().X);
	A.ActorMaterials.Reset();
	if (USkeletalMeshComponent* Mesh = C->GetMesh())
	{
		for (int32 m = 0; m < Mesh->GetNumMaterials(); ++m) { A.ActorMaterials.Add(Mesh->GetMaterial(m)); }
	}
	A.Pos = C->GetActorLocation();
	A.Yaw = C->GetActorRotation().Yaw;
	A.Actor.Reset();
	C->Destroy();
	--NumPromoted;
	if (A.HP <= 0.f) { A.State = ECDHordeState::Free; FreeSlots.Add(Index); --NumAlive; return; }
	A.State = ECDHordeState::Move;
	A.Vel = FVector2f::ZeroVector;
	A.PromoteCooldown = GetWorld()->GetTimeSeconds() + 2.f;
	A.NextThink = 0.f;
	SetClip(Index, A.bRunner ? RunClips : WalkClips, true);
}

void UCDHordeSubsystem::UpdatePromotion(float Now)
{
	CD_SCOPE(STAT_CD_HordePromotion);
	// keep promoted agents in step with their actors; handle their deaths
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		FCDHordeAgent& A = Agents[i];
		if (A.State != ECDHordeState::Promoted) { continue; }
		ACharacter* C = A.Actor.Get();
		if (!IsValid(C))
		{
			A.State = ECDHordeState::Free; A.Actor.Reset(); FreeSlots.Add(i); --NumAlive; --NumPromoted;
			continue;
		}
		A.Pos = C->GetActorLocation();
		if (CDHorde::GetBool(C, TEXT("Dead")))
		{
			// the Blueprint plays its own death (montage, lifespan); the melt roll happens in RefreshDefenders like any real zombie
			A.State = ECDHordeState::Free; A.Actor.Reset(); FreeSlots.Add(i); --NumAlive; --NumPromoted;
		}
	}
	if (Now < NextPromotion) { return; }
	NextPromotion = Now + 0.25f;

	TArray<int32> Near;
	const float RangeSq = FMath::Square(CDHorde::PromoteRange);
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		FCDHordeAgent& A = Agents[i];
		if (A.State != ECDHordeState::Move && A.State != ECDHordeState::Attack && A.State != ECDHordeState::Promoted) { continue; }
		A.CamDistSq = FVector::DistSquared(A.Pos, CameraPos);
		if (A.CamDistSq < RangeSq * 1.56f) { Near.Add(i); }   // 1.25x range: hysteresis for demotion
	}
	Near.Sort([this](int32 L, int32 R) { return Agents[L].CamDistSq < Agents[R].CamDistSq; });
	const int32 Budget = FMath::Max(0, CDHorde::FullBudget);

	// WantedOrder keeps the nearest-first order for promotion; Wanted is only for membership tests.
	TArray<int32> WantedOrder;
	TSet<int32> Wanted;
	for (int32 k = 0; k < Near.Num() && WantedOrder.Num() < Budget; ++k)
	{
		const FCDHordeAgent& A = Agents[Near[k]];
		if (A.State == ECDHordeState::Promoted || A.CamDistSq < RangeSq) { WantedOrder.Add(Near[k]); Wanted.Add(Near[k]); }
	}
	int32 Swaps = 0;
	// demote first, to make room
	for (int32 i = 0; i < Agents.Num() && Swaps < CDHorde::SwapsPerTick; ++i)
	{
		FCDHordeAgent& A = Agents[i];
		if (A.State != ECDHordeState::Promoted || Wanted.Contains(i)) { continue; }
		ACharacter* C = A.Actor.Get();
		if (!C || CDHorde::GetBool(C, TEXT("Attacking")) || CDHorde::GetBool(C, TEXT("Staggered")) || C->WasRecentlyRendered(0.5f) && A.CamDistSq < RangeSq * 1.56f) { continue; }
		Demote(i);
		++Swaps;
	}
	for (int32 i : WantedOrder)
	{
		if (Swaps >= CDHorde::SwapsPerTick || NumPromoted >= Budget) { break; }
		FCDHordeAgent& A = Agents[i];
		if (A.State == ECDHordeState::Promoted || Now < A.PromoteCooldown) { continue; }
		Promote(i);
		++Swaps;
	}
}

void UCDHordeSubsystem::SpawnMeltPool(const FVector& GroundLocation, float Radius, float Yaw)
{
	if (!Data || !Data->MeltPoolDecal) { return; }
	UWorld* World = GetWorld();
	FVector Loc = GroundLocation;
	FHitResult Hit;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(HordePool), false);
	if (World->LineTraceSingleByChannel(Hit, Loc + FVector(0, 0, 150), Loc - FVector(0, 0, 400), ECC_Visibility, Q)) { Loc = Hit.ImpactPoint; }
	UDecalComponent* D = UGameplayStatics::SpawnDecalAtLocation(World, Data->MeltPoolDecal, FVector(60.f, Radius * 0.3f, Radius * 0.3f), Loc, FRotator(-90.f, Yaw, 0.f), CDHorde::PoolSeconds + 3.f);
	if (!D) { return; }
	D->SetFadeOut(CDHorde::PoolSeconds, 3.f, false);
	D->SetFadeScreenSize(0.002f);
	if (Pools.Num() >= 64)
	{
		if (UDecalComponent* Old = Pools[0].Decal.Get()) { Old->DestroyComponent(); }
		Pools.RemoveAt(0);
	}
	Pools.Add({ D, 0.f, Radius });
}

void UCDHordeSubsystem::UpdateDeaths(float Dt, float Now)
{
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		FCDHordeAgent& A = Agents[i];
		if (A.State == ECDHordeState::Melting)
		{
			A.StateTime += Dt;
			if (A.NextAttack == 0.f && A.StateTime > 0.7f)
			{
				A.NextAttack = 1.f;
				SpawnMeltPool(A.Pos - FVector(0, 0, CapsuleHalfHeight * A.Scale), 115.f * A.Scale, FMath::FRand() * 360.f);
			}
			if (A.StateTime > 2.0f) { A.State = ECDHordeState::Free; FreeSlots.Add(i); WriteCustomData(i, 0.f); }
		}
		else if (A.State == ECDHordeState::Dying)
		{
			A.StateTime += Dt;
			const float L = Data && Data->Clips.IsValidIndex(A.Clip) ? Data->Clips[A.Clip].Length() : 2.f;
			if (A.StateTime > L + 2.5f) { A.Pos.Z -= 45.f * Dt; }   // sink into the ground
			if (A.StateTime > L + 4.5f) { A.State = ECDHordeState::Free; FreeSlots.Add(i); }
		}
	}
	for (int32 p = Pools.Num() - 1; p >= 0; --p)
	{
		FPool& P = Pools[p];
		UDecalComponent* D = P.Decal.Get();
		if (!D) { Pools.RemoveAt(p); continue; }
		P.Age += Dt;
		if (P.Age < 1.2f)
		{
			const float S = FMath::InterpEaseOut(0.3f, 1.f, P.Age / 1.2f, 2.f);   // the mush spreads out
			D->DecalSize = FVector(60.f, P.Radius * S, P.Radius * S);
			D->MarkRenderStateDirty();
		}
	}
}

void UCDHordeSubsystem::CheckRealDeaths()
{
	// BP_Zombie sets Dead, plays its death montage and calls SetLifeSpan(6): the melt (0.15 s delay + 1.9 s) ends well inside that.
	const bool bMeltReal = CDHorde::MeltRealZombies != 0 && CDHorde::MeltChance > 0.f;
	for (int32 k = LiveRealZombies.Num() - 1; k >= 0; --k)
	{
		ACharacter* C = LiveRealZombies[k].Get();
		if (!IsValid(C)) { LiveRealZombies.RemoveAtSwap(k); continue; }
		if (!CDHorde::GetBool(C, TEXT("Dead"))) { continue; }
		LiveRealZombies.RemoveAtSwap(k);
		SeenDead.Add(C);
		if (bMeltReal && C->GetMesh() && FMath::FRand() < CDHorde::MeltChance)
		{
			RealMelts.Add({ C, -0.15f, C->GetMesh()->GetRelativeScale3D(), false });
		}
	}
}

void UCDHordeSubsystem::UpdateRealMelts(float Dt)
{
	for (int32 k = RealMelts.Num() - 1; k >= 0; --k)
	{
		FRealMelt& M = RealMelts[k];
		ACharacter* C = M.Actor.Get();
		USkeletalMeshComponent* Mesh = C ? C->GetMesh() : nullptr;
		if (!Mesh) { RealMelts.RemoveAt(k); continue; }
		M.T += Dt;
		if (M.T < 0.f) { continue; }
		if (CDHorde::CandleMelt)
		{
			// Candle melt (owner, 11-06): the material's WPO reads custom primitive data 8..14 = melt start (game time), hit point xyz,
			// ground z, collapse time, front speed. The front spreads from the sword's hit point; the flesh inside it flows down and
			// out; at MeltCollapse the rest slumps into the pool. Written once; the shader does the rest (MF_CD_CandleMelt).
			if (M.T - Dt < 0.f)
			{
				const AZombieBase* Z = Cast<AZombieBase>(C);
				const FVector Hit = Z ? Z->GetLastHitPoint() : C->GetActorLocation() + FVector(0, 0, 30.f);
				const float GroundZ = float(C->GetActorLocation().Z - C->GetSimpleCollisionHalfHeight());
				// colossi (scaled zombies): the front runs faster and the collapse waits longer, so the whole body melts before it slumps
				const float Scale = FMath::Clamp(float(C->GetActorScale3D().GetAbsMax()), 0.5f, 6.f);
				const float Height = 2.f * C->GetSimpleCollisionHalfHeight();   // the real body height: colossi are 5x
				const float V[10] = { 0.f, float(Hit.X), float(Hit.Y), float(Hit.Z), GroundZ, CDHorde::MeltCollapse * (0.6f + 0.4f * Scale), CDHorde::MeltSpeed * Scale, CDHorde::MeltDescent * Scale, Height, 7319.f };
				for (int32 i = 0; i < 10; ++i) { Mesh->SetCustomPrimitiveDataFloat(8 + i, V[i]); }
			}
			Mesh->SetCustomPrimitiveDataFloat(8, FMath::Max(M.T, 0.001f));   // elapsed melt seconds, every frame (the shader does not trust the Time node)
			if (!M.bPool && M.T > 0.25f)
			{
				M.bPool = true;
				SpawnMeltPool(C->GetActorLocation() - FVector(0, 0, C->GetSimpleCollisionHalfHeight()), 95.f * float(C->GetActorScale3D().X), FMath::FRand() * 360.f);
			}
			const float CollapseAt = CDHorde::MeltCollapse * (0.6f + 0.4f * FMath::Clamp(float(C->GetActorScale3D().GetAbsMax()), 0.5f, 6.f));
			if (M.T > CollapseAt + 0.05f && M.T - Dt <= CollapseAt + 0.05f)
			{
				SpawnMeltPool(C->GetActorLocation() - FVector(0, 0, C->GetSimpleCollisionHalfHeight()), 150.f * float(C->GetActorScale3D().X), FMath::FRand() * 360.f);
			}
			if (M.T > CollapseAt + 0.9f)
			{
				Mesh->SetVisibility(false, true);
				RealMelts.RemoveAt(k);
			}
			continue;
		}
		const float m = FMath::Clamp(M.T / 1.6f, 0.f, 1.f);
		const float e = m * m * (3.f - 2.f * m);
		// slump and spread: the body sags into its own puddle
		Mesh->SetRelativeScale3D(M.BaseScale * FVector(1.f + 0.45f * e, 1.f + 0.45f * e, FMath::Max(0.04f, 1.f - 0.96f * e)));
		if (!M.bPool && m > 0.45f)
		{
			M.bPool = true;
			SpawnMeltPool(C->GetActorLocation() - FVector(0, 0, C->GetSimpleCollisionHalfHeight()), 125.f * float(C->GetActorScale3D().X), FMath::FRand() * 360.f);
		}
		if (M.T > 1.9f)
		{
			Mesh->SetVisibility(false, true);
			RealMelts.RemoveAt(k);
		}
	}
}

void UCDHordeSubsystem::PushInstances()
{
	CD_SCOPE(STAT_CD_HordeInstances);
	for (int32 i = 0; i < Agents.Num(); ++i)
	{
		const FCDHordeAgent& A = Agents[i];
		if (A.State == ECDHordeState::Free || A.State == ECDHordeState::Promoted)
		{
			InstanceXf[i].SetScale3D(FVector(0.001f));
			continue;
		}
		const FTransform Body(FRotator(0.f, A.Yaw, 0.f), A.Pos, FVector(A.Scale));
		InstanceXf[i] = MeshRelative * Body;
	}
	if (InstanceXf.Num() > 0) { ISM->BatchUpdateInstancesTransforms(0, InstanceXf, true, true, false); }
	if (bCustomDirty) { ISM->MarkRenderStateDirty(); bCustomDirty = false; }
}

void UCDHordeSubsystem::Tick(float DeltaTime)
{
	CD_SCOPE(STAT_CD_HordeTick);
	UWorld* World = GetWorld();
	const float Now = World->GetTimeSeconds();
	const float Dt = FMath::Min(DeltaTime, 0.1f);

	if (Now >= NextDefenderRefresh)
	{
		NextDefenderRefresh = Now + 0.5f;
		RefreshDefenders();
	}
	CheckRealDeaths();
	UpdateRealMelts(Dt);
	if (Agents.Num() == 0 && Pools.Num() == 0) { return; }

	if (APlayerCameraManager* Cam = UGameplayStatics::GetPlayerCameraManager(World, 0)) { CameraPos = Cam->GetCameraLocation(); }
	if (BuildCursor >= 0 && BuildCursor < Dim * Dim || BuildCursor == 0) { BuildFlowStep(800); }

	RebuildGrid();
	ThinkAndMove(Dt, Now);
	Combat(Dt, Now);
	UpdateDeaths(Dt, Now);
	UpdatePromotion(Now);
	if (ISM) { PushInstances(); }

	SET_DWORD_STAT(STAT_CD_HordeAlive, NumAlive);
	SET_DWORD_STAT(STAT_CD_HordePromoted, NumPromoted);
	CSV_CUSTOM_STAT(CastleDefender, HordeAgents, NumAlive, ECsvCustomStatOp::Set);
	CSV_CUSTOM_STAT(CastleDefender, HordePromoted, NumPromoted, ECsvCustomStatOp::Set);
}

void UCDHordeSubsystem::Report() const
{
	int32 Counts[6] = { 0 };
	for (const FCDHordeAgent& A : Agents) { ++Counts[FMath::Clamp(int32(A.State), 0, 5)]; }
	UE_LOG(LogTemp, Display, TEXT("cd.Horde.Report: alive %d | move %d attack %d dying %d melting %d promoted %d free %d | slots %d | field %s %dx%d (sampled %d) | defenders %d | pools %d | real melts %d"),
		NumAlive, Counts[0], Counts[1], Counts[2], Counts[3], Counts[4], Counts[5], Agents.Num(),
		bFlowReady ? TEXT("ready") : TEXT("building"), Dim, Dim, FMath::Max(0, BuildCursor), Defenders.Num(), Pools.Num(), RealMelts.Num());
}
