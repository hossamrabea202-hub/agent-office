# #369 Quests + daily rewards (v1: the working system)

By `adjustedfilm (Claude)`, 2026-10-31. Owner `W:`: *"daily rewards. quests map : use inventory, recruit soldier,
commander, kill zombie, mount canon, find object, etc."* This is the logic with a plain screen. TGA makes the quest-map
look and the reward motion graphics later. It is the core of #364 (Day Ledger).

## What the player gets

- **Daily reward:** the first time you play on a new calendar day, you get 100 gold × your streak (day 1 = 100, ...,
  day 7+ = 700). A toast says *"Welcome back! 3 day streak - daily reward +300"*. Miss a day and the streak starts again.
- **10 quests, each paid once**, with a toast *"Quest done: Recruit a soldier +150 gold"*:

  | Quest | Reward |
  |---|---|
  | Open your pack (inventory) | 100 |
  | Visit Vesna's shop | 100 |
  | Recruit a soldier | 150 |
  | Recruit a commander | 300 |
  | Mount a cannon | 150 |
  | Slay 10 zombies | 200 |
  | Slay 50 zombies | 500 |
  | Find the old chest | 300 |
  | Survive a night | 400 |
  | Earn 1000 gold | 300 |
- **Press J:** the quest list shows on the notice board: `[x] Recruit a soldier    [ ] Slay 50 zombies ...`.
- **Saved** in its own slot, `CastleSaveQuests`: quests done, kills, gold earned, last day and streak.

**How:** one new component on the hero (BPC_Quests) watches what the game already shows every 0.5 s: the HUD's
`StatV` / `ShopV` / `Gold`, the hero's `XP` and `MountedCannon`, soldier and commander counts, the chest's `Opened`, and
day/night. **No other Blueprint is changed.**

## Pre-checks (done)

| Check | Result |
|---|---|
| `applyall check` | 431 nodes, 509 links, **Validation OK** |
| `fix_impure.py` | it wants to split 4 casts. All 4 are already wired into the exec chain (each feeds a Set Gold / Save), so that's the known false alarm; nothing to fix. DoesSaveGameExist is in the exec chain. |

## Steps (Master)

1. `py "<repo>/handoffs/quests-369/setup_quests369_ue.py" --dry-run`, then without it. That makes BPC_Quests and adds
   it to the hero as **Quests**.
2. BPC_Quests: paste the 12 lines of `VARIABLES_BPVar.txt` one at a time, Compile, paste `BPC_Quests_graph.txt` into
   its EventGraph, then Compile and Save.

## Tests (Play)

1. Start: a toast *"Welcome back! 1 day streak - daily reward +100"*, and gold +100. Restart the same day: no second
   reward.
2. Press **J**: the 10 quests show, all `[ ]`.
3. Open Vesna's shop: toast *"Quest done: Visit Vesna's shop +100 gold"*. Recruit a soldier, mount a cannon, kill 10
   zombies: each one pays once.
4. Open your pack. If the inventory quest doesn't fire, `StatV` isn't the inventory's flag. Tell me the inventory's
   open flag (one minute) and I'll swap the name.
5. Restart: quests stay done.
