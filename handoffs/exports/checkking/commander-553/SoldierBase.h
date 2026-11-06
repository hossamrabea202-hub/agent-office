// SoldierBase.h  -  REVIEW DRAFT rev 2 (2026-11-05, i9 Master). Not built, not in the project yet.
// Target location when approved: Source/CastleDefender/Public/SoldierBase.h
//
// Native parent for BP_SoldierSword (and through it BP_SoldierXbow / BP_SoldierCommander).
// Stage 1 has ONE goal: make soldiers cheaper without changing how they fight or take orders.
//   - Combat (ForEach NearZombies, CX_145) is NOT touched in stage 1 (rev 1 proposed nearest-only: dropped, that is a gameplay
//     change for a later, separate experiment).
//   - Native versions only for loops whose rule can be kept 1:1: releasing held zombies (CX_454) and formation slots
//     (the 4 nested slot x soldier loops).
//
// The Blueprint keeps its state in scene components used as number slots; this class reads them by reflection:
//   State.X = HP, State.Z < 0.5 = dead     Order.X = order code (0..7)     Goal = assigned spot
// Goal is only ever written with SetRelativeLocation and read as RelativeLocation in the Blueprint (2 writes, 7 reads,
// no world-location reads), so slots are compared in that same space, exactly like the Blueprint does.
// Required members are validated once per class in BeginPlay (see ValidateBlueprintContract); if anything is missing the
// native functions log an error and return the conservative result described on each function.
//
// Reparent happens OFFLINE (editor started without -CONCERTAUTOCONNECT): reparenting inside the live Multi-User session
// crashed ConcertSyncClient on 11-05.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SoldierBase.generated.h"

class USceneComponent;

UCLASS(Abstract)
class CASTLEDEFENDER_API ASoldierBase : public ACharacter
{
	GENERATED_BODY()

public:
	ASoldierBase();

	// ---- Release held zombies (replaces ForEach ZombieReg, CX_454) - same rule as the Blueprint ----
	// Every zombie in Registry (pass the wave manager's ZombieReg array, same array and order the Blueprint loops over)
	// within Radius whose CustomTimeDilation is the 0.999 "held" marker: CustomTimeDilation = NormalDilation,
	// Attacking = false, ResumeMove(). Note: the marker is global, not per-soldier ownership; this is inherited from
	// the Blueprint unchanged. Returns how many were released; 0 (and an error log) if the zombie class lacks
	// Attacking / ResumeMove().
	UFUNCTION(BlueprintCallable, Category = "Soldier|Brain")
	int32 ReleaseHeldZombies(const TArray<AActor*>& Registry, float Radius = 400.f, float NormalDilation = 1.f);

	// ---- Formation / post slot (replaces the nested loops CX_631/638, CX_704/708, CX_812/816, CX_844/848) ----
	// First slot (array order) that no other live soldier on the same order holds: his Goal within SlotRadius (2D), or
	// he reserved it within the last ReservationSeconds. The returned slot is reserved for this soldier at once, so two
	// soldiers deciding in the same frame cannot pick the same slot (the Blueprint version could). The Blueprint must
	// still Set Goal = Slots[result] right after the call (it does: no latent node in between).
	// Returns INDEX_NONE if every slot is taken, or if the soldier contract is invalid (then nothing is assigned,
	// which is the Blueprint's own "all taken" outcome).
	UFUNCTION(BlueprintCallable, Category = "Soldier|Brain")
	int32 PickFreeSlot(const TArray<FVector>& Slots, int32 OrderCode, float SlotRadius = 60.f, float ReservationSeconds = 2.f);

	// ---- Assign variant used by the rewired Blueprint (one call node replaces a slot x soldier loop pair) ----
	// Same "taken" rule as the Blueprint loop it replaces, then writes the slot into TargetVar exactly like the loop's
	// own Set Relative Location (bTeleport). Rules per call site (from the 11-05 dump):
	//   loop CX_631/638  gate wall : TargetVar Goal, SlotRadius 60, OrderCode 4, bMatchXbowTag false, bWriteTmpY true
	//   loop CX_812/816  yard (xbow side)  : TargetVar Home, SlotRadius 40, OrderCode -1, bMatchXbowTag true
	//   loop CX_844/848  yard (sword side) : TargetVar Home, SlotRadius 40, OrderCode -1, bMatchXbowTag true
	// OrderCode -1 = do not compare orders. bMatchXbowTag = only soldiers whose "Xbow" tag equals ours count.
	// bWriteTmpY: the gate-wall loop leaves Tmp.Y = "taken" flag of the LAST slot it looked at; kept 1:1.
	// Returns true if a slot was assigned.
	UFUNCTION(BlueprintCallable, Category = "Soldier|Brain")
	bool AssignFreeSlot(const TArray<FVector>& Slots, FName TargetVar, float SlotRadius, int32 OrderCode, bool bMatchXbowTag, bool bWriteTmpY);

	// ---- Prune NearZombies (11-06, inserted in front of the combat loop CX_145) ----
	// BPC_NearZombies rebuilds its NearZombies list every 0.2 s from a sphere overlap, so a zombie destroyed in between stays
	// in the list until the next refresh, and the loop's first read (Get Dead on the element) hits a pending-kill actor:
	// 761 "Blueprint Runtime Error" lines in one 11-06 play, each one a formatted log line on the game thread. This removes
	// the entries that are null, pending kill or being destroyed, in place, nothing else. The Blueprint ran those iterations
	// on garbage (every read returned zero), so skipping them is the only sane reading of the graph. Returns how many were
	// removed; 0 if the component or its array is missing (error logged once per class). cd.Soldier.PruneNearZombies 0 = off.
	UFUNCTION(BlueprintCallable, Category = "Soldier|Brain")
	int32 PruneNearZombies();

	UFUNCTION(BlueprintPure, Category = "Soldier|Brain")
	int32 GetOrderCode() const;

	UFUNCTION(BlueprintPure, Category = "Soldier|Brain")
	bool IsSoldierDead() const;

	// ---- Anti-air (11-06, wasp battle system; cd.Soldier.AntiAir 0 = off) ----
	// Crossbow soldiers (tag "Xbow") shoot wasps. The Blueprint combat loop only sees BP_Zombie (BPC_NearZombies filters by that class),
	// so this native layer runs beside it: when the soldier has no ground zombie nearby (or a wasp is diving at him), he picks the best
	// wasp in range with line of sight (UCDWaspDirector::FindAntiAirTarget), aims for SoldierAAAimTime (the wasp is told, so drones may
	// roll away), plays AM_Xbow_Aim, fires SFX_XbowFire + a BP_SoldierBolt (cosmetic, lifespan = distance / bolt speed, as the graph does),
	// and the shot is resolved when the bolt would arrive: hit chance from the wasp (size, evasion), damage SoldierAADamage. Numbers in UCDSettings.
	virtual void Tick(float DeltaSeconds) override;

	// Diagnostics: counts AND time. cd.Soldier.Report prints calls and average microseconds per call; the same scopes
	// appear in "stat CastleDefender" and Insights traces (STAT_CD_Soldier*).

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	void TickAntiAir(float DeltaSeconds);
	void FireAntiAir(class ARealmWaspBase* Wasp);
	// BPC_NearZombies.NearZombies length (0 when the component or array is missing).
	int32 GetNearZombieCount();
	float AACooldown = 0.f;
	float AAAimTimer = 0.f;
	float AAXbowRecheck = 0.f;
	bool bAAAiming = false;
	bool bIsXbow = false;
	TWeakObjectPtr<class ARealmWaspBase> AATarget;

	USceneComponent* GetSlotComponent(FName VarName) const;
	static USceneComponent* GetSlotComponentOf(const AActor* Actor, FName VarName);

	// Checks once per Blueprint class that Order / Goal / State exist, are scene-component object properties and are set
	// on this instance. Logs an Error naming the missing member. Result cached per class.
	bool ValidateBlueprintContract() const;
	int32 FindFreeSlot(const TArray<FVector>& Slots, FName TargetVar, float SlotRadius, int32 OrderCode, bool bMatchXbowTag, float ReservationSeconds, bool* bLastTaken, bool bMayReserve = true);
	bool bContractOK = false;
	TWeakObjectPtr<UActorComponent> NearZombiesComp;   // BPC_NearZombies, found once per soldier
};
