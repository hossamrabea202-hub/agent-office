# #553 C++ for the i9. Written by the i5 (checkking). None of this is built.

Read against your 11-06 copies in `handoffs/exports/checkking/commander-553/` (`CDHudPolish.cpp`, `SoldierBase.h`, `CDCombatRules.h`)
and `handoffs/cpp-500/Source/CastleDefender/CDHudBase.cpp`. Your live files may differ, so check before you edit.

Part A is required: without it the window never draws. Part B is the "he decides" brain for Defend the castle. Until it exists,
that button runs the plain Blueprint plan (see README).

## A. Three small hooks (required)

### A1. Draw the card last, on top of every HUD level

`ACDHudBase::DrawHUD()`, right after `Super::DrawHUD();`. No regeneration needed, and it works with native or Blueprint HUD levels.

```cpp
// CDHudBase.h
UPROPERTY(Transient) TWeakObjectPtr<UActorComponent> CommanderCard;   // BPC_CommanderCard on the pawn
void DrawCommanderCard();

// CDHudBase.cpp
void ACDHudBase::DrawCommanderCard()
{
	if (!Canvas) { return; }
	UActorComponent* C = CommanderCard.Get();
	if (!C)
	{
		APawn* Pawn = GetOwningPawn();
		if (!Pawn) { return; }
		for (UActorComponent* Comp : Pawn->GetComponents())
		{
			if (Comp && Comp->GetClass()->GetName().StartsWith(TEXT("BPC_CommanderCard"))) { C = Comp; CommanderCard = Comp; break; }
		}
		if (!C) { return; }
	}
	static const FName NAME_DrawCommander(TEXT("DrawCommander"));
	UFunction* F = C->FindFunction(NAME_DrawCommander);
	if (!F) { return; }
	struct { AHUD* Hud; int32 SizeX; int32 SizeY; } Params{ this, Canvas->SizeX, Canvas->SizeY };
	C->ProcessEvent(F, &Params);
}
```

`DrawHUD` still runs while the game is paused (The Muster relies on this). The window pauses the game.

### A2. Keep the cursor on while the card is open

`CDHudPolish.cpp`. `BP_BarracksHUD` turns `bShowMouseCursor` off in the same frame, the same trap you fixed for Muster. The card also sets it
every frame when it draws, and A1 draws last, so this may already be fine. It is cheap insurance.
Generalise `IsMusterOpen` to take the class prefix and keep one cached weak pointer per prefix:

```cpp
static bool IsPanelOpen(APlayerController* PC, const TCHAR* ClassPrefix);          // body = today's IsMusterOpen
// SyncCursorMode:
if (!PC->bShowMouseCursor && (IsPanelOpen(PC, TEXT("BPC_Muster")) || IsPanelOpen(PC, TEXT("BPC_CommanderCard")))) { PC->bShowMouseCursor = true; }
```

### A3. E near a commander opens the card, not the old wheel

Add to `UCDCombatRules`, same pattern as `GateHeroAttack`:

```cpp
// true = the old wheel may react to this E. False while the card owns E (open, or the hero is within 3 m of a commander).
UFUNCTION(BlueprintPure, Category = "Castle Defender|Combat", meta = (WorldContext = "WorldContextObject"))
static bool GateWheelKey(bool bIn, const UObject* WorldContextObject);
```

Body: `bIn && !(Card.Open || Card.NearCommander)`, both read by reflection from `BPC_CommanderCard` on the player pawn. If the card is missing, return `bIn`.

Put it where the BP_BarracksHUD E key opens the wheel. From the 11-06 export (`handoffs/exports/adjustedfilm/fresh-1106/BP_BarracksHUD.t3d.txt`):

| Site | Where the filter goes |
|---|---|
| Orders wheel | `CX_151.ReturnValue -> CX_152.Condition` |
| Second E path | `CX_405.ReturnValue -> CX_3124` |

Use `insert_pin_filter` for the Blueprint path. For the native layer, regenerate `CDHudGen_BP_BarracksHUD.cpp` or edit those two generated nodes by hand.
Don't filter `CX_23` itself: `CX_167` and `CX_419` use it to close menus.
I read these two sites from the graph and did not run them. If E still opens both, tell me and send a fresh export.
Soldiers more than 3 m from a commander keep the old wheel. Only the commander's wheel goes away.

## B. Defend the castle: the brain

The owner's words: "he decides how to lead and how much mount canons and which canons and cooperate with other commanders and decide how
much troops stay inside and when would they go outside".

The window pays your way:
- The button tags the commander `CD_DefendCastle`. Every other order removes the tag.
- His men carry the tags `Squad` and `Lead<N>`. `<N>` is his index in `BPC_CommanderCard.Known`.
- Name, age and the message line live on the card (`CmdName`, `CmdAge`, `Msg`, `MsgUntil`).
- `BP_CastleGateControl` gets `bGateOpen`, `CmdGateOpen()` and `CmdGateClose()` from `wire_gate_ue.py`. Call them by name.

```cpp
// CDCommanderBrain.h   Source/CastleDefender/Public
UENUM() enum class ECDDefensePlan : uint8 { Hold, ManGuns, ReinforceGate, Sortie, FallBack };

USTRUCT() struct FCDDefender
{
	GENERATED_BODY()
	TWeakObjectPtr<ASoldierBase> Commander;
	ECDDefensePlan Plan = ECDDefensePlan::Hold;
	double PlanSince = 0.0;                    // hysteresis: no plan change within cd.Commander.MinPlanSeconds
	int32 GunsWanted = 0;
	TArray<TWeakObjectPtr<AActor>> ClaimedGuns; // claims are shared across commanders
};

UCLASS()
class CASTLEDEFENDER_API UCDCommanderBrain : public UTickableWorldSubsystem
{
	GENERATED_BODY()
public:
	virtual void Tick(float DeltaSeconds) override;              // 1 Hz, stagger one commander per tick
	virtual TStatId GetStatId() const override;

	// Blueprint can ask; the window can show this as a line under the orders later.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Commander")
	FString GetPlanText(const AActor* Commander) const;

	UFUNCTION(BlueprintPure, Category = "Castle Defender|Commander")
	int32 GetCrewedGuns(const AActor* Commander) const;

private:
	void SyncDefenders();                                        // tag CD_DefendCastle on GetCachedActorsWithTag("Commander")
	void ReadThreat(struct FCDThreat& Out) const;
	ECDDefensePlan ChoosePlan(const FCDDefender& D, const FCDThreat& T) const;
	void ApplyPlan(FCDDefender& D, const FCDThreat& T);
	void GetMen(const AActor* Commander, TArray<ASoldierBase*>& Swords, TArray<ASoldierBase*>& Xbows) const;
	AActor* ClaimBestGun(FCDDefender& D, const FCDThreat& T);    // skips guns another commander claimed
	void SetOrder(ASoldierBase* S, int32 Code, const FVector& Goal);  // writes Order.X and Goal, only when they change
	void SetGate(bool bOpen);                                    // CmdGateOpen / CmdGateClose
	void Say(const AActor* Commander, const FString& Line);      // card Msg + MsgUntil
	TArray<FCDDefender> Defenders;
};
```

Rules to start from. All numbers are cvars, and these are my first guesses:

| Decision | Rule |
|---|---|
| Threat | Zombies from the wave manager's `ZombieReg`, counted by sector around the castle (6 sectors) within 60 m; `GateDamage` / `GateBroken`; live tentacles; colossi counted x5 |
| How many guns | `GunsWanted = clamp(threat / 12, 0, free guns)`, never more than a third of his men. Crossbows crew first, because they fight worst up close |
| Which guns | Most zombies inside that gun's arc and range (min range 21 m and -35 deg down, from your 11-05 fix). Claim it |
| Crew a gun | `Order.X = 3`, leave Y and Z at 0. Your Blueprint loop `CX_704/708` then seats him on the nearest free one. Point him at the claimed gun with `Goal` |
| Stay inside | Default. Crossbows code 4 (wall slots), swords code 5 at a gate-side point inside (150,1750,12) |
| Go outside (Sortie) | Gate intact, zombies near the gate fewer than `men x 1.5`, no colossus and no tentacle within 25 m of the gate, more than half his men above 60 % health. Open the gate, swords code 7 at (-420,1750,10), crossbows stay on the wall |
| Come back | Any Sortie rule fails, or his men fall below half: code 5 inside, gate shuts when none of his men are left outside or after 15 s |
| Gate breached | Plan FallBack: everyone code 7 at the breach, guns keep firing |
| Work together | Claims are shared, so no two commanders crew one gun. Only one commander sorties at a time; the other holds the wall. Sectors are split by distance to each commander. Gate requests go through `SetGate`, and "stay open" wins while any commander has men outside |
| Tell the player | `Say()` on a plan change only, for example "Aldric sends four men to the east guns" |

Pave-the-way notes:
- Cost: Order and Goal writes only on change. Use `GetCachedActorsWithTag`. Target under 0.2 ms per tick, with `STAT_CD_CommanderBrain` and `cd.Commander.Report`.
- `cd.Commander.Brain 0` is the off switch. The Blueprint plan stays in place, so off means the plain plan.
- Don't write `Goal` for code 3 men every tick: the seat loop keeps Goal in `Tmp.Z`.
- While the brain owns a commander, the card's `DefendCloseAt` must not close the gate. When you tag a commander in `SyncDefenders`, set the card's `DefendCloseAt = 0`.

Test without Play: `-run=CDBrainTest` style, with fake threat numbers through `ChoosePlan`, like your ZombieBrainTest.

## C. Small and optional

Names and ages reset each session, because the card hands them out by order of first talk. If you want them saved: add `FString CommanderName; int32 CommanderAge;` to the soldier save record and have the card read them first.
