// Horde (owner, 2026-11-05): 100 soldiers against 1000 zombies on the laptop.
// Only the zombies nearest the camera are real BP_Zombie actors (full animation, hit reactions, montage deaths). Everyone else is a
// lightweight agent in this subsystem: position, health, target and state in one array, drawn in bulk by instanced meshes whose
// crowd material plays baked animation on the GPU (UCDHordeAnimData). When an agent comes near the camera it is promoted to a real
// BP_Zombie (same HP / damage / type), and a real zombie that walks away is demoted back into an agent.
//   - pathing: one shared flow field toward the goal (default the gate the wave manager measures from), built from the nav mesh;
//   - combat: one batched pass on a spatial grid: agents bite soldiers, farmers and the hero (ApplyDamage, the same event the
//     Blueprints use), soldiers cut and shoot agents;
//   - deaths: a share of the dead melt into mush and leave a wet pool for a few seconds (agents and real zombies alike);
//     the others play a baked death, lie still, then sink and return their slot.
// Console: cd.Horde.Spawn <count> [radius], cd.Horde.Clear, cd.Horde.Report, cd.Horde.* variables.
// Cost with no agents: one character scan twice a second plus a Dead-flag read per live zombie per frame (for the real-zombie melt).
//
// Invariants
//   - Agent index == ISM instance index, forever. Instances are never removed (that would reorder them); a freed slot is hidden
//     (scale 0.001) and reused by the next spawn. Actors are held only as TWeakObjectPtr, so a destroyed zombie never dangles.
//   - cd.Horde.FullBudget is a strict cap on promoted agents: Promote never runs at NumPromoted >= budget. Demotion is what may be
//     delayed (a promoted zombie that is attacking, staggered, or visible within 1.25x range keeps its actor until it is free).
//     Real zombies spawned by the wave manager are not agents and do not count toward the budget.
//   - Promote spawns BP_Zombie the same way the wave manager does (plain SpawnActor, then ZType / Runner / MaxHP / AttackDamage /
//     XPValue / DamageTaken, then ResumeMove), so every Blueprint path sees exactly the order it already sees for wave zombies.
//     Its instance is hidden the same frame. Health moves between agent and actor through DamageTaken, never added twice.
//   - Kill happens once: it runs only when HP crosses 0, and agents with HP <= 0 or not Move/Attack are out of the combat grid,
//     so they are never hit, never bite and never promoted again. Promoted agents are not in the grid either: soldiers fight
//     their actors through the Blueprints only. A promoted zombie's death is the Blueprint's own (XP, montage, lifespan).
//   - Single-player: ApplyDamage and Event AnyDamage are authority-only, which is fine here (no replication).
//   - Flow field: sampling is time-sliced (800 nav queries per frame); the shortest-path solve (about 40,000 cells) runs once in
//     one frame when sampling ends. Measure it; slice it too if it shows as a hitch.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CDHordeSubsystem.generated.h"

class ACharacter;
class UCDHordeAnimData;
class UInstancedStaticMeshComponent;
class UDecalComponent;

UENUM()
enum class ECDHordeState : uint8
{
	Move,
	Attack,
	Dying,     // baked death clip, then lie, then sink
	Melting,   // shader melt, wet pool
	Promoted,  // a real BP_Zombie stands in for this agent
	Free       // slot unused
};

USTRUCT()
struct FCDHordeAgent
{
	GENERATED_BODY()

	FVector Pos = FVector::ZeroVector;     // capsule centre, like an actor location
	FVector2f Vel = FVector2f::ZeroVector;
	float Yaw = 0.f;
	float HP = 100.f;
	float MaxHP = 100.f;
	float AttackDamage = 12.f;
	float XPValue = 1.f;
	float Speed = 110.f;
	float Scale = 1.f;
	int32 ZType = 0;
	bool bRunner = false;

	ECDHordeState State = ECDHordeState::Free;
	float StateTime = 0.f;
	int32 Clip = INDEX_NONE;
	float NextAttack = 0.f;
	float NextThink = 0.f;
	float PromoteCooldown = 0.f;
	float CamDistSq = 0.f;

	TWeakObjectPtr<AActor> Target;
	TWeakObjectPtr<ACharacter> Actor;   // while Promoted
	TArray<TObjectPtr<UMaterialInterface>> ActorMaterials;   // the real zombie's own materials, kept for its next promotion
};

UCLASS()
class CASTLEDEFENDER_API UCDHordeSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	static UCDHordeSubsystem* Get(const UObject* WorldContext);

	// Adds Count agents on walkable ground within Radius of Center (Radius 0: a ring 70-120 m out from the goal). Returns how many were placed.
	UFUNCTION(BlueprintCallable, Category = "Horde")
	int32 SpawnAgents(int32 Count, FVector Center, float Radius = 1500.f, float MaxHP = 100.f, float AttackDamage = 12.f, float Speed = 110.f, bool bRunner = false, float Scale = 1.f, int32 ZType = 0);

	// Agents + their promoted actors that are still alive (for wave logic).
	UFUNCTION(BlueprintPure, Category = "Horde")
	int32 GetAliveCount() const;

	UFUNCTION(BlueprintPure, Category = "Horde")
	int32 GetPromotedCount() const { return NumPromoted; }

	// Damage every agent (not promoted actors) within Radius: cannon shots, burning oil. Returns the number of agents hit.
	UFUNCTION(BlueprintCallable, Category = "Horde")
	int32 ApplyRadialDamageToAgents(FVector Origin, float Radius, float Damage);

	UFUNCTION(BlueprintCallable, Category = "Horde")
	void SetGoal(FVector NewGoal);

	void ClearAll();
	void Report() const;

	// The wet pool + squash for a real zombie that just died (also used by the agents' melt).
	void SpawnMeltPool(const FVector& GroundLocation, float Radius, float Yaw);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickable() const override;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	bool EnsureAssets();
	bool EnsureRenderer();
	int32 AllocAgent();
	void SetClip(int32 Index, const TArray<int32>& Choices, bool bRandomPhase);
	void WriteCustomData(int32 Index, float MeltStart);

	// flow field
	void BuildFlowStep(int32 Budget);
	void SolveFlow();
	bool CellOf(const FVector& P, int32& OutX, int32& OutY) const;
	FVector2f FlowDir(const FVector& P, float& OutGroundZ, bool& bOutInField) const;
	// One rule for the solver, the direction pick and every movement step: both cells sampled walkable, height change <= MaxStepHeight,
	// and a diagonal step needs both side cells walkable (no corner cutting).
	bool CanStep(int32 FX, int32 FY, int32 TX, int32 TY) const;
	// The same rule for a move between two positions (true outside the field or before sampling finished).
	bool CanMove(const FVector& From, const FVector& To) const;
	static constexpr float MaxStepHeight = 90.f;

	// passes
	void RefreshDefenders();
	void ThinkAndMove(float Dt, float Now);
	void Combat(float Dt, float Now);
	void UpdatePromotion(float Now);
	void Promote(int32 Index);
	void Demote(int32 Index);
	void UpdateDeaths(float Dt, float Now);
	void CheckRealDeaths();
	void UpdateRealMelts(float Dt);
	void PushInstances();
	void Kill(int32 Index, float Now);

	UPROPERTY(Transient)
	TObjectPtr<UCDHordeAnimData> Data;

	UPROPERTY(Transient)
	TObjectPtr<AActor> RenderHost;

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> ISM;

	UPROPERTY(Transient)
	TObjectPtr<UClass> ZombieClass;

	TArray<FCDHordeAgent> Agents;   // index == ISM instance index
	TArray<int32> FreeSlots;
	TArray<FTransform> InstanceXf;
	TArray<float> CustomData;
	bool bCustomDirty = false;
	int32 NumAlive = 0;
	int32 NumPromoted = 0;

	TArray<int32> WalkClips, RunClips, AttackClips, DeathClips, IdleClips;
	FTransform MeshRelative = FTransform::Identity;   // the zombie class's mesh offset from its capsule centre
	float CapsuleHalfHeight = 90.f;
	bool bAssetsTried = false;

	// flow field (cells of CellSize cm, square of Dim x Dim around Goal)
	FVector Goal = FVector(-450.f, 1750.f, 40.f);
	FVector FieldOrigin = FVector::ZeroVector;
	float CellSize = 150.f;
	int32 Dim = 0;
	TArray<float> CellZ;       // ground height, NaN = not walkable
	TArray<float> CellCost;    // path length to goal
	TArray<FVector2f> CellDir;
	int32 BuildCursor = -1;    // -1 = not started, Dim*Dim = sampled
	bool bFlowReady = false;

	// defenders (soldiers, farmers, hero), refreshed twice a second
	struct FDefender { TWeakObjectPtr<AActor> Actor; FVector Pos; float Reach; float DPS; bool bRanged; };
	TArray<FDefender> Defenders;
	float NextDefenderRefresh = 0.f;

	// spatial grid of agent indices over the flow-field square (rebuilt each frame, linked lists; agents outside clamp to the border)
	void RebuildGrid();
	int32 GridIndex(const FVector& P) const;
	template <typename F> void ForEachNear(const FVector& P, float Radius, F&& Fn) const;
	TArray<int32> GridHead;
	TArray<int32> GridNext;
	int32 GDim = 0;
	float GridCell = 250.f;

	TSet<TWeakObjectPtr<ACharacter>> SeenDead;   // real zombies whose death was already handled (melt roll)

	float NextPromotion = 0.f;
	float CombatAccum = 0.f;
	TArray<TWeakObjectPtr<ACharacter>> LiveRealZombies;   // refreshed twice a second; their Dead flag is read every frame
	FVector CameraPos = FVector::ZeroVector;

	struct FPool { TWeakObjectPtr<UDecalComponent> Decal; float Age; float Radius; };
	TArray<FPool> Pools;

	struct FRealMelt { TWeakObjectPtr<ACharacter> Actor; float T; FVector BaseScale; bool bPool; };
	TArray<FRealMelt> RealMelts;
};
