# #225 Siege engines: gameplay v1

From TGA (Claude), 2026-10-31, an owner assignment relayed by adjustedfilm. The art is #251 (`assets/tga/SiegeEngines`).

This is Blueprint-only: one engine Blueprint with two children, plus a director. **No existing Blueprint is changed.**

| File | Nodes | Check |
|---|---|---|
| BP_SiegeEngine_graph.txt | 207 | fix_impure + applyall check: Validation OK |
| BP_SiegeDirector_graph.txt | 48 | fix_impure + applyall check: Validation OK |

`gen225.py` regenerates both graphs, runs `fix_impure` and writes `VARIABLES.md`. It reuses the farming generator's helpers (#223).

## What it does

1. **Ram (BP_SiegeRam).** It spawns with **4 big zombies** (×1.25) attached behind it at the art's `Push_0..3` sockets. It walks the NavMesh to `BP_CastleGateControl`.
   - **Speed** = 120 cm/s × living pushers ÷ 4. With every pusher dead it stops for good: killing the pushers stops it.
   - **At the gate** (within 7 m) it hits every 5 s: `GateDamage += 20 ÷ (1 + 0.5 × ForgeGate)`, capped at 100. That is the same 0–100 gauge the zombies fill (12 a hit) on `BP_ZombieWaveManager`, so 100 is today's breach, and the forge's gate bands slow it down just as they slow zombies.
   - A dust burst plays on the gate with each hit.
2. **Tower (BP_SiegeTower).** It has the same 4 pushers and walks at 90 cm/s to its **WallPoint**, the nearest `SiegeWall` TargetPoint.
   - **At the wall** (within 7 m) it stops and the **drop bridge lowers over 2 s** (it is snapped to the `Bridge_Hinge` socket and starts raised).
   - Then it **spills 10 zombies onto the wall walk**, one every 2.5 s, spawned at the WallPoint.
3. **Damage.** Engines take every `ApplyDamage` that hits them: crossbow bolts, the hero's sword, and cannonballs (all three apply damage to whatever they hit).
   - A **cannonball counts ×5 and sets the wood burning for 6 s** at 15 HP/s, with smoke.
   - HP: ram 900, tower 1800.
4. **Wreck.** At 0 HP the engine swaps to `SM_Siege_RamWreck` / `SM_Siege_TowerWreck` and hides the bridge.
   - It stops for good, and **its pushers let go and fight on foot**.
   - A big smoke burst plays. **The wreck stays** in the world as debris.
5. **Waves (BP_SiegeDirector).** Every 2 s it checks for a new wave.
   - **At night:** from wave **6** a ram comes; from wave **9** a tower comes too.
   - They appear at the director's spot, 5 m left and right.
   - The director reads `BP_ZombieWaveManager.Wave` and `BP_DayNight.IsNight`. Neither is changed.

**Decision (numbers, TGA):**
- Ram: HP 900, 120 cm/s, a hit every 5 s for 20 %. From full, the gate falls in about 25 s if nothing stops the ram.
- Tower: HP 1800, 90 cm/s, 10 spilled zombies.
- Cannon ×5 with a 6 s burn at 15/s. A ram dies to about 13 cannon hits, or 6 hits plus the burns. Pushers are ×1.25 zombies.
- First ram on night wave 6, towers from night wave 9.

All of these are variables. Tune them on the children or the director.

## Master steps

0. **Import the art:** `py ".../assets/tga/SiegeEngines/import_siege_ue.py"` (#251).
1. **Create the Blueprints:** `py ".../handoffs/siege-225/setup_siege_ue.py"`.
   - Set `DRY_RUN = True` first to see what it would make, then False.
   - Run 1 creates BP_SiegeEngine (Body + Bridge, capsule, AI possess), BP_SiegeRam, BP_SiegeTower and BP_SiegeDirector.
2. **Add the variables:** add the `VARIABLES.md` variables to **BP_SiegeEngine** and **BP_SiegeDirector**, then compile.
3. **Paste the graphs:**
   - `BP_SiegeEngine_graph.txt` into BP_SiegeEngine's EventGraph. Delete the BeginPlay / AnyDamage stubs first.
   - `BP_SiegeDirector_graph.txt` into BP_SiegeDirector.
   - Refresh All Nodes, then compile both.
4. **Run the setup script again.** Run 2 fills the children: Kind, HP, speed, meshes and MeshYaw (ram 180, tower −90, so the fronts face +X).
5. **Level setup:**
   - **Director:** place one **BP_SiegeDirector** outside the walls on the zombies' road, inside the NavMesh, with its arrow pointing at the castle.
   - **Wall points:** place 1–3 **TargetPoint** actors **on the outer wall walk**, each with the **actor tag `SiegeWall`** and its **X arrow pointing out of the castle**. The tower drives to 4.5 m outside that point.
   - **NavMesh:** it must reach the gate and the foot of the wall.
6. **Test with `ForceNextWave`** (the wave manager event) until wave 6 at night, or set `RamFromWave` / `TowerFromWave` to 1 for a quick test.

## Test list

1. **Night, wave ≥ 6:** a ram rolls out of the director's spot with 4 big zombies behind it and heads for the gate.
2. **Gate:** the ram reaches the gate, and every 5 s there is a dust burst and the gate bar drops 20 % (10 % with iron bands). At 100 % the gate breaches as it does today.
3. **Pushers:** kill 2 pushers and it slows to half; kill all 4 and it stops. The dead pushers drop off.
4. **Cannon:** a cannonball hit drains HP fast, and smoke shows it burning for 6 s. Crossbow bolts and sword hits chip it.
5. **Wreck:** at 0 HP the ram becomes the wreck mesh with a big smoke burst. Living pushers walk off and fight, and the wreck stays.
6. **Tower (wave ≥ 9, night):** it drives to the nearest SiegeWall point, stops, and the bridge swings down onto the wall walk. 10 zombies appear on the wall walk, one every 2.5 s.
7. **Bridge direction:** if the bridge rests **pointing down** instead of up before it lowers, set `BridgeUpRoll` to −90 on BP_SiegeTower. The sign depends on the FBX axis conversion.
8. **Day waves:** no engines.

## Honest notes and follow-ups

- **Pushers:** they are real BP_Zombie actors with movement turned off and attached. They stand still on their sockets (idle animation), so there is no pushing animation yet. A small AnimBP flag for "pushing" would be the follow-up.
- **Fire:**
  - Cannonballs ignite the engines.
  - **Fire slime and sword fire don't ignite them yet**: in the 10-30b exports both only target zombies by cast.
  - Wiring them in needs a small manifest into those Blueprints. That's a follow-up once the current exports are in.
- **Spawning:** the spill zombies spawn on the wall walk at the WallPoint, rather than walking over the bridge. That avoids needing NavMesh links on a moving bridge.
- **Turning:** engines turn with `orient to movement` at 45°/s and their capsule is round, so very tight roads may need a wider NavMesh.
