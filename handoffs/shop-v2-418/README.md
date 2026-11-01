# #418 shop v2 (TGA): every armour piece and shield sellable at Vesna, wearable, with stats

## Step A: the four TGA Obsidian pieces (ready; data only, no graph paste)
Vambraces (17, forearms), Rerebraces (16, upper arms), Fauld (18, waist) and Cuisses (19, thighs) are already rows in
Vesna's ARMOUR list and already in the set table (`obsidian-set-v2/pieces.csv`, with their bones). They're hidden in the
game for one reason: their meshes aren't imported. `setup_set_v2_ue.py` leaves un-imported pieces out of `AvailMask`, and
Vesna only offers pieces in that mask. Once they're imported, the set attaches them to the hero by bone like the others,
counts them for the set tiers, and saves them.

![icons](renders/icons_418.png)

1. Import the meshes. Each script makes its MI under `/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/<Folder>`:
   - `assets/tga/Obsidian-Sovereign/Forearms/import_forearms_ue.py`
   - `.../UpperArms/import_upperarms_ue.py`
   - `.../Waist/import_waist_ue.py`
   - `.../Thighs/import_thighs_ue.py`
2. Re-run `handoffs/obsidian-set-v2/setup_set_v2_ue.py`. It's safe to re-run. Its log should list rows for
   `SM_ObsidianSovereign_Forearms_L/_R`, `UpperArms_L/_R`, `Waist` and `Thighs_L/_R`, and `AvailMask` should now include
   bits 6, 7, 8 and 9.
3. Run `armour/update_trade_armour_ue.py`: first as it is (DRY_RUN), then with `DRY_RUN = False`. It imports
   `T_VT_Turn_Forearms / UpperArms / Waist / Thighs` plus the new 9-icon `T_VT_Icons`, then sets BPC_VesnaTrade's
   `IconUV`, `IconFromAtlas` and `TurnTex` from `vesna-trade-361/build/trade_data.json`.
4. Play. Vesna > ARMOUR should show the four pieces with their icons and a turning preview. Buy one and it's worn on
   the right bone. Toggle it with E.

The turntables and icons are rendered by `tools/tga/vesna/turntable.py` (now reads `assets/tga/Obsidian-Sovereign` too;
L/R pairs stand upright side by side). The textures are in `assets/tga/VesnaTrade/textures/`.

## Step B: shields, and Vesna v2 (ready; one Blueprint at a time)
Three shields are sold as rows at the end of Vesna's ARMOUR list. Each shows its own icon, turntable and BLOCK %.

| Shield | Price | Block chance | A blocked hit does | Mesh |
|---|---|---|---|---|
| Round Shield (linden wood) | 180 g | 12 % | 50 % | `/Game/CastleDefender/Weapons/RoundShield/SM_RoundShield` (laptop2 pack) |
| Knight's Heater Shield (#144) | 250 g | 15 % | 50 % | `/Game/CastleDefender/Weapons/HeaterShield/SM_HeaterShield` (laptop2 pack) |
| Gilded Shield (the old SM_Shield) | 450 g | 20 % | 45 % | `/Game/CastleDefender/Equipment/Weapons/Shield/SM_Shield` |

**How it works:**
- Buy a shield and it's worn at once. E on a worn shield takes it off. Wearing another one swaps them: one off-hand at a time.
- Owned and worn shields are saved in slot `ShieldKit`.
- Vesna v2 also gets the Muster's click fix: Game And UI input while open, and its own press edge. The v1 graph used
  `WasInputKeyJustPressed` under Game Only input.

**Install:**
1. `py assets/laptop2/WeaponPack/import_weapons_ue.py HeaterShield RoundShield`
2. Run `shields/setup_shieldkit_ue.py`, first as DRY_RUN, then with `DRY_RUN = False`. It creates SG_ShieldKit and
   BPC_ShieldKit with the table above, and adds `ShieldKit` and an `OffHand` mesh component (tag OffHand) under the hero's Mesh at
   `OFFHAND_SOCKET` (`hand_l`; use the Obsidian shield's socket if it has its own).
3. Paste `shields/BPC_ShieldKit_graph.txt` into BPC_ShieldKit's EventGraph, then Compile and Save (applyall: Validation OK, 83 nodes).
   - In BPC_ShieldKit's defaults, set `GripLoc` / `GripRot` once per shield so each sits on the forearm with its face out.
     Wear one in PIE, then adjust in the viewport.
4. Run `trade/setup_trade_v2_ue.py` (DRY_RUN, then `False`). It backs up `BPC_VesnaTrade_v1_backup`, imports
   `T_VT_Atlas_418`, the 11-icon `T_VT_Icons` and the 6 turntables, adds `Kit` / `PrevDown` / `ModeUI`, and sets every
   default. **Then paste right away:**
5. Replace BPC_VesnaTrade's EventGraph with `trade/BPC_VesnaTrade_graph.txt`, then Compile and Save (applyall: Validation OK,
   1,510 nodes). The ArmoryHUD hook doesn't change.
6. **Hero damage, a 2-node edit:** where the hero multiplies the incoming damage by the Obsidian block term (10-30b:
   `ObsDmg = Damage × Select(0.4, 1.0, ObsBlocked)`):
   - call `ShieldKit.Roll` on the exec line just before that multiply;
   - multiply the result by `ShieldKit.LastMult`.

   I'll turn this into a generated paste when the fresh hero export lands. Until then, it's two nodes by hand.

**Play test:**
- [ ] Vesna > ARMOUR, scroll to the end: three shields with icons and turning previews (the Gilded Shield shows a glyph),
  `% BLOCK` in place of DEF, and their prices.
- [ ] Buy the Heater: gold −250, the hero holds it, the row says WORN, and the EQUIPMENT doll's shield slot lights.
- [ ] E on it takes it off. Buy and wear the Round: it swaps.
- [ ] About 40 hits wearing the Heater: roughly 6 do half damage.
- [ ] Save and load: owned and worn come back.
- [ ] Single clicks on tabs, rows and the button respond. After Esc, the mouse is back in game mode.

**Roll back:**
- Shop: paste the EventGraph from `BPC_VesnaTrade_v1_backup`, and set AtlasTex back to `T_VT_Atlas`.
- Shields: remove the `ShieldKit` component from the hero.

**Not in this step:**
- Wearing a kit shield doesn't hide the Obsidian shield (ShieldLevel). Both block terms apply. To make it one off-hand
  only, I need the BPC_ObsidianSet export to see how that shield is shown.
- A fourth, plainer wood shield (the card's "wood"): the Round Shield is bare linden for now. If the owner wants a
  separate one, I'll model it.
