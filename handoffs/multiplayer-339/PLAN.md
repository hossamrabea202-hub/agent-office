# #339 Multiplayer: castle vs castle in a zombie world (plan)

By `adjustedfilm (Claude)`, 2026-10-31. Owner `W:`: *"Multiplay castle vs castle in a zombie world"*.

## The game in one paragraph

Two players each hold a castle at opposite ends of one zombie-filled valley. Zombie waves hit both castles. Between
waves, each player builds up (soldiers, cannons, walls, ore from the mine) and can **raid the other castle**: send
soldiers, deploy cannons on the map, or steer zombies toward the rival. You win when the other castle's keep falls,
or when you survive the most waves. Zombies are everyone's enemy, so a weak rival is also a target for the horde.

## Where the project stands

The game is built for **one player**. Today's exports show it:

- about 100 calls to `GetPlayerCharacter(0)` / `GetPlayerController(0)` across the main Blueprints (BP_Crossbow 26,
  BP_FleshBrute 13, BP_Zombie 12, BP_BarracksHUD 10, the HUDs, and more);
- one gold / ore / XP pool, one save slot, HUDs drawn for player 0;
- nothing is set to replicate (zombies, soldiers, cannons, projectiles, waves).

So multiplayer is a **retrofit**, not a switch. It's doable in Blueprints (UE 5.3, no C++), but it touches almost every
system. The plan grows it in slices, so the single-player game keeps working at every step.

## Options

| | A. Split-screen, one PC (recommended first) | B. Online, listen server | C. Async raids (Clash-style) |
|---|---|---|---|
| What | 2 players, 2 controllers, one screen split | one player hosts, one joins over the internet | each plays alone; raids are sent as waves to the other's game |
| Networking | none | full replication | a backend server |
| Cost | free | free (Epic Online Services), or Steam needs a $100 app fee | a paid server: **owner decision** |
| Work | medium: "which player?" everywhere, a 2nd castle, 2 HUDs | large: A + replication of every actor and RPCs | large, plus a server to run |
| Risk | low; it's also the base for B | lag and desync with hundreds of zombies | servers, cheating |

**Decision (default, reversible):** build **A first**. A has to happen anyway: every `GetPlayerCharacter(0)` must become
"the player who owns this castle". Then B on top, with zombies kept server-only and cheap (positions and animation
state only).

## Slices (each one ships on its own and keeps single player working)

1. **Audit** (no editor needed): list every `GetPlayer*(0)`, every global pool (gold, ore, XP, skill points) and every
   save call, per Blueprint, from the exports. This becomes the work list.
2. **Player ownership:** a `BP_CastleOwner` component (team 0 / 1) on the hero, castle, soldiers and cannons. Calls of
   `GetPlayerCharacter(0)` change to "my team's hero". Gold, ore and XP move per team.
3. **Second castle:** place a mirrored castle at the far end of the valley, with its own wave spawners, barracks and
   artillery yard. TGA builds the variant art (walls in another stone colour, a different banner).
4. **Split-screen:** local player 2 joins (Create Player), two HUDs, two cameras, and a team colour on the soldiers.
5. **Raids:** soldiers can be ordered to the enemy castle, cannons can be deployed against it (the #283 map), and zombies
   attack whoever is nearest or weakest.
6. **Win / lose:** keep HP, a victory screen, and saves per match.
7. **Online (option B):** host / join menu (EOS, free), with replication set per actor, after slice 6 plays well.

## What I need from the owner

- **OK on "split-screen first, online later"?** Or online straight away? That roughly doubles the work and needs EOS
  or Steam setup.
- Is the **map** one valley with two castles (my default), or a bigger world?
