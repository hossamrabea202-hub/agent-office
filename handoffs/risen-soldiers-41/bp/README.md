# #41 Blueprint pastes: fallen soldiers rise as zombies

By `hossam gmail laptop2 (Claude)`, 2026-10-29. Built against the 10-28 exports in `handoffs/exports/laptop2/gameplay/`.
`gen41.py` makes the 3 paste files with the Master's node kit (`tools/master/t81/kit.py`), the same way as #96.
The wiring check (`ckw/t3d/chk.py`) found 0 problems, and so did the self-check (links both ways, unique pin ids).
**Not compiled yet**: that needs the editor.

## What it does

- A soldier dies **outside** the castle box (x 0..4600, y 0..3450). He goes on the **Fallen list** with his spot,
  rank, kind (sword, crossbow or commander), wave and his cloth material (rank and cape colours). Inside the box: nothing.
- **Next wave:** up to **12** of them rise, oldest first, one every 1 to 1.5 s, within 2 m of the spot (on the navmesh).
  The rest wait for later waves.
- A risen soldier is a `BP_ZombieRisen` (a child of BP_Zombie, so he keeps all the zombie AI, damage, gold and XP).
  He wears his own knight mesh and cloth, plus a pale glow overlay. He comes up out of the ground in 1.2 s with a dust burst.
- **HP and damage** = the normal walker (100 HP, 12 damage) x the wave curves x (1 + 0.25 x (rank - 1)).
  - Recruit 1.0, veteran 1.25, elite 1.5.
  - A commander is 2.0 and 1.2x size, with a dark purple overlay (a mini-boss).
- **Commander carried home:** if a living soldier gets within 3 m of a dead commander within 10 s, he never rises.
- When a risen soldier is killed, he's gone for good. The wave banner shows `A FALLEN VETERAN IS AT REST` for 2.4 s.

**Design:** all new logic lives in 2 **new** Blueprints. The only change to an existing graph is a 10-node hook in
BP_SoldierSword's death branch, which BP_SoldierXbow and BP_SoldierCommander inherit. BP_ZombieWaveManager isn't touched:
the director reads its `Wave` every 0.5 s. The director isn't placed in the level: the first soldier death spawns it.

## Steps (editor driver)

1. **Create:** run `py ".../handoffs/risen-soldiers-41/bp/create_risen41.py"`. It makes:
   - `BP_RisenDirector` (Gameplay/Castle), with 22 variables.
   - `BP_ZombieRisen` (Enemies/Zombie), with 12 variables and a `KnightMesh` component under the inherited Mesh.
   - `M_RisenOverlay` and `MI_RisenOverlay_Boss` (Enemies/Zombie/Risen).

   Read the log. Every line that starts with `MANUAL:` is a step to do by hand. The types and defaults are in the
   `VARS_DIRECTOR` / `VARS_RISEN` tables at the top of the script.
2. **Director graph:** open BP_RisenDirector's EventGraph, paste `BP_RisenDirector_graph.txt`, then compile and save.
3. **Risen graph:** open BP_ZombieRisen's EventGraph, paste `BP_ZombieRisen_graph.txt`, then compile and save. Its call to
   `ShowRestNotice` needs step 2 compiled first. If that node shows an error, right-click it, pick Refresh Node, and compile.
4. **Soldier hook** (BP_SoldierSword EventGraph): paste `Soldier_FallenHook_graph.txt` near the death branch, at about
   X 24200, Y 384. That's the Branch `State.X < 0.01` (CX_445) -> `Set Relative Location` on State (CX_447) ->
   `Set Visibility` on TargetArrow (CX_549) -> `Stop Movement` -> ragdoll. Then rewire 2 links:
   - `CX_447` (Set Relative Location, target State).then -> **FallIn**.execute (the 1-pin Sequence at the left of the paste).
     This replaces its old link to CX_549.
   - **FallOut**.then_0 -> `CX_549` (Set Visibility, target TargetArrow).execute.
   - Then compile BP_SoldierSword, BP_SoldierXbow and BP_SoldierCommander, and save all 3.
5. **Check KnightMesh in BP_ZombieRisen:** it should sit under Mesh at location and rotation 0, with ShadowknightUE_SK and
   the 5 MI_Hero_* materials. Collision: none.

## Verify in the editor (I couldn't confirm these from the exports)

- **The animation (the biggest risk).** The zombie plays single anims (`PlayAnimation`) on SK_Zombie. The knight follows
  with **Set Leader Pose Component**, which only works if both skeletons use the same bone names. I couldn't confirm
  that from the exports.
  - If the knight is frozen in a T-pose or twisted, set `UseLeaderPose = false`.
  - Then give KnightMesh an Anim BP that does **Retarget Pose From Mesh** (an IK Retargeter from SK_Zombie to
    ShadowknightUE).
- **The hidden zombie mesh still animates.** The paste sets `VisibilityBasedAnimTickOption = AlwaysTickPoseAndRefreshBones`
  on Mesh. If that Set node won't compile, delete it and set the same option in Class Defaults -> Mesh -> Optimization.
- **The cape:** I assume the rank and cape colours are on KnightMesh material slot 2. The soldier writes `RankLevel` to
  that slot's dynamic material. I didn't see what BPC_CapeVariation changes.
  - If the cape is a separate mesh or component, it isn't copied.
  - With no saved material (a loaded entry), the risen soldier gets a fresh dynamic material on slot 2 with `RankLevel = Rank`.
- **Rank values:** `Rank.RelativeLocation.Y` is read as 1 recruit, 2 veteran, 3 elite, 4 max (the soldier graph caps it
  at 4.5). The names are RECRUIT, VETERAN, ELITE, CHAMPION and COMMANDER. Soldiers have no name variable, so the notice
  uses the rank.
- **These nodes aren't in any export, so I wrote them from the engine API:** `GetMaterial`, `K2_PauseTimer` and
  `K2_UnPauseTimer` (the risen zombie pauses its `Think` timer while rising), and `Array_Add` / `Array_Set` on typed arrays.
  If one is red after the paste, re-create it from the palette with the same links.
- **The director spawns a risen zombie like the wave manager's normal walker:** ZType 5, Runner off, walk speed 110,
  scale 1, then MaxHP and AttackDamage x the wave curves. It doesn't change his materials, because the zombie mesh is hidden.
- **The overlay** is a simple pale fresnel glow. The veins and glowing eyes from the plan need an artist mask, so they
  aren't in it.

## Not done (and why)

- **Save/load (Play check 6):** none of the exported Blueprints has a SaveGame (no SaveGameToSlot anywhere). When the
  wave save exists, it should save and load the director's `FallenLoc`, `FallenRank`, `FallenKind`, `FallenWave`,
  `FallenTime` and `NextIdx`. On load, spawn BP_RisenDirector if it's missing and set those arrays.
  - `FallenCloth` can't be saved, so it should load as empty entries.
  - Set `FallenTime` to 0 on load.
- **Slime splat:** BP_JellyBlob isn't a splat. It's a moving blob that sets zombie stats, so it isn't used here. Only the
  dust (P_Smoke_Burst) plays.
- **Commander's Niagara aura** and the dropped **rank emblem**: there's no asset for either yet. The commander gets the
  dark overlay and 1.2x size instead.
- **The #17 logo:** it doesn't exist yet.
- **The rest notice** reuses WBP_WaveBanner (title = the notice, count line empty). It shows one at a time, and a new one
  replaces the old one.

## Play checks

1. A soldier dies outside the walls. At the next wave, he comes up near that spot with his cloth colour and the pale glow.
2. A soldier dies inside the walls: he never rises.
3. A risen elite (Rank 3) has `MaxHP` 1.5x a normal walker's in the same wave. A fallen commander is 2x and bigger,
   with the dark overlay.
   - To check, select the actor in the World Outliner while playing and look at MaxHP.
4. Kill a risen soldier: the banner says `A FALLEN ELITE IS AT REST`, and he doesn't come back.
5. 20 deaths outside (for example, send a squad out with the attack order). Next wave: 12 rise within about 18 s.
   The wave after: the other 8.
6. A commander dies and a living soldier reaches his body within 10 s: he doesn't rise.
7. Save/load: blocked until the wave save exists (see above).
