# Weapon pack: Heater Shield, Round Shield, Emberoath (legendary short sword)

Made 2026-10-29 by `hossam gmail laptop2 (Claude)`. Original work: procedural, no third-party assets, safe for the
public repo. Every piece is a **low-poly game mesh with a 4K bake** from a 1.8–2.3 million triangle high poly.

| Item | Mesh | Tris | Size | What it is |
|---|---|---|---|---|
| **Heater Shield** | `SM_HeaterShield` | 6,746 | 0.62 × 0.84 m | Painted lime planks on gesso: *azure, a tower Or, on a chief gules three bezants*. Iron rim with rivets, sword gashes, dents, chipped paint, rust bleed, seam cracks. Back: bare planks, leather arm strap, quilted arm pad, leather-wrapped grip on two blocks, guige strap with an iron buckle. |
| **Round Shield** | `SM_RoundShield` | 5,872 | Ø 0.80 m | Seven bare linden planks, tapered 10.5 → 6 mm. Hammered iron boss with 5 rivets, laced rawhide rim with nicks, sun-greyed wood, a flame scorch, sword cuts, scratches, an arrow hole. Back: a wooden grip bar across the hand hole (leather-wrapped), clinched nails, guige strap. |
| **Emberoath** | `SM_Emberoath` | 2,540 | 0.69 m | Legendary short sword. Pattern-welded leaf blade with a fuller carved with runes that **glow ember-orange** (an Emissive map plus a pulse in the material). A gilded guard with swept quillons, ball terminals and amber cabochons. Leather grip bound with twisted gold wire, and a wheel pommel bearing the castle-tower crest of the heater shield. |

Textures per item: `BaseColor` (sRGB), `ORM` (R = AO, G = roughness, B = metallic) and `Normal_DirectX`; Emberoath
also has `Emissive`. Each item has a 512 px transparent shop icon, `T_Item_<Item>`, in `icon/`.

## Unreal

`py "<repo>/assets/laptop2/WeaponPack/import_weapons_ue.py"` imports all three. Add an item name, e.g. `... Emberoath`,
to import only that one. Each item goes to `/Game/CastleDefender/Weapons/<Item>/` and gets:
- its textures and a `MI_` of the shared master `M_LP2Weapon`. The master has `Tint`, `Wetness`, and `EmissiveBoost`
  (8) plus `EmberPulse` (0.25) for the sword's rune glow.
- 3 LODs (100 / 50 / 25 %)
- a box collision
- a **`Grip` socket at the pivot**

**Pivots:**
- **Shields:** the pivot is the centre of the hand grip. The heater's grip runs along Z; the round shield's runs
  along X. The face looks toward -Y.
- **Sword:** the pivot is the centre of the grip, with the blade along +Z.

Attach any of them to the hero's hand socket and set the rotation once.

**Shop:** the heater shield's Vesna entry is card #144 (`handoffs/heater-shield-vesna`). The round shield and Emberoath
can use the same pattern. Suggested prices:
- Round Shield: 180 gold, 12 % block
- Emberoath: 1,200 gold, +25 % sword damage, plus a 10 % chance of an ember burst that sets zombies alight. Its
  #32 fire trail hookup is optional.

## Rebuild

`source/` has everything needed to rebuild or vary the pack:
- the builders: `build_heater.py`, `build_round.py`, `build_sword.py` (plus `shieldkit.py`)
- the materials: `shieldmat.py` and `swordmat.py`
- the staged bake: `bake_shield.py` and `run_shield.ps1`
- the renders and the icon

To rebake one item, run:

```
powershell -ExecutionPolicy Bypass -File run_shield.ps1 -Shield Heater|Round|Sword
```

It needs about 2 GB free.
