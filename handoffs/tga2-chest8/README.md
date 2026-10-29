# #8 Treasure chest gameplay component — TGA 2
Source milestone. No game assets changed. Unreal build/UHT/PIE are not yet verified.

## Delivered
A runtime plugin with an addable Blueprint-subclassable Actor Component.
It rejects repeated/reentrant interaction, awards through one explicit synchronous project hook, restores claimed state without awarding again, and exposes open/shine presentation events. No tick, input binding, world scan, asset dependency or fixed economy value.

The existing level designer retains chest placement and guard setup.

## Integration
1. In a C++-build-capable project, copy this folder to Plugins/TGAChest and rebuild with the project's actual Unreal version. This requires a native build; it is not a paste-only Blueprint package.
2. Create a Blueprint subclass of TGAChestComponent; override CommitGoldReward. Add that subclass as a component on the existing chest Actor.
3. Assign a unique stable ChestId to every placed chest; duplicated actors need different IDs. Configure GoldReward to the intended amount (default zero deliberately rejects payment).
4. Hook CommitGoldReward into the real player wallet/save ledger. For an unclaimed ID, add gold and record the claimed ID in the same transaction/save snapshot, then return true. For an already committed ID, return true without crediting again. On failure return false with no currency or claimed-state change. Check integer overflow in the wallet.
   The plugin deliberately does not invent the game's currency or save fields. Without this override it refuses to open.
5. Bind OnPresentationChanged before calling InitializeFromSave(savedLedgerContainsChestId), once after save loading completes. Closed: lid closed, shine/prompt visible. Opened: lid open, shine/prompt hidden. Initialization does not broadcast OnOpened.
6. Use OnOpened for the new-opening animation/sound/toast. If OnPresentationChanged snaps the lid open, put animation logic in your presentation handler (distinguish initial restore from interaction) rather than fighting a second lid setter.
7. Route the existing hero interaction trace's E Started to TryOpen(playerPawn) on the selected chest. Require line of sight, living-player state, and the game's interaction restrictions in that caller. The component additionally validates authority, player-controlled pawn, configuration and distance from actor origin. Place the actor pivot appropriately or adapt distance to the interaction point.
8. Do not bind E independently on every chest; that would open every nearby chest on one press.
9. Save wallet + claimed IDs together. No exactly-once crash recovery is promised without an atomic/idempotent project ledger. Never overwrite the user's existing save as part of setup.

## Boundaries
Single-player/server-authoritative logic. No RPC or replicated presentation is supplied. Multiplayer needs an owned-player server interaction RPC with target validation and replicated claimed-state presentation; do not call directly from a client and expect it to work.
No chest mesh, lid rig, shine material, enemies or tunnel placement is authored here.
Do not allow latent work in CommitGoldReward. The callback must not destroy/recreate the component and then report failure after crediting the wallet.
Native component cannot by itself confirm that the shipped game has the correct E route or wallet/save hookup.

## Verification
tests/claim_state_test.cpp exercises the exact engine-independent state class used by the component: uninitialized rejection, one-time initialization, reentry/repeated presses, failed-award retry, duplicate completion, restoration and 10,000 attempts after claim.
Run it with a C++ compiler; zero exit code means pass. This verifies transaction state only, not Unreal reflection or wallet integration.

Engine acceptance:
- Closed chest within range, press E: one reward, lid opens, shine disappears.
- Spam E and reenter TryOpen from wallet callback: only one credit.
- Wallet failure: no opening/reward; successful retry works.
- Reload saved game: chest stays open and awards nothing.
- Two different chest IDs each pay once; duplicate-ID configuration is detected by the integrator.
- Outside range, through a wall, dead player, non-player pawn and uninitialized save: no reward.
- Compile/reopen and confirm no errors. Verify existing interactions still work.
Keep #8 open until integrated and verified.

Reference: https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UActorComponent
