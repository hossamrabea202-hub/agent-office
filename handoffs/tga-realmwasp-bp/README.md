# BP_RealmWasp + swarm waves (#167 behaviour, #169 stage 3)

Made 2026-10-30 by `TGA (Claude)`, following the owner's order to send ready-to-paste code. The pastes are built from
the Master's 2026-10-30 exports: node blocks are **cloned from BP_Zombie, BP_ZombieWaveManager and BP_ArmoryHUD**,
so the pins are exactly what UE 5.3 writes.
- **Wave manager:** `applyall merge --dry-run` against the live export prints `Validation: OK`.
- **Wasp graph:** `applyall check` prints `Validation: OK`. It's a new Blueprint, so there's nothing to merge into.

## What it does

`BP_RealmWasp` is a **child of BP_Zombie**, so cannons, soldiers, the hero's hits, wave counts and XP already treat it
as a zombie. Its own BeginPlay, Tick and AnyDamage replace the walking-zombie brain. No other code changes are needed.

1. **BeginPlay:**
   - mesh `SK_RealmWasp`, capsule 45/60, mesh 130 cm down, gravity 0
   - skin: Ember (70 %) or Blight (30 %)
   - MaxHP 80, XP 6, sting damage (`AttackDamage`) 14
   - then the hover animation plays
2. **Tick:** flies toward `GoalLoc` at `CurSpeed` and faces where it's going. Every 0.2 s it thinks.
3. **The brain, state by state:**

   | State | What happens |
   |---|---|
   | **0** | Circles once out of the crack (4 s, 7 m radius), then picks a target |
   | **1** | Hovers `HoverHeight` (3.8 m) above the target, and dives once it's within 3.5 m |
   | **2** | Dives (`DiveSpeed` 1700) and stings. On **frame 13 (0.43 s)**: `ApplyDamage(Target)`. A stung **cannon loses its load (`bLoaded`=false)**, so the crew must reload. The hero takes the sting too if within 4.5 m |
   | **3** | Rises 3.5 m |
   | **4** | Recovers for 1.4 s, then makes the next pass |

   - **Targets:** first a random **cannon** (`BP_Cannon`). After `HitsPerTarget` (3) stings it moves on to the
     **castle gate** (`BP_CastleGateControl`). With no gate it goes for the hero.
4. **Death:** XP to the hero and `CheckLevelUp`, as BP_Zombie does. Gravity comes back, so it **falls out of the air**
   and plays `A_RealmWasp_Death`. Lifespan 6 s.
5. **Swarm waves (wave manager):** after the wave counter goes up, every `SwarmEveryNthWave`-th (2) wave spawns
   `SwarmSize` (6) wasps around `SwarmSpawnLocation`. This only happens once **`SwarmUnlocked`** is true. The breach
   logic (Codex, #169 stage 2) sets it.

## Paste steps (Master)

1. Run `py "<repo>/handoffs/tga-realmwasp-bp/create_realmwasp_bp_ue.py"`. It creates
   `/Game/CastleDefender/Characters/Enemies/RealmWasp/BP_RealmWasp`, a child of BP_Zombie.
2. Open BP_RealmWasp. In **My Blueprint**, paste the 14 lines of `BP_RealmWasp_vars.txt`, **one at a time**.
3. **EventGraph:** press **Ctrl+A, Delete** (this removes the greyed-out placeholder events). Paste
   `BP_RealmWasp_EventGraph.txt`. **Compile.**
4. **BP_ZombieWaveManager:**
   - paste the 4 lines of `BP_ZombieWaveManager_vars.txt`
   - export the EventGraph and run `python applyall.py merge --live <export> --manifest manifest_wavemanager.json --out merged.t3d`
   - in the EventGraph press Ctrl+A, Delete, paste `merged.t3d`, then compile
5. Re-run `assets/tga/RealmCrack/place_realmcrack_ue.py` (#171). It now also writes the crack mouth into the wave
   manager's `SwarmSpawnLocation`. Or type the location in by hand. Save the level.

**If a node comes in red:** right-click it, **Refresh Node**, and compile. These nodes are built from templates with a
changed signature, so they're the ones to check:
- `SetSkeletalMeshAsset`
- `VInterpTo_Constant`
- `K2_SetActorLocation`
- `Cos`
- the cast to `BP_Cannon` and the `bLoaded` set
- the typed `Get` and `Length` on the cannon array

## Test (acceptance)

1. On the wave manager instance, set `SwarmUnlocked` = true and `SwarmEveryNthWave` = 1, then press Play.
2. When the next wave starts, **6 wasps** come out at the crack, circle once, and fly to a cannon.
3. They dive and sting. The cannon has to be reloaded, and you take damage if you stand next to it.
4. After 3 stings each, they go for the castle gate.
5. Sword, crossbow or cannon hits kill them. They drop out of the air, die, and give XP.

## Known limits

- **Cannons can't be destroyed yet** (that's the open cannon bug). A sting unloads them.
- Gate damage only counts if `BP_CastleGateControl` reacts to AnyDamage.
- The wasps fly in straight lines and pass through walls. This is intentional for a swarm over the walls; it uses no
  nav mesh.
