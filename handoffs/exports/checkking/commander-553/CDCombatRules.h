// Small combat rules used from Blueprints (owner 2026-11-05).
//   GateHeadshot: BP_CrossbowBolt's instant-kill headshot branch is skipped for colossi (BP_ZombieWallBreaker, or any zombie
//   wearing a *Colossus* material): they take the normal bolt damage instead. cd.Combat.ColossusHeadshot 1 restores the old rule.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
class UAnimMontage;
#include "CDCombatRules.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDCombatRules : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Combat")
	static bool IsColossus(const UObject* Zombie);

	// bIn = the bolt's own "hit the head" test. False for colossi.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Combat")
	static bool GateHeadshot(bool bIn, UObject* Zombie);

	// Gate-breach debris: Count physics pieces of SM_Debris_Beams (scaled small) thrown out from Location, gone after 6 s.
	// cd.Combat.GateDebris 0 = off. Cheap: no collision with pawns, simple physics, short life.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Combat", meta = (WorldContext = "WorldContextObject"))
	static void SpawnGateDebris(const UObject* WorldContextObject, FVector Location, int32 Count = 10);

	// 11-06 playtest: the click that closes a HUD menu (X, buttons) must not swing the sword. Wired in front of the hero's
	// attack branch (BP_ThirdPersonCharacter CX_3.Condition). False while the mouse cursor is shown (a menu is open) and for
	// cd.Combat.MenuClickGrace seconds (real time, 0.35) after it was hidden. bIn = the hero's own "left mouse just pressed".
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Combat", meta = (WorldContext = "WorldContextObject"))
	static bool GateHeroAttack(bool bIn, const UObject* WorldContextObject);

	// 11-06 playtest "swordsmen ran to the wall and got stuck": wired in front of BP_SoldierSword's SimpleMoveToLocation goals.
	// Returns Goal if the soldier (WorldContextObject = self) can actually walk there; if the navigation path would only be
	// partial (target outside the walls, e.g. a colossus), returns the soldier's own location: he holds his ground and waits
	// for the target to come in or for an order, instead of pressing into the wall. One path query per soldier per 0.75 s
	// (same goal within 1.5 m reuses the answer). cd.Combat.ReachableGoals 0 = old behaviour.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Combat", meta = (WorldContext = "WorldContextObject"))
	static FVector ReachableGoal(FVector Goal, const UObject* WorldContextObject);

	// 11-06 owner: "1 extra soldier rotating around him". The follow order (code 2) aims at a slot computed from the hero's position
	// AND facing, so turning swings the slot around the hero and the soldier runs circles (and ends inside him). For followers this
	// returns: own location (hold) while within cd.Soldier.FollowHold of the hero, else a point cd.Soldier.FollowDist from the hero on
	// the side the soldier already is. Other orders pass through. Insert after ReachableGoal on the general move (BP_SoldierSword CX_399).
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Combat", meta = (WorldContext = "WorldContextObject"))
	static FVector FollowGoal(FVector Goal, const UObject* WorldContextObject);

	// 11-06 directional flinch: wraps AZombieBase::PickFlinchMontage for a pin filter on BP_Zombie's Montage_Play nodes
	// (WorldContextObject = the zombie itself). Not a zombie: Default comes back unchanged.
	UFUNCTION(BlueprintPure, Category = "Castle Defender|Combat", meta = (WorldContext = "WorldContextObject"))
	static UAnimMontage* ZombieFlinch(UAnimMontage* Default, const UObject* WorldContextObject);

	// 11-06 tunnel chest extras (owner): on top of the gold, give the hero SkillPoints (skill tree HUD "SPT") and Potions
	// (BPC_PotionBelt "Potions"). Reflection by name, so no Blueprint type is referenced. Returns what it managed to add.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Loot", meta = (WorldContext = "WorldContextObject"))
	static FString GrantChestExtras(const UObject* WorldContextObject, int32 SkillPoints = 10, int32 Potions = 3);
};
