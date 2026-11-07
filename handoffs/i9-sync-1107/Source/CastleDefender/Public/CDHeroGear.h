// 2026-11-07 owner: "items in inventory doesnt match items hero wearing".
// One source of truth for what the hero wears. The inventory's Loc variables on the HUD (HelmLoc ... BootLoc: 0 = in its slot, 10+ = pack cell,
// -1 = held by the mouse, NoItem = not owned) say what is ON; BPC_WeaponKit.Equipped and BPC_ShieldKit.Worn say WHICH weapon and shield that is.
// This subsystem is the only writer of the hero's gear visibility, and the slot icons of the weapon and the shield are rendered from the same meshes.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDHeroGear.generated.h"

class UMaterialInterface;
class USkeletalMeshComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UTexture;
class UTexture2D;
class UActorComponent;

UCLASS()
class CASTLEDEFENDER_API UCDHeroGearSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()
public:
	// A Loc value that draws far outside the panel and matches no slot or pack cell: the item is not owned.
	static constexpr int32 NoItem = 998;

	virtual bool DoesSupportWorldType(const EWorldType::Type T) const override { return T == EWorldType::Game || T == EWorldType::PIE; }
	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickableWhenPaused() const override { return true; } // the inventory pauses the game, the hero behind it must still follow
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UCDHeroGearSubsystem, STATGROUP_Tickables); }

	// Slot and drag icons. Fallback is the painted icon, used until the render exists.
	static UTexture* WeaponIcon(const UObject* Ctx, UTexture* Fallback);
	static UTexture* ShieldIcon(const UObject* Ctx, UTexture* Fallback);
	// The DMG line: the equipped kit weapon's own damage, Fallback for the default longsword.
	static int32 WeaponDamage(const UObject* Ctx, int32 Fallback);
	// False while the weapon is in the pack or on the mouse.
	static bool WeaponWorn(const UWorld* World);

private:
	TWeakObjectPtr<APawn> Hero;
	TWeakObjectPtr<UActorComponent> WeaponKit, ShieldKit, Obsidian;
	TWeakObjectPtr<UStaticMeshComponent> KitWeapon, Sword, OffHand, ObsShield;
	TWeakObjectPtr<USkeletalMeshComponent> Knight;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> Underlayer;
	UPROPERTY(Transient) TMap<TObjectPtr<UStaticMesh>, TObjectPtr<UTexture2D>> Icons;
	UPROPERTY(Transient) TObjectPtr<UTexture2D> CurWeaponIcon;
	UPROPERTY(Transient) TObjectPtr<UTexture2D> CurShieldIcon;
	TMap<TObjectPtr<UStaticMesh>, double> RenderedAt; // the first render can catch low mips: rendered once more shortly after
	bool bSwordOn = true;
	bool bStarted = false;
	int32 LastEquipped = -2, LastWorn = -2, ParkedWorn = -1;
	double StartAt = -1.0;

	bool FindParts();
	void SyncWeapon(UObject* Hud);
	void SyncShield(UObject* Hud);
	void SyncBody(UObject* Hud);
	UTexture2D* IconFor(UStaticMesh* Mesh);
	UTexture2D* RenderIcon(UStaticMesh* Mesh);
};
