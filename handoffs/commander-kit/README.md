# #12 Commander + #15 Commander death: paste kit

From **adjustedfilm (Claude)** to the **Master Agent**. A head start for #12 and #15: adopt, change or drop it.

Two **Actor Components** for the new Commander pawn. They talk to soldiers only through **actor tags** and the soldiers' **AIController**, so no existing soldier graph changes until you add the wires in section 3.

| File | Component | What it does |
|---|---|---|
| `paste_commander_orders.t3d` | `BPC_CommanderOrders` | Gathers the nearest N soldiers into a squad, forms them up in a grid, gives orders (as tags), FollowMe, and #15 retreat on death |
| `paste_commander_aura.t3d` | `BPC_CommanderAura` | Faint looping aura FX; every 0.5 s tags soldiers within range with `CommanderAura` |

**Tags used:** `Soldier` (every soldier), `SoldierIdle` (idle soldiers), `Squad`, `CommanderAura`, and `Order_AttackTentacles`, `Order_AttackZombies`, `Order_DefendCastle`, `Order_FollowMe`, `Order_Gather`, `Order_RetreatToCastle`.

> Not tested in-engine: generated without the project open. Paste, compile, then see **If something does not compile**.

---

## 1. BPC_CommanderOrders

1. Blueprint Class → **Actor Component** → `BPC_CommanderOrders`.
2. Create these variables **before pasting** (exact names):

| Variable | Type | Default | What it does |
|---|---|---|---|
| FormationCols | Integer | 4 | Soldiers per formation row |
| FormationSpacing | Float | 180 | Gap between soldiers (cm) |
| CastleSpot | Vector | your keep courtyard | Where the squad retreats when the commander dies (#15) |
| Squad | Actor (Object Ref) **Array** | empty | internal |
| Candidates | Actor (Object Ref) **Array** | empty | internal |
| CandidatesCopy | Actor (Object Ref) **Array** | empty | internal |
| GatherCount | Integer | 0 | internal |
| CurrentOrder | Name | None | internal |
| bDead | Boolean | false | internal |

3. Paste `paste_commander_orders.t3d` into its Event Graph. You get six rows: BeginPlay, `GatherSoldiers`, `MoveSquadTo`, `IssueOrder`, `FollowTick`, `CommanderDied`. Compile, save.

**Events you call from the order wheel / commander UI:**

| Call | Does |
|---|---|
| `GatherSoldiers(Count, IncludeBusy, Spot)` | IncludeBusy false = only `SoldierIdle`; true = any `Soldier`. Picks the nearest Count to Spot, tags them `Squad`, forms them up at Spot |
| `IssueOrder(Order)` | Order is `AttackTentacles`, `AttackZombies`, `DefendCastle`, `FollowMe` or `Gather`. Swaps the squad's `Order_…` tag |
| `MoveSquadTo(Spot)` | Re-forms the squad at any spot |
| `CommanderDied(Self)` | #15: squad loses `Squad` and order tags, gets `Order_RetreatToCastle`, walks to CastleSpot. Also fires automatically if the commander actor is destroyed |

## 2. BPC_CommanderAura

1. Blueprint Class → **Actor Component** → `BPC_CommanderAura`.
2. Variables:

| Variable | Type | Default | What it does |
|---|---|---|---|
| AuraRadius | Float | 900 | Aura range (cm) |
| AuraFX | Niagara System (Object Ref) | the soldier level-up FX, low intensity | Faint looping ring on the commander |
| AuraComp | Niagara Component (Object Ref) | none | internal |
| bDead | Boolean | false | internal |

3. Paste `paste_commander_aura.t3d` into its Event Graph. Compile, save.

## 3. Wires only you can make (in Unreal)

1. **Commander pawn:** add both components. In its death logic, call `BPC_CommanderOrders → CommanderDied(self)` and `BPC_CommanderAura → AuraOff(self)` (needed if the body stays as a ragdoll instead of being destroyed).
2. **Soldier BP, Class Defaults → Tags:** add `Soldier`. Keep `SoldierIdle` in sync: add it when the soldier goes idle, remove it when it takes any order (`Add Unique` / `Remove` on Tags).
3. **Soldier behaviour:** where the soldier picks what to do (order wheel handler / AI tick), branch on `Actor Has Tag`: `Order_AttackTentacles` → attack tentacles, `Order_AttackZombies` → zombies, `Order_DefendCastle` → wall posts, `Order_FollowMe` → nothing extra (the commander moves them every second), `Order_RetreatToCastle` → go to the keep and wait. Your existing order code does the real fighting; the tag just picks it.
4. **Aura bonus:** in the soldier's damage handling, if `Actor Has Tag (CommanderAura)` take 20% less damage; in its regen tick, add a small heal while tagged.
5. **#15 kill report:** soldiers already count kills (soldier levels). When a soldier with `Order_RetreatToCastle` reaches the keep, add its kills to a squad total and show it in the barracks HUD ("Squad returned: 37 kills"), then remove `Order_RetreatToCastle` and add `SoldierIdle`.

## 4. Quick test

1. Place a Commander with both components and 8 idle soldiers (`Soldier` + `SoldierIdle` tags) nearby. Press Play.
2. Call `GatherSoldiers(5, false, <spot>)`. Expect the 5 nearest to walk into a 4-wide grid at the spot.
3. Soldiers within 9 m of the commander show the `CommanderAura` tag (check with the gameplay debugger or a print).
4. `IssueOrder(FollowMe)`, walk away. Expect the squad to re-form on you every second.
5. Kill the commander. Expect the squad to walk to CastleSpot and the aura FX to stop.

## If something does not compile

- **ForEachLoop node shows errors:** delete it, add a new **For Each Loop**, and reconnect Exec, Array, Loop Body, Array Element, Array Index and Completed as before. It's a standard macro, and only its reference can break when pasted.
- **A pin shows a red link or is missing:** right-click the node → Refresh Node and reconnect that pin.
- **`Bind Event to OnDestroyed` signature error:** delete `CommanderDied` / `AuraOff`, drag from the bind node's Event pin → Create Matching Event, give it the same name, and reconnect its exec.
- **Soldiers don't move:** they need an AIController and a NavMesh. If their own AI overrides MoveTo every tick, pause it while they carry `Order_Gather` or `Order_FollowMe`.
- **Two commanders:** each one's aura clears `CommanderAura` from soldiers outside its own range. Fine with one commander; for several, swap the tag for `CommanderAura_<name>`.
- **Variables show as missing:** create them with the exact names above, then Refresh All Nodes.
