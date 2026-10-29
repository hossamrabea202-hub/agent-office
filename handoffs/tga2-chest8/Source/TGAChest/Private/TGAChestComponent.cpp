#include "TGAChestComponent.h"
#include "ChestClaimState.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"

struct UTGAChestComponent::FState { FChestClaimState Claim; };
UTGAChestComponent::UTGAChestComponent() : State(MakeUnique<FState>())
{
    PrimaryComponentTick.bCanEverTick = false;
}
UTGAChestComponent::~UTGAChestComponent() = default;

bool UTGAChestComponent::InitializeFromSave(bool bWasClaimed)
{
    if (!IsInGameThread() || !State->Claim.Initialize(bWasClaimed)) return false;
    OnPresentationChanged.Broadcast(bWasClaimed);
    return true;
}
bool UTGAChestComponent::IsOpened() const { return State->Claim.IsClaimed(); }
bool UTGAChestComponent::IsInitialized() const { return State->Claim.IsInitialized(); }
bool UTGAChestComponent::CommitGoldReward_Implementation(APawn*, FName, int32)
{
    return false; // No assumed wallet or save API.
}
bool UTGAChestComponent::TryOpen(APawn* Interactor)
{
    AActor* Chest = GetOwner();
    if (!IsInGameThread() || !IsValid(Chest) || !Chest->HasAuthority()
        || !IsValid(Interactor) || !Interactor->IsPlayerControlled()
        || ChestId.IsNone() || GoldReward <= 0
        || !FMath::IsFinite(InteractionDistance) || InteractionDistance <= 0.0f)
        return false;
    const double DistanceSquared = FVector::DistSquared(Chest->GetActorLocation(), Interactor->GetActorLocation());
    if (!FMath::IsFinite(DistanceSquared)
        || DistanceSquared > FMath::Square(static_cast<double>(InteractionDistance)))
        return false;
    if (!State->Claim.TryBegin()) return false;

    // Acquire before calling project code: a reentrant interaction cannot pay twice.
    const bool bCommitted = CommitGoldReward(Interactor, ChestId, GoldReward);
    const bool bOpened = State->Claim.Resolve(bCommitted);
    if (bOpened && IsValid(this) && IsValid(GetOwner()))
    {
        OnPresentationChanged.Broadcast(true);
        if (IsValid(this) && IsValid(GetOwner())) OnOpened.Broadcast();
    }
    return bOpened;
}
