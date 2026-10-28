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
