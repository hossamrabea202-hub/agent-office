# Live integration boundary and continuation

## Required before existing graphs change

Request #160: fresh BP_Zombie Think/movement/combat exports; actual bell/cannon/crossbow/sword/fire success events; guard wake and minimap APIs; engine version. It is separate from siege request #124. Do not reuse old node IDs as live patch instructions.

Historical source only: `handoffs/exports/laptop2/gameplay/BP_Zombie.t3d`, blob `2c840de2ac45b7719d691793a78ce3e5f99382db`, 2026-10-28 manifest. It had `G_AtGate.false -> K2Node_CallFunction_ZB28` (SimpleMoveToActor), using GetOwner as the existing chase target, after an earlier close-range attack gate. The current graph may differ. Preserve Owner and every current combat/gate/special-movement path.

## Master-reviewed movement adapter

1. Assign the persistent manager to the listener on spawn; reset once after binding.
2. On normal-chase fallback, call Evaluate(true, GetActorLocation). If HasGoal=false, run the original chase behavior. Higher-priority state transitions call ResetInvestigation and take over movement.
3. If HasGoal=true, validate a navigation destination and **complete** path before consuming the fallback. Reject a projection too far from the emitted location or to an unintended storey. On failure call ResetInvestigation and execute the original chase; never treat an unreachable bell as successful investigation.
4. Use the game's existing movement ownership/arbitration if present. Otherwise add a single explicit hearing-owned state around the chosen AI movement task. Avoid issuing a MoveTo every Think: that can abort the current request. Reissue only for a newly accepted GoalId or a diagnosed failure, with a one-second retry limit. Ignore completion callbacks from an earlier hearing goal (compare the captured goal token).
5. A hearing arrival/failure/expiry releases only hearing-owned movement. Combat, climb, charge and scripted requests must never be stopped by a stale hearing completion. Do not translate the old C++ request-ID comparison into a guessed Blueprint pin: that native request token is not implemented here.
6. If the current project cannot expose a reliable ownership boundary, keep hearing in diagnostic mode and return the export. Do not wire an unconditional StopMovement or SimpleMoveToLocation into every Think.

The hearing core deliberately makes no movement call. Path projection, ownership and completion callbacks are the next source-dependent adapter deliverable. Offline hearing success is not navigation success.

## Emitters and presentation

- Emit once after an actual bell ring, successful cannon/crossbow shot, sword swing or timed fire crackle. Reload attempts/UI clicks/each sword-hit victim must not each emit another pulse.
- Call presentation only after `Source.Accepted=true`. The most recent slot is `(World.WriteIndex+31)%32`; snapshot its properties immediately, before any other source emits. For the later pooled indicator pass, keep at most eight active rings and reuse MIDs. No pool/UI graph is included in this core package.
- Guard wake should use the same range/weather score and existing sleep state. Do not create a parallel guard-sleep system.
- Ground and minimap rings from v1 need a Blueprint presentation bridge and a new realism review. They are not installed by this package. The full #48 acceptance requires them.
- All gameplay is standalone/server-side. Multiplayer cosmetic replication is not included.

## Bridge into #123 siege coordination

Use the listener's accepted sound location/id/expiry as an input to the future **Blueprint** siege coordinator. Keep a single hearing system; do not reintroduce the parked native plugin. Combat/role/objective policy should arbitrate whether to investigate, but must consume a sound once. Fresh wave/gate/climb contracts in #124 are still required before movement or spawning changes.

## Next author checklist

Read #48, #160, this README and any Master compiler results. Resolve paste/API issues first. Once fresh exports arrive, implement the adapter against those exact blobs, test emitters and navigation in Play with the Master, then add guard wake and readable indicators. Close #48 only after the complete feature passes recorded game tests. Do not mark the hearing-core package as full #48 completion.
