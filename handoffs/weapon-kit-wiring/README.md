# Weapon kit wiring: buy, equip and hold the 25 checkking weapons

By `checkking (Claude)`, 2026-10-31. Paste-only for the Master (owner rule). Pre-checked:
- `fix_impure.py` + `applyall check` on `BPC_WeaponKit_graph.txt`: **Validation OK** (175 nodes).
- The ArmoryHUD hook manifest was dry-run on the 10-30b export with the checkking 3-pin hook merged first: **Validation OK**.

## What the player gets

In Vesna's shop there is a **WEAPONSMITH** panel on the **left** edge (the Obsidian panel stays on the right):
- One row per weapon (25): name, damage, and **BUY price** (red when you can't afford it), **EQUIP** or **EQUIPPED**.
- Clicking a row:
  - buys the weapon (takes `Gold`) and puts it in the hero's right hand;
  - or switches to that weapon if it's already owned;
  - or puts it away if it's the one equipped.
- Owned and equipped weapons are saved (slot `CastleSaveWeapons`).

## Steps

1. Run `py "<repo>/assets/checkking/Weapons/import_weapons_ue.py"` to import the 25 meshes.
2. Run `py "<repo>/handoffs/weapon-kit-wiring/setup_weaponkit_ue.py"`. It creates BPC_WeaponKit and adds `WeaponKit` and
   `KitWeapon` to the hero.
3. Paste the 12 lines of `VARIABLES_BPVar.txt` on BPC_WeaponKit's VARIABLES header, one at a time, then Compile.
4. Run `setup_weaponkit_ue.py` again. It fills the names, prices, damage and meshes. Check `setup_weaponkit.txt`: 25 meshes found.
5. Paste `BPC_WeaponKit_graph.txt` into BPC_WeaponKit's EventGraph. Compile and Save.
6. Export BP_ArmoryHUD's EventGraph, run `applyall.py merge --manifest handoffs/weapon-kit-wiring/manifest_armoryhud_weapons.json`,
   then paste only the 8 new nodes and their 3 links.
   - If the pasted DrawReveal node isn't named `ohHookReveal10`, link its `then` to `WeaponHookIf` by hand. That's a
     one-minute fix.

## Tests

1. With 2,000 gold, open Vesna's shop: WEAPONSMITH is on the left. Buy the Arming Sword (300): gold is 1,700 and the
   sword is in the right hand.
2. Click Longsword (600): the hand switches to it. Click it again: it's put away.
3. With 0 gold, BUY is red, and a click shows "Not enough gold, hunter."
4. Quit Play and start Play again: the owned and equipped weapon come back.

## Minor tuning (Master may do it on the spot)

`WeaponRot` on BPC_WeaponKit's class defaults sets how the weapon sits in the hand. The weapons are built Z-along-blade
with the grip at the origin. Something like (Pitch 0, Yaw 0, Roll 90) or (0, 90, 0) usually matches the knight's
`hand_r`. Set it once in Play with one sword.

## The knight's own sword

While a kit weapon is equipped, BPC_WeaponKit hides the knight's built-in sword with `HideBoneByName(KnightSwordBone)`
(default `weapon_r`). It shows it again when the weapon is put away.
- If the ShadowknightUE skeleton names that bone differently, set `KnightSwordBone` on BPC_WeaponKit's class defaults.
  The bone list is in the Skeleton editor.
- That's a one-field change, so the Master may do it on the spot.

## Part 2: the equipped weapon changes the hero's damage and attack speed (#255)

`Hero_WeaponDamage_graph.txt` + `manifest_hero_damage.json` (17 nodes, no casts; dry-run on the full 10-30b hero export:
**Validation OK**). The damage multiplier is `WeaponMul = Damage[Equipped] / 40`, or ×1 when nothing is
equipped:
- the sword slash: `XL20` (base 35 + bonuses) `× WeaponMul` goes into both ApplyRadialDamage calls (ZX8, ZX9);
- the single hit: `35 × WeaponMul` goes into CH7 ApplyDamage.

So the Arming Sword (40) is ×1.0, the Zweihänder (80) ×2.0 and the Rondel dagger (28) ×0.7.

**Attack speed:** `Speed[Equipped]` (×1 with nothing equipped) is the PlayRate of both slash montages, CC7 (AM_Slash1)
and CC12 (AM_Slash2). The dagger swings at 1.4×, polearms at 0.75×.

Apply it after part 1: export the hero EventGraph, merge `manifest_hero_damage.json`, paste the 12 nodes, then Compile.

**Test:** equip the Zweihänder and hit a zombie: it takes twice the Arming Sword's damage (watch the HP bar), and the
swing is visibly slower. Equip the Rondel dagger: fast swings, less damage. Put the weapon away: the knight's sword is
back and damage is as before.
