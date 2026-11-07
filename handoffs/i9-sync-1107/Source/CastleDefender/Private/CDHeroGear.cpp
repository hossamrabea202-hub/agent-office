#include "CDHeroGear.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "GameFramework/HUD.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialParameterCollection.h"
#include "RenderUtils.h"
#include "TextureResource.h"
#include "UObject/UnrealType.h"

static int32 GGearEnable = 1;
static FAutoConsoleVariableRef CVarGearEnable(TEXT("cd.Gear.Enable"), GGearEnable, TEXT("1 = the inventory decides what the hero visibly wears (default). 0 = leave the meshes alone."));

namespace
{
	int32 GetInt(const UObject* O, const TCHAR* Name, int32 Def = 0)
	{
		if (!O) { return Def; }
		const FIntProperty* P = FindFProperty<FIntProperty>(O->GetClass(), Name);
		return P ? P->GetPropertyValue_InContainer(O) : Def;
	}
	void SetInt(UObject* O, const TCHAR* Name, int32 V)
	{
		if (!O) { return; }
		if (const FIntProperty* P = FindFProperty<FIntProperty>(O->GetClass(), Name)) { P->SetPropertyValue_InContainer(O, V); }
	}
	bool ArrayInt(const UObject* O, const TCHAR* Name, int32 I, int32& Out)
	{
		const FArrayProperty* A = O ? FindFProperty<FArrayProperty>(O->GetClass(), Name) : nullptr;
		const FIntProperty* In = A ? CastField<FIntProperty>(A->Inner) : nullptr;
		if (!In) { return false; }
		FScriptArrayHelper H(A, A->ContainerPtrToValuePtr<void>(O));
		if (!H.IsValidIndex(I)) { return false; }
		Out = In->GetPropertyValue(H.GetRawPtr(I));
		return true;
	}
	UObject* ArrayObj(const UObject* O, const TCHAR* Name, int32 I)
	{
		const FArrayProperty* A = O ? FindFProperty<FArrayProperty>(O->GetClass(), Name) : nullptr;
		const FObjectPropertyBase* In = A ? CastField<FObjectPropertyBase>(A->Inner) : nullptr;
		if (!In) { return nullptr; }
		FScriptArrayHelper H(A, A->ContainerPtrToValuePtr<void>(O));
		return H.IsValidIndex(I) ? In->GetObjectPropertyValue(H.GetRawPtr(I)) : nullptr;
	}
	UObject* ObjVar(const UObject* O, const TCHAR* Name)
	{
		const FObjectPropertyBase* P = O ? FindFProperty<FObjectPropertyBase>(O->GetClass(), Name) : nullptr;
		return P ? P->GetObjectPropertyValue_InContainer(O) : nullptr;
	}
	UObject* FindHud(const UWorld* W)
	{
		const APlayerController* PC = W ? W->GetFirstPlayerController() : nullptr;
		AHUD* Hud = PC ? PC->GetHUD() : nullptr;
		return (Hud && FindFProperty<FIntProperty>(Hud->GetClass(), TEXT("SwordLoc"))) ? Hud : nullptr;
	}
	UCDHeroGearSubsystem* Gear(const UObject* Ctx)
	{
		const UWorld* W = Ctx ? Ctx->GetWorld() : nullptr;
		return W ? W->GetSubsystem<UCDHeroGearSubsystem>() : nullptr;
	}
	void SetVis(USceneComponent* C, bool bOn)
	{
		if (C && C->GetVisibleFlag() != bOn) { C->SetVisibility(bOn, false); }
	}
	UActorComponent* CompOf(AActor* A, const TCHAR* ClassPath)
	{
		UClass* C = LoadObject<UClass>(nullptr, ClassPath);
		return (A && C) ? A->GetComponentByClass(C) : nullptr;
	}
}

UTexture* UCDHeroGearSubsystem::WeaponIcon(const UObject* Ctx, UTexture* Fallback)
{
	const UCDHeroGearSubsystem* G = Gear(Ctx);
	return (G && GGearEnable && G->CurWeaponIcon) ? G->CurWeaponIcon.Get() : Fallback;
}

UTexture* UCDHeroGearSubsystem::ShieldIcon(const UObject* Ctx, UTexture* Fallback)
{
	const UCDHeroGearSubsystem* G = Gear(Ctx);
	return (G && GGearEnable && G->CurShieldIcon) ? G->CurShieldIcon.Get() : Fallback;
}

int32 UCDHeroGearSubsystem::WeaponDamage(const UObject* Ctx, int32 Fallback)
{
	const UCDHeroGearSubsystem* G = Gear(Ctx);
	const UActorComponent* Kit = G ? G->WeaponKit.Get() : nullptr;
	int32 D = Fallback;
	const int32 E = GetInt(Kit, TEXT("Equipped"), -1);
	if (GGearEnable && E >= 0) { ArrayInt(Kit, TEXT("Damage"), E, D); }
	return D;
}

bool UCDHeroGearSubsystem::WeaponWorn(const UWorld* World)
{
	const UCDHeroGearSubsystem* G = World ? World->GetSubsystem<UCDHeroGearSubsystem>() : nullptr;
	return !G || !GGearEnable || G->bSwordOn;
}

bool UCDHeroGearSubsystem::FindParts()
{
	APawn* Pawn = UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
	if (!Pawn) { return false; }
	if (Hero.Get() != Pawn || !Knight.IsValid())
	{
		Hero = Pawn;
		bStarted = false;
		WeaponKit = CompOf(Pawn, TEXT("/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit.BPC_WeaponKit_C"));
		ShieldKit = CompOf(Pawn, TEXT("/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit.BPC_ShieldKit_C"));
		Obsidian = CompOf(Pawn, TEXT("/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet.BPC_ObsidianSet_C"));
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Pawn);
		for (UStaticMeshComponent* M : Meshes)
		{
			if (!M) { continue; }
			if (M->ComponentHasTag(TEXT("KitWeapon"))) { KitWeapon = M; }
			else if (M->ComponentHasTag(TEXT("OffHand"))) { OffHand = M; }
			else if (M->GetFName() == TEXT("Sword")) { Sword = M; }
			else if (M->GetFName() == TEXT("ObsidianShield")) { ObsShield = M; }
		}
		TInlineComponentArray<USkeletalMeshComponent*> Skels(Pawn);
		for (USkeletalMeshComponent* S : Skels) { if (S && S->ComponentHasTag(TEXT("ObsKnight"))) { Knight = S; } }
		Underlayer = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/CastleDefender/Characters/Hero/Armor/M_KnightUnderlayer.M_KnightUnderlayer"));
	}
	return Knight.IsValid();
}

void UCDHeroGearSubsystem::SyncWeapon(UObject* Hud)
{
	UActorComponent* Kit = WeaponKit.Get();
	const int32 Eq = GetInt(Kit, TEXT("Equipped"), -1);
	int32 S = GetInt(Hud, TEXT("SwordLoc"));
	// Picking a weapon in Vesna's trade while the slot is empty puts it in the hand.
	if (bStarted && Eq != LastEquipped && Eq >= 0 && S >= 10) { S = 0; SetInt(Hud, TEXT("SwordLoc"), 0); }
	LastEquipped = Eq;
	bSwordOn = S == 0;
	SetVis(KitWeapon.Get(), bSwordOn && Eq >= 0);
	SetVis(Sword.Get(), bSwordOn && Eq < 0);
	UStaticMesh* Mesh = Eq >= 0 ? Cast<UStaticMesh>(ArrayObj(Kit, TEXT("Meshes"), Eq)) : nullptr;
	CurWeaponIcon = Mesh ? IconFor(Mesh) : nullptr; // no kit weapon: the painted longsword icon IS the default sword
}

void UCDHeroGearSubsystem::SyncShield(UObject* Hud)
{
	UObject* Kit = ShieldKit.Get();
	int32 W = GetInt(Kit, TEXT("Worn"), -1);
	int32 Sh = GetInt(Hud, TEXT("ShieldLoc"));
	const bool bObs = GetInt(Obsidian.Get(), TEXT("ShieldLevel")) > 0;
	if (bStarted && W != LastWorn && W >= 0) // Vesna: bought or put on a shield
	{
		ParkedWorn = -1;
		if (Sh != 0 && Sh != -1) { Sh = 0; }
	}
	const bool bHas = W >= 0 || ParkedWorn >= 0 || bObs;
	if (!bHas && Sh != -1) { Sh = NoItem; }
	else if (bHas && Sh == NoItem) { Sh = 0; }
	SetInt(Hud, TEXT("ShieldLoc"), Sh);
	// A shield in the pack must not block either: the kit's own Worn is parked while it is off the arm.
	if (Sh != 0 && W >= 0) { ParkedWorn = W; W = -1; SetInt(Kit, TEXT("Worn"), -1); }
	else if (Sh == 0 && W < 0 && ParkedWorn >= 0) { W = ParkedWorn; ParkedWorn = -1; SetInt(Kit, TEXT("Worn"), W); }
	LastWorn = W;
	UStaticMeshComponent* Off = OffHand.Get();
	const bool bKitShield = W >= 0 || ParkedWorn >= 0;
	SetVis(Off, Sh == 0 && bKitShield);
	SetVis(ObsShield.Get(), Sh == 0 && !bKitShield && bObs);
	UStaticMesh* Mesh = bKitShield ? (Off ? Off->GetStaticMesh().Get() : nullptr) : (bObs && ObsShield.IsValid() ? ObsShield->GetStaticMesh().Get() : nullptr);
	CurShieldIcon = Mesh ? IconFor(Mesh) : nullptr;
}

void UCDHeroGearSubsystem::SyncBody(UObject* Hud)
{
	USkeletalMeshComponent* K = Knight.Get();
	const UObject* Obs = Obsidian.Get();
	UMaterialInterface* Hidden = Cast<UMaterialInterface>(ObjVar(Obs, TEXT("HiddenMat")));
	const int32 WornEff = GetInt(Obs, TEXT("WornEff"));
	// ShadowKnight material slots: 0 arms, 1 chest, 2 cloth, 3 helmet, 4 legs.
	static const TCHAR* SlotVar[5] = { TEXT("GloveLoc"), TEXT("ChestLoc"), nullptr, TEXT("HelmLoc"), TEXT("BootLoc") };
	for (int32 I = 0; I < 5 && I < K->GetNumMaterials(); ++I)
	{
		if (!SlotVar[I]) { continue; }
		int32 Cover = 0;
		ArrayInt(Obs, TEXT("KnightCover"), I, Cover);
		if (Cover & WornEff) { continue; } // an Obsidian piece hides this slot: BPC_ObsidianSet has already set it
		UMaterialInterface* Orig = Cast<UMaterialInterface>(ArrayObj(Obs, TEXT("KnightMats"), I));
		if (!Orig) { continue; }
		const bool bOn = GetInt(Hud, SlotVar[I]) == 0;
		UMaterialInterface* Want = bOn ? Orig : (I == 3 ? Hidden : (Underlayer ? Underlayer.Get() : Orig));
		if (Want && K->GetMaterial(I) != Want) { K->SetMaterial(I, Want); }
	}
}

void UCDHeroGearSubsystem::Tick(float DeltaTime)
{
	UWorld* W = GetWorld();
	if (!W || !GGearEnable || !FindParts()) { return; }
	UObject* Hud = FindHud(W);
	if (!Hud) { return; }
	const double Now = W->GetRealTimeSeconds();
	if (StartAt < 0.0) { StartAt = Now; }
	if (Now - StartAt < 1.0) { return; } // kits and the save load during the first frames
	if (!bStarted && !UGameplayStatics::DoesSaveGameExist(TEXT("CastleSave"), 0) && GetInt(Hud, TEXT("HelmLoc")) == 10)
	{
		SetInt(Hud, TEXT("HelmLoc"), 999); // new game: the Great Helm is sold in the armoury, not owned yet (999 = the armoury's own "not bought" value)
	}
	SyncWeapon(Hud);
	SyncShield(Hud);
	SyncBody(Hud);
	bStarted = true;
}

UTexture2D* UCDHeroGearSubsystem::IconFor(UStaticMesh* Mesh)
{
	const double Now = GetWorld()->GetRealTimeSeconds();
	TObjectPtr<UTexture2D>* Found = Icons.Find(Mesh);
	double* At = RenderedAt.Find(Mesh);
	if (Found && *Found && (!At || *At < 0.0 || Now - *At < 3.0)) { return *Found; }
	UTexture2D* Tex = RenderIcon(Mesh);
	if (Tex) { Icons.Add(Mesh, Tex); }
	RenderedAt.Add(Mesh, Found ? -1.0 : Now); // -1: final
	return Tex ? Tex : (Found ? Found->Get() : nullptr);
}

UTexture2D* UCDHeroGearSubsystem::RenderIcon(UStaticMesh* Mesh)
{
	UWorld* W = GetWorld();
	if (!W || !Mesh) { return nullptr; }
	const int32 Size = 256;
	FActorSpawnParameters SP; SP.ObjectFlags |= RF_Transient; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FVector Far(0.0, 0.0, -400000.0);
	AActor* A = W->SpawnActor<AActor>(AActor::StaticClass(), FTransform(Far), SP);
	if (!A) { return nullptr; }
	USceneComponent* Root = NewObject<USceneComponent>(A); A->SetRootComponent(Root); Root->RegisterComponent(); Root->SetWorldLocation(Far);
	UStaticMeshComponent* M = NewObject<UStaticMeshComponent>(A);
	M->SetStaticMesh(Mesh);
	M->SetMobility(EComponentMobility::Movable);
	M->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	M->bForceMipStreaming = true;
	M->SetForcedLodModel(1);
	const FBox Raw = Mesh->GetBoundingBox();
	const double Scale = Raw.GetSize().Z < 5.0 ? 100.0 : 1.0; // same rule as the hand: metre imports
	M->SetupAttachment(Root);
	M->SetRelativeScale3D(FVector(Scale));
	M->RegisterComponent();

	// Look at the flat side, longest axis up; long thin items on the diagonal like the painted icons.
	const FVector Sz = Raw.GetSize() * Scale;
	const FVector Centre = Far + Raw.GetCenter() * Scale;
	const FVector AxisV[3] = { FVector::XAxisVector, FVector::YAxisVector, FVector::ZAxisVector };
	const double Vals[3] = { Sz.X, Sz.Y, Sz.Z };
	int32 Lo = 0, Hi = 0;
	for (int32 I = 1; I < 3; ++I) { if (Vals[I] < Vals[Lo]) { Lo = I; } if (Vals[I] > Vals[Hi]) { Hi = I; } }
	if (Lo == Hi) { Lo = (Hi + 1) % 3; }
	const int32 Mid = 3 - Lo - Hi;
	const FVector Forward = -AxisV[Lo];
	const bool bLong = Vals[Hi] > Vals[Mid] * 2.5;
	const FVector Up = bLong ? (AxisV[Hi] + AxisV[Mid]).GetSafeNormal() : AxisV[Hi];

	USceneCaptureComponent2D* Cap = NewObject<USceneCaptureComponent2D>(A);
	Cap->SetupAttachment(Root);
	Cap->bCaptureEveryFrame = false;
	Cap->bCaptureOnMovement = false;
	Cap->ProjectionType = ECameraProjectionMode::Orthographic;
	Cap->OrthoWidth = float((bLong ? Vals[Hi] * 0.78 : Vals[Hi]) * 1.08);
	Cap->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
	Cap->ShowOnlyComponents.Add(M);
	Cap->RegisterComponent();
	Cap->SetWorldLocationAndRotation(Centre - Forward * (Vals[Hi] * 2.0 + 50.0), FRotationMatrix::MakeFromXZ(Forward, Up).Rotator());

	UTextureRenderTarget2D* RT = NewObject<UTextureRenderTarget2D>(A);
	RT->RenderTargetFormat = RTF_RGBA16f;
	RT->ClearColor = FLinearColor::Transparent;
	RT->InitAutoFormat(Size, Size);
	RT->UpdateResourceImmediate(true);
	Cap->TextureTarget = RT;

	TArray<FLinearColor> Colour, Depth;
	FTextureRenderTargetResource* Res = RT->GameThread_GetRenderTargetResource();
	Cap->CaptureSource = ESceneCaptureSource::SCS_BaseColor;
	Cap->CaptureScene();
	const bool bA = Res && Res->ReadLinearColorPixels(Colour);
	Cap->CaptureSource = ESceneCaptureSource::SCS_DeviceDepth;
	Cap->CaptureScene();
	const bool bB = Res && Res->ReadLinearColorPixels(Depth);
	A->Destroy();
	if (!bA || !bB || Colour.Num() != Size * Size || Depth.Num() != Size * Size) { return nullptr; }

	UTexture2D* Tex = UTexture2D::CreateTransient(Size, Size, PF_B8G8R8A8);
	if (!Tex) { return nullptr; }
	Tex->SRGB = true;
	FColor* Out = static_cast<FColor*>(Tex->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE));
	for (int32 I = 0; I < Size * Size; ++I)
	{
		// Base colour has no lighting: a soft gain keeps dark metal readable on the black slot.
		const FLinearColor C = FLinearColor(Colour[I].R, Colour[I].G, Colour[I].B) * 1.6f + FLinearColor(0.03f, 0.03f, 0.03f);
		FColor Px = C.GetClamped().ToFColor(true);
		Px.A = Depth[I].R > 0.f ? 255 : 0;
		Out[I] = Px;
	}
	Tex->GetPlatformData()->Mips[0].BulkData.Unlock();
	Tex->UpdateResource();
	return Tex;
}
