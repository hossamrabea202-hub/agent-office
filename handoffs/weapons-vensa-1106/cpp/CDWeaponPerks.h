// DRAFT (audit seat, 2026-11-06), NOT compiled: weapon perks + upgrades for TGA's 5 AAA weapons (#397) sold at Vesna.
// Lives next to CDCombatRules (same pin-filter style: a pure function sits on an existing pin, Blueprint stays 1:1 when the
// weapon has no perk). Data: the FCDWeaponPerkRow table in the .cpp, keyed by the BPC_WeaponKit row index (Names/Prices/Damage/Speed/Meshes).
// Everything reads the Blueprints by name through reflection (like GrantChestExtras): BPC_WeaponKit "Equipped" (int),
// BP_SkillTreeHUD "Gold" (int), hero "DamageTaken" (double), BPC_Infection "Infected" (bool). No Blueprint type is referenced.
// Levels are saved by UCDSaveSubsystem (#500) in slot "WeaponPerks", Ints "WeaponLevel_<kit index>".
// cvars: cd.Weapon.Perks 1 (0 = every function passes its input through, the old game), cd.Weapon.PerkLog 0 (1 = log rolls).
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CDWeaponPerks.generated.h"

class AHUD;

UENUM(BlueprintType)
enum class ECDWeaponPerk : uint8 { None, Regen, Parry, Crit, Stagger, Reach };

struct FCDWeaponPerkRow
{
	int32 KitIndex = -1;                 // row in BPC_WeaponKit
	const TCHAR* Name = nullptr;         // for the HUD card
	ECDWeaponPerk Perk = ECDWeaponPerk::None;
	const TCHAR* PerkName = nullptr;
	const TCHAR* PerkText = nullptr;
	float Value[4] = { 0, 0, 0, 0 };     // perk value at level 0..3 (HP/s, chance, bonus, radius cm)
	int32 UpgradeCost[3] = { 0, 0, 0 };  // gold for level 1, 2, 3
};

UCLASS()
class CASTLEDEFENDER_API UCDWeaponPerks : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// ---- state
	// Equipped kit row of the hero (BPC_WeaponKit.Equipped), -1 = nothing. Level 0..3 of a row (saved).
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Weapons", meta = (WorldContext = "WorldContextObject"))
	static int32 EquippedIndex(const UObject* WorldContextObject);
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Weapons", meta = (WorldContext = "WorldContextObject"))
	static int32 WeaponLevel(const UObject* WorldContextObject, int32 KitIndex);
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Weapons")
	static bool HasPerk(int32 KitIndex);

	// ---- combat pin filters (hero EventGraph, BP_ThirdPersonCharacter)
	// Outgoing damage. Sits between WdMulSlash and ZX8/ZX9.BaseDamage, and between WdMulHit and CH7.BaseDamage.
	// x (1 + 0.12 x level); Crit: x3 with the row's chance. The Stagger colossus bonus is per victim (StaggerBonus, from ZombieBase::TakeDamage).
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Weapons", meta = (WorldContext = "WorldContextObject"))
	static double HeroDamage(double In, const UObject* WorldContextObject);
	// Slash radius. Sits on ZX8/ZX9.DamageRadius (150). Reach: the row's radius; else In.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Weapons", meta = (WorldContext = "WorldContextObject"))
	static double SlashRadius(double In, const UObject* WorldContextObject);
	// Incoming damage. Sits between shkMul4 (ShieldKit.LastMult product) and ObsDmg.B. Parry: x0.5 with the row's chance; else In.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Weapons", meta = (WorldContext = "WorldContextObject"))
	static double HeroIncoming(double In, const UObject* WorldContextObject);
	// For AZombieBase::PickFlinchMontage: true when the last hit came from the hero holding the Stagger weapon (force HitStagger).
	static bool ForceStagger(const AActor* Causer);
	// For AZombieBase::TakeDamage: extra multiplier on a colossus hit by the hero's Stagger weapon (1 when not).
	static float StaggerBonus(const AActor* Causer, const AActor* Victim);

	// ---- shop
	// Buys the next level of the equipped (or given) row with the hero's Gold. Returns what happened for the HUD message.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Weapons", meta = (WorldContext = "WorldContextObject"))
	static FString UpgradeWeapon(const UObject* WorldContextObject, int32 KitIndex = -1);
	// Drawn by the native ArmoryHUD right after BPC_WeaponKit.DrawWeapons (CDHudGen_BP_ArmoryHUD N_whHookWeapons5): the perk card
	// for the equipped TGA weapon: name, perk line, level pips, "UPGRADE  <cost> g  [U]" (or MAX), and the key U / click on the card.
	static void DrawShopCard(AHUD* Hud, int32 SizeX, int32 SizeY);
	// Drawn by the native HeroHUD under the HP bar: "<perk name> L<n>" badge + a 0.6 s flash on a crit / parry / stagger.
	static void DrawBadge(AHUD* Hud, int32 SizeX, int32 SizeY);

	static const FCDWeaponPerkRow* Row(int32 KitIndex);
	static void SaveLevels(const UObject* WorldContextObject);
	static void LoadLevels(const UObject* WorldContextObject);
};
