# #80 Hero attacks a tentacle: half the followers join, half guard

Seat: `hossam gmail laptop2 (Claude)` (owner reassigned from adjustedfilm, 2026-10-28).

## Behaviour

1. **Trigger:** a hero sword hit lands on a tentacle (`BP_TentacleVitals` takes damage with the hero as instigator)
   and no split is active. The split is per tentacle: hitting a second tentacle moves the strike team there.
2. **Pick the teams** from the hero's followers in order 1 (follow) / 2 (guard), plus later each commander's squad
   when the hero leads it:
   - Sort by role, then distance to the tentacle. Alternate the assignment per role (sword 1 -> strike, sword 2 ->
     guard, ...) so both teams keep swords and crossbows. **Odd counts: the extra one guards.**
   - Fewer than 2 followers: no split (they keep their order).
3. **Strike team:**
   - Swords: move to a ring of radius 2.5 m around the tentacle base (evenly spaced slots, so they don't stack),
     attack the tentacle/shell with the normal melee.
   - Crossbows: stand off at 12-15 m with a line of sight and shoot the tentacle / its jelly shell.
   - **Revenge strike** (`BPC_TentacleStrike`, slam at HP <= 10 % / shield 0): when the strike's wind-up starts, the
     swords step back to 5 m for its duration, then close in again.
4. **Guard team:** saves the hero's position at the split (`HoldPoint`) and holds a ring of radius 4 m around it.
   They engage zombies within 10 m of HoldPoint and return to their slot. They never target the tentacle.
5. **End** (any of these): the tentacle dies, the hero lands no hit on it for 6 s, or the hero is > 25 m from it.
   Everyone returns to the order they had before (saved per soldier as `PrevOrder`).
6. **Shouts** (notice, #68 look, 1.5 s): `"With me!"` at the split, `"Hold the line!"` under it in smaller text, and
   `"Fall back!"` at the end.

## Implementation (soldier side does the work; the hero only announces)

- **Hero** (`BP_ThirdPersonCharacter`, sword hit handler): on a hit whose victim is a tentacle, call
  `TentacleEngaged(Tentacle)` on a small manager (`BP_ArmySplit`, one per level, spawned on BeginPlay or placed in
  the map). It also stores `LastTentacleHitAt = Now`.
- **BP_ArmySplit:** holds `Tentacle`, `HoldPoint`, `Strike[]`, `Guard[]`. On engage: build the teams (rule 2), set
  each soldier's new order 7 = strike (target Tentacle) or 8 = hold (target HoldPoint), and save `PrevOrder`. A 0.5 s
  timer checks the end conditions and restores the orders.
- **Soldiers** (`BP_SoldierSword` / `BP_SoldierXbow`): two new orders in the existing order switch:
  - **7 Strike:** move to the given slot (sword) or the stand-off point (crossbow); attack the target; read the
    tentacle's strike wind-up flag to step back.
  - **8 Hold:** move to the slot on the ring around HoldPoint; the existing zombie engage logic with a 10 m leash
    from HoldPoint.
- Orders 7/8 don't appear on the order wheel; only `BP_ArmySplit` sets them.

## Checks (Play)

1. 6+ followers on follow: hit a tentacle. About half (both types) go to it, half form a ring at that spot. Shouts show.
2. Zombies coming in: the guard ring kills them and doesn't drift to the tentacle.
3. Tentacle slam: the swords back off and return.
4. Tentacle dies / walk 25 m away / stop hitting for 6 s: everyone back to follow.
5. 1 follower: no split. 7 followers: 3 strike, 4 guard.

## Exports needed (fresh)

`BP_SoldierSword`, `BP_SoldierXbow` (order switch + targeting), `BP_ThirdPersonCharacter` (sword hit handler),
`BP_TentacleVitals`, `BPC_TentacleStrike` (wind-up flag), `BP_ArmyHUD` (how orders are stored).

## v1 implementation (laptop2, 2026-10-29, from the 10-28 exports in handoffs/exports/laptop2/gameplay)

Findings that make this small: **no hero edit and no soldier-graph edit are needed.**
- Soldiers take orders through two components: `Order` (RelativeLocation.X = order number) and `Goal`
  (RelativeLocation = world point). The Commander HUD writes them exactly like that (commander-kit v2).
  Orders: 0 post, 1 follow, 3 crew cannon, **5 hold at Goal**, 6 attack zombies, 7 defend gate.
  `BP_SoldierXbow` is a child of `BP_SoldierSword` (one cast, tag `Xbow` tells them apart). `Dead` is a bool on them.
- The hero's sword does `ApplyDamage(OtherActor, 35, DamageCauser = hero)`. Tentacles take damage through the actor's
  `OnTakeAnyDamage` (BP_TentacleVitals binds it on its attach parent). So the manager binds `OnTakeAnyDamage` on
  every tentacle (Get All Actors Of Class BP_TentacleVitals → Get Attach Parent Actor) and engages when
  DamageCauser == Get Player Character(0).
- Soldiers only ever target BP_Zombie, so the strike team's attacks are done by the manager: sword = face the
  tentacle, `AM_Slash1`/`AM_Slash2` montage, `SC_SwordHit` sound, `ApplyDamage(tentacle, 20, causer = soldier)`;
  crossbow = `AM_Xbow_Aim`, `SFX_XbowFire`, spawn `BP_SoldierBolt` aimed at the tentacle (life span = distance /
  5000), `ApplyDamage(15)`. Paths: /Game/CastleDefender/Gameplay/Castle/Combat/AM_Slash1|2,
  /Game/CastleDefender/Gameplay/Crossbow/Anims/AM_Xbow_Aim, /Game/Audio/Kenney/SC_SwordHit,
  /Game/CastleDefender/Gameplay/Crossbow/Audio/SFX_XbowFire, /Game/CastleDefender/Characters/Knight/BP_SoldierBolt.
- Both teams use **order 5 (hold at Goal)**, so no new orders 7/8 are needed in the soldier graph:
  strike swords Goal = ring slot r 250 cm around the tentacle (500 cm while the tentacle's `BPC_TentacleStrike.State`
  != 0 = slam wind-up/strike), strike crossbows Goal = 1300 cm from the tentacle toward the hero, spread 150 cm
  sideways; guard Goal = ring slot r 400 cm around HoldPoint (the hero's position at the split).
- Teams: followers = alive soldiers with Order.X 1 or 2 (`Abs(X - 1) < 0.5 || Abs(X - 2) < 0.5`). Per role (sword /
  xbow) alternate guard, strike, guard, strike… so odd counts guard. Fewer than 2 followers: no split.
- `PrevX[]` stores each member's Order.X; Restore writes it back. End: tentacle not valid, vitals Health <= 0, no
  hero hit for 6 s, or hero > 2500 cm from it. Tick interval 0.5 s.
- Shouts are left to a socket (PushNotice) until #31's banner is confirmed installed.
