#include "CDRevealVideoSubsystem.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "MediaPlayer.h"
#include "MediaSource.h"
#include "Sound/SoundBase.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Images/SImage.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/SlateRenderTransform.h"
#include "Math/TransformCalculus2D.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"

namespace CDRevealVideo
{
	static int32 GEnable = 1;
	static float GSize = 0.42f;      // 15:30 owner: 40 % smaller than the first 0.7 (also closer to the 480 px source, less upscaling)
	static int32 GPause = 0;
	static float GMaxSeconds = 6.5f;
	static float GPopIn = 0.45f;
	static float GPopOut = 0.6f;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.Reveal.Video"), GEnable, TEXT("1 = the owner's reveal videos play on book / satchel pickup and freeze the hero (0 = nothing plays)."));
	static int32 GFreeze = 0;   // 11-07 owner: freezing the hero during the reveal was a mistake, a very annoying feeling
	static FAutoConsoleVariableRef CVarFreeze(TEXT("cd.Reveal.Freeze"), GFreeze, TEXT("1 = the hero is frozen while a reveal video plays (default 0: he keeps moving)."));
	static FAutoConsoleVariableRef CVarSize(TEXT("cd.Reveal.Size"), GSize, TEXT("Reveal video circle size as a fraction of the viewport height (0.42)."));
	static FAutoConsoleVariableRef CVarPause(TEXT("cd.Reveal.Pause"), GPause, TEXT("1 = pause the world while the reveal video plays (default 0: only the hero is frozen)."));
	static FAutoConsoleVariableRef CVarMax(TEXT("cd.Reveal.MaxSeconds"), GMaxSeconds, TEXT("Safety: the video phase ends after this many real seconds even if the player never reports the end (6.5)."));
	static FAutoConsoleVariableRef CVarPopIn(TEXT("cd.Reveal.PopIn"), GPopIn, TEXT("Pop-in seconds: the circle spins once and grows from zero with an overshoot (0.45)."));
	static FAutoConsoleVariableRef CVarPopOut(TEXT("cd.Reveal.PopOut"), GPopOut, TEXT("Pop-out seconds: the circle spins once, shrinks to the HUD icon's size and flies onto it (0.6)."));
	static bool GActive = false;

	static const TCHAR* MPCPath = TEXT("/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree");
	static const TCHAR* PlayerPath = TEXT("/Game/CastleDefender/UI/Reveal/Video/MP_Reveal.MP_Reveal");
	static const TCHAR* MaterialPath = TEXT("/Game/CastleDefender/UI/Reveal/Video/M_UI_RevealVideo.M_UI_RevealVideo");
	static const TCHAR* BookSourcePath = TEXT("/Game/CastleDefender/UI/Reveal/Video/MS_RevealBook.MS_RevealBook");
	static const TCHAR* BagSourcePath = TEXT("/Game/CastleDefender/UI/Reveal/Video/MS_RevealInventory.MS_RevealInventory");
	static const TCHAR* PopInPath = TEXT("/Game/CastleDefender/UI/Reveal/Video/SFX_RevealPopIn.SFX_RevealPopIn");
	static const TCHAR* PopOutPath = TEXT("/Game/CastleDefender/UI/Reveal/Video/SFX_RevealPopOut.SFX_RevealPopOut");
	static const TCHAR* PopInFallback = TEXT("/Game/CastleDefender/UI/Reveal/SFX_Reveal_Whoosh.SFX_Reveal_Whoosh");
	static const TCHAR* PopOutFallback = TEXT("/Game/CastleDefender/UI/Reveal/SFX_Reveal_Hit.SFX_Reveal_Hit");

	// HUD key icon centres in viewport pixels, copied from the native draw code:
	//   ZombieHUD UX_CallFunction_23  (T_HUD_InventoryKey): size 0.085 H, left = W - 0.085 H - 0.03 H, centre y = 0.91 H + 0.0112 W
	//   SkillTreeHUD CX_2402 (T_HUD_SkillTreeKey): size 0.085 H, left = W - 0.115 H - 0.097 H, centre y = 0.921201 H
	static FVector2D IconCentre(bool bBook, const FVector2D& V)
	{
		const double W = V.X, H = V.Y;
		return bBook ? FVector2D(W - 0.1695 * H, 0.921201 * H) : FVector2D(W - 0.0725 * H, 0.91 * H + 0.011201 * W);
	}
	static constexpr double IconSizeFrac = 0.085;

	static float EaseOutCubic(float T) { const float U = 1.f - T; return 1.f - U * U * U; }
	static float EaseInOutCubic(float T) { return T < 0.5f ? 4.f * T * T * T : 1.f - FMath::Pow(-2.f * T + 2.f, 3.f) * 0.5f; }
	static float BackOut(float T) { const float C1 = 1.70158f, C3 = C1 + 1.f; const float U = T - 1.f; return 1.f + C3 * U * U * U + C1 * U * U; }

	static void Viewport(FVector2D& OutSize, float& OutScale)
	{
		OutSize = FVector2D(1920.0, 1080.0);
		OutScale = 1.f;
		if (GEngine && GEngine->GameViewport)
		{
			GEngine->GameViewport->GetViewportSize(OutSize);
			OutScale = FMath::Max(GEngine->GameViewport->GetDPIScale(), 0.01f);
		}
	}

	// Overlay that eats every key and click while the reveal plays (so T / I / Esc / attack never reach the game).
	class SRevealBlocker : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SRevealBlocker) : _Brush(nullptr) {}
			SLATE_ARGUMENT(const FSlateBrush*, Brush)
		SLATE_END_ARGS()

		TSharedPtr<SImage> ImageWidget;

		void Construct(const FArguments& InArgs)
		{
			const FSlateBrush* B = InArgs._Brush;
			ChildSlot
			[
				SNew(SOverlay)
				+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
				[
					SNew(SBox)
					.WidthOverride_Lambda([this]() { return FOptionalSize(Side()); })
					.HeightOverride_Lambda([this]() { return FOptionalSize(Side()); })
					[
						SAssignNew(ImageWidget, SImage).Image(B)
					]
				]
			];
			ImageWidget->SetRenderTransformPivot(FVector2D(0.5, 0.5));
		}

		static float Side()
		{
			FVector2D Size; float Scale;
			Viewport(Size, Scale);
			return FMath::Max(64.f, static_cast<float>(Size.Y) * GSize / Scale);
		}

		virtual bool SupportsKeyboardFocus() const override { return true; }
		virtual FReply OnKeyDown(const FGeometry&, const FKeyEvent&) override { return FReply::Handled(); }
		virtual FReply OnKeyUp(const FGeometry&, const FKeyEvent&) override { return FReply::Handled(); }
		virtual FReply OnKeyChar(const FGeometry&, const FCharacterEvent&) override { return FReply::Handled(); }
		virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent&) override { return FReply::Handled(); }
		virtual FReply OnMouseButtonUp(const FGeometry&, const FPointerEvent&) override { return FReply::Handled(); }
		virtual FReply OnMouseButtonDoubleClick(const FGeometry&, const FPointerEvent&) override { return FReply::Handled(); }
		virtual FReply OnMouseWheel(const FGeometry&, const FPointerEvent&) override { return FReply::Handled(); }
	};
}

bool UCDRevealVideoSubsystem::IsRevealPlaying() { return CDRevealVideo::GActive; }

bool UCDRevealVideoSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* W = Cast<UWorld>(Outer);
	return W && (W->WorldType == EWorldType::Game || W->WorldType == EWorldType::PIE);
}

bool UCDRevealVideoSubsystem::IsTickable() const
{
	const UWorld* W = GetWorld();
	return W && W->IsGameWorld() && !IsTemplate();
}

void UCDRevealVideoSubsystem::Deinitialize()
{
	if (Current != EItem::None) { Finish(false); }
	Super::Deinitialize();
}

float UCDRevealVideoSubsystem::ReadAge(const TCHAR* Name) const
{
	if (!MPC) { return -1.f; }
	return UKismetMaterialLibrary::GetScalarParameterValue(GetWorld(), MPC, FName(Name));
}

UObject* UCDRevealVideoSubsystem::FindMotionFX() const
{
	const APawn* Pawn = UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
	if (!Pawn) { return nullptr; }
	for (UActorComponent* C : Pawn->GetComponents())
	{
		if (C && C->GetClass()->GetName() == TEXT("BPC_MotionFX_C")) { return C; }
	}
	return nullptr;
}

void UCDRevealVideoSubsystem::SetOpenNow(EItem Item, bool bValue)
{
	UObject* FX = FindMotionFX();
	if (!FX)
	{
		UE_LOG(LogTemp, Warning, TEXT("[CD] reveal video: hero has no BPC_MotionFX, cannot auto-open the %s"), Item == EItem::Book ? TEXT("skill tree") : TEXT("pack"));
		return;
	}
	const FName PropName = Item == EItem::Book ? FName(TEXT("BookOpenNow")) : FName(TEXT("BagOpenNow"));
	if (FBoolProperty* P = CastField<FBoolProperty>(FX->GetClass()->FindPropertyByName(PropName)))
	{
		P->SetPropertyValue_InContainer(FX, bValue);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[CD] reveal video: BPC_MotionFX has no %s"), *PropName.ToString());
	}
}

void UCDRevealVideoSubsystem::PlayPop(bool bIn) const
{
	// 16:30 owner: "a better reveal sound than pop and pop": layered item-specific cues SFX_RevealIn_Book / _Bag, SFX_RevealOut_Book / _Bag
	// (arrival: whoosh + sub swell + landing + shimmer + page flutter / leather creak; departure: zip + reverse whoosh + dock ting + sparkle).
	const TCHAR* Item = Current == EItem::Book ? TEXT("Book") : TEXT("Bag");
	const FString Specific = FString::Printf(TEXT("/Game/CastleDefender/UI/Reveal/Video/SFX_Reveal%s_%s.SFX_Reveal%s_%s"), bIn ? TEXT("In") : TEXT("Out"), Item, bIn ? TEXT("In") : TEXT("Out"), Item);
	USoundBase* S = LoadObject<USoundBase>(nullptr, *Specific);
	if (!S) { S = LoadObject<USoundBase>(nullptr, bIn ? CDRevealVideo::PopInPath : CDRevealVideo::PopOutPath); }
	if (!S) { S = LoadObject<USoundBase>(nullptr, bIn ? CDRevealVideo::PopInFallback : CDRevealVideo::PopOutFallback); }
	if (S) { UGameplayStatics::PlaySound2D(GetWorld(), S); }
}

void UCDRevealVideoSubsystem::UpdateTransform()
{
	if (!Image.IsValid()) { return; }
	const double Now = FPlatformTime::Seconds();
	float Scale = 1.f, Angle = 0.f;
	FVector2D Offset(0.0, 0.0);
	if (Phase == EPhase::PopIn)
	{
		const float T = FMath::Clamp(static_cast<float>((Now - PhaseStart) / FMath::Max(CDRevealVideo::GPopIn, 0.05f)), 0.f, 1.f);
		Scale = FMath::Max(0.001f, CDRevealVideo::BackOut(T));
		Angle = -360.f * (1.f - CDRevealVideo::EaseOutCubic(T));
	}
	else if (Phase == EPhase::PopOut)
	{
		const float T = FMath::Clamp(static_cast<float>((Now - PhaseStart) / FMath::Max(CDRevealVideo::GPopOut, 0.05f)), 0.f, 1.f);
		const float E = CDRevealVideo::EaseInOutCubic(T);
		FVector2D View; float Dpi;
		CDRevealVideo::Viewport(View, Dpi);
		const FVector2D Centre = View * 0.5;
		const FVector2D Icon = CDRevealVideo::IconCentre(Current == EItem::Book, View);
		Offset = (Icon - Centre) / Dpi * E;
		const float EndScale = static_cast<float>(CDRevealVideo::IconSizeFrac / FMath::Max(CDRevealVideo::GSize, 0.05f));
		Scale = FMath::Lerp(1.f, EndScale, E);
		Angle = 360.f * E;
	}
	FMatrix2x2 M = FMatrix2x2(FScale2D(Scale)).Concatenate(FMatrix2x2(FQuat2D(FMath::DegreesToRadians(Angle))));
	Image->SetRenderTransform(TOptional<FSlateRenderTransform>(FSlateRenderTransform(M, Offset)));
}

void UCDRevealVideoSubsystem::Tick(float DeltaTime)
{
	UWorld* W = GetWorld();
	if (!W || !CDRevealVideo::GEnable) { return; }

	// the one-frame auto-open pulse set at the end of the previous reveal
	if (PulseItem != EItem::None) { SetOpenNow(PulseItem, false); PulseItem = EItem::None; }

	if (!MPC)
	{
		MPC = LoadObject<UMaterialParameterCollection>(nullptr, CDRevealVideo::MPCPath);
		if (!MPC) { return; }
	}

	// detect a fresh pickup exactly like BPC_MotionFX did (0.05 < Age < 2, once per item)
	const float BookAge = ReadAge(TEXT("BookAge"));
	const float BagAge = ReadAge(TEXT("BagAge"));
	if (!bBookDone && BookAge > 0.05f && BookAge < 2.f) { bPendingBook = true; bBookDone = true; }
	if (!bBagDone && BagAge > 0.05f && BagAge < 2.f) { bPendingBag = true; bBagDone = true; }

	if (Current != EItem::None)
	{
		// keep the hero still (knockback, momentum)
		if (ACharacter* Ch = Cast<ACharacter>(FrozenPawn.Get()))
		{
			if (UCharacterMovementComponent* Move = Ch->GetCharacterMovement()) { Move->StopMovementImmediately(); }
		}
		const double Now = FPlatformTime::Seconds();
		UpdateTransform();
		if (Phase == EPhase::PopIn)
		{
			if (Now - PhaseStart >= CDRevealVideo::GPopIn) { Phase = EPhase::Play; PhaseStart = Now; }
		}
		else if (Phase == EPhase::Play)
		{
			const double Elapsed = Now - StartTime;
			bool bDone = bEndReached || bOpenFailed || Elapsed > CDRevealVideo::GMaxSeconds;
			if (!bDone && Player && Elapsed > 1.0 && !Player->IsPlaying() && !Player->IsPreparing())
			{
				const FTimespan Duration = Player->GetDuration();
				if (Duration.GetTotalSeconds() > 0.0 && Player->GetTime() >= Duration - FTimespan::FromMilliseconds(50.0)) { bDone = true; }
			}
			if (bDone) { BeginPopOut(); }
		}
		else if (Phase == EPhase::PopOut)
		{
			if (Now - PhaseStart >= CDRevealVideo::GPopOut) { Finish(true); }
		}
		return;
	}

	if (bPendingBook) { bPendingBook = false; Start(EItem::Book); }
	else if (bPendingBag) { bPendingBag = false; Start(EItem::Bag); }
}

bool UCDRevealVideoSubsystem::PlayRevealNow(int32 Item)
{
	if (Current != EItem::None) { return false; }
	Start(Item == 0 ? EItem::Book : EItem::Bag);
	return Current != EItem::None;
}

void UCDRevealVideoSubsystem::Start(EItem Item)
{
	UWorld* W = GetWorld();
	if (!W || !GEngine || !GEngine->GameViewport) { return; }
	if (!Player) { Player = LoadObject<UMediaPlayer>(nullptr, CDRevealVideo::PlayerPath); }
	UMediaSource* Source = LoadObject<UMediaSource>(nullptr, Item == EItem::Book ? CDRevealVideo::BookSourcePath : CDRevealVideo::BagSourcePath);
	UMaterialInterface* Mat = LoadObject<UMaterialInterface>(nullptr, CDRevealVideo::MaterialPath);
	if (!Player || !Source || !Mat)
	{
		UE_LOG(LogTemp, Warning, TEXT("[CD] reveal video: assets missing (player %d source %d material %d), plain auto-open instead"), Player != nullptr, Source != nullptr, Mat != nullptr);
		SetOpenNow(Item, true);
		PulseItem = Item;
		return;
	}

	Current = Item;
	Phase = EPhase::PopIn;
	bEndReached = bOpenFailed = false;
	StartTime = PhaseStart = FPlatformTime::Seconds();

	Player->OnEndReached.RemoveDynamic(this, &UCDRevealVideoSubsystem::HandleEndReached);
	Player->OnEndReached.AddDynamic(this, &UCDRevealVideoSubsystem::HandleEndReached);
	Player->OnMediaOpenFailed.RemoveDynamic(this, &UCDRevealVideoSubsystem::HandleOpenFailed);
	Player->OnMediaOpenFailed.AddDynamic(this, &UCDRevealVideoSubsystem::HandleOpenFailed);
	Player->PlayOnOpen = true;
	Player->SetLooping(false);
	Player->Close();
	if (!Player->OpenSource(Source)) { bOpenFailed = true; }

	if (!MID) { MID = UMaterialInstanceDynamic::Create(Mat, this); }
	Brush.SetResourceObject(MID);
	Brush.DrawAs = ESlateBrushDrawType::Image;
	Brush.ImageSize = FVector2D(512.0, 512.0);
	Brush.TintColor = FSlateColor(FLinearColor::White);

	TSharedRef<CDRevealVideo::SRevealBlocker> Widget = SNew(CDRevealVideo::SRevealBlocker).Brush(&Brush);
	if (!CDRevealVideo::GFreeze) { Widget->SetVisibility(EVisibility::HitTestInvisible); }   // 11-07: clicks and the wheel pass through to the game while the video plays
	Overlay = Widget;
	Image = Widget->ImageWidget;
	UpdateTransform();   // start at scale 0 before the first paint
	GEngine->GameViewport->AddViewportWidgetContent(Widget, 10000);
	if (CDRevealVideo::GFreeze && FSlateApplication::IsInitialized()) { FSlateApplication::Get().SetAllUserFocus(Widget, EFocusCause::SetDirectly); }   // no focus grab: keys must keep reaching the game

	ApplyFreeze(true);
	PlayPop(true);
	UE_LOG(LogTemp, Display, TEXT("[CD] reveal video: %s started (%s)"), Item == EItem::Book ? TEXT("book") : TEXT("satchel"), *Source->GetName());
}

void UCDRevealVideoSubsystem::BeginPopOut()
{
	Phase = EPhase::PopOut;
	PhaseStart = FPlatformTime::Seconds();
	if (Player) { Player->Pause(); }   // keep the last frame on the circle while it flies to the icon
	PlayPop(false);
	UE_LOG(LogTemp, Display, TEXT("[CD] reveal video: video done after %.2f s (%s), popping out to the %s icon"), PhaseStart - StartTime,
		bEndReached ? TEXT("end of video") : bOpenFailed ? TEXT("open failed") : TEXT("timeout"), Current == EItem::Book ? TEXT("skill tree") : TEXT("inventory"));
}

void UCDRevealVideoSubsystem::ApplyFreeze(bool bFreeze)
{
	UWorld* W = GetWorld();
	if (bFreeze)
	{
		APlayerController* PC = UGameplayStatics::GetPlayerController(W, 0);
		APawn* Pawn = PC ? PC->GetPawn() : nullptr;
		FrozenPC = PC;
		FrozenPawn = Pawn;
		if (CDRevealVideo::GFreeze)
		{
			if (PC) { PC->SetIgnoreMoveInput(true); PC->SetIgnoreLookInput(true); PC->FlushPressedKeys(); }
			if (ACharacter* Ch = Cast<ACharacter>(Pawn))
			{
				if (UCharacterMovementComponent* Move = Ch->GetCharacterMovement()) { Move->StopMovementImmediately(); }
			}
			bFrozen = true;
		}
		else { FrozenPawn = nullptr; }
		CDRevealVideo::GActive = CDRevealVideo::GFreeze != 0;   // 11-07: no longer blocks the sword unless the freeze is switched on
		if (CDRevealVideo::GPause && W && !W->IsPaused()) { bPausedByUs = UGameplayStatics::SetGamePaused(W, true); }
	}
	else
	{
		if (bFrozen)
		{
			if (APlayerController* PC = FrozenPC.Get()) { PC->SetIgnoreMoveInput(false); PC->SetIgnoreLookInput(false); PC->FlushPressedKeys(); }
			bFrozen = false;
		}
		if (bPausedByUs && W) { UGameplayStatics::SetGamePaused(W, false); bPausedByUs = false; }
		CDRevealVideo::GActive = false;
		FrozenPC = nullptr;
		FrozenPawn = nullptr;
	}
}

void UCDRevealVideoSubsystem::Finish(bool bOpenMenu)
{
	const EItem Item = Current;
	Current = EItem::None;
	Phase = EPhase::Idle;
	if (Overlay.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(Overlay.ToSharedRef());
		if (FSlateApplication::IsInitialized()) { FSlateApplication::Get().SetAllUserFocusToGameViewport(); }
	}
	Overlay.Reset();
	Image.Reset();
	if (Player)
	{
		Player->OnEndReached.RemoveDynamic(this, &UCDRevealVideoSubsystem::HandleEndReached);
		Player->OnMediaOpenFailed.RemoveDynamic(this, &UCDRevealVideoSubsystem::HandleOpenFailed);
		Player->Close();
	}
	ApplyFreeze(false);
	if (bOpenMenu && Item != EItem::None)
	{
		SetOpenNow(Item, true);   // the HUD reads it this frame; the next tick clears it: exactly one T / I toggle
		PulseItem = Item;
	}
	UE_LOG(LogTemp, Display, TEXT("[CD] reveal video: finished after %.2f s"), FPlatformTime::Seconds() - StartTime);
}

void UCDRevealVideoSubsystem::HandleEndReached() { bEndReached = true; }

void UCDRevealVideoSubsystem::HandleOpenFailed(FString FailedUrl)
{
	bOpenFailed = true;
	UE_LOG(LogTemp, Warning, TEXT("[CD] reveal video: could not open %s"), *FailedUrl);
}
