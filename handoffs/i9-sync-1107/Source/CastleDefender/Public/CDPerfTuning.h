// Runtime performance tuning for crowds, applied in C++ to live actors, so no Blueprint asset has to change.
// Master switch cd.Perf.Enable (default 0 = everything exactly as authored). With it on, each rule below is applied and reverted live 4x per second,
// so it can be A/B tested inside one run: cd.Perf.ABPeriod 5 flips it every 5 s (CSV stat CastleDefender/PerfEnable). All are console variables, settable in DefaultEngine.ini [SystemSettings].
//   cd.Perf.SoldierDriverMeshNoCollision 1   soldiers' CharacterMesh0 (hidden animation driver, weapons attach to it) gets NoCollision while
//                                            alive: no physics bodies to move every frame. Their death ragdoll sets the Ragdoll profile itself.
//   cd.Perf.SoldierURO 1                     update-rate optimisation on soldiers' skeletal meshes (keeps ticking: the driver mesh is never "rendered")
//   cd.Perf.ZombieSkipFloorChecks 1          zombies' CharacterMovement: bAlwaysCheckFloor off (floor is found only when the move needs it)
//   cd.Perf.ZombieBodyLODDistance 3500       zombies farther than this from the player (cm) have mesh collision off (0 = rule off).
//                                            Never touches a simulating / Ragdoll / dying body; restores only what it switched off itself.
//   cd.Perf.ZombieMoveTickLODDistance 4000   zombies farther than this that were not rendered recently tick movement at 10 Hz (0 = off)
// Classes are matched by name prefix (BP_SoldierSword*, BP_Zombie* and their children). `cd.Perf.Report` prints counts.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDPerfTuning.generated.h"

class ACharacter;
class USkeletalMeshComponent;

UCLASS()
class CASTLEDEFENDER_API UCDPerfTuning : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	void Report() const;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	void OnActorSpawned(AActor* Actor);
	void Consider(AActor* Actor);
	void UpdateSoldiers();
	void UpdateZombies();
	void SetBodyOff(ACharacter* Character, bool bOff);

	FDelegateHandle SpawnHandle;
	TArray<TWeakObjectPtr<ACharacter>> Soldiers;
	TArray<TWeakObjectPtr<ACharacter>> Zombies;
	TSet<TWeakObjectPtr<ACharacter>> BodiesOff;                       // meshes this subsystem switched to NoCollision
	TSet<TWeakObjectPtr<ACharacter>> SlowMovers;                      // movement tick slowed by this subsystem
	TMap<TWeakObjectPtr<USkeletalMeshComponent>, bool> OriginalURO;   // URO values this subsystem changed
	float Accum = 0.f;
	float ABAccum = 0.f;
};
