#include "CDSlashFX.h"
#include "CDWeaponPerks.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "CDSlashTrail.h"
#include "NiagaraSystem.h"
#include "TimerManager.h"
#include "UObject/StrongObjectPtr.h"

DEFINE_LOG_CATEGORY_STATIC(LogCDSlash, Log, All);

static TAutoConsoleVariable<int32> CVarSlashEnable(TEXT("cd.Slash.Enable"), 1, TEXT("1 = swords play their own slash, 0 = the old slash for every weapon."));
static TAutoConsoleVariable<int32> CVarSlashDebugRow(TEXT("cd.Slash.DebugRow"), -1, TEXT("Test only: preview this kit row's slash look whatever is equipped. -1 = off."));
static TAutoConsoleVariable<float> CVarSlashIntensity(TEXT("cd.Slash.IntensityMul"), 0.8f, TEXT("Multiplies the brightness of every sword slash."));
static TAutoConsoleVariable<float> CVarSlashEdgeMul(TEXT("cd.Slash.EdgeMul"), 0.5f, TEXT("Lowers each row's shader cut-off, so the whole ribbon shows instead of thin streaks. 1 = the row's own value."));
static TAutoConsoleVariable<float> CVarSlashNoiseFloor(TEXT("cd.Slash.NoiseFloor"), 0.3f, TEXT("Smallest NoiseFlat any row gets. The Voronoi still breaks the ribbon up, but no longer eats it."));
static TAutoConsoleVariable<float> CVarSlashScale(TEXT("cd.Slash.ScaleMul"), 1.f, TEXT("Multiplies the size of every sword slash."));

namespace
{
	struct FSlashLook
	{
		int32 KitIndex;
		const TCHAR* Name;
		FLinearColor Core;   // the bright centre of the arc
		FLinearColor Edge;   // the fading outer colour
		float Intensity;     // HDR brightness
		float NoiseFlat;     // 0 = fully broken up by the Voronoi, 1 = a clean ribbon
		float EdgeMin;       // arc width: a lower min and wider gap make a broader blade of light
		float EdgeMax;
		float Scale;         // arc size
		float RollBias;      // tilts the arc, added to the swing's own roll
		float Speed;         // effect playback speed, higher reads as a quicker, lighter weapon
		int32 Layers;        // 1 to 3 trailing arcs per swing
	};

	// Rows match BPC_WeaponKit (0 to 8 and 25 are the swords).
	const FSlashLook GSlashes[] = {
		{ 0,  TEXT("Arming Sword"),  FLinearColor(1.00f, 1.00f, 1.00f), FLinearColor(0.45f, 0.60f, 0.85f), 5.f,  0.55f, 0.50f, 0.70f, 1.00f,   0.f, 1.00f, 1 }, // clean steel
		{ 1,  TEXT("Viking Sword"),  FLinearColor(0.80f, 0.95f, 1.00f), FLinearColor(0.05f, 0.40f, 1.00f), 6.f,  0.15f, 0.45f, 0.70f, 1.05f,   8.f, 1.00f, 2 }, // cracked frost
		{ 2,  TEXT("Falchion"),      FLinearColor(1.00f, 0.85f, 0.40f), FLinearColor(1.00f, 0.35f, 0.03f), 7.f,  0.10f, 0.40f, 0.60f, 1.15f, -10.f, 0.95f, 1 }, // wide amber crescent
		{ 3,  TEXT("Messer"),        FLinearColor(1.00f, 0.95f, 0.75f), FLinearColor(1.00f, 0.45f, 0.10f), 6.f,  0.00f, 0.50f, 0.70f, 1.20f,   5.f, 1.15f, 2 }, // 11-07: the shader defaults the owner built, no more green
		{ 4,  TEXT("Katzbalger"),    FLinearColor(1.00f, 0.80f, 0.20f), FLinearColor(0.90f, 0.03f, 0.05f), 7.f,  0.40f, 0.50f, 0.70f, 1.00f,  -6.f, 1.10f, 2 }, // landsknecht red and gold
		{ 5,  TEXT("Rondel Dagger"), FLinearColor(0.95f, 0.70f, 1.00f), FLinearColor(0.45f, 0.05f, 1.00f), 7.f,  0.70f, 0.62f, 0.78f, 0.60f,  15.f, 1.50f, 2 }, // small quick violet flicks
		{ 6,  TEXT("Longsword"),     FLinearColor(1.00f, 0.97f, 0.80f), FLinearColor(1.00f, 0.65f, 0.20f), 4.5f, 0.45f, 0.50f, 0.68f, 1.20f,   0.f, 1.00f, 2 }, // knightly gold
		{ 7,  TEXT("Estoc"),         FLinearColor(0.75f, 1.00f, 1.00f), FLinearColor(0.00f, 0.75f, 0.90f), 8.f,  0.85f, 0.66f, 0.80f, 1.10f, -12.f, 1.35f, 1 }, // a thin cyan line
		{ 8,  TEXT("Zweihander"),    FLinearColor(1.00f, 0.45f, 0.25f), FLinearColor(0.60f, 0.00f, 0.02f), 9.f,  0.05f, 0.35f, 0.60f, 1.60f,   0.f, 0.80f, 3 }, // heavy crimson sweep
		{ 25, TEXT("Emberoath"),     FLinearColor(1.00f, 0.75f, 0.30f), FLinearColor(1.00f, 0.20f, 0.01f), 12.f, 0.00f, 0.38f, 0.62f, 1.30f,   0.f, 0.90f, 3 }, // burning, the hottest of them
	};

	const FSlashLook* FindLook(int32 KitIndex)
	{
		for (const FSlashLook& L : GSlashes) { if (L.KitIndex == KitIndex) { return &L; } }
		return nullptr;
	}

	UNiagaraSystem* SlashSystem()
	{
		static TStrongObjectPtr<UNiagaraSystem> S(LoadObject<UNiagaraSystem>(nullptr, TEXT("/Game/CastleDefender/VFX/SwordSlash/NS_ClassroomSlash.NS_ClassroomSlash")));
		return S.Get();
	}

	UMaterialParameterCollection* SlashParams()
	{
		static TStrongObjectPtr<UMaterialParameterCollection> M(LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/CastleDefender/VFX/SwordSlash/MPC_CDSlash.MPC_CDSlash")));
		return M.Get();
	}

	void ApplyLook(UWorld* World, const FSlashLook& L)
	{
		// All layers of a swing share one look, so writing it again for each layer costs nothing visible.
		UMaterialParameterCollection* Params = SlashParams();
		UKismetMaterialLibrary::SetVectorParameterValue(World, Params, TEXT("ColorCore"), L.Core);
		UKismetMaterialLibrary::SetVectorParameterValue(World, Params, TEXT("ColorEdge"), L.Edge);
		UKismetMaterialLibrary::SetScalarParameterValue(World, Params, TEXT("Intensity"), L.Intensity * CVarSlashIntensity.GetValueOnGameThread());
		UKismetMaterialLibrary::SetScalarParameterValue(World, Params, TEXT("NoiseFlat"), FMath::Lerp(CVarSlashNoiseFloor.GetValueOnGameThread(), 1.f, L.NoiseFlat));
		UKismetMaterialLibrary::SetScalarParameterValue(World, Params, TEXT("EdgeMin"), L.EdgeMin * CVarSlashEdgeMul.GetValueOnGameThread());
		UKismetMaterialLibrary::SetScalarParameterValue(World, Params, TEXT("EdgeMax"), L.EdgeMax * FMath::Lerp(0.75f, 1.f, CVarSlashEdgeMul.GetValueOnGameThread()));
	}

	void SpawnNow(TWeakObjectPtr<AActor> WeakHero, const FSlashLook* L, double Roll, double ZUp, double ScaleMul)
	{
		AActor* Hero = WeakHero.Get();
		UWorld* World = Hero ? Hero->GetWorld() : nullptr;
		UNiagaraSystem* System = SlashSystem();
		if (!World || !System) { return; }
		const FVector Location = Hero->GetActorLocation() + FVector(0.0, 0.0, ZUp);
		const FRotator Rotation(0.0, Hero->GetActorRotation().Yaw, Roll + L->RollBias);
		const FVector Scale(L->Scale * ScaleMul * CVarSlashScale.GetValueOnGameThread());
		UNiagaraComponent* Fx = UNiagaraFunctionLibrary::SpawnSystemAtLocation(World, System, Location, Rotation, Scale, /*bAutoDestroy*/ true, /*bAutoActivate*/ true, ENCPoolMethod::AutoRelease);
		if (Fx) { Fx->SetCustomTimeDilation(L->Speed); }
	}
}

bool UCDSlashFX::PlayRow(AActor* Hero, int32 KitIndex, double Roll, double ZUp, double TimeOffset, double ScaleMul)
{
	const int32 DebugRow = CVarSlashDebugRow.GetValueOnGameThread();
	const FSlashLook* L = FindLook(DebugRow >= 0 ? DebugRow : KitIndex);
	UWorld* World = Hero ? Hero->GetWorld() : nullptr;
	if (!L || !World) { return false; }
	if (!SlashSystem() || !SlashParams())
	{
		static bool bWarned = false;
		if (!bWarned) { bWarned = true; UE_LOG(LogCDSlash, Error, TEXT("Slash assets missing in /Game/CastleDefender/VFX/SwordSlash, falling back to the old slash.")); }
		return false;
	}
	// 11-06 night: one blade-following ribbon per swing instead of up to 3 fixed arcs (owner: wrong axis, slashes everywhere). The later layers of the event are ignored.
	if (TimeOffset > KINDA_SMALL_NUMBER) { return true; }
	ApplyLook(World, *L);
	if (UCDSlashTrailSubsystem* Trail = World->GetSubsystem<UCDSlashTrailSubsystem>())
	{
		Trail->StartSwing(float(L->Scale * ScaleMul * CVarSlashScale.GetValueOnGameThread()), float(L->Speed), L->Core, L->Edge, L->Intensity * CVarSlashIntensity.GetValueOnGameThread());
	}
	return true;
}

void UCDSlashFX::PlaySwordSlash(AActor* Hero, double Roll, double ZUp, double TimeOffset, double ScaleMul, ECDSlashResult& Result)
{
	Result = ECDSlashResult::UseOldSlash;
	if (CVarSlashEnable.GetValueOnGameThread() == 0 || !Hero) { return; }
	if (PlayRow(Hero, UCDWeaponPerks::EquippedIndex(Hero), Roll, ZUp, TimeOffset, ScaleMul))
	{
		Result = ECDSlashResult::Handled;
	}
}

static FAutoConsoleCommandWithWorldAndArgs GSlashTestCmd(
	TEXT("cd.Slash.Test"),
	TEXT("cd.Slash.Test <kit row>: plays that sword's slash at the player, without changing the weapon."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
	{
		APawn* Pawn = World ? UGameplayStatics::GetPlayerPawn(World, 0) : nullptr;
		const int32 Row = Args.Num() > 0 ? FCString::Atoi(*Args[0]) : 0;
		if (!UCDSlashFX::PlayRow(Pawn, Row, 35.0, 20.0, 0.0, 1.0))
		{
			UE_LOG(LogCDSlash, Warning, TEXT("cd.Slash.Test: no slash for row %d (or no player)."), Row);
		}
	}));
