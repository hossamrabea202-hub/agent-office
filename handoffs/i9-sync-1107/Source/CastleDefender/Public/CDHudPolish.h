// HUD polish (owner, 2026-11-05): fixes how the canvas HUD chain behaves around infection and death, without editing the
// 11-level HUD Blueprints. It runs after the whole HUD has drawn (AHUD::OnHUDPostRender) and before it draws (world tick):
//   - Death screen owns the screen: while the player's IsDead flag is set, every visible screen-space widget component
//     (the jelly-shield zombies' health bars, mount / interact prompts) is hidden, and shown again on Rise Again.
//   - Bite explainer cards (BPC_Infection.ExplainCard 1..3: BITTEN / INFECTED / THE CURE) are drawn here instead of by
//     BP_NoticeHUD: a framed card in the game's dark-leather + gold style, with a page count and a readable footer.
//     The Blueprint never sees a pending card while it draws (ExplainCard is parked at 0 for the HUD pass), so it cannot
//     draw its old grey box or eat the click; NextCard is still the Blueprint's own event.
//   - A card that would open on the killing bite is cancelled (and InfectSeen cleared), so the explainer shows at the
//     first infection the player survives, never on the death screen (which keeps its own pause; Rise Again reloads).
//   - While infected and alive: a pulsing banner under the wave title says what is happening and where the cure is.
// Console: cd.HudPolish 0 turns all of it off (the Blueprint behaviour comes back exactly).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDHudPolish.generated.h"

class AHUD;
class UCanvas;
class UFont;
class UWidgetComponent;
class APawn;

UCLASS()
class CASTLEDEFENDER_API UCDHudPolish : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickableWhenPaused() const override { return true; }
	virtual ETickableTickType GetTickableTickType() const override { return IsTemplate() ? ETickableTickType::Never : ETickableTickType::Always; }

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	void OnPostRender(AHUD* Hud, UCanvas* Canvas);
	APawn* GetPlayerPawn() const;
	UActorComponent* FindInfection(APawn* Pawn) const;
	bool IsPawnDead(APawn* Pawn) const;
	void SetDeathHidden(bool bHide);
	void DrawCard(AHUD* Hud, UCanvas* Canvas, int32 Card);
	void DrawInfectionBanner(UCanvas* Canvas);

	FDelegateHandle PostRenderHandle;
	TArray<TWeakObjectPtr<UWidgetComponent>> HiddenWidgets;
	TWeakObjectPtr<UActorComponent> ParkedInfection;
	int32 ParkedCard = 0;
	bool bDeathHidden = false;
	double CardShownAt = 0.0;
	int32 LastDrawnCard = 0;
	TWeakObjectPtr<UFont> Font;
};
