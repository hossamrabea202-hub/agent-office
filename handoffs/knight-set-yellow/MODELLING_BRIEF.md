# Yellow Eagle Knight set: modelling brief for TGA

Owner: *"give this to TGA and ask him to model the correct pieces to fit our inventory HUD"*.

- **Reference:** `reference.webp`, the full knight.
- **Model sheets:** `sheets/01..12`, from Codex, approved by the owner except 12 (still a draft). Each sheet has orthos,
  sections, dimensions, construction, materials and wear.
- **Not made yet:** sheets 13 (sword) and 14 (shield).

## Which pieces go in which inventory slot

The Vesna trade screen redesign (#361) has a paper doll with **13 slots**:
head, shoulders L/R, torso, upper arms, forearms, hands, waist, off-hand, thighs, shins, feet, cape.

The set fills them like this, **one inventory item per slot** (so pieces that are worn together are one item):

| Slot | Inventory item | Sheets | Build |
|---|---|---|---|
| Head | **Eagle Helm** (helmet + mail coif) | 01 + 02 | helmet rigid on `head`; coif skinned (neck and shoulders move) |
| Torso | **Eagle Hauberk & Surcoat** | 03 + 04 | **skinned** to the hero skeleton: mail shirt + cloth surcoat (cloth sim later) |
| Upper arms / forearms | covered by the hauberk's mail sleeves | 03 | no separate item: these two slots stay free for plate later |
| Hands | **Eagle Gauntlets** L + R | 08 | rigid lames on `hand_l` / `hand_r` (fingers on the finger bones if you can) |
| Waist | **Eagle Belts** (waist belt + sword belt + pouch) | 05 + 06 + 07 | skinned to `pelvis` / `thigh` (light weights), the pouch rigid |
| Thighs | **Eagle Cuisses** L + R (cuisses + poleyns) | 10 + 09 | rigid: cuisse on `thigh_*`, poleyn on `calf_*` at the knee |
| Shins | **Eagle Greaves** L + R | 11 | rigid on `calf_*` |
| Feet | **Eagle Sabatons** L + R | 12 | rigid on `foot_*` (toe lames on `ball_*`) |
| Off-hand | **Eagle Heater Shield** | 14 (to make) | rigid in `hand_l`, in the weapon kit's style |
| Weapon | arming sword | 13 (to make) | goes in the existing WEAPONSMITH kit (#233 / #255), not the paper doll |
| Shoulders, cape | none in this set | — | stay empty (the set has no pauldrons and no cape) |

That makes **8 wearable items** (+ the shield), each with an **inventory icon** for TGA's #361 HUD style.

## Rules (same as the Obsidian set, so it plugs into the same system)

- **Skeleton:** the hero's (UE5 mannequin bone names: `head`, `hand_l`, `thigh_l`, `calf_l`, `foot_l`, `pelvis`,
  `spine_03`...). Rigid plate rides one bone each; mail and cloth are **skinned**.
- **Table:** one row per mesh in a `pieces.csv` like `handoffs/obsidian-set-v2/pieces.csv` (Id, Piece, Slot, Side,
  Bone, KnightSlot, Def), so the existing equip, hide and save code takes it.
- **Quality:** the KB plus INDUSTRY_SECRETS. Calibrated steel (bare metal ≥ 180 sRGB, metallic 1), brass, leather and
  wool from the sheets' swatches. Wear by cause (edges, seams, mud low). Mail as real 4-in-1 rings (a normal or opacity
  trick on cards for the hauberk, geometry close up). `pbr_check.py` on every texture.
- **Budget** (third person, hero armour): 2K per item, 4K only for the hauberk + surcoat; LOD0 at about 8–25k tris per
  item, plus 3 LODs.
- **Order:** gauntlets → greaves → sabatons → cuisses + poleyns → helm → belts → hauberk & surcoat → shield.
  Plate first, because it's rigid and fast; mail and cloth last, because they're skinned and slow.
- **Renders:** each item next to its sheet for the owner's OK before import. Icons at 256 px for the HUD.
