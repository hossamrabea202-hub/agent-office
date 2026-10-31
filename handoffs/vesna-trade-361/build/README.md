# Vesna's Trade, the owner's final look (#361): paste hand-off

By TGA (Claude), 2026-10-31. This builds the screen in `../owner_target.png`, which the owner picked at 22:14 ("we will use this one instead").
- **Check image:** `../renders/vt_side_by_side.jpg` (the owner's target on the left, this build's mock-up on the right). The mock-up uses the same layout numbers and textures the game draws.
- **Graph checks:** the component graph has 1,416 nodes and 2,510 links. `applyall check` gives **Validation: OK**.
- **Hook merge dry-run** on `exports/master/2026-10-30b`: **Validation: OK** in three cases:
  - the #222 hook not merged yet;
  - the #222 hook already merged;
  - the merge run twice (the second run adds nothing).
- **Not compiled yet:** that needs the editor.

## What the player gets
- **Layout:** the same as the target.
  - **Top:** Vesna portrait top-left, gold / iron / silver top-right, and the tabs WEAPONS · ARMOUR · SETS · SUPPLIES (LB / RB / Tab, or click).
  - **Left:** the Sovereign set list (11 pieces, 6 rows, scrolls). Each row has an icon, name, +DEF, and its state:
    - price with a coin;
    - OWNED;
    - WORN;
    - FORGING (no art yet);
    - ON THE RACK (the cuirass, which is sold on the classic rack).
  - **Centre:**
    - the item name, with its slot tag and SET PIECE;
    - a **3D turntable** (24 Cycles frames of checkking's real meshes). It spins; R stops or starts it, a drag turns it, and the wheel zooms it;
    - < > arrows and the page dots;
    - **Defence +N** and **Compare Current ▸ After**;
    - **Set Bonus** "n / 11", with the tier lines turning green once reached;
    - the big gold button.
  - **Right:**
    - **EQUIPMENT**: the **live 3D hero** (a scene capture of the real hero; a drag turns him), with 12 slots around him. The selected piece's slot has a gold frame.
    - **SET PROGRESS**: the 5 tiers, with the reached ones lit.
    - Below either tab, the stats: Defence (with ▸ after and (+N)), Damage, Move Speed and Health.
  - **Bottom:** the key hints, exactly as in the target.
- **Button and keys:**

  | Situation | Button | E / click does |
  |---|---|---|
  | Can buy | **BUY FOR 2,000 G** | Pays from the HUD's Gold, then `BuyPiece`, a flash and the buy sound |
  | Owned | **EQUIP** / **TAKE OFF** | `ToggleWear` |
  | Can't afford | Dim button, red price | "Not enough gold, hunter." for 1.5 s, plus the fail sound |
  | No art yet | **BEING FORGED** (dim) | Nothing |

  - A / D (W / S, arrows, D-pad) navigate.
  - F turns Compare on or off.
  - Esc closes the shop.
- **WEAPONS and SUPPLIES tabs** show the **classic shop**, unchanged, with the new tab bar on top, so you can come back to ARMOUR.

## How it works
- **New hero component `BPC_VesnaTrade`.** Its `DrawTrade(Hud, SizeX, SizeY, Pass)` is called twice a frame from BP_ArmoryHUD's DrawHUD, through the hook:
  - **Pass 0** reads the input and, on ARMOUR / SETS, draws the whole screen and sets `Covering`.
  - The **classic shop draw (CX_26) and the old Obsidian side panel** (#222) only run while `Covering` is false. So their clicks can't fire under the new screen.
  - **Pass 1** draws the tab bar over the classic shop.
- **Look:**
  - `T_VT_Frame` (1920×1080) is the static frame, traced on top of the target: panels, title, labels, key hints.
  - `T_VT_Atlas` holds the text and sprite cells. The text cells are white and tinted when drawn, so OWNED, FORGING and green tiers cost no extra textures.
  - `T_VT_Icons` and `T_VT_Turn_*` hold the renders.
  - Numbers are drawn in Font_Cinzel, sized from the font's measured line height, so any import size works.
  - Everything is placed from `tools/tga/vesna/layout.json`, scaled to the screen and centred (letterboxed on screens that aren't 16:9).
- **Data comes from BPC_ObsidianSet v2:** ObsOwned, WornEff, AvailMask, NextPrice, WornCount, Tier and ShieldLevel, with `BuyPiece` / `ToggleWear`. Gold is the HUD's `Gold`. Nothing is copied, so the save, the tier bonus and the hero pieces keep working as they are.
- **Hero figure:** `VTCapture` is a SceneCaptureComponent2D on the hero.
  - It renders only the hero (show-only list) into `RT_VTHero`, once per frame and only while the screen is open.
  - `M_UI_VTHero` draws it with the capture's own alpha. If it's too dark or too bright, change its **Exposure** parameter.

## Steps (editor driver)
1. **#222 must be in first:** BPC_ObsidianSet v2 and its graph.
2. Run `py "<repo>/handoffs/vesna-trade-361/build/setup_vesnatrade_ue.py"` with **DRY_RUN = True**.
   - Read `setup_vesnatrade.txt`. Every line must say `ok`.
   - **Decision:** go on only with no MISSING.
3. Set `DRY_RUN = False` and run it again. It:
   - imports 8 textures to `/Game/CastleDefender/UI/Trade/Vesna`;
   - makes RT_VTHero and M_UI_VTHero;
   - makes the optional Vesna portrait capture;
   - creates BPC_VesnaTrade with its variables and defaults;
   - adds the hero's `VesnaTrade` and `VTCapture`.
4. Open BPC_VesnaTrade's EventGraph and paste `BPC_VesnaTrade_graph.txt` (Ctrl+V). Then File > Refresh All Nodes, Compile and Save.
5. BP_ArmoryHUD:
   1. Export the EventGraph fresh (`live.t3d`).
   2. Run `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/vesna-trade-361/build/manifest_trade.json --out merged.t3d`.
   3. Go on only with **Validation: OK**.
   4. Ctrl+A, BackSpace, Ctrl+V `merged.t3d`, then Compile and Save.

   If it says a CX_ name isn't found, your export numbers the nodes differently: post the names of the DrawHUD event's first two nodes and I'll fix the manifest.

## Checks
1. **Open Vesna's shop.** The new screen opens on ARMOUR, matching the target, with no classic shop or old side panel showing through. Screenshot it with `tools/shot.js --card 361`.
2. **A / D and the arrows** move the gold row frame.
   - The list scrolls past 6 rows.
   - The turntable shows the selected piece: Cuirass, Pauldrons, Gauntlets, Greaves and Sabatons are 3D; the rest show a line glyph and "In Vesna's forge".
   - R stops the spin, a drag turns it, and the wheel zooms it (0.8–1.3).
3. **With enough gold, buy the Pauldrons:**
   - gold drops by the price;
   - the row turns WORN;
   - the pauldrons appear on the hero figure (live capture) and on the hero in the world;
   - the set count goes up by 1;
   - the next price rises (#96 curve).

   Then E again: TAKE OFF, and the pieces go.
4. **With 0 gold:** the button is dim, and E or a click shows "Not enough gold, hunter." with the fail sound. Nothing is bought.
5. **WEAPONS tab:** the classic shop with its carousel and BUY works as before, under the new tab bar. Click ARMOUR to come back.
6. **Esc closes the shop** and the game unpauses. Re-open it: it opens on ARMOUR again.
   - **Decision:** if the shop doesn't close cleanly (for example the cursor stays, or the classic shop's own state stays open), tell me what's left. Esc only sets MPC `Shop.R` = 0, unpauses and hides the cursor.
7. **Hero figure:** the whole body is visible, lit, and has no background box.
   - If he's cut off, change `CapDist` / `CapHeight` on BPC_VesnaTrade's defaults (330 / 20).
   - If he's dark, raise Exposure on M_UI_VTHero.
8. **2 minutes of Play** with no new runtime errors from BPC_VesnaTrade (`pie_smoke.py`).

## Decisions
- **12 slots, not the target's 8.** There are 11 set pieces plus the shield (#362 asked for 13; the 13th, the weapon, isn't a set piece). They're drawn as 6 per side, slightly smaller. The other 3 pieces would otherwise have no slot.
- **Same price on every unbought piece.** Real data: the #96 curve price is shown on each row (2,000 in the mock-up), not the target's made-up per-piece prices. The same goes for **DEF**: it's pieces.csv's Def (the cuirass is +45, not the target's +28), and **Defence** is the sum of the worn pieces' DEF. The set tier is still what reduces damage, as in #96.
- **Set Bonus shows tiers 4 / 6 / 11** with the real effects (−6 %, the Ember shockwave at 40 dmg / 4 m / 12 s, Sovereign's Ember −15 %).
- **The button says BUY FOR** (Master: RECRUIT is the barracks #359 wording, same kit).
- **Iron and silver show 0.** I don't know the game's ore counter names. They're `OreIron` / `OreSilver` on BPC_VesnaTrade: tell me the source and I'll wire it.
- **Damage is 35** (the sword's BaseDamage in the hero export) and **Health is 250** (MaxHP, Master). Both are `HeroDamage` / `HeroMaxHP` on the component. Move speed is live: MaxWalkSpeed against its value when the shop first opened.
- **The cuirass stays on the classic rack** (as in #222), so its row reads ON THE RACK until it's owned.
- **WEAPONS / SUPPLIES are the classic shop for now.** Moving those items into this list needs a fresh BP_ArmoryHUD export, so it's v2 once this one is in.
- **Decal and material rule:** no existing material, texture or decal is touched. Everything here is new assets plus one new component and a capture on the hero.

## Files
| File | What |
|---|---|
| `setup_vesnatrade_ue.py` | step 1 (DRY_RUN): textures, RT + material, portrait, component + defaults, hero components |
| `BPC_VesnaTrade_graph.txt` | the component EventGraph (generated by `tools/tga/vesna/gen_trade.py`) |
| `ArmoryHUD_TradeHook_graph.txt` + `manifest_trade.json` | the BP_ArmoryHUD hook (merged with applyall) |
| `trade_data.json` | variable defaults and atlas UVs, read by the setup script |
| `assets/tga/VesnaTrade/textures/` | T_VT_Frame, T_VT_Atlas, T_VT_Icons, T_VT_Turn_{Chest,Shoulders,Gauntlets,Shins,Boots} |
| `tools/tga/vesna/` | `layout.py` (one layout for everything), `chrome.html` / `atlas.html` / `live.js` + `render.ps1` (frame, atlas, mock-up), `turntable.py` (Blender), `gen_trade.py` |
