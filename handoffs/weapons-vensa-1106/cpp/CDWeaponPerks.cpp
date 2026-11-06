// DRAFT (audit seat, 2026-11-06), NOT compiled. See CDWeaponPerks.h. Numbers = handoffs/weapons-vensa-1106/weapons_vensa_1106.json.
#include "CDWeaponPerks.h"
#include "CDCombatRules.h"
#include "CDSaveGame.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "GameFramework/HUD.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"
#include "Engine/Font.h"
#include "Containers/Ticker.h"
#include "Misc/DelayedAutoRegister.h"
#include "InputCoreTypes.h"

namespace CDWeaponPerks
{
	static int32 GEnable = 1;
	static int32 GLog = 0;
	static FAutoConsoleVariableRef CVarEnable(TEXT("cd.Weapon.Perks"), GEnable, TEXT("1 = TGA weapon perks and upgrade levels apply (default). 0 = pass-through, the old game."));
	static FAutoConsoleVariableRef CVarLog(TEXT("cd.Weapon.PerkLog"), GLog, TEXT("1 = log every perk roll."));
	static const float DamagePerLevel = 0.12f;

	// The sheet. KitIndex = row in BPC_WeaponKit (10-31 order: 0 Arming Sword ... 25 Emberoath).
	static const FCDWeaponPerkRow GRows[] = {
		{ 0,  TEXT("Arming Sword"), ECDWeaponPerk::Regen,   TEXT("Knight's Vigil"),     TEXT("Wounds close on their own"),            { 2.0f, 3.0f, 4.0f, 5.0f },     { 150, 240, 360 } },
		{ 6,  TEXT("Longsword"),    ECDWeaponPerk::Parry,   TEXT("Half-Sword Parry"),   TEXT("Chance to turn a blow aside"),          { 0.12f, 0.15f, 0.18f, 0.22f }, { 300, 480, 720 } },
		{ 10, TEXT("War Axe"),      ECDWeaponPerk::Crit,    TEXT("Executioner's Edge"), TEXT("Chance of a triple-damage blow"),       { 0.15f, 0.18f, 0.22f, 0.25f }, { 230, 360, 540 } },
		{ 14, TEXT("Flanged Mace"), ECDWeaponPerk::Stagger, TEXT("Bone Breaker"),       TEXT("Every blow staggers; crushes colossi"), { 0.15f, 0.25f, 0.35f, 0.50f }, { 250, 400, 600 } },
		{ 23, TEXT("Halberd"),      ECDWeaponPerk::Reach,   TEXT("Reaper's Reach"),     TEXT("The sweep reaches further"),            { 210.f, 230.f, 250.f, 270.f }, { 550, 880, 1320 } },
	};
	static TMap<int32, int32> GLevels;          // kit index -> level 0..3
	static bool GLoaded = false;
	static double GFlashUntil = 0.0;            // HUD flash after a proc
	static FString GFlashText;
	static double GLastHitTime = -100.0;        // Regen pause after a hit

	static UActorComponent* FindComp(const AActor* A, const TCHAR* ClassPrefix)
	{
		if (!A) { return nullptr; }
		for (UActorComponent* C : A->GetComponents()) { if (C && C->GetClass()->GetName().StartsWith(ClassPrefix)) { return C; } }
		return nullptr;
	}
	template <typename T, typename P> static bool GetProp(const UObject* O, const TCHAR* Name, T& Out)
	{
		if (!O) { return false; }
		if (const P* Prop = FindFProperty<P>(O->GetClass(), Name)) { Out = Prop->GetPropertyValue_InContainer(O); return true; }
		return false;
	}
	template <typename T, typename P> static bool SetProp(UObject* O, const TCHAR* Name, T Val)
	{
		if (!O) { return false; }
		if (P* Prop = FindFProperty<P>(O->GetClass(), Name)) { Prop->SetPropertyValue_InContainer(O, Val); return true; }
		return false;
	}
	static AActor* SkillTreeHud(UWorld* W)
	{
		for (TActorIterator<AActor> It(W); It; ++It) { if (*It && (*It)->GetClass()->GetName().StartsWith(TEXT("BP_SkillTreeHUD"))) { return *It; } }
		return nullptr;
	}
	static void Flash(const FString& S)
	{
		GFlashText = S; GFlashUntil = FPlatformTime::Seconds() + 0.6;
		if (GLog) { UE_LOG(LogTemp, Display, TEXT("[CD] weapon perk: %s"), *S); }
	}
}
using namespace CDWeaponPerks;

const FCDWeaponPerkRow* UCDWeaponPerks::Row(int32 KitIndex)
{
	for (const FCDWeaponPerkRow& R : GRows) { if (R.KitIndex == KitIndex) { return &R; } }
	return nullptr;
}
bool UCDWeaponPerks::HasPerk(int32 KitIndex) { return Row(KitIndex) != nullptr; }

int32 UCDWeaponPerks::EquippedIndex(const UObject* Ctx)
{
	const APawn* Hero = UGameplayStatics::GetPlayerPawn(Ctx, 0);
	int32 E = -1;
	GetProp<int32, FIntProperty>(FindComp(Hero, TEXT("BPC_WeaponKit")), TEXT("Equipped"), E);
	return E;
}
int32 UCDWeaponPerks::WeaponLevel(const UObject* Ctx, int32 KitIndex)
{
	if (!GLoaded) { LoadLevels(Ctx); }
	const int32* L = GLevels.Find(KitIndex);
	return L ? FMath::Clamp(*L, 0, 3) : 0;
}

static const FCDWeaponPerkRow* EquippedRow(const UObject* Ctx, int32& OutLevel)
{
	if (!GEnable) { return nullptr; }
	const int32 E = UCDWeaponPerks::EquippedIndex(Ctx);
	OutLevel = UCDWeaponPerks::WeaponLevel(Ctx, E);
	return UCDWeaponPerks::Row(E);
}

double UCDWeaponPerks::HeroDamage(double In, const UObject* Ctx)
{
	const int32 E = EquippedIndex(Ctx);
	if (!GEnable || E < 0) { return In; }
	const int32 L = WeaponLevel(Ctx, E);
	double Out = In * (1.0 + DamagePerLevel * L);       // only the 5 rows can gain levels, so every other kit weapon stays x1
	if (const FCDWeaponPerkRow* R = Row(E))
	{
		if (R->Perk == ECDWeaponPerk::Crit && FMath::FRand() < R->Value[L]) { Out *= 3.0; Flash(TEXT("TRIPLE BLOW")); }
	}
	return Out;
}

double UCDWeaponPerks::SlashRadius(double In, const UObject* Ctx)
{
	int32 L = 0;
	const FCDWeaponPerkRow* R = EquippedRow(Ctx, L);
	return (R && R->Perk == ECDWeaponPerk::Reach) ? R->Value[L] : In;
}

double UCDWeaponPerks::HeroIncoming(double In, const UObject* Ctx)
{
	GLastHitTime = FPlatformTime::Seconds();
	int32 L = 0;
	const FCDWeaponPerkRow* R = EquippedRow(Ctx, L);
	if (R && R->Perk == ECDWeaponPerk::Parry && In > 0.0 && FMath::FRand() < R->Value[L]) { Flash(TEXT("PARRIED")); return In * 0.5; }
	return In;
}

bool UCDWeaponPerks::ForceStagger(const AActor* Causer)
{
	const APawn* Hero = Cast<APawn>(Causer);
	if (!GEnable || !Hero || !Hero->IsPlayerControlled()) { return false; }
	int32 L = 0;
	const FCDWeaponPerkRow* R = EquippedRow(Hero, L);
	return R && R->Perk == ECDWeaponPerk::Stagger;
}
float UCDWeaponPerks::StaggerBonus(const AActor* Causer, const AActor* Victim)
{
	if (!ForceStagger(Causer) || !UCDCombatRules::IsColossus(Victim)) { return 1.f; }
	int32 L = 0;
	const FCDWeaponPerkRow* R = EquippedRow(Causer, L);
	Flash(TEXT("CRUSHED"));
	return 1.f + R->Value[L];
}

// Regen: once per frame, the hero's DamageTaken (double, dies at >= 250) shrinks by Value[L] HP/s while the Arming Sword is equipped,
// not Infected (BPC_Infection.Infected), and 3 s after the last hit. The Blueprint's own regen (RegenGate chain) is untouched.
namespace CDWeaponPerks
{
	static FDelayedAutoRegisterHelper GRegen(EDelayedRegisterRunPhase::EndOfEngineInit, []()
	{
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float Dt)
		{
			if (!GEngine || !GEnable) { return true; }
			for (const FWorldContext& WC : GEngine->GetWorldContexts())
			{
				UWorld* W = WC.World();
				if (!W || !W->IsGameWorld() || W->IsPaused()) { continue; }
				APawn* Hero = UGameplayStatics::GetPlayerPawn(W, 0);
				int32 L = 0;
				const FCDWeaponPerkRow* R = EquippedRow(Hero, L);
				if (!R || R->Perk != ECDWeaponPerk::Regen) { continue; }
				if (FPlatformTime::Seconds() - GLastHitTime < 3.0) { continue; }
				bool bInfected = false;
				GetProp<bool, FBoolProperty>(FindComp(Hero, TEXT("BPC_Infection")), TEXT("Infected"), bInfected);
				if (bInfected) { continue; }
				double Taken = 0.0;
				if (GetProp<double, FDoubleProperty>(Hero, TEXT("DamageTaken"), Taken) && Taken > 0.0)
				{
					SetProp<double, FDoubleProperty>(Hero, TEXT("DamageTaken"), FMath::Max(0.0, Taken - R->Value[L] * Dt));
				}
			}
			return true;
		}));
	});
}

FString UCDWeaponPerks::UpgradeWeapon(const UObject* Ctx, int32 KitIndex)
{
	if (KitIndex < 0) { KitIndex = EquippedIndex(Ctx); }
	const FCDWeaponPerkRow* R = Row(KitIndex);
	if (!R) { return TEXT("This weapon cannot be upgraded."); }
	const int32 L = WeaponLevel(Ctx, KitIndex);
	if (L >= 3) { return TEXT("Already at its best."); }
	UWorld* W = GEngine ? GEngine->GetWorldFromContextObject(Ctx, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
	AActor* Tree = W ? SkillTreeHud(W) : nullptr;
	int32 Gold = 0;
	if (!GetProp<int32, FIntProperty>(Tree, TEXT("Gold"), Gold)) { return TEXT("No gold purse found."); }
	const int32 Cost = R->UpgradeCost[L];
	if (Gold < Cost) { return TEXT("Not enough gold, hunter."); }
	SetProp<int32, FIntProperty>(Tree, TEXT("Gold"), Gold - Cost);
	GLevels.Add(KitIndex, L + 1);
	SaveLevels(Ctx);
	return FString::Printf(TEXT("%s forged to level %d."), R->Name, L + 1);
}

void UCDWeaponPerks::SaveLevels(const UObject* Ctx)
{
	UWorld* W = GEngine ? GEngine->GetWorldFromContextObject(Ctx, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
	UGameInstance* GI = W ? W->GetGameInstance() : nullptr;
	UCDSaveSubsystem* S = GI ? GI->GetSubsystem<UCDSaveSubsystem>() : nullptr;
	if (!S) { return; }
	UCDSaveGame* D = S->LoadOrCreate(TEXT("WeaponPerks"));
	if (!D) { return; }
	for (const auto& KV : GLevels) { D->SetInt(*FString::Printf(TEXT("WeaponLevel_%d"), KV.Key), KV.Value); }
	S->Save(D, TEXT("WeaponPerks"));
}
void UCDWeaponPerks::LoadLevels(const UObject* Ctx)
{
	GLoaded = true; GLevels.Reset();
	UWorld* W = GEngine ? GEngine->GetWorldFromContextObject(Ctx, EGetWorldErrorMode::ReturnNull) : nullptr;
	UGameInstance* GI = W ? W->GetGameInstance() : nullptr;
	UCDSaveSubsystem* S = GI ? GI->GetSubsystem<UCDSaveSubsystem>() : nullptr;
	UCDSaveGame* D = S ? S->LoadOrCreate(TEXT("WeaponPerks")) : nullptr;
	if (!D) { return; }
	for (const FCDWeaponPerkRow& R : GRows) { GLevels.Add(R.KitIndex, D->GetInt(*FString::Printf(TEXT("WeaponLevel_%d"), R.KitIndex), 0)); }
}

// ---- HUD. Fonts / colours follow the WEAPONSMITH panel (Cinzel, parchment on dark). Card: right of the weapon list, 300 x 150 px at 1080p scale.
void UCDWeaponPerks::DrawShopCard(AHUD* Hud, int32 SizeX, int32 SizeY)
{
	if (!Hud || !GEnable) { return; }
	int32 L = 0;
	const FCDWeaponPerkRow* R = EquippedRow(Hud, L);
	if (!R) { return; }
	UFont* Font = LoadObject<UFont>(nullptr, TEXT("/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel"));
	const float S = SizeY / 1080.f;
	const float X = 384.f * S, Y = SizeY * 0.30f, Wd = 300.f * S, Ht = 150.f * S;
	Hud->DrawRect(FLinearColor(0.05f, 0.04f, 0.03f, 0.85f), X, Y, Wd, Ht);
	Hud->DrawText(FString(R->Name), FLinearColor(0.93f, 0.85f, 0.65f), X + 12 * S, Y + 10 * S, Font, 1.0f * S);
	Hud->DrawText(FString(R->PerkName) + TEXT("  -  ") + R->PerkText, FLinearColor(0.62f, 0.58f, 0.52f), X + 12 * S, Y + 40 * S, Font, 0.8f * S);
	FString Pips; for (int32 i = 0; i < 3; ++i) { Pips += (i < L) ? TEXT("* ") : TEXT("- "); }
	Hud->DrawText(TEXT("LEVEL ") + Pips, FLinearColor(0.93f, 0.85f, 0.65f), X + 12 * S, Y + 70 * S, Font, 0.8f * S);
	const FString Btn = (L >= 3) ? FString(TEXT("MAX")) : FString::Printf(TEXT("UPGRADE   %d g   [U]"), R->UpgradeCost[L]);
	Hud->DrawText(Btn, (L >= 3) ? FLinearColor(0.5f, 0.5f, 0.5f) : FLinearColor(0.93f, 0.85f, 0.65f), X + 12 * S, Y + 105 * S, Font, 0.9f * S);
	// input: U key or a click on the button line (the shop shows the cursor, so a click is safe: GateHeroAttack already swallows it)
	APlayerController* PC = Hud->GetOwningPlayerController();
	if (PC && L < 3)
	{
		float MX = 0, MY = 0; PC->GetMousePosition(MX, MY);
		const bool bClick = PC->WasInputKeyJustPressed(EKeys::LeftMouseButton) && MX >= X && MX <= X + Wd && MY >= Y + 100 * S && MY <= Y + Ht;
		if (PC->WasInputKeyJustPressed(EKeys::U) || bClick) { Flash(UpgradeWeapon(Hud)); GFlashUntil = FPlatformTime::Seconds() + 2.0; }
	}
	if (FPlatformTime::Seconds() < GFlashUntil) { Hud->DrawText(GFlashText, FLinearColor(1.f, 0.9f, 0.5f), X + 12 * S, Y + Ht + 8 * S, Font, 0.8f * S); }
}

void UCDWeaponPerks::DrawBadge(AHUD* Hud, int32 SizeX, int32 SizeY)
{
	if (!Hud || !GEnable) { return; }
	int32 L = 0;
	const FCDWeaponPerkRow* R = EquippedRow(Hud, L);
	if (!R) { return; }
	UFont* Font = LoadObject<UFont>(nullptr, TEXT("/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel"));
	const float S = SizeY / 1080.f;
	// under the HP bar (HeroHUD draws it bottom-left; the Master places the badge once in Play)
	Hud->DrawText(FString::Printf(TEXT("%s  L%d"), R->PerkName, L), FLinearColor(0.62f, 0.58f, 0.52f), 40 * S, SizeY - 70 * S, Font, 0.7f * S);
	if (FPlatformTime::Seconds() < GFlashUntil) { Hud->DrawText(GFlashText, FLinearColor(1.f, 0.9f, 0.5f), SizeX * 0.5f - 60 * S, SizeY * 0.62f, Font, 1.2f * S); }
}
