# #80 Army split: BP_ArmySplit

By `hossam gmail laptop2 (Claude)`, 2026-10-29. Built from the 10-28 exports in `handoffs/exports/laptop2/gameplay/`,
following PLAN.md "v1 implementation": no hero edit and no soldier edit. Both teams use order 5 (hold at Goal), and
the manager makes the strike team's attacks itself.

`gen80.py` writes `BP_ArmySplit_graph.txt` with the Master's node kit (`tools/master/t81/kit.py`).
The wiring checker (`chk.py`) found 0 problems: 277 nodes, 348 links.
**Not compiled yet**: that needs the editor.

## What it does

- **Hero hits a tentacle** (any `TentacleHit` part, damage causer = the hero): the followers are split into 2 teams.
  Followers are alive soldiers on order 1 or 2, not commanders. Fewer than 2 followers: no split.
- **Team picking:** swords first, then crossbows, alternating guard, strike, guard… Odd counts: the extra one guards.
- **Strike team:**
  - Swords hold a 2.5 m ring around the tentacle. They step back to 5 m while its slam runs (`BPC_TentacleStrike.State != 0`).
  - Crossbows stand 13 m from the tentacle on the hero's side, about 1.5 m apart.
  - Every 0.5 s each one may attack:
    - Swords: 45 %, slash montage, 20 damage, never during the slam.
    - Crossbows: 30 %, aim montage, bolt, 15 damage.
- **Guard team:** holds a 4 m ring around the spot where the hero stood at the split.
- **End:** any one of these ends the split:
  - the tentacle dies (or is gone),
  - the hero lands no hit for 6 s,
  - the hero is more than 25 m away.
- **After the end:** everyone still on order 5 gets back their old Order and Goal. A soldier you re-ordered during the
  split keeps the new order.

## Steps (editor driver)

1. **Create:** run `py ".../handoffs/tentacle-split-80/bp/create_bp_armysplit.py"`.
   - It makes `/Game/CastleDefender/Gameplay/Army/BP_ArmySplit` (parent Actor) with the variables below and their defaults.
   - It sets Tick Interval 0.5.
   - It places one instance at the origin of the open level.
   - Read the Output Log. Any line with `!` or `not set` must be done by hand from the table.
2. **Paste:**
   - Open BP_ArmySplit and go to its EventGraph.
   - Delete the 3 grey default events (BeginPlay, ActorBeginOverlap, Tick). The paste brings its own BeginPlay and Tick.
   - Click the empty graph, then paste the whole `BP_ArmySplit_graph.txt`.
3. **Compile and save.** If a node shows an error, see "Check after paste" below.
4. **Place:** check that exactly one BP_ArmySplit is in every map with tentacles (step 1 places it in the open map).
   Then save the map.

## Variables

If `add_member_variable` is missing in your build, add these by hand (My Blueprint > Variables), then compile and set the defaults.

| Name | Type | Default |
|---|---|---|
| Tentacle | Actor (object ref) | |
| HitPart | Actor (object ref) | |
| TentVitals | BP_TentacleVitals (object ref) | |
| HoldPoint | Vector | |
| Members | BP_SoldierSword (object ref), Array | |
| Strike | BP_SoldierSword (object ref), Array | |
| Guard | BP_SoldierSword (object ref), Array | |
| PrevOrder | Vector, Array | |
| PrevGoal | Vector, Array | |
| Active | Boolean | false |
| LastHitAt | Float (double) | 0 |
| PickN | Integer | 0 |
| StrikeRadius | Float | 250 |
| StepBackRadius | Float | 500 |
| GuardRadius | Float | 400 |
| XbowStandoff | Float | 1300 |
| SwordDamage | Float | 20 |
| XbowDamage | Float | 15 |
| SwordHitChance | Float | 0.45 |
| XbowShotChance | Float | 0.3 |
| EndNoHitTime | Float | 6 |
| EndDistance | Float | 2500 |

The last 10 are the tunables. The crossbow spread (6.6 degrees, about 1.5 m at 13 m) is a number inside StrikeStep.

## How it reads the game (from the exports)

- **Soldier orders:** the components `Order` (RelativeLocation.X = order) and `Goal` (RelativeLocation = point), the same
  way the commander-kit v2 HUD writes them.
  - Setting order 5 keeps Order.Y and Order.Z.
  - Restore writes back the whole saved vectors.
- **Alive:** soldiers have no `Dead` bool (PLAN was wrong there). Their `State` component has Z = 1 when dead (the
  soldier graph sets (0,0,1) at 0 HP), so alive = `State.Z < 0.5`. That is the same test the soldier's own Tick uses.
- **Crossbow:** tag `Xbow`. **Commander:** tag `Commander` (they are excluded).
- **Tentacle hits:** BP_TentacleVitals binds OnTakeAnyDamage on the actors attached to its attach parent that have the
  tag `TentacleHit`. The manager binds the same parts, and damages the last part the hero hit (`HitPart`).
- **Tentacle position:** the attach parent of the hit part. **Slam:** `BPC_TentacleStrike` on the vitals actor,
  int `State`, where anything other than 0 is the wind-up or strike.

## Sockets (not in v1)

- **Shouts:** "With me!", "Hold the line!" and "Fall back!" are not in yet. They wait for #31's PushNotice banner.
  Hook them here:
  - "With me!" and "Hold the line!": after `Set Active` (true) in Engage.
  - "Fall back!": at the start of Restore, only when Active is true.
- **Commander squads** led by the hero (PLAN rule 2, "later") are not included.

## Check after paste (things I could not verify without the editor)

- Every node should compile without "pin not found" warnings. The ones most at risk are listed below.
  - **Custom event `OnTentHit` wired to `Bind Event to OnTakeAnyDamage`**: if the red link is dropped, drag from the
    bind node's Event pin to OnTentHit again. Its signature was copied from BP_TentacleVitals's `OnShocked`.
  - **`Get Component by Class` (BPC_TentacleStrike) -> `State`**: the output should be typed BPC_TentacleStrike. If it shows
    "Actor Component", re-pick the class on the node.
  - **Nodes not copied from an export**, so their pin names come from the engine API:
    - Set Actor Tick Interval (`TickInterval`)
    - DegCos / DegSin (`A`)
    - Percent_IntInt (`A`, `B`)
    - EqualEqual_BoolBool
    - NotEqual_IntInt
    - SelectFloat
    - Array Get (the Vector arrays)
- Variables must exist with exactly these names before the paste. Otherwise the getters paste as "variable not found".

## Checks (Play)

1. Have 6 or more followers on follow, then hit a tentacle.
   - About half go to it, swords and crossbows both.
   - The other half form a ring at the spot where you stood.
2. Let zombies come in. The guard ring kills them and doesn't drift to the tentacle.
3. When the tentacle slams, the swords back off and then return.
4. Each of these puts everyone back to follow:
   - the tentacle dies,
   - you walk 25 m away,
   - you stop hitting it for 6 s.
5. With 1 follower there is no split. With 7 followers, 3 strike and 4 guard.
6. (Extra) The tentacle's HP bar drops from the soldiers' hits. Crossbow bolts fly at the tentacle.
