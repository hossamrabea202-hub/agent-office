# Heater shield at Vesna's trade (owner request, 2026-10-29)

By `hossam gmail laptop2 (Claude)`. The owner asked for the new medieval heater shield to be sold in Vesna's
marketplace. The asset is `assets/laptop2/HeaterShield` (import script inside). This card is the shop side, for the
editor driver.

![shield](../../assets/laptop2/HeaterShield/renders/heater_front.png)

## The item

| | |
|---|---|
| Name | **Knight's Heater Shield** |
| Item id | **31**, slot **off-hand** (the Obsidian Sovereign shield is id 30, the same slot) |
| Price | **250 gold**, bought once. No upgrades: the upgrade path is the Obsidian shield (600 → 2400) |
| Effect | **15 %** block chance. A blocked hit does 50 % damage (Block = 0.5) |
| Trade text | `BLOCK 15%` · `BLOCKED HIT -50%` · `SLOT off-hand` · `lime wood, iron rim, painted arms` |
| Icon | `T_Item_HeaterShield` (512 px, transparent background, same framing as the other item icons), in `assets/laptop2/HeaterShield/icon/` |
| Mesh | `/Game/CastleDefender/Weapons/HeaterShield/SM_HeaterShield`. The pivot is the hand grip, the grip bar runs along the mesh's Z axis, and the painted face looks toward -Y |

It's the cheap starter shield: a player buys it early, then trades up to the Obsidian shield. Both are off-hand items
and only one can be worn at a time. Putting one on moves the other to the pack, the same rule as plate and cuirass.

## Steps (editor driver)

1. **Import:** `py "<repo>/assets/laptop2/HeaterShield/import_heatershield_ue.py"`. The Output Log shows
   "Heater shield imported".
2. **Icon:** import `icon/T_Item_HeaterShield.png` next to the other `T_Item_` icons (UI texture group, no mips,
   sRGB on).
3. **Hero:** add a StaticMeshComponent **HeaterShield** to BP_ThirdPersonCharacter, a child of Mesh on the same
   socket as the Obsidian shield. Relative location 0. Rotate it once in the viewport so the face points away from
   the body. Hidden by default, no collision.
4. **State:** in `BPC_ObsidianSet` (#121), next to ShieldLevel, add the bools `HeaterOwned` and `HeaterWorn` plus an
   event `BuyHeater()` that sets HeaterOwned. Put them in the save the same way as ShieldLevel.
5. **Vesna trade carousel** (BP_SkillTreeHUD, the same pattern as the other items): a new entry with the name, text,
   icon and price above.
   - **BUY:** Gold >= 250 → Gold -= 250 → `BuyHeater()` → the purchase fly-icon → the item goes to a free pack cell.
   - Once it's owned, the button shows **OWNED** and is disabled. It's never a stack.
6. **Equip** (BP_ArmoryHUD / pack drag to the off-hand slot):
   - Wearing it sets HeaterWorn and shows the HeaterShield component.
   - If the Obsidian shield is worn, it goes to the pack (and back the other way).
7. **Damage** (the #121 hero paste, Block term):
   `Block = 0.4 if (Obsidian shield worn and its roll hits) else 0.5 if (HeaterWorn and RandomFloat < 0.15) else 1.0`.
   The heater block doesn't write Shield.G (the rune flash and dome belong to the Obsidian shield only).

## Checks

- Vesna shows the heater shield with its icon at 250 gold. Buying it takes 250 gold and puts it in the pack.
  The button then shows OWNED.
- Drag it to the off-hand slot: the hero holds it on the forearm. The face points out, not into the body.
- Take about 40 hits with it on: roughly 6 of them do half damage.
- Wear the Obsidian shield: the heater goes back to the pack, and the other way around.
- Save, quit, load: owned and worn both come back.
