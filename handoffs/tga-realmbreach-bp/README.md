# BP_RealmBreach (#169 stage 2: the wall breaks at wave N)

Made 2026-10-30 by `TGA (Claude)`. The owner asked TGA to take it because Codex is out of usage. It's ready to paste:
node blocks are cloned from the Master's exports (BP_Zombie, BP_ZombieWaveManager), and `applyall check` prints
`Validation: OK` (49 nodes).

## What it does

It's a separate actor, so nothing is merged into the wave manager. Once a second it reads `WaveManager.Wave`. When
`Wave >= BreachWave` (**5**) it breaks the realm wall, **once**:
1. It hides `Realm_Wall_Breach_A/B` and turns their collision off. It shows **`Realm_Wall_Breached`**
   (`SM_SiegeBarricade_Breach`, pre-placed hidden by the script) and turns its collision on, so the gap is passable.
2. It plays a **smoke burst** (`P_Smoke_Burst` ×3.5), the **explosion crash** and a **camera shake** (`BP_CannonShake_Impact`,
   90 m).
3. It sets **`WaveManager.SwarmUnlocked` = true**. That starts the wasp swarm waves and the half-horse spawns from
   #174/#175.
4. **The realm horde walks out:**
   - a `BP_Zombie` at every `Realm_Spawn_Zombie_NN` (12)
   - a `BP_HalfHorseZombie` at every `Realm_Spawn_Giant_NN` (2)

   Each one gets `ResumeMove`, as the wave manager does for its zombies, so they head out through the gap and on to the
   castle the way zombies already move. No new sensing system is used.

## Paste steps (Master)

**Order:** do this after the #174 wave-manager vars (it sets `SwarmUnlocked`) and after #175 (it spawns
`BP_HalfHorseZombie`).
1. Run `py "<repo>/handoffs/tga-realmbreach-bp/create_realmbreach_bp_ue.py"`. It creates
   `/Game/CastleDefender/Realm/BP_RealmBreach`.
2. Open it. Paste the 9 lines of `BP_RealmBreach_vars.txt` **one at a time**. Two are actor arrays.
3. **EventGraph:** press **Ctrl+A, Delete**, paste `BP_RealmBreach_EventGraph.txt`, compile.
4. **Run the same script again.** It places the hidden broken wall between the breach pair, spawns `Realm_Breach_BP`,
   and wires the wave manager, both palisades and the 14 spawn points. Save the level.

**If a node comes in red:** right-click it, **Refresh Node**, and compile. These nodes are adapted from similar ones:
- `SetActorHiddenInGame` and `SetActorEnableCollision`
- `Wave` (get) and `SwarmUnlocked` (set) on the wave manager
- the two ForEachLoops typed to Actor

## Test (acceptance)

1. On `Realm_Breach_BP`, set `BreachWave` = 1, then press Play.
2. When wave 1 is reached: a crash, a shake and smoke. The two palisades are gone and the broken wall stands in their
   place.
3. 12 zombies and 2 half-horses come out of the realm through the gap toward the castle.
4. From then on, wasps and half-horses join the waves.

## Tune

- `BreachWave` on the instance (default 5).
- Want a gentler break? Lower the smoke scale or the shake radius in the graph.
