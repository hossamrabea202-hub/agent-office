# #3 Tentacles strike the cannon: paste handoff

From **adjustedfilm (Claude)** to the **Master Agent**. Issue: #3.

One or two tentacles wobble, rear back and whip their tip into the nearest cannon like a scorpion. Each hit damages the cannon, which steps through three baked break stages (same idea as the gate breach) and is out of the fight at stage 3.

It is two self-contained **Actor Components**, so nothing in the existing tentacle or cannon graphs has to change:

| File | Component | Goes on |
|---|---|---|
| `paste_tentacle_strike.t3d` | `BPC_TentacleStrike` | the tentacle Blueprint |
| `paste_cannon_break.t3d` | `BPC_CannonBreak` | the cannon Blueprint (`SM_FieldCannon_HD`) |

They talk only through engine features: the cannon actor tag `Cannon`, a temporary tentacle tag `CannonStriker` (caps attackers at `MaxStrikers`), and **Apply Damage → OnTakeAnyDamage**.

> Not tested in-engine: written without the project open. Paste, compile, and check **If something does not compile** at the bottom.

---

## 1. BPC_TentacleStrike

1. Content Browser → Blueprint Class → **Actor Component** → name `BPC_TentacleStrike`.
2. Create these variables **before pasting** (exact names; nodes bind by name):

| Variable | Type | Default | What it does |
|---|---|---|---|
| StrikePivot | Scene Component (Object Ref) | none | The part that leans. Empty = the tentacle's root |
| StrikeRange | Float | 3000 | Max distance to a cannon (cm) |
| StrikeDamage | Float | 450 | Damage per hit |
| StrikeEvery | Float | 12 | Seconds between strike attempts (randomised per tentacle) |
| MaxStrikers | Integer | 2 | How many tentacles may attack at once |
| LeanSign | Float | 1 | Set to -1 if it leans away from the cannon |
| WobbleTime | Float | 1.4 | Wobble warning (s) |
| WindupTime | Float | 0.45 | Rear-back (s) |
| StrikeTime | Float | 0.16 | The whip (s) |
| RecoverTime | Float | 0.9 | Back upright (s) |
| WobbleDeg | Float | 7 | Wobble size (degrees) |
| WindupDeg | Float | -22 | Rear-back angle |
| StrikeDeg | Float | 58 | Strike angle |
| HitFX | Niagara System (Object Ref) | e.g. the cannonball blast | Spawns on the cannon at impact |
| HitSound | Sound Base (Object Ref) | an impact SFX | Plays at impact |
| State | Integer | 0 | internal |
| StateTime | Float | 0 | internal |
| Angle | Float | 0 | internal |
| TargetCannon | Actor (Object Ref) | none | internal |
| BaseRot | Rotator | 0 | internal |
| LeanAxis | Vector | 0 | internal |

3. Open the component's **Event Graph**, open `paste_tentacle_strike.t3d` (Raw), copy everything, click the graph and **Ctrl+V**. You get rows for BeginPlay, `TryStrike`, Tick, the four states and the rotation.
4. Compile and save.
5. Add `BPC_TentacleStrike` to the tentacle Blueprint (Add Component). Tentacles farther than `StrikeRange` from every cannon never strike.

**StrikePivot:** if the tentacle is rooted at its base, leave it empty. If the root is not at the base, add a Scene Component at the base, parent the mesh to it, and in the tentacle's BeginPlay set `BPC_TentacleStrike → StrikePivot` to it.

**Existing wobble / jelly shell:** the component only rotates the pivot, so it stacks on top of bone animation. If another graph sets the actor's rotation every tick, use a separate pivot as above.

## 2. BPC_CannonBreak

1. Blueprint Class → **Actor Component** → `BPC_CannonBreak`.
2. Variables:

| Variable | Type | Default | What it does |
|---|---|---|---|
| MaxHP | Float | 1200 | About 3 strikes per stage with the defaults |
| HP | Float | 0 | internal |
| Stage | Integer | 0 | internal (0 intact … 3 wrecked) |
| NewStage | Integer | 0 | internal |
| StageMeshes | Static Mesh (Object Ref) **Array** | the 3 baked stages, in order | Swapped in at stage 1, 2, 3 |
| TargetMesh | Static Mesh Component (Object Ref) | none | Which mesh to swap. Empty = the first Static Mesh Component on the cannon |
| BreakFX | Niagara System (Object Ref) | debris/smoke burst | Spawns at every stage step |
| BreakSound | Sound Base (Object Ref) | metal crunch | Plays at every stage step |
| bDestroyed | Boolean | false | True at stage 3 |

3. Paste `paste_cannon_break.t3d` into its Event Graph. Compile, save.
4. On the cannon Blueprint: **Add Component → BPC_CannonBreak**, and add the Actor Tag **`Cannon`** (Class Defaults → Actor → Tags). Tentacles only look for that tag; it is removed when the cannon is wrecked so they stop targeting it.
5. If the cannon has several meshes (carriage, barrel, wheels), set `TargetMesh` in the cannon's BeginPlay to the one the stage meshes replace.
6. **Stop the cannon firing when wrecked:** in the cannon's fire input / fire function, add a Branch on `BPC_CannonBreak → bDestroyed` (false = fire). Same for the cannon crew reload. This is the one wire I could not make from outside the project.

## 3. Baked break stages (needs Unreal)

Same approach as the gate breach. From `SM_FieldCannon_HD`:

| Stage | Look | Name |
|---|---|---|
| 1 | Dented barrel, splintered carriage edge, one wheel cracked | `SM_FieldCannon_HD_Break1` |
| 2 | One wheel off, carriage split, barrel tilted down | `SM_FieldCannon_HD_Break2` |
| 3 | Barrel on the ground, carriage in pieces, wheels flat | `SM_FieldCannon_HD_Break3` |

Fracture Mode → Cluster or Uniform fracture → simulate with an impulse at the barrel (the hit comes from above and in front) → convert the settled pose to a static mesh. Repeat with stronger impulses for stages 2 and 3, then fill `StageMeshes` in order. If the gate used another method, follow that; the component only needs three static meshes.

## 4. Quick test

1. Put a cannon within 3000 cm of 1–2 tentacles, press Play, wait about 12 s.
2. Expect: a tentacle wobbles ~1.4 s, rears back, whips forward; FX and sound on the cannon; Break1 after ~3 hits, Break3 after ~9; then the cannon stops firing.
3. Never more than two tentacles striking at once.
4. Fast debug: `StrikeEvery = 3` and `MaxHP = 300`.

## If something does not compile

- **Leans the wrong way:** `LeanSign = -1`.
- **A pin shows a red link or is missing:** right-click the node → Refresh Node and reconnect that pin. The text was generated without the editor, so a pin name may differ in your engine version.
- **`Bind Event to OnTakeAnyDamage` signature error:** delete `OnCannonDamaged`, drag from the bind node's red Event pin → Create Matching Event, name it `OnCannonDamaged`, reconnect its exec to the first Branch and `Damage` to the Subtract.
- **`Get Component by Class` has no exec pins in your version:** connect the Branch's False straight to Set TargetMesh.
- **Variables show as missing:** create them with the exact names above, then Refresh All Nodes.
