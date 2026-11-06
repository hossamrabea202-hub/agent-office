# TGA's weapons at Vesna: playable, perks, upgrades (audit seat, 2026-11-06)

Owner's order (11-06): "make sure all the weapons assets created by TGA earlier this week are inside the trade HUD at Vensa and
they are playable, positioned correctly, can be used in combat and correct stats and added to hero when he is wearing it and
can be upgraded. and each weapon comes with a unique feature".

This folder is a **plan and data sheet for the Master seat (i9)**. Nothing in the project was touched. Files:

| File | What |
|---|---|
| `weapons_vensa_1106.csv` / `.json` | the 5 rows: price, damage, speed, block, perk per level, 3 upgrade tiers, grip data |
| `swap_aaa_weapons_ue.py` | data-only editor script: points `BPC_WeaponKit.Meshes[]` at the AAA meshes (dry run / `--apply` / `--revert`); syntax-checked, never run in UE |
| `cpp/CDWeaponPerks.h/.cpp` | DRAFT of the perk + upgrade rules, next to `CDCombatRules` (same pin-filter style). Not compiled; owner reviews first |

## 1. Inventory: what TGA made this week, and what is in the project

TGA's weapon hand-off this week is **#397 "Weapon kit AAA: first 5 weapons"** (commits c5018675 / 2fc26c6c, 2026-11-01, `assets/tga/WeaponsAAA`).
They are AAA rebuilds (materials, secondary edge bevel, forge scale, textures that pass pbr_check) of five weapons of checkking's
25-weapon CK kit, **same names, pivots and axes** as the live kit. The other 20 wait for the owner's OK of the before/after sheet
(`handoffs/weapon-kit-aaa/renders/before_after_5.jpg`).

| Weapon | Kit row | FBX | Textures (2K, capped 1K) | In project? | Live mesh it replaces | Grip / socket | Stats TGA wrote |
|---|---|---|---|---|---|---|---|
| Arming Sword | 0 | `assets/tga/WeaponsAAA/ArmingSword/SM_CK_ArmingSword.fbx` | `T_CK_ArmingSword_BaseColor / _ORM / _Normal_DirectX.png` | **NO** (`Content/CastleDefender/Weapons/CK_AAA/` does not exist) | `/Game/CastleDefender/Weapons/CK/ArmingSword/SM_CK_ArmingSword` | grip at origin, +Z along blade, bone `weapon_r` | none (art only; stats come from the live kit: 300 g, dmg 40, speed 1.1) |
| Longsword | 6 | `.../Longsword/SM_CK_Longsword.fbx` | `T_CK_Longsword_*` | **NO** | `.../CK/Longsword/SM_CK_Longsword` | same | 600 g, dmg 58, speed 0.95 |
| War Axe | 10 | `.../WarAxe/SM_CK_WarAxe.fbx` | `T_CK_WarAxe_*` | **NO** | `.../CK/WarAxe/SM_CK_WarAxe` | same | 450 g, dmg 52, speed 1.0 |
| Flanged Mace | 14 | `.../FlangedMace/SM_CK_FlangedMace.fbx` | `T_CK_FlangedMace_*` | **NO** | `.../CK/FlangedMace/SM_CK_FlangedMace` | same | 500 g, dmg 56, speed 0.9 |
| Halberd | 23 | `.../Halberd/SM_CK_Halberd.fbx` | `T_CK_Halberd_*` | **NO** | `.../CK/Halberd/SM_CK_Halberd` | same | 1100 g, dmg 75, speed 0.75 |

Renders per weapon: `<Name>/renders/before_*.png, after_*.png, after_*_detail.png`. Import script: `assets/tga/WeaponsAAA/import_weapons_aaa_ue.py`
(DRY_RUN = True by default; imports into the NEW folder `/Game/CastleDefender/Weapons/CK_AAA/<Name>`, MI parented to the read-only
`M_CK_Weapon`, logs live vs AAA bounds). The live CK kit (26 rows incl. Emberoath) is imported and wired; it is what Vesna sells today.

Also from TGA this week, **not weapons for Vesna** (listed so nothing is missed):
- #543 (today 16:26): the **Ulfberht sword** is a historic find in the mine with an info card (`assets/tga/MineLift543`), not a shop item.
  If the owner wants it sellable later it would be row 26 of the kit; not in this sheet.
- #502 medic gear, #338 wasp v2, Vesna trade textures (`assets/tga/VesnaTrade`, armour turntables + icons): not weapons.
- Shields at Vesna (Round / Heater / Gilded, #418 + #433 grip fix) are i5 / laptop2 work, already sold and worn via BPC_ShieldKit.

## 2. How weapons work in the game today (read from the 11-03 exports + Source)

- **Shop:** `BPC_VesnaTrade` has tabs WEAPONS (Tab 0) / ARMOUR / OBSIDIAN / SUPPLIES. The WEAPONS tab is the **WEAPONSMITH list**
  drawn by `BPC_WeaponKit.DrawWeapons` through the native ArmoryHUD hook (`CDHudGen_BP_ArmoryHUD.cpp` `N_whHookWeapons5`, C++).
  One row per kit weapon: name, damage, BUY price / EQUIP / EQUIPPED. Click = buy (takes `Gold` on BP_SkillTreeHUD, int) or equip / put away.
- **Data:** `BPC_WeaponKit` class defaults: `Names[]`, `Prices[]`, `Damage[]`, `Speed[]`, `Meshes[]` (row order = `handoffs/weapon-kit-wiring/weapons.json`),
  `Owned` (bitmask), `Equipped` (row, -1 = none), `WeaponRot` (one rotator for the whole kit), `KnightSwordBone` = `weapon_r`. Saved in slot
  `CastleSaveWeapons` (`Data` = [Owned, Equipped]; F12 fix H already applied).
- **Equip / position:** `ApplyEquip` sets the `KitWeapon` StaticMeshComponent (child of `KnightMesh`, tag KitWeapon, no collision) to
  `Meshes[Equipped]`, attaches it to bone `weapon_r`, relative rotation `WeaponRot`, and hides the knight's own sword bone. The CK meshes
  (and TGA's AAA copies) have the **grip at the origin and +Z along the blade**, so one `WeaponRot` fits all of them and per-weapon offsets are 0.
  The 10-31 export shows `WeaponRot = 0,0,0`; the README said "set it once in Play" (candidates Roll 90 or Yaw 90). **Master: read the live value
  first; if the kit sits wrong in the hand today, that is the one field to tune, for all 26 weapons at once.**
- **Damage (hero EventGraph, #255 part 2):** `WeaponMul = Damage[Equipped] / 40` (x1 with nothing equipped). Slash: `XL20 (35 + bonuses) x WeaponMul`
  into `ZX8` / `ZX9` ApplyRadialDamage (radius 150 cm); single hit `35 x WeaponMul` into `CH7` ApplyDamage. Montage PlayRate = `Speed[Equipped]`.
- **Damage taken (hero):** `ReceiveAnyDamage` -> `InfDmg` (infection DefMul) -> `ShieldKit.Roll` x `LastMult` (shkMul4) -> `ObsDmg` (Obsidian 0.4 / 1.0)
  -> `DamageTaken += ...`; dead at `DamageTaken >= 250`. There is no `Health` variable: health = 250 - DamageTaken. A `RegenGate` (not Infected) runs the BP regen.
- **Existing stats:** damage, attack speed, block (shields and Obsidian only). No crit, no per-weapon regen, no weapon levels today
  (weapon upgrades #95 are a research checkpoint only; the crossbow has its own 4 levels).
- **Combat rules in C++:** `UCDCombatRules` pin filters (`GateHeroAttack`, `ReachableGoal`, `ZombieFlinch`...). `AZombieBase::PickFlinchMontage`
  already picks stagger / heavy by damage and by causer name (#519). That is where the mace perk hooks in.
- **Save:** the C++ `UCDSaveSubsystem` (#500) with `Ints` map per slot: the levels go there (slot `WeaponPerks`), no Blueprint save paste.

## 3. The sheet (full rows in the CSV / JSON)

Base price / damage / speed stay **exactly the live kit values** (gameplay 1:1 for the other 20 weapons). Upgrades: 3 tiers, each
**+12 % damage** (rounded), costs 0.5x / 0.8x / 1.2x of the price. The perk grows with the level.

| Weapon | Price | Dmg | Speed | Perk (unique) | L0 -> L1 -> L2 -> L3 | Upgrade cost 1 / 2 / 3 | Damage L1 / L2 / L3 |
|---|---|---|---|---|---|---|---|
| Arming Sword | 300 | 40 | 1.1 | **Knight's Vigil**: health regenerates (wounds close) | 2 -> 3 -> 4 -> 5 HP/s (paused while infected and 3 s after a hit) | 150 / 240 / 360 | 45 / 50 / 54 |
| Longsword | 600 | 58 | 0.95 | **Half-Sword Parry**: block chance without a shield | 12 -> 15 -> 18 -> 22 % block, a parried hit does 50 % (stacks with a shield roll) | 300 / 480 / 720 | 65 / 72 / 79 |
| War Axe | 450 | 52 | 1.0 | **Executioner's Edge**: triple-damage chance | 15 -> 18 -> 22 -> 25 % per hit, damage x3 | 230 / 360 / 540 | 58 / 64 / 71 |
| Flanged Mace | 500 | 56 | 0.9 | **Bone Breaker**: every hit staggers; crushes colossi | stagger at every level; +15 -> 25 -> 35 -> 50 % damage vs colossi | 250 / 400 / 600 | 63 / 69 / 76 |
| Halberd | 1100 | 75 | 0.75 | **Reaper's Reach**: the sweep reaches further | slash radius 210 -> 230 -> 250 -> 270 cm (kit: 150) | 550 / 880 / 1320 | 84 / 93 / 102 |

Why these: the owner's three examples (regen, triple damage, block) are on the three "normal" weapons; the two heavy ones get what their
shape says (mace = stagger / crush, halberd = reach). Prices of the live kit already order them cheap -> dear, so the perks do too.

Grip / socket per weapon: **pivot = grip, +Z = blade, GripLoc 0,0,0, GripRot 0,0,0 relative to the kit's `WeaponRot`, socket `weapon_r`** (all five).
The import log must print live vs AAA bounds within ~1 cm per weapon; if one differs, that weapon keeps the live mesh until TGA re-exports.

## 4. Implementation plan for the Master seat (in this order, Save after every step)

**A. Import (editor Python, when no build is running)**
1. `py "C:\Users\hossa\Documents\agent-office\assets\tga\WeaponsAAA\import_weapons_aaa_ue.py"` (DRY_RUN): the log must say `master ... ok` and
   `live mesh ok` for all 5. Then set `DRY_RUN = False`, run again. Check `import_weapons_aaa.txt`: 5 x "imported", and each `live bounds z` line
   within ~1 cm of the AAA line. Commit the txt to the office repo.
2. Owner's look OK on TGA's sheet (`handoffs/weapon-kit-aaa/renders/before_after_5.jpg`) is still open on #397: ask once, in the chat.

**B. Swap the meshes (data only)**
3. `py ".../handoffs/weapons-vensa-1106/swap_aaa_weapons_ue.py"` (dry run: rows 0 / 6 / 10 / 14 / 23 must read Arming Sword / Longsword /
   War Axe / Flanged Mace / Halberd), then `--apply`. Undo: `--revert`. Nothing else in `BPC_WeaponKit` changes.

**C. C++ (owner reviews the draft first, then build while the editor is closed)**
4. Copy `cpp/CDWeaponPerks.h` to `Source/CastleDefender/Public/`, `cpp/CDWeaponPerks.cpp` to `Private/`. Read the draft: it is untested.
5. `ZombieBase.cpp`, `PickFlinchMontage`: after the heavy pick (`if (bHeavy) ...`), add
   `if (!M && UCDWeaponPerks::ForceStagger(LastHitCauser.Get())) { M = Pick(HitStagger); }`.
   `AZombieBase::TakeDamage`: multiply the incoming damage by `UCDWeaponPerks::StaggerBonus(DamageCauser, this)` (1 when not the mace).
6. `CDHudGen_BP_ArmoryHUD.cpp`, `N_whHookWeapons5`: after the `DrawWeapons` call add `UCDWeaponPerks::DrawShopCard(C.Self, SizeX, SizeY);`
   (same SizeX / SizeY it passes to DrawWeapons). `CDHudGen_BP_HeroHUD.cpp`: at the end of the draw add `UCDWeaponPerks::DrawBadge(C.Self, SizeX, SizeY);`.
   The file is generated by `bp_to_cpp.py`: put the two calls where the generator keeps hand edits, or re-add them after a regeneration.
7. Build. New cvars: `cd.Weapon.Perks` (0 = the old game), `cd.Weapon.PerkLog 1` to see every roll in the Output Log.

**D. Hero Blueprint: 4 pin filters (scripted, tagged, undoable, like GateHeroAttack; no other node changes)**
8. `BP_ThirdPersonCharacter` EventGraph:
   - `UCDWeaponPerks::HeroDamage(In)` between `WdMulSlash.ReturnValue` and `ZX8.BaseDamage` + `ZX9.BaseDamage`; and between `WdMulHit.ReturnValue` and `CH7.BaseDamage`.
   - `UCDWeaponPerks::SlashRadius(In)` on `ZX8.DamageRadius` and `ZX9.DamageRadius` (the 150 literal becomes its input).
   - `UCDWeaponPerks::HeroIncoming(In)` between `shkMul4.ReturnValue` and `ObsDmg.B`.
   With nothing equipped, or any of the other 21 weapons, every function returns its input: gameplay 1:1.
9. Compile, Save, export the hero EventGraph to `handoffs/exports/master/2026-11-06c/` for the office.

**E. Showcase (optional, TGA's side, not blocking):** the WEAPONS tab has no turntable today (the armour tab does). TGA can render
`T_VT_Turn_<Weapon>.png` for the 5 with `tools/tga/vesna/turntable.py` and a 5-icon strip; wiring them into BPC_VesnaTrade is a later card.

## 5. Play test (owner or Master, cd.Weapon.PerkLog 1)

1. Vesna > WEAPONS: the 5 rows show the live prices (300 / 600 / 450 / 500 / 1100) and damage (40 / 58 / 52 / 56 / 75).
2. Buy the Arming Sword (gold -300): it is in the right hand, grip in the fist, blade up along the hand, not through the forearm; idle, run, both slashes. Same check for the other four (halberd: haft does not sink into the ground in idle).
3. Swing at a zombie: the HP bar drops by about the same as the live kit (damage unchanged at level 0).
4. Perks: Arming Sword equipped, take a hit, stand 3 s: the HP bar refills slowly (2 HP/s). Longsword: in ~40 hits taken, ~5 show PARRIED and do half. War Axe: in ~20 hits dealt, ~3 show TRIPLE BLOW. Flanged Mace: every hit plays the stagger montage; on a colossus the log shows CRUSHED. Halberd: zombies at 2 m are hit by the slash (kit weapons miss them).
5. Shop card: with a TGA weapon equipped, a card right of the list shows the perk, LEVEL pips and `UPGRADE <cost> g [U]`. Press U twice (gold -150, -240 for the Arming Sword): pips fill, damage per hit rises (45, then 50), regen 3 then 4 HP/s. Third press: 360 g, then MAX.
6. HUD in combat: the badge under the HP bar reads the perk name and level.
7. Quit Play, Play again: owned, equipped (existing save) and the levels (`Saved/SaveGames/WeaponPerks*`) come back.
8. `cd.Weapon.Perks 0`: everything behaves as the live game. Frame time unchanged (one reflection read per hit, one per frame for regen).

## 6. Open points for the owner
- OK on the 5 perks and the numbers above (edit the JSON, the C++ table is the same rows).
- OK on TGA's AAA look (sheet on #397) before the mesh swap.
- Whether the Ulfberht (#543) should become a sellable weapon later.

## Status 2026-11-06 18:17 (Master seat, this session)
- A import: 5 AAA meshes in `/Game/CastleDefender/Weapons/CK_AAA`, re-imported at scale 0.01 to match the live kit (`reimport_aaa_scale_ue.py`, boxes match within 0.1 cm).
- B swap: `BPC_WeaponKit.Meshes[0/6/10/14/23]` on CK_AAA, saved (`swap_aaa_backup.json` for `--revert`).
- C C++: `CDWeaponPerks.h/.cpp` + 3 hooks built, Succeeded (DLL 18:14). Fix vs the first draft: `GLog` -> `GPerkLog` (name clash with Unreal's global).
- D hero pin filters: 6 insertions OK, no errors, saved; export `handoffs/exports/master/2026-11-06c`; hero backup `Saved/Backup_HeroPerks_1106`.
- NOT play-tested (owner skipped steps 3-4). Rollback: `cd.Weapon.Perks 0` (perks off), `swap_aaa_weapons_ue.py --revert` (old meshes), hero BP from the backup.
