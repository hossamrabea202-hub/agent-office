# #73 Infection: implementation plan

Seat: `hossam gmail laptop2 (Claude)` (owner reassigned from adjustedfilm, 2026-10-28). Rules and numbers are the
card's plus the vice master's Decision on it. This is the build plan for the editor driver; the graph paste waits on
fresh exports (request on the card).

## What exists (from the 10-27 exports in `handoffs/exports/checkking/`)

- Hero HP = `MaxHP - DamageTaken` on `BP_ThirdPersonCharacter`. Damage comes in through `ReceiveAnyDamage` (it adds
  to `DamageTaken`, and the armour terms (Gear.R, Obsidian) scale it there).
- Regen and the hero health bar live in `BP_ZombieHUD` (the 19 MB parent HUD): it sets the hero's `DamageTaken` back
  down after `LastHitAt`, and draws the bar.
- Notices: `BP_NoticeHUD` (top layer, runs every frame), with the #68 fade/breathing look.
- First-time explainers: #66 pickup-reveal style (`handoffs/pickup-reveals-66/DESIGN.md`, `M_HintCard`).
- Vesna's trade carousel: `BP_SkillTreeHUD` (only the trade functions, never the whole graph).

## New state (on BP_ThirdPersonCharacter, all saved)

| Variable | Type | Meaning |
|---|---|---|
| `Infected` | bool | infected now |
| `InfectedAt` | float | game time of infection (drives the drain tick and the notice) |
| `CuredAt` | float | game time of the last cure (-100 at start), for the 60 s re-infection guard |
| `AntidotesBought` | int | 0 = the next one is free; price = 1000 + 500 * (AntidotesBought - 1) after that |
| `InfectSeen` | bool | the first-time explainer has played |

## Logic

1. **Trigger, in `ReceiveAnyDamage` after DamageTaken is added:**
   `if !Infected && DamageCauser is BP_Zombie / colossus / tentacle (cast or tag "Infects") && HP < 0.30 * MaxHP && Now - CuredAt >= 60`
   -> `Infected = true; InfectedAt = Now`. If `!InfectSeen`: open the explainer and set `InfectSeen = true`.
   Use an actor tag `Infects` on the three enemy BPs so one check covers them all.
2. **Defence +50 %:** in the same `ReceiveAnyDamage` multiply: `dmg = dmg * (Infected ? 1/1.5 : 1)`. (+50 % DEF read
   as "takes 2/3 damage". Decision: apply it after the armour terms, so it stacks with Obsidian and Berserk.)
3. **Regen off + drain, in the HUD's regen block:** when `Infected`, skip the regen branch and instead, every 2 s
   (`floor((Now - InfectedAt) / 2)` changed since the last frame), add `0.01 * MaxHP` to `DamageTaken`, but never past
   `0.95 * MaxHP` (the drain can't kill; zombies still can).
4. **Health bar green:** the bar's `MakeColor` switches to green `(0.25, 0.85, 0.30)` while `Infected`; a thin pulsing
   green border around the bar (alpha 0.5-1.0 at 1 Hz).
5. **Notice:** `YOU HAVE BEEN INFECTED` above the bar in `BP_NoticeHUD`, with the #68 shared look (0.25 s fade-in,
   0.75-1.0 breathing at 0.6 Hz), green text, while `Infected`. One line under it: `Antidote: Vesna (castle)`.
6. **First-time explainer (once per save):** game paused, 3 cards in the #66 style:
   1. "BITTEN" - "Below 30 % health a zombie bite infects you."
   2. "INFECTED" - "Defence +50 %, but your health drains and won't regenerate."
   3. "THE CURE" - "Vesna in the castle brews the antidote. Your first one is free."
   `[Click to continue]` on each, then resume.
7. **Cure at Vesna:** a trade item `Antidote` shown only while `Infected`. Price `0` (label `FREE`) when
   `AntidotesBought == 0`, else `1000 + 500 * (AntidotesBought - 1)`. BUY: check gold, take it,
   `AntidotesBought++`, `Infected = false`, `CuredAt = Now`. The bar goes red and regen comes back the same frame.
   Stats lines: `CURES INFECTION`, `rare: price rises each time`.
8. **Save/load:** the five variables go in the armoury save slot (CastleSaveArmory). On load with `Infected`, set
   `InfectedAt = Now` (the drain clock restarts; don't replay the explainer).

## Checks (Play)

1. Let zombies hit the hero to below 30 %: the bar turns green, the notice fades in, and the explainer plays (first time only).
2. Wait: HP drops 1 % every 2 s and stops at 5 %. A zombie hit at 5 % can still kill.
3. Damage taken while infected is about 2/3 of normal.
4. Vesna: the antidote shows `FREE`, buying it cures (bar red, regen back). Next infection: 1000, then 1500.
5. Right after a cure, dropping below 30 % again within 60 s doesn't infect.
6. A fall or cannon blast below 30 % doesn't infect.
7. Save infected, load: still infected, no explainer replay.

## Exports needed (fresh)

`BP_ThirdPersonCharacter` (ReceiveAnyDamage), `BP_ZombieHUD` (only the hero HP regen + health bar block),
`BP_NoticeHUD`, `BP_SkillTreeHUD` (trade functions), the armoury save function(s).
