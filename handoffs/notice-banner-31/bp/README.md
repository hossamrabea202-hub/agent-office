# #31 notice banner + #68 Vesna prompt fade: Blueprint pastes

By `hossam gmail laptop2 (Claude)`, 2026-10-29. Built against the 10-28 exports:
- BP_NoticeHUD from `exports/laptop2/prompt68/`
- BP_ZombieHUD from `exports/laptop2/set96/`, the newer one

`gen31_68.py` generates both pastes with the Master's node kit (`tools/master/t81/kit.py`). The wiring check found
0 problems. **Not compiled yet.** Designs: `../DESIGN.md` (#31) and `../../prompt-fade-68/DESIGN.md` (#68).
M_NoticeBanner must exist; it was installed with #112.

## 1. Variables

Run `py ".../handoffs/notice-banner-31/bp/add_vars_31_68.py"`. It adds 4 variables to BP_ZombieHUD and 9 to
BP_NoticeHUD. If the log says **ADD BY HAND**, make that variable yourself. Types: `real` is a double,
`NoticeMID` is a Material Instance Dynamic reference.

## 2. #68 Vesna prompt (BP_ZombieHUD, 40 nodes)

The prompt's art already had a placeholder for this: every colour's alpha comes from `CX_450 = 1 x 1.0`.

Paste `ZombieHUD_VesnaFade_graph.txt` next to the Vesna prompt (`[E]  Speak with Vesna`, around
`K2Node_IfThenElse_IW2166`), then make 5 rewires:

| # | From | To |
|---|---|---|
| 1 | `GetActorOfClass (BP_NPC_Elder)` IW2161 .then | **FadeIn**.execute (it used to go to Branch IW2166) |
| 2 | **FadeOut**.then_0 | Branch IW2166 .execute |
| 3 | `AND` IW2165 .ReturnValue (near and valid) | **VesnaVisIn**.A, and then **VesnaDraw**.ReturnValue -> Branch IW2166 .Condition |
| 4 | **VesnaAlpha**.ReturnValue | `Multiply` CX_450 .B (the 1.0) |
| 5 | `WasInputKeyJustPressed (E)` IW2177 .ReturnValue | **VesnaPressIn**.A, and then **VesnaPressOK**.ReturnValue -> Branch IW2178 .Condition |

- The prompt keeps drawing while it fades out. Rewire 5 makes sure **E only opens the shop while you're really in
  range**, not during the fade-out.
- Real time drives it, so it doesn't freeze when the shop pauses the game.

**Decision:** Vesna first. The cannon prompts get the same block once you like the look:
- `[E] Mount Cannon` is drawn inside a loop over the cannons, so it needs one "any cannon in range" flag first.
- `Leave cannon` is a single branch.
- The Commander prompts are in BP_BarracksHUD.

## 3. #31 notice banner (BP_NoticeHUD, 156 nodes)

Paste `NoticeHUD_Banner_graph.txt` into BP_NoticeHUD's EventGraph, then make 3 rewires:

| # | From | To |
|---|---|---|
| 1 | `DrawText (GAME SAVED)` CX_208 .then **and** Branch CX_138 .else (the two ends of DrawHUD) | **NoticeIn**.execute |
| 2 | Event ReceiveDrawHUD CX_1 .SizeX | **NoticeSizeX**.InInt |
| 3 | CX_1 .SizeY | **NoticeSizeY**.InInt |

### What it does

- **`PushNotice(Text, Tier)`** is a custom event on BP_NoticeHUD that any Blueprint can call: Get Player Controller
  -> Get HUD -> Cast to BP_CommanderHUD -> PushNotice. Tier is 1 for important, 0 for normal.
- **Decision:** the queue is one string with a line per message, so no array nodes are needed.
  - The same text twice is dropped. If that text is showing, its hold restarts instead.
  - Important messages go to the front.
  - The `(x2)` counter from DESIGN.md is left out: duplicates are simply merged.
- **Banner:** M_NoticeBanner (through a material instance) is drawn top centre at 11 % down the screen, 64 px x S
  high (S = screen height / 1080).
  - Width = text width + 112 px x S, kept between 420 and 1100 px x S.
  - Cinzel text sits on top with a 1 px dark shadow: warm white, or gold when important.
  - The text height is fixed at 24 px x S by measuring the font, so the font's own size doesn't matter.
- **Timing:** roll out 0.35 s, text in, hold 4 s (7 s for important, + 0.04 s per character past 60), text out,
  roll in 0.3 s, fade. Then a 0.15 s gap before the next message.
- **Paused** (skill tree, trade, map): the banner is hidden and its clock stops, then it carries on after.

### Move the old texts onto it (one call each)

Call `PushNotice` from each of these:
- `The Commander has fallen. …` (BP_CommanderHUD, Tier 1).
- `A new recruit awaits` (BP_BarracksHUD, 0).
- `WAVE N`, level up, gold rewards, `not enough gold` (BP_ZombieHUD, 0).
- Infection #73 and `SOVEREIGN'S EMBER` #96 (Tier 1).

Delete each old Draw Text once its PushNotice works. GAME SAVED can stay as it is.

## Checks (Play)

1. **Vesna:** walk up and the prompt fades in over about 1/4 s, then breathes (never below 75 %). Walk away and it
   fades out. Pressing E while it's fading out does nothing.
2. **Banner:** from the editor Python, `hud.call_method('PushNotice', args=('A new recruit awaits', 0))` (hud = the
   player's HUD). Then push 3 at once, one of them Tier 1: the important one shows first, and they never overlap.
3. **Duplicates:** the same text 3 times fast shows once.
4. **Pause:** open the skill tree while a banner shows. It hides, then finishes after you close it.
5. **Size:** at 1080p and 1440p the banner and text scale together.
