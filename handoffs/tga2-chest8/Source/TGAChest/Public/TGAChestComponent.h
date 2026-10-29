#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TGAChestComponent.generated.h"

class APawn;
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FChestOpened);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FChestPresentation, bool, bOpened);

UCLASS(BlueprintType, Blueprintable, ClassGroup=(Gameplay), meta=(BlueprintSpawnableComponent))
class TGACHEST_API UTGAChestComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UTGAChestComponent();
    virtual ~UTGAChestComponent();

    // Stable unique ID per placed chest, shared with the authoritative save ledger.
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Chest")
    FName ChestId;
    // Zero deliberately means unconfigured; choose the game's intended economy value.
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Chest", meta=(ClampMin="0"))
    int32 GoldReward = 0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Chest", meta=(ClampMin="1"))
    float InteractionDistance = 200.0f;

    // Bind presentation delegates BEFORE calling this once after the save ledger loads.
    UFUNCTION(BlueprintCallable, Category="Chest")
    bool InitializeFromSave(bool bWasClaimed);
    UFUNCTION(BlueprintCallable, Category="Chest")
    bool TryOpen(APawn* Interactor);
    UFUNCTION(BlueprintPure, Category="Chest")
    bool IsOpened() const;
    UFUNCTION(BlueprintPure, Category="Chest")
    bool IsInitialized() const;

    // Called only after a new, successful reward transaction.
    UPROPERTY(BlueprintAssignable, Category="Chest")
    FChestOpened OnOpened;
    // Restore/open: set lid, shine and prompt. Restore never awards money.
    UPROPERTY(BlueprintAssignable, Category="Chest")
    FChestPresentation OnPresentationChanged;

    // Override in a Blueprint subclass or C++. Default implementation refuses.
    // Synchronous, non-latent and idempotent by StableChestId:
    // atomically add gold AND persist claimed ID; return true for already committed ID.
    // false must mean no currency/ledger mutation occurred.
    UFUNCTION(BlueprintNativeEvent, Category="Chest")
    bool CommitGoldReward(APawn* Interactor, FName StableChestId, int32 Amount);
protected:
    virtual bool CommitGoldReward_Implementation(APawn* Interactor, FName StableChestId, int32 Amount);
private:
    struct FState;
    TUniquePtr<FState> State;
};
