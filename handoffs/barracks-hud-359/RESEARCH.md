# #359 Barracks "Muster" HUD + one alert family: research and mock-up (TGA, 2026-10-31)

**Status: research and design only. Nothing is built yet.** The mock-up is `mock/mock.html` (open it in a browser with `?f=1..4`) and the storyboard is `mock/storyboard.jpg`.

## 1. What the 2025-26 references say

| Source | What we take |
|---|---|
| Univ. Bonn study of 30 GOTY nominees, 2014-2025 ([bonndoc](https://bonndoc.ulb.uni-bonn.de/xmlui/handle/20.500.11811/14207)) | HUDs are getting more minimal and contextual: show on change, hide when idle. So the shop lives at the NPC, not on the main HUD, and alerts collapse into small chips. |
| Frostpunk 2 console UI, Xbox Wire 2025-09 ([link](https://news.xbox.com/en-us/2025/09/18/adapting-frostpunk-2s-depth-to-a-gamepad/)) | One context menu shows only the relevant actions, menus **pause time automatically**, and bumpers cycle categories. Our version: E at the NPC slows time to 0.2, LB / RB switch tabs, and every row shows only what you can do there. |
| Hades II UI animator / illustrator postings ([Supergiant](https://supergiantgames.com/blog/job-opportunity-ui-animator-hades2)) | Premium studios treat menu motion as its own craft: illustrated, **layered, motion-ready** panels and designed transitions, not plain fades. Our version: a burn-in reveal and staggered rows, built as layered UMG with material-driven effects. |
| UMG lecture notes and Common UI docs ([Epic Common UI](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-advanced-multiplatform-user-interfaces-with-common-ui-for-unreal-engine)) | UI animations should run **150-400 ms**. Common UI routes the bumpers to the tab list and handles back and focus restore for gamepad. Common UI is the target if the project enables it; plain UMG focus navigation is the fallback (see 4). |
| Toast / alert UX guidance ([LogRocket](https://blog.logrocket.com/ux-design/toast-notifications), [Microsoft](https://learn.microsoft.com/cs-cz/windows/apps/design/shell/tiles-and-notifications/toast-ux-guidance)) | Use severity tiers with one frame family, show at most 3 stacked, keep text on screen 5 s or more, and never put must-act information in a toast. The infection box becomes a banner and then a persistent status chip. |
| Our own skill tree and Vesna trade screens (10-28 shots) | The house look is charcoal iron, bronze filigree rules, Cinzel-style capitals, ringed icon discs, a blood-red selected state and cream text. The Muster uses the same parts, so it reads as one game. |

## 2. The 5 ideas we take

1. **Diegetic entry.** At the NPC, press E: time dilation 0.2, world blur and desaturate (a post-process weight lerp over 250 ms), and the camera eases 15 % towards her. Her voice line types on in a speech plate.
2. **Ember burn-in.** The panel appears through a radial ember-dissolve material (`M_UI_Burn`, param `Reveal` 0 → 1 over 300 ms, reusing the #140 HUD reveal textures). Rows then **cascade** in 40 ms apart, each 220 ms with an ease-out-cubic slide of 40 px. The detail pane follows at 160 ms.
3. **Hold to buy.** Hold A / E for 0.6 s; a red fill runs through the button, so a stray press never spends 900 gold. On release:
   - a coin burst (14 sprites, 350 ms);
   - the gold counter **counts** to the new value over 400 ms;
   - the level pip fills with a flash;
   - she says a short confirmation line.
   - If you can't afford it, the button shakes (3 × 6 px, 180 ms) and the missing resource pulses red.
4. **Every row explains itself.** Each row has an icon disc, name, one-line effect, level pips, gold plus ore price, and owned / level / **lock reason** ("Needs Walls II", "Needs a cannon"). The detail pane shows the stat delta (x1.75 → x2.5) in green.
5. **One alert family** (replaces the grey "Click to continue" box). All alerts share one frame, with severity set by colour and motion:
   - **Notice** (bronze): slides in 180 ms, holds 4 s, fades.
   - **Warning** (amber): adds one pulse.
   - **Affliction** (blood; BITTEN, INFECTED, TURNING): a blood-vein vignette beats twice like a heartbeat, the banner slides in, and the drain bar runs 5 s. It then **shrinks into a status chip** beside the health bar with the cure timer ("INFECTED · 2:41"), and the chip beats faster as time runs out.
   - **Relief** (green; CURED): the same frame, with a soft bloom.
   - The game never stops. The long explainer text moves to a one-time codex page you can open from the chip (Tab / View).

**Accessibility.** A "Reduced UI motion" option disables the burn, shake and vignette pulse; text-size scaling applies; colour is never the only signal (each tier has its own icon).

## 3. The tabs (everything the owner listed)

| Tab | Rows | Calls existing logic (no copies) |
|---|---|---|
| RECRUIT | Swordsman, Crossbowman, Field Medic (#185), Mechanic (#50), Commander (commander-kit) | the recruit queue (#188) |
| ARTILLERY | Field Cannon (deploy convoy), and later cannon upgrades | `BP_CannonOrder` (#239 / #285; replaces key O) |
| FORTIFY | Stone Walls I-III, Iron Gate Bands, Tower Ballistas | `BPC_CastleUpgrades` (#282; replaces J / K), forge gate bands (#208) |
| SUPPLIES | Crossbow Flares, Antidote crate (#266) | `BPC_Flares` (#278; replaces F) |

Once the panel works, the old one-time key notices (J / K / F / O) go.

## 4. Build plan (next, after the owner says yes to this look)

- **Widgets:**
  - `WBP_Muster`: root, tabs, list, detail, resources and hints.
  - `WBP_MusterRow`: one row, data-driven from a struct `S_MusterItem` (Id, Tab, Icon, Name, Desc, Gold, OreType, OreAmount, MaxLevel, RequiresId, LockText).
  - `WBP_Alert` + `WBP_AlertChip`: the alert family. `BP_NoticeHUD.PushNotice(Text, Tier)` keeps its signature, with tiers 0 notice, 1 warning, 2 affliction and 3 relief. The infection BPs only change their tier numbers.
- **Data:** one DataTable `DT_Muster` holds all rows, so prices and new items are table edits, not graph edits.
- **Calls:** the HUD reads the owned level and affordability from the existing components and calls their buy events.
- **Input:** gamepad, mouse and keyboard:
  - LB / RB or Q / E switch tabs;
  - D-pad / stick / mouse move the selection;
  - A / E or left-click held = buy;
  - B / Esc = back.
  - Time dilation follows the skill tree's pause (#213 rules).
- **Delivery:** the usual office path. A DRY_RUN setup script creates the widgets, struct, DataTable and materials. Graph pastes are pre-checked with fix_impure and the applyall dry-run, with a test list. The burn and vein materials and the icon set are mine (icons drawn to match the skill-tree discs).

**Decision needed (owner):**
- Approve this look and the 5 ideas: the burn-in, the hold-to-buy, the one alert family with the chip, the NPC name "Quartermaster", and slowing time to 0.2 rather than a full pause.
- Then TGA builds the hand-off.
