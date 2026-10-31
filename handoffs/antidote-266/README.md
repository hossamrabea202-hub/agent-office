# #266 PRIORITY: the Antidote at Vesna (the missing step 5 of #148)

By `adjustedfilm (Claude)`, 2026-10-31. Paste-only for the Master. Built on the **2026-10-30b** export of
`BP_NoticeHUD_EventGraph.txt`, which already has #148's infection block (`InfIn` .. `InfOut`) and the #31 banner (`NoticeIn`).

**Decision:** laptop2 (owner of #148) has been offline for 24 h, so adjustedfilm built it. It isn't in Vesna's trade carousel
(BP_SkillTreeHUD, 22 MB, a full repaste can crash the editor). It's a small **APOTHECARY** panel of its own, like
WEAPONSMITH / OBSIDIAN ARMOURY, drawn by **BP_NoticeHUD**. NoticeHUD is the top HUD (child of BP_ArmoryHUD), so the panel
sits over the shop. No new variables, no BPVar lines, no self-calls. The panel calls the already-live
`Infection.BuyAntidote()` on the hero's component.

## What the player gets

- In Vesna's shop, **only while infected**, a panel under the STATS box:
  - antidote icon;
  - `Antidote` and `Cures the infection`;
  - the price: `FREE` the first time, then 1000, 1500, ... gold (BPC_Infection's `AntidotePrice`), red when you can't pay;
  - a **TAKE** / **BUY** button.
- Click the button: Gold -= price, then `BuyAntidote()` (already live). The hero is cured, the `CURED - the infection
  is gone` notice shows, the price goes up and the panel disappears.
- Hovering the button without the gold shows `Not enough gold, hunter.`

## Pre-checks (done)

| Check | Result |
|---|---|
| `fix_impure.py NoticeHUD_Antidote_graph.txt` | no changes (the cast is in the exec chain) |
| `applyall.py check NoticeHUD_Antidote_graph.txt` | 108 nodes, 186 links, **Validation OK** |
| `applyall.py merge --dry-run` on the 10-30b BP_NoticeHUD export with `manifest_noticehud_antidote.json` | 4 rewires linked, **Validation OK** |

## Steps (Master)

1. Run `py "<repo>/handoffs/antidote-266/import_antidote_icon_ue.py"`. It makes `/Game/CastleDefender/UI/T_Item_Antidote`
   from laptop2's antidote icon. Use `--dry-run` first if you want a report only.
2. Open **BP_NoticeHUD** → EventGraph, then paste `NoticeHUD_Antidote_graph.txt` (108 nodes) in an empty spot.
3. Make the 4 links by hand (or run `applyall.py merge` with `manifest_noticehud_antidote.json` on a fresh export):

   | # | From | To |
   |---|---|---|
   | 1 | `InfOut` **then 0** (now goes to `NoticeIn`) | **AntIn**.execute (replace the old link) |
   | 2 | **AntOut** then 0 | `NoticeIn`.execute |
   | 3 | Event Receive Draw HUD (`CX_1`) **Size X** | **AntSizeX**.In Int |
   | 4 | `CX_1` **Size Y** | **AntSizeY**.In Int |

4. Compile and save.
   - If the `Gold` get or set nodes show a warning, right-click → Refresh Node. They use the live `Gold` reference from this
     same graph.

## Tests (Play)

1. Get infected (zombies below 30 % HP, or editor Python `Infect` on the hero's `Infection` component, #148 test 8).
2. Talk to Vesna. The APOTHECARY panel shows under STATS with `FREE` and **TAKE**.
3. Click TAKE: the bar goes back to red, regen returns, the CURED banner shows, and the panel is gone.
4. Get infected again (more than 60 s later): the price is **1000 gold**. With less gold the price is red, and hovering
   BUY shows `Not enough gold, hunter.`; clicking does nothing. With 1000+ gold BUY cures and takes 1000.
5. When not infected, Vesna's shop shows no panel. Other shops show no panel.
6. Save while cured, then load: still cured, and the next price is still the raised one (the #148 save keeps `AntidotesBought`).

## One-minute tuning (Master may do it on the spot)

- Panel position: node `anMultiply_Doubl14` B = **0.44** (panel centre, fraction of screen width), and node
  `anMultiply_Doubl17` B = **600** (top, in 1080p pixels). Change them if the panel overlaps the shop art.
- If the shop's own click handler also reacts to the button click, move the panel lower (raise 600).

## Rules applied

- Office rules: card first (#266 claim), pre-checked paste, no editor work by me.
- INDUSTRY_SECRETS rule 0 doesn't apply much to a 2D HUD panel. I kept the shop's existing look: the same dark panel,
  gold title and cream text as WEAPONSMITH / ARMOURY. The thin green edge matches the infection bar's green, so the
  cure reads as "the green thing goes away".
