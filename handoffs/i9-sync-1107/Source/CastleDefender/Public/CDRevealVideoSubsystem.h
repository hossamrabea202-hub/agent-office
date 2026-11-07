// 11-06 owner: "I don't like the skill tree / inventory reveal, I made videos for them; the hero can't move until the reveal is done."
// 15:30 owner: "ugly and pixelated: 40 % smaller; pop in (spin + grow from zero), when done shrink and fly to the HUD icon it stands for
//   (bag -> inventory key icon, book -> skill tree key icon) with a spin, pop sounds in and out."
// This world subsystem replaces the BPC_MotionFX live-3D reveal (its start gate is set to never fire: rvLess_DoubleDou71/81 B = 0):
//   - watches MPC_SkillTree BookAge / BagAge like the old reveal (first frame in 0.05..2 s, once per item, a loaded save never replays),
//   - plays the owner's MP4 (MS_RevealBook / MS_RevealInventory via MP_Reveal -> MT_Reveal -> M_UI_RevealVideo, circle mask in the material)
//     as a Slate overlay above the HUD, cd.Reveal.Size of the viewport height (0.42),
//   - pop in: cd.Reveal.PopIn seconds, scale 0 -> 1 with overshoot, one spin; pop out: cd.Reveal.PopOut seconds, shrinks to the HUD icon's
//     size while flying to the icon's spot (positions copied from the native ZombieHUD / SkillTreeHUD draw code) with one spin,
//   - pop sounds SFX_RevealPopIn / SFX_RevealPopOut (fallback: the old SFX_Reveal_Whoosh / SFX_Reveal_Hit),
//   - freezes the hero from pop-in to the end of the pop-out (move + look input ignored, movement stopped, UCDCombatRules::GateHeroAttack
//     returns false, keys and clicks swallowed by the overlay), optionally pauses the world (cd.Reveal.Pause 1),
//   - then frees the hero and pulses BPC_MotionFX.BookOpenNow / BagOpenNow for one frame so the HUD opens the tree / pack through its own
//     T / I code path, exactly as after the old reveal.
// cd.Reveal.Video 0 = off (nothing plays; put the two Blueprint defaults back to 2.0 for the old reveal).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Styling/SlateBrush.h"
#include "CDRevealVideoSubsystem.generated.h"

class UMediaPlayer;
class UMediaSource;
class UMaterialInstanceDynamic;
class UMaterialParameterCollection;
class SWidget;
class APlayerController;
class APawn;

UCLASS()
class CASTLEDEFENDER_API UCDRevealVideoSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override;
	virtual bool IsTickableWhenPaused() const override { return true; }
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UCDRevealVideoSubsystem, STATGROUP_Tickables); }

	// True while a reveal plays in any game world (CDCombatRules::GateHeroAttack reads it).
	static bool IsRevealPlaying();

	// Console / Blueprint helper: play one now (Item 0 = book, 1 = satchel), ignoring the once-per-item rule.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Reveal")
	bool PlayRevealNow(int32 Item);

private:
	enum class EItem : uint8 { None, Book, Bag };
	enum class EPhase : uint8 { Idle, PopIn, Play, PopOut };

	void Start(EItem Item);
	void BeginPopOut();
	void Finish(bool bOpenMenu);
	void ApplyFreeze(bool bFreeze);
	void UpdateTransform();
	void PlayPop(bool bIn) const;
	void SetOpenNow(EItem Item, bool bValue);
	UObject* FindMotionFX() const;
	float ReadAge(const TCHAR* Name) const;

	UFUNCTION() void HandleEndReached();
	UFUNCTION() void HandleOpenFailed(FString FailedUrl);

	UPROPERTY() TObjectPtr<UMediaPlayer> Player;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> MID;
	UPROPERTY() TObjectPtr<UMaterialParameterCollection> MPC;
	TWeakObjectPtr<APlayerController> FrozenPC;
	TWeakObjectPtr<APawn> FrozenPawn;
	TSharedPtr<SWidget> Overlay;
	TSharedPtr<SWidget> Image;      // the circle itself, gets the render transform
	FSlateBrush Brush;

	EItem Current = EItem::None;
	EPhase Phase = EPhase::Idle;
	EItem PulseItem = EItem::None;   // set true at the end of a reveal, cleared on the next tick
	bool bBookDone = false, bBagDone = false, bPendingBook = false, bPendingBag = false;
	bool bFrozen = false, bPausedByUs = false, bEndReached = false, bOpenFailed = false;
	double StartTime = 0.0, PhaseStart = 0.0;
};
