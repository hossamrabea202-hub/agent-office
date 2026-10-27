# Vesna shop: Obsidian Sovereign chest + crossbow "Upgrade" (#52)

From **vice master (Claude)**, 2026-10-27 night. Owner asked: make the Obsidian set purchasable at Vesna, with icons and a
wearing system that swaps with the silver armour, AAA only. Not started in the graphs yet because both changes are big HUD
pastes and the night's plan budget ran low; everything below is ready for whoever drives the editor next.

## Already done (live in the project)
- `SK_ObsidianSovereign_Chest` (skinned to `ShadowknightUE_Skeleton`, fitted in Blender) + `SK_Knight_ChestRemnant`
  (knight pauldrons only), `/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Chest`.
- Hero `BP_ThirdPersonCharacter` has components **ObsidianChest** and **ChestRemnant** (children of Mesh, AnimClass
  `ABP_KnightFollow`, same as KnightMesh). No graph change needed for the wear visuals.
- Swap switch: **MPC_SkillTree `Armor`.R** (0 = silver chest, 1 = obsidian chest). Material gate `ArmorMode` on
  `M_HeroArmor_AAA` and `M_ObsidianSovereign` (1 hide when worn, -1 show only when worn). Verified in Play both ways.

## What the HUD side must do
1. **Item**: new HUD vector `ObsV` (X = cell: 0 worn / 10..29 pack / -1 held, Y = owned) on BP_ZombieHUD like PlateV.
   Treat it as a torso item exactly like the Golden Breastplate remap (`SelectInt(8, T, T==2 && (Held==8 || worn))`):
   add item id 10 the same way. Equipping it puts the silver chest (ChestLoc) into the pack (same rule as the plate in
   BP_QueueHUD: worn && ChestLoc==0 -> ChestLoc = free pack cell), and vice versa.
2. **Write Armor.R** every frame = ObsV worn (next to where Gear.R is written at the start of the parent DrawHUD).
   Plate and obsidian are exclusive (both torso).
3. **Stats**: DEF +45, DAMAGE TAKEN -35 % (hero ReceiveAnyDamage multiplies by 1 - 0.25*Gear.R today: add the
   obsidian term).
4. **Vesna**: 5th trade item 'Obsidian Sovereign Cuirass', 450 gold, stats lines 'DEFENCE +45', 'DAMAGE TAKEN -35%',
   'SLOT torso', 'blackened steel, gold inlay'. Trade carousel lives in BP_SkillTreeHUD (design: Tools/Barracks_Scripts/
   trade_hud_4items.py: nested 4-way Selects `pickn/pickns`, wrap `NIT`, BUY chain per item, purchase fly-icon loop).
   Showcase: add the SM_ObsidianSovereign_Chest to BP_TradeShowcase (base MI_ObsidianSovereign_Chest, ArmorMode 0).
5. **Icon**: T_Item_obsidian_chest (AAA: render SM_ObsidianSovereign_Chest with the game's icon setup, transparent bg,
   same framing as T_Item_plate) for pack cells, torso slot and the trade fly-in.
6. **#52 in the same paste**: a weapon is never a stack. BUY on an owned crossbow becomes **UPGRADE** (levels: reload
   faster, +damage, stun shot #4; show next level + price; MAX disables). Reproduced 10-27: second BUY -> OWNED 2, x2.

## Checks
Buy at Vesna -> chest appears in the pack -> drag to torso -> hero wears obsidian (silver chest moves to the pack) ->
drag silver back -> silver returns. Gold, DEF and damage taken update. Crossbow: buy once, button turns UPGRADE.
