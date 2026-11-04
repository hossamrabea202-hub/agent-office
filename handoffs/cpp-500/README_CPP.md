# #500 C++ for the hot spots: step 1 = zombie target pick + crowd subsystem (i5, written ahead, NOT compiled yet)

Written by checkking on i5 while the owner installs Visual Studio Community. **Nothing here is compiled or tested**: i5 has no compiler yet.
The first build will show any mistakes; send i5 the compiler output.

## What is in it
- `Source/CastleDefender.Target.cs`, `Source/CastleDefenderEditor.Target.cs`, `Source/CastleDefender/CastleDefender.Build.cs`, `CastleDefender.cpp`: the game module (makes the project a C++ project).
- `ZombieBase.h/.cpp`: **AZombieBase**, a Character subclass that becomes BP_Zombie's parent. Native functions BP_Zombie can call:
  - `PickAndSetTarget(Soldiers, Farmers)`: BP_Zombie Think's target pick (CX_501 .. zfTargetFarmer17: two Blueprint loops over every soldier and farmer, per zombie, per Think) as one native loop. Same rules, from the live graph (`dump_BP_Zombie.txt`):
    player first; a soldier not dying (LifeSpan < 0.01), within 250 cm height and 2500 cm, if nearer; then a farmer not Dead within 2500 cm, if nearer; sets Owner (BP_Zombie's target slot).
  - `GetThinkDivisor()` (1 / 2 / 4 by 3000 / 6000 cm) and `IsFullDetail()` (near 3000 cm or rendered): the same tests Think does now, native.
  - registers itself with the crowd subsystem in BeginPlay / EndPlay.
- `CrowdSubsystem.h/.cpp`: **UCrowdSubsystem** (world subsystem, game / PIE only): the zombie list; `GetAliveZombieCount`; `GetZombiesNear(Location, Radius)`;
  optional `bManageBodyCollision` = the C1 rule for all zombies in one native loop (off by default: BPC_CrowdTier does it now; switch over later, then remove the component).
- `reparent_zombie_ue.py`: makes AZombieBase BP_Zombie's parent (dry run, backup, compile check, saves only without new errors).
- `dump_BP_Zombie.txt`, `dump_BP_FleshBrute.txt`: the live brains (i9's BP_Zombie from sync d), for TGA's spec and for checking the C++.

## Steps on i9 (after Visual Studio Community 2022+ with "Game development with C++" is installed)
1. **Back up the whole project folder first.**
2. Close the editor. Copy `handoffs/cpp-500/Source` into the project root (`C:\UnrealProjects\Castle Defender 5.8\Source`).
   In `CastleDefender.uproject` add, at top level next to "Plugins":
   `"Modules": [ { "Name": "CastleDefender", "Type": "Runtime", "LoadingPhase": "Default" } ],`
3. Right-click `CastleDefender.uproject` > Generate Visual Studio project files. Open `CastleDefender.sln`, configuration **Development Editor**, Build. Send i5 the output if it fails.
4. Open the editor (it now loads the module). `py <repo>/handoffs/cpp-500/reparent_zombie_ue.py --dry-run`, then `--apply`.
5. Play test: zombies walk, attack, die, gore and ragdoll as before (nothing in their graph changed yet; only the parent).
6. Share `Binaries/` + `Source/` + the .uproject with i5 (a sync zip), so i5 can open the project. Live session does not carry compiled code.

## Next (after it compiles)
- i5 writes a graph_ops script that replaces Think's two loops (CX_501 .. zfTargetFarmer17) with one `PickAndSetTarget(SoldierCache, FarmerCache)` call. Needs the compiled class to exist.
- Same idea for BP_SoldierSword's fight loop: an `ASoldierBase` with the per-zombie checks native, fed by `GetZombiesNear` (replaces C3's sphere sweep).
- Switch the C1 rule to `bManageBodyCollision` and remove BPC_CrowdTier.
