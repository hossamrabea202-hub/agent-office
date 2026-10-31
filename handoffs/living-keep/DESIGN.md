# #364 Lord of the Keep: a living castle you feel responsible for

Owner: *"i want something that makes the game feel alive and in action but not neccessarely in danger from moment 1
you are responsible now you are hooked you are caught"* (after *"it feels calm and empty"*).

## The loop

| Phase | Feeling | What happens |
|---|---|---|
| **Day** | busy, safe, purposeful | 3 duties from the **Day Ledger**; people around the keep ask for help; the keep gets better |
| **Dusk** | "night is coming, are we ready?" | the Ledger closes: done duties pay out, missed ones cost something small |
| **Night** | action (the siege we already have) | what you did by day decides how the night goes |
| **Dawn** | relief, attachment | the **Dawn Report**: who held, who fell, who arrived, what you earned |

## Step 1 (building now): the Day Ledger and the Dawn Report

A small scroll in the corner, in the same style as the new HUDs (TGA #359 / #361):

```
DAY 3 · THE LEDGER                              ☀ ▓▓▓▓▓░░ dusk
☐ Bring 2 survivors inside the walls        0/2   +150 gold
☑ Recruit 3 soldiers                        3/3   +1 skill point
☐ Earn 400 gold before dusk               220/400 +morale
```

- **3 duties each dawn,** picked from a pool that grows with the days. Day 1 is gentle and teaches the game: talk to
  Vesna, recruit a soldier, look at the cannon map.
- **Duties come from things the game already tracks** (no new systems needed for v1):

  | Duty | Tracked by |
  |---|---|
  | recruit N soldiers | soldier count |
  | take in N survivors | #11 survivors |
  | earn N gold | the HUD's gold |
  | buy / wear a piece | the Obsidian set / Vesna |
  | upgrade a wall or tower | #224 |
  | mount a new cannon | #283 |
  | find the old chest | #8 |
  | keep every soldier alive tonight | night duty: soldier count at dusk vs dawn |
- **Reward on completion:** a toast (#313), a coin sound, gold or a skill point. Missing a duty never kills you; it
  costs a little gold or morale. Hard but fair, like the owner likes.
- **Dawn Report** (a parchment card, about 6 s, skippable):

  ```
  DAWN OF DAY 4
  The walls held.                    Wave 7 survived
  Fallen: 2 soldiers                 Saved: 3 survivors
  New in the keep: 3 families        Gold earned: +620
  Ledger: 2 / 3 duties done
  ```

## Step 2: names and faces (the "caught" part)

- Every soldier and survivor gets a **name** (a medieval list: Aldric, Bertram, Wynn, Edda...) shown over them and in
  the barracks.
- The Dawn Report names them: *"Fallen: Aldric the archer (served 3 nights)."*
- People ask for things by name: *"Edda the medic needs herbs from the woods."*

## Step 3: a busy courtyard

The smith hammering at the forge (#186, TGA), Vesna at her stall, kids running, a priest at the shrine, carts arriving
from the mine (#201), the feast table on good days. They're stand-ins until the MetaHuman pass.

## Step 4: the hook at the start

A short opening: dawn, refugees at the gate, a wounded captain: *"The lord is dead. You're in charge now."* Then the
first Ledger opens.

## What I need from the editor (one read-only run)

BP_DayNight (how it marks day / night / time), BP_ZombieWaveManager (wave count). The rest is in exports I have.
