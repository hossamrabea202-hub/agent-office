# #73 Infection: Blueprint pastes

By `hossam gmail laptop2 (Claude)`, 2026-10-29. Design: `../PLAN.md`. Built against the 10-28 exports in
`exports/laptop2/gameplay/` (hero, BP_ZombieHUD) and `exports/laptop2/prompt68/` (BP_NoticeHUD, BP_SkillTreeHUD).
`gen73.py` writes the 3 paste files with the Master's node kit (`tools/master/t81/kit.py`), the same way as #96.
The wiring check found 0 problems on all 3. **Not compiled yet**: that needs the editor.

| File | Goes into | Nodes |
|---|---|---|
| `BPC_Infection_graph.txt` | the new component's EventGraph | 154 |
| `Hero_Infection_graph.txt` | BP_ThirdPersonCharacter EventGraph | 8 |
| `NoticeHUD_Infection_graph.txt` | BP_NoticeHUD EventGraph | 150 |

**Decision:** all infection state lives in **one new component on the hero**, `BPC_Infection` (named `Infection`), in
the #96 style. PLAN.md put the 5 variables on the hero itself; the component keeps them together and out of the big
graphs. The hero gets 2 small hooks, BP_NoticeHUD gets 1 draw block, and BP_ZombieHUD and BP_SkillTreeHUD get nothing
pasted.

## What the component does

- **Bite:** it listens to the hero's OnTakeAnyDamage, which fires right after ReceiveAnyDamage has added the damage.
  The hero gets infected when all of these are true:
  - not infected already
  - the damage causer has the actor tag `Infects` (BP_Zombie passes itself as the causer)
  - HP is below 30 % (`MaxHP - DamageTaken < 0.30 x MaxHP`, MaxHP = 100 as in the hero and the HUD)
  - the hero is alive
  - at least 60 s since the last cure

  Falls and cannon blasts have no tagged causer, so they never infect.
- **Infect():** sets `Infected` and `InfectedAt`, then calls `PushNotice("YOU ARE INFECTED", 1)`. The first time only,
  it pauses the game and opens explainer card 1 (`ExplainCard = 1`).
- **Drain** (component Tick): while infected, every 2 s of game time it adds `0.01 x MaxHP` to DamageTaken. It never
  goes past `0.95 x MaxHP`, so the drain can't kill. It stops while the game is paused.
- **NextCard():** the HUD calls this on a click. After card 3 the cards close and the game unpauses.
- **BuyAntidote():** adds 1 to `AntidotesBought`, sets `Infected = false` and `CuredAt = now`, then calls
  `PushNotice("CURED - the infection is gone", 0)`.
- **`AntidotePrice`** is for the HUD: 0 (FREE) for the first antidote, then 1000, 1500, 2000 …
- **Save/load:** the component has its own slot, **`CastleSaveInfection`** (class BP_CastleSave, `Data` =
  `[1, Infected, AntidotesBought, InfectSeen]`). The same trigger as the armoury save fires it: `MPC_Controls.SaveT`
  changes, and `SaveKind > 1.5` means load. **Decision:** it gets its own slot because the armoury code rewrites all of
  `CastleSaveArmory`'s Data every save, so there'd be a race.
  - On load: `InfectedAt = now`, so the drain clock restarts. `CuredAt = -100`, and the explainer never replays.
  - With no save file, a load resets to not infected.
- **Tuning** (Class Defaults on BPC_Infection): MaxHP 100, InfectBelow 0.30, ReinfectGuard 60, DefMul 0.666667,
  DrainEvery 2, DrainPct 0.01, DrainCap 0.95.

## Steps (editor driver)

1. **Create:** run `py ".../handoffs/infection-73/bp/create_bpc_infection.py"`. It does three things:
   - makes `/Game/CastleDefender/Gameplay/Castle/BPC_Infection` with 18 variables and their defaults (the `VARS` table
     in the script)
   - adds it to BP_ThirdPersonCharacter as **`Infection`**
   - adds the actor tag **`Infects`** to BP_Zombie's Class Defaults

   If the log says **BY HAND**, add that variable or default yourself from `VARS`. `real` is a double, and `CardMID`
   is a Material Instance Dynamic reference.
2. **Component graph:** open BPC_Infection's EventGraph, paste `BPC_Infection_graph.txt`, then compile and save. It
   needs `PushNotice` on BP_NoticeHUD (the #31 paste) to exist first, or the 2 PushNotice calls won't compile.
3. **Hero graph** (BP_ThirdPersonCharacter): paste `Hero_Infection_graph.txt`, then make 4 rewires (the names are from
   the export):
   - **Damage** (Event AnyDamage):
     - #121's **ObsDmg**.ReturnValue -> **InfDmg**.A. If #121 isn't in yet, use `Multiply` K2Node_CallFunction_19 instead.
     - **InfDmg**.ReturnValue -> `DamageTaken + …` K2Node_CallFunction_PH4 .B (it used to come from ObsDmg).

     Result: `Damage x (1 - Gear.R x 0.25) x (1 - Armor.R x 0.35) x (1 - ObsSet.R x 0.15) x Block x (Infected ? 2/3 : 1)`.
   - **Regen** (Event Tick: `DamageTaken - Delta x 2.5`):
     - Branch (IsDead) K2Node_IfThenElse_ZX12 .else -> **RegenGate**.execute.
     - **RegenGate**.else -> Set DamageTaken K2Node_VariableSet_ZX17 .execute. RegenGate.then stays empty: no regen
       while infected.

   Then compile and save.
4. **BP_NoticeHUD:** paste `NoticeHUD_Infection_graph.txt` into the EventGraph, then make 4 rewires:

   | # | From | To |
   |---|---|---|
   | 1 | `DrawText (GAME SAVED)` CX_208 .then **and** Branch CX_138 .else (they go to #31's NoticeIn now) | **InfIn**.execute |
   | 2 | **InfOut**.then_0 | #31's **NoticeIn**.execute, so the banner draws on top. Leave it empty if #31 isn't pasted |
   | 3 | Event ReceiveDrawHUD CX_1 .SizeX | **InfSizeX**.InInt |
   | 4 | CX_1 .SizeY | **InfSizeY**.InInt |

   Then compile and save. It draws three things:
   - **While infected:**
     - a green `(0.25, 0.85, 0.30)` fill over the hero bar, at BP_ZombieHUD's own H23..H25 geometry
     - the bar frame redrawn on top, plus an additive green glow on the frame that pulses 0.5..1.0 at 1 Hz
     - `YOU HAVE BEEN INFECTED` above the bar (Cinzel, 20 px x S, green; 0.25 s fade-in, then breathing 0.75..1.0 at
       0.6 Hz), with `Antidote: Vesna (castle)` under it (14 px x S)
   - **Explainer cards** (game paused):
     - the screen dimmed to 55 %
     - an M_HintCard (#66) card at 900 x 300 px x S, with `Age` = real time since that card opened
     - the title (gold, 34 px), the body (20 px) and `Click to continue` (15 px)
     - a click, Space or Enter goes to the next card (ignored for the first 0.6 s). If M_HintCard is missing, a plain
       dark panel is drawn instead.
5. **Vesna's trade carousel** (BP_SkillTreeHUD, spec only, not pasted): add an **Antidote** entry in the same pattern as
   the other items (`trade_hud_4items.py`: nested Selects on the item index, wrap at `NIT`, a BUY chain per item).
   - **Read:** Get Player Character -> Cast to BP_ThirdPersonCharacter -> `Infection`.
   - **Shown only while `Infected`:** make it the **last** index, with `NIT = base count + (Infected ? 1 : 0)`. That
     way the wrap hides it when the hero is healthy.

   | | |
   |---|---|
   | Name | **Antidote** |
   | Price label | `FREE` when `AntidotePrice == 0`, otherwise the number |
   | Stats lines | `CURES INFECTION` · `rare: price rises each time` |
   | BUY | `Gold >= AntidotePrice` -> `Gold -= AntidotePrice` -> `Infection.BuyAntidote()`. Otherwise the existing "not enough gold" line |
   | Pack | none: it's used on the spot, no pack cell and no fly-to-pack |
   | Icon | **`T_Item_Antidote` doesn't exist yet**: it needs a 512 px icon in the T_Item_ framing (green glass vial) |

   The same frame the BUY runs, the bar goes red and regen comes back, because the hero hook and the HUD both read
   `Infected`.
6. **Other biters:** the colossus and tentacle weren't in the exports. If they damage the hero, pass `self` as
   DamageCauser and give them the `Infects` tag too.

## Checks (Play)

1. Let zombies hit the hero below 30 %:
   - the bar turns green and pulses
   - the banner and the above-bar notice fade in
   - the game pauses on card 1/3; click through all 3 cards and the game resumes
   - next time (same save), no cards
2. Wait: HP drops about 1 % every 2 s and stops at 5 %. A zombie hit at 5 % can still kill.
3. Hits while infected do about 2/3 of the damage. `Infection.DefMul` is the factor.
4. Vesna: the antidote shows `FREE`. Buying it cures: the bar goes red, regen comes back, and the CURED banner shows.
   The next infection costs 1000, then 1500.
5. Drop below 30 % again within 60 s of a cure: no infection.
6. A fall or cannon damage below 30 % doesn't infect.
7. Save while infected, then load: still infected, the drain restarts, no cards.
8. Editor Python, quick test: `hero.get_component_by_class(<BPC_Infection class>).call_method('Infect')` infects at
   once.

## Verify in the editor (I couldn't confirm these from the exports)

- **The regen isn't where PLAN.md says.** The 10-28 hero export regenerates on its own **Event Tick**
  (2.5 HP/s, ZX10..ZX17), not after `LastHitAt` in BP_ZombieHUD, so the gate goes there.
- **BP_ZombieHUD also scales every DamageTaken increase** (IW2189..IW2202: `prev + (new - prev) x 100/(100+a) x
  100/(100+b)`, the skill-tree DEF). This means two things:
  - the drain is also cut by the player's DEF stats, so it's a little under 1 % per 2 s
  - the bite check sees the HP before that cut, so it can infect at a little over 30 %
- **The hero bar has no MakeColor.** The fill is the material `M_HPLiquid`, so "green" is a tinted `T_HP_Fill`
  (alpha 0.82) drawn over it, with the frame redrawn on top. If M_HPLiquid has a colour parameter, a MID would look
  better. The text position above the bar (frame top - 6 px x S) wasn't checked against other HUD art there.
- **Delegate order:** the bite check relies on UE calling ReceiveAnyDamage before OnTakeAnyDamage.Broadcast, so
  DamageTaken is already updated. That's the engine order in AActor::TakeDamage.
- **Pausing:** the component pauses the game itself. In the export, BP_ZombieHUD's pause and menu logic leaves a pause
  with `ShopV.X == 0` alone. Check that Esc or P during a card doesn't open another menu on top.
- **Assets and paths I couldn't open:**
  - `M_HintCard` at `/Game/CastleDefender/UI/Hints/` (from `make_M_HintCard.py`; it may not have been built)
  - `BP_CastleSave` at `/Game/CastleDefender/Gameplay/Save/`, with `Data` as a double array (from the BP_ArmoryHUD
    export)
  - BP_NoticeHUD's `PushNotice(Text: string, Tier: int)` from the #31 paste; the component casts the player's HUD to
    BP_NoticeHUD
- **Pin layouts the exports didn't have:**
  - the component's `ReceiveTick` and `CreateDynamicMaterialInstance` (copied from #31)
  - `GetHUD` (found in another export)

  If one comes in broken, right-click -> Refresh Node.
