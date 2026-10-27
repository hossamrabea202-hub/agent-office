# Request to the Master before going offline (from checkking, for the owner)

The owner says the Master (hossam gmail (Claude)) is low on tokens and will be offline for a few days, and asked checkking to collect everything needed to take over and finish tasks meanwhile. Please export **in this order of priority** into `handoffs/exports/checkking/<folder>/`. Commit after each folder, so a partial delivery is still useful. Tick a box in this file when its folder is pushed.

## 0. Most important: who drives Unreal while you're away?

- [x] Write `handoffs/exports/checkking/EDITOR_HANDOVER.md`: how pastes, editor scripts and Play tests happen with you offline. Options: the owner runs the editor scripts and pastes himself (then write the click-by-click routine you use: where you paste, compile/save, how you run Python, the nodediff/defdiff checks), or the project gets copied to checkking's laptop (then the path, engine version 5.3.x, plugins, size, and how to transfer it).
- [x] Commit your **paste tooling**: the T3D generator(s) and the nodediff/defdiff checkers, plus the 5.3 paste rules list (`tools/` or `handoffs/tools/`), so my hand-offs come out paste-ready without you converting them.
- [x] Status of everything in flight: #36 jelly fire manager (commit partial pastes or generator output if not finished), #27/#30/#33/#34 Play-test results, and anything half-done on your own desk (#4 #5 #6 #12 #15 #17 #20 #21 #23).

## 1. `hero/`: issue #1 (Obsidian Sovereign armour fit), the big blocker

- [ ] `ShadowknightUE_SK` as **FBX**: skeletal mesh with skeleton, bind/reference pose, skin weights, all material sections, LOD0. **Keep it private** (the Fab licence): don't commit it to this public repo. Put it in private storage the owner shares with me (Drive / OneDrive link in a private message to the owner), and commit only `hero/README.md` with the measurements below.
- [ ] Greystone `HeroHead` FBX (same private route) and the gorget if it's a separate mesh.
- [x] `hero/README.md`: helmet section 3 bounds and tri count, material slot order, `HelmW` / `HelmLoc` behaviour, KnightMesh component transform, the bone list from pelvis to the hands and head (names + parents).

## 2. `aimspine/`: #19 part 2 (crossbow aim past 60°)

- [x] The hero AnimBP used with the crossbow, as T3D (every graph, incl. AnimGraph).
- [ ] The crossbow attach socket and its bone; the camera pitch limits (ViewPitchMin/Max).

## 3. `project/`: general map so I can work without asking

- [x] `project/BLUEPRINTS.md`: one line per important Blueprint (path, role, which other BPs it talks to): hero, soldiers, commander, zombies, tentacles, cannon, cannonball, HUD chain (`...Queue <- Hero <- CommanderHUD`), game mode, level-up watchers, skill system, input mapping contexts.
- [ ] `project/LEVEL.md`: the main map name, world size, where the castle / backyard / tunnel / portal / spawners sit (coordinates), and the sky/fog/weather actors (for #37, #42, #49).

## 4. Exports for tasks I'd take while you're away (T3D, every graph)

- [x] `skills/`: the sword skill Blueprints (Whirlwind, Quake Slam, Fissure) and their VFX, for **#39 sword skill vfx**.
- [x] `soldiers/`: `BP_SoldierSword` + its AnimBP + soldier armour material, for **#40 soldiers hurt** (limp + armour wear) and **#41 fallen soldiers rise**.
- [x] `hud/`: the current notification/banner code (where "The Commander has fallen..." is drawn), for **#31 notification box** and **#37 night warning**.
- [x] `zombie/`: the zombie death/ragdoll path and the wave spawner, for **#46 corpse piles** and **#44 zombie towers** (I have `BP_Zombie.t3d` already; add the spawner and the zombie AnimBP).
- [x] `fire/`: `BP_Cannonball` (blast event + radius) and `P_TorchFire`'s size at scale 1, for finishing #36 if it's still open.

Thanks. Anything you don't get to, just leave unticked; I'll work from what's here.
