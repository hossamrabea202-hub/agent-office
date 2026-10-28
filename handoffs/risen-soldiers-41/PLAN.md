# #41 Fallen soldiers rise as zombies

Seat: `hossam gmail laptop2 (Claude)` (owner assigned, 2026-10-28).

## Rules

1. A soldier who dies **outside the walls** is added to the **Fallen list**. One who dies **inside** isn't.
   Inside = within the castle rectangle (x 0..4600, y 0..3450, `handoffs/exports/checkking/project/BLUEPRINTS.md`),
   checked with an actor-in-box test (or a `BP_CastleInside` trigger volume, which is cleaner if the walls move).
2. **Next wave:** each fallen soldier rises **once** as a zombie, at the spot he fell (within 2 m, on the navmesh),
   in the first 20 s of the wave, spread out (one every 1-2 s), with a rise animation and a dust/slime burst.
3. **He keeps his look:** the same knight mesh with the zombie material overlay (pale, rot, glowing eyes), his
   **rank cape and banner colours**, and the #17 logo once it exists. The player recognises his own men.
4. **Tougher by rank:** HP and damage = the zombie base x (1 + 0.25 x rank): recruit 1.0, veteran 1.25, elite
   1.5, commander 2.0 (a fallen commander rises as a mini-boss with his cape and a dark aura).
5. **The squad saves them:** a soldier's body that a living squad member reaches within 10 s of his death (#15
   commander-death retreat: the squad runs back) is carried home and doesn't rise. Decision: this only applies to
   commanders at first (his squad carrying him back), regular soldiers just rise.
6. Killing a risen soldier removes him for good. He gives the normal zombie gold + XP and drops his rank emblem
   (cosmetic notice: `Sergeant Aldric is at rest`, if soldiers have names; otherwise `A fallen veteran is at rest`).
7. **Cap:** at most 12 risen soldiers per wave (the oldest fallen first). The rest wait for later waves.

## Implementation

- **Soldier death** (`BP_SoldierSword` / `BP_SoldierXbow` / `BP_SoldierCommander`, the existing death branch): if
  outside -> append `{Location, Rank, CapeColour, Role, Name}` to `FallenList` on `BP_ZombieWaveManager` (it already
  owns the wave spawns).
- **Wave start** (`BP_ZombieWaveManager`): after the normal spawn list is built, start a timer that pops up to 12
  entries from FallenList and spawns `BP_ZombieRisen` at each location.
- **BP_ZombieRisen** = child of `BP_Zombie`: on spawn, set the knight skeletal mesh (retarget is already done for
  the soldiers: same skeleton family `ShadowknightUE_Skeleton`; if the zombie AnimBP can't drive it, use the
  soldier's mesh with the zombie AnimBP via a Leader Pose / copy pose on the zombie skeleton), attach the cape
  component with the rank colour, the overlay material `M_RisenOverlay` (pale + veins + emissive eyes, gated by
  nothing: always on), and the rank multipliers on MaxHP / damage.
- **Rise:** a 1.2 s montage from the ground (reuse a zombie get-up anim if there is one, otherwise a root-motion
  lift from -120 cm with a dust Niagara burst and the slime splat from BP_JellyBlob).
- **Save/load:** `FallenList` goes in the wave save, so quitting mid-game keeps them.

## Checks (Play)

1. A soldier dies outside the walls. Next wave: he rises at that spot, with his cape colour and rank.
2. One dies inside the walls: he never rises.
3. A risen elite has 1.5x HP. A fallen commander is a mini-boss.
4. Kill a risen soldier: he's gone for good, with the notice.
5. 20 fallen: 12 rise this wave, 8 the next.
6. Save with fallen soldiers, load: they still rise next wave.

## Exports needed (fresh)

`BP_SoldierSword`, `BP_SoldierXbow`, `BP_SoldierCommander` (death branch + rank/cape variables),
`BP_ZombieWaveManager` (wave start), `BP_Zombie` (spawn/init + HP), the zombie AnimBP name, the wave save function.
