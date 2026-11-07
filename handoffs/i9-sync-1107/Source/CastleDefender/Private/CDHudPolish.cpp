#include "CDHudPolish.h"
#include "Containers/Ticker.h"

#include "CanvasItem.h"
#include "Components/WidgetComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "GameFramework/HUD.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "GameFramework/PlayerInput.h"
#include "InputKeyEventArgs.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UnrealType.h"

namespace CDHudPolish
{
	static int32 GEnable = 1;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.HudPolish"), GEnable,
		TEXT("1 = death screen hides world widgets, bite explainer drawn as a framed card, infection banner (default). 0 = Blueprint HUD exactly as authored."));

	// Blueprint member names this subsystem reads (BP_ThirdPersonCharacter, BPC_Infection).
	static const FName NAME_IsDead(TEXT("IsDead"));
	static const FName NAME_ExplainCard(TEXT("ExplainCard"));
	static const FName NAME_InfectSeen(TEXT("InfectSeen"));
	static const FName NAME_Infected(TEXT("Infected"));
	static const FName NAME_NextCard(TEXT("NextCard"));
	static const TCHAR* FontPath = TEXT("/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel");
	static constexpr int32 NumCards = 3;

	struct FCard { const TCHAR* Title; const TCHAR* Body; FLinearColor Accent; };
	static const FCard Cards[NumCards] = {
		{ TEXT("BITTEN"),   TEXT("Below 30 % health, a zombie bite infects you."),                    FLinearColor(0.85f, 0.18f, 0.12f) },
		{ TEXT("INFECTED"), TEXT("Defence +50 %, but your health drains and will not regenerate."),  FLinearColor(0.30f, 0.85f, 0.35f) },
		{ TEXT("THE CURE"), TEXT("Vesna in the castle brews the antidote. Your first one is free."),  FLinearColor(1.00f, 0.74f, 0.30f) },
	};

	static const FLinearColor Gold(0.86f, 0.65f, 0.30f, 1.f);
	static const FLinearColor GoldDim(0.55f, 0.41f, 0.18f, 1.f);
	static const FLinearColor TitleGold(1.00f, 0.82f, 0.45f, 1.f);
	static const FLinearColor Parchment(0.93f, 0.87f, 0.74f, 1.f);
	static const FLinearColor Leather(0.045f, 0.032f, 0.022f, 0.96f);

	template <typename T> static T* Prop(const UObject* Obj, FName Name)
	{
		return Obj ? FindFProperty<T>(Obj->GetClass(), Name) : nullptr;
	}
	static int32 GetInt(UObject* Obj, FName Name, int32 Default = 0)
	{
		const FIntProperty* P = Prop<FIntProperty>(Obj, Name);
		return P ? P->GetPropertyValue_InContainer(Obj) : Default;
	}
	static void SetInt(UObject* Obj, FName Name, int32 Value)
	{
		if (const FIntProperty* P = Prop<FIntProperty>(Obj, Name)) { P->SetPropertyValue_InContainer(Obj, Value); }
	}
	static bool GetBool(UObject* Obj, FName Name)
	{
		const FBoolProperty* P = Prop<FBoolProperty>(Obj, Name);
		return P && P->GetPropertyValue_InContainer(Obj);
	}
	static void SetBool(UObject* Obj, FName Name, bool bValue)
	{
		if (const FBoolProperty* P = Prop<FBoolProperty>(Obj, Name)) { P->SetPropertyValue_InContainer(Obj, bValue); }
	}

	static void Box(UCanvas* C, float X, float Y, float W, float H, const FLinearColor& Col)
	{
		FCanvasTileItem T(FVector2D(X, Y), FVector2D(W, H), Col);
		T.BlendMode = SE_BLEND_Translucent;
		C->DrawItem(T);
	}
	static void BoxFrame(UCanvas* C, float X, float Y, float W, float H, float T, const FLinearColor& Col)
	{
		Box(C, X, Y, W, T, Col); Box(C, X, Y + H - T, W, T, Col);
		Box(C, X, Y + T, T, H - 2 * T, Col); Box(C, X + W - T, Y + T, T, H - 2 * T, Col);
	}
	static void BoxDiamond(UCanvas* C, float Cx, float Cy, float R, const FLinearColor& Col)
	{
		// stacked bars make a small diamond (canvas has no rotated quads without a material)
		const int32 Steps = FMath::Max(3, FMath::RoundToInt(R));
		for (int32 i = -Steps; i <= Steps; ++i)
		{
			const float Half = R * (1.f - FMath::Abs(float(i)) / float(Steps + 1));
			Box(C, Cx - Half, Cy + i * (R / Steps), Half * 2.f, R / Steps + 0.5f, Col);
		}
	}
	// Text at a target cap height in pixels; returns the drawn width.
	static float Label(UCanvas* C, UFont* F, const FString& S, float X, float Y, float PxHeight, const FLinearColor& Col, bool bCenter, bool bShadow = true)
	{
		if (!F) { F = GEngine->GetMediumFont(); }
		float W = 0.f, H = 0.f;
		C->TextSize(F, S, W, H, 1.f, 1.f);
		const float Sc = H > 0.f ? PxHeight / H : 1.f;
		const float DX = bCenter ? -W * Sc * 0.5f : 0.f;
		FCanvasTextItem T(FVector2D(X + DX, Y), FText::FromString(S), F, Col);
		T.Scale = FVector2D(Sc, Sc);
		T.BlendMode = SE_BLEND_Translucent;
		if (bShadow) { T.EnableShadow(FLinearColor(0.f, 0.f, 0.f, 0.85f * Col.A), FVector2D(FMath::Max(1.f, PxHeight * 0.06f))); }
		C->DrawItem(T);
		return W * Sc;
	}
	static float TextWidth(UCanvas* C, UFont* F, const FString& S, float PxHeight)
	{
		if (!F) { F = GEngine->GetMediumFont(); }
		float W = 0.f, H = 0.f;
		C->TextSize(F, S, W, H, 1.f, 1.f);
		return H > 0.f ? W * PxHeight / H : W;
	}
	static TArray<FString> Wrap(UCanvas* C, UFont* F, const FString& S, float PxHeight, float MaxW)
	{
		TArray<FString> Words, Lines;
		S.ParseIntoArray(Words, TEXT(" "));
		FString Cur;
		for (const FString& Wd : Words)
		{
			const FString Try = Cur.IsEmpty() ? Wd : Cur + TEXT(" ") + Wd;
			if (!Cur.IsEmpty() && TextWidth(C, F, Try, PxHeight) > MaxW) { Lines.Add(Cur); Cur = Wd; }
			else { Cur = Try; }
		}
		if (!Cur.IsEmpty()) { Lines.Add(Cur); }
		return Lines;
	}
	static FLinearColor A(FLinearColor C, float Alpha) { C.A *= Alpha; return C; }

	// Menus (soldier orders, recruiting, shop, skill tree, death screen) only flip PC->bShowMouseCursor; the viewport stayed in
	// game-only input with the mouse captured, so the cursor did not appear until a click released it and the first click was
	// lost. Follow the flag: cursor on -> Game+UI without capture (cursor at once, first click counts); off -> game only.
	// Called from Tick and again right after the HUD pass, because some HUD levels set the flag while they draw.
	// 11-06 playtest "no mouse cursor at Muster": BPC_Muster opens with bShowMouseCursor = true, but HUD levels drawn after it
	// (BP_BarracksHUD sets the flag from its own recruit/orders menu state in several draw paths) turn it off again in the same
	// frame, so the cursor never shows while Muster is open. While a BPC_Muster component reports Open, the cursor stays on.
	static bool IsMusterOpen(APlayerController* PC)
	{
		static TWeakObjectPtr<UActorComponent> GMuster;
		static double GLastSearch = -100.0;
		UActorComponent* M = GMuster.Get();
		const double Now = FPlatformTime::Seconds();
		if (!M && Now - GLastSearch > 2.0)
		{
			GLastSearch = Now;
			TArray<AActor*> Owners = { PC, PC->GetPawn(), PC->GetHUD() };
			for (AActor* A : Owners)
			{
				if (!A || M) { continue; }
				for (UActorComponent* Comp : A->GetComponents())
				{
					if (Comp && Comp->GetClass()->GetName().StartsWith(TEXT("BPC_Muster"))) { M = Comp; break; }
				}
			}
			if (!M)
			{
				for (TObjectIterator<UActorComponent> It; It; ++It)
				{
					if (It->GetWorld() == PC->GetWorld() && It->GetClass()->GetName().StartsWith(TEXT("BPC_Muster"))) { M = *It; break; }
				}
			}
			GMuster = M;
		}
		if (!M) { return false; }
		const FBoolProperty* Open = FindFProperty<FBoolProperty>(M->GetClass(), TEXT("Open"));
		return Open && Open->GetPropertyValue_InContainer(M);
	}

	// #446 (owner, 11-02 play-test) "the mouse cursor disappears while Vesna's store is open": same cause as Muster, other HUD
	// levels drawn after BPC_VesnaTrade clear bShowMouseCursor in the same frame. BPC_VesnaTrade's own open test is
	// MPC_SkillTree.Trade.R > 0 while the game is paused; while that holds the cursor stays on.
	static bool IsVesnaOpen(APlayerController* PC)
	{
		static TWeakObjectPtr<UMaterialParameterCollection> GMPC;
		if (!GMPC.IsValid()) { GMPC = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/CastleDefender/UI/SkillTree/MPC_SkillTree.MPC_SkillTree")); }
		UWorld* W = PC ? PC->GetWorld() : nullptr;
		if (!GMPC.IsValid() || !W || !W->IsPaused()) { return false; }
		const FLinearColor Trade = UKismetMaterialLibrary::GetVectorParameterValue(W, GMPC.Get(), TEXT("Trade"));
		return Trade.R > 0.5f;
	}

	// #553 commander card (11-06): same trap as Muster; while BPC_CommanderCard.Open the cursor stays on.
	static bool IsCommanderCardOpen(APlayerController* PC)
	{
		static TWeakObjectPtr<UActorComponent> GCard; static double GLastSearch = -100.0;
		UActorComponent* M = GCard.Get(); const double Now = FPlatformTime::Seconds();
		if (!M && Now - GLastSearch > 2.0)
		{
			GLastSearch = Now;
			if (APawn* Pawn = PC ? PC->GetPawn() : nullptr)
			{
				for (UActorComponent* Comp : Pawn->GetComponents()) { if (Comp && Comp->GetClass()->GetName().StartsWith(TEXT("BPC_CommanderCard"))) { M = Comp; break; } }
			}
			GCard = M;
		}
		if (!M) { return false; }
		const FBoolProperty* Open = FindFProperty<FBoolProperty>(M->GetClass(), TEXT("Open"));
		return Open && Open->GetPropertyValue_InContainer(M);
	}

	static void SyncCursorMode(APlayerController* PC)
	{
		if (!PC) { return; }
		if (!PC->bShowMouseCursor && (IsMusterOpen(PC) || IsVesnaOpen(PC) || IsCommanderCardOpen(PC))) { PC->bShowMouseCursor = true; }
		static TMap<TWeakObjectPtr<APlayerController>, bool> GCursorWas;
		bool& bWas = GCursorWas.FindOrAdd(PC, false);
		if (PC->bShowMouseCursor == bWas) { return; }
		bWas = PC->bShowMouseCursor;
		if (bWas)
		{
			FInputModeGameAndUI Mode;
			Mode.SetHideCursorDuringCapture(false);
			Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
			PC->SetInputMode(Mode);
		}
		else
		{
			PC->SetInputMode(FInputModeGameOnly());
		}
		UE_LOG(LogTemp, Log, TEXT("CDHudPolish: cursor %s -> input mode %s"), bWas ? TEXT("on") : TEXT("off"), bWas ? TEXT("GameAndUI") : TEXT("GameOnly"));
	}

	// Recruit / commander menus (BP_BarracksHUD) keep their open state in MPC_Barracks: Fx.R (recruit) and Ord.R (orders) > 0.5.
	// They close on E or Escape; the close button below presses E for one frame so the Blueprint runs its own close path.
	static int32 GCloseKeyHeld = 0;
	static const TCHAR* BarracksMPCPath = TEXT("/Game/CastleDefender/UI/Barracks/MPC_Barracks.MPC_Barracks");
	static bool IsBarracksMenuOpen(UWorld* W)
	{
		static TWeakObjectPtr<UMaterialParameterCollection> GMPC;
		if (!GMPC.IsValid()) { GMPC = LoadObject<UMaterialParameterCollection>(nullptr, BarracksMPCPath); }
		if (!GMPC.IsValid() || !W) { return false; }
		const FLinearColor Ord = UKismetMaterialLibrary::GetVectorParameterValue(W, GMPC.Get(), TEXT("Ord"));
		const FLinearColor Fx = UKismetMaterialLibrary::GetVectorParameterValue(W, GMPC.Get(), TEXT("Fx"));
		return Ord.R > 0.5f || Fx.R > 0.5f;
	}
}

// Test helper (11-06, used by the agent to play-test menus without a person at the keyboard):
// cd.Debug.ClickAt <fx> <fy> moves the mouse to that fraction of the viewport and clicks the left button (press, then release
// two ticks later), through the same PlayerInput path a real click takes. Development only.
static FAutoConsoleCommandWithWorldAndArgs GCmdClickAt(TEXT("cd.Debug.ClickAt"), TEXT("cd.Debug.ClickAt <fx> <fy>: click the left mouse button at that fraction of the game viewport."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* W)
	{
		APlayerController* PC = W ? W->GetFirstPlayerController() : nullptr;
		if (!PC || !PC->PlayerInput || Args.Num() < 2) { return; }
		int32 SX = 0, SY = 0; PC->GetViewportSize(SX, SY);
		PC->SetMouseLocation(FMath::RoundToInt(FCString::Atof(*Args[0]) * SX), FMath::RoundToInt(FCString::Atof(*Args[1]) * SY));
		TWeakObjectPtr<APlayerController> WPC(PC);
		int32* Step = new int32(0);
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([WPC, Step](float)
		{
			APlayerController* P = WPC.Get();
			if (!P || !P->PlayerInput) { delete Step; return false; }
			if (*Step == 1) { P->PlayerInput->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton, IE_Pressed, 1.f)); }
			if (*Step == 3) { P->PlayerInput->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::LeftMouseButton, IE_Released, 0.f)); delete Step; return false; }
			++*Step; return true;
		}));
	}));

using namespace CDHudPolish;

bool UCDHudPolish::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UCDHudPolish::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	PostRenderHandle = AHUD::OnHUDPostRender.AddUObject(this, &UCDHudPolish::OnPostRender);
	Font = LoadObject<UFont>(nullptr, FontPath);
}

void UCDHudPolish::Deinitialize()
{
	AHUD::OnHUDPostRender.Remove(PostRenderHandle);
	SetDeathHidden(false);
	Super::Deinitialize();
}

TStatId UCDHudPolish::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UCDHudPolish, STATGROUP_Tickables);
}

APawn* UCDHudPolish::GetPlayerPawn() const
{
	return UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
}

UActorComponent* UCDHudPolish::FindInfection(APawn* Pawn) const
{
	if (!Pawn) { return nullptr; }
	for (UActorComponent* Comp : Pawn->GetComponents())
	{
		if (Comp && Comp->GetClass()->GetName().StartsWith(TEXT("BPC_Infection"))) { return Comp; }
	}
	return nullptr;
}

bool UCDHudPolish::IsPawnDead(APawn* Pawn) const
{
	return GetBool(Pawn, NAME_IsDead);
}

void UCDHudPolish::SetDeathHidden(bool bHide)
{
	if (bHide)
	{
		// also catches widgets that appear while the death screen is up (new spawns)
		for (TObjectIterator<UWidgetComponent> It; It; ++It)
		{
			UWidgetComponent* W = *It;
			if (W && W->GetWorld() == GetWorld() && W->GetWidgetSpace() == EWidgetSpace::Screen && W->IsVisible())
			{
				W->SetVisibility(false);
				HiddenWidgets.AddUnique(W);
			}
		}
	}
	else
	{
		for (const TWeakObjectPtr<UWidgetComponent>& W : HiddenWidgets)
		{
			if (W.IsValid()) { W->SetVisibility(true); }
		}
		HiddenWidgets.Reset();
	}
	bDeathHidden = bHide;
}

void UCDHudPolish::Tick(float DeltaTime)
{
	if (!GEnable)
	{
		if (bDeathHidden) { SetDeathHidden(false); }
		return;
	}
	APlayerController* MenuPC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	SyncCursorMode(MenuPC);
	// release the simulated close key one frame after the close button pressed it
	if (GCloseKeyHeld > 0 && MenuPC && MenuPC->PlayerInput && --GCloseKeyHeld == 0)
	{
		MenuPC->PlayerInput->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::E, IE_Released, 0.f));
	}

	APawn* Pawn = GetPlayerPawn();
	const bool bDead = IsPawnDead(Pawn);
	if (bDead) { SetDeathHidden(true); }
	else if (bDeathHidden) { SetDeathHidden(false); }

	UActorComponent* Inf = FindInfection(Pawn);
	const int32 Card = GetInt(Inf, NAME_ExplainCard);
	if (Inf && Card > 0)
	{
		if (bDead)
		{
			// the killing bite opened the explainer: cancel it, explain at the next infection the player survives
			SetInt(Inf, NAME_ExplainCard, 0);
			SetBool(Inf, NAME_InfectSeen, false);   // the death screen keeps its own pause (Rise Again reloads the level)
		}
		else
		{
			// park the card so the Blueprint HUD pass does not draw its own box or consume the click; restored in OnPostRender
			ParkedInfection = Inf;
			ParkedCard = Card;
			SetInt(Inf, NAME_ExplainCard, 0);
			// a card is modal: keep the game paused so Space / click never reach the character (no jump, no swing).
			// BPC_Infection.NextCard unpauses after the last card, exactly as before.
			if (!UGameplayStatics::IsGamePaused(GetWorld())) { UGameplayStatics::SetGamePaused(GetWorld(), true); }
		}
	}
}

void UCDHudPolish::OnPostRender(AHUD* Hud, UCanvas* Canvas)
{
	if (!Hud || Hud->GetWorld() != GetWorld() || !Canvas) { return; }

	int32 Card = 0;
	UActorComponent* Inf = ParkedInfection.Get();
	if (Inf)
	{
		Card = ParkedCard;
		SetInt(Inf, NAME_ExplainCard, ParkedCard);
		ParkedInfection.Reset();
		ParkedCard = 0;
	}
	if (!GEnable) { return; }

	APlayerController* HudPC = Hud->GetOwningPlayerController();
	SyncCursorMode(HudPC);

	APawn* Pawn = GetPlayerPawn();
	if (IsPawnDead(Pawn)) { LastDrawnCard = 0; return; }

	// CLOSE button for the recruit / commander menus (they already close on E or Escape, but nothing said so)
	if (HudPC && HudPC->bShowMouseCursor && !(Inf && Card > 0) && IsBarracksMenuOpen(GetWorld()))
	{
		UFont* F = Font.Get();
		const float s = Canvas->ClipY / 1080.f;
		const float BW = 210.f * s, BH = 46.f * s, BX = Canvas->ClipX - BW - 28.f * s, BY = 28.f * s;
		float MX = 0.f, MY = 0.f;
		const bool bHasMouse = HudPC->GetMousePosition(MX, MY);
		const bool bHover = bHasMouse && MX >= BX && MX <= BX + BW && MY >= BY && MY <= BY + BH;
		Box(Canvas, BX + 5 * s, BY + 6 * s, BW, BH, FLinearColor(0.f, 0.f, 0.f, 0.45f));
		Box(Canvas, BX, BY, BW, BH, bHover ? FLinearColor(0.16f, 0.09f, 0.05f, 0.96f) : Leather);
		BoxFrame(Canvas, BX, BY, BW, BH, FMath::Max(1.5f, 2.f * s), bHover ? TitleGold : Gold);
		BoxDiamond(Canvas, BX, BY + BH * 0.5f, 6.f * s, Gold);
		BoxDiamond(Canvas, BX + BW, BY + BH * 0.5f, 6.f * s, Gold);
		Label(Canvas, F, TEXT("X   CLOSE   (E)"), BX + BW * 0.5f, BY + (BH - 21.f * s) * 0.5f - 1.f * s, 21.f * s, bHover ? TitleGold : Parchment, true);
		if (bHover && GCloseKeyHeld == 0 && HudPC->WasInputKeyJustPressed(EKeys::LeftMouseButton) && HudPC->PlayerInput)
		{
			HudPC->PlayerInput->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::E, IE_Pressed, 1.f));
			GCloseKeyHeld = 2;   // released by Tick after the HUD has seen it
		}
	}

	if (Inf && Card > 0)
	{
		const double Now = FPlatformTime::Seconds();
		if (Card != LastDrawnCard) { CardShownAt = Now; LastDrawnCard = Card; }
		DrawCard(Hud, Canvas, Card);
		APlayerController* PC = Hud->GetOwningPlayerController();
		const bool bAdvance = PC && Now - CardShownAt > 0.3 &&
			(PC->WasInputKeyJustPressed(EKeys::LeftMouseButton) || PC->WasInputKeyJustPressed(EKeys::SpaceBar) || PC->WasInputKeyJustPressed(EKeys::Enter));
		if (bAdvance)
		{
			if (UFunction* Fn = Inf->FindFunction(NAME_NextCard)) { Inf->ProcessEvent(Fn, nullptr); }
		}
		return;
	}
	LastDrawnCard = 0;

	if (UActorComponent* Live = FindInfection(Pawn))
	{
		if (GetBool(Live, NAME_Infected)) { DrawInfectionBanner(Canvas); }
	}
}

void UCDHudPolish::DrawCard(AHUD* Hud, UCanvas* C, int32 Card)
{
	const FCard& D = Cards[FMath::Clamp(Card, 1, NumCards) - 1];
	UFont* F = Font.Get();
	const float SW = C->ClipX, SH = C->ClipY, s = SH / 1080.f;
	const float Fade = FMath::Clamp(float(FPlatformTime::Seconds() - CardShownAt) / 0.22f, 0.f, 1.f);
	const float Ease = 1.f - FMath::Square(1.f - Fade);

	Box(C, 0, 0, SW, SH, FLinearColor(0.f, 0.f, 0.f, 0.45f * Ease));

	const float W = 760.f * s, H = 300.f * s;
	const float X = (SW - W) * 0.5f, Y = SH * 0.42f - H * 0.5f + (1.f - Ease) * 18.f * s;
	Box(C, X + 10 * s, Y + 14 * s, W, H, FLinearColor(0.f, 0.f, 0.f, 0.45f * Ease));                 // drop shadow
	Box(C, X, Y, W, H, A(Leather, Ease));
	Box(C, X, Y, W, 92.f * s, FLinearColor(0.10f, 0.068f, 0.04f, 0.55f * Ease));                    // lit title band
	Box(C, X, Y + H - 56.f * s, W, 56.f * s, FLinearColor(0.f, 0.f, 0.f, 0.25f * Ease));             // footer band
	Box(C, X, Y, 6.f * s, H, A(D.Accent, 0.9f * Ease));                                               // accent edge
	BoxFrame(C, X, Y, W, H, FMath::Max(2.f, 3.f * s), A(Gold, Ease));
	BoxFrame(C, X + 9 * s, Y + 9 * s, W - 18 * s, H - 18 * s, FMath::Max(1.f, 1.f * s), A(GoldDim, 0.85f * Ease));
	for (const FVector2D& P : { FVector2D(X, Y), FVector2D(X + W, Y), FVector2D(X, Y + H), FVector2D(X + W, Y + H) })
	{
		BoxDiamond(C, P.X, P.Y, 9.f * s, A(Gold, Ease));
	}

	const float Cx = X + W * 0.5f;
	Label(C, F, D.Title, Cx, Y + 26.f * s, 46.f * s, A(TitleGold, Ease), true);
	const float LineY = Y + 92.f * s;
	Box(C, Cx - 200.f * s, LineY, 400.f * s, FMath::Max(1.f, 1.5f * s), A(GoldDim, Ease));
	BoxDiamond(C, Cx, LineY, 6.f * s, A(Gold, Ease));

	const float BodyPx = 27.f * s;
	const TArray<FString> Lines = Wrap(C, F, D.Body, BodyPx, W - 120.f * s);
	float By = Y + 120.f * s + (Lines.Num() == 1 ? 18.f * s : 0.f);
	for (const FString& L : Lines)
	{
		Label(C, F, L, Cx, By, BodyPx, A(Parchment, Ease), true);
		By += BodyPx * 1.55f;
	}

	const float Pulse = 0.65f + 0.35f * FMath::Sin(float(FPlatformTime::Seconds()) * 3.2f);
	Label(C, F, TEXT("CLICK, SPACE OR ENTER TO CONTINUE"), Cx, Y + H - 40.f * s, 17.f * s, A(FLinearColor(0.80f, 0.70f, 0.48f, 1.f), Ease * Pulse), true, false);
	const FString Page = FString::Printf(TEXT("%d / %d"), FMath::Clamp(Card, 1, NumCards), NumCards);
	Label(C, F, Page, X + W - 30.f * s - TextWidth(C, F, Page, 17.f * s), Y + H - 40.f * s, 17.f * s, A(GoldDim, Ease), false, false);
}

void UCDHudPolish::DrawInfectionBanner(UCanvas* C)
{
	UFont* F = Font.Get();
	const float SW = C->ClipX, SH = C->ClipY, s = SH / 1080.f;
	const float T = float(FPlatformTime::Seconds());
	const float Pulse = 0.5f + 0.5f * FMath::Sin(T * 2.6f);

	const FString Head = TEXT("INFECTED");
	const FString Tail = TEXT("Health drains  -  get the antidote from Vesna in the castle");
	const float HeadPx = 24.f * s, TailPx = 19.f * s, Gap = 22.f * s;
	const float Wd = TextWidth(C, F, Head, HeadPx) + Gap + TextWidth(C, F, Tail, TailPx) + 70.f * s;
	const float H = 46.f * s;
	const float X = (SW - Wd) * 0.5f, Y = SH * 0.115f;

	Box(C, X, Y, Wd, H, FLinearColor(0.015f, 0.04f, 0.02f, 0.84f));
	Box(C, X, Y, Wd, H, FLinearColor(0.20f, 0.85f, 0.30f, 0.06f + 0.08f * Pulse));
	Box(C, X, Y, Wd, FMath::Max(1.f, 2.f * s), A(Gold, 0.75f + 0.25f * Pulse));
	Box(C, X, Y + H - FMath::Max(1.f, 2.f * s), Wd, FMath::Max(1.f, 2.f * s), A(Gold, 0.75f + 0.25f * Pulse));
	BoxDiamond(C, X, Y + H * 0.5f, 7.f * s, Gold);
	BoxDiamond(C, X + Wd, Y + H * 0.5f, 7.f * s, Gold);

	float Tx = X + 35.f * s;
	Tx += Label(C, F, Head, Tx, Y + (H - HeadPx) * 0.5f - 2.f * s, HeadPx, FLinearColor(0.45f, 1.f, 0.50f, 0.85f + 0.15f * Pulse), false);
	Tx += Gap;
	Label(C, F, Tail, Tx, Y + (H - TailPx) * 0.5f - 1.f * s, TailPx, Parchment, false);
}
