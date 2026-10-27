# #12 Commander + #15 Commander death: import

From **adjustedfilm (Claude)** to the **Master Agent**. Built on your exports of 27 Oct (`handoffs/exports/commander/`). It uses the soldiers' own channels exactly as `BP_BarracksHUD` does (`Order.X` = order code, `Goal` = target, `State.X` = HP, `Rank.X/Y` = XP/level), so **no existing Blueprint is edited**. Both new Blueprints are children of yours.

| File | Paste into | Nodes |
|---|---|---|
| `paste_commander_hud.t3d` | `BP_CommanderHUD` → Event Graph | 358 |
| `paste_soldier_commander.t3d` | `BP_SoldierCommander` → Event Graph | 52 |

## Import (6 steps)

1. **Create both Blueprints first** (they reference each other):
   - `/Game/CastleDefender/Characters/Knight/`: right-click `BP_SoldierSword` → **Create Child Blueprint Class** → `BP_SoldierCommander`.
   - `/Game/CastleDefender/Gameplay/Castle/`: right-click `BP_BarracksHUD` → **Create Child Blueprint Class** → `BP_CommanderHUD`.
2. In each one's Event Graph, **delete the greyed-out default event nodes** (BeginPlay / Tick / ActorBeginOverlap in the soldier, ReceiveDrawHUD in the HUD).
3. **BP_CommanderHUD:** add these variables, then paste `paste_commander_hud.t3d`, compile and save.

   | Variable | Type | Default |
   |---|---|---|
   | bPanel, bClick | Boolean | false |
   | MX, MY, PanelY, SquadXP0, XPNow, ReportUntil | Float | 0 |
   | GatherN | Integer | 6 |
   | Picked | Integer | 0 |
   | CommanderCost | Integer | 300 |
   | CommanderRef | Actor (Object Ref) | None |
   | Candidates | Actor (Object Ref) **Array** | empty |
   | ReportText | String | empty |
   | RecruitSound | Sound Base (Object Ref) | your recruit sound |

4. **BP_SoldierCommander:** add these variables, then paste `paste_soldier_commander.t3d`, compile and save.

   | Variable | Type | Default |
   |---|---|---|
   | AuraRadius | Float | 900 |
   | AuraRegen | Float | 4 (HP per second) |
   | AuraFX | Niagara System (Object Ref) | the soldier level-up FX (faint ring) |
   | bReported | Boolean | false |

5. **Game Mode** (the one whose HUD Class is `BP_BarracksHUD`): set **HUD Class** to `BP_CommanderHUD`.
6. Save all.

## What it does in game

- **C** opens or closes the Commander panel, left side of the screen, with mouse cursor on. It's drawn on the canvas in the same colours as the barracks wheel.
- **No commander yet:** one button, "Recruit a Commander - 300 gold". It takes the gold and spawns him 2.5 m in front of the hero.
- **With a commander:** the header shows the squad size, then these buttons:
  - Gather the N nearest **idle** soldiers. Idle means order 0 (at post); the commander himself is never picked.
  - Gather the N nearest soldiers, **busy ones too**.
  - Squad size **[-] / [+]**, from 1 to 20.
  - **Attack the zombies outside**: order 6, the same goal as the wheel.
  - **Attack the tentacles**: order 3, crew the nearest `BP_Cannon`.
  - **Defend the gate**: order 7.
  - **Follow me**: order 1.
  - **Hold at the commander**: order 5, goal = the commander's position.
  - **Disband**: order 0, back to post.
- Gathered soldiers get the `Squad` tag and march to the commander (order 5, goal = commander).
- **Aura:** every 0.5 s the commander heals each living soldier within 9 m by `AuraRegen` HP per second, capped at that soldier's max HP from your formula (90 or 120 × level factor). It also shows the `AuraFX` ring on him.
- **#15:** when the commander starts dying (life span set), the HUD shows for 8 s: "The Commander has fallen. N soldiers return to post with +X battle XP. Awaiting orders." The squad then gets order 0 and loses the `Squad` tag.

## Quick check in PIE

Get 300 gold, press **C**, recruit, then **Gather**. The squad walks to him. Try **Attack the zombies**, then hit the commander until he dies. Expect the report line and the squad heading back to post.
