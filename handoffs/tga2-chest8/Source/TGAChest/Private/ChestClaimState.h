#pragma once
// Engine-independent transaction state used directly by the Unreal component.
// Restore once, before accepting interactions. Never reset on equip/overlap.
class FChestClaimState
{
public:
    bool Initialize(bool WasClaimed)
    {
        if (bInitialized) return false;
        bInitialized = true;
        bClaimed = WasClaimed;
        return true;
    }
    bool TryBegin()
    {
        if (!bInitialized || bClaimed || bPending) return false;
        bPending = true;
        return true;
    }
    bool Resolve(bool AwardSucceeded)
    {
        if (!bPending) return false;
        bPending = false;
        if (AwardSucceeded) bClaimed = true;
        return AwardSucceeded;
    }
    bool IsClaimed() const { return bClaimed; }
    bool IsInitialized() const { return bInitialized; }
    bool IsPending() const { return bPending; }
private:
    bool bInitialized = false;
    bool bClaimed = false;
    bool bPending = false;
};
