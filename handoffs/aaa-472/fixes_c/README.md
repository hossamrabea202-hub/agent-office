# #472 fix C: zombie significance + hit-stop + brute flinch (i5 for i9). Paste AFTER fix A and fix B

**Pre-checked:** merge Validation OK on fix B's output; `fix_impure`; `check` OK; `setup_472c_ue.py` ran on i5 in a temp folder (additive type and base pose set, 2 montages in DefaultSlot) and `--revert` deleted them.
**NOT checked:** never pasted, compiled or played. If fix A or B failed to compile, stop and send i5 the error: this one builds on them.

## What changes
| Part | Rule | Why |
|---|---|---|
| Think rate | under 30 m from the player every Think; 30-60 m every 2nd; beyond 60 m every 4th | far zombies retarget and path less often |
| Tick rate | beyond 30 m AND not rendered: CharacterMovement 10 Hz, actor 4 Hz | off-screen movement can be coarse; a rendered zombie always keeps full rate |
| Hit-stop | a blow of at least 25 % of MaxHP pauses the victim's animation for 60 ms (`bPauseAnims`) | makes heavy blows land; small hits don't stutter. Not CustomTimeDilation: BP_SoldierSword uses that as a state flag on zombies |
| Brute flinch | additive jolt, front or back by hit side, at most 1 a second, play rate 3 (brutes run at anim rate 0.2-0.5) | brutes had no reaction at all |

Far zombies now react more slowly to targets: up to 1 s instead of 0.25 s beyond 60 m. They still walk their current path meanwhile.

**Decision:** a far zombie attacking a soldier out of sight may start its attack up to 1 s late. That's acceptable off-screen; if a fight 60 m away looks late, raise the 6000 in `zc472Less...`.
**Decision:** the flinch uses Montage_Play with bStopAllMontages = false in DefaultSlot, not a new slot. A second slot name can't be put in its own group from a script, and a brute's crawl is itself a looping slot montage that must not stop. The engine layers additive montages over the slot pose (from memory of the source; to confirm in Play).

## Steps (Master, not in Play, after fix B is saved)
1. `py handoffs/aaa-472/fixes_c/setup_472c_ue.py --dry-run`, then `--apply`. Adds ThinkTick and LastFlinchAt; makes 2 additive clips + 2 montages in `Zombie/Anim/Hit`.
2. Export fresh BP_Zombie, then `python handoffs/aaa-472/fixes_c/build_472c.py <export>`. It must end `OK: paste ...`.
3. BP_Zombie > EventGraph: Ctrl+A, Delete, paste `zombie_c_merged.txt`. Compile, save. Check the 4 child classes compile.

## Test list (Play)
- [ ] Zombies near the player behave as before. Walk 60 m+ away and look back: they keep moving smoothly when rendered, no slideshow.
- [ ] Far zombies still reach and attack soldiers, farmers and the gate.
- [ ] Heavy hit: a short freeze on that zombie only, then it continues (never stays frozen). Kill during the freeze: the death still plays.
- [ ] Hit a crawling brute from the front and from behind: an upper-body jolt on top of the crawl; **the crawl keeps going**. Hit it during its slam: the slam continues.
- [ ] Hit-stop or flinch too strong / too weak? Values: 0.25 and 0.06 in `zc472`; flinch rate 3.
- [ ] `stat game` / `stat anim` at the busiest wave against the earlier run.

## Revert
Paste the step 2 export back, compile, save. Then `setup_472c_ue.py --revert`.

Rules applied (INDUSTRY_SECRETS): "zombie motion variation": the flinch layers on the existing motion and does not replace it.
