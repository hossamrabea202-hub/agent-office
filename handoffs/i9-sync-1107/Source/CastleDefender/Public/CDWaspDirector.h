// CDWaspDirector (2026-11-06): the swarm's brain above the wasps. One per world.
//   - Wave hook: reads BP_ZombieWaveManager.Wave by reflection every 0.5 s (like BP_BattleDirector polls it). On a new wave it
//     spawns a flight by the rules in UCDSettings (first wave, drones per wave, a Matriarch every Nth wave), one wasp every
//     WaspSpawnInterval seconds from a point far out and high up, so the flight is seen coming in over the field.
//   - Turns the Blueprint's own swarm spawn off (SwarmEveryNthWave -> huge) unless bWaspReplacesBlueprintSwarm is false, so wasps
//     come from one place. SwarmUnlocked is NOT touched (it also gates the half-horse spawns).
//   - Swarm coordination: dive tokens (at most WaspMaxDiversPerTarget on one target; a Matriarch counts double), a cap on wasps
//     hunting the hero, target claims for the score, and "who is aiming at whom" for the soldiers.
//   - Anti-air queries for ASoldierBase: the best wasp to shoot from a point, and whether a wasp threatens a defender.
// Console: cd.Wasp.Enable (1), cd.Wasp.Debug (draw state over each wasp), cd.Wasp.Spawn <drones> [matriarchs] (owner's test),
//          cd.Wasp.Kill (kill every wasp), cd.Wasp.Report.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDWaspDirector.generated.h"

class ARealmWaspBase;
enum class EWaspCaste : uint8;

UCLASS()
class CASTLEDEFENDER_API UCDWaspDirector : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	static UCDWaspDirector* Get(const UObject* WorldContext);

	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UCDWaspDirector, STATGROUP_Tickables); }

	// ---- spawning ----
	// Queue a flight: Drones + Matriarchs, streamed in from the spawn point. Wave only labels the wasps (HP scaling).
	UFUNCTION(BlueprintCallable, Category = "Wasp")
	void SpawnFlight(int32 Drones, int32 Matriarchs, int32 ForWave);
	// Spawn one wasp now at Location (deferred spawn + Init + FinishSpawning). Returns null if spawning failed.
	ARealmWaspBase* SpawnWasp(EWaspCaste Caste, const FVector& Location, int32 ForWave);

	// ---- registry ----
	void Register(ARealmWaspBase* Wasp);
	void Unregister(ARealmWaspBase* Wasp);
	UFUNCTION(BlueprintPure, Category = "Wasp") int32 GetAliveWaspCount() const;
	UFUNCTION(BlueprintCallable, Category = "Wasp") TArray<ARealmWaspBase*> GetWasps() const;
	template <typename F> void ForEachWasp(F&& Fn) const { for (const TWeakObjectPtr<ARealmWaspBase>& W : Wasps) { if (ARealmWaspBase* A = W.Get()) { Fn(A); } } }

	// ---- swarm coordination (wasps call these) ----
	int32 ClaimsOn(const AActor* Target) const;          // wasps with this target
	int32 HeroHunters() const;                           // wasps whose target is the player
	bool RequestDiveToken(ARealmWaspBase* Wasp, AActor* Target);
	void ReleaseDiveToken(ARealmWaspBase* Wasp);
	int32 DiversOn(const AActor* Target) const;
	// Where the battlefield is: the castle gate control if there is one, else the first wave manager, else origin.
	FVector GetAnchor() const { return Anchor; }
	// The zombie spawn side: direction from the anchor toward the wave manager (unit XY), so the flight comes from the enemy side.
	FVector GetEnemyDirection() const { return EnemyDir; }
	// #169 stage 3: the mountain crack (Realm_MountainCrack, SM_RealmCrack) and the Realm_SwarmSpawn TargetPoint, when the level has them.
	bool HasCrack() const { return bCrackFound; }
	FVector GetCrackMouth() const { return CrackMouth; }
	FVector GetCrackOrbitPoint() const { return CrackOrbit; }
	// A flight is coming out: flare the crack light and the glow for a moment.
	void PulseCrack(float Strength);

	// ---- for the soldiers' anti-air layer ----
	// Best wasp to shoot: alive, within Range of From, line of sight if bNeedLOS (Visibility trace from From). Diving wasps and
	// low-HP wasps are preferred, farther ones less. Null if none.
	ARealmWaspBase* FindAntiAirTarget(const AActor* Shooter, const FVector& From, float Range, bool bNeedLOS) const;
	// A wasp is diving at Defender, or any wasp is within Radius of it.
	bool IsWaspThreatening(const AActor* Defender, float Radius) const;

	// ---- stats for cd.Wasp.Report ----
	int32 TotalSpawned = 0, TotalKilled = 0, TotalStings = 0, TotalRetreats = 0, TotalDodges = 0, SoldierShots = 0, SoldierHits = 0;

private:
	void PollWaves();
	void RefreshWaveManagers();
	void RefreshAnchor();
	int32 ReadWave() const;
	void DisableBlueprintSwarm();
	FVector FlightSpawnPoint(int32 Index) const;

	struct FPendingSpawn { EWaspCaste Caste; int32 Wave; };
	TArray<FPendingSpawn> Queue;
	float SpawnTimer = 0.f;
	int32 FlightIndex = 0;

	TArray<TWeakObjectPtr<ARealmWaspBase>> Wasps;
	TMap<TWeakObjectPtr<ARealmWaspBase>, TWeakObjectPtr<AActor>> DiveTokens;

	TArray<TWeakObjectPtr<AActor>> WaveManagers;
	TWeakObjectPtr<UClass> WaveManagerClass;
	bool bWaveClassLookedUp = false;
	float WavePollTimer = 0.f;
	float ManagerRefreshTimer = 0.f;
	int32 LastWave = -1;
	bool bSwarmDisabled = false;
	FVector Anchor = FVector::ZeroVector;
	FVector EnemyDir = FVector(1, 0, 0);
	bool bAnchorFound = false;
	void RefreshCrack();
	bool bCrackFound = false;
	FVector CrackMouth = FVector::ZeroVector;    // inside the fissure: where a wasp appears
	FVector CrackOrbit = FVector::ZeroVector;    // the TargetPoint (6 m out, 5 m up): where it circles once
	TWeakObjectPtr<AActor> CrackActor;
	TWeakObjectPtr<class UPointLightComponent> CrackLight;
	TWeakObjectPtr<class UMaterialInstanceDynamic> CrackMat;
	float CrackLightBase = -1.f, CrackGlowBase = -1.f, CrackPulse = 0.f;
	bool bSwarmUnlockedSeen = false;
};
