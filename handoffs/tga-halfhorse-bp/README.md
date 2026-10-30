# BP_HalfHorseZombie (#168 behaviour)

Made 2026-10-30 by `TGA (Claude)`, following the owner's order to send ready-to-paste code. Node blocks are cloned from
the Master's 2026-10-30 exports, like the realm wasp's (#174). `applyall check` prints `Validation: OK` (152 nodes).

## What it does

`BP_HalfHorseZombie` is a **child of BP_Zombie**, so cannons, soldiers, hits, wave counts and XP already treat it as a
zombie.

1. **BeginPlay:**
   - It copies the **zombie's own mesh and skin** from the inherited Mesh onto the new **`Torso`** component. Then the
     Mesh becomes `SK_HorseBody` (Bay 60 % / Grey 40 %), so no licensed path is written anywhere.
   - Capsule 60/110, horse mesh 110 cm down.
   - The torso attaches to the horse's **`TorsoSocket`**: location snaps to the socket, world rotation and scale are
     kept. BeginPlay is in the rest pose, so the torso stands upright and from then on rides the stump through gallop
     and rear. It's then lowered by `TorsoDrop` (-100 cm), so its pelvis sits in the stump.
   - It hides the torso's legs with `HideBoneByName`. It tries `thigh_l`/`thigh_r` (mannequin) and
     `LeftUpLeg`/`RightUpLeg` (Mixamo); a name that doesn't exist does nothing.
   - MaxHP 400, XP 20, damage 30. The torso plays the zombie's `ZA_Walk_A`, so its arms sway.
2. **Brain (every 0.25 s):**
   - It chases the hero with `SimpleMoveToActor`, like BP_Zombie. Far away (more than 9 m) it **gallops** (650 cm/s,
     `A_HorseBody_Gallop`); near, it walks (240, `A_HorseBody_Walk`). The anim only restarts when that choice changes.
   - Within 3.2 m it stops and **rears** (`A_HorseBody_Rear`), and the torso swings `A_Attack`.
   - On **frame 22 (0.73 s)**, if the hero is still within 4.2 m: `ApplyDamage`, and the hero is **knocked back**
     (`LaunchCharacter`, 750 forward + 380 up).
   - After 1.25 s it goes back to the chase.
3. **Death:** XP to the hero and `CheckLevelUp`, as BP_Zombie does. Capsule collision goes off and it stops. The horse
   plays `A_HorseBody_Death` (falls on its side) and the torso plays `A_Death`. Lifespan 8 s.
4. **Spawns:** the wave-manager swarm paste in `handoffs/tga-realmwasp-bp/` (#174, updated) also spawns
   `HorsesPerWave` (1) of these at `HorseSpawnLocation` (the breach, X -10500) every wave once `SwarmUnlocked` is true.

## Paste steps (Master)

**Order matters:** create both new Blueprints before you paste the wave-manager hook, because its spawn nodes name
both classes.

1. Run `py "<repo>/handoffs/tga-halfhorse-bp/create_halfhorse_bp_ue.py"`. It creates
   `/Game/CastleDefender/Characters/Enemies/HalfHorseZombie/BP_HalfHorseZombie`, a child of BP_Zombie with a
   **Torso** component.
2. Open it. Paste the 6 lines of `BP_HalfHorseZombie_vars.txt` **one at a time** in My Blueprint.
3. **EventGraph:** press **Ctrl+A, Delete**, paste `BP_HalfHorseZombie_EventGraph.txt`, compile.
4. Do the wave-manager step from #174 (it now has 6 BPVar lines and the horse spawn on the sequence's `then_2`).

**If a node comes in red:** right-click it, **Refresh Node**, and compile. These nodes are built from templates with a
changed signature, so they're the ones to check:
- `GetSkeletalMeshAsset`, `GetMaterial`, `SetSkeletalMeshAsset`
- `K2_AttachToComponent` (rules: SnapToTarget / KeepWorld / KeepWorld)
- `K2_AddWorldOffset`
- `HideBoneByName`

## Test (acceptance)

1. Drop a `BP_HalfHorseZombie` near the hero, or set `SwarmUnlocked` on the wave manager.
2. Press Play. A horse body with the zombie torso on top walks toward you, and gallops when you're far away.
3. Up close it rears, slams down, hurts you and knocks you back.
4. Hits kill it: it falls on its side and gives 20 XP.

## Tune by eye

- **The torso sits too high or too low:** change `TorsoDrop` in the Class Defaults.
- **Legs still show:** the zombie skeleton uses other bone names. Change the four `HideBoneByName` names to its thigh
  bones.
