# checkking medieval weapon kit (night of 2026-10-30)

16 historical weapons, built procedurally in Blender (`source/build_weapon.py`), baked to 2K PBR, ready for UE 5.3.
They're static meshes, with the hand point at the origin and Z along the weapon.

| Weapon | Folder | Length | Tris | Notes |
|---|---|---|---|---|
| Arming sword | `ArmingSword` | 0.93 m | 4.6k | one-handed, fuller over 70 % of the blade, wheel pommel, leather-wrapped grip |
| Longsword | `Longsword` | ~1.2 m | | two-handed grip, short fuller, scent-stopper pommel |
| Falchion | `Falchion` | 0.82 m | 3.3k | single edge, widening clipped tip, bronze pommel |
| Rondel dagger | `RondelDagger` | 0.42 m | 3.0k | stiff triangular blade, disc guard and pommel |
| Messer | `Messer` | 0.88 m | 1.9k | single edge with a slight curve, nagel, riveted oak grip slabs |
| Bearded axe | `BeardedAxe` | 0.76 m | 3.0k | Viking hand axe: the beard hooks below the eye |
| Dane axe | `DaneAxe` | 1.47 m | 3.3k | two-handed, broad thin crescent, iron bands |
| War axe | `WarAxe` | 0.59 m | 6.3k | horseman's axe: steel head, back spike, langets, leather grip |
| Bardiche | `Bardiche` | 2.08 m | 3.9k | long crescent fixed to the haft at two sockets |
| Flanged mace | `FlangedMace` | 0.71 m | 6.5k | seven iron flanges, iron haft, leather grip |
| War hammer | `WarHammer` | 0.75 m | 4.6k | square face, back beak, top spike, langets |
| Winged spear | `WingedSpear` | 2.43 m | 1.3k | leaf blade, side wings, butt cap |
| Boar spear | `BoarSpear` | 2.26 m | 1.8k | broad blade, wings, leather grip rings |
| Partisan | `Partisan` | 2.55 m | 1.8k | broad triangular head with side lugs |
| Glaive | `Glaive` | 2.66 m | 1.1k | curved blade, back hook |
| Halberd | `Halberd` | 2.33 m | 4.0k | axe blade, back fluke, top spike, langets |

Each folder holds:
- `SM_CK_<Name>.fbx`
- `textures/T_CK_<Name>_BaseColor.png` (sRGB) and `_ORM.png` (R AO, G roughness, B metallic)
- `_Normal_DirectX.png`
- `renders/<name>_preview.png`

## Import

```
py "<repo>/assets/checkking/Weapons/import_weapons_ue.py"
```

It imports every folder into `/Game/CastleDefender/Weapons/CK/<Name>/`: the mesh, 3 textures, and `MI_CK_<Name>` on the
shared master `M_CK_Weapon` (Tint and RoughnessScale parameters). Nothing live is changed, and it writes
`import_weapons.txt`.

Using a weapon in game:
- Attach the static mesh to the hand socket. The grip or haft hand point is the mesh origin.
- One-handed weapons put the grip centre at the origin. Polearms put the main hand at the origin.

## Realism (knowledge base)

- **Calibrated values:**
  - bare steel is metallic 1, base ~sRGB 192
  - forged iron is darker and rougher (oxide scale)
  - ash and oak hafts are in the 30–240 sRGB band, with growth-ring grain
  - leather grips
- **Roughness is never flat:** grinding streaks run along the blade, plus large smudges.
- **Wear by cause:** edges are polished brighter and smoother (curvature), cavities darken (AO).
- **Blades are real sections:** thin edges, a thick spine and a fuller groove (thick at the eye of an axe, about
  0.6 mm at the edge).
- **Bake gate:** the batch logs the baked albedo range (`ALBEDO sRGB p2/p50/p98`). Steel is ~185–210, wood ~70–90, and
  nothing sits below 27.

## Known limits / v2

- v2 (done): metal-first UV packing. Wood and leather islands are packed at 35 %, so blades and heads get about 4x the
  texels.
- Rigid static meshes: no skinning needed for weapons.

## Rebuild

```
blender -b --factory-startup -P source/build_weapon.py -- <weapon> <out_root> 2048 32
```

`<weapon>` is one of: `arming_sword longsword falchion messer rondel_dagger bearded_axe dane_axe war_axe bardiche
flanged_mace war_hammer winged_spear boar_spear partisan glaive halberd`.
