// Start-of-game army formation (owner request 2026-11-05, screenshot with circles):
// on each side of the courtyard fountain, facing the main gate:
//   front: 1 commander;  then 1 row x 5 sword soldiers;  then 1 row x 5 crossbow soldiers;  back outer corner: 1 medic (24 total).
// Cheap while idle: each spawned soldier's actor tick (its Blueprint brain) is paused, only animation runs, so they stand in place.
// A soldier wakes (tick back on, normal behaviour) when a zombie is within cd.StartArmy.WakeRange (2500 cm) of him or the hero
// comes within 300 cm (to talk / give orders).
// Spawned once per play session, 0.5 s after BeginPlay, only in ThirdPersonMap. cvars: cd.StartArmy.Enable (1),
// cd.StartArmy.Spacing (160 cm), cd.StartArmy.SideOffset (750 cm from the fountain centre to each block centre).
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDStartArmy.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDStartArmySubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;

	// Spawns the formation now (also console: cd.StartArmy.Spawn). Returns how many actors were placed.
	int32 SpawnFormation();

private:
	void CheckWake();
	// rev 3 (review P2-2): one entry per formation slot; a slot is spawned once and only refilled if its spawn failed.
	struct FSlot { TSubclassOf<AActor> Class; float Ahead = 0.f; float Across = 0.f; TWeakObjectPtr<AActor> Spawned; bool bTried = false; };
	TArray<FSlot> Slots;
	int32 Attempts = 0;
	TArray<TWeakObjectPtr<AActor>> Idle;
	FTimerHandle WakeTimer;
	FTimerHandle Timer;
	bool bSpawned = false;
};
