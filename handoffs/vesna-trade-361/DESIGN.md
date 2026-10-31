# #361 Vesna Trade v2: the Obsidian set inside the carousel (TGA, 2026-10-31)

**Status: design only, nothing built.** This is the same motion-graphics family as the #359 Muster: same research ([RESEARCH.md](../barracks-hud-359/RESEARCH.md)), parts and timings. Mock-up: `mock/mock.html` (`?f=1`, `?f=2`), frames `mock/frame1.png` and `mock/frame2.png`. The piece images are checkking's real Obsidian renders.

## Why the old one failed
The #221 set panel was drawn on the right edge by `BPC_ObsidianSet.DrawArmoury`, under the trade screen's Inventory window. Closing the Inventory closed the shop, so the owner never saw the set.

## Layout (one screen, nothing floating on top)
| Zone | What |
|---|---|
| Top | `VESNA'S TRADE` + **category tabs**: WEAPONS · ARMOUR · **OBSIDIAN SOVEREIGN** · SUPPLIES (LB / RB, Q / E, click) |
| Left | **3D turntable** of the selected item on the BP_TradeShowcase plinth. Swipe with A / D (the #319 swipe stays); turn it with a drag or the right stick |
| Left, below | **Item card**: name, SET x/11 badge, stats with green deltas, slot, what it replaces, price with the "set piece #n · next costs more" line (#96 curve), then **HOLD TO BUY** (0.6 s, as in #359) or **WEAR / TAKE OFF** when owned |
| Middle | **Carousel list** of the tab: icon disc, name, slot, state (price / OWNED / WORN / FORGING for pieces whose art isn't imported yet). W / S, wheel or click |
| Right | **THE HERO paper doll**, now part of the trade screen (not a separate window): 12 slots round a silhouette (head, shoulders L/R, torso, upper arms, forearms, hands, waist, off-hand, thighs, shins, feet). Below it: the **set bar** (11 segments, `x / 11 WORN`, the Sovereign's Ember bonus text) and the pack grid |
| Bottom | Gold and ore, and input hints for the active device |

## Obsidian tab rules
- Every piece is a normal carousel item, from the `BPC_ObsidianSet` data: `BuyPiece(Id)`, `SetPieceWorn(Id, Worn)`, `AvailMask`, the owned and worn masks, and the save. Nothing is copied.
- Pieces not in `AvailMask` (no mesh yet) show as **FORGING**, dimmed and not buyable. They become buyable when checkking's art is imported, with no UI change.
- Price comes from the #96 curve (`round50(450 * 1.45^n)`). Every unbought piece shows the same next price.
- **The Knight's Great Helm is removed from the store** (owner).

## Wearing (paper doll)
- **Drag** the piece from the pack or the carousel onto its slot. Matching slots pulse gold while dragging.
- Or **double-click** it, or press **Y** on the selected item.
- The previous piece (silver) drops into the pack. Plate and Obsidian stay exclusive per slot, as before.
- **Feedback:**
  - The slot flashes, and the set bar gains one segment with a gold flash.
  - At **11/11** the whole doll flares, the bar turns gold and reads **SOVEREIGN'S EMBER**, and `ObsSet` drives the hero aura (#96).

## Motion (same family as #359)
| Event | Motion |
|---|---|
| Open | Burn-in 300 ms, then the list cascades in 40 ms apart |
| Switch tab | The list slides 40 px and cross-fades, 220 ms |
| Swipe | The turntable eases to the next item with a 15° overshoot, 260 ms |
| Buy | Hold-fill, then the coin burst and the gold count-down; the bought piece flies into the pack cell (the existing fly-icon loop) |
| Can't afford | The button shakes, and the gold value pulses red |

## Remove when v2 works
- `BPC_ObsidianSet.DrawArmoury` and its `BP_ArmoryHUD` hook
- The separate Inventory window's close-the-shop path
- The Great Helm trade item

## #66 book / satchel reveal spin
It isn't in this mock-up. It needs a look at the live BP_SkillTreeHUD / showcase export to see why the 3D spin doesn't fire. I'll check that in the build pass and report it there.

## Decision for the owner
Approve this layout:
- Obsidian as a tab, with FORGING shown for pieces whose art isn't imported yet
- the paper doll as part of the trade screen
- hold to buy
- drag, double-click or Y to wear

Then TGA builds #359 and #361 together as one widget family (shared row, button, tab and alert widgets), as a DRY_RUN setup script plus pre-checked pastes.

## v3 (owner instructions 2026-10-31, 20:05): supersedes the layout above
Mock-up: `mock/mock2.html` (`?f=0` dialogue, `?f=1` shop) · `mock/v3_frame0.png`, `mock/v3_frame1.png`, `mock/side_by_side.jpg`.
- **Talk, then TRADE, then "SHOP!"**:
  - The dialogue plate (TALK / TRADE / LEAVE) uses the same kit.
  - TRADE stamps **SHOP!** on screen with a 400 ms gold flash, and it becomes the window title.
- **Three windows open together:**
  1. **INSPECT**: the spinning 3D item, now **smaller** (a 380 px box, so the render target is sharper), with info, price and HOLD TO BUY.
  2. **VESNA'S WARES** (new): a menu of everything she sells, in collapsible categories: WEAPONS, OBSIDIAN SOVEREIGN (with set progress), SUPPLIES. W / S browse, Q / E jump between categories.
  3. **THE HERO**: paper doll and pack, now with **13 slots including CAPE** (#362: back slot drawn behind the shoulders, folded-cloak icon; piece id 20, DEF +4). It shows FORGING until the cape art exists. The torn-cape wear (#256 / #258) will show as a frayed icon edge later.
- **One design system with #359** (owner): the same frames, Cinzel caps, bronze rules, blood-red selection, icon discs, hold-to-buy, burn-in open, cascading rows and alert family. Build plan: a shared kit first (`WBP_UI_Window`, `WBP_UI_Row`, `WBP_UI_HoldButton`, `WBP_UI_Tabs`, `WBP_Alert`), then the Muster and the Shop on top of it.
