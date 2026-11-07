// #506 (owner, wave 15): "a lot of crowd of zombies at the gate with broken door got stuck together and can't get in the castle".
// Gate jam breaker. Once a second, for every BP_CastleGateControl, while the wave manager says GateBroken:
//   - counts zombies within cd.GateJam.Radius of the gate that are alive, not fighting and standing still;
//   - when at least cd.GateJam.MinCount of them have been still for cd.GateJam.Seconds in a row, the gateway is jammed:
//       1. any component of the gate control that still blocks pawns (the ZombieStop box or a door leaf that kept its collision) is
//          switched to no collision and logged by name (the thing the owner's zombies were pressing against);
//       2. every jammed zombie gets its own goal through the gateway: a point spread across the gateway width, 3-9 m inside the
//          castle, instead of all of them aiming at the same gate point and wedging each other. 4 s cool-down per zombie, then
//          the zombie's own brain takes over again (its Think picks soldiers / farmers / hero as before).
// Does nothing while the gate stands. Log lines "[CD] gatejam:". cd.GateJam 0 = off, cd.GateJam.Report = state now.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDGateJamSubsystem.generated.h"

class AZombieBase;

UCLASS()
class CASTLEDEFENDER_API UCDGateJamSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override;
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UCDGateJamSubsystem, STATGROUP_Tickables); }

	// Console / Blueprint: one line per gate with the current counts.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Gate")
	FString Report();

	// Console / Blueprint: break the jam at every broken gate now, whatever the counters say.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Gate")
	int32 BreakJamNow();

private:
	struct FGate
	{
		TWeakObjectPtr<AActor> Control;
		int32 StillChecks = 0;      // consecutive 1 s checks with a jam-sized still crowd
		int32 LastStill = 0, LastNear = 0;
		double LastBreak = -100.0;
	};
	TArray<FGate> Gates;
	TArray<TWeakObjectPtr<AActor>> WaveManagers;
	TMap<TWeakObjectPtr<AZombieBase>, double> Rerouted;   // zombie -> time of its last re-route
	double LastScan = -100.0, LastCheck = -100.0;

	void Refresh();
	bool IsGateBroken() const;
	FVector Inward(const FVector& GateLoc) const;
	int32 Break(FGate& G, bool bForce);
	int32 FreeBlockers(AActor* Control) const;
	void Check(FGate& G);
};
