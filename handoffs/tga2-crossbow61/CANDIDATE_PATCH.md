# Crossbow #61 — candidate Blueprint cadence patch
Author: TGA 2
Status: prepared from exported source; NOT applied, compiled or play-tested.

## Source and scope
BP_Crossbow: handoffs/exports/codex/weapon95/BP_Crossbow.t3d
Git blob: 6093ef485b3b5ecae83cd22f696f1b9f0338fa25.
Asset: /Game/CastleDefender/Gameplay/Crossbow/BP_Crossbow.
This is a manual node-edit patch, not an importable whole-Blueprint replacement.
Match the listed nodes and connections in the live graph before editing. Save a Blueprint backup first.

The export demonstrates an early-reload bypass: a rejected shot follows CX_114.false -> CX_157 -> CX_80 and can start reloading during the 0.35-second recovery. This patch closes that bypass and makes recovery/reload exclusion explicit. It does not establish that this is the only cause of the reported rapid fire.

## Variables
Add two Boolean instance variables, default false, not instance editable:
- TGA61_Recovering
- TGA61_Reloading

Do not use LoadedBolt visibility or montage playback as the sole lock. Keep their existing checks as additional conditions.

## Exact graph edits
1. Keep CX_104 IA_XbowFire wired from Started. Its Triggered pin is already disconnected; leave it disconnected.
2. Disconnect CX_157.then from CX_80.execute. Preserve CX_114.false -> CX_157 for existing dry-fire feedback. Rejected clicks must not start reload.
3. Insert a Branch between CX_106.then and CX_114.execute:
   condition = NOT(TGA61_Recovering OR TGA61_Reloading).
   True -> CX_114.execute. False -> nothing.
   This prevents repeated clicks from producing repeated dry-fire feedback while busy.
4. Insert Set TGA61_Recovering=true between CX_114.true and CX_123.execute. Acquire this lock BEFORE trace/spawn/effects.
5. Preserve CX_123 -> CX_138 -> CX_146 -> CX_147 and the subsequent sound/recoil chain unchanged. The lock covers the full shot path.
6. Between CX_156.then and CX_80.execute insert Set TGA61_Recovering=false.
   Preserve CX_156.Duration=0.35. Do not clear the lock from button release, aim changes or another click.
7. Insert a Branch between CX_80.then and CX_89.execute:
   condition = NOT(TGA61_Recovering OR TGA61_Reloading).
   True -> CX_89.execute. False -> nothing.
   All existing reload callers converge here, including explicit reload CX_103 and delayed auto-reload CX_156.
8. Insert Set TGA61_Reloading=true between CX_89.true and CX_607.execute.
9. After CX_101.then add Set TGA61_Reloading=false.
   Keep CX_100 -> CX_101 (restore LoadedBolt visibility) in that order; release the lock only after visibility is restored.
10. Compile and inspect every edited connection. There must be only one call into the shot spawn chain and no new connection that replays rejected input.

## Reload timing stays unchanged
Leave CX_607 through CX_613 and their inputs unchanged:
- CX_99 selects 1.05 seconds for Sovereign, 0.73 for Noble.
- CX_611 computes 1 + 0.15 * selected XbowUp channel.
- CX_613 divides the base delay by this multiplier.
- CX_612 adjusts montage speed with the same upgrade multiplier.
Earliest successful shots on this path are separated by at least:
  0.35 + baseReload / (1 + 0.15 * selectedLevel)
subject to any longer existing montage gate and frame scheduling.
Use the actual channel value; do not assume whether level numbering starts at 0 or 1.
Do not replace this with a flat one-second cooldown.

## Lifecycle assumptions and boundaries
These edits retain the original latent Delay lifetime. Do not add equip-time resets to the two locks while an old delay can still complete. The existing path finishes recovery/reload even if input is temporarily removed. Test holster/re-equip and cannon transitions during both delays. If current code cancels latent actions, destroys/replaces the actor, or resets bolt state on equip, reconcile that lifecycle before applying this patch.
A failed projectile spawn must not produce Accessed None or permanently hold a lock. If the live graph can fail the spawn, add an IsValid branch after CX_138 and route failure to a controlled recovery completion with no success effects/ammo debit. Verify the existing failure behavior rather than assuming AlwaysSpawn is a guarantee.

This is a per-instance patch. Two enabled BP_Crossbow instances could each fire once. CX_2 enables input at BeginPlay; the snapshot's shot predicate lacks an explicit equipped-instance check. Do not claim this patch solves duplicate input ownership.
If traces show multiple responding actors, identify the authoritative currently equipped crossbow reference, then gate fire/reload on Self == that reference. Inactive instances must not consume fire input. Do not blindly disable the entire actor's input: its equip controls may use the same input component. Do not invent a new owner reference without checking the existing equip system.

## Application and regression checks
Only the authorized editor driver applies changes under the office's current editor rule. Source preparation does not require that driver to be online.

Record game time, crossbow instance name, equipped weapon, upgrade channel, reload start/end and actual projectile spawn for each accepted shot. Count real hero bolts, not audio events.
- For Noble and Sovereign, test the available base and upgraded levels: hold RMB and click LMB rapidly for 10 seconds. Every interval must meet the formula above.
- Repeat without aiming.
- Hold LMB through several reload durations: only one shot for that press.
- Press repeatedly during recovery/reload, then stop. No shot should occur at completion without a new press.
- Press reload immediately after firing and spam it: recovery cannot be skipped, one reload starts, and no duplicate completion re-arms a second shot.
- Fire normally after reload; one projectile, one ammo debit if present, one firing effect sequence.
- Holster/re-equip and enter/leave a cannon during recovery and reload: no stuck lock, stale completion, or extra shot.
- Confirm visible bolt behavior (#60), aiming, recoil and upgrade reload differences remain intact.
- If more than one actor logs a spawn for a press, resolve active-instance ownership before closing #61.
- Save, reopen, compile and repeat the aimed rapid-click case.

## Rollback
Restore the backed-up Blueprint, or remove the inserted lock nodes/variables and reconnect the recorded original edges. Do not overwrite the player's save.
#61 remains open until the actual reported burst is reproduced before the change and absent after it in Unreal.
