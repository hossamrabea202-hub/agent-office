# #31 Notification box: a rolled-out banner + one message queue

Seat: `hossam gmail laptop2 (Claude)` · card #31. Material script ready (`make_M_NoticeBanner.py`, preview
`preview_banner.png`: rolled up / opening / open / important). The queue lives in `BP_NoticeHUD` (top HUD layer,
export in `handoffs/exports/laptop2/prompt68/BP_NoticeHUD.t3d`). The paste builds on that export.

## Look

- Top centre, 11 % down the screen. Height `64 * S`, where `S = ViewportHeight / 1080` (1440p -> 85 px).
- Width = text width + 2 x 56 px, clamped to 420..1100 px (x S).
- `M_NoticeBanner` behind the text: blackened-steel plate, gold trim lines, a gold rod at each end.
  `Tier 1` (important) turns the plate deep red with brighter gold.
- Text: `Font_Cinzel` (the HUD's font), 24 px x S, warm white `(0.95, 0.88, 0.76)` (the colour BP_NoticeHUD already
  uses), with a 1 px dark shadow. Important: gold `(1.0, 0.80, 0.35)`.

## Timing per message

| Phase | Time | What moves |
|---|---|---|
| Roll out | 0.35 s | `Roll` 0 -> 1 (ease-out), `Fade` 0 -> 1 in the first 0.1 s |
| Text in | 0.15 s | text alpha 0 -> 1, starting 0.25 s in |
| Hold | 4 s (important 7 s), +0.04 s per character past 60 | |
| Text out | 0.15 s | text alpha 1 -> 0 |
| Roll in | 0.30 s | `Roll` 1 -> 0 (ease-in), then `Fade` 1 -> 0 over 0.1 s |

Total for a normal message: about 4.9 s.

## One place for every system to push messages

`BP_NoticeHUD.PushNotice(Text: String, Tier: int)`. Any Blueprint calls it with
`Get Player Controller -> Get HUD -> Cast to BP_CommanderHUD` (the game HUD, the child of the whole chain, so the
cast reaches BP_NoticeHUD's function).

- **Queue:** an array of `{Text, Tier}`, at most 6. Full: drop the oldest normal message (an important one is never
  dropped).
- **Duplicates:** if the same text is already showing or queued, don't add it again. Add ` (x2)`, ` (x3)` … to the
  queued one and restart its hold if it's showing.
- **Important jumps the queue:** it goes in front of every normal message, not in front of another important one.
- **One at a time.** The next message starts when the previous one has fully rolled in, plus a 0.15 s gap.
- **Pause / menus:** the timer uses real time (`Get Real Time Seconds`) so messages don't freeze when the game pauses
  for a menu, but they're hidden while the skill tree, trade or map screen is open (and resume after).

## What moves into it

Replace these plain-text draws with a `PushNotice` call (the 10-27 exports show the old ones in BP_ZombieHUD,
8 draws with the default engine font, and BP_CommanderHUD / BP_BarracksHUD):

| Message | From | Tier |
|---|---|---|
| `The Commander has fallen. N soldiers return to post with +X battle XP. Awaiting orders.` | BP_CommanderHUD | 1 |
| `A new recruit awaits` | BP_BarracksHUD | 0 |
| `WAVE N` / `GAME SAVED` (they overlapped before, #71) | BP_ZombieHUD | 0 |
| Level up, gold rewards, "not enough gold" | BP_ZombieHUD / trade | 0 |
| Infection (#73), set complete `SOVEREIGN'S EMBER` (#96) | new | 1 |

Prompts (`[E] Speak with Vesna` etc.) are **not** notices; they keep #68's own look.

## Checks (Play)

1. Commander death: a red banner rolls out with the message, holds ~7 s and rolls back.
2. Recruit + wave start at the same time: they show one after the other, never overlapping.
3. The same message 3 times fast: it shows once, with `(x3)`.
4. 1080p and 1440p: the text is crisp and the banner scales with it.
5. Open the skill tree while a banner shows: it hides, then comes back after.
