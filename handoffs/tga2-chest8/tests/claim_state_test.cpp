#include "../Source/TGAChest/Private/ChestClaimState.h"
#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (0)
int main()
{
    FChestClaimState fresh;
    CHECK(!fresh.TryBegin()); // save load must happen first
    CHECK(!fresh.Resolve(true)); // no fabricated completion
    CHECK(fresh.Initialize(false));
    CHECK(!fresh.Initialize(true)); // cannot change loaded state mid-session
    CHECK(!fresh.IsClaimed());
    CHECK(fresh.TryBegin());
    CHECK(!fresh.TryBegin()); // reentrant reward callback and repeated input
    CHECK(fresh.IsPending());
    CHECK(!fresh.Resolve(false)); // wallet rejection consumes no reward
    CHECK(!fresh.IsPending());
    CHECK(!fresh.IsClaimed());
    CHECK(fresh.TryBegin()); // failed award can retry
    CHECK(fresh.Resolve(true));
    CHECK(fresh.IsClaimed());
    CHECK(!fresh.Resolve(true)); // duplicate completion rejected
    CHECK(!fresh.Initialize(false)); // cannot reopen a claimed chest
    for (int i = 0; i < 10000; ++i) CHECK(!fresh.TryBegin());
    FChestClaimState restored;
    CHECK(restored.Initialize(true));
    CHECK(restored.IsClaimed());
    CHECK(!restored.TryBegin()); // loaded claimed chest never pays again
    FChestClaimState interrupted;
    CHECK(interrupted.Initialize(false));
    CHECK(interrupted.TryBegin());
    CHECK(!interrupted.Initialize(false)); // pending reward cannot be reset
    CHECK(interrupted.Resolve(true));
    FChestClaimState reloadAfterCommit;
    CHECK(reloadAfterCommit.Initialize(interrupted.IsClaimed()));
    CHECK(!reloadAfterCommit.TryBegin());
    return 0;
}
