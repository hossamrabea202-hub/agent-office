# #435 P1: hero and soldier faces render black (hand-off to i9, 2026-11-02)

Built on: a read-only scan of the CastleDefender6 assets on i5 (`scan_faces435_ue.py` -> `scan_report.txt`). The owner
moved the face test to i9 because the i5 editor GPU-crashed on a head render (2 GB GPU).

## What the scan found
- **Soldiers** (`BP_SoldierSword`, `BP_SoldierXbow`, `BP_SoldierCommander`): **no head mesh at all**. They only have
  `KnightMesh` = `ShadowknightUE_SK` (armour, `MI_Hero_HelmetWorn` on the helmet), plus the hidden Quinn body. The black
  "face" is the empty inside of the helmet.
- **Hero** (`BP_ThirdPersonCharacter`): has `HeroHead` = `SM_HeroHead` (static mesh, Paragon Greystone set:
  `M_Greystone_Flesh_head`, subsurface profile `SSP_Greystone_Skin`, hair, eyes, lashes, tear line). All 10 skin
  textures are present at 2048 and the material is intact, so the black is most likely **light**: a static head inside a
  closed helmet gets no direct light and little Lumen bounce. **Not proven yet.**
- `SM_HeroHead` is authored at 100x (bounds about 24 x 29 x 37 **m**); the hero component scales it down. Spawned alone
  at scale 1 it fills the scene, so take the scale from the hero's component.

## Steps for i9 (Master PC)
1. **Prove the hero cause (2 min).** In Play, stand the hero in daylight and look at the face up close (F8, eject):
   - Lit mode vs `ShowFlag.Lighting 0` / Unlit view (or `viewmode unlit`): if the face shows skin in Unlit, the material
     is fine and it's lighting.
   - Select `HeroHead`: check **Cast Shadow** on the helmet slot is what darkens it; test by unticking Cast Shadow on
     `KnightMesh` for a second. If the face comes back, it's the helmet's shadow.
2. **Hero fix (decide by step 1)**, smallest first:
   - a. On the hero's `HeroHead` component: **Lighting Channels**: keep 0, add a tiny **visor fill**: a PointLight
     component attached to the head socket, 3500 K, intensity about 2 cd, attenuation radius 25 cm, **Cast Shadows off**,
     lighting channel 1 only, and put `HeroHead` on channels 0 + 1. Real-world reason: the visor catches sky/ground
     bounce. That's a catch light, not a glow (INDUSTRY_SECRETS lighting section: motivated light only).
   - b. If it's the material (Unlit is black too): make `MI_HeroFace435` from the skin material path and report it on
     the card, don't edit `M_Greystone_Flesh_head`.
3. **Soldier fix:** open `BP_ThirdPersonCharacter`, select the `HeroHead` component, Ctrl+C. Open each soldier BP and
   paste the component under `KnightMesh`. Set **Parent Socket** to the same socket as the hero's `HeroHead` and keep its
   relative transform. Do the visor fill from 2a the same way. Compile and save the 3 BPs.
   - Optional variety: give soldiers a different eye colour / no hair (helmet covers it): new MI only.
4. Backup first: duplicate each BP you touch as `<BP>_BACKUP435`.

## Checks
- [ ] Hero face shows skin tones in daylight at 1-2 m, not black, and stays dark-but-readable at night.
- [ ] Each soldier type shows a face inside the helmet, no head poking through the helmet (check the nose and chin at
      the visor, from the front and the side, while running).
- [ ] No new light spill on the armour or the wall behind (fill radius 25 cm, channel 1 only).
- [ ] Play: 20 soldiers on screen, frame time not worse by more than about 0.3 ms.
